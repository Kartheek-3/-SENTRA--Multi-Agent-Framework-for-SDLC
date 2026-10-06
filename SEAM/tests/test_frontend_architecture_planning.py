from langchain_core.language_models.fake_chat_models import FakeListChatModel

from backend.agents.planning_agent import PlanningAgent
from backend.models.analysis import AnalysisResult, Requirement
from backend.models.planning import APIEndpoint, ProjectPlan, SystemDesign
from backend.models.state import ProjectState


class MockModelRouter:
    def __init__(self):
        self.fake_llm = FakeListChatModel(responses=["{}"])

    def get_model(self):
        return self.fake_llm


def _analysis():
    return AnalysisResult(
        project_summary="Travel booking",
        application_domain="travel",
        functional_requirements=[
            Requirement(id="FR-001", description="Users can login"),
            Requirement(id="FR-002", description="Users can search destinations with filters"),
            Requirement(id="FR-003", description="Users can submit a booking form"),
            Requirement(id="FR-004", description="Users can view a responsive dashboard"),
        ],
        non_functional_requirements=[
            Requirement(id="NFR-001", description="The frontend must be responsive and accessible"),
        ],
        actors=["Traveler"],
        entities=["User", "Destination", "Booking"],
        constraints=[],
        assumptions=[],
        risks=[],
        technical_considerations=["React TypeScript frontend"],
        ambiguities=[],
        recommended_capabilities=[],
    )


def _plan():
    return ProjectPlan(
        project_overview="Travel booking",
        system_design=SystemDesign(
            architecture_style="Client-server",
            technology_stack=["React", "TypeScript", "FastAPI"],
            api_endpoints=[
                APIEndpoint(method="POST", path="/api/auth/login", purpose="Login users", authentication_required=False),
                APIEndpoint(method="GET", path="/api/search", purpose="Search destinations", authentication_required=False),
                APIEndpoint(method="POST", path="/api/bookings", purpose="Create booking", authentication_required=True),
                APIEndpoint(method="GET", path="/api/dashboard", purpose="Dashboard summary", authentication_required=True),
            ],
        ),
    )


def test_frontend_architecture_uses_detected_capabilities_and_api_contracts():
    state = ProjectState(
        project_id="frontend-plan",
        user_requirement="Build a travel booking UI with login, search, booking form, and dashboard.",
        structured_requirements=_analysis(),
        project_plan=_plan(),
        system_design=_plan().system_design,
        frontend_capabilities={
            "package_json": True,
            "framework": "React",
            "language": "TypeScript",
            "build_system": "Vite",
            "typecheck_available": True,
            "lint_available": True,
            "frontend_test_framework": "vitest",
            "playwright_available": True,
            "accessibility_available": True,
        },
    )

    frontend_plan = PlanningAgent(MockModelRouter())._build_frontend_architecture_plan(state)

    assert frontend_plan.framework == "React"
    assert frontend_plan.language == "TypeScript"
    assert frontend_plan.build_system == "Vite"
    assert {route.path for route in frontend_plan.routes} >= {"/login", "/search", "/booking", "/dashboard"}
    assert {page.name for page in frontend_plan.pages} >= {"LoginPage", "SearchPage", "BookingPage", "DashboardPage"}
    assert any(item.api_endpoint == "POST /api/auth/login" for item in frontend_plan.traceability)
    assert any(file.path == "src/pages/LoginPage.tsx" for file in frontend_plan.file_structure)
    assert any("vitest" in item for item in frontend_plan.testing_strategy)


def test_frontend_architecture_does_not_guess_react_when_framework_unknown():
    state = ProjectState(
        project_id="unknown-frontend",
        user_requirement="Build a UI with an add expense form and view expenses list.",
        structured_requirements=AnalysisResult(
            project_summary="Expense tracker",
            application_domain="finance",
            functional_requirements=[
                Requirement(id="FR-001", description="Users can add expenses"),
                Requirement(id="FR-002", description="Users can view expenses"),
            ],
            non_functional_requirements=[],
            actors=["User"],
            entities=["Expense"],
            constraints=[],
            assumptions=[],
            risks=[],
            technical_considerations=[],
            ambiguities=[],
            recommended_capabilities=[],
        ),
        project_plan=ProjectPlan(
            project_overview="Expense tracker",
            system_design=SystemDesign(
                architecture_style="Client-server",
                api_endpoints=[APIEndpoint(method="GET", path="/api/expenses", purpose="View expenses")],
            ),
        ),
        frontend_capabilities={"package_json": False, "framework": "UNKNOWN", "language": "UNKNOWN", "build_system": "UNKNOWN"},
    )

    frontend_plan = PlanningAgent(MockModelRouter())._build_frontend_architecture_plan(state)

    assert frontend_plan.framework == "UNKNOWN"
    assert frontend_plan.build_system == "UNKNOWN"
    assert any(file.path.startswith("frontend/") for file in frontend_plan.file_structure)
    assert all("React Router" not in item for item in [frontend_plan.routing_strategy])

