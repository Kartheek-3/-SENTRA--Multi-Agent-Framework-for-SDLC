# SEAM LangChain/LangGraph Implementation Report

Date: 2026-09-19

## Implemented

SEAM now has explicit LangChain, LangGraph, Qwen3-Coder-Next, and RAG integration points while preserving the existing architecture.

## Model Configuration

Primary model configuration is centralized in `backend/config.py`.

```text
SEAM_LLM_PROVIDER=ollama
SEAM_LLM_MODEL=qwen3-coder-next
```

The existing per-agent model variables still work as overrides:

- `SEAM_ANALYSIS_MODEL`
- `SEAM_PLANNING_MODEL`
- `SEAM_CODING_MODEL`
- `SEAM_QA_MODEL`

## LangChain

LangChain remains the LLM invocation layer for the SEAM agents. Agents use prompt templates, parser-backed structured output, and LangChain chat model interfaces.

New RAG adapter:

- `backend/knowledge/langchain_retriever.py`
- Class: `SEAMKnowledgeRetriever`
- Returns LangChain `Document` objects with source, domain, status, URL, and score metadata.

## LangGraph

The workflow remains a LangGraph `StateGraph(ProjectState)`.

```text
Supervisor
  -> AnalysisAgent
  -> Supervisor
  -> PlanningAgent
  -> Supervisor
  -> CodingAgent
  -> Supervisor
  -> QAAgent
  -> Supervisor
  -> DeliveryAgent
  -> Supervisor
  -> END
```

Supervisor decisions remain in `SupervisorAgent`; LangGraph handles execution and routing.

## Qwen3-Coder-Next

The default model is now `qwen3-coder-next`. The backend reports:

- configured provider
- configured primary model
- Ollama model list availability
- primary model availability
- Qwen3-Coder-Next availability

No alternate model is silently selected by this implementation.

## Tests Added

- `tests/test_langchain_integration.py`
- `tests/test_langchain_rag.py`
- `tests/test_langgraph_workflow.py`
- `tests/test_qwen_model.py`
- `tests/test_langgraph_rework.py`

## Validation Limitation In This Shell

This execution environment could not locate `python`, `py`, or the previously referenced virtualenv path `C:\Users\KARTHIK\Downloads\SEAM1.venv\Scripts\python.exe`. Because of that, the tests could not be executed from this shell in this pass.

The exact attempted command was:

```powershell
python -m pytest tests\test_langchain_integration.py tests\test_langchain_rag.py tests\test_langgraph_workflow.py tests\test_qwen_model.py tests\test_langgraph_rework.py -q
```

It failed because `python` was not recognized.

The second attempted command was:

```powershell
..\.venv\Scripts\python.exe -m pytest ...
```

It failed because that virtualenv path does not exist from this workspace.

## Obsolete Runtime Dependencies

Runtime references to Unity, Antigravity, StarUML, Flask, or old Flask app wiring were not found in `backend` or `requirements.txt`.

One PlantUML mention exists only as a negative instruction in `backend/tools/diagram_generator.py`: SEAM should not use PlantUML and should emit React Flow JSON.
