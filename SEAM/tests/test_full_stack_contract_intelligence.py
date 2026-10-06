from backend.contracts import build_full_stack_contract_profile
from backend.models.analysis import AnalysisResult, Requirement
from backend.models.planning import (
    APIEndpoint,
    DatabaseEntity,
    FrontendAPIIntegration,
    FrontendArchitecturePlan,
    FrontendPagePlan,
    FrontendServicePlan,
    ProjectPlan,
    SystemDesign,
)
from backend.models.state import ProjectState


def _state(frontend_endpoint="POST /api/auth/login", backend_method="POST"):
    design = SystemDesign(
        architecture_style="Client-server",
        api_endpoints=[
            APIEndpoint(
                method=backend_method,
                path="/api/auth/login",
                purpose="Authenticate user login",
                request_schema='{"title":"LoginRequest","properties":{"email":{"type":"string"},"password":{"type":"string"}}}',
                response_schema='{"title":"LoginResponse","properties":{"token":{"type":"string"},"email":{"type":"string"}}}',
                authentication_required=False,
            )
        ],
        database_schema=[
            DatabaseEntity(name="User", fields=["id", "email", "password_hash"]),
        ],
    )
    return ProjectState(
        project_id="contracts",
        user_requirement="Build login",
        structured_requirements=AnalysisResult(
            project_summary="Login app",
            application_domain="auth",
            functional_requirements=[Requirement(id="FR-001", description="Users can login")],
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
        project_plan=ProjectPlan(project_overview="Login app", system_design=design),
        system_design=design,
        frontend_architecture_plan=FrontendArchitecturePlan(
            framework="React",
            language="TypeScript",
            build_system="Vite",
            pages=[FrontendPagePlan(name="LoginPage", route="/login", components=["LoginForm"])],
            services=[FrontendServicePlan(name="AuthService", files=["src/services/auth.ts"])],
            api_integration=[FrontendAPIIntegration(page="LoginPage", service="AuthService", endpoints=[frontend_endpoint])],
        ),
    )


def test_full_stack_contract_profile_maps_frontend_api_backend_and_database():
    profile = build_full_stack_contract_profile(_state())

    assert profile.status == "PASS"
    assert profile.api_contracts[0].endpoint == "/api/auth/login"
    assert profile.frontend_api_usage[0].frontend_file == "src/services/auth.ts"
    assert profile.mappings[0].status == "MATCH"
    assert profile.mappings[0].database_entity.name == "User"
    assert profile.traceability[0]["frontend_page"] == "LoginPage"


def test_full_stack_contract_detects_missing_backend_endpoint():
    profile = build_full_stack_contract_profile(_state(frontend_endpoint="POST /api/login"))

    assert profile.status == "FAIL"
    assert any(issue.category == "MISSING_BACKEND_ENDPOINT" for issue in profile.issues)
    issue = next(issue for issue in profile.issues if issue.category == "MISSING_BACKEND_ENDPOINT")
    assert issue.expected == "backend endpoint"
    assert issue.actual == "not found"


def test_full_stack_contract_detects_http_method_mismatch():
    profile = build_full_stack_contract_profile(_state(frontend_endpoint="GET /api/auth/login"))

    assert profile.status == "FAIL"
    assert any(issue.category == "HTTP_METHOD_MISMATCH" for issue in profile.issues)

