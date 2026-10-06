---
category: testing
topic: testing_best_practices
source: SEAM curated knowledge
version: 1.0
status: VALIDATED
---
# Testing Best Practices

Description: General testing guidance for generated projects.

Principles:
- Combine deterministic checks with semantic review.
- Fail fast on syntax and security issues.
- Keep QA independent from coding.

Recommended practices:
- Run syntax checks before expensive semantic QA.
- Validate generated files physically exist.
- Check requirement traceability.

Common mistakes:
- Treating LLM QA as proof of correctness.
- Ignoring missing files because text output looked plausible.

Applicable project types: generated apps, agent workflows, CI pipelines.

Relevant technologies: pytest, npm test, static analysis.
