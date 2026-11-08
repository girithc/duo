# Duo

### Verify what a pull request was meant to do—not only what its tests happen to check.

Duo is an intent-driven pull request verification prototype. It reads the requirement, chooses relevant test types, generates implementation-blind tests, executes them, and presents the evidence as a live workflow.

It is designed for a familiar problem in software delivery: **a green CI check proves that selected tests passed. It does not, by itself, prove that the change satisfies the requirement for every input.**

## Why this matters to CI/CD and the SDLC

A typical delivery pipeline moves through:

**Requirement → implementation → code review → CI tests → merge → deployment.**

Tests are usually written by someone who already knows the implementation. That is useful, but it creates a predictable gap: the tests can reproduce the implementation author's assumptions instead of independently checking the requested behavior.

Duo separates those concerns:

1. **Intent** comes from the PR title and body—the requested behavior.
2. **The contract** comes from the changed-file manifest and Python declaration signatures. Implementation bodies are withheld from the writer.
3. **Test selection** is a structured decision constrained by a defined catalog.
4. **Test generation** turns one selected test type at a time into executable pytest code.
5. **Execution** runs real test processes and reports their actual outcomes.

The goal is not to replace existing unit tests, code review, integration testing, or CI. It is to add another source of evidence **before merge**, when changing code is still cheaper than responding to a production incident.

A passing generated test is an observation, not a mathematical proof of correctness. That distinction is fundamental to trustworthy continuous delivery.

## How it works

```text
GitHub repository + PR
        │
        ▼
Fetch PR metadata and verify the requested head commit
        │
        ▼
Contract: ticket + changed-file manifest + declaration signatures
        │
        ▼
SubQ decision model: select relevant families and granular test types
        │
        ▼
Gemini: one streamed, implementation-blind generation per selected type
        │
        ▼
Pytest: execute generated tests in parallel, with limits and real logs
        │
        ├── Execution/setup error ──► error output returns to Writer for repair
        │
        └── Assertion failure ─────► retained as failure evidence
```

Each selected test type produces a Python file. Test generation is currently **one direct Gemini pass**; there is no separate model-review loop before execution.

### 1. Repository and PR ingestion

- Accepts a GitHub repository URL and a PR number or PR URL.
- Fetches the actual PR from GitHub.
- Materializes the PR head revision and verifies the checked-out SHA against the API response.
- Forms a contract from ticket text, the changed-file manifest, and Python signature declarations—not implementation bodies.

**Current scope:** public GitHub repositories and a Python-focused test catalog.

### 2. Test selection

The SubQ Decisions API (`subq-snap-1.1`) evaluates the contract against a frozen catalog:

- 24 high-level test families.
- 669 granular test types in the Python ecosystem.
- Two passes: family selection, then selection of leaf test types.
- A confidence cutoff controls whether a test type enters the generation queue.

This makes model selection a **bounded policy input to the lifecycle**, rather than an unrestricted instruction to generate arbitrary tests.

### 3. Writer

- Gemini `gemini-3.8-flash` uses the ticket, declarations, and one selected test definition.
- Code chunks stream to the browser as the model produces them.
- The Writer accordion opens code editors when real code arrives. Editors can be expanded and collapsed independently during parallel generation.
- CodeMirror provides syntax highlighting, line numbers, and folding.
- Unstated assumptions are marked in generated code with `# ASSUMPTION:`.

The editor shows model-generated code; it does not imply that the code is correct or has passed.

### 4. Execution

- Dependencies are prepared in a fresh virtual environment.
- Test files execute through pytest in separate processes.
- At most **four** test processes run concurrently, so resource use is bounded instead of unlimited.
- stdout and stderr stream to a single-column, expandable log view for each test.
- Timeouts terminate the process group created for that test.
- Results distinguish **passed**, **failed assertions**, **execution error**, and **timeout**.
- Setup/collection errors are sent back to Writer with the real execution output for a bounded repair cycle.

A failed assertion cannot be rewritten merely to obtain a green result. A model failure is also distinct from a defect in the submitted implementation.

### 5. Evidence and arbitration

The UI currently stops after execution. The repository also contains arbitration stages used by the broader CLI pipeline; they are outside the current four-section UI workflow. A future merge decision should incorporate observed execution, reviewer judgment, and repository policy—not model confidence alone.

## The local UI

| Section | What it presents |
| --- | --- |
| Pull request | Repository/PR input and cloning status only |
| Tests | Actual test types selected by the decision model |
| Writer | Live generated code in independent accordions |
| Execution | Parallel test status, live stdout/stderr, durations, and outcomes |

The interface uses Next.js, React, TypeScript, Tailwind CSS, and CodeMirror. Stage-level status is shown explicitly; the UI does not invent model progress percentages or artificial typing animations.

An initial model response can take time before its first visible code chunk. Streaming reduces delivery delay once generation starts; it does not remove model or network latency.

## Architecture

