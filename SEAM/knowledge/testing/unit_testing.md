---
category: testing
topic: unit_testing
source: SEAM curated knowledge
version: 1.0
status: VALIDATED
---
# Unit Testing

Description: Testing small units of behavior in isolation.

Principles:
- Tests should be deterministic.
- Test behavior, not implementation details.
- Keep fixtures minimal.

Recommended practices:
- Cover validation, edge cases, and error paths.
- Use mocks only at external boundaries.
- Name tests by expected behavior.

Common mistakes:
- Testing only happy paths.
- Depending on test execution order.

Applicable project types: APIs, services, utilities.

Relevant technologies: pytest, vitest.
