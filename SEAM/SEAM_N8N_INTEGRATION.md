# SEAM n8n Integration

Date: 2026-09-22

## Architecture

n8n is integrated as optional external automation. SEAM still uses LangGraph for agent orchestration, the existing ToolRegistry for controlled capability access, and the PermissionEngine for tool execution policy. Agents do not call n8n directly.

SEAM emits allowlisted operational events through `N8NIntegrationService` and `N8NClient`. n8n callbacks return through `/api/integrations/n8n/webhook` and are validated as external data.

## Setup

Local n8n assets live under `n8n/`.

1. Copy `n8n/.env.example` to `n8n/.env`.
2. Set `N8N_ENCRYPTION_KEY` and `SEAM_N8N_INTEGRATION_SECRET`.
3. Start local n8n from `n8n/`:

```powershell
docker compose --env-file .env up -d
```

Default URL: `http://localhost:5678`

## Environment

- `N8N_BASE_URL`: n8n UI/base URL, default `http://localhost:5678`.
- `N8N_WEBHOOK_URL`: optional default webhook URL.
- `N8N_ALLOWED_WORKFLOWS`: comma-separated `name=url` allowlist.
- `N8N_ALLOWED_EVENT_TYPES`: optional SEAM event allowlist override.
- `SEAM_API_URL`: SEAM backend URL, default `http://127.0.0.1:8000`.
- `SEAM_N8N_INTEGRATION_SECRET`: shared secret for n8n callbacks and SEAM outbound webhook authentication.

Secrets are never stored in ProjectState, EventStore payloads, status responses, or workflow JSON files.

## SEAM API

- `GET /api/integrations/n8n/status`
- `POST /api/integrations/n8n/events`
- `POST /api/integrations/n8n/test`
- `POST /api/integrations/n8n/trigger` keeps the earlier workflow trigger contract.
- `POST /api/integrations/n8n/webhook` accepts authenticated callbacks.

## Workflows

Importable workflow templates:

- `SEAM_EVENT_ROUTER`
- `N8N_TO_SEAM`
- `GITHUB_TO_SEAM`
- `SEAM_DELIVERY_NOTIFICATION`
- `SEAM_EXPERIMENT_NOTIFICATION`
- `SEAM_DEFECT_ROUTER`

Optional Slack, Teams, Email, Jira, and GitHub actions remain `NOT_CONFIGURED` until credentials are explicitly configured in n8n.

## Security

Callbacks require `X-SEAM-Integration-Secret` or the backward-compatible `X-N8N-API-Key`. Payloads are schema validated, event types are allowlisted, repeated callback correlation IDs are rate-limited, and secret-like payload fields are redacted.

n8n is not exposed as an unrestricted agent tool. Controlled tools only:

- `n8n_status`
- `n8n_emit_event`
- `n8n_test_connection`

No arbitrary shell execution, forced Git operations, destructive filesystem access, or deployment bypass is added.

## Failure Handling

n8n is optional. If n8n is unavailable, SEAM records the failure and continues the core Analysis, Planning, Coding, QA, Delivery, and evaluation workflows.

## Testing

Focused validation:

```powershell
python -m pytest tests/test_n8n_integration.py -q
```

Full validation should additionally verify Docker container startup, workflow import, SEAM to n8n emission, n8n to SEAM callback, invalid authentication rejection, and unavailable n8n behavior.
