# SEAM E2E Testing And Defect Localization

## Purpose

Application-level E2E validation extends QA beyond static contracts and runtime API checks. It generates traceable workflow scenarios, executes configured browser validation through existing Playwright tooling, and localizes failures to the most likely application layer using evidence.

This is not a new agent and not a replacement for existing QA checks.

## Models

ProjectState now stores:

- `e2e_scenarios`
- `e2e_results`
- `defect_locations`

The structured models are:

- `E2EScenario`
- `E2EStep`
- `E2EStepResult`
- `E2EResult`
- `DefectLocation`

Supported step actions are controlled values such as `OPEN`, `CLICK`, `FILL`, `SELECT`, `WAIT`, `ASSERT_TEXT`, `ASSERT_VISIBLE`, `ASSERT_URL`, `ASSERT_STATUS`, and `SCREENSHOT`.

## Scenario Generation

QAAgent generates scenarios from:

- Analysis requirements
- `FrontendArchitecturePlan.traceability`
- frontend pages/components/files
- API endpoints from contract traceability

Scenarios are not invented outside the current requirements and frontend plan.

## Execution

E2E execution uses existing tools:

- `runtime_manager`
- `runtime_api_validator`
- `playwright_runner`
- `browser_screenshot`

If runtime or Playwright is unavailable, E2E status becomes `BLOCKED` or `NOT_CONFIGURED`; it is never converted to PASS.

## Observation

The Playwright tool returns bounded structured evidence for:

- configured browser test result
- console errors when available
- network errors when available
- screenshots on failure/checkpoints when configured

Secrets, cookies, tokens, passwords, and authorization headers must not be stored or shown.

## Defect Localization

`DefectLocation` records:

- layer
- confidence
- file
- endpoint
- component
- evidence
- issue
- suggested investigation

Layers include:

- `FRONTEND`
- `BACKEND`
- `API_CONTRACT`
- `DATABASE`
- `RUNTIME`
- `AUTHENTICATION`
- `CONFIGURATION`
- `UNKNOWN`

Localization is evidence-based. Low-evidence failures use `UNKNOWN`.

## QA/Rework Flow

Failed E2E results are stored in ProjectState and included in QA findings. CodingAgent can receive:

- failed scenario
- failed step
- expected/actual evidence
- screenshot path
- API/runtime evidence
- console/network evidence
- suspected layer
- affected file when traceability exists

Autonomous defect repair consumes `DefectLocation` and `E2EResult` evidence to create targeted `RepairPlan` records. See `SEAM_AUTONOMOUS_DEFECT_REPAIR.md`.

## Events

QAAgent emits:

- `E2E_SCENARIO_GENERATION_STARTED`
- `E2E_SCENARIO_GENERATED`
- `E2E_EXECUTION_STARTED`
- `E2E_STEP_STARTED`
- `E2E_STEP_COMPLETED`
- `E2E_STEP_FAILED`
- `E2E_EXECUTION_COMPLETED`
- `DEFECT_LOCALIZED`

## IDE

The SEAM IDE renders an E2E Validation summary from ProjectState and event stream. It does not hardcode scenario or defect data.

## Delivery Integration

Delivery & Deployment Intelligence aggregates E2E results into `release_readiness.e2e_status`. Failed E2E results block delivery; missing E2E evidence is reported as `NOT_CONFIGURED` rather than treated as a fake pass.

## Limitations

- Browser execution is only as complete as the existing configured Playwright project.
- SEAM does not execute arbitrary browser JavaScript.
- Network/console observation depends on existing Playwright tooling outputs.
- This implementation does not claim real E2E runtime success unless runtime and browser tooling actually execute.
