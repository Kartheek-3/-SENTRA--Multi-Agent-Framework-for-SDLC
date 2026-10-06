---
category: coding
topic: database_practices
source: SEAM curated knowledge
version: 1.0
status: VALIDATED
---
# Database Practices

Description: Database guidance for small web apps and service backends.

Principles:
- Schema should reflect domain entities.
- Use migrations or explicit initialization.
- Keep persistence operations predictable.

Recommended practices:
- Add created_at and updated_at where useful.
- Use primary keys and constraints.
- Keep transactions small.
- Avoid storing derived UI-only state.

Common mistakes:
- Trusting user IDs without authorization checks.
- Using unparameterized SQL.
- Creating tables directly inside request handlers.

Applicable project types: expense trackers, notes apps, inventory tools.

Relevant technologies: SQLite, PostgreSQL, SQLAlchemy.
