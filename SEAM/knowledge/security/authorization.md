---
category: security
topic: authorization
source: SEAM curated knowledge
version: 1.0
status: VALIDATED
---
# Authorization

Description: Deciding whether an authenticated caller may perform an action.

Principles:
- Authorization must be enforced on the server.
- Check ownership and roles close to the operation.
- Deny by default.

Recommended practices:
- Model roles and permissions explicitly.
- Check resource ownership for user-owned records.
- Keep admin-only actions separate.

Common mistakes:
- Hiding UI controls but leaving API access open.
- Trusting client-provided role values.

Applicable project types: multi-user apps, dashboards, APIs.

Relevant technologies: FastAPI dependencies, RBAC, policy checks.
