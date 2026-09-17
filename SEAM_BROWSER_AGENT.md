# SEAM Browser Agent

## Current State

No browser automation service exists in the backend.

## Target Capabilities

- Open a URL in a controlled browser session.
- Capture screenshots, console logs, network errors, and DOM summaries.
- Run UI smoke checks for generated web apps.
- Attach browser results as artifacts.
- Request approval before form submission, downloads, credential use, or external network actions.

## Backend Design

Recommended service boundary:

- `BrowserSessionService`
- `BrowserInspectionService`
- `BrowserArtifactService`

Recommended APIs:

- `POST /api/projects/{project_id}/browser/sessions`
- `POST /api/projects/{project_id}/browser/sessions/{session_id}/navigate`
- `POST /api/projects/{project_id}/browser/sessions/{session_id}/inspect`
- `GET /api/projects/{project_id}/browser/sessions/{session_id}/artifacts`

## Implementation Notes

Use Playwright when this feature is implemented. Do not simulate browser success from static text.
