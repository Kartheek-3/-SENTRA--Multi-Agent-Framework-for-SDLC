# SEAM Frontend Architecture Planning

## Purpose

Frontend architecture planning makes PlanningAgent produce a structured implementation contract before CodingAgent generates frontend files.

This is not a new agent, graph, tool registry, or project state system. It is part of the existing Planning phase and is stored once in `ProjectState.frontend_architecture_plan`.

## Flow

```text
Requirement
  -> AnalysisAgent
  -> PlanningAgent
  -> detect_frontend_capabilities
  -> FrontendArchitecturePlan
  -> ProjectState
  -> CodingAgent
  -> QAAgent
```

## Model

`FrontendArchitecturePlan` records:

- framework, language, and build system from `ProjectState.frontend_capabilities`
- routing strategy and route metadata
- page plans
- layout and component plans
- service/API integration plans
- authentication notes when required
- forms and validation expectations
- error/loading/responsive/accessibility strategies
- testing strategy from detected tools
- file-level create/modify plan
- implementation order
- requirement -> page -> component -> API -> file -> validation traceability

Unknown frontend environments remain `UNKNOWN`. SEAM does not assume React, Vite, React Router, Redux, or any other library when the capability profile does not prove it exists.

## Capability-Aware Planning

PlanningAgent consumes `ProjectState.frontend_capabilities` and may invoke the existing `detect_frontend_capabilities` tool when frontend scope is present and no profile exists yet.

The detected profile remains the source for:

- framework
- language
- package/build system
- configured typecheck, lint, unit, browser, accessibility, and build tools

## API Contract Mapping

Frontend pages are mapped to existing `SystemDesign.api_endpoints` where possible.

If no matching backend API contract exists, the plan records a mismatch note instead of inventing an endpoint.

## Coding Handoff

CodingAgent receives the serialized `FrontendArchitecturePlan` in its prompt. When a valid plan exists, CodingAgent must follow its:

- framework and build assumptions
- routes and pages
- components and services
- API mappings
- file plan
- implementation order

## QA Traceability

QAAgent receives the same plan and records frontend architecture traceability under `ProjectState.frontend_execution[task_id].architecture_traceability` when frontend QA runs.

The traceability contract is:

```text
Requirement -> Page -> Component -> API -> File -> Validation
```

Full-stack contract intelligence extends this with API/backend/database mappings in `ProjectState.full_stack_contract`.

## Events

Planning emits events through the existing EventStore/WebSocket path:

- `FRONTEND_PLAN_STARTED`
- `FRONTEND_PLAN_COMPLETED`
- `FRONTEND_PLAN_FAILED`

After frontend planning, PlanningAgent also runs full-stack contract analysis and emits `CONTRACT_ANALYSIS_STARTED`, `CONTRACT_ANALYSIS_COMPLETED`, or `CONTRACT_ANALYSIS_FAILED`.

The SEAM IDE renders these events and also displays a ProjectState-derived "Frontend Architecture" summary.

## Security

- No arbitrary commands are introduced.
- No dependencies are added by planning.
- No file writes happen during planning.
- Repository content and RAG context are treated as reference data only.
- Project-root path restrictions remain enforced by existing tools.
