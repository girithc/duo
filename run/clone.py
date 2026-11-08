#!/usr/bin/env python3
"""Stage 1 — clone: materialise the PR and emit its contract.

Downloads a depth-1 snapshot of the repo at the PR's head commit, fetches the
PR title/body and diff, and writes the contract every later stage reads
(TICKET, HEAD_SHA, SIGNATURES_SKELETON, FILE_MANIFEST).

The git/API/AST primitives live in engine/01-intercept/extract.py and are called
in-process here — one implementation, no duplicated clone logic.

Per rule.md: real network calls, real checkouts, every error raised with context.
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine"))

import bus  # noqa: E402
EXTRACT = ROOT / "engine" / "01-intercept" / "extract.py"

SNAPSHOT_DIR = ROOT / "tests" / "fixtures"
CONTRACT_DIR = ROOT / "tests" / "01-interceptor"

# Accepted at run time: "owner/repo", "https://github.com/owner/repo",
# ".../owner/repo.git", ".../owner/repo/pull/123", "git@github.com:owner/repo".
_GITHUB_URL = re.compile(
    r"^(?:https?://)?(?:www\.)?github\.com/"
    r"(?P<owner>[^/]+)/(?P<repo>[^/]+?)"
    r"(?:\.git)?(?:/pull/(?P<pr>\d+))?/?$",
    re.IGNORECASE,
)
_GITHUB_SSH = re.compile(
    r"^git@github\.com:(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?$",
    re.IGNORECASE,
)
_SLUG = re.compile(r"^(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$")


def parse_target(target: str, pr_number: str | int | None = None) -> tuple[str, int]:
    """Normalise a repo reference into ("owner/repo", pr_number).

    The repo and PR are chosen per run — nothing downstream assumes a specific
    project. A PR number in the URL wins; if both are given they must agree.
    """
    text = target.strip()
    ssh = _GITHUB_SSH.match(text)
    if ssh:
        owner, repo, url_pr = ssh["owner"], ssh["repo"], None
    else:
        url = _GITHUB_URL.match(text)
        slug = None if url else _SLUG.match(text)
        if url is None and slug is None:
            raise ValueError(
                f"not a repo reference: {target!r} — use owner/repo or a "
                f"GitHub repo/PR URL"
            )
        owner = (url or slug)["owner"]
        repo = (url or slug)["repo"]
        url_pr = url["pr"] if url else None

    if isinstance(pr_number, str):
        supplied_pr_url = _GITHUB_URL.match(pr_number.strip())
        if supplied_pr_url is not None:
            if supplied_pr_url["pr"] is None:
                raise ValueError(f"PR URL has no pull/number: {pr_number!r}")
            supplied_repo = f"{supplied_pr_url['owner']}/{supplied_pr_url['repo']}"
            if supplied_repo.lower() != f"{owner}/{repo}".lower():
                raise ValueError(
                    f"repository and PR URL disagree: {owner}/{repo} != {supplied_repo}"
                )
            pr_number = int(supplied_pr_url["pr"])

    if url_pr is not None:
        number = int(url_pr)
        if pr_number is not None and int(pr_number) != number:
            raise ValueError(
                f"PR number given twice and they disagree: URL says {number}, "
                f"argument says {pr_number}"
            )
    elif pr_number is None:
        raise ValueError(f"no PR number: pass it, or use a .../pull/<n> URL")
    else:
        try:
            number = int(pr_number)
        except ValueError:
            raise ValueError(f"PR number must be an integer, got {pr_number!r}")

    return f"{owner}/{repo}", number


def _extract():
    """Import the extractor by path (the folder name starts with a digit)."""
    if not EXTRACT.is_file():
        raise FileNotFoundError(f"extractor missing: {EXTRACT}")
    spec = importlib.util.spec_from_file_location("duo_extract", EXTRACT)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {EXTRACT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def clone(owner_repo: str, pr_number: int,
          contract_name: str = "test-real.py") -> dict:
    """Fetch PR facts + snapshot, write the contract, return what later stages need.

    Returns {"owner_repo", "pr_number", "head_sha", "title", "snapshot",
    "contract", "files"}. Raises on any network, git or parse failure.
    """
    extract = _extract()
    snapshot = SNAPSHOT_DIR / f"{owner_repo.replace('/', '_')}_pr{pr_number}"
    contract = CONTRACT_DIR / contract_name

    pr = extract.fetch_pr(owner_repo, pr_number)
    bus.publish("clone_progress", phase="pr_fetched", head=pr["head_sha"],
                title=pr["title"])

    extract.get_snapshot(owner_repo, pr_number, pr["head_sha"], snapshot)

    bus.publish("clone_progress", phase="snapshot_ready", head=pr["head_sha"],
                snapshot=str(snapshot))
    diff_text = extract.fetch_diff(owner_repo, pr_number)
    files = extract.diff_manifest(diff_text)
    if not files:
        raise ValueError(f"{owner_repo}#{pr_number}: diff parsed to zero files")

    skeleton = extract.build_skeleton(snapshot, files)
    CONTRACT_DIR.mkdir(parents=True, exist_ok=True)
    extract.emit_contract(
        contract,
        ticket=f"Issue: {pr['title']}\n\n{pr['body']}",
        skeleton=skeleton,
        files=files,
        head_sha=pr["head_sha"],
    )

    bus.publish("clone_progress", phase="contract_written",
                head=pr["head_sha"], files=len(files),
                contract=str(contract))

    return {
        "owner_repo": owner_repo,
        "pr_number": pr_number,
        "head_sha": pr["head_sha"],
        "title": pr["title"],
        "snapshot": snapshot,
        "contract": contract,
        "files": files,
    }
