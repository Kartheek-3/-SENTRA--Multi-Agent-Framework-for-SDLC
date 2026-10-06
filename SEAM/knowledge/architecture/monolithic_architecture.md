---
category: architecture
topic: monolithic_architecture
source: SEAM curated knowledge
version: 1.0
status: VALIDATED
---
# Monolithic Architecture

Description: A single deployable application containing UI/backend or backend modules.

Principles:
- Prefer a modular monolith for small products.
- Keep module boundaries clear even in one process.
- Optimize for simple development and deployment.

Recommended practices:
- Use clear packages for routes, services, schemas, and persistence.
- Keep deployment instructions simple.
- Add tests around module boundaries.

Common mistakes:
- Confusing monolith with unstructured code.
- Splitting into services too early.

Applicable project types: small SaaS, prototypes, internal tools.

Relevant technologies: FastAPI, React, SQLite, Docker.
