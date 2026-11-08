#!/usr/bin/env python3
"""Stage 2 — curate: decide which test types this change actually needs.

SubQ answers the catalog's gates against the contract (ticket + signatures):
pass 1 picks families, pass 2 keeps the granular types above the confidence
floor, ordered by severity. Output: tests/01-interceptor/output/<test>_curated.json.

No model writes anything here — this is selection, not generation.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STAGE = ROOT / "tests" / "01-interceptor" / "run.py"


def curate(contract: Path) -> None:
    """Run the curator for one contract; raises if it exits non-zero."""
    contract = Path(contract).resolve()
    if not contract.is_file():
        raise FileNotFoundError(f"contract missing: {contract}")

    cmd = [sys.executable, str(STAGE), contract.name]
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        raise RuntimeError(
            f"curate failed (exit {result.returncode}): {' '.join(cmd)}"
        )