```text
Next.js / React UI
       │ POST /runs; EventSource
       ▼
FastAPI service
       │ starts and supervises a real pipeline process
       ▼
Clone → Select → Write → Execute
       │
       ▼
Redis Streams ──► Server-Sent Events ──► section-specific UI updates
```

### Notable components

| Path | Responsibility |
| --- | --- |
| [app/api/main.py](app/api/main.py) | Run creation, status, and replayable SSE |
| [engine/bus.py](engine/bus.py) | JSON run events in Redis Streams |
| [run/main.py](run/main.py) | Pipeline orchestration and stage tracebacks |
| [engine/01-intercept/extract.py](engine/01-intercept/extract.py) | GitHub metadata, real checkout, and contract extraction |
| [engine/01-intercept/inputs/tests.py](engine/01-intercept/inputs/tests.py) | Generated test-family and test-type catalog |
| [engine/02-blind-test-writer/part1.py](engine/02-blind-test-writer/part1.py) | One-pass generation and execution-error repairs |
| [engine/03-sandbox/part1.py](engine/03-sandbox/part1.py) | Bounded test execution and process output streaming |
| [ui/components/review/](ui/components/review/) | Four-section review interface |

Streaming model output and streaming process output are separate concerns: the first transports generated text chunks; the second transports real subprocess stdout/stderr.

## Run locally

These instructions are for a local engineering demo. Use a public, trusted PR.

### Prerequisites

- Python and a virtual environment.
- Node.js and npm.
- `redis-server`.
- A Gemini API key and a SubQ API key.

### Install dependencies

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
(cd ui && npm --cache ./.npmcache install)
```

Create a root `.env` with real credentials:

```dotenv
SUBQ_API_KEY=your_server_side_subq_key
GEMINI_API_KEY=your_server_side_gemini_key
```

Keep `.env` local and out of version control. These are server-side credentials; they are not input fields in the UI.

The frontend defaults to `http://localhost:8000`. To use a different API origin, set `NEXT_PUBLIC_DUO_API_URL` when running or building it.

### Start Redis, the API, and the UI with one command

Run this from the project root:

```bash
bash -c '
set -e

redis-server --port 6379 --bind 127.0.0.1 --save "" --appendonly no --dir /tmp &
REDIS_PID=$!

./.venv/bin/python -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000 &
API_PID=$!

(cd ui && exec ./node_modules/.bin/next dev --hostname localhost --port 3010) &
UI_PID=$!

trap "kill $REDIS_PID $API_PID $UI_PID 2>/dev/null" EXIT INT TERM
wait
'
```

Open **http://localhost:3010**—use `localhost`, not an IP address, for the Next.js development origin.

Press **Ctrl+C** to stop these three services. Backend changes require restarting FastAPI; this command does not enable API hot reload or supervise an already-detached pipeline after shutdown.

For development, Redis streams are deliberately in-memory without persistence. Runtime logs and generated source/result artifacts are written under `runtime/` and `tests/` on disk.

### API

Start a run through the UI, or directly against the local service:

```bash
curl -X POST http://localhost:8000/runs \
  -H 'Content-Type: application/json' \
  -d '{
    "target": "https://github.com/tqdm/tqdm.git",
    "pr": "1916",
    "stop_after": "sandbox"
  }'
```

The response contains a `run_id` and an SSE path at `/runs/{run_id}/events`. The endpoint supports `Last-Event-ID` or an explicit starting event ID for replay.

| Endpoint | Purpose |
| --- | --- |
| `POST /runs` | Start a real pipeline process |
| `GET /runs/{run_id}` | Inspect process/run metadata |
| `GET /runs/{run_id}/events` | Read the Redis-backed SSE event stream |
| `GET /health` | Check Redis connectivity |

The API rejects concurrent runs inside its single FastAPI process because the current pipeline still uses shared artifact paths. Before CI or multi-user hosting, those paths should be made unique per run.

### Static checks

```bash
.venv/bin/python -m compileall -q app engine run
(cd ui && npx tsc --noEmit)
```

Static checks validate compilation and types. They do **not** substitute for executing a real PR through the full workflow.

## Current status and honest limits

**Implemented and exercised:** real public PR ingestion, SubQ test selection, Gemini streaming, browser event delivery, and generated Writer artifacts.

**Implemented in the latest execution integration:** parallel pytest processes, bounded concurrency, process output streaming, timeouts, and execution-error repair. Its complete UI-to-execution journey still requires another real-PR validation after restarting the updated services.

Important boundaries:

- The catalog and writer are Python-focused, not yet language-agnostic.
- Public GitHub ingestion is implemented; GitHub App authentication and private-repository onboarding are future work.
- The current per-run output locations are shared artifact paths.
- Explicit API startup, Redis, and provider credentials are required for the local stack.
- Models can produce weak or incorrect tests. Execution reports what happened; it cannot repair reality or prove arbitrary program correctness.

### Security boundary

The bundled execution layer runs repository setup code and tests with host filesystem and network access. Although known model-credential environment variables are removed from those subprocesses, **this is not an OS-level or hostile-code security sandbox**.

