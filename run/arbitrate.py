#!/usr/bin/env python3
"""Stage 5 — arbitrate: rule on each failure, then audit whether the pass is real.

For every failing test: is the implementer wrong, or is the test wrong? Then a
SubQ audit scores the run on tests_genuine / pass_genuine / diff_gaming and
emits the final decision. Output: tests/04-arbitrator/output/verdicts.json and
final_audit.json, returned here as a dict.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STAGE = ROOT / "tests" / "04-arbitrator" / "run.py"
AUDIT = ROOT / "tests" / "04-arbitrator" / "output" / "final_audit.json"


def arbitrate(contract: Path) -> dict:
    """Arbitrate one contract and return the parsed final audit."""
    contract = Path(contract).resolve()
    if not contract.is_file():
        raise FileNotFoundError(f"contract missing: {contract}")

    cmd = [sys.executable, str(STAGE), contract.name]
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        raise RuntimeError(
            f"arbitrate failed (exit {result.returncode}): {' '.join(cmd)}"
        )
    if not AUDIT.is_file():
        raise FileNotFoundError(
            f"arbitrate exited 0 but wrote no audit: {AUDIT}"
        )
    return json.loads(AUDIT.read_text(encoding="utf-8"))
