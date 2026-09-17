# SEAM

Self-Evolving Autonomous Multi-Agent Framework for end-to-end software engineering.

## Current Product Direction

SEAM is now a standalone lightweight IDE plus FastAPI backend.

- `backend/`: FastAPI, Supervisor, six executable agents, RAG, GitHub intelligence, diagram generation, QA, and delivery.
- `../seam-ide/`: React + TypeScript + Vite standalone IDE with CodeMirror 6 and a Tauri desktop scaffold.
- `generated_projects/`: generated project files edited by the standalone IDE through secure backend filesystem APIs.

## Agents

Exactly six executable agents remain:

1. Analysis Agent
2. Planning and Design Agent
3. Supervisor / Orchestrator Agent
4. Coding Agent
5. QA Agent
6. Delivery Agent

The frontend is not an agent. `ProjectState` remains authoritative in the backend.

## Backend Setup

```bash
pip install -r requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Default backend URL:

```text
http://127.0.0.1:8000
```

## Standalone IDE Setup

From the repository root:

```bash
cd seam-ide
npm install
npm run dev
```

The development IDE runs at:

```text
http://127.0.0.1:5173
```

Production frontend build:

```bash
npm run build
```

Tauri desktop build, when Rust/Tauri prerequisites are available:

```bash
npm run tauri:build
```

## Safety

- File operations are routed through FastAPI filesystem endpoints.
- File access is restricted to the selected generated project root.
- Path traversal and arbitrary absolute paths are blocked.
- GitHub is optional.
- No frontend secrets are required.
- The diagram pipeline uses structured JSON, not PlantUML or StarUML.
