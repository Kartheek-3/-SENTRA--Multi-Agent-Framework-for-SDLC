# SEAM VS Code Integration Audit

Date: 2026-09-16

## 1. Current Backend Status

The backend is a FastAPI application in `SEAM/backend/main.py`. It includes routers for projects, artifacts, workflow, WebSocket events, and knowledge:

- `backend.api.projects`
- `backend.api.artifacts`
- `backend.api.workflow`
- `backend.api.ws`
- `backend.api.knowledge`

The backend preserves the requested architecture boundary: FastAPI owns the API boundary, `ProjectState` is the workflow state model, and orchestration is implemented by `backend/graph/workflow.py` using a `SupervisorAgent`.

Exactly six executable agents are present in `SEAM/backend/agents/`:

- `AnalysisAgent`
- `PlanningAgent`
- `SupervisorAgent`
- `CodingAgent`
- `QAAgent`
- `DeliveryAgent`

Supporting services exist for GitHub intelligence, Chroma/FastEmbed knowledge storage, diagram generation, delivery packaging, QA validation, and model routing.

## 2. Current Extension Status

The VS Code extension exists in `seam-vscode/` and is packaged as `seam-vscode/seam-1.0.0.vsix`.

Current source files include:

- `src/extension.ts`
- `src/api/seamClient.ts`
- `src/api/websocketClient.ts`
- `src/webview/DashboardView.tsx`
- `src/webview/DiagramsView.tsx`
- `src/webview/index.tsx`

The extension currently provides a dashboard webview, a React Flow diagram view, a tree view, a status bar entry, a typed-enough API client, and a WebSocket client. It is not yet feature-complete against the requested IDE surface.

## 3. Existing API Endpoints

Observed backend endpoints:

- `GET /`
- `GET /health`
- `GET /docs`
- `GET /api/system/models`
- `POST /api/projects`
- `GET /api/projects/{project_id}/status`
- `GET /api/projects/{project_id}/repositories`
- `GET /api/projects/{project_id}/diagrams`
- `GET /api/projects/{project_id}/diagrams/{diagram_type}`
- `POST /api/projects/{project_id}/diagrams/{diagram_type}/regenerate`
- `POST /api/projects/{project_id}/run`
- `GET /api/projects/{project_id}/artifacts`
- `GET /api/projects/{project_id}/files?path=...`
- `POST /api/knowledge/search`
- `POST /api/knowledge/ingest`
- `GET /api/knowledge/categories`

## 4. Existing WebSocket Endpoints

Observed WebSocket endpoint:

- `WS /api/projects/{project_id}/events`

The backend filters event bus messages by `project_id` and sends matching events as JSON.

## 5. Extension-To-Backend Communication Status

Working or partially working:

- Backend health check via `/docs`
- Project creation via `POST /api/projects`
- Workflow start via `POST /api/projects/{project_id}/run`
- Project status fetch via `GET /api/projects/{project_id}/status`
- Diagram fetch/regeneration via existing diagram endpoints

Broken:

- The extension WebSocket client uses `/api/ws/projects/{project_id}/events`, but the backend exposes `/api/projects/{project_id}/events`.

Incomplete:

- The API client lacks methods for artifacts, generated files metadata, GitHub repository status, knowledge search/categories, and model/health details.
- The UI does not expose most requested agent, supervisor, QA, delivery, GitHub, RAG, generated-code, and logs views.

## 6. Missing Integration Pieces

- Command palette registrations for most requested commands.
- Full SEAM Activity Bar tree entries.
- New Project form fields for scale, technology preferences, workspace/project location, GitHub repository, and additional constraints.
- Extension status bar with real Backend/Qwen/RAG/GitHub health summary.
- Artifact/generated file browser.
- Safe file opening backed by backend artifact metadata.
- QA, delivery, GitHub intelligence, knowledge/RAG, supervisor, and logs UI views.
- Stop workflow command. The backend currently has no stop endpoint.
- Real state refresh after WebSocket events in the extension.
- API contract documentation reflecting the final actual routes.

## 7. Broken Integration Pieces

- WebSocket route mismatch blocks live workflow events.
- `seam.openGeneratedFile` assumes the VS Code workspace contains `generated_projects/`; the backend project root is under `SEAM/generated_projects`, so this can fail depending on which folder is opened.
- The dashboard fabricates agent statuses from only `current_agent` and `workflow_status`; it can show `COMPLETED` for agents without per-agent evidence.
- Diagram tabs cover only five diagram labels and omit Class, Object, Activity, and exact DFD Level labels.
- Current frontend does not clearly display unavailable backend data per view.

## 8. Security Risks

- `GET /api/projects/{project_id}/files` uses `startswith(project_dir)` for path containment. This should be hardened with `os.path.commonpath`.
- `GET /api/projects/{project_id}/diagrams/{diagram_type}` constructs a path from a slug but should still enforce containment and safe project directory resolution.
- Extension `openGeneratedFile` performs path checks, but it depends on workspace layout and does not consult backend artifact metadata.
- The extension should keep credentials out of source. No frontend `OPENAI_API_KEY`, `GITHUB_TOKEN`, JWT secret, or database password was observed in the inspected extension source.
- GitHub code execution is not observed in the extension. Existing GitHub capability remains backend-side.

## 9. Testing Gaps

- Backend unit tests exist for agents, API, diagrams, GitHub models/ranking, knowledge, QA, delivery, supervisor, and state.
- No extension integration test or VS Code UI automation was found.
- No verified VSIX install/activation test has been run yet in this pass.
- No real end-to-end workflow has been run yet in this pass.
- Controlled QA failure and scale tests exist as scripts/tests, but have not yet been executed in this pass.
- WebSocket endpoint has not yet been verified from the extension because of the route mismatch.

## 10. Recommended Fixes

1. Fix the extension WebSocket URL to `/api/projects/{project_id}/events`.
2. Expand the extension manifest with the requested commands and views.
3. Keep the extension thin: all commands should call FastAPI endpoints or open backend-backed views.
4. Add API client methods for real existing endpoints instead of inventing routes.
5. Improve backend `/status` to expose structured ProjectState fields needed by the UI without moving orchestration to TypeScript.
6. Harden backend file/path handling using common-path checks.
7. Add UI panes for unavailable data with `NOT_AVAILABLE`/`BLOCKED` states instead of placeholders.
8. Update `SEAM_API.md`, `SEAM_VSCODE_INTEGRATION_GUIDE.md`, `README.md`, and final report after verification.
9. Run backend tests, extension compile/build, VSIX packaging, and as much real workflow validation as the local Ollama/model environment permits.
