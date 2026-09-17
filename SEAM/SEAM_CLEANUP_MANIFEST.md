# SEAM Cleanup Manifest

Date: 2026-09-16

## Removed Items

| Path | Reason | Replacement | Reference Check | Status |
|---|---|---|---|---|
| `.venv/` | Project-local virtual environment artifact | `SEAM/requirements.txt` | Not imported by source | REMOVED |
| `antigravity-unity/` | Obsolete Unity/Antigravity integration | `seam-vscode/` | No active backend/extension import | REMOVED |
| `seam-ide-extension/` | Old Antigravity-oriented extension | `seam-vscode/` | No active backend/extension import | REMOVED |
| `Assets/` | Unity project artifact | `SEAM/` + `seam-vscode/` | No active backend/extension import | REMOVED |
| `Library/` | Unity generated cache | Not applicable | Generated cache | REMOVED |
| `Logs/` | Unity generated logs | Not applicable | Generated logs | REMOVED |
| `Packages/` | Unity package metadata | `seam-vscode/package.json` for active extension | No active backend/extension import | REMOVED |
| `ProjectSettings/` | Unity project settings | Not applicable | No active backend/extension import | REMOVED |
| `UserSettings/` | Unity/editor local settings | Not applicable | Local settings | REMOVED |
| `SEAM1.sln` | Unity/Visual Studio generated solution | Not applicable | No active backend/extension import | REMOVED |
| `Unity.Antigravity.Editor.csproj` | Unity/Antigravity C# project | Not applicable | No active backend/extension import | REMOVED |
| `debug.log` | Temporary root debug log | Not applicable | Log artifact | REMOVED |
| `repo_list_utf8.txt` | Obsolete inventory artifact containing removed paths | `SEAM_REPOSITORY_CLEANUP_AUDIT.md` | Stale report/cache | REMOVED |
| `SEAM/repo_list.txt` | Obsolete inventory artifact | `SEAM_REPOSITORY_CLEANUP_AUDIT.md` | Stale report/cache | REMOVED |
| `SEAM/repo_tree.txt` | Obsolete inventory artifact | `SEAM_REPOSITORY_CLEANUP_AUDIT.md` | Stale report/cache | REMOVED |
| `SEAM/.pytest_cache/` | Pytest cache | Recreated by pytest | Generated cache | REMOVED |
| `SEAM/**/__pycache__/` | Python bytecode cache | Recreated by Python | Generated cache | REMOVED |
| `SEAM/**/*.pyc` | Python bytecode cache | Recreated by Python | Generated cache | REMOVED |
| `SEAM/.env` | Local environment file should not be kept in a clean repository | `SEAM/.env.example` | Placeholder token only; no runtime import | REMOVED |
| `SEAM/generated_projects/**/*.puml` | Legacy generated PlantUML artifacts | Structured diagram JSON + React Flow rendering | Active generator does not depend on `.puml` | REMOVED |
| `seam-vscode/node_modules/` | Generated Node dependencies | `npm install` from lockfile | Recreated by npm | REMOVED |
| `seam-vscode/out/` | Generated extension build output | `npm run compile` + `npm run build:webview` | Recreated by build | REMOVED |

## Preserved Items

- `SEAM/backend/` - active FastAPI backend and orchestration.
- `SEAM/backend/agents/` - exactly six executable agents plus `__init__.py`.
- `SEAM/backend/models/`, `graph/`, `knowledge/`, `github/`, `rag/`, `tools/` - active backend subsystems.
- `SEAM/tests/` - active tests.
- `SEAM/generated_projects/` - generated project artifacts; only obsolete `.puml` files were removed.
- `SEAM/knowledge/` and `SEAM/chroma_db/` - knowledge/RAG data.
- `seam-vscode/src/`, `package.json`, `package-lock.json`, `tsconfig.json`, `README.md`, `seam-1.0.0.vsix` - active VS Code extension source and final package.
- `SEAM/.env.example` - sanitized environment template.

## Dependency Cleanup

- No Python dependency removed. `requirements.txt` does not include Flask, PlantUML, StarUML, or Unity-specific packages.
- No VS Code extension dependency removed. React and React Flow remain required by the VS Code webview.

## Reference Cleanup

- `SEAM/README.md` updated to remove old Unity/Antigravity runtime instructions.
- Post-cleanup searches found no remaining path matches for Antigravity, Unity, old Antigravity extension, Python caches, `.puml`, logs, or `node_modules`.

## REVIEW_REQUIRED

- `SEAM/chroma_db/` - RAG runtime data. Preserved because it may contain useful validated local knowledge.
- `SEAM/generated_projects/` project directories - preserved as valid generated artifacts unless individual temporary files are clearly obsolete.
- Local developer `.env` files - should be recreated from `.env.example` and kept out of source control.
