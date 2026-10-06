---
category: architecture
topic: layered_architecture
source: SEAM curated knowledge
version: 1.0
status: VALIDATED
---
# Layered Architecture

Description: A structure with presentation, application/service, domain, and persistence layers.

Principles:
- Higher layers depend on lower abstractions, not concrete infrastructure details.
- Keep API routes thin and place business rules in services.
- Keep persistence logic behind repository-style functions when complexity grows.

Recommended practices:
- Use DTOs or Pydantic models at API boundaries.
- Place database access in a data layer.
- Keep UI concerns out of backend services.

Common mistakes:
- Putting all logic in controllers.
- Letting database models leak everywhere.
- Creating too many layers for tiny scripts.

Applicable project types: web apps, CRUD services, admin tools.

Relevant technologies: FastAPI, React, SQLAlchemy, SQLite.
