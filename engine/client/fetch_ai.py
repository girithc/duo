"""Fetch.ai client (ASI:One chat completions) — Best Use of Fetch.ai track.

TODO(hackathon): confirm endpoint, auth scheme, and model ids from the
FetchAI hackathon guide, then finish `chat()`. Kept OpenAI-completions-
shaped until verified.
"""
from __future__ import annotations

import os

from client import env


class FetchAIError(RuntimeError):
    pass


class FetchAIClient:
    BASE_URL = "https://api.asi1.ai/v1"  # TODO: verify against guide
    DEFAULT_MODEL = "asi1-mini"          # TODO: verify model id

    def __init__(self, api_key: str | None = None, model: str | None = None,
                 timeout: float = 120.0):
        env.load_project_env()
        self.api_key = api_key or os.environ.get("FETCH_API_KEY")
        if not self.api_key:
            raise RuntimeError("FETCH_API_KEY not set (env or api_key arg)")
        self.model = model or self.DEFAULT_MODEL
        self.timeout = timeout

    def chat(self, messages: list[dict], model: str | None = None) -> str:
        """messages = [{"role": "user", "content": "..."}] -> assistant text."""
        raise NotImplementedError(
            "Finish FetchAIClient.chat() once endpoint/model ids are "
            "confirmed from the FetchAI guide"
        )
