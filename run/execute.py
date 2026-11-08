#!/usr/bin/env python3
"""Stage 4 — execute: run the generated tests against the PR snapshot.

Builds a real venv inside a copy of the snapshot, installs the repo, runs the
blind tests, and stores per-test outcome + traceback in
tests/03-sandbox/output/run_results.json. Auto-repairs collection errors
(import path, missing conftest) so a harness bug is not reported as a failed
implementer test.

No verdict is formed here — this stage only produces evidence.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STAGE = ROOT / "tests" / "03-sandbox" / "run.py"


def execute(contract: Path, repo_dir: Path) -> None:
    """Run one contract's generated tests against `repo_dir`; raises on failure."""
    contract = Path(contract).resolve()
    repo_dir = Path(repo_dir).resolve()
    if not contract.is_file():
        raise FileNotFoundError(f"contract missing: {contract}")
    if not repo_dir.is_dir():
        raise FileNotFoundError(f"PR snapshot missing: {repo_dir}")

    cmd = [sys.executable, str(STAGE), contract.name, "--repo", str(repo_dir)]
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        raise RuntimeError(
            f"execute failed (exit {result.returncode}): {' '.join(cmd)}"
        )
