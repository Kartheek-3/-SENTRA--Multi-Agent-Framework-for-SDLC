# SEAM Remote Control Architecture

## Current State

The app is local-first. There is no remote monitoring, remote command execution, or remote approval service.

## Target Capabilities

- Observe project runs remotely.
- Review pending approvals remotely.
- Receive workflow status updates.
- Resume or cancel tasks with explicit authentication.

## Security Requirements

- Authentication
- Per-project authorization
- Audit logging
- Short-lived session tokens
- Read-only mode by default
- Explicit approval for remote write actions

## Implementation Plan

1. Add persisted event store.
2. Add authenticated project sessions.
3. Add read-only remote status endpoint.
4. Add approval-only remote action flow.
5. Add full remote control only after audit logs and permission gates are enforced.
