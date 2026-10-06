---
category: architecture
topic: event_driven_architecture
source: SEAM curated knowledge
version: 1.0
status: VALIDATED
---
# Event-Driven Architecture

Description: Components communicate by publishing and consuming events.

Principles:
- Events represent facts that happened.
- Event consumers should be idempotent.
- Terminal workflow events should be durable and delivered promptly.

Recommended practices:
- Use event names and schemas consistently.
- Separate command handling from event publication.
- Store enough metadata for replay and debugging.

Common mistakes:
- Emitting fake progress.
- Losing events due to non-durable queues.
- Using events where synchronous validation is required.

Applicable project types: workflows, notifications, audit trails, agent systems.

Relevant technologies: WebSockets, append-only logs, queues.
