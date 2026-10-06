# SEAM n8n Integration

n8n is an optional external automation layer for SEAM. It does not replace LangGraph, agents, the ToolRegistry, or the PermissionEngine.

## Local Setup

1. Copy `.env.example` to `.env`.
2. Replace `N8N_ENCRYPTION_KEY` and `SEAM_N8N_INTEGRATION_SECRET` with local secret values.
3. Start n8n:

```powershell
docker compose --env-file .env up -d
```

Default URL: `http://localhost:5678`

## Workflows

Import the JSON files from `workflows/` into n8n:

- `SEAM_EVENT_ROUTER.json`
- `N8N_TO_SEAM.json`
- `GITHUB_TO_SEAM.json`
- `SEAM_TO_GITHUB.json`
- `SEAM_TO_JIRA.json`
- `FIGMA_TO_SEAM.json`
- `SEAM_TO_FIGMA.json`
- `SEAM_DELIVERY_TO_CICD.json`
- `SEAM_DELIVERY_NOTIFICATION.json`
- `SEAM_EXPERIMENT_NOTIFICATION.json`
- `SEAM_DEFECT_ROUTER.json`

Optional Slack, Email, Teams, Jira, GitHub, Figma, and CI/CD credentials remain `NOT_CONFIGURED` until explicitly added in n8n.

External workflows must preserve `correlation_id`, `project_id`, and `event_id`. They orchestrate business automation only; SEAM internal tools remain responsible for files, Git, Docker execution, Mermaid generation, RAG, and tests.

## Security

Callbacks into SEAM must include `X-SEAM-Integration-Secret`. Payloads are schema-validated and treated as data, not system instructions. Secrets are redacted before persistence or events.
