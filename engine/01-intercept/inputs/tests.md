# Duo Test-Type Catalog — Interceptor Input

> Stored in `01-intercept/inputs/`. This catalog is the frozen yardstick: SubQ **selects** from it, never invents types.
> Python ecosystem focus. Two levels: 24 families → granular leaf types.

## How SubQ (Decisions API, `subq-snap-1.1`) consumes this

- **Pass 1 — family relevance:** one `POST /v1/systemone` request. `state` = ticket + signatures skeleton + file manifest (`contract/input.txt`). 24 `noul` questions, one per family ("Is family X relevant to this change?"). A `choice` question is single-select, so multi-select relevance uses `noul` gates. Fits the 1–128 question limit.
- **Pass 2 — granular selection (pooled + batched):** collect ALL leaf types from every selected family into one pool (deduplicate by leaf-id), then chunk into batches of at most 128 `noul` questions each — one request per batch. Each question is named `famNN__leaf-id` so every answer stays traceable to its family and name collisions across families are impossible. Merge all batch answers, drop leaves below the confidence threshold (0.6), sort by severity then confidence. Worst case (all 24 families selected): 669 leaves → 6 batches; typical case (~5 families): ~150 leaves → 2 batches.
- **Output artifact:** curated, severity-ordered list of test types → handed to the Stage 02 test generator as mandatory coverage.
- Constraints honored: 384K-token context window, 1–128 questions per request, input-tokens-only billing.

## Escape hatch

If no leaf fits a novel risk, SubQ returns a low-confidence result and the pipeline logs `other: <proposal>`. Proposals are human-reviewed and promoted into this catalog later. The frozen list never changes mid-run.

## The 24 families

1. Static, Type & Architectural Verification
2. Isolated Unit & Functional Logic Testing
3. Test-Double & State-Isolation Testing
4. Property-Based, Fuzzing & Symbolic Verification
5. Contract, Schema & Wire-Serialization Testing
6. Integration & Ephemeral Infrastructure Testing
7. API, End-to-End (E2E), Acceptance (BDD) & UI Testing
8. Concurrency, Race & Free-Threading Stress Testing
9. Performance, Memory & Resource Ceiling Testing
10. Chaos Engineering & Resilience Fault Injection
11. Security, Supply Chain & Adversarial Testing
12. Data, Scientific, AI/ML & Meta-Verification
13. Packaging, Distribution & Environment Testing
14. Compatibility & Portability Testing
15. Documentation & Example Testing
16. Exploratory, Usability & Accessibility Testing
17. Differential & Behavioral-Equivalence Testing
18. Observability, Ops & Config Testing
19. Compliance, Privacy & Governance Testing
20. Upgrade & Migration Path Testing
21. Feature-Flag & Rollout Testing
22. Determinism & Reproducibility Testing
23. Disaster Recovery & Backup-Restore Testing
24. Experimentation & Statistical Testing

Cross-cutting tags (any test can carry): `regression-lock`, `mutation-target`.

---
# Batch A — Test-Type Catalog (Part 1 of 2)

## 1. Static, Type & Architectural Verification

Pre-execution verification of type annotations, lint rules, import boundaries, complexity, and dead code without running the program.

Tool belt: `mypy`, `ruff`, `pylint`, `import-linter`, `vulture`, `radon`

### Granular test types

- `mypy-strict-annotation-coverage` — Verify type annotations across modules under strict mode. Trigger: new module lacks complete type hints. Sev: high. Tool: `mypy`
- `mypy-none-safety-check` — Detect Optional misuse and missing None guards. Trigger: nullable values flow into non-null contexts. Sev: critical. Tool: `mypy`
- `mypy-generic-variance-check` — Validate generic parameters and type variance correctness. Trigger: container types use inheritance unsoundly. Sev: medium. Tool: `mypy`
- `mypy-overload-signature-match` — Check overload signatures match implementation dispatch. Trigger: API branches on argument types. Sev: medium. Tool: `mypy`
- `mypy-protocol-structural-conformance` — Verify structural Protocol conformance at type level. Trigger: duck-typed interfaces formalized as Protocols. Sev: medium. Tool: `mypy`
- `mypy-pydantic-plugin-check` — Validate model field types via the Pydantic plugin. Trigger: settings or schemas defined as models. Sev: high. Tool: `mypy`
- `mypy-typed-orm-queries` — Type-check ORM expressions with typed SQLAlchemy stubs. Trigger: repository queries constructed dynamically. Sev: high. Tool: `mypy`
- `mypy-stub-completeness-sync` — Check third-party stub presence and version alignment. Trigger: dependency upgrade lands without stubs. Sev: medium. Tool: `mypy`
- `ruff-lint-rule-suite` — Run curated ruff rule set on changed files. Trigger: lint baseline must not regress. Sev: medium. Tool: `ruff`
- `ruff-import-order-hygiene` — Enforce deterministic import ordering and grouping. Trigger: diffs churn import blocks repeatedly. Sev: low. Tool: `ruff`
- `ruff-modernization-upgrade` — Flag legacy syntax upgradeable to modern Python. Trigger: old interpreter versions dropped. Sev: low. Tool: `ruff`
- `ruff-noqa-suppression-audit` — Audit inline suppressions and per-file ignores. Trigger: new noqa comments appeared in review. Sev: medium. Tool: `ruff`
- `ruff-security-antipatterns` — Lint eval, shell injection, and unsafe calls. Trigger: user input reaches dynamic execution. Sev: critical. Tool: `ruff`
- `ruff-error-handling-lint` — Detect bare excepts and swallowed exceptions. Trigger: silent failures reported from production. Sev: high. Tool: `ruff`
- `ruff-async-blocking-calls` — Flag blocking calls inside async functions. Trigger: event-loop stalls reported under load. Sev: high. Tool: `ruff`
- `pylint-refactor-smells` — Detect long functions, broad scopes, duplicated branches. Trigger: review flags sprawling function growth. Sev: low. Tool: `pylint`
- `pylint-design-contract` — Enforce naming, docstrings, and design heuristics. Trigger: public API style consistency demanded. Sev: low. Tool: `pylint`
- `pylint-duplicate-code-detection` — Detect copy-pasted blocks across modules. Trigger: parallel implementations suspected after changes. Sev: medium. Tool: `pylint`
- `import-linter-layered-boundaries` — Enforce layered architecture import contracts. Trigger: domain must not import infrastructure. Sev: critical. Tool: `import-linter`
- `import-linter-forbidden-dependencies` — Forbid explicit cross-package dependency edges. Trigger: plugin boundaries split into packages. Sev: high. Tool: `import-linter`
- `import-linter-circular-imports` — Detect circular import chains between containers. Trigger: import-time side effects and cycles appear. Sev: high. Tool: `import-linter`
- `import-linter-interface-isolation` — Keep adapters behind designated interface modules. Trigger: hexagonal ports-and-adapters mandated. Sev: medium. Tool: `import-linter`
- `vulture-dead-code-scan` — Identify unreachable functions, classes, and variables. Trigger: large refactor orphaned code paths. Sev: low. Tool: `vulture`
- `vulture-unused-exports` — Flag unused public exports and API surface. Trigger: deprecated endpoints scheduled for removal. Sev: low. Tool: `vulture`
- `vulture-dead-feature-flags` — Find code behind removed feature flags. Trigger: flag-cleanup epic in progress. Sev: low. Tool: `vulture`
- `radon-cyclomatic-complexity` — Enforce cyclomatic complexity thresholds per function. Trigger: nested conditionals grow in review. Sev: medium. Tool: `radon`
- `radon-cognitive-load-check` — Enforce cognitive complexity limits on hot paths. Trigger: reviewer complaints about readability. Sev: low. Tool: `radon`
- `radon-maintainability-index` — Track maintainability index on changed modules. Trigger: legacy module absorbs another feature. Sev: low. Tool: `radon`
- `radon-raw-metrics-hotspots` — Report LOC and size metrics for hotspots. Trigger: file size limits in contribution guide. Sev: low. Tool: `radon`
- `mypy-config-typed-parsing` — Verify typed settings parsing and env coercion. Trigger: env-driven configuration handling added. Sev: medium. Tool: `mypy`

## 2. Isolated Unit & Functional Logic Testing

White-box and black-box testing of individual functions, classes, and async coroutines across happy paths, boundaries, and exception paths.

Tool belt: `pytest`, `pytest-asyncio`, `unittest`, `time-machine`

### Granular test types

- `pytest-happy-path-assertions` — Assert expected outputs for canonical valid inputs. Trigger: new function or endpoint behavior defined. Sev: critical. Tool: `pytest`
- `pytest-boundary-conditions` — Test min, max, empty, and off-by-one values. Trigger: numeric or collection limits specified. Sev: high. Tool: `pytest`
- `pytest-exception-path-coverage` — Verify raised exceptions and error types. Trigger: failure modes enumerated in contract. Sev: high. Tool: `pytest`
- `pytest-parametrized-equivalence-classes` — Parametrize equivalent input classes compactly. Trigger: many inputs share expected behavior. Sev: medium. Tool: `pytest`
- `pytest-fixture-scoped-setup` — Build reusable, well-scoped fixtures per concern. Trigger: repeated setup across test modules. Sev: medium. Tool: `pytest`
- `pytest-regression-bug-repro` — Reproduce reported bug as failing test. Trigger: bug ticket has deterministic repro steps. Sev: high. Tool: `pytest`
- `pytest-tmp-path-filesystem` — Exercise file logic inside isolated temp directories. Trigger: code reads and writes local files. Sev: medium. Tool: `pytest`
- `pytest-capsys-output-check` — Capture and assert CLI stdout and stderr. Trigger: console tooling behavior specified. Sev: low. Tool: `pytest`
- `pytest-monkeypatch-env-vars` — Control environment variables per test safely. Trigger: behavior keyed on env configuration. Sev: medium. Tool: `pytest`
- `pytest-inherited-behavior-subclasses` — Test subclass contracts through shared suites. Trigger: polymorphic hierarchy with common contract. Sev: medium. Tool: `pytest`
- `pytest-doctest-embedded-examples` — Verify docstring examples stay truthful. Trigger: public documentation examples exist. Sev: low. Tool: `pytest`
- `pytest-marker-selection-matrix` — Organize markers to slice suites by feature. Trigger: CI needs targeted test selection. Sev: low. Tool: `pytest`
- `pytest-warning-strict-filters` — Turn warnings into errors catching deprecations. Trigger: dependency upgrade in flight. Sev: medium. Tool: `pytest`
- `pytest-overload-dispatch-cases` — Test dispatch across typed function overloads. Trigger: function branches on argument types. Sev: medium. Tool: `pytest`
- `pytest-state-transition-sequences` — Walk entity lifecycle transitions in sequence. Trigger: state machine defined for entity. Sev: high. Tool: `pytest`
- `pytest-idempotency-repeat-check` — Run operation twice asserting identical outcome. Trigger: handler must be retry-safe. Sev: high. Tool: `pytest`
- `pytest-value-semantics-containers` — Verify equality, hashing, and copy semantics. Trigger: models used as keys or compared. Sev: low. Tool: `pytest`
- `pytest-error-message-contract` — Assert error messages match documented format. Trigger: users script against message text. Sev: low. Tool: `pytest`
- `pytest-random-order-isolation` — Detect inter-test state via random ordering. Trigger: order-dependent flaky failures observed. Sev: medium. Tool: `pytest`
- `pytest-cli-entrypoint-invocation` — Exercise CLI entrypoints in-process end to end. Trigger: command-line flags added or changed. Sev: medium. Tool: `pytest`
- `pytest-asyncio-coroutine-tests` — Test async coroutines on managed event loops. Trigger: async function added or changed. Sev: critical. Tool: `pytest-asyncio`
- `pytest-asyncio-task-cancellation` — Verify cancellation semantics and cleanup paths. Trigger: background tasks have cancellation branches. Sev: high. Tool: `pytest-asyncio`
- `pytest-asyncio-timeout-deadline` — Assert async operations honor deadlines. Trigger: hang reports under slow dependencies. Sev: high. Tool: `pytest-asyncio`
- `pytest-asyncio-concurrent-tasks` — Drive concurrent coroutines to surface races. Trigger: shared state touched by async tasks. Sev: medium. Tool: `pytest-asyncio`
- `pytest-asyncio-exception-groups` — Assert grouped async exception aggregation behavior. Trigger: fan-out tasks collect multiple failures. Sev: medium. Tool: `pytest-asyncio`
- `unittest-legacy-suite-extension` — Extend existing unittest suites consistently. Trigger: codebase standard is unittest. Sev: medium. Tool: `unittest`
- `unittest-pure-logic-no-doubles` — Test deterministic logic without test doubles. Trigger: pure functions isolated from IO. Sev: medium. Tool: `unittest`
- `time-machine-frozen-clock` — Freeze clock for deterministic time-dependent logic. Trigger: scheduler or expiry logic added. Sev: high. Tool: `time-machine`
- `time-machine-deadline-traversal` — Step time across retries and TTL windows. Trigger: backoff or lease expiry behavior matters. Sev: medium. Tool: `time-machine`
- `time-machine-tz-dst-boundaries` — Test timezone and DST boundary handling. Trigger: date logic spans timezones. Sev: high. Tool: `time-machine`

## 3. Test-Double & State-Isolation Testing

Mocking, stubbing, spying, and in-memory faking of external dependencies while enforcing zero network and disk leakage from tests.

Tool belt: `unittest.mock`, `fakeredis`, `pytest-socket`, `responses`

### Granular test types

