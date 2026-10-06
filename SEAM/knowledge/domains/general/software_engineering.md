---
title: General Software Engineering Domain Guidance
category: domain
domain: general
topic: general_software_engineering
source: SEAM curated/validated knowledge repository
version: 1.0
status: VALIDATED
created_at: 2026-09-19
updated_at: 2026-09-19
---

# General Software Engineering Domain Guidance

Description: Cross-domain guidance that may be used alongside domain-specific knowledge.

Principles:
- Separate user workflows, domain rules, persistence, and presentation.
- Prefer simple architecture for small systems and introduce complexity only when justified.
- Make requirements traceable from analysis to design, implementation, and QA.

Recommended practices:
- Validate external input at the API boundary.
- Keep durable records for important state changes.
- Write small focused tests around domain rules.
- Use consistent naming for entities and API contracts.

Common mistakes:
- Jumping to distributed architecture too early.
- Letting UI-only validation become the security boundary.
- Omitting traceability between requirements and implementation tasks.

Applicable project types: web apps, internal tools, dashboards, workflow systems.

Relevant technologies: FastAPI, React, SQL databases, pytest.
