# SEAM Scheduled Tasks

## Current State

No scheduler exists in the backend.

## Target Capabilities

- One-time tasks
- Recurring tasks
- Background maintenance jobs
- Nightly QA runs
- Repository refresh
- RAG re-indexing
- Delivery package generation

## Required Safeguards

- Explicit user approval before enabling a schedule.
- Clear next-run time.
- Ability to pause and delete.
- Audit log for every scheduled execution.
- No silent terminal, git, browser, or network actions.

## APIs Needed

- `GET /api/projects/{project_id}/schedules`
- `POST /api/projects/{project_id}/schedules`
- `PATCH /api/projects/{project_id}/schedules/{schedule_id}`
- `DELETE /api/projects/{project_id}/schedules/{schedule_id}`
