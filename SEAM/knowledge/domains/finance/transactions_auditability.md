---
title: Finance Transactions And Auditability
category: domain
domain: finance
topic: transactions_auditability
source: SEAM curated/validated knowledge repository
version: 1.0
status: VALIDATED
created_at: 2026-09-19
updated_at: 2026-09-19
---

# Finance Transactions And Auditability

Description: Domain guidance for applications that record expenses, balances, ledgers, or financial transactions.

Principles:
- Financial records should be append-friendly and auditable.
- Every transaction should have an actor, timestamp, amount, currency, category, and status.
- Corrections should preserve history rather than silently rewriting important records.

Recommended practices:
- Use decimal-safe numeric handling for money.
- Keep created_at and updated_at timestamps.
- Record audit events for transaction creation, approval, update, deletion, and export.
- Separate draft, posted, reversed, and void states where relevant.

Common mistakes:
- Using floating point numbers for money.
- Deleting transaction history without an audit trail.
- Mixing reporting summaries with source transaction records.

Applicable project types: expense trackers, transaction ledgers, finance dashboards, billing systems.

Relevant technologies: SQL constraints, Decimal, audit tables, report queries.
