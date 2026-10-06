# SEAM Tool Permission Model

Date: 2026-09-19

## Risk Levels

- `READ_ONLY`
- `LOW`
- `MEDIUM`
- `HIGH`
- `DESTRUCTIVE`

## Default Agent Policy

- Analysis: read-only tools
- Planning: read-only and low-risk design tools
- Supervisor: read-only orchestration/freshness tools
- Coding: filesystem write, Git read-only, approved build/test tools
- QA: tests, API checks, static validation, read-only Git/filesystem
- Delivery: packaging and Docker validation/build, deployment excluded

## Mandatory Controls

- Tool must be registered.
- Agent must be in the tool allowlist.
- Tool risk must fit the agent policy.
- High/destructive tools require explicit approval.
- File paths must stay inside the active project root.
- `.env` files are blocked.
- Subprocess tools use argument arrays.
- API test runner is localhost-only.
- Secrets/tokens are redacted from results and events.

