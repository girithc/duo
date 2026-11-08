#!/usr/bin/env python3
"""03-sandbox, part 1: execute the blind tests against the real PR code.

Steps:
  1. Copy the PR-head checkout to a persistent sandbox dir.
  2. Inject ONLY the generated test files listed in the writer's manifest.
  3. Create a fresh venv; pip install the repo + pytest.
  4. Run pytest per test file with a hard timeout (hangs = timeout, never
     silent).
  5. Write run_results.json: per test file -> passed | failed | error |
     timeout + output tail. This file is Stage 04's only input.

Per rule.md: real execution, no mocks; all errors recorded, none filtered.
"""
from __future__ import annotations

import codecs
from concurrent.futures import ThreadPoolExecutor
import json
import os
import re
import selectors
import shutil
import signal
import subprocess
import sys
import time
import traceback
from pathlib import Path

STAGE_DIR = Path(__file__).parent          # 03-sandbox
ROOT = STAGE_DIR.parent                    # project root

VENV_TIMEOUT = 300      # seconds for pip install
TEST_TIMEOUT = 120      # seconds per test file
OUTPUT_TAIL = 2000      # chars of pytest output kept per file
OUTPUT_READ_SIZE = 65536
PROCESS_DRAIN_TIMEOUT = 2.0
MAX_TEST_PROCESSES = 4
MODEL_CREDENTIAL_ENV_VARS = frozenset({
    "SUBQ_API_KEY",
    "GEMINI_API_KEY",
    "META_API_KEY",
    "MODEL_API_KEY",
    "FETCH_API_KEY",
})

_sys_path_done = False


def _setup_path() -> None:
    global _sys_path_done
    if not _sys_path_done:
        import sys
        sys.path.insert(0, str(ROOT))
        _sys_path_done = True


def _emit(event: str, **fields) -> None:
    """Publish a progress event; a bus outage must not stop the run."""
    _setup_path()
    from bus import publish
    publish(event, **fields)


def _run(cmd: list[str], cwd: Path | None = None, timeout: int = 60,
         env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, timeout=timeout, env=env,
                          capture_output=True, text=True, errors="replace")


def test_subprocess_environment() -> dict[str, str]:
    """Scrub Duo's model credentials; this is not OS-level isolation."""
    return {
        key: value for key, value in os.environ.items()
        if key not in MODEL_CREDENTIAL_ENV_VARS
    }


def prepare_sandbox(clone_dir: Path, test_files: list[Path], sandbox_dir: Path) -> Path:
    if sandbox_dir.exists():
        shutil.rmtree(sandbox_dir)
    shutil.copytree(clone_dir, sandbox_dir,
                    ignore=shutil.ignore_patterns(".git", "__pycache__"))
    duo_tests = sandbox_dir / "duo_tests"
    duo_tests.mkdir()
    for f in test_files:
        shutil.copy2(f, duo_tests / f.name)
    return duo_tests


def make_venv(sandbox_dir: Path) -> Path:
    venv = sandbox_dir / ".duo_venv"
    result = _run([sys.executable, "-m", "venv", str(venv)], timeout=120)
    if result.returncode != 0:
        raise RuntimeError(f"venv creation failed: {result.stderr[-500:]}")
    pip = venv / "bin" / "pip"
    env = test_subprocess_environment()
    env["SETUPTOOLS_SCM_PRETEND_VERSION"] = "0.0.0"  # shallow clone has no tags
    result = _run([str(pip), "install", "--quiet", "pytest", "pytest-asyncio",
                   "pytest-timeout", str(sandbox_dir)],
                  cwd=sandbox_dir, timeout=VENV_TIMEOUT, env=env)
    if result.returncode != 0:
        raise RuntimeError(f"pip install failed: {result.stderr[-800:]}")
    return venv


def _pytest_status(returncode: int, output: str) -> str:
    if returncode == 0:
        return "passed"
    # Pytest uses exit 1 for assertion failures and some setup failures. Keep
    # genuine assertion failures distinct from collection/build errors.
    n_errors = re.search(r"(\d+) error", output)
    if ((n_errors and int(n_errors.group(1)) > 0)
            or "INTERNALERROR" in output or "no tests ran" in output):
        return "error"
    return "failed"


def _finish_test(leaf_id: str, test_file: str, status: str, returncode: int | None,
                 seconds: float, output: str, error: str | None = None) -> dict:
    """Publish the old result event plus the complete streaming outcome."""
    tail = output[-OUTPUT_TAIL:]
    finished = {
        "leaf_id": leaf_id,
        "status": status,
        "returncode": returncode,
        "seconds": round(seconds, 3),
    }
    if error is not None:
        finished["error"] = error
    _emit("execution_finished", **finished)
    _emit("sandbox_result", leaf_id=leaf_id, status=status,
          output_tail=tail[-400:])
    return {"file": test_file, "status": status, "output_tail": tail}


