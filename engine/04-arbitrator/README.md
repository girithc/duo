# 04 — The Arbitrator (Judge)

On test failure: looks at the crash log, the ticket, the PR code, and the failing test.

Decides:
- Builder wrote bad code → PR is genuinely defective, block/rollback.
- Tester hallucinated a rule not in the ticket → correct the Tester, regenerate tests.

Guards against the verifier's own blind spots.