- `responses-http-stubbing` — Stub HTTP client calls with canned responses. Trigger: tests must avoid live third-party APIs. Sev: high. Tool: `responses`
- `responses-status-code-matrix` — Simulate 4xx, 5xx, and rate-limit responses. Trigger: retry and error handling verified. Sev: high. Tool: `responses`
- `responses-request-match-strict` — Match requests by URL, headers, and body. Trigger: request shape is contractual. Sev: medium. Tool: `responses`
- `responses-throttle-retry-replay` — Replay throttled responses to verify backoff. Trigger: rate-limit retry policy changed. Sev: medium. Tool: `responses`
- `responses-binary-multipart-fixtures` — Serve binary and multipart fixture payloads. Trigger: upload or download logic added. Sev: low. Tool: `responses`
- `mock-call-contract-assertions` — Assert call args, order, and counts. Trigger: collaboration protocol between objects matters. Sev: medium. Tool: `unittest.mock`
- `mock-spec-autospeccing-safety` — Use specced mocks tracking real signatures. Trigger: mocks drift from refactored interfaces. Sev: high. Tool: `unittest.mock`
- `mock-side-effect-exceptions` — Simulate dependency failures via side effects. Trigger: failure propagation paths need coverage. Sev: medium. Tool: `unittest.mock`
- `mock-patch-scoped-isolation` — Patch precisely with context-managed cleanup. Trigger: global state leaked between tests. Sev: high. Tool: `unittest.mock`
- `mock-async-coroutine-doubles` — Mock async functions and awaitable clients. Trigger: async code depends on remote clients. Sev: high. Tool: `unittest.mock`
- `mock-spy-observation-only` — Spy on collaborators without altering behavior. Trigger: verify interaction, not output. Sev: low. Tool: `unittest.mock`
- `mock-partial-wrap-delegate` — Wrap select methods, delegate remaining behavior. Trigger: large dependency, narrow tested behavior. Sev: medium. Tool: `unittest.mock`
- `mock-filesystem-path-isolation` — Redirect filesystem access into temp directories. Trigger: code must never write outside sandbox. Sev: high. Tool: `unittest.mock`
- `mock-sleep-neutralization` — Neutralize sleeps keeping the suite fast. Trigger: backoff sleeps slow test runs. Sev: low. Tool: `unittest.mock`
- `mock-database-session-fake` — Fake DB sessions with scripted query results. Trigger: repository logic tested without database. Sev: high. Tool: `unittest.mock`
- `mock-notification-channel-fakes` — Fake webhook and notification senders. Trigger: side-effect channels must stay silent. Sev: medium. Tool: `unittest.mock`
- `mock-config-object-injection` — Inject fake config instead of mutating env. Trigger: tests mutate process environment unsafely. Sev: medium. Tool: `unittest.mock`
- `mock-streaming-iterator-fakes` — Provide fake iterators for streaming interfaces. Trigger: streaming consumption logic under test. Sev: low. Tool: `unittest.mock`
- `mock-di-seam-wiring` — Wire fakes through injection seams, not patching. Trigger: architecture prefers constructor injection. Sev: low. Tool: `unittest.mock`
- `fakeredis-cache-behavior` — Exercise Redis logic against in-memory server. Trigger: caching or queue code touches Redis. Sev: high. Tool: `fakeredis`
- `fakeredis-ttl-expiry-simulation` — Simulate key expiry and TTL semantics. Trigger: TTL-driven eviction or refresh logic. Sev: medium. Tool: `fakeredis`
- `fakeredis-pubsub-streams` — Test pub/sub and streams in memory. Trigger: event-driven components consume streams. Sev: medium. Tool: `fakeredis`
- `fakeredis-pipeline-atomicity` — Verify pipelines and transactions stay atomic. Trigger: multi-key updates must be atomic. Sev: high. Tool: `fakeredis`
- `fakeredis-lua-script-execution` — Test Lua scripts and atomic command blocks. Trigger: server-side scripts gate consistency. Sev: medium. Tool: `fakeredis`
- `fakeredis-cluster-mode-semantics` — Emulate cluster-mode command restrictions. Trigger: deployment targets Redis cluster. Sev: medium. Tool: `fakeredis`
- `pytest-socket-disable-all-egress` — Hard-disable network sockets across suite. Trigger: zero-network guarantee required in CI. Sev: critical. Tool: `pytest-socket`
- `pytest-socket-loopback-allowlist` — Allow only loopback for local fixtures. Trigger: local test server legitimately needed. Sev: medium. Tool: `pytest-socket`
- `pytest-socket-dns-block-guard` — Block DNS resolution to catch leaks. Trigger: hidden hostname lookups suspected. Sev: high. Tool: `pytest-socket`
- `pytest-socket-egress-audit` — Audit suite for network egress attempts. Trigger: intermittent CI failures from network. Sev: medium. Tool: `pytest-socket`
- `responses-passthrough-decline-guard` — Ensure real network calls fail loudly. Trigger: accidental live calls suspected. Sev: high. Tool: `responses`

## 4. Property-Based, Fuzzing & Symbolic Verification

Mathematical invariant testing over generated inputs, coverage-guided fuzzing of untrusted inputs, and SMT-based symbolic verification of contracts.

Tool belt: `hypothesis`, `atheris`, `CrossHair`

### Granular test types

- `hypothesis-roundtrip-inversion` — Verify encode/decode and serialize/parse invert. Trigger: pair of inverse transformations defined. Sev: high. Tool: `hypothesis`
- `hypothesis-oracle-equivalence` — Compare optimized path against reference implementation. Trigger: refactor must preserve behavior exactly. Sev: high. Tool: `hypothesis`
- `hypothesis-invariant-postconditions` — Assert invariants hold for arbitrary inputs. Trigger: documented invariant or formal contract. Sev: high. Tool: `hypothesis`
- `hypothesis-edge-value-tour` — Explore unicode, negatives, NaN, and empties. Trigger: parser mishandles extreme edge values. Sev: high. Tool: `hypothesis`
- `hypothesis-stateful-rule-machine` — Model systems as stateful rule sequences. Trigger: ordered operations mutate object state. Sev: medium. Tool: `hypothesis`
- `hypothesis-composite-strategies` — Build reusable strategies for domain types. Trigger: recurring domain objects in properties. Sev: low. Tool: `hypothesis`
- `hypothesis-shrinking-minimal-repro` — Use shrinking for minimal failing examples. Trigger: property failure needs small repro. Sev: medium. Tool: `hypothesis`
- `hypothesis-derandomized-ci-stability` — Stabilize CI with seeded examples and databases. Trigger: property failures not reproducible. Sev: medium. Tool: `hypothesis`
- `hypothesis-metamorphic-relations` — Assert output relations under input transformations. Trigger: no oracle, but transform invariants exist. Sev: medium. Tool: `hypothesis`
- `hypothesis-schema-model-generation` — Generate schema-bound models and payloads. Trigger: schema validation logic is broad. Sev: medium. Tool: `hypothesis`
- `hypothesis-deadline-performance-guard` — Enforce deadlines catching slow examples. Trigger: performance regressions on outlier inputs. Sev: low. Tool: `hypothesis`
- `hypothesis-recursive-structure-generation` — Generate recursive trees and nested graphs. Trigger: algorithms traverse recursive structures. Sev: medium. Tool: `hypothesis`
- `hypothesis-temporal-strategy-coverage` — Generate datetimes with DST and timezone coverage. Trigger: temporal logic has boundary pitfalls. Sev: medium. Tool: `hypothesis`
- `hypothesis-model-based-mirror` — Compare complex implementation to simple model. Trigger: query layer mimics set operations. Sev: medium. Tool: `hypothesis`
- `hypothesis-async-operation-properties` — Property-test async queues and caches. Trigger: async component semantics specified. Sev: medium. Tool: `hypothesis`
- `hypothesis-idempotence-property` — Verify repeated application yields stable results. Trigger: consumers must be idempotent. Sev: medium. Tool: `hypothesis`
- `hypothesis-grammar-parser-fuzz` — Combine generation and fuzzing for grammars. Trigger: DSL or mini-language introduced. Sev: high. Tool: `hypothesis`
- `atheris-parser-crash-fuzzing` — Fuzz parsers for crashes and memory errors. Trigger: untrusted bytes reach custom parsers. Sev: critical. Tool: `atheris`
- `atheris-deserialization-fuzzing` — Fuzz deserialization of external payloads. Trigger: formats decoded from network or files. Sev: critical. Tool: `atheris`
- `atheris-sanitizer-crash-triage` — Triage sanitizer findings into minimal cases. Trigger: fuzzer reports intermittent crashes. Sev: high. Tool: `atheris`
- `atheris-corpus-regression-seeding` — Maintain corpus and regression inputs from findings. Trigger: fuzz artifacts must gate merges. Sev: medium. Tool: `atheris`
- `atheris-encoding-unicode-fuzzing` — Fuzz encoding and decoding boundaries. Trigger: charset conversion code paths present. Sev: medium. Tool: `atheris`
- `atheris-file-format-fuzzing` — Fuzz file-format readers with malformed inputs. Trigger: imports user-supplied documents. Sev: high. Tool: `atheris`
- `crosshair-symbolic-contract-verification` — Verify pre/postconditions via SMT reasoning. Trigger: annotated contracts on pure functions. Sev: high. Tool: `CrossHair`
- `crosshair-counterexample-witnesses` — Produce counterexamples for violated contracts. Trigger: proof-like correctness assurance demanded. Sev: high. Tool: `CrossHair`
- `crosshair-stdlib-equivalence-checks` — Check reimplementations against stdlib semantics. Trigger: custom utilities mirror stdlib functions. Sev: medium. Tool: `CrossHair`
- `crosshair-exception-freedom-proof` — Prove absence of unexpected exceptions. Trigger: crash-free guarantee required. Sev: high. Tool: `CrossHair`
- `crosshair-dataclass-invariant-smt` — Verify dataclass invariants symbolically. Trigger: model invariants stated formally. Sev: medium. Tool: `CrossHair`
- `crosshair-loop-boundary-reasoning` — Verify loop invariants and termination bounds. Trigger: numeric loops with tight bounds. Sev: medium. Tool: `CrossHair`
- `crosshair-monotonicity-contract-check` — Verify monotonicity and ordering properties symbolically. Trigger: ranking or ordering logic changed. Sev: low. Tool: `CrossHair`
## 5. Contract, Schema & Wire-Serialization Testing

Verifies data models, API schemas, wire formats, and cross-service contracts stay compatible and correctly enforced.

Tool belt: `pydantic`, `schemathesis`, `pact-python`, `syrupy`

### Granular test types

- `pydantic-field-constraints` — Enforces type, bounds, and constraint rules on model fields. Trigger: Ticket tightens accepted input ranges or types. Sev: high. Tool: `pydantic`
- `pydantic-strict-mode` — Rejects implicit coercions like numeric strings becoming ints. Trigger: Contract bans silent type coercion at boundaries. Sev: high. Tool: `pydantic`
- `pydantic-alias-roundtrip` — Verifies field aliases serialize and parse wire names correctly. Trigger: API renames fields while keeping internal names. Sev: medium. Tool: `pydantic`
- `pydantic-discriminated-unions` — Validates tagged union payloads parse to correct variants. Trigger: Payload gains polymorphic event or message types. Sev: high. Tool: `pydantic`
- `pydantic-nested-depth` — Checks deeply nested payloads populate and validate fully. Trigger: Response embeds multi-level nested structures. Sev: medium. Tool: `pydantic`
- `pydantic-invalid-input-rejection` — Confirms malformed payloads fail with actionable error details. Trigger: Downstream reports crashes from bad client data. Sev: critical. Tool: `pydantic`
- `pydantic-default-drift` — Catches changed defaults silently altering serialized output. Trigger: Reviewer alters a field default value. Sev: low. Tool: `pydantic`
- `openapi-spec-drift` — Diffs generated OpenAPI spec against committed published contract. Trigger: Endpoint change not reflected in published spec. Sev: high. Tool: `schemathesis`
- `openapi-fuzz-property-testing` — Generates adversarial payloads from schema to force 500s. Trigger: Endpoint accepts user-authored request bodies. Sev: critical. Tool: `schemathesis`
- `openapi-response-shape` — Asserts response bodies match declared schema, not just status. Trigger: Consumers break on unexpected response fields. Sev: high. Tool: `schemathesis`
- `openapi-parameter-validation` — Checks query, header, path parameters honor schema constraints. Trigger: Handler ignores declared parameter limits. Sev: medium. Tool: `schemathesis`
- `openapi-nullability-ambiguity` — Flags required-nullable fields and missing examples confusing generators. Trigger: Spec ambiguity causes client generator confusion. Sev: low. Tool: `schemathesis`
- `graphql-schema-breaking-change` — Detects removed fields and changed nullability in GraphQL schema. Trigger: GraphQL schema PR touches public types. Sev: critical. Tool: `schemathesis`
- `graphql-persisted-query-compat` — Runs pinned client operations against evolved GraphQL schema. Trigger: Mobile clients rely on stored query documents. Sev: high. Tool: `schemathesis`
- `pact-consumer-expectations` — Runs consumer-defined interaction expectations against provider. Trigger: Consumer publishes new expected interaction. Sev: critical. Tool: `pact-python`
- `pact-provider-verification` — Verifies provider still satisfies all consumer pacts before release. Trigger: Provider deploy queued to shared environment. Sev: critical. Tool: `pact-python`
- `pact-message-contracts` — Validates async message payloads against pact message expectations. Trigger: Queue consumers and producers evolve independently. Sev: high. Tool: `pact-python`
- `pact-provider-state-setup` — Sets up and tears down provider state handlers reliably. Trigger: Verification fails on stateful endpoints. Sev: medium. Tool: `pact-python`
- `pact-version-negotiation` — Checks API version headers honored across staged releases. Trigger: API versions published for phased consumer migration. Sev: medium. Tool: `pact-python`
- `protobuf-wire-golden-snapshot` — Snapshots serialized message bytes to catch wire-format drift. Trigger: Proto field numbers or types changed. Sev: critical. Tool: `syrupy`
- `wire-decoded-field-validation` — Validates decoded protobuf payloads against modeled field rules. Trigger: Wire message gains optional nested fields. Sev: high. Tool: `pydantic`
- `grpc-transcoding-schema` — Validates REST transcoding of gRPC services against spec. Trigger: Gateway exposes new gRPC method over HTTP. Sev: medium. Tool: `schemathesis`
- `golden-response-snapshot` — Pins full response bodies as snapshot baselines across refactors. Trigger: Refactor must not alter external payloads. Sev: high. Tool: `syrupy`
- `golden-error-envelope` — Locks error response shape, codes, and message structure. Trigger: Consumers parse error codes for retries. Sev: high. Tool: `syrupy`
- `golden-pii-redaction` — Ensures serialized output excludes sensitive or regulated fields. Trigger: Compliance audit on exported payloads. Sev: critical. Tool: `syrupy`
- `datetime-serialization-normalization` — Verifies timestamps serialize to agreed timezone-aware ISO formats. Trigger: Consumer chokes on naive datetime strings. Sev: medium. Tool: `pydantic`
- `enum-contract-stability` — Flags enum member removals or value reordering across versions. Trigger: New enum value added for feature rollout. Sev: medium. Tool: `pydantic`
- `payload-size-limit-contract` — Confirms oversized payloads rejected per agreed size limits. Trigger: Broker drops messages exceeding size caps. Sev: medium. Tool: `pydantic`

## 6. Integration & Ephemeral Infrastructure Testing

Exercises real databases, caches, brokers, cloud emulators, and migrations inside disposable, production-like environments.

Tool belt: `testcontainers`, `moto`, `respx`, `pytest-alembic`, `pytest-postgresql`

