"""Google Gemini API client — generateContent over REST (stdlib only, no SDK).

Used where a text-generation model is needed (e.g. Stage 02 Tester,
Stage 04 Arbitrator). Prize track: Gemini credits are part of the overall
1st/2nd/3rd prizes.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from collections.abc import Callable

from client import env

BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiError(RuntimeError):
    pass


class GeminiClient:
    def __init__(self, api_key: str | None = None,
                 model: str = "gemini-3.8-flash", timeout: float = 120.0):
        env.load_project_env()
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY not set (env or api_key arg)")
        self.model, self.timeout = model, timeout

    def generate(self, prompt: str, system: str | None = None,
                 temperature: float = 0.2) -> str:
        body: dict = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature},
        }
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}

        request = urllib.request.Request(
            f"{BASE_URL}/{self.model}:generateContent",
            data=json.dumps(body).encode("utf-8"),
            headers={"x-goog-api-key": self.api_key,
                     "Content-Type": "application/json"},
            method="POST",
        )
        import time
        last_exc: Exception | None = None
        for attempt in range(3):  # transient timeouts / 429 / 5xx: retry visibly
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    data = json.loads(response.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as exc:
                last_exc = GeminiError(
                    f"{exc.code}: {exc.read().decode('utf-8', errors='replace')[:200]}"
                )
                if exc.code in (429, 500, 502, 503) and attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                raise last_exc from exc
            except (urllib.error.URLError, TimeoutError) as exc:
                last_exc = GeminiError(f"network error: {exc}")
                if attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                raise last_exc from exc

        try:
            parts = data["candidates"][0]["content"]["parts"]
            return "".join(p.get("text", "") for p in parts)
        except (KeyError, IndexError) as exc:
            raise GeminiError(f"unexpected response shape: {data}") from exc

    def generate_stream(self, prompt: str, on_text: Callable[[str], None],
                        system: str | None = None, temperature: float = 0.2) -> str:
        """Stream real Gemini text chunks through the SSE endpoint.

        Chunks are emitted only as Gemini returns them. A stream that fails
        after partial output is not retried (replaying it could duplicate code).
        """
        body: dict = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature},
        }
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}

        request = urllib.request.Request(
            f"{BASE_URL}/{self.model}:streamGenerateContent?alt=sse",
            data=json.dumps(body).encode("utf-8"),
            headers={"x-goog-api-key": self.api_key,
                     "Content-Type": "application/json",
                     "Accept": "text/event-stream"},
            method="POST",
        )

        import time
        last_exc: Exception | None = None
        for attempt in range(3):
            chunks: list[str] = []
            last_event: dict | None = None
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    for raw_line in response:
                        line = raw_line.decode("utf-8").strip()
                        if not line or line.startswith(":"):
                            continue
                        if not line.startswith("data:"):
                            raise GeminiError(f"unexpected Gemini stream line: {line}")
                        raw_event = line.removeprefix("data:").strip()
                        if raw_event == "[DONE]":
                            break
                        event = json.loads(raw_event)
                        if not isinstance(event, dict):
                            raise GeminiError(f"unexpected Gemini stream event: {raw_event}")
                        last_event = event
                        if "error" in event:
                            raise GeminiError(json.dumps(event["error"]))
                        for candidate in event.get("candidates", []):
                            for part in candidate.get("content", {}).get("parts", []):
                                if part.get("thought"):
                                    continue
                                text = part.get("text")
                                if text is None:
                                    continue
                                if not isinstance(text, str):
                                    raise GeminiError(f"non-text Gemini part: {part}")
                                chunks.append(text)
                                on_text(text)
                    if chunks:
                        return "".join(chunks)
                    raise GeminiError(
                        f"Gemini stream returned no generated text; last event: {last_event}"
                    )
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                last_exc = GeminiError(f"{exc.code}: {detail}")
                if chunks:
                    raise GeminiError(
                        f"Gemini stream interrupted after {len(''.join(chunks))} characters: "
                        f"{exc.code}: {detail}"
                    ) from exc
                if exc.code not in (429, 500, 502, 503, 504) or attempt == 2:
                    raise last_exc from exc
            except (urllib.error.URLError, TimeoutError) as exc:
                last_exc = GeminiError(f"network error: {exc}")
                if chunks:
                    raise GeminiError(
                        f"Gemini stream interrupted after {len(''.join(chunks))} characters: {exc}"
                    ) from exc
                if attempt == 2:
                    raise last_exc from exc
            except (GeminiError, json.JSONDecodeError):
                raise

            time.sleep(2 ** attempt)

        raise last_exc or GeminiError("Gemini stream retry loop exited")
