import os
import shutil

import pytest

from backend.agents.delivery_agent import DeliveryAgent
from backend.models.analysis import AnalysisResult
from backend.models.contracts import RepairPlan
from backend.models.planning import ArchitectureComponent, ProjectPlan, SystemDesign, Task
from backend.models.state import ProjectState
from backend.utils import slugify


def _state() -> ProjectState:
    state = ProjectState(project_id="Delivery Intelligence Test", user_requirement="Build a small app")
    state.structured_requirements = AnalysisResult(
        project_summary="summary",
        application_domain="domain",
        functional_requirements=[],
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
        project_overview="Expense tracker",
        system_design=SystemDesign(
            architecture_style="Full-stack web",
            components=[ArchitectureComponent(component_id="C1", name="API", responsibility="Serve REST APIs")],
            data_flow="",
            database_schema=[],
            api_endpoints=[],
            technology_stack=["React", "FastAPI", "SQLite"],
            security_considerations=[],
        ),
        tasks=[],
    )
    task = Task(task_id="TASK-001", title="App", description="Generate app", related_requirements=[])
    task.status = "completed"
    task.result = {"files": [{"path": "backend/main.py"}], "qa_result": {"passed": True}}
    state.tasks[task.task_id] = task
    state.project_plan.tasks.append(task)
    state.completed_tasks.append(task.task_id)
    return state


def _project_dir(state: ProjectState) -> str:
    return os.path.join("generated_projects", state.project_name)


@pytest.fixture(autouse=True)
def clean_generated_projects():
    yield
    for name in [slugify("Delivery Intelligence Test")]:
        path = os.path.join("generated_projects", name)
        if os.path.exists(path):
            shutil.rmtree(path)


def test_delivery_detects_docker_profile_and_environment_without_secret_values():
    state = _state()
    root = _project_dir(state)
    os.makedirs(os.path.join(root, "backend"), exist_ok=True)
    with open(os.path.join(root, "Dockerfile"), "w", encoding="utf-8") as f:
        f.write("FROM python:3.12\nEXPOSE 8000\nCMD [\"python\", \"backend/main.py\"]\n")
    with open(os.path.join(root, "backend", "main.py"), "w", encoding="utf-8") as f:
        f.write("import os\nfrom fastapi import FastAPI\napp = FastAPI()\nDATABASE_URL = os.getenv('DATABASE_URL')\n")
    with open(os.path.join(root, ".env.example"), "w", encoding="utf-8") as f:
        f.write("DATABASE_URL=${DATABASE_URL}\n")

    result = DeliveryAgent().process(state)

    assert result.deployment_profile is not None
    assert result.deployment_profile.target == "Docker"
    assert result.deployment_profile.containerization_status == "CONFIGURED"
    assert result.deployment_profile.exposed_ports == [8000]
    assert result.release_readiness is not None
    assert result.release_readiness.security_status == "PASS"
    env = result.deployment_profile.required_environment_variables[0]
    assert env.name == "DATABASE_URL"
    assert env.secret is True
    assert "${DATABASE_URL}" not in result.deployment_result.model_dump_json()


def test_delivery_blocks_on_unresolved_repair_before_packaging():
    state = _state()
    root = _project_dir(state)
    os.makedirs(os.path.join(root, "backend"), exist_ok=True)
    with open(os.path.join(root, "backend", "main.py"), "w", encoding="utf-8") as f:
        f.write("print('hello')\n")
    state.repair_plans.append(RepairPlan(repair_id="RP-1", source="E2E", status="PENDING"))

    result = DeliveryAgent().process(state)

    assert result.release_readiness is not None
    assert result.release_readiness.status == "BLOCKED"
    assert result.delivery_result["status"] == "failed"
    assert any("Unresolved repair" in item for item in result.delivery_result["errors"])


def test_delivery_blocks_on_real_secret_without_exposing_value():
    state = _state()
    root = _project_dir(state)
    os.makedirs(os.path.join(root, "backend"), exist_ok=True)
    secret_value = "abc12345678901234567890"
    with open(os.path.join(root, "backend", "main.py"), "w", encoding="utf-8") as f:
        f.write(f"token = '{secret_value}'\n")

    result = DeliveryAgent().process(state)

    dumped = result.model_dump_json()
    assert result.release_readiness is not None
    assert result.release_readiness.security_status == "FAIL"
    assert any("SECRET_DETECTED" in item for item in result.release_readiness.blockers)
    assert secret_value not in dumped


def test_delivery_state_contains_release_artifacts_after_success():
    state = _state()
    root = _project_dir(state)
    os.makedirs(os.path.join(root, "backend"), exist_ok=True)
    with open(os.path.join(root, "backend", "main.py"), "w", encoding="utf-8") as f:
        f.write("print('hello')\n")

    result = DeliveryAgent().process(state)

    assert result.release_readiness is not None
    assert result.deployment_profile is not None
    assert result.deployment_result is not None
    assert result.post_deployment_verification is not None
    assert result.rollback_info is not None
    assert os.path.exists(os.path.join(root, "delivery", "release_readiness.json"))
    assert os.path.exists(os.path.join(root, "delivery", "deployment_profile.json"))
