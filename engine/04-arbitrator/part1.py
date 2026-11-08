#!/usr/bin/env python3
"""04-arbitrator, part 1: rule on every failed/error test from the sandbox.

For each non-passing test file, ONE Gemini call judges:

  real_defect        — the ticket's requirement is genuinely violated → BLOCK
  hallucinated_test  — the test invents a rule/fixture not in the ticket → discard
  assumption_failed  — an `# ASSUMPTION:` tag guessed wrong → discard + correct tester

Inputs per verdict: crash log + ticket + skeleton + the failing test's code.
Output: verdicts.json + the final gate (any real_defect => BLOCK).
Per rule.md: real inputs from disk, no mocks; all errors surfaced.
"""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

STAGE_DIR = Path(__file__).parent          # 04-arbitrator
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
    return GeminiClient()


VERDICTS = ("real_defect", "hallucinated_test", "assumption_failed")

PROMPT = """\
You are Duo's Arbitrator — a neutral judge. A test written WITHOUT seeing the
implementation has failed against the real code. Decide which side is wrong.

Verdicts (choose exactly one):
- "real_defect": the test checks a rule stated in the ticket, and the code
  violates it. The PR is genuinely defective.
- "hallucinated_test": the test depends on something NOT stated in the ticket
  or signatures (an invented fixture, rule, or behavior). The test is wrong.
- "assumption_failed": the test explicitly tagged an ASSUMPTION that the real
  code does not satisfy. The test guessed an interface wrongly.

Answer with ONLY a JSON object:
{{"verdict": "...", "reason": "one or two sentences citing the ticket/skeleton/test line"}}

TICKET:
{ticket}

SIGNATURES SKELETON (all the test writer was allowed to see):
{skeleton}

THE FAILING TEST ({test_type}):
```python
{test_code}
```

SANDBOX FAILURE OUTPUT:
```
{failure_output}
```
"""

JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def arbitrate_one(test_type: str, test_code: str, failure_output: str,
                  ticket: str, skeleton: str, gemini) -> dict:
    prompt = PROMPT.format(ticket=ticket, skeleton=skeleton, test_type=test_type,
                           test_code=test_code,
                           failure_output=failure_output[-1500:])
    response = gemini.generate(prompt, temperature=0.1)
    match = JSON_RE.search(response)
    if not match:
        raise ValueError(f"arbitrator returned no JSON: {response[:200]}")
    verdict = json.loads(match.group(0))
    if verdict.get("verdict") not in VERDICTS:
        raise ValueError(f"arbitrator returned unknown verdict: {verdict}")
    return verdict


def run(results_path: Path, contract_path: Path, generated_dir: Path,
        out_path: Path) -> dict:
    results = json.loads(results_path.read_text(encoding="utf-8"))
    contract = load_module(contract_path.stem.replace("-", "_"), contract_path)
    gemini = _gemini()

    verdicts = {}
    for test_type, r in results["results"].items():
        if r["status"] == "passed":
            verdicts[test_type] = {"verdict": "pass", "reason": "sandbox passed"}
        else:
            test_code = (generated_dir / f"{test_type}.py").read_text(encoding="utf-8")
            verdicts[test_type] = {
                "sandbox_status": r["status"],
                **arbitrate_one(test_type, test_code, r["output_tail"],
                                contract.TICKET, contract.SIGNATURES_SKELETON, gemini),
            }
        _emit("verdict", test_type=test_type,
              verdict=verdicts[test_type]["verdict"],
              reason=verdicts[test_type].get("reason", ""))

    block = any(v["verdict"] == "real_defect" for v in verdicts.values())
    gate = {"decision": "BLOCK" if block else "PASS",
            "reason": ("real defect(s) found: " + ", ".join(
                t for t, v in verdicts.items() if v["verdict"] == "real_defect"))
            if block else "no real defect confirmed by execution + arbitration"}

    out = {"verdicts": verdicts, "gate": gate}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    return out
