---
category: domain
topic: general_software_engineering
source: SEAM curated knowledge
version: 1.0
status: VALIDATED
---
# General Software Engineering

Description: Guidance for small to medium software systems where correctness, maintainability, and clear requirements matter.

Principles:
- Trace implementation tasks to requirements.
- Prefer simple architecture until scale requirements justify complexity.
- Separate domain logic, persistence, API boundaries, and UI behavior.

Recommended practices:
- Write explicit functional and non-functional requirements.
- Define data entities and API contracts before coding.
- Keep configuration separate from code.

Common mistakes:
- Building infrastructure before confirming requirements.
- Mixing UI state, API logic, and persistence rules.
- Skipping validation and error handling.

Applicable project types: CRUD apps, dashboards, internal tools, lightweight SaaS prototypes.

Relevant technologies: Python, TypeScript, REST APIs, SQL databases.
