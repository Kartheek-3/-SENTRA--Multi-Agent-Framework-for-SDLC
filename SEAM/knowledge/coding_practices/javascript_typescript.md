---
category: coding
topic: javascript_typescript
source: SEAM curated knowledge
version: 1.0
status: VALIDATED
---
# JavaScript and TypeScript

Description: Frontend coding practices for maintainable browser applications.

Principles:
- Keep component state local unless shared state is required.
- Use typed API client functions.
- Avoid UI updates based on fake progress.

Recommended practices:
- Use small components with clear props.
- Keep fetch logic in API modules.
- Handle loading, empty, success, and error states.

Common mistakes:
- Repeating URL strings across components.
- Ignoring cancellation or stale responses.
- Allowing text overflow in fixed panels.

Applicable project types: React apps, dashboards, IDE panels.

Relevant technologies: React, TypeScript, Vite.
