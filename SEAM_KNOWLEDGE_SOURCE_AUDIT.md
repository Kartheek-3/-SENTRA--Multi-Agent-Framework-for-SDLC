# SEAM Knowledge Source Audit

## Existing Knowledge Sources

Existing local sources were already stored under `SEAM/knowledge`.

Before this phase, most documents were SEAM-written Markdown files with frontmatter such as:

- `category`
- `topic`
- `source`
- `version`
- `status`

The existing active ingestion path is:

- `backend/knowledge/indexer.py`
- `backend/knowledge/document_processor.py`
- `backend/knowledge/chroma_repository.py`
- `backend/knowledge/knowledge_service.py`

The older `backend/rag/retriever.py` and `backend/rag/vector_store.py` files are placeholder code and are not the active retrieval implementation.

## Existing Metadata

Existing metadata supported category, topic, source, version, status, document ID, and tags.

Missing before this phase:

- explicit source type hierarchy
- source ID
- organization
- URL
- document version/date/access date
- license
- academic fields
- project-derived validation metadata

## Existing Ingestion Pipeline

Implemented flow:

1. Discover `SEAM/knowledge/**/*.md`.
2. Parse Markdown frontmatter.
3. Create `KnowledgeDocument`.
4. Chunk content through `DocumentProcessor`.
5. Attach metadata to each chunk.
6. Embed with FastEmbed.
7. Persist chunks in ChromaDB.

## Existing Validation Mechanism

Before this phase, production retrieval used `VALIDATED` status.

This phase keeps compatibility with `VALIDATED` and also supports `ACTIVE` for source-lifecycle documents.

Production retrieval now allows:

- `VALIDATED`
- `ACTIVE`

Unvalidated statuses are excluded from normal RAG:

- `PENDING`
- `REVIEWED`
- `REJECTED`
- `ARCHIVED`
- `SOURCE_UNAVAILABLE`

## Missing Capabilities Addressed

- Added `KnowledgeSource` Pydantic model.
- Added explicit source types:
  - `AUTHORITATIVE`
  - `ACADEMIC`
  - `OFFICIAL_TECHNICAL_DOCUMENTATION`
  - `SEAM_CURATED`
  - `VALIDATED_PROJECT_KNOWLEDGE`
  - `LESSON_LEARNED`
- Added source validation for required metadata.
- Added official-domain validation for authoritative and official documentation URLs.
- Added source-aware ranking preference.
- Preserved source metadata through chunking, FastEmbed, ChromaDB, retrieval, agent context, and domain artifacts.

## Modified Files

- `backend/knowledge/models.py`
- `backend/knowledge/document_processor.py`
- `backend/knowledge/indexer.py`
- `backend/knowledge/chroma_repository.py`
- `backend/knowledge/knowledge_service.py`
- `backend/knowledge/domain_intelligence.py`
- `backend/models/domain.py`
- `tests/test_knowledge_sources.py`
- `SEAM/knowledge/authoritative/**`
- `SEAM/knowledge/official_docs/**`
- `SEAM/knowledge/academic/**`
- `SEAM/knowledge/validated_project_knowledge/**`
- `SEAM/knowledge/lessons_learned/validated_source_metadata.md`