### Granular test types

- `postgres-container-lifecycle` — Boots real Postgres per session and tears down cleanly. Trigger: Query logic depends on Postgres-specific behavior. Sev: high. Tool: `testcontainers`
- `redis-cache-behavior` — Validates cache read-through, TTL expiry, and invalidation flows. Trigger: Stale reads or stampede reported in production. Sev: high. Tool: `testcontainers`
- `kafka-producer-consumer-flow` — Produces and consumes real messages across consumer groups. Trigger: Pipeline loses or duplicates events under load. Sev: critical. Tool: `testcontainers`
- `rabbitmq-routing-acks` — Verifies publish, ack, nack, and dead-letter routing behavior. Trigger: Poison messages loop in queue retries. Sev: high. Tool: `testcontainers`
- `container-network-isolation` — Ensures containers reach only declared service dependencies. Trigger: Test passes only via unintended external service. Sev: medium. Tool: `testcontainers`
- `container-reuse-performance` — Reuses containers across runs without state bleeding between tests. Trigger: Suite runtime balloons from container startup. Sev: low. Tool: `testcontainers`
- `container-init-seeding` — Applies seed SQL and config scripts on container start. Trigger: Tests need reference data or schema baseline. Sev: low. Tool: `testcontainers`
- `s3-roundtrip-operations` — Uploads, lists, versions, and deletes objects against mocked S3. Trigger: Object storage logic ships without integration coverage. Sev: high. Tool: `moto`
- `dynamodb-access-patterns` — Checks DynamoDB query pagination and condition expression semantics. Trigger: Item access patterns changed for new feature. Sev: high. Tool: `moto`
- `sqs-delivery-semantics` — Verifies visibility timeout, batching, and FIFO ordering behavior. Trigger: Worker crashes reprocess already-handled jobs. Sev: medium. Tool: `moto`
- `sts-credential-flows` — Simulates credential resolution and assumed-role session flows. Trigger: Service adds cross-account resource access. Sev: medium. Tool: `moto`
- `aws-error-injection` — Forces throttling and error codes into cloud client calls. Trigger: Retry and backoff behavior must be proven. Sev: high. Tool: `moto`
- `iam-policy-boundaries` — Asserts least-privilege policies permit exactly intended actions. Trigger: Security review of expanded cloud permissions. Sev: high. Tool: `moto`
- `respx-external-http-stubs` — Mocks third-party HTTP APIs at transport with call assertions. Trigger: External API calls make tests flaky or costly. Sev: medium. Tool: `respx`
- `respx-retry-backoff-simulation` — Simulates timeouts and 5xx responses to verify retry policies. Trigger: Circuit breaker behavior needs executable proof. Sev: high. Tool: `respx`
- `respx-outbound-headers` — Asserts outbound requests carry auth and idempotency headers. Trigger: Partner rejects requests missing idempotency keys. Sev: high. Tool: `respx`
- `alembic-upgrade-to-head` — Runs all migrations from base to head on clean database. Trigger: Fresh environments fail to reach current schema. Sev: critical. Tool: `pytest-alembic`
- `alembic-downgrade-path` — Verifies downgrade steps reverse each upgrade cleanly. Trigger: Rollback plan required for risky migration. Sev: high. Tool: `pytest-alembic`
- `alembic-single-head` — Detects divergent migration branches requiring a merge revision. Trigger: Two branches both added migration files. Sev: medium. Tool: `pytest-alembic`
- `alembic-data-migration-correctness` — Validates backfill transformations preserve row-level data correctness. Trigger: Migration backfills or reshapes existing data. Sev: critical. Tool: `pytest-alembic`
- `alembic-rerun-idempotency` — Confirms rerunning migrations is safe and effectively no-op. Trigger: Deploy tooling may retry failed release steps. Sev: medium. Tool: `pytest-alembic`
- `schema-model-consistency` — Database schema matches ORM models and migration history. Trigger: Drift suspected between models and deployed schema. Sev: high. Tool: `pytest-alembic`
- `postgres-fixture-isolation` — Provisions template-database fixtures with per-test rollback isolation. Trigger: Tests must not observe each other's writes. Sev: medium. Tool: `pytest-postgresql`
- `postgres-constraint-enforcement` — Exercises unique, foreign key, check constraints on real engine. Trigger: ORM permits state the database rejects. Sev: high. Tool: `pytest-postgresql`
- `index-query-plan-regression` — Confirms hot queries keep using intended indexes and plans. Trigger: Slow-query alert after schema or ORM change. Sev: medium. Tool: `pytest-postgresql`
- `transaction-rollback-semantics` — Verifies commit and rollback boundaries under nested transactions. Trigger: Partial writes observed after failure paths. Sev: critical. Tool: `testcontainers`
- `connection-pool-exhaustion` — Stresses pool limits, checkout waits, and leaked connections. Trigger: Incidents cite pool exhaustion under burst load. Sev: high. Tool: `testcontainers`
- `object-storage-emulator-roundtrip` — Round-trips multipart uploads through local cloud storage emulator. Trigger: Storage client upgraded or endpoint config changed. Sev: medium. Tool: `moto`

## 7. API, End-to-End (E2E), Acceptance (BDD) & UI Testing

Verifies complete user workflows across ASGI/WSGI apps, real browsers, CLIs/TUIs, and Gherkin business specifications.

Tool belt: `httpx`, `playwright`, `pytest-bdd`, `tavern`, `typer.testing`

### Granular test types

- `asgi-endpoint-crud` — Full CRUD round-trips against live ASGI app via transport. Trigger: New resource endpoint added to service. Sev: high. Tool: `httpx`
- `httpx-auth-flows` — Exercises login, token refresh, and scoped access end to end. Trigger: Auth middleware or token format changed. Sev: critical. Tool: `httpx`
- `httpx-multipart-upload` — Uploads files with multipart encoding and verifies stored results. Trigger: File ingestion feature ships to users. Sev: medium. Tool: `httpx`
- `httpx-streaming-response` — Validates chunked and SSE responses consumed incrementally. Trigger: Endpoint streams large or live datasets. Sev: medium. Tool: `httpx`
- `httpx-pagination-contract` — Walks paginated collections verifying cursor and offset correctness. Trigger: Listing endpoints grow or add filters. Sev: medium. Tool: `httpx`
- `tavern-yaml-journeys` — Declarative multi-step API journeys with response value chaining. Trigger: QA owns API regression without Python skills. Sev: medium. Tool: `tavern`
- `tavern-token-chaining` — Chains authentication tokens across YAML test stages correctly. Trigger: Scenarios span authenticated and public endpoints. Sev: medium. Tool: `tavern`
- `playwright-navigation-routes` — Drives real browser through routes, redirects, and history. Trigger: Frontend routing changes affect deep links. Sev: high. Tool: `playwright`
- `playwright-form-workflow` — Fills, submits, and validates complex multi-step forms. Trigger: Checkout or onboarding wizard changes. Sev: critical. Tool: `playwright`
- `playwright-visual-regression` — Snapshots rendered pages to catch unintended UI drift. Trigger: Design system or CSS overhaul merged. Sev: low. Tool: `playwright`
- `playwright-cross-browser` — Runs identical journeys across Chromium, Firefox, and WebKit. Trigger: Browser-specific bugs reported by users. Sev: medium. Tool: `playwright`
- `playwright-accessibility-roles` — Interacts via roles and labels, asserting accessible semantics. Trigger: Accessibility audit findings must not regress. Sev: medium. Tool: `playwright`
- `playwright-deterministic-waits` — Waits on network responses and elements, never sleeps. Trigger: Flaky timing failures on slow CI runners. Sev: medium. Tool: `playwright`
- `playwright-viewport-responsive` — Verifies responsive layouts at device breakpoints. Trigger: Mobile users report overlapping or cut-off UI. Sev: low. Tool: `playwright`
- `bdd-scenario-to-code` — Maps every Gherkin scenario to executing pytest test code. Trigger: Product adds acceptance criteria in Gherkin. Sev: medium. Tool: `pytest-bdd`
- `bdd-outline-example-coverage` — Runs scenario outlines across all example table rows. Trigger: Example table expands with new market. Sev: low. Tool: `pytest-bdd`
- `bdd-business-rule-acceptance` — Encodes stakeholder-approved business rules as executable specifications. Trigger: Pricing or compliance rules become contractual. Sev: high. Tool: `pytest-bdd`
- `bdd-step-isolation` — Shared steps stay context-safe across independently running features. Trigger: Step definitions collide or leak state. Sev: low. Tool: `pytest-bdd`
- `acceptance-signoff-pack` — Curated scenario run mapped to requirement IDs for signoff. Trigger: Release requires documented acceptance evidence. Sev: low. Tool: `pytest-bdd`
- `cli-exit-codes` — Asserts Typer CLI exit codes for success and each failure mode. Trigger: CI scripting depends on command exit status. Sev: high. Tool: `typer.testing`
- `cli-output-formats` — Verifies table and JSON output modes remain parseable. Trigger: Downstream tooling consumes CLI JSON output. Sev: medium. Tool: `typer.testing`
- `cli-input-validation` — Checks bad flags produce helpful errors, never tracebacks. Trigger: Support tickets about confusing CLI errors. Sev: low. Tool: `typer.testing`
- `e2e-cross-service-journey` — Chains API and UI steps through one full workflow. Trigger: Feature spans frontend, backend, and worker. Sev: critical. Tool: `playwright`
- `e2e-smoke-critical-path` — Minimal login-to-value journey gating every deployment. Trigger: Release checklist requires smoke pass first. Sev: critical. Tool: `httpx`
- `e2e-idempotent-replay` — Repeats workflow to confirm no duplicate side effects. Trigger: Users double-click submit or retry requests. Sev: high. Tool: `httpx`
- `e2e-seeded-environment` — Runs suites against staging-like environment with realistic seeded data. Trigger: Bug reproduces only with realistic data volume. Sev: medium. Tool: `httpx`

## 8. Concurrency, Race & Free-Threading Stress Testing

Hunts thread-safety bugs, async deadlocks, deterministic-interleaving failures, and GIL-free execution races under stress.

Tool belt: `pytest-run-parallel`, `frontrun`, `pytest-timeout`

### Granular test types

- `parallel-suite-execution` — Runs whole suites concurrently to expose cross-test shared state. Trigger: Green tests fail when CI parallelizes. Sev: high. Tool: `pytest-run-parallel`
- `hot-loop-race-stress` — Repeats suspect code thousands of times across threads. Trigger: Race reported once in production, unreproducible. Sev: critical. Tool: `frontrun`
- `forced-interleaving-repro` — Pins thread schedules to reproduce ordering-dependent failures reliably. Trigger: Race fix needs a permanent regression test. Sev: high. Tool: `frontrun`
- `check-then-act-window` — Exposes check-then-act gaps on shared counters and caches. Trigger: Metrics show lost updates or duplicate work. Sev: critical. Tool: `frontrun`
- `lazy-init-partial-state` — Stresses lazy singletons for half-initialized object reads. Trigger: Occasional unconfigured instance on cold start. Sev: critical. Tool: `frontrun`
- `shared-fixture-mutation` — Catches tests concurrently mutating module-scoped fixtures. Trigger: Fixture assertions fail only under parallel workers. Sev: high. Tool: `pytest-run-parallel`
- `unsafe-collection-concurrency` — Detects unguarded dict, list, queue use across writers. Trigger: Runtime warns about unsynchronized collection iteration. Sev: high. Tool: `frontrun`
- `lock-ordering-deadlock` — Bounds nested-lock acquisition scenarios with watchdog timeouts. Trigger: Threads occasionally freeze holding two locks. Sev: critical. Tool: `pytest-timeout`
- `async-deadlock-bound` — Fails event-loop waits exceeding hard time limits. Trigger: CI job sporadically hangs with no output. Sev: high. Tool: `pytest-timeout`
- `hang-diagnostic-failure` — Turns infinite hangs into failures with diagnostic output. Trigger: Nightly suite stalls until cluster reaps it. Sev: medium. Tool: `pytest-timeout`
- `connection-pool-race` — Stresses concurrent acquire and release of pooled resources. Trigger: Pool leaks connections after error paths. Sev: high. Tool: `pytest-run-parallel`
- `producer-consumer-burst` — Drives queues with bursty concurrent producers and consumers. Trigger: Workers skip or duplicate jobs at peak. Sev: high. Tool: `pytest-run-parallel`
- `graceful-shutdown-race` — Triggers shutdown while threads hold in-flight operations. Trigger: Deploy loses recently accepted work. Sev: high. Tool: `frontrun`
- `double-submit-idempotency` — Fires identical concurrent requests to verify deduplication. Trigger: Payments occasionally double-apply on retry. Sev: critical. Tool: `frontrun`
- `read-write-lock-fairness` — Checks writer starvation and fairness under mixed load. Trigger: Writers starve on read-heavy endpoints. Sev: medium. Tool: `pytest-run-parallel`
- `async-cancellation-consistency` — Cancellation mid-await must leave shared state consistent. Trigger: Cancelled task traceback leaves partial writes. Sev: high. Tool: `frontrun`
- `gather-exception-isolation` — One failed concurrent task must not mask siblings. Trigger: Batch job loses unrelated results on error. Sev: medium. Tool: `pytest-timeout`
- `gil-free-race-scan` — Exercises hot paths under free-threaded CPython builds. Trigger: Migration to GIL-free Python planned. Sev: critical. Tool: `pytest-run-parallel`
- `subinterpreter-isolation` — Verifies per-interpreter and multiprocessing state isolation holds. Trigger: GIL-free rollout moves work to isolated interpreters. Sev: medium. Tool: `pytest-run-parallel`
- `compound-update-atomicity` — Multi-step shared-state updates commit fully or not at all. Trigger: Audit log disagrees with final state. Sev: critical. Tool: `frontrun`
- `race-regression-freeze` — Freezes reproduced interleaving as a named regression case. Trigger: Fixed race must never silently return. Sev: high. Tool: `frontrun`
- `parallel-safe-hooks` — Test hooks and reporters survive concurrent execution cleanly. Trigger: Custom pytest plugins corrupt output in parallel. Sev: low. Tool: `pytest-run-parallel`
- `latency-under-contention` — Bounds operation latency while threads contend hot locks. Trigger: p99 latency spikes correlate with concurrency. Sev: medium. Tool: `pytest-timeout`
- `timeout-budget-escalation` — Verifies per-test timeout budgets escalate correctly in CI. Trigger: Slow tests mask true deadlock failures. Sev: low. Tool: `pytest-timeout`
# Batch C — Families 9–12

