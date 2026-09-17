import pytest
from unittest.mock import Mock, patch
from backend.models.state import ProjectState
from backend.agents.analysis_agent import AnalysisAgent
from backend.models.analysis import AnalysisResult
from langchain_core.messages import AIMessage
from langchain_community.chat_models.fake import FakeListChatModel

class MockModelRouter:
    def __init__(self, fake_llm):
        self.fake_llm = fake_llm
    def get_model(self):
        return self.fake_llm

VALID_JSON_RESPONSE = """
{
    "project_summary": "Test Summary",
    "application_domain": "E-commerce",
    "functional_requirements": [{"id": "FR-001", "description": "User login"}],
    "non_functional_requirements": [{"id": "NFR-001", "description": "Fast"}],
    "actors": ["User"],
    "entities": ["Product"],
    "constraints": ["Must use Python"],
    "assumptions": ["Users have internet"],
    "risks": ["Database failure"],
    "technical_considerations": ["Use FastAPI"],
    "ambiguities": ["Payment gateway not specified"],
    "recommended_capabilities": ["Social login"]
}
"""

def test_analysis_agent_valid_requirement():
    state = ProjectState(project_id="1", user_requirement="Build a store")
    
    fake_llm = FakeListChatModel(responses=[VALID_JSON_RESPONSE])
    router = MockModelRouter(fake_llm)
    
    agent = AnalysisAgent(router)
    new_state = agent.process(state)
    
    assert new_state.structured_requirements is not None
    assert new_state.structured_requirements.application_domain == "E-commerce"
    assert new_state.domain == "E-commerce"
    assert len(new_state.structured_requirements.functional_requirements) == 1
    
    assert len(new_state.execution_history) == 1
    assert new_state.execution_history[0]["status"] == "success"
    assert "duration" in new_state.execution_history[0]
    assert len(new_state.errors) == 0

def test_analysis_agent_empty_requirement():
    state = ProjectState(project_id="1", user_requirement="   ")
    agent = AnalysisAgent(MockModelRouter(FakeListChatModel(responses=[""])))
    
    new_state = agent.process(state)
    assert new_state.structured_requirements is None
    assert len(new_state.errors) == 1
    assert "empty" in new_state.errors[0]
    assert new_state.execution_history[-1]["status"] == "error"

def test_analysis_agent_invalid_llm_output():
    state = ProjectState(project_id="1", user_requirement="Build a store")
    
    fake_llm = FakeListChatModel(responses=["This is not valid json"])
    router = MockModelRouter(fake_llm)
    
    agent = AnalysisAgent(router)
    new_state = agent.process(state)
    
    assert new_state.structured_requirements is None
    assert len(new_state.errors) == 1
    assert "Failed to parse LLM output" in new_state.errors[0]
    assert new_state.execution_history[-1]["status"] == "error"

def test_analysis_agent_pydantic_validation_failure():
    state = ProjectState(project_id="1", user_requirement="Build a store")
    
    # Missing required fields
    invalid_json = '{"project_summary": "Test Summary"}'
    
    fake_llm = FakeListChatModel(responses=[invalid_json])
    router = MockModelRouter(fake_llm)
    
    agent = AnalysisAgent(router)
    new_state = agent.process(state)
    
    assert new_state.structured_requirements is None
    assert len(new_state.errors) == 1
    assert "Failed to parse LLM output" in new_state.errors[0]
    assert new_state.execution_history[-1]["status"] == "error"

def test_analysis_agent_model_api_failure():
    state = ProjectState(project_id="1", user_requirement="Build a store")
    
    class FailingFakeChatModel(FakeListChatModel):
        def invoke(self, *args, **kwargs):
            raise Exception("API connection error")

    fake_llm = FailingFakeChatModel(responses=["dummy"])
    router = MockModelRouter(fake_llm)
    
    agent = AnalysisAgent(router)
    new_state = agent.process(state)
    
    assert new_state.structured_requirements is None
    assert len(new_state.errors) == 1
    assert "Failed to parse LLM output. Details: API connection error" in new_state.errors[0]
    assert new_state.execution_history[-1]["status"] == "error"
