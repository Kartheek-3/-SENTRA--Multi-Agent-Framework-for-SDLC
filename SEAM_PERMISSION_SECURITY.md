# SEAM Permission And Security

## Current State

The filesystem API protects project paths against traversal and only operates inside the generated project root.

The backend does not yet expose terminal, git write operations, browser automation, scheduled tasks, or remote-control APIs.

## Required Permission Gates

Actions requiring approval:

- File creation outside the project root
- Recursive delete
- Terminal command execution
- Package installation
- Git commit, push, reset, branch deletion, worktree deletion
- Browser automation that submits forms or uses credentials
- Network calls to external services
- Scheduled or recurring actions
- Remote control sessions

## Policy Model

Use per-project policies:

- `allow_read_files`
- `allow_write_files`
- `allow_terminal`
- `allow_network`
- `allow_git_write`
- `allow_browser_actions`
- `allow_schedules`
- `allow_remote_control`

## Implementation Plan

1. Add a permission request table.
2. Emit `PERMISSION_REQUIRED` events.
3. Block the underlying action until approval is granted.
4. Persist approvals with actor, scope, expiration, and audit metadata.
5. Show approvals in the IDE before execution.