## 9. Performance, Memory & Resource Ceiling Testing

Verifies that Python services meet latency, memory, throughput, and resource-consumption budgets under controlled and loaded conditions.

Tool belt: `pytest-benchmark`, `pytest-memray`, `memray`, `objgraph`, `pympler`, `locust`, `psutil`, `py-spy`, `scalene`, `asv`, `pytest-django`, `sqlalchemy`

### Granular test types

- `latency-regression-benchmark` — Detect p50/p99 latency regressions against stored benchmark baselines. Trigger: Hot path refactor or performance-sensitive dependency upgrade merged. Sev: high. Tool: `pytest-benchmark`
- `benchmark-baseline-gate` — Fail CI when benchmark exceeds baseline deviation thresholds. Trigger: Contract promises per-endpoint latency budget. Sev: high. Tool: `pytest-benchmark`
- `benchmark-noise-control` — Disable GC and pin calibration rounds for stable measurements. Trigger: Benchmark deltas flapping between identical commits. Sev: low. Tool: `pytest-benchmark`
- `cold-start-latency-measure` — Measure first-request latency after fresh process or worker start. Trigger: Serverless or recycled-worker startup SLA. Sev: medium. Tool: `pytest-benchmark`
- `allocation-tracking-per-test` — Track allocations per call; fail on increase beyond budget. Trigger: Memory budget clause in service contract. Sev: high. Tool: `pytest-memray`
- `heap-ceiling-enforcement` — Hard-fail tests exceeding fixed heap memory ceiling. Trigger: Container memory limits documented in deploy spec. Sev: critical. Tool: `pytest-memray`
- `native-memory-profiling` — Profile native and C-extension allocations leaking under load. Trigger: RSS grows while Python heap stays flat. Sev: high. Tool: `memray`
- `leak-growth-across-iterations` — Detect object-count growth over repeated invocations of suspect code. Trigger: Long-running worker OOM after hours. Sev: high. Tool: `objgraph`
- `reference-cycle-detection` — Find uncollectable reference cycles retaining memory after gc. Trigger: gc.collect fails to free expected objects. Sev: medium. Tool: `objgraph`
- `object-count-snapshot-diff` — Diff type-level object counts before and after tests. Trigger: Suspected cache or registry leak. Sev: medium. Tool: `pympler`
- `memory-fragmentation-check` — RSS-to-heap ratio stays stable after allocation churn cycles. Trigger: Allocator fragmentation suspected in long runners. Sev: low. Tool: `memray`
- `n1-query-detection` — Fail when one request triggers more queries than budgeted. Trigger: List endpoint slow with large result sets. Sev: high. Tool: `sqlalchemy`
- `query-count-regression-gate` — CI gate on query-count delta versus recorded baseline. Trigger: ORM migration touching hot list views. Sev: high. Tool: `pytest-django`
- `load-test-sustained-rps` — Sustain target RPS; assert error rate stays budgeted. Trigger: Capacity plan states launch SLA. Sev: critical. Tool: `locust`
- `spike-load-test` — Sudden traffic spikes must not error or cascade failures. Trigger: Campaign launch or webhook burst expected. Sev: high. Tool: `locust`
- `soak-endurance-test` — Long steady load detects slow leaks and degradation. Trigger: Service advertised for week-long uptime. Sev: high. Tool: `locust`
- `stress-breakpoint-finding` — Find load level where latency or errors breach thresholds. Trigger: Autoscaling limits being tuned. Sev: medium. Tool: `locust`
- `backpressure-under-overload` — Overload sheds work gracefully without unbounded queue growth. Trigger: Upstream retry storms documented in design. Sev: high. Tool: `locust`
- `cache-hit-ratio-under-load` — Assert cache hit ratio and backend offload under load. Trigger: Cache tier added to meet latency SLA. Sev: medium. Tool: `locust`
- `concurrency-scalability-check` — Throughput scales with worker count until expected ceiling. Trigger: Horizontal scaling claims in design doc. Sev: medium. Tool: `locust`
- `cost-ceiling-per-request` — Computed cost per request stays under FinOps cap. Trigger: FinOps budget line in contract. Sev: medium. Tool: `locust`
- `fd-leak-check` — Open file descriptors return to baseline after operations. Trigger: Too many open files in production. Sev: critical. Tool: `psutil`
- `connection-pool-leak-check` — Pooled DB and HTTP connections release after use. Trigger: Pool exhaustion alerts under moderate load. Sev: critical. Tool: `psutil`
- `thread-leak-detection` — Thread count stable after repeated operations complete. Trigger: Worker memory grows with thread count. Sev: high. Tool: `psutil`
- `socket-handle-audit` — No sockets left unclosed across exercised scenarios. Trigger: Ephemeral port exhaustion in staging. Sev: high. Tool: `psutil`
- `subprocess-reap-check` — Child processes reaped; no zombies after job runs. Trigger: Task workers spawn shell commands. Sev: medium. Tool: `psutil`
- `cpu-hotspot-profiling` — Sampled profiles pinpoint hotspots in slow code paths. Trigger: Endpoint exceeds latency budget; cause unknown. Sev: medium. Tool: `py-spy`
- `gc-pause-impact` — Quantify GC pause contribution to tail latency. Trigger: p99 spikes without CPU saturation. Sev: low. Tool: `py-spy`
- `line-level-mixed-profiling` — Attribute CPU versus allocation cost per source line. Trigger: Deciding optimization before adding cache layer. Sev: low. Tool: `scalene`
- `historical-benchmark-tracking` — Track performance across commit history for core libraries. Trigger: Quarterly performance review of core lib. Sev: low. Tool: `asv`

## 10. Chaos Engineering & Resilience Fault Injection

Injects realistic network, infrastructure, and process faults to prove retries, degradation paths, shutdown semantics, and recovery drills hold.

Tool belt: `toxiproxy-python`, `chaostoolkit`, `pook`, `pytest-xprocess`, `tenacity`, `pytest-postgresql`, `psutil`

### Granular test types

- `injected-network-latency` — Inject latency; verify timeouts fire and UX degrades gracefully. Trigger: Dependency added without timeout configuration. Sev: high. Tool: `toxiproxy-python`
- `latency-jitter-tail-check` — Random jitter exposes fragile timeout budgeting assumptions. Trigger: p99 SLO on cross-service calls. Sev: medium. Tool: `toxiproxy-python`
- `dropped-connection-recovery` — Connections killed mid-flight; clients reconnect and recover cleanly. Trigger: HTTP or DB connection pooling adopted. Sev: critical. Tool: `toxiproxy-python`
- `connection-reset-midstream` — Reset during body transfer; partial reads handled safely. Trigger: Streaming endpoint or large file upload. Sev: high. Tool: `toxiproxy-python`
- `packet-loss-resilience` — Simulated loss verified against retransmission and backoff behavior. Trigger: Lossy region or mobile client targets. Sev: medium. Tool: `toxiproxy-python`
- `bandwidth-throttling-check` — Throttled links keep bulk jobs within deadline budgets. Trigger: Large batch transfer windows in contract. Sev: low. Tool: `toxiproxy-python`
- `dependency-hang-timeout` — Hanging dependency opens circuit breaker on schedule. Trigger: Circuit breaker adopted without failure drills. Sev: high. Tool: `toxiproxy-python`
- `retry-storm-containment` — Retries use jittered backoff; no thundering herd forms. Trigger: Incident caused synchronized retry waves. Sev: high. Tool: `chaostoolkit`
- `circuit-breaker-half-open` — Half-open probes recovery correctly without flooding dependency. Trigger: Breaker configuration change under review. Sev: medium. Tool: `pook`
- `fallback-degradation-check` — Downstream failure triggers cached or default responses. Trigger: Graceful degradation promised in design doc. Sev: high. Tool: `pook`
- `partial-outage-routing` — Single replica failure drains traffic without 5xx spike. Trigger: Rolling deploy or spot-termination policy. Sev: high. Tool: `chaostoolkit`
- `pod-kill-resilience` — Killed pods recover within stated recovery-time objective. Trigger: Quarterly k8s chaos drill scheduled. Sev: high. Tool: `chaostoolkit`
- `network-partition-split` — Partition forces quorum behavior or safe read-only mode. Trigger: Distributed lock or consensus dependency present. Sev: critical. Tool: `chaostoolkit`
- `dns-failure-handling` — DNS outage fails fast using cached resolution. Trigger: DNS flake froze workers previously. Sev: high. Tool: `pook`
- `disk-full-behavior` — Disk exhaustion logs, alerts, and degrades safely. Trigger: Log volume growth ticket open. Sev: medium. Tool: `chaostoolkit`
- `clock-skew-tolerance` — Skewed clocks don't corrupt tokens, leases, or ordering. Trigger: NTP drift incident follow-up action. Sev: medium. Tool: `chaostoolkit`
- `dependency-blackhole` — Blackholed dependency requests time out instead of hanging. Trigger: Missing read timeouts found in audit. Sev: high. Tool: `toxiproxy-python`
- `sigterm-graceful-shutdown` — SIGTERM drains in-flight work before process exit. Trigger: Zero-downtime deploy requirement. Sev: critical. Tool: `pytest-xprocess`
- `sigterm-inflight-completeness` — No requests or tasks lost when terminated mid-processing. Trigger: Payment or idempotent write flows. Sev: critical. Tool: `pytest-xprocess`
- `worker-shutdown-idempotency` — Requeued tasks never double-apply side effects. Trigger: At-least-once queue semantics documented. Sev: high. Tool: `pytest-xprocess`
- `retry-exhaustion-behavior` — Exhausted retries raise typed errors, alert, and halt. Trigger: Retry decorator tuning in review. Sev: medium. Tool: `tenacity`
- `health-flap-recovery` — Flapping health endpoint doesn't cascade instance restarts. Trigger: Liveness probe tuning change. Sev: medium. Tool: `chaostoolkit`
- `backup-restore-drill` — Restore backup into clean environment; verify integrity and RPO. Trigger: Quarterly disaster-recovery drill compliance. Sev: critical. Tool: `chaostoolkit`
- `point-in-time-recovery` — PITR reaches target timestamp with consistent state. Trigger: Database retention policy in contract. Sev: high. Tool: `pytest-postgresql`
- `database-failover-promotion` — Primary loss promotes replica within data-loss budget. Trigger: HA database tier SLA signed. Sev: critical. Tool: `chaostoolkit`
- `region-evacuation-drill` — Simulated region loss reroutes traffic to secondary. Trigger: Multi-region failover design review. Sev: high. Tool: `chaostoolkit`
- `steady-state-hypothesis-check` — Steady-state metrics must hold throughout fault injection. Trigger: Chaos experiment definition under review. Sev: high. Tool: `chaostoolkit`
- `blast-radius-guardrails` — Experiments scoped with abort conditions and automatic rollback. Trigger: Chaos safety policy rollout. Sev: medium. Tool: `chaostoolkit`
- `credential-rotation-under-fault` — Rotated credentials picked up without restart during faults. Trigger: Credential rotation runbook update. Sev: medium. Tool: `chaostoolkit`
- `broker-failover-backlog-drain` — Broker failover resumes consumers and drains backlog correctly. Trigger: Message broker upgrade drill. Sev: high. Tool: `chaostoolkit`

## 11. Security, Supply Chain & Adversarial Testing

Hunts vulnerabilities across code, dependencies, secrets, and running surfaces, including adversarial red-team probes of live behavior.

Tool belt: `bandit`, `semgrep`, `pip-audit`, `wapiti3`, `detect-secrets`, `trivy`, `hypothesis`

### Granular test types

- `static-ast-vuln-scan` — Flag risky constructs: eval, exec, unsafe yaml loads. Trigger: New Python service onboarding. Sev: high. Tool: `bandit`
- `custom-rule-ast-scan` — Semgrep rules encode organization-specific insecure patterns. Trigger: Security team publishes pattern playbook. Sev: high. Tool: `semgrep`
- `taint-flow-analysis` — Track untrusted input flowing into dangerous sinks. Trigger: User input reaches subprocess or SQL. Sev: critical. Tool: `semgrep`
- `dependency-cve-audit` — Block known CVEs in pinned dependencies at CI. Trigger: New advisory hits pinned package. Sev: critical. Tool: `pip-audit`
- `transitive-dependency-scan` — Scan full dependency closure including transitive packages. Trigger: Indirect dependency flagged upstream. Sev: high. Tool: `trivy`
- `container-image-scan` — Scan base images and layers for CVEs. Trigger: Dockerfile or image bump in PR. Sev: high. Tool: `trivy`
- `iac-misconfig-scan` — Flag insecure infrastructure-as-code settings and embedded secrets. Trigger: Infrastructure template change merged. Sev: high. Tool: `trivy`
- `secret-detection-gate` — Block API keys and tokens entering version control. Trigger: Leaked credential incident or new key type. Sev: critical. Tool: `detect-secrets`
- `secret-baseline-drift` — Audit catches secrets added since last baseline snapshot. Trigger: Rotation schedule or periodic repo audit. Sev: high. Tool: `detect-secrets`
- `sql-injection-fuzzing` — Probe inputs for SQLi; assert parameterized queries. Trigger: Dynamic query construction found in review. Sev: critical. Tool: `wapiti3`
- `xss-fuzzing` — Reflected and stored XSS probes across user fields. Trigger: User content rendered as HTML. Sev: high. Tool: `wapiti3`
- `ssrf-probe` — User-supplied URLs cannot reach internal metadata endpoints. Trigger: Feature fetches external URLs. Sev: critical. Tool: `wapiti3`
- `command-injection-fuzzing` — Shell metacharacters cannot escape subprocess invocations. Trigger: Code shells out with interpolated input. Sev: critical. Tool: `hypothesis`
- `path-traversal-probe` — Traversal sequences cannot escape sandboxed file roots. Trigger: File download or upload endpoints. Sev: critical. Tool: `wapiti3`
- `unsafe-deserialization-checks` — Pickle and unsafe YAML rejected on untrusted data. Trigger: Cache or queue payload format reviewed. Sev: critical. Tool: `bandit`
- `ssti-template-injection` — Template injection probes against user-facing rendered templates. Trigger: Format strings used in templates. Sev: high. Tool: `semgrep`
- `auth-bypass-red-team` — Every route enforces identity; no unauthenticated access. Trigger: New endpoint or middleware change. Sev: critical. Tool: `wapiti3`
- `idor-access-control` — Other tenants' object IDs return 403 or 404. Trigger: Multi-tenant resource routes shipped. Sev: critical. Tool: `wapiti3`
- `privilege-escalation-probes` — Role boundaries hold against parameter tampering attempts. Trigger: RBAC claims matrix updated. Sev: critical. Tool: `wapiti3`
- `jwt-validation-matrix` — Reject alg=none, weak signatures, expired or forged tokens. Trigger: Auth library upgrade merged. Sev: critical. Tool: `hypothesis`
- `mass-assignment-probe` — Extra or protected fields not writable via payloads. Trigger: Serializer accepts untrusted JSON bodies. Sev: high. Tool: `hypothesis`
- `csrf-protection-check` — State-changing routes require valid CSRF tokens. Trigger: Cookie-based session handling changed. Sev: high. Tool: `wapiti3`
- `open-redirect-checks` — Redirect targets validated against strict allowlists. Trigger: Return URL parameter accepted. Sev: medium. Tool: `wapiti3`
- `file-upload-validation` — Content type, size, filename, and magic bytes enforced. Trigger: Upload endpoint added or changed. Sev: high. Tool: `hypothesis`
- `xxe-xml-hardening` — XML parsers disable entities and external fetches. Trigger: Partner XML ingestion integrated. Sev: high. Tool: `semgrep`
- `redos-pattern-audit` — Regexes stay linear-time on adversarial input. Trigger: User-supplied regex or pattern matching. Sev: medium. Tool: `hypothesis`
- `rate-limit-bypass-checks` — Limits hold against spoofed headers and rotating IPs. Trigger: Quota or abuse-prevention product change. Sev: high. Tool: `wapiti3`
- `sast-ci-gate` — Security scan failures block merge with triaged baseline. Trigger: Security gate policy rollout. Sev: high. Tool: `semgrep`
- `sbom-generation-audit` — SBOM emitted; licenses checked against allowlist. Trigger: Customer compliance questionnaire received. Sev: medium. Tool: `trivy`
- `malicious-package-screening` — Screen typosquat and suspicious packages before adoption. Trigger: New internal dependency requested. Sev: medium. Tool: `pip-audit`

