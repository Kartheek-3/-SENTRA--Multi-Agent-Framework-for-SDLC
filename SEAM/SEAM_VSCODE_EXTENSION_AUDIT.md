# SEAM VS Code Extension Audit

## Current Backend Architecture
- **Framework**: Python FastAPI (`backend/main.py`)
- **State Management**: Authoritative `ProjectState` model (`backend/models/state.py`)
- **Agents**: Exactly six agents (Analysis, Planning, Coding, QA, Delivery) orchestrated by the Supervisor (`backend/graph/workflow.py`).
- **Scale Awareness**: Recently implemented. The `ProjectScale` dictates architecture and parallelization logic.
- **LLM/RAG**: `ModelRouter` manages Qwen/Ollama inference. `ChromaRepository` handles RAG with `fastembed`.

## API & WebSocket Capabilities
- **REST APIs**: `backend/api/projects.py` and `backend/api/workflow.py` provide standard endpoints.
- **WebSocket**: Currently handled by `backend/api/ws.py` emitting events via the `EventBus` (`backend/events.py`).

## Existing Artifact Structure
- Projects are generated in `./generated_projects/{project_slug}/`.
- Contains `backend/`, `frontend/`, `tests/`, `design/`, `qa/`, and `delivery/` subdirectories.

## Current Diagram System
- Handled by `backend/tools/diagram_generator.py`.
- Produces structured `DiagramJSON` using Pydantic models.
- Persisted as JSON files under generated project design folders.
- Rendered visually in the VS Code webview with React Flow.

## Required VS Code Extension Components
- **Extension Host**: `src/extension.ts` (Typescript).
- **UI Paradigm**: Sidebar TreeView + Webview panels for complex dashboards.
- **API Client**: A robust wrapper around fetch/axios and a WebSocket client with automatic reconnection.
- **Webviews needed**: Requirements Editor, Agent Monitor, Supervisor View, Live Workflow, Interactive Architecture (React Flow), LLM Diagrams, QA Workspace, Delivery Workspace.
