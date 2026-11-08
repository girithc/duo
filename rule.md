# Duo — Engineering Rules

These rules govern **all code in this repo** — and they are also the values Duo
itself enforces on the PRs it reviews. A verifier that fakes is worthless.

## 1. No mocks allowed

Never mock — not in product code, not in tests. Use real inputs: real local git
fixture repos, real diffs, real API calls. A mocked test proves nothing about
reality; it only proves the mock works.

## 2. No placeholders allowed

No stubs that return fake data, no dummy values standing in for real behavior,
no "will finish later" paths that still return something. Unfinished code must
**stop the run loudly** (e.g. raise `NotImplementedError`) — that is a loud
failure, which is allowed. A placeholder pretending to work is not.

## 3. Errors are returned, never filtered

Every error is raised/propagated with full context (status, source, message).
Never catch-and-swallow, never collapse multiple errors into one silent
success, never trim the error list to make output look clean. If 5 things
failed, the caller sees 5 failures.

## 4. When not sure — mark it HAVE-TO-DO

Uncertainty is never resolved by guessing silently. Mark the exact spot with
`HAVE-TO-DO:` and what is unverified. A visible debt is fixable; a hidden
assumption ships a bug.

## 5. Better to fail than silently falsely pass

Any check that cannot complete must **fail visibly**. A pass is only a pass
when it was actually verified. When in doubt, block — a false pass in a
verifier is the one unforgivable bug.

---

**Enforcement:** PRs to this repo are reviewed against exactly these five
rules. Grep-able markers: `HAVE-TO-DO:` (allowed, must be visible),
mock/placeholder patterns (not allowed).