## 12. Data, Scientific, AI/ML & Meta-Verification (Testing the Tests)

Covers data and ML correctness contracts — schemas, numerics, LLM behavior — plus meta-verification that the test suite itself is meaningful, stable, and mutation-hardened.

Tool belt: `pandera`, `deepeval`, `coverage.py`, `mutmut`, `cosmic-ray`, `hypothesis`, `numpy`, `pytest-flakefinder`, `pytest-randomly`

### Granular test types

- `dataframe-schema-contract` — Validate columns, dtypes, and nullability on ingestion. Trigger: Upstream feed schema changes silently. Sev: high. Tool: `pandera`
- `dataframe-value-constraints` — Check ranges, enums, uniqueness, and sortedness invariants. Trigger: Corrupt ingestion incident follow-up. Sev: medium. Tool: `pandera`
- `schema-coercion-policy` — Strict mode rejects silent type coercion surprises. Trigger: Numeric strings entered data pipelines. Sev: medium. Tool: `pandera`
- `etl-transform-invariants` — Row counts and totals preserved through transforms. Trigger: Aggregation pipeline rewrite merged. Sev: high. Tool: `pandera`
- `cross-field-constraints` — Dependent column rules validated jointly, not per-field. Trigger: Business rule spans multiple columns. Sev: medium. Tool: `pandera`
- `streaming-window-contracts` — Windowed aggregates stay within tolerance and ordering guarantees. Trigger: Streaming feature store release. Sev: high. Tool: `pandera`
- `golden-dataset-regression` — Frozen gold dataset pins expected data behavior. Trigger: Data vendor or schema migration. Sev: medium. Tool: `pandera`
- `tensor-allclose-tolerance` — Numerical outputs within dtype-aware tolerance windows. Trigger: Numeric kernel or library upgrade. Sev: high. Tool: `numpy`
- `tensor-shape-dtype-contract` — Shapes, dtypes, and device placement asserted everywhere. Trigger: Model input pipeline refactor. Sev: medium. Tool: `numpy`
- `numerical-stability-edge-inputs` — NaN, Inf, and zero-division handled on extreme values. Trigger: Loss spikes reported during training. Sev: high. Tool: `hypothesis`
- `seeded-determinism-check` — Fixed seeds reproduce training and evaluation results. Trigger: Reproducibility clause in model card. Sev: medium. Tool: `pytest-randomly`
- `metamorphic-consistency-checks` — Invariant transforms keep predictions consistent across runs. Trigger: Preprocessing change without new labels. Sev: medium. Tool: `hypothesis`
- `model-regression-metric-gate` — Quality metrics must not drop beyond epsilon. Trigger: Model retrain or feature change. Sev: critical. Tool: `deepeval`
- `llm-answer-relevance` — Generated answers score above relevance thresholds. Trigger: Prompt or model swap shipped. Sev: high. Tool: `deepeval`
- `llm-faithfulness-grounding` — Claims grounded in retrieved context; hallucinations flagged. Trigger: Hallucination complaints on support bot. Sev: critical. Tool: `deepeval`
- `rag-retrieval-quality` — Retrieved chunks hit expected gold documents. Trigger: Embedding or chunking strategy change. Sev: high. Tool: `deepeval`
- `llm-pii-leak-check` — Outputs scanned for PII and credential leakage. Trigger: Compliance review of LLM feature. Sev: critical. Tool: `deepeval`
- `llm-toxicity-safety-eval` — Safety policy violations scored with adversarial prompts. Trigger: Public-facing assistant launch. Sev: critical. Tool: `deepeval`
- `prompt-perturbation-robustness` — Paraphrases and typos keep outputs within bounds. Trigger: Prompt hardening ticket opened. Sev: medium. Tool: `deepeval`
- `eval-judge-calibration` — LLM-judge scores calibrated against human labels. Trigger: Automated eval gating adopted. Sev: medium. Tool: `deepeval`
- `line-coverage-threshold` — Coverage fails below configured line threshold. Trigger: Organization coverage minimum policy. Sev: medium. Tool: `coverage.py`
- `branch-coverage-threshold` — Both branch directions exercised on critical modules. Trigger: Audit demands branch, not line, coverage. Sev: high. Tool: `coverage.py`
- `coverage-diff-gate` — New code fully covered; totals never regress. Trigger: PR touches previously untested module. Sev: medium. Tool: `coverage.py`
- `mutation-testing-mutmut` — Surviving mutants expose weak or missing assertions. Trigger: Suite green but defects escaped. Sev: high. Tool: `mutmut`
- `mutation-testing-cosmic-ray` — Framework-level mutation score tracked across releases. Trigger: Critical library reliability review. Sev: medium. Tool: `cosmic-ray`
- `mutation-hotspot-targeting` — Mutate only changed lines for fast CI gates. Trigger: Full mutation runs too slow. Sev: medium. Tool: `mutmut`
- `mutation-harness-smoke` — Tiny mutation sample validates harness on each PR. Trigger: Adopting mutation testing incrementally. Sev: low. Tool: `cosmic-ray`
- `flakiness-detection-repeated` — Repeated runs surface intermittent failures statistically. Trigger: Flaky reruns hiding real bugs. Sev: high. Tool: `pytest-flakefinder`
- `randomized-execution-order` — Random ordering exposes shared-state test dependencies. Trigger: Suite passes solo, fails together. Sev: high. Tool: `pytest-randomly`
- `property-based-invariants` — Roundtrip, idempotence, and serialization invariants via properties. Trigger: Parser or codec edge-case defects. Sev: medium. Tool: `hypothesis`
# Test-Type Catalog — Batch D (Families 13–16)

## 13. Packaging, Distribution & Environment Testing

Verifies that the package installs, resolves, and behaves correctly across installation methods, dependency environments, and configuration matrices.

Tool belt: `build`, `pip check`, `pip`, `pipdeptree`, `virtualenv`, `tox`, `nox`

### Granular test types

- `sdist-build-integrity` — sdist builds cleanly and contains all required files. Trigger: release cut or packaging configuration changed. Sev: high. Tool: `build`
- `wheel-build-success` — wheel builds for target platforms without errors. Trigger: new extension module or build backend change. Sev: high. Tool: `build`
- `wheel-sdist-equivalence` — wheel and sdist install to identical behavior. Trigger: users report install-method-dependent failures. Sev: medium. Tool: `build`
- `pip-install-clean` — fresh pip install succeeds with no errors. Trigger: dependency list edited in pyproject. Sev: critical. Tool: `pip`
- `pip-check-consistency` — installed metadata satisfies all declared requirements. Trigger: version pins bumped in pyproject. Sev: high. Tool: `pip check`
- `dependency-conflict-detection` — resolver surfaces conflicting transitive requirements clearly. Trigger: adding a library sharing dependencies. Sev: high. Tool: `pip`
- `dependency-tree-audit` — transitive dependency tree matches declared expectations. Trigger: lockfile drift or surprise upgrades. Sev: medium. Tool: `pipdeptree`
- `entry-point-console-script` — console scripts install and execute correctly. Trigger: new CLI command added. Sev: high. Tool: `pip`
- `entry-point-plugin-registration` — plugin entry points register in target namespace. Trigger: plugin architecture change. Sev: medium. Tool: `pip`
- `editable-install-behavior` — editable install matches installed-package behavior. Trigger: developers report import discrepancies. Sev: medium. Tool: `pip`
- `venv-isolation` — package works in isolated venv without leakage. Trigger: works locally but fails on CI. Sev: high. Tool: `virtualenv`
- `extras-variants-install` — each extras group installs its intended dependencies. Trigger: optional feature reported broken. Sev: medium. Tool: `pip`
- `extras-absent-graceful` — package functions without optional extras installed. Trigger: minimal-install user complaint. Sev: medium. Tool: `pip`
- `extras-combination-resolution` — extras installed together resolve without conflicts. Trigger: two optional groups used simultaneously. Sev: medium. Tool: `pip check`
- `constraint-file-resolution` — pip constraints produce the intended pinned resolution. Trigger: security pinning mandate. Sev: medium. Tool: `pip`
- `locked-install-reproducibility` — lockfile installs identically across machines. Trigger: CI cache checksum mismatch. Sev: medium. Tool: `pip`
- `python-requires-enforcement` — pip refuses install on unsupported Python versions. Trigger: raised requires-python floor. Sev: high. Tool: `pip`
- `metadata-completeness` — package metadata like license and classifiers complete. Trigger: repository lint warnings on metadata. Sev: low. Tool: `build`
- `manifest-inclusion` — package data and non-code files ship in distributions. Trigger: runtime error about missing data file. Sev: high. Tool: `build`
- `namespace-package-install` — namespace packages coexist without clobbering each other. Trigger: vendor package split into parts. Sev: medium. Tool: `pip`
- `config-environment-matrix` — behavior verified across config and environment combinations. Trigger: deployment environment mismatch report. Sev: medium. Tool: `tox`
- `env-var-precedence` — environment variables override config files in documented order. Trigger: configuration precedence question in ticket. Sev: medium. Tool: `nox`
- `secrets-exclusion` — distributions contain no secrets or local paths. Trigger: pre-release audit of artifacts. Sev: critical. Tool: `build`
- `upgrade-path-install` — upgrading from prior release preserves user data. Trigger: new major release preparation. Sev: high. Tool: `pip`
- `uninstall-cleanliness` — uninstall removes all files without collateral damage. Trigger: ghost module reports after removal. Sev: low. Tool: `pip`
- `offline-install` — install completes from local artifacts without network. Trigger: air-gapped deployment requirement. Sev: medium. Tool: `pip`
- `tox-environment-parity` — test environments mirror target deployment configurations. Trigger: flaky environment-specific failures. Sev: medium. Tool: `tox`
- `nox-session-parity` — nox sessions reproduce documented contributor workflows. Trigger: onboarding friction complaints. Sev: low. Tool: `nox`
- `pep-517-build-isolation` — build isolation produces reproducible artifacts. Trigger: builds differ across contributor machines. Sev: low. Tool: `build`
- `wheel-tag-correctness` — wheel tags match supported interpreters and ABIs. Trigger: users get no matching distribution error. Sev: high. Tool: `build`

## 14. Compatibility & Portability Testing

Confirms the library behaves identically across Python versions, operating systems, interpreters, and serialization boundaries within its supported matrix.

Tool belt: `tox`, `vermin`, `cibuildwheel`, `pytest`

### Granular test types

- `py39-baseline` — suite passes on the Python 3.9 floor version. Trigger: minimum supported version claim. Sev: critical. Tool: `tox`
- `py310-matrix` — suite passes on Python 3.10. Trigger: version matrix expansion. Sev: high. Tool: `tox`
- `py311-matrix` — suite passes on Python 3.11. Trigger: version matrix expansion. Sev: high. Tool: `tox`
- `py312-matrix` — suite passes on Python 3.12. Trigger: 3.12 removals of deprecated APIs. Sev: high. Tool: `tox`
- `py313-matrix` — suite passes on Python 3.13. Trigger: newest interpreter adoption. Sev: high. Tool: `tox`
- `future-version-smoke` — smoke suite runs against pre-release Python for breakage. Trigger: CPython beta availability. Sev: medium. Tool: `tox`
- `os-linux-compat` — suite passes on Linux runners. Trigger: primary deployment target. Sev: high. Tool: `tox`
- `os-macos-compat` — suite passes on macOS. Trigger: developer-machine parity. Sev: medium. Tool: `tox`
- `os-windows-compat` — suite passes on Windows including path handling. Trigger: Windows-only bug report. Sev: high. Tool: `tox`
- `path-separator-portability` — path building uses portable separators everywhere. Trigger: Windows-only path failure. Sev: high. Tool: `pytest`
- `pypy-compat` — package works under the PyPy interpreter. Trigger: PyPy support request. Sev: low. Tool: `tox`
- `abi3-wheel-compat` — abi3 wheel loads across interpreter versions. Trigger: cibuildwheel configuration change. Sev: high. Tool: `cibuildwheel`
- `c-extension-build-matrix` — extension modules compile across version and OS matrix. Trigger: release containing compiled code. Sev: critical. Tool: `cibuildwheel`
- `cpython-api-drift` — C API usage survives interpreter internal changes. Trigger: interpreter upgrade breaks import. Sev: high. Tool: `cibuildwheel`
- `deprecated-api-usage` — code avoids APIs removed in supported versions. Trigger: DeprecationWarning surge in CI logs. Sev: high. Tool: `vermin`
- `minimum-version-inference` — tooling reports the true minimum Python required. Trigger: requires-python floor uncertainty. Sev: medium. Tool: `vermin`
- `stdlib-shim-backport` — shims cover missing newer stdlib features on old versions. Trigger: ImportError on older interpreter. Sev: high. Tool: `vermin`
- `cross-version-pickle` — pickles interchange across supported Python versions. Trigger: cached objects unreadable after upgrade. Sev: high. Tool: `pytest`
- `cross-version-serialization` — JSON or msgpack payloads stable across versions. Trigger: service upgrade compatibility contract. Sev: high. Tool: `pytest`
- `bytecode-independence` — behavior identical with or without stale pyc caches. Trigger: deployment caching oddities. Sev: low. Tool: `pytest`
- `locale-portability` — behavior stable under different locale settings. Trigger: numeric parsing bug in EU locale. Sev: medium. Tool: `tox`
- `filesystem-case-sensitivity` — imports tolerate case-sensitivity differences across systems. Trigger: macOS-developed code failing on Linux. Sev: high. Tool: `tox`
- `line-ending-portability` — file handling tolerant of CRLF and LF. Trigger: repository checked out on Windows. Sev: low. Tool: `pytest`
- `cpu-arch-arm64` — wheels build and tests pass on ARM64. Trigger: Apple Silicon or ARM server adoption. Sev: medium. Tool: `cibuildwheel`
- `musl-libc-compat` — wheels function on musl-based systems. Trigger: Alpine container deployment. Sev: medium. Tool: `cibuildwheel`
- `endianness-portability` — binary formats correct on big-endian platforms. Trigger: exotic target support request. Sev: low. Tool: `pytest`
- `timezone-portability` — datetime logic stable across runner timezone settings. Trigger: CI runner timezone drift. Sev: medium. Tool: `pytest`
- `deprecation-timeline` — removal warnings mapped to the supported version matrix. Trigger: upcoming EOL of a Python version. Sev: medium. Tool: `vermin`
- `vendor-lib-compat` — vendored dependencies work across supported versions. Trigger: vendored library upgrade. Sev: medium. Tool: `tox`
- `subprocess-portability` — subprocess behavior consistent across OS shells. Trigger: shell-specific command failure. Sev: medium. Tool: `pytest`

