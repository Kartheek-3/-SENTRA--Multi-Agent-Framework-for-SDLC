# SEAM Artifact System

## Current State

The backend exposes generated files through:

- `GET /api/projects/{project_id}/artifacts`
- `GET /api/projects/{project_id}/filesystem/tree`
- `GET /api/projects/{project_id}/filesystem/file`

The UI displays generated file cards and opens real files in CodeMirror.

The backend now also includes a first persistent artifact registry at `/artifacts`. Generated code file writes register real `CODE` artifacts when files are written to disk.

## Target Artifact Types

- Source files
- Folder structure snapshots
- Agent plans
- Architecture documents
- Mermaid diagrams
- QA reports
- Test output
- Diffs and patches
- Browser screenshots
- Terminal logs
- Delivery packages

## Required Model

Each artifact should include:

- `artifact_id`
- `project_id`
- `run_id`
- `task_id`
- `agent`
- `type`
- `path`
- `title`
- `summary`
- `created_at`
- `updated_at`
- `metadata`

## Implementation Plan

1. Keep filesystem reads/writes secured under the generated project root. Implemented.
2. Add an artifact registry instead of deriving everything from `os.walk`. Implemented foundation.
3. Link events to artifact IDs. Implemented for generated code artifacts.
4. Add artifact detail and history endpoints. Detail implemented; history remains future work.
5. Render artifacts in chat, explorer, and a dedicated artifact panel. Existing chat/explorer use generated files; dedicated registry UI remains future work.
