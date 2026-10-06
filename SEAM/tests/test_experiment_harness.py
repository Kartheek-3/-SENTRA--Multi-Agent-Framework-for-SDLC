import os
import shutil
import uuid

import pytest

from backend.api.projects import projects_db
from backend.evaluation.experiment_harness import EXPERIMENTS, ExperimentHarness
from backend.events import event_bus
from backend.models.analysis import AnalysisResult, Requirement
from backend.models.evaluation import ExperimentDefinition, RunConfiguration, ScenarioDefinition
from backend.models.planning import ArchitectureComponent, ProjectPlan, SystemDesign, Task
from backend.models.state import ProjectState


def _definition(experiment_id: str) -> ExperimentDefinition:
    return ExperimentDefinition(
        experiment_id=experiment_id,
        name="Domain RAG Study",
        description="Recorded experiment definition",
        hypothesis="No conclusion is encoded.",
        scenarios=[
            ScenarioDefinition(
                scenario_id="SCENARIO_05",
                name="Domain-aware application",
                domain="healthcare",
                requirements="Build a healthcare appointment app",
                expected_capabilities=["appointments", "validation"],
                seed=42,
                evaluation_metrics=["requirement_coverage", "e2e_pass_rate"],
            )
        ],
        configurations=[
            RunConfiguration(configuration_id="SEAM_FULL", mode="SEAM_FULL"),
            RunConfiguration(configuration_id="SEAM_NO_DOMAIN_RAG", mode="ABLATION", disabled_capabilities=["domain-aware RAG"]),
            RunConfiguration(configuration_id="BASELINE", mode="BASELINE", baseline_source="recorded", baseline_version="1", baseline_provenance="test fixture"),
        ],
        repetitions=2,
        metrics=["requirement_coverage", "e2e_pass_rate", "tool_invocation_count"],
    )


def _state(project_id: str, with_requirements: bool = True) -> ProjectState:
    state = ProjectState(project_id=project_id, user_requirement="Build a healthcare appointment app", domain=f"project-{project_id}")
    if with_requirements:
        state.structured_requirements = AnalysisResult(
            project_summary="summary",
            application_domain="healthcare",
            functional_requirements=[Requirement(id="FR-001", description="Book appointment")],
            non_functional_requirements=[],
            actors=[],
            entities=[],
            constraints=[],
            assumptions=[],
            risks=[],
            technical_considerations=[],
            ambiguities=[],
            recommended_capabilities=[],
        )
        state.project_plan = ProjectPlan(
            project_overview="Appointment app",
            system_design=SystemDesign(
                architecture_style="Full-stack",
                components=[ArchitectureComponent(component_id="C1", name="API", responsibility="REST")],
                data_flow="",
                database_schema=[],
                api_endpoints=[],
                technology_stack=["FastAPI"],
                security_considerations=[],
            ),
            tasks=[],
        )
        task = Task(task_id="TASK-001", title="Appointment", description="Implement", related_requirements=["FR-001"])
        task.status = "completed"
        task.result = {"qa_result": {"passed": True}}
        state.tasks[task.task_id] = task
        state.project_plan.tasks.append(task)
        state.completed_tasks.append(task.task_id)
        state.delivery_result = {"status": "deployed", "package_created": True, "errors": []}
    return state


@pytest.fixture(autouse=True)
def clear_experiments():
    EXPERIMENTS.clear()
    yield
    EXPERIMENTS.clear()
    for name in os.listdir("generated_projects") if os.path.exists("generated_projects") else []:
        if name.startswith("project-exp-"):
            shutil.rmtree(os.path.join("generated_projects", name), ignore_errors=True)


def test_experiment_and_scenario_models_preserve_research_metadata():
    definition = _definition("exp-model")

    assert definition.scenarios[0].scenario_id == "SCENARIO_05"
    assert definition.scenarios[0].seed == 42
    assert definition.configurations[1].disabled_capabilities == ["domain-aware RAG"]
    assert definition.configurations[2].baseline_provenance == "test fixture"


