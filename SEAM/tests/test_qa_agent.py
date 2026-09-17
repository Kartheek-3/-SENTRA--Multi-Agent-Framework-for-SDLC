import pytest
import os
import shutil
from unittest.mock import Mock, patch
from backend.models.state import ProjectState
from backend.models.planning import Task, ProjectPlan, SystemDesign
from backend.agents.qa_agent import QAAgent
from langchain_community.chat_models.fake import FakeListChatModel
from backend.utils import slugify

class MockModelRouter:
    def __init__(self, fake_llm):
        self.fake_llm = fake_llm
    def get_model(self):
        return self.fake_llm

VALID_QA_JSON = """
{
  "task_id": "TASK-001",
  "status": "passed",
  "passed": true,
  "functional_issues": [],
  "requirement_violations": [],
  "architecture_violations": [],
  "security_issues": [],
  "syntax_errors": [],
  "test_results": [],
  "recommendations": [],
  "severity": "none",
  "files_checked": ["backend/main.py"]
}
"""

def _mock_project_state_qa():
    state = ProjectState(project_id="QA Test", user_requirement="req")
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
    task.status = "completed"
    task.result = {
        "files": [{"path": "backend/main.py", "content": "print('hello')"}]
    }
    state.tasks["TASK-001"] = task
    state.completed_tasks.append("TASK-001")
    
    proj_dir = os.path.join("generated_projects", slugify("QA Test"))
    os.makedirs(os.path.join(proj_dir, "backend"), exist_ok=True)
    with open(os.path.join(proj_dir, "backend", "main.py"), "w", encoding="utf-8") as f:
        f.write("print('hello')\n")
        
    return state

@pytest.fixture(autouse=True)
def clean_generated_projects_qa():
    yield
    test_proj = os.path.join("generated_projects", slugify("QA Test"))
    if os.path.exists(test_proj):
        shutil.rmtree(test_proj)

def test_qa_agent_invalid_syntax():
    state = _mock_project_state_qa()
    proj_dir = os.path.join("generated_projects", slugify("QA Test"))
    with open(os.path.join(proj_dir, "backend", "main.py"), "w", encoding="utf-8") as f:
        f.write("def invalid_syntax( \n") # Syntax error
        
    fake_llm = FakeListChatModel(responses=[""])
    agent = QAAgent(MockModelRouter(fake_llm))
    new_state = agent.process(state, "TASK-001")
    
    assert new_state.tasks["TASK-001"].status == "failed"
    res = new_state.tasks["TASK-001"].result.get("qa_result", {})
    assert "syntax_errors" in res
    assert len(res["syntax_errors"]) > 0

def test_qa_agent_security_heuristics():
    state = _mock_project_state_qa()
    proj_dir = os.path.join("generated_projects", slugify("QA Test"))
    with open(os.path.join(proj_dir, "backend", "main.py"), "w", encoding="utf-8") as f:
        f.write("import os\nos.system('rm -rf /')\n") # Syntax is fine, but security flagged
        
    fake_llm = FakeListChatModel(responses=[VALID_QA_JSON]) # LLM says passed
    agent = QAAgent(MockModelRouter(fake_llm))
    new_state = agent.process(state, "TASK-001")
    
    # QA should still fail due to deterministic security check overriding semantic check
    assert new_state.tasks["TASK-001"].status == "failed"
    res = new_state.tasks["TASK-001"].result.get("qa_result", {})
    assert "security_issues" in res
    assert len(res["security_issues"]) > 0

def test_qa_agent_success():
    state = _mock_project_state_qa()
    fake_llm = FakeListChatModel(responses=[VALID_QA_JSON])
    agent = QAAgent(MockModelRouter(fake_llm))
    new_state = agent.process(state, "TASK-001")
    
    assert new_state.tasks["TASK-001"].status == "completed" # Remains completed
    res = new_state.tasks["TASK-001"].result.get("qa_result", {})
    assert res.get("passed") is True
    
    proj_dir = os.path.join("generated_projects", slugify("QA Test"))
    assert os.path.exists(os.path.join(proj_dir, "qa", "TASK-001_qa_report.md"))

def test_qa_agent_missing_file():
    state = _mock_project_state_qa()
    state.tasks["TASK-001"].result["files"].append({"path": "missing.py", "content": ""})
    
    fake_llm = FakeListChatModel(responses=[""])
    agent = QAAgent(MockModelRouter(fake_llm))
    new_state = agent.process(state, "TASK-001")
    
    assert new_state.tasks["TASK-001"].status == "failed"
    res = new_state.tasks["TASK-001"].result.get("qa_result", {})
    assert len(res["syntax_errors"]) > 0
    assert "missing" in res["syntax_errors"][0].lower()
