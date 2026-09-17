# SEAM Standalone IDE Guide

## Architecture

SEAM IDE is a React + TypeScript + Vite frontend with a Tauri desktop scaffold. It communicates with the FastAPI backend through REST and WebSocket. The backend owns ProjectState, Supervisor orchestration, six agents, Qwen/Ollama routing, RAG/ChromaDB, GitHub intelligence, QA, delivery, diagrams, and secure file operations.

## Installation

Backend:

```bash
cd SEAM
pip install -r requirements.txt
```

Frontend:

```bash
cd seam-ide
npm install
```

## Development Mode

Start backend:

```bash
cd SEAM
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Start IDE:

```bash
cd seam-ide
npm run dev
```

Open `http://127.0.0.1:5173`.

## Backend Startup

The IDE defaults to `http://127.0.0.1:8000`. If the backend is unavailable, local UI remains visible and the status panel reports backend offline.

## IDE Startup

Use the Vite development server for local development. Use Tauri scripts for desktop packaging when Rust/Tauri prerequisites are installed.

## Creating A Project

Open the SEAM right panel, select Project, enter project name and requirements, choose scale, optionally add technology preferences and GitHub repository, then create the project.

## Opening Files

Select a project, use the left Explorer, and click a file. The IDE reads actual file contents through `GET /api/projects/{project_id}/filesystem/file`.

## Editing Files

The center editor uses CodeMirror 6. Edits remain dirty until saved.

## Running SEAM

Use Run Workflow in the top bar or Dashboard. This calls `POST /api/projects/{project_id}/run`.

## Agent Monitoring

The Agents section shows Analysis, Planning, Supervisor, Coding, QA, and Delivery statuses from backend ProjectState.

## Supervisor

The Supervisor section shows current task, pending tasks, completed tasks, failed tasks, and retry count.

## Diagrams

The Diagrams section reads backend diagram metadata and structured diagram JSON. The active pipeline is JSON/Pydantic-based.

## QA

The QA section displays deterministic and semantic QA results when available. Missing tests are shown as `NOT_AVAILABLE`.

## Delivery

Delivery displays package/manifest/QA readiness. Delivery remains blocked if QA prerequisites fail.

## RAG

Knowledge / RAG supports backend knowledge search. Trusted retrieval is backend-controlled.

## GitHub

GitHub is optional. If no token is configured, the IDE reports `token_missing` and the core workflow remains available.

## Troubleshooting

- Backend offline: start FastAPI on port 8000.
- Qwen unavailable: start Ollama and pull the configured Qwen model.
- RAG unavailable: check ChromaDB/FastEmbed dependencies.
- WebSocket disconnected: refresh the project or restart backend.
- File not found: refresh Explorer and verify the selected project.

## Security

Filesystem APIs normalize paths and restrict all operations to `generated_projects/<project>`. Path traversal returns HTTP 403. The frontend does not expose arbitrary shell execution.

## Performance

Files are loaded on demand. The Explorer requests a bounded tree depth and avoids loading all source files into memory. WebSocket events update state incrementally.

## Packaging

Frontend:

```bash
npm run build
```

Desktop:

```bash
npm run tauri:build
```

If Tauri prerequisites are unavailable, use the Vite development build until Rust/Tauri are installed.
