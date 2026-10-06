---
category: domain
topic: web_applications
source: SEAM curated knowledge
version: 1.0
status: VALIDATED
---
# Web Applications

Description: Knowledge for browser-based applications with backend APIs and persistent data.

Principles:
- The frontend should call stable API contracts.
- The backend owns validation, persistence, and authorization.
- The database schema should reflect domain entities.

Recommended practices:
- Use typed request and response models.
- Return clear HTTP status codes.
- Keep client-side state predictable.
- Add health checks and basic error responses.

Common mistakes:
- Trusting browser input.
- Creating API endpoints without schema validation.
- Treating frontend-only validation as security.

Applicable project types: todo apps, expense trackers, notes apps, inventory systems.

Relevant technologies: React, FastAPI, SQLite, PostgreSQL, REST.
