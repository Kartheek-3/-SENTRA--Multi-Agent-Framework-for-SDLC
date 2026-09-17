# SEAM Repository Cleanup Audit

Date: 2026-09-16

## Repository State

No `.git` repository was found at `C:\Users\KARTHIK\Downloads\SEAM1` or `C:\Users\KARTHIK\Downloads\SEAM1\SEAM`; `git status` fails in both locations. Cleanup therefore uses this audit and `SEAM_CLEANUP_MANIFEST.md` as the safety record.

## Active SEAM Source

Active backend source is under `SEAM/backend/`:

- FastAPI entrypoint: `SEAM/backend/main.py`
- API routers: `SEAM/backend/api/`
- Workflow graph: `SEAM/backend/graph/workflow.py`
- Six executable agents: `SEAM/backend/agents/analysis_agent.py`, `planning_agent.py`, `supervisor_agent.py`, `coding_agent.py`, `qa_agent.py`, `delivery_agent.py`
- Models: `SEAM/backend/models/`
- Knowledge/RAG: `SEAM/backend/knowledge/`, `SEAM/backend/rag/`
- GitHub Intelligence: `SEAM/backend/github/`
- Diagram/document tools: `SEAM/backend/tools/`
- Tests: `SEAM/tests/`

## Active VS Code Extension

The active extension is the root-level `seam-vscode/` folder:

- `seam-vscode/src/`
- `seam-vscode/package.json`
- `seam-vscode/package-lock.json`
- `seam-vscode/tsconfig.json`
- `seam-vscode/README.md`
- `seam-vscode/seam-1.0.0.vsix`

Generated extension artifacts currently present:

- `seam-vscode/node_modules/`
- `seam-vscode/out/`

These can be recreated from `package-lock.json` and source. The final VSIX should be preserved unless packaging succeeds after cleanup.

## Generated Projects

`SEAM/generated_projects/` contains several project outputs and should not be wholesale deleted. It also contains legacy `.puml` diagram files under generated project design folders. These are generated artifacts from the obsolete PlantUML era, not active pipeline source.

## Knowledge / ChromaDB

`SEAM/knowledge/` and `SEAM/chroma_db/` exist. `SEAM/chroma_db/` is runtime data and should not be packaged as source, but it is not deleted automatically because the request protects knowledge/RAG state unless clearly temporary.

## Obsolete Antigravity / Unity Candidates

Clearly obsolete with respect to the final VS Code architecture:

- `antigravity-unity/`
- `seam-ide-extension/`
- root Unity project folders/files: `Assets/`, `Packages/`, `ProjectSettings/`, `UserSettings/`, `Logs/`, `Library/`, `SEAM1.sln`, `Unity.Antigravity.Editor.csproj`

Reference result:

- Active `SEAM/backend/` and `seam-vscode/src/` do not import Unity/Antigravity files.
- `SEAM/README.md` still documents old Unity/Antigravity integration and should be updated.
- `repo_list_utf8.txt`, `SEAM/repo_list.txt`, and `SEAM/repo_tree.txt` are old inventory artifacts referencing Antigravity and should be treated as obsolete reports/caches.

## PlantUML / StarUML Candidates

No active StarUML source was identified. `.puml` files exist under `SEAM/generated_projects/**/design/**`. The active diagram generator explicitly instructs the LLM not to use PlantUML and returns structured JSON for React Flow, so `.puml` generated artifacts are obsolete.

Keep:

- `SEAM/backend/models/diagram.py`
- `SEAM/backend/tools/diagram_generator.py`
- diagram API routes
- `seam-vscode/src/webview/DiagramsView.tsx`
- diagram tests

## Old Web Frontend / Flask Candidates

No standalone root `frontend/`, `web/`, or old Flask app was found outside generated projects. Generated project frontends/backends are project artifacts and are not removed automatically.

## Duplicate Agent Candidates

Only six agent files exist under `SEAM/backend/agents/`, plus `__init__.py`. No duplicate active agents were identified.

## Temporary / Cache Candidates

Safe cleanup candidates:

- `SEAM/**/__pycache__/`
- `SEAM/**/*.pyc`
- `SEAM/.pytest_cache/`
- root `.venv/`
- root `debug.log`
- root `Logs/`
- `seam-vscode/node_modules/`
- `seam-vscode/out/`

## Dependency Cleanup Candidates

`SEAM/requirements.txt` does not list Flask, PlantUML, StarUML, or Unity dependencies. `seam-vscode/package.json` dependencies are for the VS Code extension and React Flow webview. No dependency should be removed solely from this audit.

## Recommended Cleanup Actions

1. Remove obsolete Unity/Antigravity folders/files from the root.
2. Remove old `seam-ide-extension/`.
3. Remove generated caches: Python caches, pytest cache, root venv, VS Code `node_modules/`, VS Code `out/`, logs.
4. Remove generated `.puml` artifacts under `SEAM/generated_projects/`.
5. Update README to remove Unity as a maintained integration.
6. Reinstall extension dependencies, rebuild `out/`, and repackage `seam-1.0.0.vsix`.
7. Document all removals in `SEAM_CLEANUP_MANIFEST.md`.

## Review Required

The following are not deleted automatically:

- `SEAM/chroma_db/`: runtime RAG data; may be valuable local knowledge.
- `SEAM/generated_projects/` project directories: valid generated outputs, not necessarily obsolete.
- Historical official reports under `SEAM/`: preserved unless they actively claim Unity/PlantUML as final runtime.
