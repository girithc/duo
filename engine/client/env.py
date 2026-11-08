"""Load the .env file into os.environ — once, no overrides.

Looks in engine/ first, then the repo root, because the stage code lives under
engine/ while the developer's .env sits at the repo root. Real values from the
developer's real environment (rule.md: no mocks); existing process env vars
always win over file entries, and the first file to define a key wins.

Missing keys are NOT handled here — each client fails loudly on its own
missing key (rule.md: better to fail than silently falsely pass).
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).parent.parent                     # engine/
ENV_FILES = (ROOT / ".env", ROOT.parent / ".env")       # engine/.env, then repo root
_loaded = False


def load_project_env() -> None:
    global _loaded
    if _loaded:
        return
    _loaded = True
    for env_path in ENV_FILES:
        if not env_path.is_file():
            continue
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
