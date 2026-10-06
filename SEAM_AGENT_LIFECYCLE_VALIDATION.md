# SEAM Agent Lifecycle Validation

## Objective

Prevent agents from remaining visually or operationally `RUNNING` indefinitely.

## Implemented Stabilization

- `backend/graph/workflow.py` now emits terminal agent events even when an agent raises an exception.
- Terminal events now include:
  - `AGENT_COMPLETED`
  - `AGENT_FAILED`
  - `AGENT_TIMEOUT`
- `backend/events.py` now maps `AGENT_FAILED`, `AGENT_TIMEOUT`, and `AGENT_CANCELLED` into terminal foundation agent states.
- `seam-ide/src/seam/eventToChatMessage.ts` now displays `AGENT_FAILED`, `AGENT_TIMEOUT`, and `AGENT_CANCELLED` as terminal right-panel chat messages.
- Existing model timeout configuration remains in `MODEL_REQUEST_TIMEOUT`.
- Existing workflow timeout configuration remains in `WORKFLOW_TIMEOUT_SECONDS`.

## Verified By Tests

The full backend suite passed after lifecycle and stabilization changes:

```text
73 passed, 2 warnings in 280.91s
```

Frontend build after lifecycle UI changes:

```text
npm.cmd run build
PASS
```

## Remaining Lifecycle Gaps

Not yet experimentally validated in a live workflow:

- model timeout from a real Ollama hang
- user stop/cancellation of an in-progress thread
- WebSocket reconnect after terminal agent event
- exactly-one-terminal-event invariant under every real workflow branch

## Status

IMPLEMENTED:

- Terminal event emission on normal success and agent exception.
- EventStore/foundation status mapping for failed/timeout/cancelled agent events.
- UI terminal display for failed/timeout/cancelled agent events.

VALIDATED:

- Backend regression suite passes.
- Frontend build passes.

LIMITATION:

- Real timeout/cancel/reconnect experiments were not executed in this pass.