def test_repeated_runs_are_isolated_by_project_and_run_id():
    harness = ExperimentHarness()
    experiment = harness.create_experiment(_definition("exp-repeat"))
    state_1 = _state(f"exp-{uuid.uuid4().hex}")
    state_2 = _state(f"exp-{uuid.uuid4().hex}")

    run_1 = harness.record_run(experiment.experiment_id, state_1, "SCENARIO_05", "SEAM_FULL", repetition_index=1, persist=False)
    run_2 = harness.record_run(experiment.experiment_id, state_2, "SCENARIO_05", "SEAM_FULL", repetition_index=2, persist=False)

    assert run_1.run_id != run_2.run_id
    assert run_1.project_id != run_2.project_id
    assert len(experiment.runs) == 2


def test_event_isolation_uses_current_project_only():
    harness = ExperimentHarness()
    experiment = harness.create_experiment(_definition("exp-events"))
    other = _state(f"exp-{uuid.uuid4().hex}")
    current = _state(f"exp-{uuid.uuid4().hex}")
    projects_db[other.project_id] = other
    projects_db[current.project_id] = current
    event_bus.emit_sync("TOOL_REQUESTED", {"project_id": other.project_id, "tool_name": "pytest_runner"})
    event_bus.emit_sync("TOOL_REQUESTED", {"project_id": current.project_id, "tool_name": "pytest_runner"})

    result = harness.record_run(experiment.experiment_id, current, "SCENARIO_05", "SEAM_FULL", persist=False)

    assert result.evaluation.run.tool_invocation_count == 1


def test_aggregation_dataset_and_report_generation():
    harness = ExperimentHarness()
    experiment = harness.create_experiment(_definition("exp-aggregate"))
    harness.record_run(experiment.experiment_id, _state(f"exp-{uuid.uuid4().hex}"), "SCENARIO_05", "SEAM_FULL", repetition_index=1, persist=False)
    harness.record_run(experiment.experiment_id, _state(f"exp-{uuid.uuid4().hex}"), "SCENARIO_05", "SEAM_FULL", repetition_index=2, persist=False)

    comparisons = harness.compare(experiment.experiment_id)
    dataset = harness.dataset(experiment)
    report = harness.report(experiment)

    assert comparisons[0].aggregate.count == 2
    assert dataset[0]["experiment_id"] == "exp-aggregate"
    assert "SEAM is superior" not in report
    assert "Raw Observations" in report


def test_persist_exports_dataset_and_report_artifacts():
    harness = ExperimentHarness()
    experiment = harness.create_experiment(_definition("exp-persist"))
    state = _state(f"exp-{uuid.uuid4().hex}")
    projects_db[state.project_id] = state
    os.makedirs(os.path.join("generated_projects", state.project_name), exist_ok=True)
    harness.record_run(experiment.experiment_id, state, "SCENARIO_05", "SEAM_FULL", persist=False)
    harness.compare(experiment.experiment_id)

    harness.persist(experiment, state)

    root = os.path.join("generated_projects", state.project_name, "evaluation")
    assert os.path.exists(os.path.join(root, "datasets", "experiment_results.json"))
    assert os.path.exists(os.path.join(root, "datasets", "experiment_results.csv"))
    assert os.path.exists(os.path.join(root, "reports", "exp-persist_SEAM_EXPERIMENT_REPORT.md"))
    assert state.experiment_summary["run_count"] == 1


def test_missing_denominators_remain_not_applicable():
    harness = ExperimentHarness()
    experiment = harness.create_experiment(_definition("exp-missing"))
    result = harness.record_run(experiment.experiment_id, _state(f"exp-{uuid.uuid4().hex}", with_requirements=False), "SCENARIO_05", "SEAM_FULL", persist=False)

    assert result.evaluation.requirements.requirement_coverage == "NOT_APPLICABLE"
    assert harness.compare(experiment.experiment_id)[0].aggregate.count == 0
