# SEAM Experiment and Benchmark Harness

## Purpose

The Experiment Harness is a reproducible research layer above the existing SEAM workflow and Evaluation Engine.

It does not create another agent, workflow engine, telemetry system, or database.

## Architecture

Experiment Definition
-> Experiment Harness
-> isolated Project Run
-> Evaluation Engine
-> EvaluationRun
-> Aggregation
-> Comparison
-> Dataset
-> Research Report

## Models

- `ExperimentDefinition`
- `ScenarioDefinition`
- `RunConfiguration`
- `ReproducibilityMetadata`
- `RunResult`
- `AggregateMetric`
- `ExperimentComparison`
- `ExperimentRun`

## Scenarios

Scenarios are reusable definitions with:

- scenario id
- name
- description
- domain
- complexity
- complexity rationale
- requirements
- required features
- expected artifacts
- expected validation layers
- expected capabilities
- seed/configuration
- evaluation metrics

The harness does not hardcode successful outcomes.

The initial catalog is documented in `SEAM_RESEARCH_SCENARIO_CATALOG.md`.

## Configurations

Supported configuration examples:

- `SEAM_FULL`
- `SEAM_NO_DOMAIN_RAG`
- `SEAM_NO_GITHUB_CONTEXT`
- `SEAM_NO_AUTONOMOUS_REPAIR`
- `BASELINE`

Configurations are experiment metadata. The harness does not silently modify production architecture.

## Baseline Support

Baselines are supported only when recorded baseline data or a baseline run exists.

Stored baseline metadata includes:

- source
- version
- configuration
- provenance

No baseline values are fabricated.

## Ablation Support

Ablations are represented with explicit `disabled_capabilities`.

Examples:

- without domain-aware RAG
- without autonomous repair
- without runtime validation
- without GitHub intelligence

The report records the configuration; it does not claim causality without a valid experimental design.

## Run Isolation

Every run records:

- unique experiment id
- unique run id
- unique project id
- scenario id
- configuration id
- repetition index

Evaluation consumes EventStore events for the current project id only, preventing cross-run event mixing.

## Controlled Execution

`ExperimentHarness.execute_controlled_run(...)` creates an isolated ProjectState from a catalog scenario, applies explicit configuration metadata, runs the existing SEAM workflow, and then records the resulting EvaluationRun.

This method does not bypass the normal workflow and does not create another workflow engine.

## Ablation Wiring

Operational ablations are wired into the existing execution path:

- `ABLATION_NO_DOMAIN_RAG` skips domain-aware retrieval/context injection while leaving general RAG infrastructure available.
- `ABLATION_NO_AUTONOMOUS_REPAIR` preserves QA and defect evidence but prevents Supervisor from routing automatic Coding repair.
- `ABLATION_NO_CONTRACT_INTELLIGENCE` skips static and runtime contract intelligence while leaving other QA layers active.

If a configuration cannot be safely disabled, it must be reported as `NOT_IMPLEMENTED`.

## Dry Run

`ExperimentHarness.dry_run(experiment_id)` reports scenarios, configurations, disabled capabilities, repetitions, and metrics without executing project generation.

## Experiment Matrix

The harness exposes an experiment matrix:

Experiment -> Scenario -> Configuration -> Runs

The matrix reports expected repetitions and completed runs. Missing runs remain absent; they are not fabricated.

## Data Quality

Each `RunResult` includes data-quality checks for:

- experiment id
- scenario id
- configuration id
- run id
- evaluation id
- ProjectState/run/evaluation project id alignment
- model metadata

Invalid runs are marked `INVALID` and excluded from aggregate metrics.

## Reproducibility Metadata

Each `RunResult` records:

- timestamp
- git commit when available
- model name and configured agent models
- knowledge base version
- repository context version
- configuration flags
- operating environment
- Python version
- Node version
- relevant package versions
- seed
- nondeterminism limitations

Secrets, tokens, cookies, `.env` values, passwords, and hidden reasoning are excluded.

## Aggregation

For repeated runs, the harness calculates:

- count
- mean
- median
- minimum
- maximum
- standard deviation

Statistics are calculated only from valid numeric observations. Missing values remain `NOT_APPLICABLE`.

## Dataset Export

The harness writes:

- `evaluation/datasets/experiment_results.json`
- `evaluation/datasets/experiment_results.csv`

Each row is one normalized run record.

## Report Generation

The harness writes:

- `evaluation/reports/<experiment_id>_SEAM_EXPERIMENT_REPORT.md`
- `evaluation/reports/scenario_catalog.md`
- `evaluation/reports/experiment_catalog.md`

The report includes experiment definition, hypothesis, scenarios, configurations, number of runs, environment, raw observations, aggregated observations, baseline/ablation observations, limitations, and reproducibility metadata.

It reports measurements only. It does not use rankings, winners, or “best system” language.

## Events

The harness emits:

- `EXPERIMENT_CREATED`
- `EXPERIMENT_STARTED`
- `EXPERIMENT_RUN_STARTED`
- `EXPERIMENT_RUN_COMPLETED`
- `EXPERIMENT_RUN_FAILED`
- `EXPERIMENT_COMPARISON_STARTED`
- `EXPERIMENT_COMPARISON_COMPLETED`
- `EXPERIMENT_COMPLETED`

## API

The existing FastAPI app exposes:

- `POST /api/experiments`
- `GET /api/experiments`
- `GET /api/experiments/{id}`
- `GET /api/experiments/{id}/runs`
- `GET /api/experiments/{id}/comparison`

## Benchmark Runner

The existing `tests/run_benchmark.py` now recognizes conceptual experiment commands:

- `run experiment`
- `run scenario`
- `run baseline`
- `run ablation`
- `compare experiment`
- `export dataset`
- `generate report`

No separate runner was created.

## Limitations

- The harness records actual EvaluationEngine outputs only.
- It does not fabricate missing baselines, ablations, or runs.
- It does not claim performance improvements.
- It does not prove causality from a single run.
- It depends on isolated project ids and recorded EventStore data.
