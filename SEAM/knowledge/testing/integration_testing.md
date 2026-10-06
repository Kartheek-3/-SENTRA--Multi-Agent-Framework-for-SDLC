---
category: testing
topic: integration_testing
source: SEAM curated knowledge
version: 1.0
status: VALIDATED
---
# Integration Testing

Description: Testing interactions between components such as API routes and databases.

Principles:
- Validate real boundaries.
- Use isolated test databases.
- Keep external services controlled.

Recommended practices:
- Test API request/response contracts.
- Verify persistence effects.
- Use temporary directories for file operations.

Common mistakes:
- Running destructive tests against production data.
- Mocking the integration being tested.

Applicable project types: web APIs, RAG systems, workflow engines.

Relevant technologies: pytest, FastAPI TestClient, SQLite.
