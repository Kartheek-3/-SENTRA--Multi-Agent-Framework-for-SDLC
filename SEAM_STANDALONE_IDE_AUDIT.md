# SEAM Standalone IDE Audit

## 1. Existing Backend

The working backend lives in `SEAM/backend`. It is a FastAPI application with routers for projects, workflow, generated artifacts, knowledge/RAG, diagrams, and WebSocket events. `ProjectState` remains the authoritative workflow state.

## 2. Existing VS Code Integration

The old UI lives in `seam-vscode`. It contains a VS Code extension host entrypoint, VS Code webview wrappers, a React webview bundle, API clients, WebSocket client logic, and a packaged `.vsix`.

## 3. Reusable Components

- REST API client behavior from `seam-vscode/src/api/seamClient.ts`
- WebSocket endpoint knowledge from `seam-vscode/src/api/websocketClient.ts`
- Dashboard, diagrams, agent, QA, delivery, knowledge, and generated-file UI concepts
- Backend FastAPI routers and ProjectState-based workflow
- Diagram JSON APIs and generated artifact layout

## 4. Components To Remove

- `seam-vscode/`
- VS Code extension entrypoint
- VS Code manifest and command registrations
- VS Code webview API wrapper
- `.vsix` package artifacts
- Documentation that says VS Code is the primary IDE

## 5. Components To Adapt

- UI becomes a standalone React/Vite app under `seam-ide`.
- File opening/saving moves from VS Code APIs to secure backend filesystem APIs.
- Generated code display becomes a real IDE explorer plus CodeMirror editor.
- WebSocket status remains backend-driven.

## 6. New Standalone IDE Architecture

`seam-ide` provides a lightweight React + TypeScript + Vite interface with CodeMirror 6. Tauri configuration is scaffolded for desktop packaging. The frontend talks to FastAPI through REST and WebSocket. FastAPI remains the only backend authority for workflow, agents, tasks, QA, delivery, RAG, and generated files.

## 7. Files / Directories To Remove

Confirmed obsolete after migration:

- `seam-vscode/`

Review before deletion:

- Historical VS Code documentation files under `SEAM/`
- Generated project samples under `SEAM/generated_projects/`

## 8. Risks

- Tauri desktop build depends on Rust/Tauri tooling on the machine.
- Full multi-agent E2E validation can be long-running because it depends on local Ollama performance.
- In-memory `projects_db` means project workflow state is not persisted across backend restarts.
- Existing generated projects may have inconsistent slug names from older runs.

## 9. Migration Plan

1. Keep backend logic intact.
2. Add secure backend file-tree and file-edit APIs.
3. Create `seam-ide` React/Vite/Tauri app.
4. Implement project explorer, CodeMirror editor, file tabs, SEAM right panel, logs, diagrams, RAG, GitHub optional status, and workflow controls.
5. Build and validate the standalone frontend.
6. Remove confirmed obsolete VS Code extension files.
7. Update documentation and final report.
