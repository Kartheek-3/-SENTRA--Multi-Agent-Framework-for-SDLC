# SEAM Full-Stack Contract Intelligence

## Purpose

Full-stack contract intelligence validates the relationships between:

```text
Frontend -> API -> Backend -> Database
```

It is part of the existing Planning and QA flow. It does not add a ContractAgent, new graph, new EventStore, new database, or new API specification system.

## Contract Model

The contract profile is stored in `ProjectState.full_stack_contract` and uses:

- `APIContract`
- `APIParameter`
- `APIRequestSchema`
- `APIResponseSchema`
- `FrontendAPIUsage`
- `DatabaseEntityContract`
- `ContractMapping`
- `ContractIssue`
- `FullStackContractProfile`

Project-level issues are also exposed as `ProjectState.contract_issues`.

## Sources

The profile is built from existing SEAM artifacts:

- `ProjectState.frontend_architecture_plan`
- `SystemDesign.api_endpoints`
- `SystemDesign.database_schema`
- frontend service and API integration plans
- frontend traceability when present

The builder does not invent contracts when source artifacts exist. Missing links become explicit `ContractIssue` records.

## Mappings

Each mapping can connect:

```text
Requirement
  -> Frontend page/component/file/service
  -> HTTP method + endpoint
  -> request/response schema
  -> backend model
  -> database entity/table
```

## Mismatch Categories

Implemented validation detects:

- missing backend endpoint
- HTTP method mismatch
- missing frontend API usage
- request schema name mismatch
- response schema name mismatch
- missing database mapping for persistent-looking APIs

The `ContractIssue` model records source, target, file, endpoint, field, expected, actual, severity, description, and suggested fix.

## Planning Integration

PlanningAgent runs contract analysis after frontend architecture planning and stores `ProjectState.full_stack_contract`.

Events:

- `CONTRACT_ANALYSIS_STARTED`
- `CONTRACT_ANALYSIS_COMPLETED`
- `CONTRACT_ANALYSIS_FAILED`

## Coding Integration

CodingAgent receives the serialized `FullStackContractProfile` with its normal task context. It is instructed not to introduce known contract mismatches when expected frontend/API/backend/database contracts are already defined.

## QA Integration

QAAgent rebuilds and validates the contract profile during QA. Contract validation is recorded separately from generic UI checks.

If an ERROR or BLOCKER contract issue exists, QA marks the task failed and emits:

- `CONTRACT_MISMATCH_DETECTED`

The event includes concrete fields such as endpoint, file, expected value, actual value, description, and suggested fix so Supervisor/Coding rework receives actionable detail.

Runtime contract validation is a separate QA layer that checks a running local service against `ProjectState.full_stack_contract` when `ProjectState.runtime_base_url` is available. RuntimeManager may populate that URL for supported local projects. See `SEAM_RUNTIME_CONTRACT_VALIDATION.md` and `SEAM_RUNTIME_LIFECYCLE_MANAGEMENT.md`.

E2E validation adds user-workflow evidence and defect localization on top of static/runtime contract results. See `SEAM_E2E_TESTING_AND_DEFECT_LOCALIZATION.md`.

Autonomous repair uses contract issues as evidence for targeted repair and regression verification. See `SEAM_AUTONOMOUS_DEFECT_REPAIR.md`.

## API And IDE

The existing project status API exposes:

- `full_stack_contract`
- `contract_issues`

The SEAM IDE renders contract analysis events and a ProjectState-derived "Full-Stack Contracts" summary.

## Security

Contract intelligence works on schemas and source structure only. It does not read secrets, tokens, passwords, or `.env` values.

## Limitations

Static contract intelligence does not claim runtime behavior. Runtime checks require an explicitly configured running service and are handled by `runtime_api_validator`.

Field-level type/required mismatch detection is limited to fields present in structured request/response schemas and database schema fields.
