# SEAM n8n Integration Report

Date: 2026-09-22

## Status

Status: PASS

Reason: The real `SEAM -> n8n -> workflow execution -> SEAM callback -> EventStore` round trip completed successfully with preserved correlation ID.

## Installation Method

- Local Docker Compose service: `n8n/docker-compose.yml`
- Persistent volume: `n8n_data`
- Default URL: `http://localhost:5678`
- Callback base URL: `SEAM_CALLBACK_BASE_URL=http://host.docker.internal:8000`
- Workflow templates: `n8n/workflows/*.json`

## SEAM Endpoints

- `GET /api/integrations/n8n/status`
- `POST /api/integrations/n8n/events`
- `POST /api/integrations/n8n/test`
- `POST /api/integrations/n8n/trigger`
- `POST /api/integrations/n8n/webhook`

## Workflows

- `SEAM_EVENT_ROUTER`: created
- `N8N_TO_SEAM`: created
- `GITHUB_TO_SEAM`: created
- `SEAM_DELIVERY_NOTIFICATION`: created
- `SEAM_EXPERIMENT_NOTIFICATION`: created
- `SEAM_DEFECT_ROUTER`: created

## Security

- Shared-secret callback authentication is implemented.
- Existing `X-N8N-API-Key` compatibility is preserved.
- SEAM outbound events are allowlisted.
- Secrets are redacted from payloads and results.
- n8n is optional and does not bypass the PermissionEngine.
- Optional external credentials are not committed.

## Tests

- Focused n8n integration: `17 passed`
- Targeted n8n/tool regression: `29 passed`
- Backend compile: PASS
- Full backend regression: `222 passed, 2 warnings`
- IDE build: PASS
- Focused n8n integration after callback fix: `17 passed`

## Live Runtime Validation

- Docker image pull: PASS (`n8nio/n8n:latest`)
- n8n container startup: PASS (`seam-n8n`)
- n8n health: PASS (`GET http://localhost:5678/healthz -> 200 {"status":"ok"}`)
- Workflow import: PASS (`Successfully imported 6 workflows`)
- Workflow availability: PASS (`SEAM_EVENT_ROUTER`, `N8N_TO_SEAM`, `GITHUB_TO_SEAM`, `SEAM_DELIVERY_NOTIFICATION`, `SEAM_EXPERIMENT_NOTIFICATION`, `SEAM_DEFECT_ROUTER`)
- SEAM to n8n delivery: PASS (`status=completed`, `correlation_id=seam-n8n-live-fixed-001`)
- n8n workflow execution: PASS
- n8n to SEAM callback: PASS
- correlation_id preservation: PASS (`seam-n8n-live-fixed-001`)
- EventStore `N8N_EVENT_SENT`: PASS
- EventStore `N8N_EVENT_DELIVERED`: PASS
- EventStore `N8N_CALLBACK_RECEIVED`: PASS
- Invalid authentication rejection: PASS (`401 Invalid n8n webhook authentication`; EventStore recorded `N8N_WEBHOOK_REJECTED` and `N8N_CALLBACK_REJECTED`)
- Stop n8n and unavailable behavior: PASS (`reachable=false`; event emission failed gracefully with `n8n unavailable: ConnectionError`)

## Root Cause And Fix

Root cause:

- The local n8n validation volume contained duplicate `SEAM_EVENT_ROUTER` imports and stale publication state.
- n8n blocked `$env.*` usage inside node expressions, causing `access to env vars denied`.
- The callback response node used invalid dynamic JSON.

Fix:

- Reset only the local n8n Docker validation volume and imported a clean workflow set.
- Added configurable `SEAM_CALLBACK_BASE_URL`.
- Set `N8N_BLOCK_ENV_ACCESS_IN_NODE=false` for the local n8n service.
- Updated `SEAM_EVENT_ROUTER` to send a structured authenticated callback to SEAM.
- Replaced the dynamic response body with valid static JSON.

## EventStore Evidence

Successful round trip correlation ID: `seam-n8n-live-fixed-001`

- `N8N_EVENT_SENT`, sequence `560`
- `N8N_WEBHOOK_RECEIVED`, sequence `561`
- `N8N_CALLBACK_RECEIVED`, sequence `562`
- `N8N_EVENT_DELIVERED`, sequence `563`

## Limitations

- Optional Slack, Jira, Email, Teams, and GitHub automations are `NOT_CONFIGURED`.
