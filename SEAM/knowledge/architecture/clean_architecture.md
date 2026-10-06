---
category: architecture
topic: clean_architecture
source: SEAM curated knowledge
version: 1.0
status: VALIDATED
---
# Clean Architecture

Description: Dependency-inversion architecture that isolates domain rules from frameworks.

Principles:
- Domain entities should not depend on web frameworks or databases.
- Use interfaces/ports for persistence and external services.
- Keep use cases explicit.

Recommended practices:
- Apply when the domain is complex or expected to evolve.
- Keep adapters small and replaceable.
- Test use cases without web or database dependencies.

Common mistakes:
- Applying clean architecture to tiny CRUD apps with no domain complexity.
- Creating abstractions that do not reduce coupling.

Applicable project types: business workflows, complex domains, long-lived products.

Relevant technologies: Python services, dependency injection, repository interfaces.
