---
category: coding
topic: python
source: SEAM curated knowledge
version: 1.0
status: VALIDATED
---
# Python Coding Practices

Description: Python guidance for backend services and automation.

Principles:
- Prefer readable functions with clear inputs and outputs.
- Validate external inputs at boundaries.
- Keep side effects explicit.

Recommended practices:
- Use Pydantic models for API contracts.
- Use context managers for files and resources.
- Avoid global mutable state except for controlled service registries.

Common mistakes:
- Swallowing exceptions without recording useful context.
- Mixing path strings without path safety checks.
- Returning inconsistent response shapes.

Applicable project types: FastAPI backends, CLI tools, agents.

Relevant technologies: Python 3.12, FastAPI, Pydantic, pytest.
