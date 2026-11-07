import os
import shutil
import pytest
from unittest.mock import MagicMock, patch

from backend.models.state import ProjectState
from backend.github.workspace_service import SafeWorkspaceService, SafeWorkspaceError
from backend.github.understanding_service import ProjectUnderstandingService
from backend.github.enhancement_planner import EnhancementPlanningService
from backend.github.intelligence_models import DetailedRepositoryProfile, ProjectUnderstanding
from backend.agents.analysis_agent import AnalysisAgent
from backend.agents.planning_agent import PlanningAgent
from backend.agents.coding_agent import CodingAgent
from backend.agents.supervisor_agent import SupervisorAgent
from backend.llm.model_router import ModelRouter

TEST_WORKSPACE_ROOT = os.path.abspath(os.path.join(os.getcwd(), "test_phase3_scratch"))

@pytest.fixture(autouse=True)
def cleanup_test_scratch():
    os.makedirs(TEST_WORKSPACE_ROOT, exist_ok=True)
    yield
    if os.path.exists(TEST_WORKSPACE_ROOT):
        shutil.rmtree(TEST_WORKSPACE_ROOT, ignore_errors=True)

def _create_sample_repo(path: str):
    """Creates a realistic sample repository on disk with FastAPI backend, React frontend, SQLite DB, and tests."""
    os.makedirs(os.path.join(path, "backend"), exist_ok=True)
    os.makedirs(os.path.join(path, "frontend"), exist_ok=True)
    os.makedirs(os.path.join(path, "tests"), exist_ok=True)

    # 1. README
    with open(os.path.join(path, "README.md"), "w", encoding="utf-8") as f:
        f.write("# TaskPulse System\n\nTaskPulse is a collaborative workflow and task management platform.\nFeatures include task assignment and analytics.\n")

    # 2. Package manifest
    with open(os.path.join(path, "requirements.txt"), "w", encoding="utf-8") as f:
        f.write("fastapi>=0.100.0\nuvicorn>=0.23.0\nsqlalchemy>=2.0.0\npytest>=7.4.0\n")

    # 3. Backend entry point with API routes and SQLAlchemy model
    main_py = """from fastapi import FastAPI, APIRouter
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

app = FastAPI(title="TaskPulse API")
router = APIRouter()
Base = declarative_base()

class TaskModel(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)

@app.get("/api/v1/health")
def health():
    return {"status": "ok"}

@router.get("/api/v1/tasks")
def list_tasks():
    return [{"id": 1, "title": "Initial Task"}]

@router.post("/api/v1/tasks")
def create_task(title: str):
    return {"id": 2, "title": title}

app.include_router(router)
"""
    with open(os.path.join(path, "backend", "main.py"), "w", encoding="utf-8") as f:
        f.write(main_py)

    # 4. Frontend manifest and component
    with open(os.path.join(path, "frontend", "package.json"), "w", encoding="utf-8") as f:
        f.write('{"name": "taskpulse-ui", "dependencies": {"react": "^18.2.0"}}\n')

    with open(os.path.join(path, "frontend", "App.tsx"), "w", encoding="utf-8") as f:
        f.write("import React from 'react';\nexport function App() { return <div>TaskPulse</div>; }\n")

    # 5. Tests
    with open(os.path.join(path, "tests", "test_tasks.py"), "w", encoding="utf-8") as f:
        f.write("def test_dummy():\n    assert True\n")

    # 6. Dockerfile
    with open(os.path.join(path, "Dockerfile"), "w", encoding="utf-8") as f:
        f.write("FROM python:3.11-slim\nCMD [\"uvicorn\", \"backend.main:app\"]\n")


def test_workflow_a_vs_workflow_b_selection():
    """1. Validates that Workflow A (new_project) and Workflow B (enhance_existing) have distinct state semantics."""
    state_a = ProjectState(project_id="proj-a", user_requirement="Build an expense tracker", workflow_type="new_project")
    assert state_a.workflow_type == "new_project"
    assert state_a.is_enhance_workflow is False

    state_b = ProjectState(
        project_id="proj-b",
        user_requirement="Add CSV export to tasks",
        workflow_type="enhance_existing",
        repo_url="https://github.com/octocat/Hello-World",
        repo_branch="main"
    )
    assert state_b.workflow_type == "enhance_existing"
    assert state_b.is_enhance_workflow is True
    assert state_b.repo_url == "https://github.com/octocat/Hello-World"


