import os
import shutil
import uuid

import pytest

from backend.api.projects import projects_db
from backend.evaluation import EvaluationEngine
from backend.events import event_bus
from backend.models.analysis import AnalysisResult, Requirement
from backend.models.contracts import ContractIssue, E2EResult, DefectLocation, RepairPlan, RepairResult, TargetedVerification, RegressionResult
from backend.models.delivery import ReleaseReadiness
from backend.models.planning import ArchitectureComponent, ProjectPlan, SystemDesign, Task
from backend.models.state import ProjectState
from backend.utils import slugify


def _state(project_id: str = "Evaluation Test") -> ProjectState:
    state = ProjectState(project_id=project_id, user_requirement="Build a small CRUD app", domain="evaluation-test")
    state.structured_requirements = AnalysisResult(
        project_summary="summary",
        application_domain="demo",
        functional_requirements=[
            Requirement(id="FR-001", description="Create item"),
            Requirement(id="FR-002", description="List items"),
        ],
        non_functional_requirements=[],
        actors=[],
        entities=[],
        constraints=["Use domain validation"],
        assumptions=[],
        risks=[],
        technical_considerations=[],
        ambiguities=[],
        recommended_capabilities=[],
    )
    state.project_plan = ProjectPlan(
        project_overview="CRUD app",
        system_design=SystemDesign(
            architecture_style="Full-stack web",
            components=[ArchitectureComponent(component_id="C1", name="API", responsibility="REST")],
            data_flow="",
            database_schema=[],
            api_endpoints=[],
            technology_stack=["FastAPI", "React"],
            security_considerations=[],
        ),
        tasks=[],
    )
    task = Task(task_id="TASK-001", title="CRUD", description="Implement CRUD", related_requirements=["FR-001", "FR-002"])
    task.status = "completed"
    task.result = {"qa_result": {"passed": True}, "files": [{"path": "backend/main.py"}]}
    state.tasks[task.task_id] = task
    state.project_plan.tasks.append(task)
    state.completed_tasks.append(task.task_id)
    state.delivery_result = {"status": "deployed", "package_created": True, "errors": []}
    state.release_readiness = ReleaseReadiness(status="READY", qa_status="PASS", security_status="PASS")
    return state


@pytest.fixture(autouse=True)
def clean_eval_project():
    yield
    for name in ["evaluation-test"]:
        path = os.path.join("generated_projects", slugify(name))
        if os.path.exists(path):
            shutil.rmtree(path)


def test_evaluation_engine_computes_core_metrics_without_subjective_scores():
    state = _state()
    state.e2e_results.append(E2EResult(scenario_id="E2E-1", status="PASS", duration_ms=120))
    state.defect_locations.append(DefectLocation(layer="FRONTEND", confidence="HIGH", issue="Button failed"))
    state.repair_plans.append(RepairPlan(repair_id="RP-1", status="RESOLVED"))
    state.repair_results.append(RepairResult(repair_id="RP-1", status="SUCCESS", defect_addressed=True))
    state.targeted_verifications.append(TargetedVerification(repair_id="RP-1", validation_type="E2E", status="PASS"))
    state.regression_results.append(RegressionResult(repair_id="RP-1", status="PASS"))

    summary = EvaluationEngine().evaluate(state, persist=False)

    assert summary.requirements.requirement_coverage == 1.0
    assert summary.e2e.e2e_pass_rate == 1.0
    assert summary.defects.frontend_defects == 1
    assert summary.repairs.repair_resolution_rate == 1.0
    dumped = summary.model_dump_json().lower()
    assert "winner" not in dumped
    assert "best" not in dumped


def test_evaluation_engine_reports_not_applicable_for_missing_denominators():
    state = ProjectState(project_id="No Denominator", user_requirement="empty")

    summary = EvaluationEngine().evaluate(state, persist=False)

    assert summary.requirements.requirement_coverage == "NOT_APPLICABLE"
    assert summary.e2e.e2e_pass_rate == "NOT_APPLICABLE"
    assert summary.contracts.contract_compliance_rate == "NOT_APPLICABLE"


def test_evaluation_engine_uses_eventstore_tool_metrics():
    state = _state(f"Evaluation Event Test {uuid.uuid4()}")
    projects_db[state.project_id] = state
    event_bus.emit_sync("TOOL_REQUESTED", {"project_id": state.project_id, "agent": "QAAgent", "tool_name": "pytest_runner"})
    event_bus.emit_sync("TOOL_COMPLETED", {"project_id": state.project_id, "agent": "QAAgent", "tool_name": "pytest_runner", "duration_ms": 25})
    event_bus.emit_sync("AGENT_STARTED", {"project_id": state.project_id, "agent": "QAAgent"})
    event_bus.emit_sync("AGENT_COMPLETED", {"project_id": state.project_id, "agent": "QAAgent"})

    summary = EvaluationEngine().evaluate(state, persist=False)

    testing = next(tool for tool in summary.tools if tool.category == "Testing")
    assert testing.tool_invocation_count == 1
    assert testing.success_rate == 1.0
    qa_agent = next(agent for agent in summary.agents if agent.agent == "QAAgent")
    assert qa_agent.invocation_count == 1


def test_evaluation_engine_persists_json_and_markdown_artifacts():
    state = _state()
    projects_db[state.project_id] = state
    os.makedirs(os.path.join("generated_projects", state.project_name), exist_ok=True)

    EvaluationEngine().evaluate(state, persist=True)

    root = os.path.join("generated_projects", state.project_name, "evaluation")
    assert os.path.exists(os.path.join(root, "evaluation_results.json"))
    assert os.path.exists(os.path.join(root, "SEAM_EVALUATION_REPORT.md"))
    assert state.evaluation_summary is not None


def test_evaluation_engine_compares_only_recorded_baseline_values():
    state = _state()

    summary = EvaluationEngine().evaluate(state, baseline={"requirement_coverage": 0.5, "missing_metric": 1}, persist=False)

    assert len(summary.baseline_comparison) == 1
    comparison = summary.baseline_comparison[0]
    assert comparison.metric == "requirement_coverage"
    assert comparison.absolute_difference == 0.5
