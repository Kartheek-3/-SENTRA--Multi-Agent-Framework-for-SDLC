# SEAM Git System

## Current State

GitHub Intelligence exists in `SEAM/backend/github`, but the standalone IDE does not yet expose a full git panel, local git operations, branches, commits, pull requests, or worktrees.

## Target Capabilities

- Repository status
- Diff viewer
- Stage and unstage
- Commit
- Branch creation and checkout
- Worktree creation for parallel agents
- Pull request metadata
- GitHub repository intelligence results

## Safety Rules

Write operations require approval:

- Commit
- Push
- Reset
- Rebase
- Merge
- Delete branch
- Delete worktree

## APIs Needed

- `GET /api/projects/{project_id}/git/status`
- `GET /api/projects/{project_id}/git/diff`
- `POST /api/projects/{project_id}/git/stage`
- `POST /api/projects/{project_id}/git/commit`
- `POST /api/projects/{project_id}/git/worktrees`

Git commands should run only inside approved project roots.
