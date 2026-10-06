from langchain_core.language_models.fake_chat_models import FakeListChatModel

from backend.agents.qa_agent import QAAgent
from backend.models.contracts import DefectLocation, RepairResult
from backend.models.qa import QAResult
from backend.models.state import ProjectState


class MockModelRouter:
    def __init__(self):
        self.fake_llm = FakeListChatModel(responses=["{}"])

    def get_model(self):
        return self.fake_llm


def test_repair_plan_created_from_backend_defect():
    state = ProjectState(project_id="repair", user_requirement="Login")
    state.defect_locations.append(
        DefectLocation(
            layer="BACKEND",
            confidence="MEDIUM",
            file="backend/routes/auth.py",
            endpoint="POST /api/auth/login",
            issue="Login returned HTTP 500",
            suggested_investigation="Check auth route",
        )
    )
    qa_result = QAResult(task_id="T-1", status="failed", passed=False)

    QAAgent(MockModelRouter())._plan_repairs_from_defects(state, "T-1", qa_result)

    assert len(state.repair_plans) == 1
    plan = state.repair_plans[0]
    assert plan.status == "PENDING"
    assert plan.affected_files == ["backend/routes/auth.py"]
    assert plan.affected_endpoint == "POST /api/auth/login"
    assert "endpoint implementation" in plan.repair_strategy


def test_ambiguous_defect_becomes_needs_review():
    state = ProjectState(project_id="repair", user_requirement="Login")
    state.defect_locations.append(DefectLocation(layer="UNKNOWN", confidence="LOW", issue="Unknown failure"))
    qa_result = QAResult(task_id="T-1", status="failed", passed=False)

    QAAgent(MockModelRouter())._plan_repairs_from_defects(state, "T-1", qa_result)

    assert state.repair_plans[0].status == "NEEDS_REVIEW"


def test_repair_verification_passes_when_matching_defect_is_absent():
    state = ProjectState(project_id="repair", user_requirement="Login")
    state.defect_locations = []
    state.repair_results.append(
        RepairResult(
            repair_id="REPAIR-001",
            status="SUCCESS",
            modified_files=["backend/routes/auth.py"],
            defect_addressed=True,
        )
    )
    qa_result = QAResult(task_id="T-1", status="passed", passed=True)

    QAAgent(MockModelRouter())._run_repair_verification(state, "T-1", qa_result)

    assert state.targeted_verifications[0].status == "PASS"
    assert state.regression_results[0].status == "PASS"

