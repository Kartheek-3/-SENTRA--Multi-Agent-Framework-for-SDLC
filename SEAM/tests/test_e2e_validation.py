from langchain_core.language_models.fake_chat_models import FakeListChatModel

from backend.agents.qa_agent import QAAgent
from backend.models.analysis import AnalysisResult, Requirement
from backend.models.contracts import RuntimeContractResult
from backend.models.planning import (
    FrontendArchitecturePlan,
    FrontendPagePlan,
    FrontendTraceabilityItem,
)
from backend.models.state import ProjectState


class MockModelRouter:
    def __init__(self):
        self.fake_llm = FakeListChatModel(responses=["{}"])

    def get_model(self):
        return self.fake_llm


def _state():
    return ProjectState(
        project_id="e2e",
        user_requirement="User can log in and view dashboard",
        structured_requirements=AnalysisResult(
            project_summary="Login app",
            application_domain="auth",
            functional_requirements=[Requirement(id="FR-001", description="User can log in and view dashboard")],
            non_functional_requirements=[],
            actors=["User"],
            entities=["User"],
            constraints=[],
            assumptions=[],
            risks=[],
            technical_considerations=[],
            ambiguities=[],
            recommended_capabilities=[],
        ),
        frontend_architecture_plan=FrontendArchitecturePlan(
            framework="React",
            language="TypeScript",
            build_system="Vite",
            pages=[FrontendPagePlan(name="LoginPage", route="/login", components=["LoginForm"])],
            traceability=[
                FrontendTraceabilityItem(
                    requirement_id="FR-001",
                    requirement="User can log in and view dashboard",
                    page="LoginPage",
                    component="LoginForm",
                    service="AuthService",
                    api_endpoint="POST /api/auth/login",
                    file="src/pages/LoginPage.tsx",
                    validation="E2E login workflow",
                )
            ],
        ),
    )


def test_e2e_scenario_generation_links_requirement_frontend_and_api():
    agent = QAAgent(MockModelRouter())

    scenarios = agent._generate_e2e_scenarios(_state())

    assert len(scenarios) == 1
    assert scenarios[0].scenario_id == "E2E-001"
    assert scenarios[0].source_requirement.startswith("FR-001")
    assert scenarios[0].frontend_page == "LoginPage"
    assert scenarios[0].api_endpoint == "POST /api/auth/login"
    assert [step.action for step in scenarios[0].steps] == ["OPEN", "ASSERT_VISIBLE", "ASSERT_STATUS", "SCREENSHOT"]


def test_e2e_localization_uses_runtime_contract_failure_as_backend_evidence():
    state = _state()
    state.runtime_contract_results = [
        RuntimeContractResult(
            contract_id="POST /api/auth/login",
            endpoint="/api/auth/login",
            method="POST",
            actual_status=500,
            status="FAIL",
        )
    ]
    scenario = QAAgent(MockModelRouter())._generate_e2e_scenarios(state)[0]

    defect = QAAgent(MockModelRouter())._localize_e2e_defect(state, scenario, type("R", (), {"stdout": "", "stderr": "", "structured_data": {}})(), "FAIL")[0]

    assert defect.layer == "BACKEND"
    assert "POST /api/auth/login" in defect.endpoint
    assert defect.confidence == "MEDIUM"


def test_e2e_localization_marks_missing_playwright_as_configuration():
    state = _state()
    scenario = QAAgent(MockModelRouter())._generate_e2e_scenarios(state)[0]
    result = type("R", (), {"stdout": "", "stderr": "Playwright is not configured", "structured_data": {"status": "NOT_CONFIGURED"}})()

    defect = QAAgent(MockModelRouter())._localize_e2e_defect(state, scenario, result, "NOT_CONFIGURED")[0]

    assert defect.layer == "CONFIGURATION"
    assert "Playwright" in defect.issue

