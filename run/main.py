#!/usr/bin/env python3
"""Duo — pipeline entry point: clone → curate → write → execute → arbitrate.

Usage (from the repo root; any public GitHub PR works):
    python3 run/main.py <owner/repo> <pr_number>
    python3 run/main.py https://github.com/<owner>/<repo> <pr_number>
    python3 run/main.py https://github.com/<owner>/<repo>/pull/<pr_number>

Stage progress is published to the Redis bus (see engine/bus.py); the run id is
put in the environment so every stage process tags its own events. A non-zero
stage exit stops the run, and nothing is printed until the final verdict.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
import traceback
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "engine"))

import bus  # noqa: E402

from arbitrate import arbitrate  # noqa: E402
from clone import clone, parse_target  # noqa: E402
from curate import curate  # noqa: E402
from execute import execute  # noqa: E402
from write import write  # noqa: E402


def run_stage(name: str, fn, *args):
    """Run one stage, publishing start/end/error around it.

    The stage's exception propagates unchanged — the bus records it, it does
    not replace it.
    """
    started = time.monotonic()
    bus.publish("stage_start", stage=name)
    try:
        result = fn(*args)
    except Exception as exc:
        bus.publish("stage_error", stage=name,
                    error=f"{type(exc).__name__}: {exc}",
                    traceback=traceback.format_exc(),
                    seconds=round(time.monotonic() - started, 1))
        raise
    bus.publish("stage_end", stage=name,
                seconds=round(time.monotonic() - started, 1))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Duo against a real GitHub PR")
    parser.add_argument("target", help="owner/repo, repository URL, or pull request URL")
    parser.add_argument("pr", nargs="?", help="pull request number or URL")
    parser.add_argument(
        "--stop-after",
        choices=("curate", "write", "sandbox"),
        help="stop successfully after the selected pipeline stage",
    )
    args = parser.parse_args()

    try:
        owner_repo, pr_number = parse_target(args.target, args.pr)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        print(__doc__, file=sys.stderr)
        return 2

    # The API sets DUO_RUN_ID before spawning us; a CLI run mints its own.
    run_id = os.environ.get("DUO_RUN_ID") or uuid.uuid4().hex[:12]
    os.environ["DUO_RUN_ID"] = run_id
    bus.publish("run_start", repo=owner_repo, pr=pr_number)

    try:
        facts = run_stage("clone", clone, owner_repo, pr_number)
        contract = facts["contract"]
        bus.publish("pr", sha=facts["head_sha"], title=facts["title"],
                    repo=owner_repo, pr=pr_number)

        run_stage("curate", curate, contract)
        if args.stop_after == "curate":
            bus.publish("run_end", status="completed", stage="curate")
            return 0
        run_stage("write", write, contract)
        if args.stop_after == "write":
            bus.publish("run_end", status="completed", stage="write")
            return 0
        run_stage("sandbox", execute, contract, facts["snapshot"])
        if args.stop_after == "sandbox":
            bus.publish("run_end", status="completed", stage="sandbox")
            return 0
        audit = run_stage("arbitrate", arbitrate, contract)
    except Exception as exc:
        # Always close the stream, even on failure, or a watching UI hangs.
        bus.publish("run_end", status="error", error=f"{type(exc).__name__}: {exc}",
                    traceback=traceback.format_exc())
        raise

    bus.publish("verdict", decision=audit["decision"], reason=audit["reason"],
                sandbox_passed=audit["sandbox_passed"],
                audit={k: v["noul"] for k, v in audit["audit"].items()})
    bus.publish("run_end", status="completed", decision=audit["decision"])

    print(f"  repo    : {facts['owner_repo']}#{facts['pr_number']}")
    print(f"  head    : {facts['head_sha']}")
    print(f"  sandbox : {'passed' if audit['sandbox_passed'] else 'FAILED'}")
    for name, scores in audit["audit"].items():
        print(f"  audit.{name:<14} = {scores['noul']:.2f}")
    print(f"\n  *** {audit['decision']} ***\n  {audit['reason']}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
