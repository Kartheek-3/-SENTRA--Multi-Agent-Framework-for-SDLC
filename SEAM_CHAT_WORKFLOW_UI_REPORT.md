# SEAM Chat Workflow UI Report

## Old Workflow UI

The prior standalone IDE right panel was section/dashboard oriented. It showed status metrics, JSON blocks, and separate panels for agents, QA, delivery, RAG, diagrams, and logs.

## New Conversational UI

The right panel is now a ChatGPT/Gemini-style SEAM AI conversation. It displays user requirements, SEAM replies, agent progress, supervisor events, task events, file cards, warnings, errors, and final summaries when the backend actually emits the corresponding events.

## Chat Architecture

- `ChatMessage` model: `seam-ide/src/seam/chatTypes.ts`
- Event translator: `seam-ide/src/seam/eventToChatMessage.ts`
- Chat UI: `seam-ide/src/seam/SeamPanel.tsx`
- App wiring and deduplication: `seam-ide/src/App.tsx`

Messages support roles `USER`, `SEAM`, `AGENT`, and `SYSTEM`; types such as `MESSAGE`, `PROGRESS`, `TASK`, `FILE`, `QA`, `ERROR`, `SUCCESS`, `WARNING`, `DIAGRAM`, and `SUMMARY`; and statuses `WAITING`, `RUNNING`, `COMPLETE`, `FAILED`, `BLOCKED`, and `NOT_AVAILABLE`.

## Event Architecture

Backend events now include:

- `event_id`
- `timestamp`
- `event`
- optional `agent`
- optional `task_id`
- optional `path`
- optional `operation`
- optional `error`

Events are persisted per project in:

```text
generated_projects/<project>/logs/execution_events.jsonl
```

## WebSocket Integration

The UI still uses:

```text
/api/projects/{project_id}/events
```

WebSocket events are translated with `eventToChatMessages()` and deduplicated with a processed-event set.

## ProjectState Synchronization

ProjectState remains authoritative. After a WebSocket event, the UI fetches `GET /api/projects/{project_id}/status` and uses backend state for summaries. Limitation: the backend currently merges LangGraph state back into `projects_db` only after `workflow.invoke()` returns, so long-running agent calls can leave status sparse while events continue streaming.

## Agent Progress

Implemented for real backend events:

- `AGENT_STARTED`
- `AGENT_COMPLETED`
- `TASK_STARTED`
- `TASK_COMPLETED`
- `FILE_GENERATED`
- `FILE_UPDATED`
- `WORKFLOW_STARTED`
- `WORKFLOW_COMPLETED`
- `WORKFLOW_FAILED`
- `WORKFLOW_STOPPED`

No fake timers or fake token streaming were added.

## Code-File Integration

File events produce file cards with an `Open File` button. Clicking opens the actual generated file in the center CodeMirror editor through the existing secure backend file API.

The chat now also reads the actual saved file after `FILE_GENERATED` / `FILE_UPDATED` and displays a bounded code preview in the conversation. This is not fake token streaming; it is a real preview from disk after the LLM-generated file has been written.

## Explorer Integration

On `DIRECTORY_CREATED`, `FILE_GENERATED`, `FILE_UPDATED`, and `WORKFLOW_COMPLETED`, the Explorer refreshes from the backend file tree.

The coding agent now emits `DIRECTORY_CREATED` for newly created folders and emits file events only after writing the file to disk. Coding, QA, Delivery, artifacts, and filesystem APIs now use the same project-name folder, so the visible Explorer tree and chat file cards point to the same physical project.

## QA Progress

QA start/completion events map to QA chat messages. QA summaries use actual ProjectState task `qa_result` values. If test execution is missing, the UI shows `NOT_AVAILABLE`.

## Delivery Progress

Delivery messages are driven by `DeliveryAgent` start/completion events and `delivery_result` from ProjectState.

## Diagrams

Diagram chat cards are supported by message type and artifact shape. Diagram-generation-specific backend events are not currently emitted, so this remains partially available through ProjectState/API queries.

## RAG

RAG remains backend-controlled. Health currently reports RAG online. Chat commands can query current state but do not expose hidden vector details.

## GitHub Optional Behavior

GitHub token is currently missing. Backend health reports `token_missing`, and the chat UI treats GitHub as optional instead of failing the core workflow.

## Performance Optimizations

