---
category: security
topic: input_validation
source: SEAM curated knowledge
version: 1.0
status: VALIDATED
---
# Input Validation

Description: Ensuring external data is safe and shaped as expected.

Principles:
- Validate at API boundaries.
- Normalize data before persistence.
- Reject unexpected fields where possible.

Recommended practices:
- Use Pydantic models for request validation.
- Use parameterized database queries.
- Validate file paths against an allowed root.

Common mistakes:
- Trusting frontend validation.
- Concatenating SQL strings.
- Allowing path traversal with `..`.

Applicable project types: APIs, file managers, code generators.

Relevant technologies: Pydantic, SQLAlchemy, pathlib.
