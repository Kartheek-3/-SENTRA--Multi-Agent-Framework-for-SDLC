import pytest
from unittest.mock import Mock, patch
from backend.models.state import ProjectState
from backend.agents.planning_agent import PlanningAgent
from backend.models.analysis import AnalysisResult, Requirement
from backend.models.planning import ProjectPlan, Task
from langchain_core.language_models.fake_chat_models import FakeListChatModel

class MockModelRouter:
    def __init__(self, fake_llm):
        self.fake_llm = fake_llm
    def get_model(self):
        return self.fake_llm

VALID_PLAN_JSON = """
{
    "project_overview": "Overview",
    "implementation_phases": ["Phase 1"],
    "tasks": [
        {
            "task_id": "TASK-001",
            "title": "DB Setup",
            "description": "Setup DB",
            "capability": "Storage",
            "priority": "High",
            "dependencies": [],
            "related_requirements": ["FR-001"],
            "estimated_complexity": "Medium"
        },
        {
            "task_id": "TASK-002",
            "title": "API Setup",
            "description": "Setup API",
            "capability": "Backend",
            "priority": "High",
            "dependencies": ["TASK-001"],
            "related_requirements": ["FR-002"],
            "estimated_complexity": "Medium"
        }
    ],
    "milestones": ["Milestone 1"],
    "system_design": {
        "architecture_style": "Microservices",
        "components": [],
        "data_flow": "Flow",
        "database_schema": [],
        "api_endpoints": [],
        "technology_stack": ["Python"],
        "security_considerations": ["JWT"]
    },
    "implementation_strategy": "Agile",
    "risks_and_mitigations": ["Risk 1"]
}
"""

def _mock_analysis_result():
    return AnalysisResult(
        project_summary="test",
        application_domain="test",
        functional_requirements=[Requirement(id="FR-001", description="Auth"), Requirement(id="FR-002", description="API")],
        non_functional_requirements=[],
        actors=["User"],
        entities=["Order"],
        constraints=[],
        assumptions=[],
        risks=[],
        technical_considerations=[],
        ambiguities=[],
        recommended_capabilities=[]
    )

def test_planning_agent_missing_analysis():
    state = ProjectState(project_id="1", user_requirement="req")
    agent = PlanningAgent(MockModelRouter(FakeListChatModel(responses=[""])))
    new_state = agent.process(state)
    assert new_state.project_plan is None
    assert len(new_state.errors) == 1
    assert "missing" in new_state.errors[0]

def test_planning_agent_success_first_attempt():
    state = ProjectState(project_id="1", user_requirement="req", structured_requirements=_mock_analysis_result())
    fake_llm = FakeListChatModel(responses=[VALID_PLAN_JSON])
    agent = PlanningAgent(MockModelRouter(fake_llm))
    new_state = agent.process(state)
    assert new_state.project_plan is not None
    history = new_state.execution_history[-1]
    assert history["status"] == "success"
    assert history["attempts"] == 1
    assert "self_correction" not in history

def test_planning_agent_success_second_attempt():
    state = ProjectState(project_id="1", user_requirement="req", structured_requirements=_mock_analysis_result())
    fake_llm = FakeListChatModel(responses=["Invalid JSON", VALID_PLAN_JSON])
    agent = PlanningAgent(MockModelRouter(fake_llm))
    new_state = agent.process(state)
    assert new_state.project_plan is not None
    history = new_state.execution_history[-1]
    assert history["status"] == "success"
    assert history["attempts"] == 2
    assert history["initial_validation"] == "failed"
    assert history["self_correction"] == "successful"
    assert len(new_state.errors) == 1  # 1st attempt error logged

def test_planning_agent_fails_both_attempts():
    state = ProjectState(project_id="1", user_requirement="req", structured_requirements=_mock_analysis_result())
    fake_llm = FakeListChatModel(responses=["Invalid 1", "Invalid 2"])
    agent = PlanningAgent(MockModelRouter(fake_llm))
    new_state = agent.process(state)
    assert new_state.project_plan is None
    history = new_state.execution_history[-1]
    assert history["status"] == "error"
    assert history["attempts"] == 2
    assert len(new_state.errors) == 3 # 2 attempt errors + 1 final error
    assert state.design_artifacts is None # Artifacts not generated

def test_planning_agent_duplicate_task_id():
    state = ProjectState(project_id="1", user_requirement="req", structured_requirements=_mock_analysis_result())
    dup_json = VALID_PLAN_JSON.replace("TASK-002", "TASK-001")
    fake_llm = FakeListChatModel(responses=[dup_json, dup_json])
    agent = PlanningAgent(MockModelRouter(fake_llm))
    new_state = agent.process(state)
    assert new_state.project_plan is None
    assert "Duplicate task_id" in new_state.errors[0]

def test_planning_agent_circular_dependency():
    state = ProjectState(project_id="1", user_requirement="req", structured_requirements=_mock_analysis_result())
    circ_json = VALID_PLAN_JSON.replace('"dependencies": []', '"dependencies": ["TASK-002"]')
    fake_llm = FakeListChatModel(responses=[circ_json, circ_json])
    agent = PlanningAgent(MockModelRouter(fake_llm))
    new_state = agent.process(state)
    assert new_state.project_plan is None
    assert "Circular dependency" in new_state.errors[0]

def test_planning_agent_api_failure():
    state = ProjectState(project_id="1", user_requirement="req", structured_requirements=_mock_analysis_result())
    
    class FailingFakeChatModel(FakeListChatModel):
        def invoke(self, *args, **kwargs):
            raise Exception("API Error")

    fake_llm = FailingFakeChatModel(responses=["dummy", "dummy"])
    agent = PlanningAgent(MockModelRouter(fake_llm))
    new_state = agent.process(state)
    
    assert new_state.project_plan is None
    assert "API Error" in new_state.errors[0]

def test_planning_agent_valid_milestones():
    state = ProjectState(project_id="1", user_requirement="req", structured_requirements=_mock_analysis_result())
    valid_milestone_json = VALID_PLAN_JSON.replace(
        '"milestones": ["Milestone 1"]',
        '"milestones": ["Requirement Analysis", "System Design", "Implementation"]'
    )
    fake_llm = FakeListChatModel(responses=[valid_milestone_json])
    agent = PlanningAgent(MockModelRouter(fake_llm))
    new_state = agent.process(state)
    assert new_state.project_plan is not None
    assert new_state.project_plan.milestones == ["Requirement Analysis", "System Design", "Implementation"]

def test_planning_agent_invalid_milestones():
    state = ProjectState(project_id="1", user_requirement="req", structured_requirements=_mock_analysis_result())
    invalid_milestone_json = VALID_PLAN_JSON.replace(
        '"milestones": ["Milestone 1"]',
        '"milestones": [{"milestone_id": "M1", "title": "Requirement Analysis"}]'
    )
    fake_llm = FakeListChatModel(responses=[invalid_milestone_json, invalid_milestone_json])
    agent = PlanningAgent(MockModelRouter(fake_llm))
    new_state = agent.process(state)
    assert new_state.project_plan is None
    assert len(new_state.errors) > 0
    assert "Failed to generate/parse plan" in new_state.errors[0] or "milestones" in new_state.errors[0]

