# SEAM Runtime Contract Validation

## Purpose

Runtime contract validation checks whether a running local application conforms to `ProjectState.full_stack_contract`.

It extends static full-stack contract intelligence. It does not replace it, start servers, or create a new agent.

## Tool

`runtime_api_validator` is a controlled ToolRegistry tool available to `QAAgent`.

It accepts structured input:

- `base_url`
- `endpoint`
- `method`
- `request`
- `expected_request_schema`
- `expected_response_schema`
- `expected_status_codes`
- `authentication_required`

It does not accept shell commands.

## Security Model

The tool only allows explicit local project runtime URLs:

- `http://127.0.0.1:<port>`
- `http://localhost:<port>`

It blocks external URLs, requires an explicit port, keeps requests on the configured origin, and redacts secret-like values through the existing ToolResult redaction path.

It does not store credentials, tokens, cookies, or authorization headers.

## Result States

`RuntimeContractResult.status` may be:

- `PASS`
- `FAIL`
- `BLOCKED`
- `NOT_CONFIGURED`
- `UNAVAILABLE`
- `TIMEOUT`

Unavailable runtime infrastructure is never converted to PASS.

## QA Integration

QAAgent runs static contract validation first, then runtime contract validation.

Runtime validation uses `ProjectState.runtime_base_url`. RuntimeManager can populate that URL when it safely starts a supported local runtime. If no base URL exists, QA records:

```text
runtime_contract_validation: NOT_CONFIGURED
```

Application-level E2E validation runs after runtime contract validation when runtime and configured Playwright tooling are available. See `SEAM_E2E_TESTING_AND_DEFECT_LOCALIZATION.md`.

QA emits:

- `RUNTIME_CONTRACT_VALIDATION_STARTED`
- `RUNTIME_CONTRACT_VALIDATION_COMPLETED`
- `RUNTIME_CONTRACT_VALIDATION_FAILED`
- `RUNTIME_CONTRACT_MISMATCH_DETECTED`

Runtime ERROR/BLOCKER issues fail QA and are added to `ProjectState.contract_issues`.

Autonomous repair can convert runtime contract failures into targeted repair plans and verification records. See `SEAM_AUTONOMOUS_DEFECT_REPAIR.md`.

## Rework Integration

Runtime failures are normalized as `ContractIssue` records. They include endpoint, field, expected value, actual value, description, and suggested fix so CodingAgent receives concrete rework context through ProjectState and QA feedback.

## Traceability

Runtime results are stored in `ProjectState.runtime_contract_results` and remain linked to the static contract endpoint/method.

The traceability chain is:

```text
Requirement -> Frontend Architecture -> Static Contract -> Runtime Contract -> API -> Backend -> Database -> QA
```

## Limitations

- SEAM only starts servers through the controlled `runtime_manager` lifecycle.
- SEAM does not guess arbitrary ports; it selects bounded local ports from detected runtime profiles.
- Runtime validation requires `ProjectState.runtime_base_url`, either explicitly configured or produced by RuntimeManager.
- Authentication checks are structural and status-code based; real credential flows are not implemented here.