## 15. Documentation & Example Testing

Ensures documentation, docstrings, and examples stay executable, accurate, and in sync with the shipped code.

Tool belt: `doctest`, `pytest --doctest-modules`, `sphinx`, `pytest`

### Granular test types

- `doctest-inline` — inline doctests in docstrings pass. Trigger: docstring examples edited. Sev: medium. Tool: `doctest`
- `doctest-modules-sweep` — pytest collects doctests across all modules. Trigger: documentation drift between code and docs. Sev: medium. Tool: `pytest --doctest-modules`
- `doctest-output-determinism` — doctest outputs stable across runs and platforms. Trigger: flaky example outputs in CI. Sev: medium. Tool: `doctest`
- `readme-quickstart` — README quickstart commands execute successfully. Trigger: onboarding complaint about README. Sev: high. Tool: `pytest`
- `readme-code-blocks` — all README code blocks run in a fresh environment. Trigger: copy-paste failure reports. Sev: high. Tool: `pytest`
- `docs-example-execution` — tutorial examples produce the documented results. Trigger: documentation release. Sev: high. Tool: `sphinx`
- `docs-example-fresh-env` — examples work in a clean venv without hidden state. Trigger: examples work only for maintainers. Sev: medium. Tool: `pytest`
- `docs-install-instructions` — documented install commands match package reality. Trigger: package rename or extras change. Sev: high. Tool: `pytest`
- `docstring-signature-drift` — documented parameters match actual function signatures. Trigger: function signature refactored. Sev: high. Tool: `sphinx`
- `docstring-type-accuracy` — documented types match current annotations. Trigger: type annotation overhaul. Sev: medium. Tool: `sphinx`
- `docstring-return-docs` — return values documented and consistent with behavior. Trigger: API review checklist. Sev: medium. Tool: `sphinx`
- `docstring-exception-docs` — raised exceptions documented where they occur. Trigger: error-handling changes. Sev: low. Tool: `sphinx`
- `docstring-default-values` — documented defaults match code defaults. Trigger: default parameter change. Sev: medium. Tool: `pytest`
- `docstring-deprecation-notes` — deprecated APIs marked with migration guidance. Trigger: deprecation introduced. Sev: medium. Tool: `sphinx`
- `docs-build-clean` — sphinx builds without errors or broken references. Trigger: docs CI failure. Sev: high. Tool: `sphinx`
- `docs-link-integrity` — internal and external documentation links resolve. Trigger: restructured docs pages. Sev: low. Tool: `sphinx`
- `docs-version-pinned` — docs match released version behavior, not main. Trigger: users on old docs report bugs. Sev: medium. Tool: `sphinx`
- `doctest-skips-marked` — intentionally non-executable examples marked appropriately. Trigger: illustrative pseudocode in docstrings. Sev: low. Tool: `doctest`
- `docs-api-coverage` — every public API appears in generated documentation. Trigger: new module left undocumented. Sev: medium. Tool: `sphinx`
- `docs-example-deps-declared` — example requirements declared explicitly in docs. Trigger: ImportError when following example. Sev: medium. Tool: `pytest`
- `docs-notebook-execution` — notebook tutorials execute end-to-end without errors. Trigger: tutorial notebook updated. Sev: medium. Tool: `pytest`
- `docs-output-formatting` — documented output matches actual console output. Trigger: CLI output format change. Sev: medium. Tool: `doctest`
- `docs-terminology-consistency` — terminology consistent across docs and code. Trigger: renamed concepts in review. Sev: low. Tool: `sphinx`
- `docstring-example-runs` — every usage example is executable, not pseudocode. Trigger: API documentation audit. Sev: medium. Tool: `pytest --doctest-modules`
- `docs-config-samples` — sample configuration files parse and validate. Trigger: config schema change. Sev: medium. Tool: `pytest`
- `docs-cli-help-sync` — documented CLI flags match actual help output. Trigger: CLI flag added or renamed. Sev: medium. Tool: `pytest`
- `docs-changelog-links` — changelog entries link to docs and issues. Trigger: release notes drafted. Sev: low. Tool: `sphinx`
- `docs-doctest-warnings` — doctests surface warnings instead of hiding them. Trigger: silent deprecation inside examples. Sev: low. Tool: `doctest`
- `docs-example-determinism` — examples avoid nondeterministic timestamps or ids. Trigger: flaky documentation test. Sev: low. Tool: `pytest`
- `docs-migration-guide-verified` — migration steps verified against both versions. Trigger: major version migration guide. Sev: high. Tool: `pytest`

## 16. Exploratory, Usability & Accessibility Testing

Human-gated charters plus assisted audits for usability, internationalization, and accessibility gaps automation alone cannot certify.

Tool belt: `axe-playwright`, `babel`, `pytest`

### Granular test types

- `charter-based-exploration` — timeboxed charters probe risky workflows without scripts. Trigger: novel feature lacking coverage. Sev: medium. Tool: `pytest`
- `error-message-usability` — error messages are actionable and non-cryptic. Trigger: support tickets citing confusing errors. Sev: medium. Tool: `pytest`
- `cli-first-run-experience` — first CLI run guides users toward success. Trigger: onboarding feedback session. Sev: low. Tool: `pytest`
- `error-recovery-usability` — users can recover from common failure modes. Trigger: retries leave stuck states. Sev: medium. Tool: `pytest`
- `api-ergonomics-review` — public API naming and defaults feel intuitive. Trigger: new public API drafted. Sev: medium. Tool: `pytest`
- `visual-glitch-exploration` — rendered UI states reviewed visually for glitches. Trigger: rendering changes shipped. Sev: low. Tool: `axe-playwright`
- `axe-audit-core-pages` — automated axe scan of key pages passes. Trigger: web UI release. Sev: high. Tool: `axe-playwright`
- `axe-color-contrast` — text meets WCAG contrast thresholds everywhere. Trigger: design token update. Sev: high. Tool: `axe-playwright`
- `axe-landmarks-labels` — pages expose landmarks and labeled controls. Trigger: new page templates. Sev: medium. Tool: `axe-playwright`
- `keyboard-navigation` — all interactive elements reachable by keyboard. Trigger: accessibility bug report. Sev: high. Tool: `axe-playwright`
- `focus-management` — focus order and traps behave predictably. Trigger: modal or drawer added. Sev: high. Tool: `axe-playwright`
- `screen-reader-labels` — dynamic regions announce via correct ARIA. Trigger: live-updating dashboard shipped. Sev: medium. Tool: `axe-playwright`
- `aria-live-regions` — async updates announced without focus loss. Trigger: streaming status UI added. Sev: medium. Tool: `axe-playwright`
- `reduced-motion-respect` — animations honor prefers-reduced-motion settings. Trigger: animation-heavy feature shipped. Sev: low. Tool: `axe-playwright`
- `i18n-string-extraction` — user-facing strings extracted into translation catalogs. Trigger: localization kickoff. Sev: high. Tool: `babel`
- `babel-extraction-freshness` — catalog updates capture newly added strings. Trigger: release with UI copy changes. Sev: medium. Tool: `babel`
- `translation-pluralization` — plural forms correct across target languages. Trigger: new locale added. Sev: medium. Tool: `babel`
- `locale-date-formatting` — dates and numbers format per active locale. Trigger: international user report. Sev: medium. Tool: `babel`
- `rtl-layout-review` — layouts work in right-to-left locales. Trigger: Arabic or Hebrew support requested. Sev: low. Tool: `axe-playwright`
- `string-concatenation-i18n` — no broken sentences built by string concatenation. Trigger: translators flag untranslatable fragments. Sev: medium. Tool: `babel`
- `pseudo-localization-testing` — pseudo-locale reveals remaining hard-coded strings. Trigger: i18n readiness audit. Sev: medium. Tool: `babel`
- `utf8-handling-exploration` — unusual Unicode inputs handled gracefully end-to-end. Trigger: international names break forms. Sev: high. Tool: `pytest`
- `timezone-usability` — times displayed in the user's zone consistently. Trigger: cross-region team confusion. Sev: medium. Tool: `babel`
- `help-text-clarity` — help and placeholder text understandable to newcomers. Trigger: usability session findings. Sev: low. Tool: `pytest`
- `finding-triage-review` — exploratory findings triaged into actionable tickets. Trigger: exploration session completed. Sev: medium. Tool: `pytest`
- `accessibility-regression-checks` — axe checks run in CI on changed pages. Trigger: accessibility fixes keep regressing. Sev: high. Tool: `axe-playwright`
- `export-localization` — exported data respects locale-specific formats. Trigger: localized CSV consumers report errors. Sev: low. Tool: `babel`
- `console-output-encoding` — CLI output safe on non-UTF8 consoles. Trigger: Windows codepage errors. Sev: low. Tool: `pytest`
- `empty-state-usability` — empty and error states communicate next steps. Trigger: user confusion on first load. Sev: low. Tool: `pytest`
- `accessibility-manual-audit` — human audit of flows automation cannot judge. Trigger: compliance requirement. Sev: medium. Tool: `axe-playwright`
## 17. Differential & Behavioral-Equivalence Testing

Comparing old and new implementations on identical inputs to prove behavioral equivalence across refactors, swaps, and upgrades.

Tool belt: `pytest`, `dirty-equals`, `deepdiff`, `syrupy`, `hypothesis`, `pytest-asyncio`, `pytest-mock`, `freezegun`, `pytest-benchmark`, `memray`, `pact-python`, `coverage.py`

### Granular test types

- `refactor-equivalence-diff` — old vs new implementation outputs compared on identical inputs. Trigger: refactor ticket touching core logic. Sev: critical. Tool: `dirty-equals`
- `golden-fixture-replay` — recorded golden input-output pairs replayed against new implementation. Trigger: contract mentions golden files. Sev: high. Tool: `pytest`
- `shadow-traffic-comparison` — shadow copy of live traffic run against candidate build. Trigger: deploy plan includes shadow or canary. Sev: high. Tool: `pytest`
- `property-equivalence-check` — invariants asserted identically across old and new implementations. Trigger: algorithm swap with stated invariants. Sev: high. Tool: `hypothesis`
- `floating-point-tolerance-diff` — numeric outputs compared within defined tolerance across versions. Trigger: numerical library upgrade. Sev: medium. Tool: `dirty-equals`
- `serialization-roundtrip-parity` — serialized forms compared byte-for-byte across versions. Trigger: wire format or schema refactor. Sev: high. Tool: `deepdiff`
- `snapshot-output-parity` — rendered output snapshots compared before and after change. Trigger: rendering or template change. Sev: medium. Tool: `syrupy`
- `random-seed-parity` — deterministic behavior verified under identical fixed seeds. Trigger: randomness in changed code paths. Sev: medium. Tool: `pytest`
- `error-path-parity` — exception types and messages matched across versions. Trigger: error handling rewrite. Sev: medium. Tool: `pytest`
- `boundary-input-differential` — edge inputs run through both implementations and diffed. Trigger: parser or validation rewrite. Sev: high. Tool: `hypothesis`
- `api-signature-compat-diff` — call signatures diffed between old and new module versions. Trigger: internal API reshuffle. Sev: high. Tool: `pytest`
- `performance-regression-differential` — latency compared old versus new on same workload. Trigger: performance-sensitive rewrite. Sev: medium. Tool: `pytest-benchmark`
- `memory-footprint-differential` — allocation behavior compared across old and new implementations. Trigger: memory-constrained service change. Sev: low. Tool: `memray`
- `idempotency-parity-check` — repeated invocation behavior matched across versions. Trigger: retry or queue consumer change. Sev: medium. Tool: `pytest`
- `concurrency-behavior-parity` — threaded and async behavior compared old versus new. Trigger: async migration ticket. Sev: high. Tool: `pytest-asyncio`
- `side-effect-parity` — external calls and writes diffed between versions. Trigger: storage or client swap. Sev: high. Tool: `pytest-mock`
- `config-behavior-parity` — same configuration yields same behavior across versions. Trigger: config schema refactor. Sev: medium. Tool: `pytest`
- `locale-timezone-parity` — outputs compared under varied locales and timezones. Trigger: datetime handling rewrite. Sev: medium. Tool: `freezegun`
- `unicode-normalization-parity` — string handling matched across encodings and normal forms. Trigger: text pipeline change. Sev: low. Tool: `pytest`
- `large-payload-differential` — oversized inputs processed identically by both versions. Trigger: bulk processing change. Sev: medium. Tool: `pytest`
- `order-dependence-diff` — result ordering compared while input order varies. Trigger: collection or sort refactor. Sev: medium. Tool: `deepdiff`
- `partial-failure-parity` — behavior under induced failures matched across versions. Trigger: resilience refactor. Sev: high. Tool: `pytest`
- `legacy-behavior-lock` — documented quirks pinned so refactors preserve them. Trigger: bug-for-bug compatibility requirement. Sev: high. Tool: `pytest`
- `cross-version-contract-test` — producer and consumer from different versions interoperate. Trigger: staged rollout plan. Sev: high. Tool: `pact-python`
- `dead-code-differential` — removed paths confirmed unreachable with behavior preserved. Trigger: cleanup ticket deleting branches. Sev: low. Tool: `coverage.py`
- `determinism-audit` — repeated runs of new code produce identical outputs. Trigger: nondeterminism suspected after refactor. Sev: medium. Tool: `pytest`

