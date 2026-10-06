# SEAM GitHub Incremental Intelligence Report

Date: 2026-09-19

## Implementation

GitHub Intelligence v2 adds change-aware repository intelligence while keeping the existing GitHub REST API.

## Repository Registry

Persistent JSON registry:

- Records: `.seam/github_intelligence/records`
- Snapshots: `.seam/github_intelligence/snapshots`
- Change sets: `.seam/github_intelligence/changes`
- RAG supersession markers: `.seam/github_intelligence/rag_status`

## Snapshot Mechanism

Each analyzed repository stores a lightweight manifest:

- path
- file SHA
- size
- type
- language
- last analyzed commit

Full source code is not stored.

## Commit Tracking

`RepositoryRecord` tracks:

- `current_commit_sha`
- `last_analyzed_commit_sha`
- `analysis_version`
- `last_analyzed_at`
- `status`
- `stale`

## Change Detection

Changed repositories use GitHub compare API through:

`GET /repos/{owner}/{repo}/compare/{before}...{after}`

Detected statuses:

- added
- modified
- removed/deleted
- renamed

## Incremental Analysis

If the latest commit differs from the last analyzed commit, SEAM analyzes only changed file paths and lightweight dependent components derived from static path relationships.

This is a bounded static approximation, not a compiler-level dependency graph.

## Webhooks

Endpoint:

`POST /api/github/webhook`

Supported event:

- `push`

Security:

- Requires `X-Hub-Signature-256`
- Uses `GITHUB_WEBHOOK_SECRET`
- Fails closed if the secret is missing

Webhook requests acknowledge quickly and schedule refresh through FastAPI background tasks.

## Polling / On-Demand Freshness

Endpoint:

`POST /api/github/repositories/refresh`

If unchanged, cached intelligence is reused.

If changed, incremental analysis runs.

## Stale Handling

If GitHub API fails:

- Existing cached intelligence becomes `STALE`
- Missing intelligence becomes `UNAVAILABLE`
- Agent context includes repository, commit, analysis version, status, and last analyzed time

## RAG Integration

Repository-derived knowledge uses:

- `source_type = GITHUB_REPOSITORY`
- repository commit identity in source URI
- analysis version in metadata/tags

Old context is marked superseded through a lifecycle marker. Historical metadata is retained.

## Event/WebSocket Integration

New events:

- `GITHUB_REPOSITORY_DISCOVERED`
- `GITHUB_REPOSITORY_ANALYSIS_STARTED`
- `GITHUB_REPOSITORY_ANALYSIS_COMPLETED`
- `GITHUB_REPOSITORY_CHANGED`
- `GITHUB_INCREMENTAL_ANALYSIS_STARTED`
- `GITHUB_INCREMENTAL_ANALYSIS_COMPLETED`
- `GITHUB_REPOSITORY_CURRENT`
- `GITHUB_REPOSITORY_STALE`
- `GITHUB_WEBHOOK_RECEIVED`

The SEAM IDE chat mapper renders these events.

## Security

- GitHub token is loaded from environment only.
- Token is not logged or written to artifacts.
- Webhook secret is loaded from environment only.
- Repository content is treated as untrusted input.
- SEAM does not execute repository code during analysis.

## Tests Added

- `tests/test_github_repository_registry.py`
- `tests/test_github_change_detection.py`
- `tests/test_github_incremental_analysis.py`
- `tests/test_github_webhook.py`
- `tests/test_github_stale_context.py`
- `tests/test_github_rag_versioning.py`

## Validation Limitation

Automated tests were added but could not be executed in this shell because no Python interpreter or expected virtual environment was discoverable.

## Real Integration Result

Not executed in this pass. No real repository push/change test was run, so SEAM should be described as `change-aware repository intelligence`, not experimentally proven real-time GitHub intelligence.

## Performance

No full vs incremental timing was measured because tests could not be run from this shell and no real repository update test was executed.

## Known Limitations

- Dependency impact analysis is path/name based.
- RAG supersession is recorded through lifecycle markers; bulk Chroma metadata mutation is not implemented.
- Webhook processing uses FastAPI background tasks, not a durable external queue.
- UI has event rendering for GitHub freshness, but no dedicated full repository intelligence panel yet.

