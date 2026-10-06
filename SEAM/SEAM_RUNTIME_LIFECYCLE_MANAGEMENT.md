# SEAM Runtime Lifecycle Management

## Purpose

Runtime lifecycle management lets QAAgent safely prepare a local project runtime before runtime contract validation.

This is a tool capability named `runtime_manager`, not a RuntimeAgent and not a replacement for LangGraph, ToolRegistry, ProjectState, or `runtime_api_validator`.

## Actions

`runtime_manager` supports:

- `DETECT`
- `START`
- `HEALTH_CHECK`
- `STATUS`
- `STOP`

All actions run through the existing ToolRegistry, PermissionEngine, ToolExecutor, and AgentToolBridge.

## Runtime Detection

Frontend detection uses existing project metadata only:

- `package.json`
- existing scripts such as `dev` or `start`
- detected package manager: npm, pnpm, or yarn

Backend detection recognizes actual files/configuration:

- FastAPI when an app file contains `FastAPI(`
- Flask when an app file contains `Flask(`

SEAM does not invent commands or entry points.

## Process Lifecycle

RuntimeManager starts only project-owned processes from safe argument arrays. It stores:

- process name
- PID
- command array
- project root
- selected port
- URL
- status

STOP only affects processes created and tracked by SEAM for the current project root.

## Port Management

RuntimeManager uses localhost only and chooses an available local port near the project/default runtime port:

- frontend: 5173 or nearby
- backend: 8401 or nearby

The selected backend URL is stored in `ProjectState.runtime_base_url` for `runtime_api_validator`.

## Health Checks

Backend health checks use `/health` when available in the profile. Frontend health checks use the runtime root.

Readiness states:

- `READY`
- `NOT_READY`
- `UNAVAILABLE`
- `TIMEOUT`

Runtime infrastructure that cannot start or become healthy is never treated as PASS.

## QA Integration

QA flow now includes:

```text
Static Contract Validation
Runtime Detection
Runtime Start
Health Check
Runtime Contract Validation
Runtime Cleanup
Frontend/API/Browser Validation
Final QA
```

If runtime detection has no supported command, QA records `runtime_lifecycle: NOT_CONFIGURED`.

## Events

Runtime lifecycle emits:

- `RUNTIME_DETECTION_STARTED`
- `RUNTIME_DETECTION_COMPLETED`
- `RUNTIME_START_STARTED`
- `RUNTIME_STARTED`
- `RUNTIME_START_FAILED`
- `RUNTIME_HEALTH_CHECK_STARTED`
- `RUNTIME_READY`
- `RUNTIME_HEALTH_FAILED`
- `RUNTIME_STOP_STARTED`
- `RUNTIME_STOPPED`

## Security

RuntimeManager enforces:

- project-root confinement
- localhost-only runtime
- safe executable allowlist
- safe argument arrays
- no arbitrary shell strings
- no shell chaining or redirection
- no arbitrary process termination
- no remote URL access
- no credential persistence
- no `.env` exposure

## Limitations

- Server lifecycle support is intentionally conservative.
- Only detected npm/pnpm/yarn frontend scripts and recognized FastAPI/Flask entry points are supported.
- RuntimeManager does not install dependencies.
- RuntimeManager does not run production deployment or remote services.

## E2E Integration

Application-level E2E validation runs after runtime readiness when configured browser tooling exists. See `SEAM_E2E_TESTING_AND_DEFECT_LOCALIZATION.md`.

## Delivery Integration

Delivery & Deployment Intelligence consumes `runtime_status`, `runtime_base_url`, runtime processes, and runtime contract results. Runtime failures become release blockers, while unavailable runtime evidence is reported honestly as `NOT_CONFIGURED`.