## 18. Observability, Ops & Config Testing

Verifying that logs, metrics, traces, health checks, shutdown behavior, and configuration behave correctly in operations.

Tool belt: `opentelemetry-sdk`, `structlog`, `pydantic-settings`, `prometheus-client`, `pytest`, `freezegun`

### Granular test types

- `log-message-assertion` — expected log lines asserted for level, message, context. Trigger: incident fix adds logging. Sev: medium. Tool: `structlog`
- `log-level-config-test` — configured log levels honored per environment. Trigger: verbosity complaints in production. Sev: low. Tool: `pytest`
- `structured-log-schema` — JSON log fields validated against agreed schema. Trigger: log pipeline contract change. Sev: high. Tool: `structlog`
- `correlation-id-propagation` — request IDs flow through logs across components. Trigger: correlation gap in incident review. Sev: high. Tool: `structlog`
- `pii-log-scrubbing` — sensitive fields masked before log emission. Trigger: compliance flag on logged payloads. Sev: critical. Tool: `structlog`
- `metric-emission-check` — counters, gauges, histograms emitted as specified. Trigger: new dashboard depends on metrics. Sev: high. Tool: `prometheus-client`
- `metric-label-cardinality` — label sets bounded to prevent cardinality blowup. Trigger: telemetry cost alert. Sev: medium. Tool: `prometheus-client`
- `span-coverage-check` — critical paths produce complete trace spans. Trigger: distributed tracing rollout. Sev: high. Tool: `opentelemetry-sdk`
- `trace-context-propagation` — trace context propagated across service boundaries. Trigger: broken trace waterfalls. Sev: high. Tool: `opentelemetry-sdk`
- `sampling-config-test` — tracer sampling rules behave as configured. Trigger: telemetry volume overrun. Sev: low. Tool: `opentelemetry-sdk`
- `health-endpoint-check` — liveness and readiness endpoints reflect true state. Trigger: orchestrator restart loops. Sev: critical. Tool: `pytest`
- `readiness-dependency-gate` — readiness fails when downstream dependencies are down. Trigger: traffic routed to unhealthy pods. Sev: critical. Tool: `pytest`
- `graceful-shutdown-sigterm` — SIGTERM drains in-flight work before exit. Trigger: deploys drop in-flight requests. Sev: critical. Tool: `pytest`
- `shutdown-cleanup-test` — connections and temporary resources released on exit. Trigger: resource leak after redeploy. Sev: medium. Tool: `pytest`
- `startup-failure-fast` — missing dependencies abort startup with clear errors. Trigger: silent misconfiguration incident. Sev: high. Tool: `pydantic-settings`
- `env-var-validation` — required environment variables checked with types and ranges. Trigger: onboarding misconfiguration. Sev: high. Tool: `pydantic-settings`
- `config-defaults-test` — defaults are safe and documented for each environment. Trigger: config refactor ticket. Sev: medium. Tool: `pydantic-settings`
- `secret-handling-test` — secrets never rendered in logs or error messages. Trigger: secret leak report. Sev: critical. Tool: `pydantic-settings`
- `config-hot-reload-test` — dynamic config changes apply without restart. Trigger: feature flag rollout. Sev: medium. Tool: `pydantic-settings`
- `alert-threshold-signal` — emitted metrics make alert thresholds meaningful. Trigger: noisy or silent alerts. Sev: medium. Tool: `prometheus-client`
- `error-rate-attribution` — failures tagged to enable per-cause breakdown. Trigger: opaque error spikes. Sev: medium. Tool: `prometheus-client`
- `log-volume-guard` — hot paths do not emit excessive log volume. Trigger: logging cost spike. Sev: low. Tool: `structlog`
- `otel-exporter-failure-test` — telemetry export failures never break requests. Trigger: collector outage. Sev: high. Tool: `opentelemetry-sdk`
- `diagnostic-context-completeness` — errors logged with enough context to debug. Trigger: unusable incident logs. Sev: high. Tool: `structlog`
- `deprecated-config-warning` — obsolete configuration keys warn instead of failing silently. Trigger: config cleanup. Sev: low. Tool: `pydantic-settings`
- `timestamp-normalization-test` — log and metric timestamps normalized across regions. Trigger: cross-region log confusion. Sev: low. Tool: `freezegun`
- `process-signal-handling` — SIGINT and SIGTERM handlers registered and idempotent. Trigger: worker cleanup ticket. Sev: medium. Tool: `pytest`

## 19. Compliance, Privacy & Governance Testing

Enforcing privacy, licensing, audit, retention, and data-governance obligations across code and data flows.

Tool belt: `presidio`, `pip-licenses`, `pip-audit`, `detect-secrets`, `pytest`, `pip`

### Granular test types

- `pii-leakage-scan` — outputs and logs scanned for PII patterns. Trigger: feature touches user data. Sev: critical. Tool: `presidio`
- `pii-detection-coverage` — detectors catch names, emails, identifiers across formats. Trigger: new data field types added. Sev: high. Tool: `presidio`
- `pii-redaction-test` — redaction removes PII while preserving usability. Trigger: data-sharing request. Sev: critical. Tool: `presidio`
- `dependency-license-inventory` — licenses of new dependencies enumerated and classified. Trigger: PR adds third-party package. Sev: high. Tool: `pip-licenses`
- `copyleft-license-gate` — copyleft dependencies blocked per license policy. Trigger: license policy enforcement. Sev: critical. Tool: `pip-licenses`
- `license-notice-generation` — required attributions generated for distributed artifacts. Trigger: shipping open-source artifacts. Sev: medium. Tool: `pip-licenses`
- `vulnerability-audit` — dependencies checked against known CVEs. Trigger: routine security review. Sev: high. Tool: `pip-audit`
- `transitive-dependency-audit` — indirect dependencies audited, not just direct. Trigger: supply-chain review. Sev: high. Tool: `pip-audit`
- `audit-trail-completeness` — every privileged action produces an audit record. Trigger: SOC2 control check. Sev: critical. Tool: `pytest`
- `audit-record-integrity` — audit entries immutable and tamper-evident. Trigger: audit storage redesign. Sev: critical. Tool: `pytest`
- `audit-actor-attribution` — records identify who acted, including service identity. Trigger: accountability gap finding. Sev: high. Tool: `pytest`
- `data-retention-enforcement` — expired data deleted on schedule. Trigger: retention policy published. Sev: high. Tool: `pytest`
- `retention-policy-config-test` — per-class retention durations honored exactly. Trigger: multi-tenant data classes. Sev: medium. Tool: `pytest`
- `right-to-erasure-flow` — deletion requests remove all user data traces. Trigger: GDPR request handling. Sev: critical. Tool: `pytest`
- `data-export-compliance` — exports respect consent and access scopes. Trigger: data portability feature. Sev: high. Tool: `pytest`
- `consent-enforcement-test` — processing blocked without recorded consent. Trigger: consent management integration. Sev: critical. Tool: `pytest`
- `anonymization-effectiveness` — anonymized datasets resist re-identification attempts. Trigger: analytics dataset release. Sev: high. Tool: `presidio`
- `access-control-audit` — permission checks logged and coverage reviewed. Trigger: quarterly access review. Sev: high. Tool: `pytest`
- `secret-detection-scan` — repository scanned for committed credentials. Trigger: pre-push policy gate. Sev: critical. Tool: `detect-secrets`
- `data-lineage-completeness` — transformations traceable from source to sink. Trigger: lineage documentation mandate. Sev: medium. Tool: `pytest`
- `cross-border-data-rule` — data residency constraints enforced per region. Trigger: new region deployment. Sev: high. Tool: `pytest`
- `audit-log-retention-test` — audit records retained for mandated duration. Trigger: regulator retention schedule. Sev: medium. Tool: `pytest`
- `pii-in-fixtures-scan` — test data contains no real personal data. Trigger: fixture hygiene policy. Sev: high. Tool: `presidio`
- `model-data-governance` — training and evaluation data usage complies with policy. Trigger: ML feature launch. Sev: medium. Tool: `pytest`
- `compliance-report-generation` — required compliance artifacts generated reproducibly. Trigger: audit season. Sev: medium. Tool: `pytest`
- `dependency-reproducibility` — installs verified against pinned hashes. Trigger: supply-chain hardening. Sev: medium. Tool: `pip`

## 20. Upgrade & Migration Path Testing

Proving that version upgrades, data migrations, backfills, rollbacks, and zero-downtime deploys preserve data and service availability.

Tool belt: `alembic`, `pytest-alembic`, `pytest`

### Granular test types

- `upgrade-path-forward` — v1 to v2 upgrade completes on production-like data. Trigger: major version migration. Sev: critical. Tool: `alembic`
- `schema-migration-forward` — schema migrations apply cleanly to current database. Trigger: new alembic revision added. Sev: critical. Tool: `pytest-alembic`
- `migration-downgrade-rollback` — downgrade scripts restore previous schema and data. Trigger: rollback plan review. Sev: critical. Tool: `alembic`
- `data-backfill-idempotency` — backfill reruns without duplicating or corrupting data. Trigger: large backfill job. Sev: high. Tool: `pytest`
- `backfill-completeness` — backfill covers all rows including late arrivals. Trigger: historical data conversion. Sev: high. Tool: `pytest`
- `zero-downtime-expand-contract` — schema changes staged expand-then-contract without downtime. Trigger: live table migration. Sev: critical. Tool: `alembic`
- `mixed-version-compatibility` — old and new application versions share database mid-deploy. Trigger: rolling deploy plan. Sev: critical. Tool: `pytest`
- `migration-reversibility` — data transformations invertible losslessly where promised. Trigger: destructive transform ticket. Sev: high. Tool: `alembic`
- `migration-data-integrity` — row counts and checksums match pre and post. Trigger: data migration signoff. Sev: critical. Tool: `pytest`
- `long-running-migration-locking` — migrations avoid long locks blocking production traffic. Trigger: large table alteration. Sev: high. Tool: `alembic`
- `migration-order-dependence` — revisions apply correctly from any pending state. Trigger: divergent branches with migrations. Sev: high. Tool: `pytest-alembic`
- `fresh-install-migration` — fresh installs match migrated schema exactly. Trigger: deployment divergence suspicion. Sev: high. Tool: `pytest-alembic`
- `orphan-data-handling` — rows referencing missing records handled safely. Trigger: legacy data quality concerns. Sev: medium. Tool: `pytest`
- `enum-value-migration` — enum value changes mapped for existing rows. Trigger: status field extension. Sev: high. Tool: `alembic`
- `index-migration-safety` — index creation uses non-blocking patterns. Trigger: index rollout on hot table. Sev: high. Tool: `alembic`
- `migration-performance-budget` — migration completes within maintenance window. Trigger: timeboxed deploy. Sev: medium. Tool: `pytest`
- `default-value-backfill` — new columns populated correctly for existing rows. Trigger: column addition with defaults. Sev: medium. Tool: `alembic`
- `multi-tenant-migration` — migrations applied consistently across all shards. Trigger: sharded architecture. Sev: critical. Tool: `pytest`
- `migration-failure-recovery` — failed migration leaves database recoverable. Trigger: aborted deploy incident. Sev: critical. Tool: `alembic`
- `config-format-upgrade` — configuration files transformed to new version format. Trigger: config schema version bump. Sev: medium. Tool: `pytest`
- `api-version-transition` — deprecated API version served during migration window. Trigger: deprecation timeline. Sev: high. Tool: `pytest`
- `message-schema-evolution` — consumers tolerate old and new payload versions. Trigger: event schema change. Sev: high. Tool: `pytest`
- `cache-invalidation-on-upgrade` — stale caches flushed or versioned after upgrade. Trigger: cache poisoning risk. Sev: medium. Tool: `pytest`
- `dependency-upgrade-compat` — framework version bump keeps behavior intact. Trigger: dependency major upgrade. Sev: high. Tool: `pytest`
- `storage-engine-migration` — data moved between stores without loss. Trigger: database switch project. Sev: critical. Tool: `pytest`
- `migration-dry-run` — migrations rehearsed against production snapshot. Trigger: high-risk migration plan. Sev: high. Tool: `alembic`
- `rollback-drill` — full rollback executed and verified in staging. Trigger: release readiness review. Sev: high. Tool: `pytest`
- `in-place-upgrade-concurrency` — upgrade safe while live traffic flows. Trigger: no maintenance window constraint. Sev: high. Tool: `pytest`
# Batch F — Test-Type Catalog (Families 21–24)

## 21. Feature-Flag & Rollout Testing

Verifies that feature flags, canary allocations, staged rollouts, dark launches, and kill switches behave safely across every configuration combination and failure mode.

Tool belt: `hypothesis`, `pytest-parametrize`, `pytest-mock`, `pytest`, `responses`, `freezegun`, `coverage.py`, `pytest-benchmark`

### Granular test types

