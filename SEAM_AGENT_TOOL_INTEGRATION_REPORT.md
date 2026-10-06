# SEAM Agent Tool Integration Report

Date: 2026-09-20

## Previous Architecture

SEAM agents used LangChain/LangGraph and existing services directly. The ToolRegistry, PermissionEngine, and ToolExecutor existed, but agents did not call them during workflow execution.

## Identified Gap

Focused tool tests proved the tools worked in isolation, but a real workflow could not prove agent tool usage because the agents bypassed ToolExecutor.

## Integration Architecture

Added:

- `backend/tools/agent_tools.py`

Flow:

```text
Agent
  -> agent tool bridge
  -> ToolExecutor
  -> ToolRegistry
  -> PermissionEngine
  -> registered tool
  -> ToolResult
  -> ProjectState execution_history + EventStore tool events
```

## Agent/Tool Matrix

- Analysis: `rag_search`
- Planning: `rag_search`, `mermaid_generate`
- Coding: `rag_search`, `file_search`, `file_write`, `git_status`, `git_diff`, `git_add`, `git_commit`
- QA: `rag_search`, `pytest_runner`
- Delivery: `docker_validate`, `docker_build`
- Supervisor: no arbitrary execution tools

## Permission Path

All bridge calls go through `ToolExecutor.execute()`, which calls `PermissionEngine.check()`.

## LangChain Integration

Existing LLM prompt chains remain intact. This pass integrates deterministic agent operations with ToolExecutor. Full model-directed tool binding remains a later enhancement.

## EventStore Integration

ToolExecutor emits existing tool lifecycle events:

- `TOOL_REQUESTED`
- `TOOL_PERMISSION_CHECKED`
- `TOOL_STARTED`
- `TOOL_COMPLETED`
- `TOOL_PERMISSION_DENIED`
- `TOOL_FAILED`
- `TOOL_TIMEOUT`

## ProjectState Integration

The bridge appends tool invocation summaries to `ProjectState.execution_history`. Existing artifacts and task state are preserved.

## Tests

Added:

- `tests/test_agent_tool_integration.py`

It verifies delegation through ToolExecutor for:

- Analysis/RAG
- Planning/Mermaid
- Coding/file and Git tools
- QA/Pytest
- Delivery/Docker
- failure recording

## Qwen Diagnostic Result

Direct Ollama generation with `qwen3-coder-next:latest` timed out after about 62.76 seconds for an 8-token request. See `SEAM_QWEN_RUNTIME_DIAGNOSTIC.md`.

## Remaining Blockers

- Direct Qwen generation must complete reliably before another real E2E run.
- Full model-directed LangChain tool binding is not yet implemented; this pass integrates agent deterministic operations through ToolExecutor.

