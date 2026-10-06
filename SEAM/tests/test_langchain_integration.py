from unittest.mock import MagicMock, patch

from langchain_core.language_models.fake_chat_models import FakeListChatModel

from backend.agents.analysis_agent import AnalysisAgent
from backend.llm.model_router import ModelRouter
from backend.models.state import ProjectState


VALID_ANALYSIS_JSON = """
{
  "project_summary": "Expense tracker",
  "application_domain": "finance",
  "functional_requirements": [{"id": "FR-001", "description": "Add expense"}],
  "non_functional_requirements": [{"id": "NFR-001", "description": "Validate input"}],
  "actors": ["User"],
  "entities": ["Expense"],
  "constraints": [],
  "assumptions": [],
  "risks": [],
  "technical_considerations": ["FastAPI"],
  "ambiguities": [],
  "recommended_capabilities": []
}
"""


class Router:
    active_models = {"analysis": {"actual": "fake-langchain"}}

    def __init__(self):
        self.model = FakeListChatModel(responses=[VALID_ANALYSIS_JSON])

    def get_model(self, task_type="analysis"):
        return self.model


def test_agent_llm_request_uses_langchain_chain():
    state = ProjectState(project_id="langchain-analysis", user_requirement="Build a finance expense tracker")
    agent = AnalysisAgent(Router())

    new_state = agent.process(state)

    assert new_state.structured_requirements is not None
    assert new_state.domain == "finance"
    assert new_state.execution_history[-1]["status"] == "success"


@patch("backend.llm.model_router.ChatOllama")
@patch("backend.llm.model_router.requests.get")
def test_model_router_returns_langchain_chat_ollama(mock_get, mock_chat):
    response = MagicMock()
    response.json.return_value = {"models": [{"name": "qwen3-coder-next"}]}
    mock_get.return_value = response
    mock_chat.return_value = object()

    router = ModelRouter()
    model = router.get_model("coding")

    assert model is mock_chat.return_value
    assert router.active_models["coding"]["actual"] == "qwen3-coder-next"
    mock_chat.assert_called_once()


@patch("backend.llm.model_router.requests.get")
def test_qwen_health_reports_model_availability(mock_get):
    response = MagicMock()
    response.json.return_value = {"models": [{"name": "qwen3-coder-next"}]}
    mock_get.return_value = response

    router = ModelRouter()
    health = router.health()

    assert health["provider"] == "ollama"
    assert health["qwen3_coder_next_available"] is True
    assert health["primary_model_available"] is True
