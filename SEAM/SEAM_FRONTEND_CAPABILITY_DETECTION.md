# SEAM Frontend Capability Detection

## Purpose

Frontend capability detection lets SEAM understand what frontend technology exists in a generated project before CodingAgent or QAAgent chooses validation tools.

This is not a new agent and not a new orchestration system. It is a ToolRegistry capability named `detect_frontend_capabilities`.

## Architecture

```text
PlanningAgent / CodingAgent / QAAgent
  |
AgentToolBridge
  |
detect_frontend_capabilities
  |
ToolRegistry / PermissionEngine / ToolExecutor
  |
FrontendCapabilityProfile
  |
ProjectState.frontend_capabilities
```

The tool emits normal EventStore/WebSocket events:

- `TOOL_REQUESTED`
- `TOOL_PERMISSION_CHECKED`
- `TOOL_STARTED`
- `TOOL_COMPLETED`

It also emits frontend-specific operational events through the existing event bus:

- `FRONTEND_DETECTION_STARTED`
- `FRONTEND_CAPABILITIES_DETECTED`
- `FRONTEND_DETECTION_FAILED`

## Capability Model

`FrontendCapabilityProfile` records:

- `framework`
- `language`
- `package_manager`
- `build_system`
- `package_json`
- `available_scripts`
- `typecheck_available`
- `lint_available`
- `frontend_test_framework`
- `playwright_available`
- `accessibility_available`
- `dev_server_available`
- `build_available`
- `dev_server_command`
- `build_command`
- `test_command`
- `lint_command`
- `typecheck_command`
- `build_output_directory`
- `detected_files`

Commands are stored as structured argument arrays, not shell strings.

## Supported Frameworks

Detection currently recognizes:

- React
- Vite
- Next.js
- Angular
- Vue

If no known framework is found, SEAM records:

```text
framework = UNKNOWN
```

SEAM does not guess React or Vite.

## Package Managers

Detection order:

- `package-lock.json` -> `npm`
- `pnpm-lock.yaml` -> `pnpm`
- `yarn.lock` -> `yarn`
- otherwise package.json projects default to `npm`

SEAM does not rewrite or replace the package manager.

## Script Detection

The detector reads `package.json` scripts and maps these scripts when present:

- `dev`
- `start`
- `build`
- `test`
- `lint`
- `typecheck`
- `preview`
- `test:e2e`
- `test:a11y`

Missing scripts remain missing. They are never invented.

## Testing Detection

Frontend unit/component test framework detection:

- `vitest` or `vitest.config.*` -> `vitest`
- `jest` or `jest.config.*` -> `jest`
- `@testing-library/react` -> `react_testing_library`
- otherwise `not_configured`

Browser validation:

- `playwright` / `@playwright/test` / `playwright.config.*` -> Playwright available
- otherwise not configured

Accessibility:

- `test:a11y` script or known axe/jest-axe dependencies -> available
- otherwise not configured

## Build Detection

Build availability comes from the actual `build` script.

Likely output directory:

- Vite -> `dist`
- Angular -> `dist`
- Next.js -> `.next`
- Unknown build systems -> not assumed

## Agent Behavior

PlanningAgent:

- uses the detected profile to build `ProjectState.frontend_architecture_plan`
- preserves `UNKNOWN` values when the framework or build system cannot be detected
- never assumes React, Vite, or a routing library from requirement text alone

CodingAgent:

- detects frontend capabilities when `package.json` exists
- stores the profile in `ProjectState.frontend_capabilities`
- runs typecheck/lint/build only when the profile says those capabilities exist

QAAgent:

- detects frontend capabilities when `package.json` exists
- stores the profile in `ProjectState.frontend_capabilities`
- runs configured checks
- records missing checks as `NOT_CONFIGURED`
- does not convert missing tooling into PASS

## NOT_CONFIGURED Behavior

`NOT_CONFIGURED` means the capability was inspected and no safe configured tool/script was found.

Examples:

- no test framework -> frontend tests `NOT_CONFIGURED`
- no Playwright dependency/config -> browser tests `NOT_CONFIGURED`
- no a11y script/framework -> accessibility `NOT_CONFIGURED`

This is not a pass.

## Security Constraints

## Frontend Architecture Planning

PlanningAgent consumes `ProjectState.frontend_capabilities` before building `ProjectState.frontend_architecture_plan`. Unknown frameworks and build systems remain `UNKNOWN`; SEAM does not guess React, Vite, React Router, or state-management libraries from requirement text alone.

- No arbitrary shell strings.
- No arbitrary package scripts beyond the controlled allowlist.
- No path traversal outside project root.
- `.env` files remain blocked by the PermissionEngine.
- Secrets in stdout/stderr/structured data are redacted.
- Repository content is treated as untrusted data.

## IDE

The IDE receives the detected profile from ProjectState and frontend detection events. It displays a real “Frontend Environment” summary only when the backend has detected a `package.json` project.
