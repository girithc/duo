#!/usr/bin/env python3
"""04-arbitrator run file — pulls sandbox results, rules on every failure,
emits the final gate (BLOCK / PASS).

Usage (from project root):
    python3 tests/04-arbitrator/run.py test-real.py
"""
from __future__ import annotations

import sys
from pathlib import Path

TESTS_DIR = Path(__file__).parent           # tests/04-arbitrator
ROOT = TESTS_DIR.parent.parent              # repo root
STAGE_DIR = ROOT / "engine" / "04-arbitrator"   # stage implementation

sys.path.insert(0, str(STAGE_DIR))
import part1  # noqa: E402
import part2  # noqa: E402


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    test_name = args[0] if args else "test-real"

    results_path = TESTS_DIR.parent / "03-sandbox" / "output" / "run_results.json"
    contract_candidates = [
        TESTS_DIR / test_name,                       # tests/04-arbitrator/
        TESTS_DIR.parent / "01-interceptor" / test_name,  # tests/01-interceptor/
        TESTS_DIR.parent / test_name,                # tests/
    ]
    contract_path = next((p for p in contract_candidates if p.is_file()), None)
    if contract_path is None:
        raise FileNotFoundError(
            f"contract '{test_name}' not found in: "
            f"{[str(p) for p in contract_candidates]}")
    generated_dir = (TESTS_DIR.parent / "02-test-writer" / "output"
                     / "generated_tests")
    out_path = TESTS_DIR / "output" / "verdicts.json"

    for required in (results_path, contract_path):
        if not required.is_file():
            raise FileNotFoundError(f"missing input: {required}")

    part1.run(results_path, contract_path, generated_dir, out_path)

    # Final reverification audit (SubQ): is the pass genuine?
    part2.run(results_path, contract_path, generated_dir,
              TESTS_DIR / "output" / "final_audit.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
