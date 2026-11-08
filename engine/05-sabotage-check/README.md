# 05 — The Sabotage Check (Mutation)

Tests pass? Still don't trust them.

Deliberately sabotages the PR code (delete a null check, flip a boolean) and reruns the tests.
- Tests catch the sabotage → suite is real.
- Tests miss it → suite is weak, force the Tester to write stricter tests (loop back to Stage 02).
