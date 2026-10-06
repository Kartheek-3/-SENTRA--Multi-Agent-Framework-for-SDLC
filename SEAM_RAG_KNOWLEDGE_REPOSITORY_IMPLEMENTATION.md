# SEAM RAG Knowledge Repository Implementation

## Summary

SEAM now has a real shared RAG + ChromaDB knowledge repository. It is not a new agent. It is backend infrastructure used by the existing agents for contextual retrieval during analysis, planning, coding, and QA.

## Implemented

- Added curated Markdown knowledge under `SEAM/knowledge`.
- Added deterministic document discovery and indexing from `SEAM/knowledge/**/*.md`.
- Added deterministic document IDs based on repository-relative paths.
- Added real chunk metadata: category, source path, document ID, topic, version, validation status.
- Added explicit deterministic local embeddings for ChromaDB upsert/query.
- Preserved validated-only retrieval by default.
- Added RAG API endpoints:
  - `POST /rag/index`
  - `POST /rag/retrieve`
  - `GET /rag/status`
- Added RAG event emission for indexing and retrieval.
- Added UI event mapping so RAG usage appears in the SEAM AI stream.
- Integrated RAG retrieval into existing agents:
  - Analysis Agent
  - Planning Agent
  - Coding Agent
  - QA Agent

## Knowledge Documents

Documents on disk: 27

Indexed documents: 27

ChromaDB chunks/records: 27

Categories:

- `domain`
- `architecture`
- `coding`
- `security`
- `testing`
- `reusable_code`
- `past_project`
- `lesson_learned`
- `repository`

## Validation

Backend compile:

- `python -m compileall backend`
- Result: PASS

Frontend build:

- `npm.cmd run build`
- Result: PASS

Focused RAG tests:

- `python -m pytest tests\test_rag_repository.py tests\test_knowledge.py -q`
- Result: PASS
- Output: `9 passed`

RAG indexing check:

- Documents discovered: 27
- Documents indexed: 27
- Chunks indexed: 27
- Collection count: 27
- Result: PASS

RAG API check:

- `GET /rag/status`: PASS
- `POST /rag/retrieve`: PASS
- Example retrieval returned `security/authentication.md` for a JWT/FastAPI authentication query.

Full backend test suite:

- `python -m pytest tests -q`
- Result: FAIL
- Summary: 31 passed, 29 failed
- The observed failures are pre-existing/non-RAG suite issues around mock model-router signatures, `ProjectState.qa_feedback`, and supervisor artifact tests requiring project registration.

## Notes

The ChromaDB repository now passes embeddings explicitly instead of storing a new Chroma embedding function. This avoids conflicts with existing persisted Chroma collections created with a different embedding configuration.

Delivery Agent knowledge write-back existed previously through `KnowledgeService.update_knowledge`. This phase added retrieval integration to Analysis, Planning, Coding, and QA. Delivery retrieval can be added later if the delivery workflow needs repository context before packaging.
