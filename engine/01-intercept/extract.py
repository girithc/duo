#!/usr/bin/env python3
"""01-intercept: real-repo contract extractor.

Materialises a real GitHub repo at a PR's head commit (depth-1 snapshot,
cached under tests/fixtures/ and keyed by head sha), fetches the PR body
(ticket) and diff, and emits a contract module (TICKET, HEAD_SHA,
SIGNATURES_SKELETON, FILE_MANIFEST) — the same shape as hand-written
tests/test-1.py, but derived from live data.

Usage:
    python3 01-intercept/extract.py <owner/repo> <pr_number> [out_path]

Emits (default tests/test-real.py). Per rule.md: real network calls, real
files; every error returned loudly.
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

STAGE_DIR = Path(__file__).parent          # 01-intercept
ROOT = STAGE_DIR.parent                    # project root

# Where PR snapshots live: one shallow checkout per <owner>_<repo>_pr<n>.
# The sha sidecar next to it (not inside the work tree — an untracked file in
# the snapshot would leak into the sandbox's `git status`) is the cache key.
SNAPSHOT_DIR = ROOT / "tests" / "fixtures"

API = "https://api.github.com"


def _get(url: str, accept: str = "application/vnd.github+json") -> bytes:
    request = urllib.request.Request(url, headers={
        "User-Agent": "duo-verifier",
        "Accept": accept,
    })
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def fetch_pr(owner_repo: str, number: int) -> dict:
    raw = _get(f"{API}/repos/{owner_repo}/pulls/{number}")
    data = json.loads(raw)
    return {
        "title": data["title"],
        "body": data.get("body") or "",
        "diff_url": data["diff_url"],
        "head_sha": data["head"]["sha"],
    }


def _git(args: list[str], cwd: Path | None = None, timeout: int = 300) -> str:
    """Run git; any non-zero exit is raised with git's own stderr attached."""
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                            text=True, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed ({result.returncode}): "
            f"{result.stderr.strip() or result.stdout.strip()}"
        )
    return result.stdout.strip()


def get_snapshot(owner_repo: str, number: int, head_sha: str,
                 workdir: Path) -> Path:
    """Materialise `owner_repo` at PR #`number`'s head commit — shallow (depth 1).

    Cached at `workdir` and reused only when the recorded sha matches
    `head_sha`: a push to the PR re-fetches instead of silently reviewing the
    old code (rule.md §5). The checked-out sha is re-verified against the sha
    the API reported, so a push landing mid-fetch fails loudly rather than
    producing a verdict on a different tree.
    """
    sha_file = workdir.parent / f"{workdir.name}.sha"
    remote_url = f"https://github.com/{owner_repo}.git"

    if workdir.is_dir():
        recorded = sha_file.read_text(encoding="utf-8").strip() if sha_file.is_file() else ""
        if recorded == head_sha:
            return workdir
        actual_remote = _git(["remote", "get-url", "origin"], cwd=workdir, timeout=30)
        if actual_remote.rstrip("/") != remote_url.rstrip("/"):
            raise RuntimeError(
                f"snapshot {workdir} belongs to {actual_remote}, "
                f"not {remote_url} — refusing to reuse it"
            )
    else:
        workdir.parent.mkdir(parents=True, exist_ok=True)
        _git(["clone", "--quiet", "--depth", "1", remote_url, str(workdir)])

    _git(["fetch", "--quiet", "--depth", "1", "origin", f"pull/{number}/head"],
         cwd=workdir)
    _git(["checkout", "--quiet", "--force", "FETCH_HEAD"], cwd=workdir, timeout=60)

    checked_out = _git(["rev-parse", "HEAD"], cwd=workdir, timeout=30)
    if checked_out != head_sha:
        raise RuntimeError(
            f"PR #{number} head moved while fetching: API said {head_sha}, "
            f"checked out {checked_out} — re-run to review the new head"
        )
    sha_file.write_text(head_sha + "\n", encoding="utf-8")
    return workdir


def fetch_diff(owner_repo: str, number: int) -> str:
    """Read the API diff representation, avoiding the legacy redirecting URL."""
    return _get(
        f"{API}/repos/{owner_repo}/pulls/{number}",
        accept="application/vnd.github.v3.diff",
    ).decode("utf-8", errors="replace")


