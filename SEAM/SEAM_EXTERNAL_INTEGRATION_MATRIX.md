# SEAM External Integration Matrix

| Integration | Direction | n8n | SEAM Boundary |
|---|---|---:|---|
| GitHub webhook | External -> SEAM | YES | n8n webhook -> SEAM API -> GitHub Intelligence / Analysis |
| Jira issue | External -> SEAM | YES | n8n webhook -> SEAM API -> Analysis |
| External issue | External -> SEAM | YES | n8n webhook -> SEAM API -> project/workflow boundary |
| QA notification | SEAM -> External | YES | QA/Supervisor event -> n8n workflow |
| Delivery notification | SEAM -> External | YES | Delivery event -> n8n workflow |
| Slack notification | SEAM -> External | YES | n8n workflow target |
| Email notification | SEAM -> External | YES | n8n workflow target |
| External HTTP API | SEAM -> External | YES | configured n8n workflow only |
| RAG | Internal | NO | ToolRegistry |
| Filesystem | Internal | NO | ToolRegistry |
| Git status/diff/add/commit | Internal | NO | ToolRegistry |
| Mermaid generation | Internal | NO | ToolRegistry |
| Pytest runner | Internal | NO | ToolRegistry |
| API test runner | Internal | NO | ToolRegistry |
| Docker validation/build | Internal | NO | ToolRegistry |
| GitHub Intelligence internals | Internal | NO | SEAM GitHub Intelligence service/tool |
| LangGraph orchestration | Internal | NO | SEAM workflow graph |
| LangChain tool routing | Internal | NO | SEAM agents |

## Rules

- n8n is for external integration and automation only.
- n8n does not execute SEAM tools directly.
- All external events enter through FastAPI request validation.
- All internal actions remain governed by ToolRegistry, PermissionEngine, ToolExecutor, ProjectState, and EventStore.
- Secrets are never stored in ProjectState or emitted to EventStore.
