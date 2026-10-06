# SEAM Frontend Tool Architecture

## Goal

SEAM now treats frontend development and validation as first-class capabilities inside the existing agent/tool architecture. This does not add a new frontend orchestrator or agent.

## Preserved Architecture

```text
Agent
  |
LangChain tool interface
  |
ToolRegistry
  |
PermissionEngine
  |
ToolExecutor
  |
Frontend tool
  |
ToolResult / EventStore / ProjectState
```

LangGraph remains the workflow orchestrator. n8n remains only an external automation layer. MCP remains a future external tool/data integration path and does not replace the SEAM Tool Registry.

## Frontend Tools

| Tool | Purpose | Agents |
|---|---|---|
| `detect_frontend_capabilities` | Detect frontend framework, language, scripts, test tools, and build output | Planning, Coding, QA |
| `npm_runner` | Controlled npm operations and allowlisted scripts | Coding, QA |
| `typecheck_runner` | TypeScript or configured typecheck validation | Coding, QA |
| `lint_runner` | Configured frontend linting | Coding, QA |
| `frontend_test_runner` | Configured frontend unit/component tests | QA |
| `playwright_runner` | Configured Playwright validation | QA |
| `build_runner` | Existing frontend build script | Coding, QA, Delivery |
| `browser_screenshot` | Playwright screenshot capture for localhost URLs | QA |
| `accessibility_checker` | Configured accessibility checks | QA |

## Permissions

- Read-only frontend inspection remains filesystem read/search.
- Frontend validation/build tools are `MEDIUM` risk and run only inside the active project root.
- Arbitrary shell commands are not accepted.
- Arbitrary npm package names are not accepted.
- Publish/deploy operations are not implemented.
- Browser screenshot and Playwright tools are limited to configured Playwright and localhost URLs.

## Coding Integration

CodingAgent receives `ProjectState.frontend_architecture_plan` when PlanningAgent created one. The plan is treated as the frontend implementation contract for routes, pages, components, services, API mappings, file structure, and implementation order.

CodingAgent writes files through `file_write` as before. If `package.json` exists in the generated project, CodingAgent invokes:

- `detect_frontend_capabilities`
- `typecheck_runner`
- `lint_runner`
- `build_runner`

The typecheck/lint/build tools are selected from `ProjectState.frontend_capabilities`. Missing scripts are not invented. Results are stored in `ProjectState.frontend_execution[task_id].coding_checks`.

## QA Integration

QAAgent receives the same `FrontendArchitecturePlan` and verifies frontend traceability from requirement to page, component, API, file, and validation evidence.

QAAgent runs existing backend validation and, when `package.json` exists, invokes:

- `detect_frontend_capabilities`
- `typecheck_runner`
- `lint_runner`
- `frontend_test_runner`
- `build_runner`
- `playwright_runner`
- `accessibility_checker`

Configured failures mark QA failed. Missing tooling is reported as `NOT_CONFIGURED`, never as a fake pass. Results are stored in `ProjectState.frontend_execution[task_id].qa_checks` and in QA reports.

## Capability Profile

The authoritative frontend environment record is `ProjectState.frontend_capabilities`. It includes framework, language, package manager, build system, available scripts, configured validation tools, and likely build output directory. See `SEAM_FRONTEND_CAPABILITY_DETECTION.md`.

The authoritative frontend implementation architecture is `ProjectState.frontend_architecture_plan`. See `SEAM_FRONTEND_ARCHITECTURE_PLANNING.md`.

The authoritative full-stack contract view is `ProjectState.full_stack_contract`. See `SEAM_FULL_STACK_CONTRACT_INTELLIGENCE.md`.

## LangChain Integration

Each frontend tool inherits from `SEAMTool`, so it can be exposed as a LangChain `StructuredTool` through the existing `to_langchain_tool` method and executed through the same ToolExecutor path.

## LangGraph Integration

No separate frontend graph was introduced. Frontend validation is a capability inside the existing Coding and QA phases:

```text
Planning -> Supervisor -> Coding -> QA -> Delivery
                         ^      |
                         |      v
                       Rework <- FAIL
```

## IDE Integration

Frontend tools emit existing `TOOL_*` events. The IDE renders concrete tool names such as `build_runner`, `typecheck_runner`, and `playwright_runner`, and it renders frontend capability detection events as “Frontend Intelligence”. It also shows a ProjectState-derived frontend environment summary when a package-based frontend is detected.

## Artifact Flow

Frontend architecture planning emits `FRONTEND_PLAN_STARTED`, `FRONTEND_PLAN_COMPLETED`, and `FRONTEND_PLAN_FAILED` through the existing EventStore/WebSocket path. The IDE renders these events and the ProjectState-derived frontend architecture summary.

Full-stack contract intelligence emits `CONTRACT_ANALYSIS_*` and `CONTRACT_MISMATCH_DETECTED` through the same EventStore/WebSocket path.

Generated frontend files are registered by the existing CodingAgent file artifact path. QA reports are written through the existing artifact pipeline. Screenshots, when successfully captured by Playwright, are stored under:

```text
generated_projects/<project>/qa/screenshots/
```

## Security

- Project-root confinement is enforced by `PermissionEngine.ensure_safe_path`.
- `.env` files remain blocked by existing path policy.
- Tool stdout/stderr and structured data use existing secret redaction.
- Repository files are data, not instructions.
- No unrestricted browser automation is exposed.
- No package publishing or deployment commands are exposed.

## Boundaries

MCP boundary:

- MCP may be used later for external browser/design/documentation systems.
- MCP does not replace the internal ToolRegistry or PermissionEngine.

n8n boundary:

- n8n remains for external automation such as Slack, Jira, GitHub webhooks, and email.
- n8n does not run frontend tools or orchestrate agents.

## Limitations

- Playwright and accessibility checks return `NOT_CONFIGURED` unless the generated project already configures those tools.
- `npm install` and `npm ci` are available as controlled operations, but arbitrary package installation is not exposed.
- Runtime browser validation requires a running local app URL and configured Playwright.