Use trusted PRs for local development. **Do not expose the current executor directly to untrusted code or use it as a multi-tenant SaaS runner without an isolation layer.** Credential removal alone does not protect secrets stored in reachable files. A descendant process can also escape a process-group boundary; reliable hostile-code containment requires a real sandbox or disposable container/VM isolation.

## Roadmap: meet developers inside CI/CD and the SDLC

The architecture already separates source input, test policy, generation, execution, and events. The next step is to support the same workflow wherever delivery decisions occur.

### 1. GitHub Actions: PR-native verification

Add a workflow triggered by:

- `pull_request` on open, update, reopen, and ready-for-review.
- `workflow_dispatch` for explicitly selected pull requests.
- Optionally `push` for protected-branch regressions after merge.

The action should turn repository and PR metadata into a Duo change target, invoke an isolated worker, and publish results using **GitHub Checks**. Every result should link to the exact source SHA, run ID, selected test types, generated code, and execution logs.

Use repository concurrency to prevent obsolete runs, for example:

```yaml
concurrency:
  group: duo-pr-${{ github.event.pull_request.number }}
  cancel-in-progress: true
```

Avoid running untrusted PR code under `pull_request_target` merely to obtain secrets. Use least-privilege permissions, protected environments, short-lived credentials, and an explicit trust/approval policy for forked PRs. Model credentials must remain separate from the test environment.

Planned CI reporting should distinguish:

- **Evidence available:** tests executed successfully.
- **Verification failed:** real assertions failed against the submitted change.
- **Infrastructure/provider error:** GitHub, model, broker, or worker failure.
- **Neutral:** no executable evidence was produced or the change is not currently supported.

### 2. Cloud-triggered and cloud-hosted runs

Support an authenticated GitHub App or webhook receiver so teams do not need to operate a local API.

A cloud implementation should add:

- A durable queue and per-run workspace rather than shared paths.
- Disposable containers or microVMs for execution.
- Controlled network egress, filesystem access, CPU/memory limits, and secret scoping.
- Worker autoscaling with bounded concurrency per repository and organization.
- Managed Redis/broker storage, artifact storage, retention policies, and audit logs.
- Provider failure recovery and explicit timeout/error reporting.

The goal is a repeatable CI result regardless of whether the same immutable runner image is used locally, in GitHub Actions, or in a cloud service.

### 3. Local triggers

Provide an installable CLI and a `git pre-push` integration for developers who want a signal before opening or updating a PR.

Support both:

- **Local loop:** quick, selected checks on a developer machine with clear trust boundaries.
- **CI parity:** the same test catalog, runner image, timeout configuration, and reporting format used by hosted CI.

Developer overrides should be explicit and reviewable—for example, through a future `.duo.yml` policy file—not hidden in model state. Local infrastructure failures should never be presented as source-code verification failures.

### 4. Delivery and operational checkpoints

After execution evidence is trustworthy, extend triggers to the rest of continuous delivery:

- Scheduled nightly verification of the current integration branch.
- Pre-release workflows against a staging artifact.
- Post-deployment smoke checks and incident evidence collection.
- Release gates or rollback signals based on explicit team policies.

These are quality signals for a release decision, not autonomous deployment authority.

### 5. Broader coverage with honest boundaries

Later extensions can include:

- Language adapters beyond Python.
- Supported private-repository authentication.
- Monetary and latency budgets per run.
- Saved run history and PR trends.
- Human approval of test selections and generated assumptions.
- Clear repair policies for timeout versus assertion failure.
- Versioned catalogs, model configuration, and policy files for CI reproducibility.

Every trigger—UI, webhook, GitHub Action, CLI, schedule, or deployment—should feed the same typed execution contract rather than creating separate verification logic.

## Engineering principles

1. **No fabricated evidence.** Real repositories, model calls, and processes; no mock result standing in for a real run.
2. **No silent success.** A failed or incomplete check remains visibly failed or incomplete.
3. **Errors stay observable.** Server failures include their source and traceback; failures are not collapsed into an apparent pass.
4. **Independent evidence matters.** Generated tests come from intent and public contracts, not implementation bodies.
5. **Bound resource usage.** Limit concurrency, define timeouts, and separate provider calls from execution processes.
6. **CI should communicate causality.** Distinguish a code failure, a test-authoring error, and an infrastructure failure.

## What this project demonstrates

For engineers, hiring managers, and founders, Duo is a vertical slice across software-testing strategy and delivery infrastructure:

- Translating requirements into test policy and executable evidence.
- An incremental TypeScript/React interface over real asynchronous work.
- FastAPI, process supervision, Redis Streams, and replayable SSE.
- Parallel process control with timeouts and full error propagation.
- An explicit path from a **local developer tool** to **PR-native CI**, **cloud execution**, and **delivery controls**.

The central idea is intentionally simple: **software delivery is more trustworthy when the tests investigate the requirement, and the release evidence reports what actually happened.**
