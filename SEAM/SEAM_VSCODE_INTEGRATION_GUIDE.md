# SEAM VS Code Integration Guide

## 1. Architecture

VS Code hosts the SEAM extension. The extension is a thin client that communicates with the FastAPI backend over REST and `WS /api/projects/{project_id}/events`. The backend owns ProjectState, Supervisor orchestration, the six executable agents, LLM/RAG services, GitHub intelligence, QA, delivery, and diagram generation.

## 2. Installation

Install the packaged extension:

```powershell
code --install-extension ..\seam-vscode\seam-1.0.0.vsix --force
```

The install smoke test passed with VS Code `1.137.0`.

## 3. Backend Startup

From `SEAM/`:

```powershell
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

The local Python environment in this workspace is currently broken, so this command was documented but not executed in the final pass.

## 4. Ollama Startup

```powershell
ollama serve
```

Ensure the configured Qwen model is installed.

## 5. VS Code Extension Installation

The extension package is:

```text
seam-vscode/seam-1.0.0.vsix
```

The packaged VSIX contains only `package.json`, `README.md`, and compiled `out/**` assets.

## 6. Backend Configuration

Default extension setting:

```json
"seam.apiUrl": "http://127.0.0.1:8000"
```

## 7. Creating A Project

Open the SEAM Activity Bar, choose New Project, and enter:

- Project name
- Requirements
- Scale: AUTO, SMALL, MEDIUM, LARGE, ENTERPRISE
- Technology preferences
- Optional workspace/project location
- Optional GitHub repository
- Optional constraints

## 8. Running A Workflow

Use `SEAM: Run Project` or the Dashboard Run Workflow button. The extension calls `POST /api/projects/{project_id}/run`.

## 9. Viewing Agents

Use `SEAM: Show Agents`. The view renders backend `agent_status` and execution history from ProjectState.

## 10. Viewing Supervisor

Use `SEAM: Show Supervisor`. The view renders current task, pending/completed/failed tasks, retry count, and execution history from the backend.

## 11. Viewing Diagrams

Use `SEAM: Show Diagrams`. Supported tabs are Architecture, Use Case, Class, Object, Sequence, Activity, DFD Level 0, and DFD Level 1. Missing diagrams show backend errors instead of placeholder diagrams.

## 12. Opening Generated Code

Use `SEAM: Show Generated Files`, then select a listed artifact. Files open with `vscode.workspace.openTextDocument()` and `vscode.window.showTextDocument()` after workspace-contained path checks.

## 13. QA

Use `SEAM: Show QA`. QA results are read from task results. Unavailable tests remain `NOT_AVAILABLE`; they are not converted to PASS.

## 14. Delivery

Use `SEAM: Show Delivery`. Delivery results come from backend `delivery_result`. If QA has not satisfied backend preconditions, delivery remains blocked or unavailable.

## 15. GitHub

Use `SEAM: Search GitHub`. The view displays backend GitHub selection state. If no `GITHUB_TOKEN` is configured, `/api/system/health` reports `token_missing`.

## 16. RAG

Use `SEAM: Search Knowledge`. Searches call `POST /api/knowledge/search`, which uses only VALIDATED knowledge.

## 17. Troubleshooting

- Backend unavailable: start FastAPI at `http://127.0.0.1:8000`.
- Ollama unavailable: start `ollama serve` and install the configured Qwen model.
- WebSocket disconnect: extension reconnects and refreshes ProjectState.
- Diagram missing: run analysis/planning first, then regenerate the diagram.
- Python unavailable: repair the local Python installation or recreate `.venv`.

## 18. Security

- No frontend secrets were found in `seam-vscode/out`, `package.json`, or extension README.
- Generated file opening blocks absolute paths and `..` traversal.
- Backend artifact access uses `os.path.commonpath`.
- The extension does not call individual agents directly.

## 19. Development Mode

```powershell
cd seam-vscode
npm.cmd run compile
npm.cmd run build:webview
```

## 20. VSIX Packaging

```powershell
cd seam-vscode
npm.cmd run package
```

The final package is `seam-vscode/seam-1.0.0.vsix`.
