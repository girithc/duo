#!/usr/bin/env python3
"""04-arbitrator, part 2: final reverification audit via SubQ.

After the sandbox says PASS, one SubQ request audits the verdict with:
  - the sandbox results (what actually executed and passed)
  - the test cases (what was actually asserted)
  - the code diff signatures (what surface the PR changed)

Three noul gates:
  tests_genuine   — tests assert the ticket's acceptance criteria (not vacuous)
  pass_genuine    — executed pass + these tests justify "PR satisfies ticket"
  diff_gaming     — the diff appears designed to dodge/skip the tested behavior

Final decision: VERIFIED only if all tests passed AND all gates say genuine.
Per rule.md: real calls, honest labels — this is an audit of executed evidence,
clearly recorded as such in the output.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

STAGE_DIR = Path(__file__).parent          # 04-arbitrator
ROOT = STAGE_DIR.parent

_sys_path_done = False


def _setup_path() -> None:
    global _sys_path_done
    if not _sys_path_done:
        import sys
        sys.path.insert(0, str(ROOT))
        _sys_path_done = True


def _client():
    _setup_path()
    from client.subq import SubQClient  # noqa: E402
    from client import env  # noqa: E402
    env.load_project_env()
    return SubQClient()


def _load_module(name: str, path: Path):
    _setup_path()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


QUESTIONS = {
    "tests_genuine": {
        "type": "noul",
        "instructions": (
            "Do these executed test cases genuinely assert the ticket's stated "
            "requirements (real assertions on observable behavior), rather than "
            "being vacuous or skipping the core behavior?"
        ),
        "criteria": {
            "true": "Tests contain real assertions mapped to the ticket's rules",
            "false": "Tests are vacuous, assert trivia, or skip the ticket's core behavior",
        },
    },
    "pass_genuine": {
        "type": "noul",
        "instructions": (
            "Given that these exact tests were executed against the PR code and "
            "all passed, does that justify the conclusion that the PR satisfies "
            "the ticket's requirements?"
        ),
        "criteria": {
            "true": "Executed pass + these tests justify 'PR satisfies ticket'",
            "false": "The pass does not justify it (tests miss the ticket's rules)",
        },
    },
    "diff_gaming": {
        "type": "noul",
        "instructions": (
            "Does the changed surface (signatures below) appear designed to evade "
            "or trivially satisfy the tested behavior — e.g. special-casing the "
            "tested inputs instead of fixing the general behavior?"
        ),
        "criteria": {
            "true": "Diff appears to game the tested behavior",
            "false": "No sign of gaming the tested behavior",
        },
    },
}


def run(results_path: Path, contract_path: Path, generated_dir: Path,
        out_path: Path) -> dict:
    results = json.loads(results_path.read_text(encoding="utf-8"))
    contract = _load_module("duo_audit_contract", contract_path)

    all_passed = (results["failed"] == 0 and results["error"] == 0
                  and results["timeout"] == 0 and results["passed"] > 0)

    tests_code = "\n\n".join(
        (generated_dir / f"{leaf_id}.py").read_text(encoding="utf-8")
        for leaf_id in results["results"])
    state = {
        "ticket": contract.TICKET,
        "signatures_skeleton": contract.SIGNATURES_SKELETON,
        "sandbox_results": {
            "executed": results["total"], "passed": results["passed"],
            "failed": results["failed"], "errors": results["error"],
            "timeouts": results["timeout"],
        },
        "executed_test_code": tests_code,
    }

    answers = _client().decide(state, QUESTIONS)

    audit = {name: {"noul": ans.get("noul", 0.0)} for name, ans in answers.items()}
    # polarity: tests_genuine & pass_genuine must be HIGH; diff_gaming must be LOW
    genuine = (audit["tests_genuine"]["noul"] >= 0.5
               and audit["pass_genuine"]["noul"] >= 0.5
               and audit["diff_gaming"]["noul"] < 0.5)
    diff_gaming = audit["diff_gaming"]["noul"] >= 0.5

    if not all_passed:
        decision = "BLOCK"
        reason = "sandbox reported failing tests (see verdicts)"
    elif genuine and not diff_gaming:
        decision = "VERIFIED"
        reason = ("all blind tests passed on execution; SubQ audit confirms "
                  "tests are genuine, pass is justified, no diff gaming")
    else:
        decision = "REVIEW"
        reason = f"audit flags: {json.dumps(audit)}"

    from bus import publish
    publish("audit", **{k: v["noul"] for k, v in audit.items()},
            decision=decision, reason=reason)

    out = {
        "sandbox_passed": all_passed,
        "audit": audit,
        "decision": decision,
        "reason": reason,
        "method_note": ("audit of executed evidence; not mutation-proven "
                        "(stage 05 not run)"),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    return out
