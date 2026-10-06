---
title: Python 3 Documentation
category: coding
domain: general
topic: python
source_type: OFFICIAL_TECHNICAL_DOCUMENTATION
organization: Python Software Foundation
url: https://docs.python.org/3/
document_version: 3
publication_date:
accessed_date: 2026-09-19
license: PSF License
status: ACTIVE
created_at: 2026-09-19
updated_at: 2026-09-19
---

# Python 3 Documentation

Engineering use:
- Prefer standard-library features and idiomatic language constructs before adding dependencies.
- Use the official language and library reference for behavior-sensitive decisions.
- Keep code simple, explicit, and readable.

SEAM application:
- Generated Python code should use context managers for files and connections.
- Error handling should catch specific exceptions where possible.
- Tests should use Python-native tooling such as `pytest` when available in the project.
