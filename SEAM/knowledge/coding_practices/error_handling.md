---
category: coding
topic: error_handling
source: SEAM curated knowledge
version: 1.0
status: VALIDATED
---
# Error Handling

Description: Practices for safe error reporting and recovery.

Principles:
- Fail fast on invalid inputs.
- Keep user-facing errors clear.
- Log enough context for debugging without exposing secrets.

Recommended practices:
- Convert expected domain failures into structured responses.
- Preserve stack traces in server logs only.
- Use bounded retries for transient external failures.

Common mistakes:
- Retrying validation failures.
- Returning raw exceptions to clients.
- Leaving long-running jobs permanently running.

Applicable project types: APIs, agent workflows, background jobs.

Relevant technologies: FastAPI, Python logging, event stores.
