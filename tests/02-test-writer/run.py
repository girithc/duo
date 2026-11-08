#!/usr/bin/env python3
"""02-test-writer run file — pulls Stage 01 outputs, drives part 1 (writer).

Stage 01 outputs (pulled from here, never duplicated):
  - curated test types: tests/01-interceptor/output/<test>_curated.json
  - contract inputs:    tests/01-interceptor/<test>.py (TICKET, SIGNATURES_SKELETON)

Part 1 (02-blind-test-writer/part1.py): for each curated test type, one
Gemini (gemini-3.8-flash) call writes the pytest tests from ticket + skeleton
+ that test type. Never sees implementation bodies.

Outputs:
  output/generated_tests/<leaf_id>.py
  output/generated_manifest.json

Usage (from project root):
    python3 tests/02-test-writer/run.py              # default test (test-1)
    python3 tests/02-test-writer/run.py test-1.py    # a specific test

Per rule.md: real outputs pulled from disk, no mocks, all errors returned.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).parent           # tests/02-test-writer
ROOT = TESTS_DIR.parent.parent              # repo root
STAGE_DIR = ROOT / "engine" / "02-blind-test-writer"   # stage implementation
STAGE1_OUTPUT_DIR = ROOT / "tests" / "01-interceptor" / "output"
STAGE1_TESTS_DIR = ROOT / "tests" / "01-interceptor"
OUTPUT_DIR = TESTS_DIR / "output"

sys.path.insert(0, str(STAGE_DIR))
import part1  # noqa: E402


def locate_stage1_outputs(test_name: str | None) -> tuple[Path, Path]:
    if test_name is None:
        curated_files = sorted(STAGE1_OUTPUT_DIR.glob("*_curated.json"))
        if not curated_files:
            raise FileNotFoundError(
                f"no Stage 01 outputs found in {STAGE1_OUTPUT_DIR} — "
                "run tests/01-interceptor/run.py first"
            )
        curated_path = curated_files[-1]
    else:
        curated_path = STAGE1_OUTPUT_DIR / f"{test_name}_curated.json"
        if not curated_path.is_file():
            raise FileNotFoundError(f"missing Stage 01 output: {curated_path}")
    contract_path = STAGE1_TESTS_DIR / curated_path.name.replace("_curated.json", "")
    if not contract_path.is_file():
        raise FileNotFoundError(f"missing contract file: {contract_path}")
    return curated_path, contract_path


def main() -> int:
    test_name = sys.argv[1] if len(sys.argv) > 1 else None
    curated_path, contract_path = locate_stage1_outputs(test_name)

    result = part1.run(curated_path, contract_path, OUTPUT_DIR)

    manifest_path = OUTPUT_DIR / "generated_manifest.json"
    manifest_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    if result["failed"]:
        print("\n!!! failures (all listed, none filtered):", file=sys.stderr)
        for leaf_id, entry in result["manifest"].items():
            if entry["status"] == "error":
                print(f"  {leaf_id}: {entry['error']}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
