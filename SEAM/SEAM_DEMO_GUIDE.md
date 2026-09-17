# SEAM Demo Guide

## Prerequisites

1. Ensure Ollama is running with the configured Qwen model.
2. Ensure Python 3.12+ is installed with dependencies from `requirements.txt`.
3. Install the SEAM VS Code extension from `../seam-vscode/seam-1.0.0.vsix`.

## Start Backend

From `SEAM/`:

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

## Run A VS Code Demo

1. Open VS Code.
2. Open the SEAM Activity Bar.
3. Run **SEAM: Check Backend Connection**.
4. Open **New Project**.
5. Enter a realistic requirement, for example:

```text
Build a task management system.
Users can register and log in.
Users can create, update, delete, assign, and track tasks.
Administrators can manage users and tasks.
Provide REST APIs using FastAPI, React, PostgreSQL, authentication, authorization, validation, secure password storage, logging, and automated testing.
Start simple while preserving a credible path to future scale.
```

6. Select `AUTO` scale.
7. Click **Create & Analyze**.
8. Run the workflow from the dashboard.
9. Inspect Analysis, Scale Assessment, Planning & Design, Supervisor, Agents, Generated Code, QA, Delivery, GitHub Intelligence, Knowledge/RAG, and Logs.
10. Open generated files directly in the VS Code editor.
11. Open diagrams in the Diagram view. Diagrams are structured JSON rendered visually through React Flow.

## Expected Architecture

```text
VS Code
  -> SEAM VS Code Extension
  -> REST / WebSocket
  -> FastAPI
  -> Supervisor
  -> Analysis, Planning & Design, Coding, QA, Delivery
  -> Qwen + ChromaDB/RAG + GitHub Intelligence
```
