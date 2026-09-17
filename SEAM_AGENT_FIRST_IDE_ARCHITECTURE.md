# SEAM Agent-First IDE Architecture

## Current State

SEAM currently has a FastAPI backend in `SEAM/backend` and a standalone React/Vite IDE in `seam-ide`. The backend keeps the existing six-agent workflow:

- Analysis Agent
- Planning and Design Agent
- Supervisor
- Coding Agent
- QA Agent
- Delivery Agent

The IDE already supports project creation, workflow run/stop commands, WebSocket event streaming, generated file previews, a file explorer, and CodeMirror editing against secured backend filesystem APIs.

## Target Architecture

The Antigravity-style version should become an agent-first IDE with these backend-owned services:

- `TaskService`: durable tasks, task groups, dependencies, status, cancellation, resume.
- `AgentRunService`: agent executions, logs, cost/timing metadata, retries, background runs.
- `ArtifactService`: files, plans, diffs, diagrams, QA reports, browser captures, delivery packages.
- `PermissionService`: approval gates for writes, commands, git, network, browser, and scheduled actions.
- `ConversationService`: ChatGPT/Gemini-style threads with messages linked to tasks and artifacts.
- `EventStore`: persisted event replay, dedupe, and recovery.
- `WorkspaceService`: project filesystem tree, editor file state, search, and generated structure.

The frontend should become a multi-pane IDE shell:

- Left: project explorer, task groups, artifact index.
- Center: editor/workbench with tabs.
- Right: SEAM conversation and agent timeline.
- Bottom: terminal, logs, QA, git, browser, and diagnostics panels.

## Required Event Contract

Every streamed event should include:

- `event_id`
- `timestamp`
- `project_id`
- `run_id`
- `task_id`
- `agent`
- `event`
- `status`
- `summary`
- `artifact_ids`
- `requires_approval`
- `error`

The current event bus provides `event_id`, `timestamp`, and JSONL persistence, but it is still an in-memory pub/sub bus. Durable replay and task-level recovery are not implemented yet.

Update: the backend now includes a first JSON-backed Event Store with sequence numbers and replay/list APIs. Browser reconnect replay has not yet been wired into the standalone IDE.

## Phased Implementation Plan

1. Normalize event schema and add a replay API.
2. Add durable task, run, artifact, and conversation models.
3. Build Agent Manager UI backed by real task/run APIs.
4. Add permission gates before filesystem, terminal, git, browser, and scheduled actions.
5. Add terminal and git panels with restricted backend command execution.
6. Add browser automation as an explicit service with captured artifacts.
7. Add AI editor actions and tab-completion endpoints.
8. Add persistent project history and remote monitoring.
9. Run end-to-end validation with a real generated project.

## Non-Goals For The First Pass

The first implementation pass must not fake subagents, terminal execution, browser results, git operations, voice, or scheduled jobs. Unimplemented capabilities should show `NOT_AVAILABLE` until backed by real backend APIs.
