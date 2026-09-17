# SEAM Agent Manager

## Current State

The UI shows a six-agent workflow timeline and streams agent events through `/api/projects/{project_id}/events`.

The backend now includes a first Agent Manager foundation with JSON persistence and APIs at `/agents`. Current workflow execution is still a single in-process background task started by `/api/projects/{project_id}/run`.

## Target Capabilities

- View all agents and their current status.
- Show active, queued, blocked, failed, and completed tasks.
- Start, pause, cancel, retry, and resume task groups.
- Run background subagents without blocking the UI.
- Attach each task to generated files, plans, QA output, logs, and approvals.
- Preserve task history across backend restarts.

## Backend APIs Needed

- `POST /agents` implemented.
- `GET /agents` implemented.
- `GET /agents/{id}` implemented.
- `POST /agents/{id}/pause` implemented.
- `POST /agents/{id}/resume` implemented.
- `POST /agents/{id}/cancel` implemented.
- `POST /agents/{id}/retry` implemented.

Project-scoped task APIs are implemented separately at `/tasks`.

## UI Plan

The Agent Manager should be a left or bottom workbench view with filters for:

- Agent
- Status
- Task group
- Approval state
- Artifact type

No UI control should be enabled until the backend supports the matching operation.
