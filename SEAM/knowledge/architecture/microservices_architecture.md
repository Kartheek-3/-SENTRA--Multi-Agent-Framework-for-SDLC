---
category: architecture
topic: microservices_architecture
source: SEAM curated knowledge
version: 1.0
status: VALIDATED
---
# Microservices Architecture

Description: Independent deployable services organized around business capabilities.

Principles:
- Use microservices only when team, deployment, and scaling needs justify them.
- Services should own their data.
- Inter-service contracts must be explicit and versioned.

Recommended practices:
- Start from clear bounded contexts.
- Add observability, retries, and failure isolation.
- Prefer asynchronous messaging for decoupled workflows.

Common mistakes:
- Creating distributed systems for small CRUD apps.
- Sharing one database across services.
- Ignoring operational complexity.

Applicable project types: large systems, multi-team products, independently scaled domains.

Relevant technologies: Docker, Kubernetes, message queues, API gateways.
