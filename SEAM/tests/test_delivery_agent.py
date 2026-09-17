import pytest
import os
import shutil
import zipfile
import json
from backend.models.state import ProjectState
from backend.models.planning import Task, ProjectPlan, SystemDesign, ArchitectureComponent
from backend.models.analysis import AnalysisResult
from backend.agents.delivery_agent import DeliveryAgent
from backend.utils import slugify

def _mock_project_state_delivery():
    state = ProjectState(project_id="Delivery Test", user_requirement="req")
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
        recommended_capabilities=[]
    )
    state.project_plan = ProjectPlan(
        project_overview="...",
        system_design=SystemDesign(
            architecture_style="Monolith",
            components=[ArchitectureComponent(component_id="C1", name="C1", responsibility="R")],
            data_flow="",
            database_schema=[],
            api_endpoints=[],
            technology_stack=["Python"],
            security_considerations=[]
        ),
        tasks=[]
    )
    task = Task(task_id="TASK-001", title="DB", description="Setup DB", related_requirements=[])
    task.status = "completed"
    task.result = {
        "files": [{"path": "backend/main.py", "content": "print('hello')"}],
        "qa_result": {"passed": True}
    }
    state.tasks["TASK-001"] = task
    state.project_plan.tasks.append(task)
    state.completed_tasks.append("TASK-001")
    
    proj_dir = os.path.join("generated_projects", slugify("Delivery Test"))
    os.makedirs(os.path.join(proj_dir, "backend"), exist_ok=True)
    with open(os.path.join(proj_dir, "backend", "main.py"), "w", encoding="utf-8") as f:
        f.write("print('hello')\n")
        
    return state

@pytest.fixture(autouse=True)
def clean_generated_projects_delivery():
    yield
    test_proj = os.path.join("generated_projects", slugify("Delivery Test"))
    if os.path.exists(test_proj):
        shutil.rmtree(test_proj)

def test_delivery_agent_qa_missing():
    state = _mock_project_state_delivery()
    state.tasks["TASK-001"].result["qa_result"] = None
    agent = DeliveryAgent()
    new_state = agent.process(state)
    assert new_state.delivery_result["status"] == "failed"
    assert any("failed QA" in e for e in new_state.delivery_result["errors"])

def test_delivery_agent_secret_scan():
    state = _mock_project_state_delivery()
    proj_dir = os.path.join("generated_projects", slugify("Delivery Test"))
    with open(os.path.join(proj_dir, "backend", "secret.py"), "w", encoding="utf-8") as f:
        f.write("API_KEY = '12345ABCD'\n")
        
    agent = DeliveryAgent()
    new_state = agent.process(state)
    assert new_state.delivery_result["status"] == "failed"
    assert any("Secret detected" in e for e in new_state.delivery_result["errors"])

def test_delivery_agent_success():
    state = _mock_project_state_delivery()
    agent = DeliveryAgent()
    new_state = agent.process(state)
    
    res = new_state.delivery_result
    assert res["status"] == "deployed"
    assert res["qa_verified"] is True
    assert res["documentation_generated"] is True
    assert res["package_created"] is True
    
    proj_dir = os.path.join("generated_projects", slugify("Delivery Test"))
    assert os.path.exists(os.path.join(proj_dir, "README.md"))
    assert os.path.exists(os.path.join(proj_dir, "delivery", "delivery_manifest.json"))
    assert os.path.exists(os.path.join(proj_dir, "delivery", "project_package.zip"))
    
    with zipfile.ZipFile(os.path.join(proj_dir, "delivery", "project_package.zip"), 'r') as z:
        assert "README.md" in z.namelist()
        assert "backend/main.py" in [p.replace('\\', '/') for p in z.namelist()]
