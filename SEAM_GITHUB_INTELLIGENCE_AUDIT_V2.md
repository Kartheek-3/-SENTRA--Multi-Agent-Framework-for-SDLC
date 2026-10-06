# SEAM GitHub Intelligence Audit v2

Date: 2026-09-19

## Current Capabilities Before v2

- GitHub REST API client exists in `SEAM/backend/github/github_client.py`.
- Repository search and ranking exist through:
  - `backend/github/repository_service.py`
  - `backend/github/repository_analyzer.py`
  - `backend/github/repository_ranker.py`
- Analysis agent calls GitHub Intelligence as a capability through `backend/tools/github_intelligence.py`.
- GitHub findings are stored in `ProjectState.github_findings`, `github_selection`, and `github_status`.
- WebSocket/chat rendering already recognizes existing GitHub events.

## Current Data Structures

- `RepositoryCandidate`
- `RepositoryEvaluation`
- `RepositorySelection`
- `ProjectState.github_selection`
- `ProjectState.github_findings`
- `ProjectState.github_status`

## Current API Endpoints Before v2

- `GET /api/projects/{project_id}/repositories`
- System health reports GitHub token presence.

There was no dedicated repository registry API and no webhook endpoint.

## Current Limitations Before v2

- No persistent repository registry.
- No repository commit version tracking.
- No file-level SHA manifest.
- No change detection.
- No incremental repository analysis.
- No webhook support.
- No stale-context contract for agents.
- No repository-specific RAG lifecycle.
- Repository context could be used without explicit freshness metadata.

## Storage Before v2

- Repository search results were stored only in project state and generated analysis artifacts.
- There was no durable repository snapshot or versioned repository intelligence record.

## Commit/File SHA Tracking Before v2

- Commit SHA tracking: not implemented.
- File SHA tracking: not implemented.

## RAG Before v2

- General RAG/ChromaDB exists under `backend/knowledge/*`.
- Repository-derived knowledge was not versioned separately from general SEAM knowledge.

## Files Modified Or Added For v2

- `backend/github/intelligence_models.py`
- `backend/github/registry.py`
- `backend/github/intelligence_service.py`
- `backend/github/github_client.py`
- `backend/api/github.py`
- `backend/main.py`
- `backend/models/state.py`
- `backend/tools/github_intelligence.py`
- `backend/knowledge/models.py`
- `seam-ide/src/seam/eventToChatMessage.ts`
- GitHub v2 tests under `SEAM/tests/test_github_*.py`

