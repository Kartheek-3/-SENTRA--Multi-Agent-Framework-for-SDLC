import pytest
import os
from unittest.mock import patch, MagicMock

@patch("backend.llm.model_router.requests.get")
def test_model_router_fallback(mock_get):
    # Mocking Ollama /api/tags response
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "models": [
            {"name": "qwen2.5-coder:7b"},
            {"name": "llama3:latest"}
        ]
    }
    mock_get.return_value = mock_response
    
    # Reload model router to pick up the mock
    from backend.llm.model_router import ModelRouter
    router = ModelRouter()
    
    # We requested qwen3-coder-next by default, it's not installed.
    # Fallback is qwen3-coder:30b, also not installed.
    # Legacy is qwen2.5-coder:7b, which is installed!
    
    model = router.get_model("coding")
    
    assert router.active_models["coding"]["actual"] == "qwen2.5-coder:7b"
    assert router.active_models["coding"]["fallback_used"] is True