def test_github_url_validation_and_parsing():
    """2. Validates accepted GitHub URL formats and rejection of invalid / malicious URLs."""
    # Valid formats
    o, n, u = SafeWorkspaceService.parse_github_url("https://github.com/org/my-repo")
    assert (o, n, u) == ("org", "my-repo", "https://github.com/org/my-repo")

    o, n, u = SafeWorkspaceService.parse_github_url("git@github.com:org/my-repo.git")
    assert (o, n, u) == ("org", "my-repo", "https://github.com/org/my-repo")

    o, n, u = SafeWorkspaceService.parse_github_url("owner/repo")
    assert (o, n, u) == ("owner", "repo", "https://github.com/owner/repo")

    # Invalid / malicious URLs
    with pytest.raises(SafeWorkspaceError):
        SafeWorkspaceService.parse_github_url("https://evil.com/owner/repo")

    with pytest.raises(SafeWorkspaceError):
        SafeWorkspaceService.parse_github_url("owner/../../etc/passwd")

    with pytest.raises(SafeWorkspaceError):
        SafeWorkspaceService.parse_github_url("")


def test_private_repository_not_configured_when_no_token():
    """3. Verifies that private repositories without a configured GITHUB_TOKEN return NOT_CONFIGURED without leaking secrets."""
    from backend.api.github import connect_repository, ConnectRepositoryRequest
    with patch.dict(os.environ, {}, clear=True), \
         patch("backend.github.github_client.GitHubClient.get_repository", return_value=None):
        req = ConnectRepositoryRequest(repo_url="https://github.com/private-org/secret-repo")
        res = connect_repository(req)
        assert res["status"] == "NOT_CONFIGURED"
        assert res["connected"] is False
        assert "NOT_CONFIGURED" in res["detail"]


def test_public_repository_access_and_branch_inspection():
    """4. Verifies public repository access and branch commit inspection."""
    from backend.api.github import connect_repository, ConnectRepositoryRequest
    mock_repo_payload = {
        "name": "public-repo",
        "owner": {"login": "public-org"},
        "default_branch": "main",
        "private": False,
        "stargazers_count": 42,
        "language": "Python",
    }
    with patch("backend.github.github_client.GitHubClient.get_repository", return_value=mock_repo_payload), \
         patch("backend.github.github_client.GitHubClient.get_latest_commit_sha", return_value="a1b2c3d4e5f6"):
        req = ConnectRepositoryRequest(repo_url="public-org/public-repo", branch="main")
        res = connect_repository(req)
        assert res["status"] == "CONNECTED"
        assert res["connected"] is True
        assert res["commit_sha"] == "a1b2c3d4e5f6"
        assert res["is_private"] is False


def test_workspace_path_confinement():
    """5. Verifies path confinement within designated repository workspace prevents directory escape."""
    service = SafeWorkspaceService(base_workspaces_dir=TEST_WORKSPACE_ROOT)
    ws_path = service.get_workspace_path("test-proj")
    os.makedirs(ws_path, exist_ok=True)

    # Valid relative path
    safe_target = service.validate_path_confinement(ws_path, "backend/main.py")
    assert safe_target.startswith(ws_path)

    # Traversal escape attempts
    with pytest.raises(SafeWorkspaceError):
        service.validate_path_confinement(ws_path, "../outside.py")

    with pytest.raises(SafeWorkspaceError):
        service.validate_path_confinement(ws_path, "/etc/shadow")

    with pytest.raises(SafeWorkspaceError):
        service.validate_path_confinement(ws_path, "C:\\Windows\\System32\\cmd.exe")


