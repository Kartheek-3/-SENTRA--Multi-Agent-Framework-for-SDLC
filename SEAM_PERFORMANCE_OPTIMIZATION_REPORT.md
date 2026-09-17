# SEAM Performance Optimization Report

## 1. Baseline Architecture
SEAM uses a six-agent workflow: Analysis, Planning & Design, Supervisor, Coding, QA, and Delivery. The existing workflow is driven through FastAPI and LangGraph, with Ollama/Qwen model calls, RAG retrieval, artifact persistence, event streaming, and a React IDE frontend.

## 2. Bottlenecks Discovered
- Workflows could remain `running` without a bounded timeout.
- Agent and LLM durations were not persisted in a machine-readable performance log.
- Eight diagram LLM generations ran sequentially.
- Analysis and Planning were not using explicit task-specific model routes.
- Ollama model discovery did not reuse an HTTP session.

## 3. Measured Latency
Actual baseline measurements are recorded in `SEAM_PERFORMANCE_BASELINE.md`. A completed before/after workflow percentage is not reported because the baseline demo did not complete.

## 4. Optimizations Implemented
- Added append-only performance event logging at `.seam/runtime/performance_events.jsonl`.
- Added workflow execution timing.
- Added agent phase timing.
- Added LLM call timing with model, retry count, timeout, and estimated input tokens.
- Added RAG retrieval timing.
- Added bounded LLM concurrency.
- Added bounded workflow execution.
- Added workflow timeout failure reporting.
- Added bounded parallel diagram generation.
- Added separate diagram rendering timing.
- Fixed Analysis and Planning model routing.
- Reused a persistent HTTP session for Ollama model discovery.

## 5. Async Execution
The FastAPI workflow start endpoint now submits workflow work to a bounded in-process executor and returns immediately. Timeout monitoring runs in a lightweight daemon thread.

## 6. Parallel Execution
Diagram generation now submits the eight independent diagrams to a bounded executor after the authoritative planning model exists. The diagrams still consume the same validated analysis and project plan.

## 7. Caching
Full result caching is not implemented in this pass. The new performance log provides the data needed to decide where caching should be added safely.

## 8. Model Routing
Analysis uses the configured analysis model. Planning uses the configured planning model. Coding and QA continue to use their configured task-specific routes. A configurable fast model setting was added for future lightweight operations.

## 9. RAG Optimization
RAG calls are now measured. Retrieval behavior and top-k policy were not changed in this pass to avoid altering quality without completed baseline data.

## 10. Connection Pooling
Ollama model discovery now uses a shared `requests.Session`.

## 11. Event Optimization
Workflow, agent, LLM, RAG, and diagram performance events are append-only JSONL records. Existing user-facing event behavior is preserved.

## 12. Diagram Optimization
Diagram generation is bounded-parallel. Rendering is measured independently and still writes real PNG artifacts.

## 13. QA Optimization
QA model calls are now timed. Deterministic QA checks remain intact.

## 14. Timeout / Retry Strategy
The workflow now has `SEAM_WORKFLOW_TIMEOUT_SECONDS`. Model requests use `SEAM_MODEL_REQUEST_TIMEOUT`. Existing bounded agent retry loops remain in place.

## 15. Before / After Measurements
Before/after improvement percentage is intentionally not reported yet. A valid comparison requires one completed baseline run and one completed optimized run for the same prompt, model, and environment.

## 16. P50 / P95 / P99
Not available yet. The new JSONL performance log enables these once multiple completed runs exist.

## 17. Quality Validation
Required agents and artifacts were not removed. Diagram generation still uses the planning model and produces JSON plus PNG artifacts. QA remains enabled.

## 18. Regression Test Results
- Backend compile: PASS
- Frontend build: PASS
- ModelRouter runtime construction with configured Qwen model: PASS
- Full Task Manager E2E: NOT RUN in this pass because the running server must be restarted to load the new backend code, and the previous baseline workflow did not complete.

## 19. Remaining Bottlenecks
- Full artifact/result caching by content hash.
- Incremental coding task parallelism.
- EventStore JSON table rewrite cost.
- ArtifactRegistry path index.
- Deterministic QA parallel checks.
- WebSocket batching for high-frequency progress.

## 20. Next Measurement Step
Restart the backend so it loads these changes, run the same small Task Manager prompt, then compare `.seam/runtime/performance_events.jsonl` against this baseline.
