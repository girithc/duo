"""Meta Model API client (Llama models) — dev.meta.ai, $100 hackathon credits.

OpenAI-compatible chat completions shape (Llama API preview):
POST {BASE}/chat/completions, Bearer auth, response choices[].message.content.
Model id configurable via META_MODEL env (default below); any API mismatch
fails loudly with the raw response (rule.md #3) so it can be fixed, not hidden.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from client import env

BASE_URL = "https://api.meta.ai/v1"
DEFAULT_MODEL = os.environ.get("META_MODEL", "muse-wonder-1.0")


class MetaError(RuntimeError):
    pass


class MetaClient:
    def __init__(self, api_key: str | None = None, model: str | None = None,
                 timeout: float = 120.0):
        env.load_project_env()
        self.api_key = (api_key or os.environ.get("META_API_KEY")
                        or os.environ.get("MODEL_API_KEY"))
        if not self.api_key:
            raise RuntimeError("META_API_KEY not set (env or api_key arg)")
        self.model = model or os.environ.get("META_MODEL", DEFAULT_MODEL)
        self.timeout = timeout

    def chat(self, messages: list[dict], model: str | None = None,
             temperature: float = 0.2) -> str:
        """messages = [{"role": ..., "content": ...}] -> assistant text."""
        body = json.dumps({
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
        }).encode("utf-8")
        request = urllib.request.Request(
            f"{BASE_URL}/chat/completions",
            data=body,
            headers={"Authorization": f"Bearer {self.api_key}",
                     "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise MetaError(
                f"{exc.code}: {exc.read().decode('utf-8', errors='replace')[:300]}"
            ) from exc
        except urllib.error.URLError as exc:
            raise MetaError(f"network error: {exc.reason}") from exc

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise MetaError(f"unexpected response shape: {json.dumps(data)[:300]}") from exc
        if content is None:
            raise MetaError(f"empty completion: {json.dumps(data)[:300]}")
        return content
