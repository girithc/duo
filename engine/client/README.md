# client — sponsor model wrappers

One folder for every external model call, so debugging is a single place.
Stages import from here; no stage talks to a sponsor API directly.

| File | Sponsor / API | Env var | Status |
|---|---|---|---|
| `subq.py` | SubQ Decisions API (`subq-snap-1.1`) | `SUBQ_API_KEY` | ✅ implemented |
| `gemini.py` | Google Gemini `generateContent` | `GEMINI_API_KEY` | ✅ implemented |
| `meta.py` | Meta Model API (dev.meta.ai, Llama) | `META_API_KEY` | ⚠️ stub — confirm endpoint/model ids |
| `fetch_ai.py` | Fetch.ai ASI:One chat | `FETCH_API_KEY` | ⚠️ stub — confirm endpoint/model ids |

## Conventions

- Keys are read from env vars; override via constructor args.
- Errors raise `*Error(RuntimeError)` with status + message; transient 429/5xx retried with backoff where implemented.
- Catalog-driven question payloads come from `01-intercept/inputs/tests.py`
  (`pass1_questions`, `pass2_questions`) and are sent via `SubQClient.decide()`.

## Usage

```python
from client.subq import SubQClient
from tests import pass1_questions

answers = SubQClient().decide(state=contract_text, questions=pass1_questions())
```
