#!/usr/bin/env python3
"""Stage 3 — write: generate the blind tests for the curated test types.

Each curated type gets one Gemini call that sees the ticket, the curated
definition and the signature skeleton — never the implementation bodies. One
streamed Gemini call per type. Output: tests/02-test-writer/output/generated_tests/*.py
plus generated_manifest.json.

Stale output is deleted first: only the current run's tests may reach the
sandbox, otherwise an old PR's files would be executed against this one.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STAGE = ROOT / "tests" / "02-test-writer" / "run.py"
GENERATED = ROOT / "tests" / "02-test-writer" / "output" / "generated_tests"


def write(contract: Path) -> None:
    """Generate tests for one contract; raises if the stage exits non-zero."""
    contract = Path(contract).resolve()
    if not contract.is_file():
        raise FileNotFoundError(f"contract missing: {contract}")

    if GENERATED.exists():
        shutil.rmtree(GENERATED)

    cmd = [sys.executable, str(STAGE), contract.name]
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        raise RuntimeError(
            f"write failed (exit {result.returncode}): {' '.join(cmd)}"
        )
