import pytest
import os
import shutil
from unittest.mock import Mock, patch
from backend.models.state import ProjectState
from backend.models.planning import Task, ProjectPlan, SystemDesign
from backend.agents.coding_agent import CodingAgent
from langchain_community.chat_models.fake import FakeListChatModel
from backend.utils import slugify

class MockModelRouter:
    def __init__(self, fake_llm):
        self.fake_llm = fake_llm
    def get_model(self):
        return self.fake_llm

VALID_CODE_JSON = """
{
    "task_id": "TASK-001",
    "summary": "Generated DB",
    "requirements_implemented": ["FR-001"],
    "dependencies_used": [],
    "files": [
        {
            "path": "backend/db.py",
            "content": "print('db')"
        }
    ]
}
"""

def _mock_project_state():
    state = ProjectState(project_id="Test Project", user_requirement="req")
    state.project_plan = ProjectPlan(
        project_overview="...",
        system_design=SystemDesign(
            architecture_style="Monolith",
            components=[],
            data_flow="",
            database_schema=[],
            api_endpoints=[],
            technology_stack=["Python"],
            security_considerations=[]
        ),
        tasks=[]
    )
    task = Task(task_id="TASK-001", title="DB", description="Setup DB", related_requirements=["FR-001"])
    state.tasks["TASK-001"] = task
    return state

@pytest.fixture(autouse=True)
def clean_generated_projects():
    yield
    test_proj = os.path.join("generated_projects", "test_project")
    if os.path.exists(test_proj):
        shutil.rmtree(test_proj)

def test_coding_agent_invalid_task_id():
    state = _mock_project_state()
    agent = CodingAgent(MockModelRouter(FakeListChatModel(responses=[""])))
    new_state = agent.process(state, "UNKNOWN")
    assert "not found" in new_state.errors[0]

def test_coding_agent_dependency_not_completed():
    state = _mock_project_state()
    state.tasks["TASK-001"].dependencies = ["TASK-000"]
    # TASK-000 is not in completed_tasks
    agent = CodingAgent(MockModelRouter(FakeListChatModel(responses=[""])))
    new_state = agent.process(state, "TASK-001")
    assert "Dependency TASK-000 is not completed" in new_state.errors[0]
    assert state.tasks["TASK-001"].status == "failed"

def test_coding_agent_success_first_attempt():
    state = _mock_project_state()
    fake_llm = FakeListChatModel(responses=[VALID_CODE_JSON])
    agent = CodingAgent(MockModelRouter(fake_llm))
    new_state = agent.process(state, "TASK-001")
    
    assert new_state.tasks["TASK-001"].status == "completed"
    assert "TASK-001" in new_state.completed_tasks
    history = new_state.execution_history[-1]
    assert history["status"] == "success"
    assert history["attempts"] == 1
    
    # Check file exists
    proj_dir = os.path.join("generated_projects", slugify("Test Project"))
    assert os.path.exists(os.path.join(proj_dir, "backend", "db.py"))

def test_coding_agent_success_second_attempt():
    state = _mock_project_state()
    fake_llm = FakeListChatModel(responses=["invalid json", VALID_CODE_JSON])
    agent = CodingAgent(MockModelRouter(fake_llm))
    new_state = agent.process(state, "TASK-001")
    
    assert new_state.tasks["TASK-001"].status == "completed"
    history = new_state.execution_history[-1]
    assert history["status"] == "success"
    assert history["attempts"] == 2
    assert history["self_correction"] == "successful"

def test_coding_agent_fails_both_attempts():
    state = _mock_project_state()
    fake_llm = FakeListChatModel(responses=["invalid 1", "invalid 2"])
    agent = CodingAgent(MockModelRouter(fake_llm))
    new_state = agent.process(state, "TASK-001")
    
    assert new_state.tasks["TASK-001"].status == "failed"
    assert "TASK-001" in new_state.failed_tasks
    history = new_state.execution_history[-1]
    assert history["status"] == "error"
    assert history["attempts"] == 2

def test_coding_agent_unsafe_path_traversal():
    state = _mock_project_state()
    unsafe_json = VALID_CODE_JSON.replace("backend/db.py", "../../../etc/passwd")
    fake_llm = FakeListChatModel(responses=[unsafe_json, unsafe_json])
    agent = CodingAgent(MockModelRouter(fake_llm))
    new_state = agent.process(state, "TASK-001")
    
    assert new_state.tasks["TASK-001"].status == "failed"
    assert "Unsafe path traversal" in new_state.errors[0]

def test_coding_agent_absolute_path_rejection():
    state = _mock_project_state()
    abs_json = VALID_CODE_JSON.replace("backend/db.py", "/etc/passwd" if os.name != 'nt' else "C:\\\\\\\\Windows\\\\\\\\System32\\\\\\\\cmd.exe")
    fake_llm = FakeListChatModel(responses=[abs_json, abs_json])
    agent = CodingAgent(MockModelRouter(fake_llm))
    new_state = agent.process(state, "TASK-001")
    
    assert new_state.tasks["TASK-001"].status == "failed"
    assert "Absolute paths are forbidden" in new_state.errors[0] or "Unsafe path traversal" in new_state.errors[0]
