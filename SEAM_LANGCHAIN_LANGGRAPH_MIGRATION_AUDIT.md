# SEAM LangChain/LangGraph Migration Audit

Date: 2026-09-19

## Summary

SEAM already had a real LangChain and LangGraph foundation before this pass. The migration work is therefore an integration hardening pass, not a rewrite.

## Existing LangChain Usage

- `backend/agents/analysis_agent.py` builds a `ChatPromptTemplate | llm` chain and parses responses with `PydanticOutputParser`.
- `backend/agents/planning_agent.py` uses LangChain prompt and parser primitives for planning/design output.
- `backend/agents/coding_agent.py` uses LangChain prompt composition for code generation tasks.
- `backend/agents/qa_agent.py` uses LangChain prompt composition for QA output.
- `backend/tools/diagram_generator.py` uses LangChain prompt/parser primitives for structured React Flow diagram generation.

## Existing LangGraph Usage

- `backend/graph/workflow.py` creates a `StateGraph(ProjectState)`.
- The compiled graph has these nodes:
  - `Supervisor`
  - `AnalysisAgent`
  - `PlanningAgent`
  - `CodingAgent`
  - `QAAgent`
  - `DeliveryAgent`
- Agents return control to `Supervisor`, and `Supervisor.current_agent` selects the next graph edge.
- The existing `SupervisorAgent` remains the workflow authority.

## Existing Qwen/Ollama Usage

- `backend/llm/model_router.py` uses `langchain_ollama.ChatOllama`.
- Default model configuration now resolves through:
  - `SEAM_LLM_PROVIDER=ollama`
  - `SEAM_LLM_MODEL=qwen3-coder-next`
  - task model overrides such as `SEAM_CODING_MODEL`
- Analysis, planning, coding, and QA default to the configured primary Qwen model unless an environment override is supplied.

## RAG Status

- Knowledge storage and retrieval live under `backend/knowledge/*`.
- ChromaDB is the persistent vector store.
- Domain-aware retrieval is already available through `KnowledgeService.retrieve_domain_aware`.
- This pass adds `SEAMKnowledgeRetriever`, a LangChain `BaseRetriever` adapter over the existing knowledge service.

## Gaps Closed In This Pass

- Added `langchain-ollama` as an explicit dependency.
- Added explicit primary model/provider configuration.
- Added model availability health reporting for `qwen3-coder-next`.
- Added a LangChain retriever adapter for the existing SEAM RAG layer.
- Added focused tests for:
  - LangChain agent invocation
  - LangChain/Ollama model routing
  - Qwen3-Coder-Next configuration
  - LangGraph workflow compilation and node registration
  - Supervisor-controlled rework routing
  - LangChain retriever integration with Chroma-backed RAG

## Remaining Runtime Dependency

Actual Qwen generation depends on local Ollama serving the configured model:

```powershell
ollama list
ollama pull qwen3-coder-next
```

No fallback model is hardcoded by this migration.

