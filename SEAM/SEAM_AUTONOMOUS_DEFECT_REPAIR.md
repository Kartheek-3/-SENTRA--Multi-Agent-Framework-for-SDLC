# SEAM Autonomous Defect Repair

## Purpose

Autonomous defect repair closes the QA rework loop. SEAM no longer only reports localized defects; it converts structured defect evidence into a targeted repair plan, routes it through Supervisor and CodingAgent, and verifies the repair before Delivery.

This is not a new RepairAgent.

## Models

ProjectState stores:

- `repair_plans`
- `repair_results`
- `targeted_verifications`
- `regression_results`
- `max_repair_iterations`

Models:

- `RepairPlan`
- `RepairAction`
- `RepairResult`
- `TargetedVerification`
- `RegressionResult`

## Defect To Repair Flow

Inputs:

- `DefectLocation`
- `E2EResult`
- `ContractIssue`
- runtime contract evidence

Output:

- targeted `RepairPlan`

If evidence does not identify a file, endpoint, or component, the plan is marked `NEEDS_REVIEW`.

## Supervisor Integration

Supervisor routes `PENDING` repair plans to CodingAgent using the existing retry/rework loop and `max_repair_iterations`.

Ambiguous `NEEDS_REVIEW` repairs stop the workflow instead of guessing.

## CodingAgent Integration

CodingAgent receives active repair plans in its normal prompt context and is instructed to make the smallest targeted change.

After code generation, CodingAgent records `RepairResult` with:

- modified files
- diff summary
- defect addressed flag
- remaining issues
- verification required

## Verification

QA performs targeted verification first:

- API/backend/contract/database defects -> runtime/static contract validation
- frontend defects -> frontend/E2E validation
- configuration defects -> capability/configured tool validation

Only after targeted verification passes does QA record a related regression result.

## Delivery Gate

Delivery is blocked when:

- repair plans remain unresolved
- targeted verification failed or is blocked
- regression failed or is blocked
- blocker defect evidence remains

Delivery & Deployment Intelligence now records those checks in `release_readiness` and reports unresolved repair evidence as a release blocker before packaging proceeds.

## Events

The repair loop emits:

- `REPAIR_PLAN_CREATED`
- `REPAIR_STARTED`
- `REPAIR_COMPLETED`
- `REPAIR_FAILED`
- `TARGETED_VERIFICATION_STARTED`
- `TARGETED_VERIFICATION_COMPLETED`
- `REGRESSION_STARTED`
- `REGRESSION_COMPLETED`
- `DEFECT_RESOLVED`
- `DEFECT_REMAINING`

## Security

Repair uses existing CodingAgent file-writing and PermissionEngine path controls. It does not push, merge, or modify remotes.

## Limitations

- Live autonomous repair success is not claimed unless an actual failing runtime/E2E cycle is executed.
- Targeted verification uses available ProjectState/tool evidence and configured runtime/browser tooling.
- Ambiguous defects are intentionally marked `NEEDS_REVIEW`.
