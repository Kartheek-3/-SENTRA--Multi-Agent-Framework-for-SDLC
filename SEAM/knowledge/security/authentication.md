---
category: security
topic: authentication
source: SEAM curated knowledge
version: 1.0
status: VALIDATED
---
# Authentication

Description: Verifying user or service identity.

Principles:
- Authentication answers who the caller is.
- Passwords and tokens must never be logged.
- Session and token lifetimes should be explicit.

Recommended practices:
- Use established libraries for password hashing and token verification.
- Validate issuer, audience, signature, and expiry for JWTs.
- Add rate limiting for login endpoints.

Common mistakes:
- Storing plaintext passwords.
- Accepting unsigned or expired tokens.
- Confusing authentication with authorization.

Applicable project types: user-facing apps, admin tools, APIs.

Relevant technologies: OAuth2, JWT, FastAPI security utilities.
