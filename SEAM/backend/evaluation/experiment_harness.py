import csv
import json
import os
import platform
import statistics
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from io import StringIO
from typing import Any, Dict, List, Optional

from backend.events import event_bus
from backend.evaluation.engine import EvaluationEngine
from backend.evaluation.scenario_catalog import experiment_catalog, scenario_catalog
from backend.models.evaluation import (
    AggregateMetric,
    EvaluationComparison,
    ExperimentComparison,
    ExperimentDefinition,
    ExperimentRun,
    ReproducibilityMetadata,
    RunConfiguration,
    RunResult,
    ScenarioDefinition,
)
from backend.models.state import ProjectState
from backend.tools.artifact_pipeline import write_text_artifact


EXPERIMENTS: Dict[str, ExperimentRun] = {}
DEFAULT_METRICS = [
    "requirement_coverage",
    "e2e_pass_rate",
    "repair_resolution_rate",
    "contract_compliance_rate",
    "tool_invocation_count",
]


class ExperimentHarness:
    def create_experiment(self, definition: ExperimentDefinition) -> ExperimentRun:
        if not definition.created_at:
            definition.created_at = self._now()
        if definition.repetitions < 1:
            definition.repetitions = 1
        run = ExperimentRun(
            experiment_id=definition.experiment_id,
            definition=definition,
            status="CREATED",
            created_at=self._now(),
            limitations=[
                "Experiment harness records actual SEAM evaluation outputs only.",
                "Ablation configurations are metadata unless executed by an explicit isolated run configuration.",
                "No baseline values are fabricated.",
            ],
        )
        EXPERIMENTS[definition.experiment_id] = run
        event_bus.emit_sync("EXPERIMENT_CREATED", {
            "project_id": definition.experiment_id,
            "agent": "ExperimentHarness",
            "experiment_id": definition.experiment_id,
            "summary": f"Experiment created: {definition.name}",
        })
        return run

    def record_run(
        self,
        experiment_id: str,
        state: ProjectState,
        scenario_id: str,
        configuration_id: str,
        repetition_index: int = 1,
        baseline: Optional[Dict[str, Any]] = None,
        persist: bool = True,
    ) -> RunResult:
        experiment = self._get(experiment_id)
        scenario = self._scenario(experiment, scenario_id)
        configuration = self._configuration(experiment, configuration_id)
        run_id = f"{experiment_id}-{scenario_id}-{configuration_id}-{repetition_index}-{uuid.uuid4().hex[:8]}"
        if not state.project_id:
            state.project_id = run_id
        event_bus.emit_sync("EXPERIMENT_RUN_STARTED", {
            "project_id": state.project_id,
            "agent": "ExperimentHarness",
            "experiment_id": experiment_id,
            "run_id": run_id,
            "scenario_id": scenario_id,
            "configuration_id": configuration_id,
            "summary": f"Experiment run started: {run_id}",
        })
        try:
            evaluation = EvaluationEngine().evaluate(state, scenario_id=scenario_id, baseline=baseline, persist=persist)
            result = RunResult(
                run_id=run_id,
                experiment_id=experiment_id,
                scenario_id=scenario_id,
                configuration_id=configuration_id,
                repetition_index=repetition_index,
                project_id=state.project_id,
                status="COMPLETED",
                evaluation=evaluation,
                reproducibility=self._metadata(experiment_id, scenario, configuration, run_id, state),
            )
            result.data_quality = self.validate_run_result(result, state)
            if not result.data_quality.get("valid", False):
                result.status = "INVALID"
                result.errors.extend(result.data_quality.get("failures", []))
            experiment.runs.append(result)
            experiment.status = "RUNNING"
            event_bus.emit_sync("EXPERIMENT_RUN_COMPLETED", {
                "project_id": state.project_id,
                "agent": "ExperimentHarness",
                "experiment_id": experiment_id,
                "run_id": run_id,
                "status": result.status,
                "summary": f"Experiment run completed: {run_id}",
            })
        except Exception as exc:
            experiment.failed_runs += 1
            event_bus.emit_sync("EXPERIMENT_RUN_FAILED", {
                "project_id": state.project_id,
                "agent": "ExperimentHarness",
                "experiment_id": experiment_id,
                "run_id": run_id,
                "status": "FAILED",
                "error": str(exc),
                "summary": f"Experiment run failed: {run_id}",
            })
            raise
        if persist:
            self.persist(experiment, state)
        return result

    def dry_run(self, experiment_id: str) -> Dict[str, Any]:
        experiment = self._get(experiment_id)
        return {
            "experiment_id": experiment.experiment_id,
            "name": experiment.definition.name,
            "hypothesis": experiment.definition.hypothesis,
            "scenarios": [scenario.model_dump() for scenario in experiment.definition.scenarios],
            "configurations": [
                {
                    "configuration_id": config.configuration_id,
                    "mode": config.mode,
                    "disabled_capabilities": config.disabled_capabilities,
                    "flags": config.flags,
                    "status": self._configuration_status(config),
                }
                for config in experiment.definition.configurations
            ],
            "repetitions": experiment.definition.repetitions,
            "metrics": experiment.definition.metrics,
            "execution": "DRY_RUN_ONLY",
        }

    def execute_controlled_run(
        self,
        experiment_id: str,
        scenario_id: str,
        configuration_id: str,
        repetition_index: int = 1,
    ) -> RunResult:
        experiment = self._get(experiment_id)
        scenario = self._scenario(experiment, scenario_id)
        configuration = self._configuration(experiment, configuration_id)
        project_id = f"{experiment_id}-{scenario_id}-{configuration_id}-{repetition_index}-{uuid.uuid4().hex[:8]}"
        state = ProjectState(project_id=project_id, user_requirement=scenario.requirements, domain=scenario.domain)
        state.experiment_summary = {
            "experiment_id": experiment_id,
            "scenario_id": scenario_id,
            "configuration_id": configuration_id,
            "repetition_index": repetition_index,
            "configuration_flags": configuration.flags,
            "disabled_capabilities": configuration.disabled_capabilities,
        }
        try:
            from backend.api.projects import projects_db
            from backend.graph.workflow import create_workflow

            projects_db[project_id] = state
            workflow = create_workflow()
            current_state = state.model_dump()
            for output in workflow.stream(current_state):
                for _, snapshot in output.items():
                    current_state = snapshot
            state = ProjectState(**current_state)
            projects_db[project_id] = state
        except Exception as exc:
            event_bus.emit_sync("EXPERIMENT_RUN_FAILED", {
                "project_id": project_id,
                "agent": "ExperimentHarness",
                "experiment_id": experiment_id,
                "scenario_id": scenario_id,
                "configuration_id": configuration_id,
                "status": "FAILED",
                "error": str(exc),
                "summary": "Controlled experiment run failed during SEAM workflow execution.",
            })
            raise
        return self.record_run(experiment_id, state, scenario_id, configuration_id, repetition_index=repetition_index, persist=True)

    def compare(self, experiment_id: str, metrics: Optional[List[str]] = None, persist_state: Optional[ProjectState] = None) -> List[ExperimentComparison]:
        experiment = self._get(experiment_id)
        metrics = metrics or experiment.definition.metrics or DEFAULT_METRICS
        event_bus.emit_sync("EXPERIMENT_COMPARISON_STARTED", {
            "project_id": experiment_id,
            "agent": "ExperimentHarness",
            "experiment_id": experiment_id,
            "summary": "Experiment comparison started.",
        })
        comparisons: List[ExperimentComparison] = []
        for metric in metrics:
            values = []
            sources = []
            for result in experiment.runs:
                if result.status not in {"COMPLETED", "RECORDED"}:
                    continue
                value = self._metric_value(result, metric)
                if isinstance(value, (int, float)):
                    values.append(value)
                    sources.append(result.run_id)
            aggregate = self._aggregate(metric, values)
            comparisons.append(ExperimentComparison(
                experiment_id=experiment_id,
                metric=metric,
                values=values,
                aggregate=aggregate,
                data_sources=sources,
            ))
        experiment.comparisons = comparisons
        event_bus.emit_sync("EXPERIMENT_COMPARISON_COMPLETED", {
            "project_id": experiment_id,
            "agent": "ExperimentHarness",
            "experiment_id": experiment_id,
            "summary": "Experiment comparison completed.",
        })
        if persist_state:
            self.persist(experiment, persist_state)
        return comparisons

    def complete(self, experiment_id: str, persist_state: Optional[ProjectState] = None) -> ExperimentRun:
        experiment = self._get(experiment_id)
        if not experiment.comparisons:
            self.compare(experiment_id)
        experiment.status = "COMPLETED"
        experiment.completed_at = self._now()
        experiment.failed_runs = len([run for run in experiment.runs if run.status == "FAILED"])
        experiment.blocked_runs = len([run for run in experiment.runs if run.status == "BLOCKED"])
        event_bus.emit_sync("EXPERIMENT_COMPLETED", {
            "project_id": experiment_id,
            "agent": "ExperimentHarness",
            "experiment_id": experiment_id,
            "status": experiment.status,
            "summary": f"Experiment completed: {experiment.definition.name}",
        })
        if persist_state:
            self.persist(experiment, persist_state)
        return experiment

    def persist(self, experiment: ExperimentRun, state: ProjectState) -> None:
        state.experiment_summary = {
            "experiment_id": experiment.experiment_id,
            "name": experiment.definition.name,
            "scenario_count": len(experiment.definition.scenarios),
            "configuration_count": len(experiment.definition.configurations),
            "run_count": len(experiment.runs),
            "status": experiment.status,
            "metrics": self.dataset(experiment),
            "comparisons": [comparison.model_dump() for comparison in experiment.comparisons],
        }
        write_text_artifact(state, f"evaluation/experiments/{experiment.experiment_id}.json", experiment.model_dump_json(indent=2), "SUMMARY", "ExperimentHarness")
        write_text_artifact(state, "evaluation/datasets/experiment_results.json", json.dumps(self.dataset(experiment), indent=2), "SUMMARY", "ExperimentHarness")
        write_text_artifact(state, "evaluation/datasets/experiment_results.csv", self.dataset_csv(experiment), "SUMMARY", "ExperimentHarness")
        write_text_artifact(state, f"evaluation/datasets/{experiment.experiment_id}_results.json", json.dumps(self.dataset(experiment), indent=2), "SUMMARY", "ExperimentHarness")
        write_text_artifact(state, f"evaluation/datasets/{experiment.experiment_id}_results.csv", self.dataset_csv(experiment), "SUMMARY", "ExperimentHarness")
        write_text_artifact(state, f"evaluation/reports/{experiment.experiment_id}_SEAM_EXPERIMENT_REPORT.md", self.report(experiment), "SUMMARY", "ExperimentHarness")
        write_text_artifact(state, "evaluation/reports/scenario_catalog.md", self.scenario_catalog_report(), "SUMMARY", "ExperimentHarness")
        write_text_artifact(state, "evaluation/reports/experiment_catalog.md", self.experiment_catalog_report(), "SUMMARY", "ExperimentHarness")

    def dataset(self, experiment: ExperimentRun) -> List[Dict[str, Any]]:
        rows = []
        for result in experiment.runs:
            rows.append({
                "experiment_id": result.experiment_id,
                "run_id": result.run_id,
                "scenario_id": result.scenario_id,
                "configuration_id": result.configuration_id,
                "repetition_index": result.repetition_index,
                "project_id": result.project_id,
                "status": result.status,
                "configuration": result.configuration_id,
                "disabled_capabilities": self._configuration(experiment, result.configuration_id).disabled_capabilities,
                "requirements": self._scenario(experiment, result.scenario_id).requirements,
                "requirement_coverage": result.evaluation.requirements.requirement_coverage,
                "contract_compliance_rate": result.evaluation.contracts.contract_compliance_rate,
                "e2e_pass_rate": result.evaluation.e2e.e2e_pass_rate,
                "defect_count": result.evaluation.run.defect_count,
                "resolved_defects": result.evaluation.run.resolved_defect_count,
                "repair_iterations": result.evaluation.run.repair_iterations,
                "repair_resolution_rate": result.evaluation.repairs.repair_resolution_rate,
                "tool_invocation_count": result.evaluation.run.tool_invocation_count,
                "qa_status": result.evaluation.run.qa_status,
                "delivery_status": result.evaluation.run.delivery_status,
                "runtime_duration": result.evaluation.performance.breakdown_by_stage.get("Runtime", "NOT_APPLICABLE"),
                "workflow_duration": result.evaluation.performance.total_workflow_duration_ms,
                "domain_detected": result.evaluation.domain_rag.domain_detected,
                "evaluation_id": result.evaluation.run.evaluation_id,
                "git_commit": result.reproducibility.git_commit,
                "model": result.reproducibility.model_name,
                "seed": result.reproducibility.seed,
                "knowledge_version": result.reproducibility.knowledge_base_version,
                "data_quality_valid": result.data_quality.get("valid", "NOT_AVAILABLE"),
            })
        return rows

    def dataset_csv(self, experiment: ExperimentRun) -> str:
        rows = self.dataset(experiment)
        if not rows:
            return ""
        buffer = StringIO()
        writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
        return buffer.getvalue()

    def report(self, experiment: ExperimentRun) -> str:
        rows = self.dataset(experiment)
        comparison_lines = []
        for comparison in experiment.comparisons:
            aggregate = comparison.aggregate
            comparison_lines.append(f"- {comparison.metric}: count={aggregate.count}, mean={aggregate.mean}, median={aggregate.median}, min={aggregate.minimum}, max={aggregate.maximum}, stdev={aggregate.standard_deviation}")
        return f"""# SEAM Experiment Report

## Experiment Definition

ID: {experiment.experiment_id}
Name: {experiment.definition.name}
Version: {experiment.definition.version}

## Hypothesis

{experiment.definition.hypothesis or 'No conclusion encoded in the experiment definition.'}

## Scenarios

{chr(10).join(f'- {scenario.scenario_id}: {scenario.name} ({scenario.domain or "domain not specified"})' for scenario in experiment.definition.scenarios) or 'None'}

## Configurations

{chr(10).join(f'- {config.configuration_id}: {config.mode}; disabled={", ".join(config.disabled_capabilities) or "none"}' for config in experiment.definition.configurations) or 'None'}

## Number Of Runs

{len(experiment.runs)}

## Environment

Environment metadata is captured per RunResult. Secrets and hidden reasoning are excluded.

## Metrics

{', '.join(experiment.definition.metrics or DEFAULT_METRICS)}

## Raw Observations

{json.dumps(rows, indent=2)}

## Aggregated Observations

{chr(10).join(comparison_lines) if comparison_lines else 'NOT_APPLICABLE'}

## Comparison

{self._comparison_table(experiment)}

## Failed/Blocked Runs

{self._failed_run_lines(experiment)}

## Data-Quality Checks

{self._quality_lines(experiment)}

## Baseline Observations

Baselines are included only when recorded baseline runs or baseline values are supplied.

## Ablation Observations

Ablation configurations are explicitly recorded through `disabled_capabilities`. No architecture is silently modified.

## Limitations

{chr(10).join(f'- {item}' for item in experiment.limitations)}

## Reproducibility Metadata

Each RunResult records git commit, model configuration, environment, seed, and nondeterminism limitations when available.

This report states measurements only. It does not claim superiority, rankings, or causal conclusions.
"""

    def validate_run_result(self, result: RunResult, state: ProjectState) -> Dict[str, Any]:
        failures = []
        if not result.experiment_id:
            failures.append("missing experiment_id")
        if not result.scenario_id:
            failures.append("missing scenario_id")
        if not result.configuration_id:
            failures.append("missing configuration_id")
        if not result.run_id:
            failures.append("missing run_id")
        if not result.evaluation.run.evaluation_id:
            failures.append("missing evaluation_id")
        if result.project_id != state.project_id:
            failures.append("ProjectState project_id does not match RunResult project_id")
        if result.evaluation.run.project_id != state.project_id:
            failures.append("EvaluationRun project_id does not match ProjectState")
        if result.evaluation.run.scenario_id != result.scenario_id:
            failures.append("EvaluationRun scenario_id does not match RunResult")
        if not result.reproducibility.model_name:
            failures.append("missing model name")
        if result.reproducibility.experiment_id != result.experiment_id:
            failures.append("reproducibility experiment_id mismatch")
        if result.reproducibility.run_id != result.run_id:
            failures.append("reproducibility run_id mismatch")
        return {
            "valid": not failures,
            "failures": failures,
            "project_id": state.project_id,
            "evaluation_id": result.evaluation.run.evaluation_id,
        }

    def scenario_catalog_report(self) -> str:
        scenarios = scenario_catalog().values()
        lines = []
        for scenario in scenarios:
            lines.append(f"""## {scenario.scenario_id}: {scenario.name}

- Domain: {scenario.domain}
- Complexity: {scenario.complexity}
- Rationale: {scenario.complexity_rationale}
- Version: {scenario.version}
- Metrics: {', '.join(scenario.evaluation_metrics)}
- Required features: {', '.join(scenario.required_features)}
- Expected artifacts: {', '.join(scenario.expected_artifacts)}
- Validation layers: {', '.join(scenario.expected_validation_layers)}
""")
        return "# SEAM Research Scenario Catalog\n\n" + "\n".join(lines)

    def experiment_catalog_report(self) -> str:
        experiments = experiment_catalog().values()
        lines = []
        for experiment in experiments:
            lines.append(f"""## {experiment.experiment_id}: {experiment.name}

- Objective: {experiment.description}
- Hypothesis: {experiment.hypothesis}
- Scenario: {experiment.scenarios[0].scenario_id if experiment.scenarios else 'NOT_CONFIGURED'}
- Configurations: {', '.join(config.configuration_id for config in experiment.configurations)}
- Repetitions: {experiment.repetitions}
- Metrics: {', '.join(experiment.metrics)}
- Reproducibility: scenario seed, configuration flags, git/model/environment metadata are recorded per run.
- Limitations: hypotheses are not marked as proven by catalog definitions.
""")
        return "# SEAM Experiment Catalog\n\n" + "\n".join(lines)

    def experiment_matrix(self, experiment_id: str) -> Dict[str, Any]:
        experiment = self._get(experiment_id)
        matrix = {
            "experiment_id": experiment_id,
            "scenarios": {},
        }
        for scenario in experiment.definition.scenarios:
            matrix["scenarios"][scenario.scenario_id] = {"configurations": {}}
            for configuration in experiment.definition.configurations:
                runs = [
                    run.model_dump()
                    for run in experiment.runs
                    if run.scenario_id == scenario.scenario_id and run.configuration_id == configuration.configuration_id
                ]
                matrix["scenarios"][scenario.scenario_id]["configurations"][configuration.configuration_id] = {
                    "expected_repetitions": experiment.definition.repetitions,
                    "completed_runs": len([run for run in runs if run.get("status") == "COMPLETED"]),
                    "runs": runs,
                }
        return matrix

    def _configuration_status(self, configuration: RunConfiguration) -> str:
        implemented = {"SEAM_FULL", "ABLATION_NO_DOMAIN_RAG", "ABLATION_NO_AUTONOMOUS_REPAIR", "ABLATION_NO_CONTRACT_INTELLIGENCE"}
        if configuration.configuration_id == "BASELINE":
            return "NOT_IMPLEMENTED" if not configuration.baseline_source else "AVAILABLE"
        return "OPERATIONAL" if configuration.configuration_id in implemented else "NOT_IMPLEMENTED"

    def _comparison_table(self, experiment: ExperimentRun) -> str:
        if not experiment.comparisons:
            return "NOT_AVAILABLE"
        lines = ["| metric | values | data sources |", "| --- | --- | --- |"]
        for comparison in experiment.comparisons:
            lines.append(f"| {comparison.metric} | {comparison.values} | {len(comparison.data_sources)} run(s) |")
        return "\n".join(lines)

    def _failed_run_lines(self, experiment: ExperimentRun) -> str:
        runs = [run for run in experiment.runs if run.status in {"FAILED", "BLOCKED", "CANCELLED", "NOT_CONFIGURED", "INVALID"}]
        if not runs:
            return "None"
        return "\n".join(f"- {run.run_id}: {run.status}; {', '.join(run.errors) if run.errors else 'no error text'}" for run in runs)

    def _quality_lines(self, experiment: ExperimentRun) -> str:
        if not experiment.runs:
            return "No runs recorded."
        return "\n".join(
            f"- {run.run_id}: {'VALID' if run.data_quality.get('valid') else 'INVALID'}"
            for run in experiment.runs
        )

    def _metadata(self, experiment_id: str, scenario: ScenarioDefinition, configuration: RunConfiguration, run_id: str, state: ProjectState) -> ReproducibilityMetadata:
        from backend.config import SEAM_LLM_MODEL, SEAM_CODING_MODEL, SEAM_PLANNING_MODEL, SEAM_QA_MODEL
        return ReproducibilityMetadata(
            experiment_id=experiment_id,
            scenario_id=scenario.scenario_id,
            run_id=run_id,
            timestamp=self._now(),
            project_version="local-worktree",
            git_commit=self._git_commit(),
            model_name=SEAM_LLM_MODEL,
            model_configuration={
                "coding": SEAM_CODING_MODEL,
                "planning": SEAM_PLANNING_MODEL,
                "qa": SEAM_QA_MODEL,
            },
            knowledge_base_version="local",
            repository_context_version=str(state.github_status or "NOT_AVAILABLE"),
            configuration_flags=configuration.flags,
            operating_environment={
                "platform": platform.platform(),
                "machine": platform.machine(),
            },
            python_version=sys.version.split()[0],
            node_version=self._node_version(),
            package_versions={"pydantic": self._package_version("pydantic")},
            seed=scenario.seed,
            nondeterminism_limitations=[
                "LLM generation and external tool availability may be nondeterministic unless controlled by the run configuration.",
            ],
        )

    def _aggregate(self, metric: str, values: List[float]) -> AggregateMetric:
        if not values:
            return AggregateMetric(metric=metric)
        stdev: Any = "NOT_APPLICABLE"
        if len(values) > 1:
            stdev = round(statistics.stdev(values), 4)
        return AggregateMetric(
            metric=metric,
            count=len(values),
            mean=round(statistics.mean(values), 4),
            median=round(statistics.median(values), 4),
            minimum=min(values),
            maximum=max(values),
            standard_deviation=stdev,
        )

    def _metric_value(self, result: RunResult, metric: str) -> Any:
        lookup = {
            "requirement_coverage": result.evaluation.requirements.requirement_coverage,
            "e2e_pass_rate": result.evaluation.e2e.e2e_pass_rate,
            "repair_resolution_rate": result.evaluation.repairs.repair_resolution_rate,
            "contract_compliance_rate": result.evaluation.contracts.contract_compliance_rate,
            "tool_invocation_count": result.evaluation.run.tool_invocation_count,
            "domain_retrieval_count": result.evaluation.domain_rag.domain_retrieval_count,
            "qa_defect_count": result.evaluation.qa.qa_defect_count,
            "defect_count": result.evaluation.run.defect_count,
            "repair_count": result.evaluation.repairs.repair_plans,
            "targeted_verification_pass_rate": result.evaluation.repairs.targeted_verification_pass_rate,
            "regression_pass_rate": result.evaluation.repairs.regression_pass_rate,
            "contract_issues": result.evaluation.contracts.static_contract_issues,
            "runtime_failures": 1 if result.evaluation.qa.runtime_contract_result == "FAIL" else 0,
            "e2e_failures": result.evaluation.e2e.scenarios_failed,
            "repair_iterations": result.evaluation.run.repair_iterations,
        }
        return lookup.get(metric, "NOT_APPLICABLE")

    def _scenario(self, experiment: ExperimentRun, scenario_id: str) -> ScenarioDefinition:
        for scenario in experiment.definition.scenarios:
            if scenario.scenario_id == scenario_id:
                return scenario
        raise ValueError(f"Unknown scenario: {scenario_id}")

    def _configuration(self, experiment: ExperimentRun, configuration_id: str) -> RunConfiguration:
        for configuration in experiment.definition.configurations:
            if configuration.configuration_id == configuration_id:
                return configuration
        raise ValueError(f"Unknown configuration: {configuration_id}")

    def _get(self, experiment_id: str) -> ExperimentRun:
        if experiment_id not in EXPERIMENTS:
            raise ValueError(f"Experiment not found: {experiment_id}")
        return EXPERIMENTS[experiment_id]

    def _git_commit(self) -> Optional[str]:
        try:
            proc = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=5)
            return proc.stdout.strip() if proc.returncode == 0 else None
        except Exception:
            return None

    def _node_version(self) -> str:
        try:
            proc = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=5)
            return proc.stdout.strip() if proc.returncode == 0 else "NOT_AVAILABLE"
        except Exception:
            return "NOT_AVAILABLE"

    def _package_version(self, name: str) -> str:
        try:
            from importlib.metadata import version
            return version(name)
        except Exception:
            return "NOT_AVAILABLE"

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()