- Chat list renders only the most recent 150 visible messages.
- Stored chat state is capped at 300 messages.
- Long messages are collapsed behind `Show details`.
- Events are deduplicated by `event_id`.
- Files are loaded on demand.
- Explorer refreshes only on relevant events.

## Security

- No hidden chain-of-thought is displayed.
- Chat commands map only to real backend operations or ProjectState queries.
- File cards use safe backend file APIs.
- No frontend secrets are introduced.
- No VS Code, Unity, PlantUML, or StarUML dependency was introduced.

## Testing

| Feature | Status | Evidence | Notes |
| --- | --- | --- | --- |
| Frontend build | PASS | `npm run build` completed | Vite bundle generated |
| Standalone IDE launch | PASS | `http://127.0.0.1:5173/` returned 200 | Dev server running |
| Backend health | PASS | `/health` returned `{"status":"ok","service":"SEAM"}` | FastAPI running |
| Qwen status | PASS | `/api/system/health` reported `qwen: online` | Ollama was online during final check |
| RAG status | PASS | `/api/system/health` reported `rag: online` | Chroma/RAG initialized |
| GitHub optional | PASS | `/api/system/health` reported `github: token_missing` | Core app does not fail |
| Event ids/timestamps | PASS | persisted JSONL contains `event_id` and `timestamp` | `execution_events.jsonl` verified |
| Event persistence | PASS | `generated_projects/chat_workflow_event_test/logs/execution_events.jsonl` written | Project-created test |
| Event translator | PASS | Build compiles translator and chat model | Runtime UI path wired |
| Event deduplication | PASS | `processedEvents` set in `App.tsx` | Avoids reconnect duplicates |
| File cards | PASS | `FILE_GENERATED`/`FILE_UPDATED` maps to `artifact.kind=file` | Opens through existing editor path |
| Code preview in chat | PASS | File events read saved file content and attach `codePreview` | Bounded preview; full file opens in editor |
| Project structure visibility | PASS | `DIRECTORY_CREATED` event added, Explorer refreshes | Real folders only |
| Generated folder/file API alignment | PASS | Coding/QA/Delivery use project-name generated folder | Matches Explorer/artifacts APIs |
| WebSocket handling | PASS | Existing WebSocket client wired to translator | Long workflow events persist |
| ProjectState sync | PASS | UI fetches `/status` after events | Backend sparse during long invoke is a limitation |
| Real Smart E-Commerce workflow | BLOCKED | Workflow still running after polling window | No final result fabricated |
| Analysis event | PASS | `AGENT_STARTED AnalysisAgent` persisted | LLM call was still running |
| Planning event | BLOCKED | Workflow did not reach planning during polling window | Waiting on AnalysisAgent |
| Supervisor event | PASS | `SupervisorAgent` started/completed persisted | Real event log |
| Coding event | BLOCKED | Workflow did not reach coding during polling window | Waiting on earlier agents |
| QA event | BLOCKED | Workflow did not reach QA during polling window | Waiting on earlier agents |
| Delivery event | BLOCKED | Workflow did not reach delivery during polling window | Waiting on earlier agents |
| Controlled QA failure | BLOCKED | Not reached in real workflow | No fake QA failure added |
| Diagram event | NOT_AVAILABLE | Backend does not emit diagram-specific events yet | Diagram APIs still exist |

## E2E Results

Created and started real project:

```text
Smart E-Commerce Platform
project_id: 190a3509-56ec-45a5-b4f7-16e74dc5e80b
```

Observed persisted events:

```text
PROJECT_CREATED
WORKFLOW_STARTED
AGENT_STARTED SupervisorAgent
AGENT_COMPLETED SupervisorAgent
AGENT_STARTED AnalysisAgent
```

After the polling window, ProjectState still reported:

```text
workflow=running
errors=0
```

Final completion was not claimed.

## Known Limitations

- Full E2E completion depends on local LLM speed and did not finish in the polling window.
- Backend ProjectState does not update incrementally inside `workflow.invoke()`; events are live, but state fields update primarily after the graph returns.
- Backend does not yet emit dedicated diagram/RAG/GitHub/QA detail events beyond the current agent/task/directory/file/workflow events.
- Frontend test runner such as Vitest is not configured; current validation is build/API/runtime based.

## Final Status

The SEAM right panel now behaves as a live AI workflow conversation driven by real backend events and ProjectState. The full multi-agent completion remains BLOCKED/RUNNING until the local backend finishes the real Smart E-Commerce workflow.
