---
category: coding
topic: api_design
source: SEAM curated knowledge
version: 1.0
status: VALIDATED
---
# API Design

Description: Practices for HTTP APIs used by frontend applications and agents.

Principles:
- API routes should model resources and workflows clearly.
- Use stable request and response schemas.
- Errors should be meaningful and safe.

Recommended practices:
- Use proper status codes.
- Validate request bodies.
- Keep route handlers thin and delegate logic to services.
- Add health and status endpoints.

Common mistakes:
- Returning plain strings for structured errors.
- Overloading one endpoint for unrelated operations.
- Exposing secrets or internal traces.

Applicable project types: FastAPI services, agent backends, CRUD apps.

Relevant technologies: FastAPI, Pydantic, REST, WebSockets.
