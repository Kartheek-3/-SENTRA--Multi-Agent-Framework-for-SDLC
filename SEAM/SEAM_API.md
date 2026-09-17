# SEAM API

Base URL: `http://127.0.0.1:8000`

## System

- `GET /` - backend health alias
- `GET /health` - backend health
- `GET /docs` - FastAPI OpenAPI UI
- `GET /api/system/models` - Ollama/model routing status
- `GET /api/system/health` - IDE health summary for Backend, Qwen/Ollama, RAG, and GitHub token configuration

## Projects

- `POST /api/projects` - create a project
- `GET /api/projects/{project_id}/status` - return authoritative ProjectState summary, including analysis, scale, plan, tasks, agent status, QA, delivery, GitHub, and execution history
- `POST /api/projects/{project_id}/run` - start the backend workflow
- `POST /api/projects/{project_id}/stop` - stop when safe; returns `NOT_AVAILABLE` for active in-process workflow cancellation

## Artifacts

- `GET /api/projects/{project_id}/artifacts` - list generated project files
- `GET /api/projects/{project_id}/files?path={relative_path}` - safely read a generated file

## Diagrams

- `GET /api/projects/{project_id}/diagrams` - list persisted diagram JSON files
- `GET /api/projects/{project_id}/diagrams/{diagram_type}` - read diagram JSON
- `POST /api/projects/{project_id}/diagrams/{diagram_type}/regenerate` - regenerate diagram from ProjectState

Supported UI labels:

- Architecture
- Use Case
- Class
- Object
- Sequence
- Activity
- DFD Level 0
- DFD Level 1

## GitHub Intelligence

- `GET /api/projects/{project_id}/repositories` - return repository selection/evaluation status if available

GitHub search and selection are currently executed as backend workflow capability through `GitHubRepositoryService`, not as separate extension-side orchestration endpoints.

## Knowledge / RAG

- `POST /api/knowledge/search` - search only VALIDATED knowledge
- `POST /api/knowledge/ingest` - ingest a PENDING knowledge document
- `GET /api/knowledge/categories` - list categories

## WebSocket

- `WS /api/projects/{project_id}/events` - stream event bus messages for one project

WebSocket messages are event transport only. The VS Code extension refreshes `GET /api/projects/{project_id}/status` after events because ProjectState remains authoritative.