- `flag-matrix-combinatorial` — Exhaustively exercises flag on/off combinations across feature set. Trigger: PR modifies flag evaluation logic. Sev: high. Tool: `hypothesis`
- `flag-safe-default-fallback` — Unavailable flag source falls back to safe default. Trigger: contract demands offline resilience. Sev: critical. Tool: `pytest-mock`
- `kill-switch-immediate-disabling` — Kill switch disables feature within one evaluation cycle. Trigger: ticket mandates emergency shutoff. Sev: critical. Tool: `pytest`
- `kill-switch-state-persistence` — Kill switch state survives process restart. Trigger: durable shutoff requirement stated. Sev: critical. Tool: `pytest`
- `kill-switch-recovery-reenable` — Re-enabling after kill switch restores prior behavior. Trigger: rollback runbook defines recovery. Sev: high. Tool: `pytest`
- `canary-percentage-allocation` — Cohort assignment matches configured rollout percentage. Trigger: staged rollout plan changes bucketing. Sev: high. Tool: `hypothesis`
- `canary-sticky-bucketing` — Same user consistently lands in same cohort. Trigger: contract demands stable assignment. Sev: high. Tool: `pytest-parametrize`
- `canary-ramp-monotonicity` — Raising rollout threshold never demotes enabled users. Trigger: rollout stage transition documented. Sev: medium. Tool: `pytest-parametrize`
- `rollout-auto-halt-guardrail` — Rollout pauses automatically when error budget breached. Trigger: guardrail policy referenced in ticket. Sev: critical. Tool: `pytest-mock`
- `dark-launch-telemetry-only` — Dark launch emits metrics without user-visible exposure. Trigger: "dark launch" named in feature ticket. Sev: medium. Tool: `pytest-mock`
- `flag-targeting-rules` — Targeting honors user and tenant attribute rules. Trigger: targeting rule change reviewed. Sev: high. Tool: `pytest-parametrize`
- `flag-dependency-ordering` — Dependent flags evaluate prerequisites before dependents. Trigger: flags declare dependencies. Sev: medium. Tool: `pytest`
- `flag-config-cache-refresh` — Cached evaluations refresh after config update. Trigger: poll interval or TTL changed. Sev: medium. Tool: `freezegun`
- `flag-provider-failover` — Secondary provider serves when primary unavailable. Trigger: multi-provider resilience contract. Sev: high. Tool: `responses`
- `flag-sdk-timeout-degradation` — SDK timeout falls back to last-known values. Trigger: latency SLO covers evaluation path. Sev: high. Tool: `pytest-mock`
- `cross-flag-conflict-resolution` — Simultaneously enabled conflicting flags resolve deterministically. Trigger: overlapping flags documented. Sev: medium. Tool: `hypothesis`
- `flag-removal-dead-code` — Removed flag leaves no dead branches behind. Trigger: tech-debt ticket retires flag. Sev: medium. Tool: `coverage.py`
- `flag-evaluation-audit-log` — Evaluation decisions logged with actor and context. Trigger: compliance audit requirement cited. Sev: low. Tool: `pytest`
- `allowlist-override-precedence` — Explicit allowlist beats percentage bucketing. Trigger: beta allowlist introduced. Sev: medium. Tool: `pytest-parametrize`
- `flag-gated-migration-steps` — Flag gates dual-write and cutover migration stages. Trigger: migration plan staged by flag. Sev: high. Tool: `pytest`
- `flag-config-version-compat` — Older flag config versions still evaluate correctly. Trigger: SDK version skew risk noted. Sev: medium. Tool: `pytest`
- `tenant-scoped-rollout-isolation` — One tenant's rollout never leaks to others. Trigger: multi-tenant release plan. Sev: high. Tool: `pytest-parametrize`
- `flag-evaluation-latency-budget` — Evaluation latency stays within budget under load. Trigger: hot-path performance requirement. Sev: medium. Tool: `pytest-benchmark`
- `flag-cannot-bypass-authz` — Flag state cannot bypass permission enforcement. Trigger: security review of gated feature. Sev: critical. Tool: `pytest`

## 22. Determinism & Reproducibility Testing

Verifies that seeded runs reproduce identical output with no dependence on wall-clock time, randomness, iteration order, hashing, or run-to-run residue.

Tool belt: `freezegun`, `pytest-repeat`, `pytest-randomly`, `PYTHONHASHSEED`, `pytest-xdist`, `pytest-asyncio`, `vcrpy`, `pip-tools`, `numpy`, `pytest`

### Granular test types

- `seeded-run-identical-artifacts` — Same seed produces byte-identical output artifacts. Trigger: reproducibility promised in contract. Sev: high. Tool: `pytest-repeat`
- `wall-clock-independence` — Outputs independent of current system time. Trigger: flaky timestamp assertions observed. Sev: high. Tool: `freezegun`
- `timezone-offset-independence` — Results unchanged across UTC offset environments. Trigger: timezone-sensitive date logic changed. Sev: medium. Tool: `freezegun`
- `random-seed-injection` — All randomness routed through injectable seeded generator. Trigger: nondeterministic test failures reported. Sev: high. Tool: `pytest-randomly`
- `hash-seed-pinning` — String hashing stable across interpreter processes. Trigger: set iteration order leaked into output. Sev: high. Tool: `PYTHONHASHSEED`
- `dict-ordering-stability` — Serialization order stable for identical insertion sequence. Trigger: snapshot diffs shuffle between runs. Sev: medium. Tool: `pytest`
- `unordered-collection-canonicalization` — Sets and maps serialized in canonical order. Trigger: report equality comparison flaky. Sev: medium. Tool: `pytest`
- `float-replay-same-platform` — Same binary reproduces float outputs exactly. Trigger: numeric pipeline output drift reported. Sev: high. Tool: `numpy`
- `parallel-worker-determinism` — Concurrent workers yield identical merged output ordering. Trigger: xdist-enabled pipeline nondeterministic. Sev: high. Tool: `pytest-xdist`
- `replay-idempotence` — Rerunning pipeline on own output changes nothing. Trigger: replay or idempotency contract. Sev: high. Tool: `pytest`
- `entropy-source-stubbing` — Generated UUIDs deterministic under fixed entropy. Trigger: generated-ID equality assertions flaky. Sev: medium. Tool: `freezegun`
- `ambient-environment-independence` — Results insensitive to ambient environment variables. Trigger: CI and local divergence reported. Sev: medium. Tool: `pytest`
- `locale-independence` — Number and date formatting locale-stable. Trigger: formatting code touched. Sev: low. Tool: `pytest`
- `framework-rng-pinning` — NumPy and framework RNG states pinned together. Trigger: ML-adjacent run variance reported. Sev: medium. Tool: `numpy`
- `scheduling-order-independence` — Result independent of thread and task scheduling. Trigger: async pipeline output flaky. Sev: high. Tool: `pytest-asyncio`
- `golden-file-versioning` — Golden snapshots versioned with generator version. Trigger: snapshot drift complaints recurring. Sev: medium. Tool: `pytest`
- `dependency-lock-reproducibility` — Locked dependency set reproduces identical behavior. Trigger: lockfile change inside PR. Sev: medium. Tool: `pip-tools`
- `cache-cold-warm-parity` — Cold and warm runs produce equal results. Trigger: caching layer introduced. Sev: medium. Tool: `pytest`
- `serialization-field-ordering` — Dataclass and JSON field order fixed. Trigger: serializer refactor under review. Sev: low. Tool: `pytest`
- `filesystem-walk-ordering` — Directory traversal sorted deterministically. Trigger: glob-based batch processing added. Sev: medium. Tool: `pytest`
- `recorded-http-replay-order` — Recorded HTTP interactions replay identically ordered. Trigger: VCR-based tests flaky. Sev: medium. Tool: `vcrpy`
- `monotonic-clock-hygiene` — Durations measured via monotonic clock only. Trigger: benchmark timing code reviewed. Sev: low. Tool: `freezegun`
- `seed-provenance-logging` — Effective seeds logged and reconstructible. Trigger: audit requires run reproduction. Sev: medium. Tool: `pytest`
- `cross-run-state-cleanliness` — Runs never read residue from earlier runs. Trigger: order-dependent CI failures observed. Sev: high. Tool: `pytest-randomly`

## 23. Disaster Recovery & Backup-Restore Testing

Verifies that systems recover from backups and snapshots within declared recovery objectives, with integrity, compatibility, and security intact.

Tool belt: `testcontainers`, `psycopg`, `boto3`, `docker`, `pytest-timeout`, `freezegun`, `alembic`, `cryptography`, `locust`, `kombu`, `pytest`

### Granular test types

- `full-restore-drill` — Full restore from latest backup into clean environment. Trigger: scheduled DR drill. Sev: critical. Tool: `testcontainers`
- `point-in-time-recovery` — Restore to timestamp between backup points. Trigger: PITR window contract. Sev: critical. Tool: `psycopg`
- `rto-verification` — Restore completes inside declared recovery time objective. Trigger: SLA defines recovery time. Sev: critical. Tool: `pytest-timeout`
- `rpo-verification` — Data loss window within declared recovery point objective. Trigger: SLA defines tolerable loss. Sev: critical. Tool: `psycopg`
- `backup-artifact-integrity` — Backup artifacts pass checksum verification before restore. Trigger: corruption suspected in artifacts. Sev: high. Tool: `boto3`
- `hot-snapshot-consistency` — Snapshot taken under write load stays consistent. Trigger: hot-backup policy changed. Sev: high. Tool: `docker`
- `cross-region-restore` — Restore succeeds from replica-region artifacts. Trigger: regional outage runbook. Sev: high. Tool: `testcontainers`
- `schema-drift-restore-compat` — Older backup restores against current schema. Trigger: migrations shipped since backup. Sev: critical. Tool: `alembic`
- `restore-credential-rotation` — Restored environment enforces rotated credentials. Trigger: secrets discovered in backups. Sev: high. Tool: `pytest`
- `backup-encryption-verification` — Backups encrypted and decryptable with managed keys. Trigger: encryption-at-rest audit. Sev: high. Tool: `cryptography`
- `selective-partial-restore` — Single table or tenant restored in isolation. Trigger: granular recovery request. Sev: high. Tool: `psycopg`
- `restore-script-automation` — Restore runs unattended end-to-end. Trigger: runbook-as-code requirement. Sev: medium. Tool: `pytest`
- `backup-schedule-adherence` — Backups produced on schedule per policy. Trigger: cron or retention change. Sev: medium. Tool: `freezegun`
- `retention-purge-enforcement` — Expired backups purged per retention policy. Trigger: retention configuration changed. Sev: medium. Tool: `freezegun`
- `wal-gap-replay` — Write-ahead logs replay to close gap. Trigger: replication lag incident. Sev: critical. Tool: `psycopg`
- `event-log-state-reconstruction` — State rebuilt from snapshots plus event log. Trigger: event-sourced service added. Sev: high. Tool: `pytest`
- `post-restore-smoke-suite` — Restored service passes smoke suite. Trigger: drill exit criteria. Sev: high. Tool: `pytest`
- `post-restore-load-parity` — Restored system sustains baseline traffic. Trigger: capacity assumptions after DR. Sev: medium. Tool: `locust`
- `restore-privilege-enforcement` — Only authorized roles may trigger restore. Trigger: privilege audit finding. Sev: high. Tool: `pytest`
- `external-config-restore` — External endpoints and credentials restored correctly. Trigger: DR config-as-code added. Sev: medium. Tool: `pytest`
- `queue-drain-after-restore` — Queues drained idempotently after restore. Trigger: broker state in DR scope. Sev: medium. Tool: `kombu`
- `backup-immutability-protection` — Backups resist deletion inside retention window. Trigger: ransomware immutability policy. Sev: high. Tool: `boto3`
- `sequence-counter-restore` — Database sequences and counters restored correctly. Trigger: duplicate-key failure post-restore. Sev: high. Tool: `psycopg`
- `dr-runbook-liveness` — Runbook steps execute exactly as written. Trigger: drill notes stale steps. Sev: medium. Tool: `pytest`

## 24. Experimentation & Statistical Testing

Verifies A/B experimentation statistics — assignment integrity, hypothesis validity, and guardrail metrics — as human-gated leaves mostly outside PR-verifier scope.

Tool belt: `scipy`, `statsmodels`, `pandas`

### Granular test types

- `sample-ratio-mismatch-check` — Observed arm counts match configured split ratio. Trigger: experiment ramp configured. Sev: high. Tool: `scipy`
- `assignment-log-integrity` — Assignment log complete and unique per unit. Trigger: duplicate assignment suspected. Sev: high. Tool: `pandas`
- `aa-test-null-result` — A/A test produces no spurious effect. Trigger: new experimentation platform onboarded. Sev: high. Tool: `statsmodels`
- `primary-metric-hypothesis-test` — Primary metric tested against declared hypothesis. Trigger: experiment readout requested. Sev: medium. Tool: `statsmodels`
- `confidence-interval-reporting` — Effects reported with intervals, not p-values alone. Trigger: statistics review of readout. Sev: medium. Tool: `statsmodels`
- `multiplicity-correction` — Family-wise error controlled across many metrics. Trigger: readout covers many metrics. Sev: medium. Tool: `statsmodels`
- `pre-launch-power-analysis` — Sample size supports minimum detectable effect. Trigger: experiment design review. Sev: medium. Tool: `statsmodels`
- `novelty-effect-decay` — Early effects checked for decay over time. Trigger: post-launch readout scheduled. Sev: low. Tool: `pandas`
- `guardrail-nonregression` — Guardrail metrics stay within declared thresholds. Trigger: launch decision checklist. Sev: high. Tool: `pandas`
- `segment-heterogeneity` — Treatment effect stable across key segments. Trigger: segment strategy planned. Sev: medium. Tool: `statsmodels`
- `network-interference-check` — Units do not influence each other's outcomes. Trigger: social or networked feature. Sev: high. Tool: `scipy`
- `randomization-unit-alignment` — Analysis unit matches randomization unit. Trigger: unit mismatch flagged. Sev: high. Tool: `pandas`
- `srm-temporal-stability` — Split ratio stable across time buckets. Trigger: ramp changed mid-flight. Sev: medium. Tool: `scipy`
- `outlier-winsorization-sensitivity` — Conclusions robust to outlier capping choices. Trigger: heavy-tailed metric reported. Sev: low. Tool: `scipy`
- `sequential-peeking-validity` — Repeated peeking accounted in error rates. Trigger: live monitoring dashboard used. Sev: medium. Tool: `statsmodels`
- `covariate-balance-check` — Pre-period covariates balanced across arms. Trigger: stratified assignment used. Sev: medium. Tool: `statsmodels`
- `metric-pipeline-parity` — Metric computed identically across arms. Trigger: metric pipeline changed mid-experiment. Sev: high. Tool: `pandas`
- `exposure-log-completeness` — Exposure events complete and timely. Trigger: ingestion delay suspected. Sev: high. Tool: `pandas`
- `preregistration-conformance` — Analysis matches pre-registered hypothesis document. Trigger: readout deviates from plan. Sev: low. Tool: `pandas`
- `experiment-overlap-conflicts` — Overlapping experiments checked for interaction. Trigger: experiment calendar overlap. Sev: medium. Tool: `scipy`
- `sustained-window-stability` — Long-window readout precedes ship decision. Trigger: launch policy requires sustained cycle. Sev: medium. Tool: `pandas`
- `alert-threshold-justification` — Guardrail alert thresholds statistically justified. Trigger: alerting configuration PR. Sev: low. Tool: `scipy`
- `bootstrap-interval-estimation` — Bootstrap intervals for ratio or quantile metrics. Trigger: nonstandard metric readout. Sev: low. Tool: `scipy`
- `human-gated-readout-signoff` — Experiment readout requires human sign-off before launch. Trigger: verifier reaches experiment-stage change. Sev: low. Tool: `statsmodels`
