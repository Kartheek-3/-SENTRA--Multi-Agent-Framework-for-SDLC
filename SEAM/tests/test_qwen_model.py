from unittest.mock import MagicMock, patch

from backend.llm.model_router import ModelRouter


@patch("backend.llm.model_router.requests.get")
def test_qwen3_coder_next_is_configured_primary_model(mock_get):
    response = MagicMock()
    response.json.return_value = {"models": [{"name": "qwen3-coder-next"}]}
    mock_get.return_value = response

    router = ModelRouter()
    health = router.health()

    assert health["primary_model"] == "qwen3-coder-next"
    assert health["primary_model_available"] is True
    assert router.model_available("qwen3-coder-next") is True


@patch("backend.llm.model_router.ChatOllama")
@patch("backend.llm.model_router.requests.get")
def test_coding_model_uses_qwen3_coder_next_when_available(mock_get, mock_chat):
    response = MagicMock()
    response.json.return_value = {"models": [{"name": "qwen3-coder-next"}]}
    mock_get.return_value = response
    mock_chat.return_value = object()

    router = ModelRouter()
    router.get_model("coding")

    kwargs = mock_chat.call_args.kwargs
    assert kwargs["model"] == "qwen3-coder-next"

