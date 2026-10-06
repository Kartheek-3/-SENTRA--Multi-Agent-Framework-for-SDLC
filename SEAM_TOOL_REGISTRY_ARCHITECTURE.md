# SEAM Tool Registry Architecture

Date: 2026-09-19

## Purpose

SEAM agents now have a controlled way to call specialized engineering tools without becoming new agents and without bypassing existing workflow boundaries.

## Flow

```text
Agent
  -> LangChain-compatible SEAM tool
  -> ToolRegistry
  -> PermissionEngine
  -> ToolExecutor
  -> Existing SEAM/local capability
  -> ToolResult
  -> EventStore/WebSocket
```

## Core Files

- `backend/tools/base.py`
- `backend/tools/registry.py`
- `backend/tools/permissions.py`
- `backend/tools/schemas.py`
- `backend/tools/executor.py`
- `backend/tools/errors.py`
- `backend/tools/builtin.py`

## Design Rules

- Tools are capabilities, not agents.
- Existing RAG, GitHub Intelligence, artifacts, and project state remain the source of truth.
- Tool execution is explicit, typed, permission checked, timeout bounded, and evented.
- High-risk operations require approval.
- Tool outputs redact secrets before returning structured results.

