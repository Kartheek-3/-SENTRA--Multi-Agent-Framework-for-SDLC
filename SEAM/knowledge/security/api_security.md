---
category: security
topic: api_security
source: SEAM curated knowledge
version: 1.0
status: VALIDATED
---
# API Security

Description: Securing HTTP and WebSocket APIs.

Principles:
- Expose only necessary data.
- Validate every request.
- Treat WebSocket messages as untrusted input.

Recommended practices:
- Use CORS deliberately.
- Avoid returning secrets in health endpoints.
- Add authentication and authorization when user data exists.

Common mistakes:
- Logging authorization headers.
- Sending internal stack traces to clients.
- Broadcasting sensitive events.

Applicable project types: web backends, IDE backends, agent systems.

Relevant technologies: FastAPI, WebSockets, CORS.
