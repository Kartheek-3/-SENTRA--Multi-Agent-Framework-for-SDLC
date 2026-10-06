---
category: security
topic: secrets_management
source: SEAM curated knowledge
version: 1.0
status: VALIDATED
---
# Secrets Management

Description: Handling tokens, passwords, API keys, and credentials.

Principles:
- Secrets belong in environment variables or secret managers.
- Never commit secrets.
- Rotate exposed credentials immediately.

Recommended practices:
- Provide `.env.example` without real values.
- Redact secrets in logs and artifacts.
- Avoid sending tokens to the frontend.

Common mistakes:
- Pasting tokens into chat, code, or README files.
- Writing secrets into generated artifacts.

Applicable project types: any project with external APIs or authentication.

Relevant technologies: dotenv, environment variables, GitHub tokens.