def test_repository_profile_and_project_understanding_extraction():
    """6 & 7. Verifies evidence-based extraction of languages, frameworks, entry points, APIs, schemas, tests, and the 14 project understanding sections."""
    repo_dir = os.path.join(TEST_WORKSPACE_ROOT, "sample_repo")
    _create_sample_repo(repo_dir)

    service = ProjectUnderstandingService(repo_dir)
    profile, understanding = service.analyze(repo_dir, owner="test-org", name="TaskPulse", branch="main", commit_sha="c0ffee1234")

    # 1. Profile Verification
    assert "Python" in profile.detected_languages
    assert "TypeScript" in profile.detected_languages
    assert "FastAPI" in profile.frameworks
    assert "React" in profile.frameworks
    assert "pip / poetry" in profile.package_managers
    assert any("main.py" in ep for ep in profile.application_entry_points)
    assert len(profile.api_routes) >= 2
    assert any(r["path"] == "/api/v1/health" for r in profile.api_routes)
    assert any(r["path"] == "/api/v1/tasks" for r in profile.api_routes)
    assert any(s["entity"] == "TaskModel" for s in profile.database_schemas)
    assert any("Dockerfile" in d for d in profile.deployment_configuration)

    # 2. 14 Sections of ProjectUnderstanding
    assert "TaskPulse" in understanding.project_purpose
    assert len(understanding.technology_stack) > 0
    assert understanding.architecture_and_entry_points
    assert len(understanding.directory_structure) > 0
    assert len(understanding.main_modules) > 0
    assert len(understanding.api_surface) >= 2
    assert understanding.database_and_persistence["confirmed"] is True
    assert understanding.existing_tests["test_files_count"] >= 1
    assert len(understanding.build_and_runtime_instructions["commands"]) > 0
    assert len(understanding.deployment_configuration["manifests"]) >= 1
    assert len(understanding.architectural_limitations) > 0
    assert isinstance(understanding.potential_defects, list)
    assert len(understanding.improvement_opportunities) > 0
    assert len(understanding.uncertainties_requiring_input) > 0

    # 3. Artifact writing
    gen_dir = os.path.join(TEST_WORKSPACE_ROOT, "artifacts")
    paths = service.write_artifacts(gen_dir, profile, understanding)
    assert os.path.exists(paths["json"])
    assert os.path.exists(paths["md"])


def test_enhancement_plan_generation_and_approval_enforcement():
    """8, 9, 10. Verifies structured enhancement plan generation, approval gating, and permission controls."""
    repo_dir = os.path.join(TEST_WORKSPACE_ROOT, "sample_repo")
    _create_sample_repo(repo_dir)

    u_service = ProjectUnderstandingService(repo_dir)
    profile, understanding = u_service.analyze(repo_dir, "test-org", "TaskPulse")

    p_service = EnhancementPlanningService()
    plan = p_service.create_plan(
        project_id="proj-enh-1",
        user_requirement="Add CSV export functionality to tasks",
        profile=profile,
        understanding=understanding
    )

    assert plan.status == "pending_approval"
    assert len(plan.items) == 1
    item = plan.items[0]
    assert item.approved is False
    assert item.current_behavior
    assert item.proposed_improvement
    assert item.why_needed
    assert len(item.files_expected_to_change) > 0
    assert item.rollback_considerations

    # Write plan artifacts
    gen_dir = os.path.join(TEST_WORKSPACE_ROOT, "artifacts")
    paths = p_service.write_artifacts(gen_dir, plan)
    assert os.path.exists(paths["json"])
    assert os.path.exists(paths["md"])


def test_supervisor_halts_at_approval_gate_before_approval():
    """11. Verifies Supervisor halts at APPROVAL_GATE before user approval in Workflow B."""
    state = ProjectState(
        project_id="proj-gate",
        user_requirement="Refactor auth",
        workflow_type="enhance_existing",
        repo_url="test/repo",
    )
    from backend.models.analysis import AnalysisResult
    from backend.models.planning import ProjectPlan, SystemDesign
    state.structured_requirements = AnalysisResult(
        project_summary="summary",
        application_domain="Domain",
        functional_requirements=[],
        non_functional_requirements=[],
        actors=["User"],
        entities=["Project"],
        constraints=["None"],
        assumptions=["Standard setup"],
        risks=[],
        technical_considerations=["FastAPI"],
        ambiguities=[],
        recommended_capabilities=[],
    )
    state.project_plan = ProjectPlan(project_overview="overview", implementation_phases=[], tasks=[], milestones=[], system_design=SystemDesign(architecture_style="Modular", components=[]))
    state.enhancement_approved = False

    supervisor = SupervisorAgent()
    next_state = supervisor.process(state)

    assert next_state.current_agent == "APPROVAL_GATE"
    assert next_state.workflow_status == "waiting_for_approval"
    assert next_state.approval_status == "pending"


