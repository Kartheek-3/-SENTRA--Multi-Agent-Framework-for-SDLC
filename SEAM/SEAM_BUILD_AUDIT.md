# SEAM Build Audit

## Current Architecture

SEAM is a VS Code-first autonomous software engineering framework. The extension is the primary UI, FastAPI is the backend/API boundary, and the Supervisor controls orchestration.

## Active Components

1. Analysis Agent: `backend/agents/analysis_agent.py`
2. Planning & Design Agent: `backend/agents/planning_agent.py`
3. Supervisor Agent: `backend/agents/supervisor_agent.py`
4. Coding Agent: `backend/agents/coding_agent.py`
5. QA Agent: `backend/agents/qa_agent.py`
6. Delivery Agent: `backend/agents/delivery_agent.py`
7. Knowledge/RAG: `backend/knowledge/` and `backend/rag/`
8. GitHub Intelligence: `backend/github/`
9. FastAPI/WebSocket API: `backend/api/`
10. VS Code extension: `../seam-vscode/`

## Removed Or Retired

- Unity editor UI/runtime.
- Antigravity-specific IDE integration.
- Legacy generated `.puml` artifacts.

## Duplicated Components

No duplicate active agents detected. RAG, diagrams, and GitHub intelligence remain supporting capabilities, not additional agents.
