# SEAM Current System Audit

## Implemented Components

- FastAPI backend with project, filesystem, artifact, knowledge, and RAG APIs.
- Standalone SEAM IDE frontend with WebSocket event streaming and Explorer integration.
- Multi-agent workflow components: Analysis, Supervisor, Planning, Coding, QA, Delivery.
- RAG infrastructure under `backend/knowledge/*` using Markdown knowledge documents, FastEmbed embeddings, and ChromaDB persistence.
- Domain-aware intelligence with structured domain identification, domain-filtered retrieval, domain context artifacts, and cross-domain tests.
- Knowledge source provenance with explicit source types, source metadata validation, and source-aware retrieval ranking.
- Artifact pipeline that writes physical files under `generated_projects/<project>` and registers them through `ArtifactRegistry`.
- Event bus/EventStore that records backend events and streams them to the UI.

## Partially Implemented Components

- Agent lifecycle events exist, but not every direct unit-test path emits terminal lifecycle events.
- Workflow timeout/cancellation is configured in parts, but full cancellation/reconnect validation has not been completed.
- Full real LLM end-to-end workflow has not been executed in this audit phase.
- Baseline-vs-domain experiment is not yet executed.
- Performance evidence exists for focused tests and builds, but not full multi-run P50/P95 workflow timings.

## Known Failures Before Stabilization

- Legacy tests use `MockModelRouter.get_model()` without a task-type argument, while agents now request task-specific models.
- `ProjectState` did not define `qa_feedback` or `pending_qa_knowledge`, although QA/Coding/Delivery use those fields.
- Supervisor unit tests construct `ProjectState` directly without registering it in `projects_db`, while artifact registration requires a project.
- Full historical test suite previously reported `36 passed, 29 failed, 1 warning`.
- A full-suite run after source-provenance work was stopped after roughly three minutes with no final summary.

## Test Status

Validated focused tests before this audit:

- Source/domain/RAG focused suite: `18 passed in 93.47s`
- Backend compile: PASS
- Frontend build: PASS

Not validated:

- Full backend suite green status.
- Full real SEAM E2E workflow.
- Healthcare/ecommerce/finance real LLM workflow experiments.
- Domain-aware versus baseline execution comparison.

## RAG Status

- Active implementation: `backend/knowledge/*`
- Placeholder legacy package: `backend/rag/*`
- Repository status from latest provenance work:
  - 48 documents
  - 53 Chroma chunks
  - source types: SEAM curated, authoritative, official technical documentation, academic, validated project knowledge, lesson learned
- Retrieval uses production statuses `VALIDATED` and `ACTIVE`.

## Domain Intelligence Status

- Implemented for healthcare, ecommerce, finance, and general engineering.
- Domain context is persisted as:
  - `analysis/domain_context.md`
  - `analysis/domain_context.json`
  - `analysis/domain_traceability.md`
  - `analysis/domain_traceability.json`
- Cross-domain isolation is covered by focused tests.
- Real workflow experiment evidence is still missing.

## Agent Integration Status

- Analysis identifies domain and retrieves domain context.
- Planning receives domain-aware context.
- Coding receives generic RAG and domain-aware context.
- QA receives domain-aware context.
- Delivery refreshes/uses domain context where available.

## Workflow Issues

- Terminal lifecycle consistency needs stronger enforcement for direct workflow execution.
- Stop/cancel/timeout behavior needs explicit validation.
- Planning has previously appeared RUNNING indefinitely in UI; root cause likely lifecycle/event terminal-state consistency rather than only model generation.

## Missing Evidence

- Healthcare, ecommerce, and finance complete real workflow runs.
- Baseline versus domain-aware comparison using the same requirement.
- Full E2E expense tracker workflow including QA/rework/delivery.
- Explorer synchronization proof for all generated artifacts in an end-to-end run.
- Raw timing measurements for all phases from real workflows.

## LangChain/LangGraph/Qwen Audit Update - 2026-09-19

- LangChain is the active agent invocation layer for Analysis, Planning, Coding, QA, and diagram generation.
- LangGraph is the active workflow orchestration layer through `backend/graph/workflow.py`.
- `SupervisorAgent` remains the source of routing decisions; LangGraph executes those decisions.
- `qwen3-coder-next` is now the default primary model through `SEAM_LLM_MODEL`.
- `langchain-ollama` is now an explicit dependency.
- The existing RAG/ChromaDB knowledge layer now has a LangChain retriever adapter: `SEAMKnowledgeRetriever`.
- New focused tests cover LangChain invocation, Qwen routing, LangGraph graph registration, Supervisor rework routing, and LangChain RAG retrieval.
- Local test execution for this audit pass was blocked because this shell could not locate a Python interpreter or the expected virtual environment.
