---
category: domain
topic: data_engineering
source: SEAM curated knowledge
version: 1.0
status: VALIDATED
---
# Data Engineering

Description: Guidance for systems that ingest, transform, validate, and expose datasets.

Principles:
- Preserve lineage from source to output.
- Validate schema at ingestion boundaries.
- Make transformations reproducible.

Recommended practices:
- Track source metadata and timestamps.
- Separate raw, processed, and published data.
- Log failed records with safe diagnostic detail.

Common mistakes:
- Mutating raw data without preserving original copies.
- Hiding transformation failures.
- Mixing operational and analytical schemas.

Applicable project types: ETL jobs, reporting tools, analytics dashboards.

Relevant technologies: Python, SQL, queues, object storage.