def diff_manifest(diff_text: str) -> list[tuple[str, str]]:
    """Parse a unified diff -> [(path, change-note)] in PR order.

    Path is the post-PR (b/) side, except for deletions which keep the a/ side
    because the file is gone at head. Renames resolve to the new path and are
    marked `renamed` instead of `modified`.
    HAVE-TO-DO: git C-quotes paths containing non-ASCII or control characters
    (and marks them `"a/\342\200\246"`); those still parse wrong here.
    """
    files: list[tuple[str, str]] = []
    old_path = ""
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            rest = line[len("diff --git "):]
            a_part, sep, b_part = rest[2:].partition(" b/")
            old_path = a_part
            files.append((b_part if sep else a_part, "modified"))
        elif line.startswith("new file mode") and files:
            files[-1] = (files[-1][0], "added")
        elif line.startswith("deleted file mode") and files:
            files[-1] = (old_path, "deleted")
        elif line.startswith("rename to ") and files:
            files[-1] = (files[-1][0], "renamed")
    return files


def py_signatures(file_path: Path) -> list[str]:
    """Signature lines (defs/classes) of one file — bodies stripped."""
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError) as exc:
        raise ValueError(f"cannot parse {file_path}: {exc}") from exc
    sigs = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            seg = ast.get_source_segment(file_path.read_text(encoding="utf-8"), node)
            if seg:
                sigs.append(seg.splitlines()[0])
    return sigs


def is_test_path(path: str) -> bool:
    """Implementer test files are excluded from the skeleton — their
    signatures would dominate the state and their bodies are off-limits."""
    parts = Path(path).parts
    return bool(parts) and parts[0] in ("tests", "test") or path.startswith("test_")


def build_skeleton(repo_dir: Path, files: list[tuple[str, str]]) -> str:
    lines: list[str] = []
    for path, note in files:
        if is_test_path(path):
            lines.append(f"# {path}  (implementer tests — excluded from skeleton)")
            continue
        if not path.endswith(".py"):
            lines.append(f"# {path}  ({note}, non-python)")
            continue
        full = repo_dir / path
        if not full.is_file():
            lines.append(f"# {path}  ({note}, not present at PR head)")
            continue
        lines.append(f"# {path}  ({note})")
        for sig in py_signatures(full):
            lines.append(f"{sig}  ...")
        lines.append("")
    return "\n".join(lines)


def emit_contract(out_path: Path, ticket: str, skeleton: str,
                  files: list[tuple[str, str]], head_sha: str) -> None:
    letter = {"added": "A", "deleted": "D", "renamed": "R"}
    manifest = "\n".join(f"{letter.get(note, 'M')}  {path}  ({note})"
                         for path, note in files)
    content = f'''"""Real-repo contract: {out_path.stem} — generated by 01-intercept/extract.py."""

TICKET = {json.dumps(ticket)}

HEAD_SHA = {json.dumps(head_sha)}

SIGNATURES_SKELETON = {json.dumps(skeleton)}

FILE_MANIFEST = {json.dumps(manifest)}
'''
    out_path.write_text(content, encoding="utf-8")


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: extract.py <owner/repo> <pr_number> [out_path]", file=sys.stderr)
        return 2
    owner_repo, number = sys.argv[1], int(sys.argv[2])
    out_path = Path(sys.argv[3]) if len(sys.argv) > 3 else ROOT / "tests" / "test-real.py"

    pr = fetch_pr(owner_repo, number)
    ticket = f"Issue: {pr['title']}\n\n{pr['body']}"

    workdir = SNAPSHOT_DIR / f"{owner_repo.replace('/', '_')}_pr{number}"
    get_snapshot(owner_repo, number, pr["head_sha"], workdir)

    diff_text = fetch_diff(owner_repo, number)
    files = diff_manifest(diff_text)
    if not files:
        raise ValueError("diff parsed to zero files")

    skeleton = build_skeleton(workdir, files)
    emit_contract(out_path, ticket, skeleton, files, pr["head_sha"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
