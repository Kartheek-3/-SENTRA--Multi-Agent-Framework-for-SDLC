---
category: testing
topic: regression_testing
source: SEAM curated knowledge
version: 1.0
status: VALIDATED
---
# Regression Testing

Description: Tests that protect behavior after changes.

Principles:
- Every fixed bug should have a targeted regression test when practical.
- Keep regression tests stable and focused.
- Test the observable failure mode.

Recommended practices:
- Add tests around agent routing, artifact persistence, and API contracts.
- Run existing tests before release.

Common mistakes:
- Adding broad flaky tests that obscure the actual bug.
- Skipping tests after refactors.

Applicable project types: long-lived apps, agent frameworks.

Relevant technologies: pytest, CI, build scripts.
