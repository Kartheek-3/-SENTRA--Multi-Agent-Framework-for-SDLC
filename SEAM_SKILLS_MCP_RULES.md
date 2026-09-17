# SEAM Skills, MCP, And Rules

## Current State

The backend has project knowledge/RAG APIs, but no first-class skills, MCP server registry, or project rules engine.

## Target Capabilities

- Project rules files
- Agent-specific instructions
- Skill registry
- MCP tool registry
- Tool permission policies
- Context attachments using `@file`, `@folder`, `@artifact`, and `@task`

## Suggested Rule Files

- `.seam/rules.md`
- `.seam/agents.md`
- `.seam/tools.json`
- `.seam/permissions.json`

## Backend APIs Needed

- `GET /api/projects/{project_id}/rules`
- `PUT /api/projects/{project_id}/rules`
- `GET /api/projects/{project_id}/skills`
- `GET /api/projects/{project_id}/mcp/tools`

Rules should be loaded into agent prompts through a controlled context builder, not concatenated ad hoc inside UI code.
