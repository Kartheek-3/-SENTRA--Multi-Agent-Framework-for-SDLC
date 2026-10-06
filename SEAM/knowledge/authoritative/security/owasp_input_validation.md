---
title: OWASP Input Validation Guidance
category: security
domain: general
topic: input_validation
source_type: AUTHORITATIVE
organization: OWASP
url: https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html
document_version: current
publication_date:
accessed_date: 2026-09-19
license: Creative Commons Attribution-ShareAlike 4.0 International
status: ACTIVE
created_at: 2026-09-19
updated_at: 2026-09-19
---

# OWASP Input Validation Guidance

Engineering use:
- Validate untrusted input at the boundary before it enters business workflows.
- Prefer allowlist validation for structured fields.
- Validate both syntax and business meaning.
- Treat denylist-only validation as insufficient.
- Add server-side checks even when the frontend validates inputs.

SEAM application:
- API request schemas should enforce type, length, range, and allowed values.
- Domain rules such as appointment time ordering, stock limits, and transaction amount ranges should be validated server-side.
- File names and paths must be validated against an allowed project root.
