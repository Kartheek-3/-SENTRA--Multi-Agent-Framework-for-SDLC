# SEAM n8n Integration Architecture

## Purpose

n8n is integrated as an external automation and integration layer for SEAM. It connects SEAM to systems such as GitHub webhooks, Jira, Slack, email, and other SaaS or HTTP APIs.

n8n does not replace SEAM's agent workflow, LangGraph orchestration, LangChain tool usage, ToolRegistry, PermissionEngine, ToolExecutor, ProjectState, or EventStore.

## Architecture

```text
User
  |
SEAM FastAPI
  |
LangGraph
  |
Analysis -> Planning -> Supervisor -> Coding -> QA -> Delivery
  |
LangChain
  |
ToolRegistry / PermissionEngine / ToolExecutor
  |
SEAM internal tools

External automation boundary:

SEAM <-> n8n <-> GitHub / Jira / Slack / Email / External APIs
```

## What n8n Does

- Receives external automation events and forwards validated events to SEAM.
- Receives SEAM outbound integration notifications.
- Connects SEAM to third-party systems such as Slack, email, Jira, and external HTTP APIs.
- Carries correlation IDs across external workflows.

## What n8n Does Not Do

- It does not orchestrate SEAM agents.
- It does not replace LangGraph.
- It does not replace LangChain.
- It does not execute SEAM internal tools.
- It does not execute shell, filesystem, Git, Python, Docker, RAG, Mermaid, pytest, or GitHub Intelligence directly.
- It does not store or expose credentials through SEAM status responses or events.

## Backend Modules

```text
backend/integrations/n8n/
  client.py
  config.py
  events.py
  schemas.py
  security.py
  service.py

backend/api/n8n.py
```

## API Endpoints

```text
GET  /api/integrations/n8n/status
POST /api/integrations/n8n/trigger
POST /api/integrations/n8n/webhook
```

## Environment Variables

```text
N8N_BASE_URL=http://localhost:5678
N8N_WEBHOOK_URL=http://localhost:5678/webhook/default
N8N_ALLOWED_WORKFLOWS=qa_notification=http://localhost:5678/webhook/qa,delivery_notification=http://localhost:5678/webhook/delivery
N8N_API_KEY=replace-with-secret
N8N_TIMEOUT_SECONDS=8
N8N_MAX_RESPONSE_BYTES=65536
N8N_REQUIRE_HTTPS=false
```

`N8N_API_KEY` is never returned by the status endpoint and is never emitted in EventStore payloads.

## Inbound Webhook Flow

```text
n8n
  |
POST /api/integrations/n8n/webhook
  |
API key authentication
  |
Pydantic event validation
  |
EventStore / WebSocket event
  |
ProjectState.external_integrations record
  |
Existing SEAM workflow/API boundary
```

Supported initial inbound event types:

- `github.push`
- `jira.issue_created`
- `external.issue_created`
- `qa.failed`
- `delivery.completed`

Inbound events are treated as untrusted input. They cannot directly run shell commands, filesystem changes, Git commands, or ToolRegistry tools.

## Outbound Workflow Flow

```text
SEAM
  |
N8NIntegrationService.trigger_workflow
  |
Configured workflow allowlist
  |
HTTP request with timeout
  |
n8n
  |
Slack / Email / Jira / External system
```

Outbound workflow calls require the workflow name to exist in `N8N_ALLOWED_WORKFLOWS` or the default `N8N_WEBHOOK_URL`. Arbitrary URLs are rejected.

## Security Model

- API-key authentication for inbound n8n webhooks.
- Workflow URL allowlist for outbound calls.
- HTTPS enforcement can be enabled through `N8N_REQUIRE_HTTPS=true`.
- Plain HTTP is accepted only for `localhost` and `127.0.0.1` unless HTTPS enforcement is disabled for local development.
- Request timeout via `N8N_TIMEOUT_SECONDS`.
- Response size cap via `N8N_MAX_RESPONSE_BYTES`.
- Secret redaction for keys containing `api_key`, `token`, `secret`, `password`, `authorization`, or `credential`.
- Correlation IDs on inbound and outbound interactions.
- EventStore auditing through existing SEAM event infrastructure.
- Simple correlation-based duplicate/rate rejection for repeated inbound events.

## Event Model

The integration emits existing EventStore/WebSocket events through `event_bus`:

- `N8N_WORKFLOW_REQUESTED`
- `N8N_WORKFLOW_STARTED`
- `N8N_WORKFLOW_COMPLETED`
- `N8N_WORKFLOW_FAILED`
- `N8N_WEBHOOK_RECEIVED`
- `N8N_WEBHOOK_REJECTED`

No separate event store is introduced.

## ProjectState Integration

`ProjectState.external_integrations` stores non-secret records:

```json
{
  "provider": "n8n",
  "direction": "inbound",
  "workflow": "github.push",
  "status": "accepted",
  "timestamp": "2026-09-21T...",
  "correlation_id": "...",
  "result_summary": "N8N: GitHub event received for owner/repo"
}
```

## IDE Integration

The standalone IDE maps n8n events into visible chat activity:

- `N8N: GitHub event received`
- `N8N: Triggering external workflow`
- `N8N: workflow completed`
- `N8N: webhook rejected`

Secrets are not shown.

## Example GitHub Workflow

```text
GitHub push
  |
n8n GitHub trigger
  |
n8n validation/function node
  |
HTTP Request -> POST /api/integrations/n8n/webhook
  |
SEAM records github.push event
  |
SEAM GitHub Intelligence can be invoked through normal SEAM workflow boundaries
```

## Example QA Notification Workflow

```text
QA failed in SEAM
  |
SEAM -> POST configured n8n qa_notification webhook
  |
n8n formats message
  |
Slack or email notification
```

## Example Delivery Notification Workflow

```text
Delivery completed in SEAM
  |
SEAM -> POST configured n8n delivery_notification webhook
  |
n8n formats package summary
  |
Slack / email / external tracking system
```

## Example Jira Workflow

```text
Jira issue created
  |
n8n Jira trigger
  |
n8n validates issue payload
  |
POST /api/integrations/n8n/webhook with event_type=jira.issue_created
  |
SEAM records external request and can start an ordinary LangGraph project workflow
```

## Local Setup

1. Start n8n locally.
2. Configure SEAM environment variables in `.env`.
3. Start SEAM FastAPI.
4. Check `GET /api/integrations/n8n/status`.
5. Configure n8n HTTP Request nodes to call `POST /api/integrations/n8n/webhook` with `X-N8N-API-Key`.

## Runtime Verification

This implementation validates the SEAM integration boundary and tests it with mocked HTTP calls. It does not claim a real n8n runtime execution unless an actual n8n instance and workflow are available.

Status:

```text
N8N_RUNTIME_NOT_VERIFIED
```
