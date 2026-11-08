"""SubQ Decisions API client (subq-snap-1.1) — fully implemented, stdlib only.

Docs source: https://docs.subq.ai (Decisions API, public preview).
POST /v1/systemone — structured judgments: noul / choice / score answers
with probabilities. You pay only for input tokens (output_tokens is 0).

Question dicts are built by 01-intercept/inputs/tests.py:
    pass1_questions() / pass2_questions() — noul gates for catalog selection.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

from client import env

BASE_URL = "https://api.subq.ai/v1"
MODEL = "subq-snap-1.1"
RETRY_STATUSES = {429, 500, 502, 503}


class SubQError(RuntimeError):
    def __init__(self, status: int, error_type: str, message: str):
        self.status, self.error_type, self.message = status, error_type, message
        super().__init__(f"SubQ {status} {error_type}: {message}")


def _post_json(url: str, payload: dict, headers: dict, timeout: float) -> dict:
    """POST JSON, return parsed body. Raises SubQError on any non-200."""
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(raw)["detail"]
            error_type = detail.get("error_type", "?")
            message = detail.get("message", "?")
        except Exception:
            error_type, message = "unknown", raw[:200]
        raise SubQError(exc.code, error_type, message) from exc
    except urllib.error.URLError as exc:
        raise SubQError(0, "network_error", str(exc.reason)) from exc


class SubQClient:
    def __init__(self, api_key: str | None = None, model: str = MODEL,
                 timeout: float = 120.0, retries: int = 2):
        env.load_project_env()
        self.api_key = api_key or os.environ.get("SUBQ_API_KEY")
        if not self.api_key:
            raise RuntimeError("SUBQ_API_KEY not set (env or api_key arg)")
        self.model, self.timeout, self.retries = model, timeout, retries

    def decide_full(self, state, questions: dict, images: list | None = None) -> dict:
        """Full response: {"model", "answers", "usage"}. Retries on 429/5xx."""
        payload: dict = {"model": self.model, "state": state, "questions": questions}
        if images:
            payload["images"] = images
        headers = {"Authorization": f"Bearer {self.api_key}",
                   "Content-Type": "application/json"}
        last_error: SubQError | None = None
        for attempt in range(self.retries + 1):
            try:
                return _post_json(f"{BASE_URL}/systemone", payload, headers, self.timeout)
            except SubQError as exc:
                if exc.status in RETRY_STATUSES and attempt < self.retries:
                    last_error = exc
                    time.sleep(2 ** attempt)
                    continue
                raise
        raise last_error or SubQError(0, "unreachable", "retry loop exited")

    def decide(self, state, questions: dict, images: list | None = None) -> dict:
        """Just the answers: {question_name: {type, noul|choice|score, ...}}."""
        return self.decide_full(state, questions, images)["answers"]
