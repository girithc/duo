#!/usr/bin/env python3
"""03-sandbox run file — pulls Stage 02's generated tests + the PR checkout,
executes the blind tests, writes run_results.json for Stage 04.

Usage (from project root):
    python3 tests/03-sandbox/run.py test-real.py
    python3 tests/03-sandbox/run.py test-real.py --repo tests/fixtures/<owner>_<repo>_pr<n>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

TESTS_DIR = Path(__file__).parent           # tests/03-sandbox
ROOT = TESTS_DIR.parent.parent              # repo root
STAGE_DIR = ROOT / "engine" / "03-sandbox"  # stage implementation
STAGE2_OUTPUT = ROOT / "tests" / "02-test-writer" / "output"

sys.path.insert(0, str(STAGE_DIR))
import part1  # noqa: E402


def main() -> int:
    raw_args = sys.argv[1:]
    repo_override = None
    if "--repo" in raw_args:
        i = raw_args.index("--repo")
        repo_override = Path(raw_args[i + 1])
        raw_args = raw_args[:i] + raw_args[i + 2:]
    args = [a for a in raw_args if not a.startswith("--")]
    test_name = args[0] if args else None

    manifest_path = STAGE2_OUTPUT / "generated_manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"missing Stage 02 manifest: {manifest_path}")

    if repo_override is None:
        raise SystemExit(
            "no PR checkout given — pass --repo <snapshot path>; "
            "the repo under test must be chosen at run time, never defaulted"
        )
    repo_dir = repo_override
    if not repo_dir.is_dir():
        raise FileNotFoundError(
            f"PR checkout missing: {repo_dir} — run the clone stage first")

    # resolve the contract module (same candidates as the arbitrator runner)
    contract_candidates = [
        TESTS_DIR / (test_name or "test-real"),
        TESTS_DIR.parent / "01-interceptor" / (test_name or "test-real"),
        TESTS_DIR.parent / (test_name or "test-real"),
    ]
    contract_path = next((p for p in contract_candidates if p.is_file()), None)
    if contract_path is None:
        raise FileNotFoundError(
            f"contract not found in: {[str(p) for p in contract_candidates]}")

    part1.run_with_repair(manifest_path, repo_dir,
                          TESTS_DIR / "output", contract_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