def _kill_process_group(process: subprocess.Popen) -> int:
    """Kill only the group created by start_new_session for this process."""
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    return process.wait()


def run_test_file(venv: Path, sandbox_dir: Path, test_file: str,
                  timeout: float = TEST_TIMEOUT) -> dict:
    """Stream one real pytest process without allowing its pipes to deadlock it."""
    py = venv / "bin" / "python"
    leaf_id = Path(test_file).stem
    command = [str(py), "-m", "pytest", test_file, "-q", "--no-header",
               "-p", "no:cacheprovider"]
    started = time.monotonic()
    process = None
    selector = None
    outputs: dict[str, list[str]] = {"stdout": [], "stderr": []}

    try:
        process = subprocess.Popen(
            command,
            cwd=sandbox_dir,
            env=test_subprocess_environment(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
            start_new_session=True,
        )
        _emit("execution_started", leaf_id=leaf_id)
        selector = selectors.DefaultSelector()
        decoders = {}
        for stream_name, pipe in (("stdout", process.stdout),
                                  ("stderr", process.stderr)):
            if pipe is None:
                raise RuntimeError(f"pytest {stream_name} pipe was not created")
            os.set_blocking(pipe.fileno(), False)
            selector.register(pipe, selectors.EVENT_READ, stream_name)
            decoders[stream_name] = codecs.getincrementaldecoder("utf-8")(
                errors="replace")

        deadline = started + timeout
        drain_deadline = None
        timed_out = False
        drain_timed_out = False
        while selector.get_map() or process.poll() is None:
            now = time.monotonic()
            if not timed_out and process.poll() is None and now >= deadline:
                _kill_process_group(process)
                timed_out = True
                drain_deadline = now + PROCESS_DRAIN_TIMEOUT
            if process.poll() is not None and drain_deadline is None:
                # A detached descendant can retain a pipe after pytest exits.
                # Never let that keep the run alive forever.
                drain_deadline = now + PROCESS_DRAIN_TIMEOUT
            if drain_deadline is not None and now >= drain_deadline:
                drain_timed_out = True
                break

            if selector.get_map():
                readable = selector.select(timeout=0.05)
            else:
                time.sleep(0.05)
                readable = []
            for key, _ in readable:
                pipe = key.fileobj
                stream_name = key.data
                while True:
                    try:
                        chunk = os.read(pipe.fileno(), OUTPUT_READ_SIZE)
                    except BlockingIOError:
                        break
                    if chunk:
                        text = decoders[stream_name].decode(chunk)
                        if text:
                            outputs[stream_name].append(text)
                            _emit("execution_output", leaf_id=leaf_id,
                                  stream=stream_name, text=text)
                        continue
                    remainder = decoders[stream_name].decode(b"", final=True)
                    if remainder:
                        outputs[stream_name].append(remainder)
                        _emit("execution_output", leaf_id=leaf_id,
                              stream=stream_name, text=remainder)
                    selector.unregister(pipe)
                    pipe.close()
                    break

        returncode = process.wait()
        output = "".join(outputs["stdout"]) + "\n" + "".join(outputs["stderr"])
        if timed_out:
            message = f"exceeded {timeout}s — killed owned process group"
            error = message + ("\n" + output if output.strip() else "")
            return _finish_test(leaf_id, test_file, "timeout", returncode,
                                time.monotonic() - started,
                                message + "\n" + output, error=error)
        if drain_timed_out:
            message = (
                f"output pipes remained open {PROCESS_DRAIN_TIMEOUT}s after "
                "pytest exited; closed them and marked execution as error"
            )
            return _finish_test(leaf_id, test_file, "error", returncode,
                                time.monotonic() - started,
                                output + "\n" + message,
                                error=output + "\n" + message)
        status = _pytest_status(returncode, output)
        error = None
        if status != "passed":
            error = output if output.strip() else f"pytest exited {returncode}"
        return _finish_test(leaf_id, test_file, status, returncode,
                            time.monotonic() - started, output, error=error)
    except Exception:
        # Spawn/read/emit failures become real per-file errors with complete
        # tracebacks. A running child is reaped before recording the failure.
        details = traceback.format_exc()
        if process is not None and process.poll() is None:
            _kill_process_group(process)
        returncode = process.poll() if process is not None else None
        captured = "".join(outputs["stdout"]) + "\n" + "".join(outputs["stderr"])
        combined = captured + "\n" + details
        return _finish_test(leaf_id, test_file, "error", returncode,
                            time.monotonic() - started, combined, error=combined)
    finally:
        if selector is not None:
            selector.close()
        if process is not None:
            for pipe in (process.stdout, process.stderr):
                if pipe is not None and not pipe.closed:
                    pipe.close()


def run_test_files(venv: Path, sandbox_dir: Path, test_files: list[str]) -> dict:
    """Run independent pytest files with at most four live child processes."""
    if not test_files:
        return {}

    def one(test_file: str) -> dict:
        return run_test_file(venv, sandbox_dir, test_file)

    results = {}
    workers = min(MAX_TEST_PROCESSES, len(test_files))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for test_file, result in zip(test_files, pool.map(one, test_files)):
            results[Path(test_file).stem] = result
    return results


def run_with_repair(manifest_path: Path, clone_dir: Path, out_dir: Path,
                    contract_path: Path, max_rounds: int = 2) -> dict:
    """Run blind tests; when a test ERRORS while building (not asserting),
    send it back to the test writer with the error and repair it — up to
    max_rounds times. Still-broken tests go to the arbitrator as-is."""
    writer = _load_writer()
    contract = _load_contract(contract_path)

    summary = run(manifest_path, clone_dir, out_dir)
    sandbox_dir = Path(summary["sandbox"])
    venv = sandbox_dir / ".duo_venv"
    gen_dir = manifest_path.parent / "generated_tests"
    repairs: dict[str, dict] = {}

    for round_no in range(1, max_rounds + 1):
        errored = {k: v for k, v in summary["results"].items()
                   if v["status"] == "error"}
        if not errored:
            break
        rerun = []
        for leaf_id, r in errored.items():
            code_file = gen_dir / f"{leaf_id}.py"
            old_code = code_file.read_text(encoding="utf-8")
            fixed = writer.improve_test(leaf_id, old_code, r["output_tail"],
                                        contract.TICKET, contract.SIGNATURES_SKELETON,
                                        _gemini())
            code_file.write_text(fixed["code"], encoding="utf-8")
            # copy the repaired file INTO the sandbox before rerunning
            shutil.copy2(code_file, sandbox_dir / "duo_tests" / code_file.name)
            repairs[leaf_id] = {"round": round_no,
                                "assumptions": fixed["assumptions"]}
            _emit("repair", leaf_id=leaf_id, round=round_no)
            rerun.append(f"duo_tests/{leaf_id}.py")
        # Rerun real error cases in the same prepared sandbox and environment.
        # Assertion failures and timeouts are intentionally not repaired here.
        summary["results"].update(run_test_files(venv, sandbox_dir, rerun))

    for key in ("passed", "failed", "error", "timeout"):
        summary[key] = sum(1 for x in summary["results"].values()
                           if x["status"] == key)
    summary["repairs"] = repairs
    out_path = out_dir / "run_results.json"
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def _load_writer():
    _setup_path()
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "duo_writer", Path(__file__).parent.parent / "02-blind-test-writer" / "part1.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_contract(contract_path: Path):
    _setup_path()
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "duo_sandbox_contract", contract_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _gemini():
    _setup_path()
    from client.gemini import GeminiClient  # noqa: E402
    from client import env  # noqa: E402
    env.load_project_env()
    return GeminiClient()


def run(manifest_path: Path, clone_dir: Path, out_dir: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    ok_entries = [(leaf_id, entry) for leaf_id, entry in manifest["manifest"].items()
                  if entry["status"] == "ok"]
    if not ok_entries:
        raise ValueError("manifest has zero successfully generated test files")

    gen_root = manifest_path.parent / "generated_tests"
    test_files = [gen_root / entry["file"].split("/")[-1]
                  for _, entry in ok_entries]
    missing = [str(f) for f in test_files if not f.is_file()]
    if missing:
        raise FileNotFoundError(f"manifest lists missing test files: {missing}")

    leaf_ids = [leaf_id for leaf_id, _ in ok_entries]
    relative_tests = [f"duo_tests/{Path(entry['file']).name}"
                      for _, entry in ok_entries]
    _emit("execution_queued", leaf_ids=leaf_ids)
    _emit("execution_phase", phase="preparing")
    sandbox_dir = out_dir / "sandbox_repo"
    prepare_sandbox(clone_dir, test_files, sandbox_dir)
    venv = make_venv(sandbox_dir)

    _emit("execution_phase", phase="running")
    results = run_test_files(venv, sandbox_dir, relative_tests)

    summary = {
        "repo": str(clone_dir),
        "sandbox": str(sandbox_dir),
        "total": len(results),
        "passed": sum(1 for r in results.values() if r["status"] == "passed"),
        "failed": sum(1 for r in results.values() if r["status"] == "failed"),
        "error": sum(1 for r in results.values() if r["status"] == "error"),
        "timeout": sum(1 for r in results.values() if r["status"] == "timeout"),
        "results": results,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "run_results.json"
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary
