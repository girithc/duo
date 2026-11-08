#!/usr/bin/env python3
"""02-test-writer, part 1: blind test generation.

For EACH curated test type from Stage 01, ONE Gemini call that writes the
pytest test cases for that type, using exactly three inputs:

  1. the ticket body (the requirement)
  2. the signatures skeleton from the diff (surface shape, no bodies)
  3. the single test type being written (id, definition, severity)

The writer never sees the PR's implementation. Anything it must assume
(collaborators, interfaces not in the skeleton) is tagged `# ASSUMPTION:`
inline so Stage 04's arbitrator can tell assumption-failures from defects.

Output (written by tests/02-test-writer/run.py):
  output/generated_tests/<leaf_id>.py   one file per test type
  output/generated_manifest.json        per type: file, status, error, tokens

Per rule.md: real API calls, no mocks; every error is recorded, none filtered.
"""
from __future__ import annotations

import ast
import importlib.util
import json
import re
import traceback
from pathlib import Path

STAGE_DIR = Path(__file__).parent          # 02-blind-test-writer
ROOT = STAGE_DIR.parent                    # project root

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


def load_module(name: str, path: Path):
    _setup_path()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _gemini():
    _setup_path()
    from client.gemini import GeminiClient  # noqa: E402
    from client import env  # noqa: E402
    env.load_project_env()
    return GeminiClient(timeout=240.0)  # thinking models run long


PROMPT_TEMPLATE = """\
You are Duo's Blind Test Writer. You write tests from requirements only.

You receive:
1. The ticket (the requirement — the source of truth)
2. A signatures skeleton (the public surface of the change — signatures only,
   no implementation bodies)
3. Exactly ONE test type to cover

Rules:
- Write pytest test cases covering ONLY this test type.
- Import the target code exactly as the skeleton declares it.
- You may NOT see the implementation. If you must assume a collaborator,
  parameter, or behavior not stated in the ticket or skeleton, write the
  test anyway but tag the exact line with `# ASSUMPTION: <what you assumed>`.
- Every test must have assertions that check observable behavior.
- Do not invent requirements that are not in the ticket.
- Output ONLY a Python code block, no explanations.

TICKET:
{ticket}

SIGNATURES SKELETON:
{skeleton}

TEST TYPE TO COVER:
id: {leaf_id}
description: {definition}
severity: {severity}
"""

CODE_FENCE_RE = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL)


def build_prompt(test_type: dict, ticket: str, skeleton: str) -> str:
    return PROMPT_TEMPLATE.format(
        ticket=ticket, skeleton=skeleton, leaf_id=test_type["leaf_id"],
        definition=test_type["definition"], severity=test_type["severity"],
    )


def extract_code(response: str, leaf_id: str) -> str:
    blocks = CODE_FENCE_RE.findall(response)
    if not blocks:
        raise ValueError(f"{leaf_id}: no python code block in model response")
    return max(blocks, key=len).strip() + "\n"


def run_one(test_type: dict, ticket: str, skeleton: str, gemini) -> dict:
    """One streamed Gemini generation per selected test type, with no review."""
    prompt = build_prompt(test_type, ticket, skeleton)
    response = gemini.generate_stream(
        prompt,
        lambda delta: _emit(
            "test_code_delta", leaf_id=test_type["leaf_id"], delta=delta
        ),
        temperature=0.3,
    )
    code = extract_code(response, test_type["leaf_id"])
    _emit("test_code", leaf_id=test_type["leaf_id"], code=code)
    _emit("write_progress", leaf_id=test_type["leaf_id"], phase="generated")
    return {"code": code, "assumptions": re.findall(r"# ASSUMPTION: (.+)", code)}


IMPROVE_PROMPT = """\
You are Duo's Blind Test Writer. Your previously written test FAILED TO RUN
in the sandbox. Fix it.

Execution error:
{error}

Your previous test:
{code}

Rules:
- The error usually means you invented something (a fixture, import, or
  parameter) that does not exist. Remove or replace it with plain pytest.
- You still may NOT see the implementation. Keep testing the same test type,
  from the ticket and skeleton only.
- Keep `# ASSUMPTION:` tags for anything still assumed.
- Every test must have assertions on observable behavior.
- Output ONLY a Python code block.

TICKET:
{ticket}

SIGNATURES SKELETON:
{skeleton}
"""


def improve_test(leaf_id: str, code: str, error_output: str, ticket: str,
                 skeleton: str, gemini) -> dict:
    """Take a test that failed to build + its error, return a repaired test."""
    prompt = IMPROVE_PROMPT.format(error=error_output, code=code,
                                   ticket=ticket, skeleton=skeleton)
    _emit("repair_started", leaf_id=leaf_id)
    response = gemini.generate_stream(
        prompt,
        lambda delta: _emit(
            "test_code_delta", leaf_id=leaf_id, delta=delta, phase="repair"
        ),
        temperature=0.2,
    )
    fixed = extract_code(response, leaf_id)
    _emit("test_code", leaf_id=leaf_id, code=fixed, phase="repair")
    return {"code": fixed, "assumptions": re.findall(r"# ASSUMPTION: (.+)", fixed)}


def run(curated_path: Path, contract_path: Path, out_dir: Path) -> dict:
    curated = json.loads(curated_path.read_text(encoding="utf-8"))
    test_types = curated["curated_test_types"]
    contract = load_module(contract_path.stem.replace("-", "_"), contract_path)
    gemini = _gemini()

    tests_dir = out_dir / "generated_tests"
    tests_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, dict] = {}

    def one(test_type: dict) -> tuple[str, dict]:
        leaf_id = test_type["leaf_id"]
        entry: dict = {"file": f"generated_tests/{leaf_id}.py", "status": "ok"}
        _emit("test_started", leaf_id=leaf_id)
        try:
            result = run_one(test_type, contract.TICKET, contract.SIGNATURES_SKELETON, gemini)
            (tests_dir / f"{leaf_id}.py").write_text(result["code"], encoding="utf-8")
            entry["assumptions"] = result["assumptions"]
            _emit("test_written", leaf_id=leaf_id, status="ok",
                  code=result["code"], assumptions=result["assumptions"])
        except Exception as exc:  # rule.md #3: record ALL failures, keep going
            entry["status"] = "error"
            entry["error"] = f"{type(exc).__name__}: {exc}"
            _emit("test_written", leaf_id=leaf_id, status="error",
                  error=str(exc), traceback=traceback.format_exc())
        return leaf_id, entry

    # Independent generation calls run concurrently; the UI lets users choose
    # which live test editors to expand while the streams arrive.
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max(1, len(test_types))) as pool:
        for leaf_id, entry in pool.map(one, test_types):
            manifest[leaf_id] = entry

    return {
        "source_curated": curated_path.name,
        "generated": sum(1 for m in manifest.values() if m["status"] == "ok"),
        "failed": sum(1 for m in manifest.values() if m["status"] == "error"),
        "manifest": dict(sorted(manifest.items())),
    }
