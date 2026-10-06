# SEAM Evaluation and Benchmarking

## Purpose

SEAM Evaluation and Benchmarking is a reporting layer over the existing SEAM architecture.

It does not add an EvaluationAgent, a telemetry system, or a separate database. It consumes:

- `ProjectState`
- EventStore
- ArtifactRegistry

The goal is to produce reproducible research and demonstration evidence without fabricating improvements.

## Methodology

For each evaluated project, `EvaluationEngine` collects operational metadata from the completed workflow and writes:

- `evaluation/evaluation_results.json`
- `evaluation/SEAM_EVALUATION_REPORT.md`

Both files are registered through the existing ArtifactRegistry.

## Core Models

- `EvaluationRun`
- `RequirementMetrics`
- `AgentMetric`
- `ToolMetric`
- `QAMetrics`
- `DefectMetrics`
- `RepairMetrics`
- `E2EMetrics`
- `ContractMetrics`
- `DeliveryMetrics`
- `PerformanceMetrics`
- `AutonomyMetrics`
- `DomainRAGMetrics`
- `EvaluationComparison`
- `EvaluationSummary`

## Metrics

The evaluator measures:

- requirements, traceability, and coverage
- agent invocations, success/failure/timeout counts, and durations
- tool invocations, success/failure rates, blocked actions, approval checks, and durations
- QA, contract, runtime, frontend/backend, security, and E2E status
- defects by existing defect category
- repairs, targeted verification, regression, and resolution rate
- delivery readiness, packaging, deployment profile, rollback, and post-deployment verification
- runtime and workflow duration
- autonomy observations
- RAG/domain retrieval metadata

## Formulas

Requirement coverage:

`implemented_and_verified_requirements / total_requirements`

E2E pass rate:

`passed_scenarios / executed_scenarios`

Repair resolution rate:

`resolved_defects / repairable_defects`

Contract compliance:

`contracts_without_unresolved_errors / total_contracts`

If denominator is zero, SEAM reports:

`NOT_APPLICABLE`

It does not return zero for missing evidence.

## Baseline Methodology

Baseline comparison is supported only when actual baseline values are provided.

Supported baseline examples:

- traditional pipeline run
- single-agent run
- tool-assisted non-orchestrated run

The evaluator creates `EvaluationComparison` records with:

- metric
- baseline value
- SEAM value
- absolute difference
- relative difference when mathematically valid

SEAM does not create fake baseline data.

## Research Integrity

The report is descriptive.

It must not claim:

- SEAM is better
- best/worst ranking
- winner
- causal improvement

unless a recorded baseline and study design support that claim.

The current framework reports observed values, limitations, and sample size constraints.

## Domain and RAG Metrics

Domain-aware evaluation records:

- detected domain
- whether knowledge was retrieved
- source types
- number of retrieved documents
- domain retrieval count
- repository knowledge retrieval count
- domain-specific constraints present in requirements

It does not log hidden reasoning and does not claim RAG improved quality without comparison data.

## API and IDE

Project status includes `evaluation_summary`.

The API also exposes:

`GET /api/projects/{project_id}/evaluation`

The SEAM IDE renders an Evaluation section from ProjectState.

## Experiment Harness

The reproducible experiment layer sits above the Evaluation Engine.

It adds:

- a research scenario catalog
- experiment definitions
- scenario definitions
- run configurations
- baseline metadata
- ablation metadata
- isolated run results
- aggregation
- dataset export
- experiment reports

It consumes `EvaluationSummary` outputs and does not recalculate metrics independently. See `SEAM_EXPERIMENT_AND_BENCHMARK_HARNESS.md`.

The scenario catalog is documented in `SEAM_RESEARCH_SCENARIO_CATALOG.md`.

## Reproducibility

Evaluation artifacts include the scenario id, timestamps, durations, counts, and operational evidence available at the time of evaluation.

To reproduce a run:

1. Preserve the generated project directory.
2. Preserve EventStore and ArtifactRegistry runtime files.
3. Re-run the same project requirement under the same configured models/tools.
4. Compare `evaluation_results.json` files.

## Limitations

- Metrics are only as complete as the recorded events and state.
- Missing configured subsystems are reported as `NOT_CONFIGURED`.
- Missing denominators are reported as `NOT_APPLICABLE`.
- A single run is not evidence of superiority.
- External deployment, push, merge, or release creation is not part of evaluation unless actually executed and recorded.