def test_coding_agent_blocks_modification_without_approval():
    """12. Verifies CodingAgent refuses to modify workspace files if enhancement is not approved."""
    repo_dir = os.path.join(TEST_WORKSPACE_ROOT, "sample_repo")
    _create_sample_repo(repo_dir)

    state = ProjectState(
        project_id="proj-unapproved",
        user_requirement="Dangerous patch",
        workflow_type="enhance_existing",
        repo_workspace_path=repo_dir,
        enhancement_approved=False,
    )
    from backend.models.planning import Task
    t = Task(task_id="TASK-001", title="Modify", description="Modify code", related_requirements=[])
    state.tasks[t.task_id] = t

    router = ModelRouter()
    agent = CodingAgent(router)
    res_state = agent.process(state, "TASK-001")

    assert t.status == "failed"
    assert any("blocked" in err.lower() or "not approved" in err.lower() for err in res_state.errors)


def test_approved_targeted_code_enhancement_and_diff_generation():
    """13. Verifies targeted non-destructive code enhancement in isolated workspace produces real diff and updates state."""
    repo_dir = os.path.join(TEST_WORKSPACE_ROOT, "sample_repo")
    _create_sample_repo(repo_dir)

    state = ProjectState(
        project_id="proj-approved",
        user_requirement="Add CSV export helper",
        workflow_type="enhance_existing",
        repo_workspace_path=repo_dir,
        enhancement_approved=True,
    )
    from backend.models.planning import Task
    t = Task(task_id="TASK-ENH-001", title="Export helper", description="Add export helper to backend", related_requirements=[])
    t.status = "in_progress"
    state.tasks[t.task_id] = t

    # Initialize a git repo in sample_repo so git diff works
    import subprocess
    subprocess.run(["git", "init"], cwd=repo_dir, capture_output=True, check=False)
    subprocess.run(["git", "config", "user.name", "TestRunner"], cwd=repo_dir, capture_output=True, check=False)
    subprocess.run(["git", "config", "user.email", "test@test.local"], cwd=repo_dir, capture_output=True, check=False)
    subprocess.run(["git", "add", "."], cwd=repo_dir, capture_output=True, check=False)
    subprocess.run(["git", "commit", "-m", "Baseline commit"], cwd=repo_dir, capture_output=True, check=False)

    router = ModelRouter()
    agent = CodingAgent(router)

    # Mock the LLM to return valid CodeGenerationResult modifying backend/export.py
    import json
    from langchain_core.language_models.fake_chat_models import FakeListChatModel
    mock_result_json = json.dumps({
        "task_id": "TASK-ENH-001",
        "summary": "Export helper implemented",
        "requirements_implemented": [],
        "dependencies_used": [],
        "files": [{"path": "backend/export.py", "content": "def export_csv(tasks):\n    return 'id,title\\n1,Sample'\n"}]
    })
    fake_llm = FakeListChatModel(responses=[mock_result_json])

    with patch.object(router, "get_model", return_value=fake_llm):
        res_state = agent.process(state, "TASK-ENH-001")

    if t.status != "completed":
        print(f"FAILED ERRORS: {res_state.errors}")
    assert t.status == "completed"
    assert os.path.exists(os.path.join(repo_dir, "backend", "export.py"))
    # Changed files and diff should be captured
    assert len(res_state.targeted_changes) >= 1
    assert any("export.py" in str(c) for c in res_state.targeted_changes)
    # Check diff artifact
    gen_dir = os.path.join("generated_projects", state.project_name)
    assert os.path.exists(os.path.join(gen_dir, "enhancement_diff.patch"))
    assert os.path.exists(os.path.join(gen_dir, "enhancement_diff.md"))
