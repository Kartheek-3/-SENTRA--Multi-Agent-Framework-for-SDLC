# SEAM Performance Baseline

## Measurement Date
2026-09-17

## Baseline Scope
This baseline records the observed behavior before the performance changes in this pass. It does not invent a complete workflow duration because the demo workflow did not complete during the observed window.

## Demo Project Used
- Project name: `small_todo_demo`
- Project ID: `8ceea6f6-39e3-4284-a2e7-3e9da8cd39f8`
- Requirement: small full-stack Task Manager / task tracker
- Technology: React, FastAPI, SQLite
- Scale: SMALL

## Observed API Measurements
- `GET /health`: PASS, returned `{"status":"ok","service":"SEAM"}`
- `GET /api/projects`: PASS, returned an empty project list before demo creation
- `POST /api/projects`: PASS, project created
- `POST /api/projects/{project_id}/run`: PASS, returned `status=running`
- First status sample after about 20 seconds:
  - `workflow_status`: `running`
  - `current_agent`: `null`
  - `current_task`: `null`
  - `execution_history`: `0`
  - `errors`: `0`
  - `tasks`: `0`
- Later status polling blocked long enough that the command was aborted by the operator.

## Bottlenecks Identified From Code Inspection
- Workflow execution used FastAPI background task execution without an explicit bounded execution manager or timeout.
- No workflow-level timeout existed, so a workflow could remain visibly `running` without producing agent progress.
- Analysis and Planning were using the default model route instead of explicit `analysis` and `planning` routes.
- LLM calls were not recorded with duration, model, timeout, retry count, or estimated input size.
- Diagram generation was sequential across eight independent diagram types.
- Diagram rendering was coupled to diagram generation and not timed separately.
- RAG retrieval was called synchronously without per-call latency records.
- Model availability lookup created a new HTTP connection instead of reusing a session.

## Missing Baseline Measurements
These could not be measured before optimization because the observed workflow did not reach the corresponding phases:
- `analysis_started` / `analysis_completed`
- `planning_started` / `planning_completed`
- `coding_started` / `coding_completed`
- `qa_started` / `qa_completed`
- `delivery_started` / `delivery_completed`
- completed workflow P50/P95/P99
- diagram generation duration
- QA duration
- delivery duration

## Baseline Conclusion
The immediate baseline bottleneck is not merely slow model generation. The workflow can enter `running` without visible phase progress or bounded failure, making latency unbounded from the user's perspective. The first optimization target is therefore observability, bounded execution, and fail-fast behavior before claiming percentage improvements.
