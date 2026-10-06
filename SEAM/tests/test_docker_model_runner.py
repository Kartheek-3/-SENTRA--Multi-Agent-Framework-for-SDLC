import pytest
from unittest.mock import MagicMock, patch

from backend.llm.model_router import ModelRouter
from backend.events import event_bus


def test_docker_model_runner_health_probe():
    router = ModelRouter(provider="docker")
    with patch("backend.llm.model_router.requests.get") as mock_get:
        # Mock version
        ver_resp = MagicMock()
        ver_resp.status_code = 200
        ver_resp.json.return_value = {"version": "v1.2.8"}

        # Mock models
        models_resp = MagicMock()
        models_resp.status_code = 200
        models_resp.json.return_value = {"data": [{"id": "ai/qwen3-coder"}, {"id": "ai/devstral-small-2"}]}

        def side_effect(url, timeout=5):
            if "version" in url:
                return ver_resp
            return models_resp

        mock_get.side_effect = side_effect

        health = router.probe_dmr_health()
        assert health["available"] is True
        assert health["version"] == "v1.2.8"
        assert "ai/qwen3-coder" in health["models"]


def test_docker_provider_returns_chat_openai():
    with patch("backend.llm.model_router.requests.get") as mock_get:
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"data": [{"id": "ai/qwen3-coder"}]}
        mock_get.return_value = resp

        router = ModelRouter(provider="docker")
        router.available_models = ["ai/qwen3-coder"]

        model = router.get_model("coding")
        from langchain_openai import ChatOpenAI
        assert isinstance(model, ChatOpenAI)
        assert model.model_name == "ai/qwen3-coder"
        assert "12434" in str(model.openai_api_base)


def test_model_router_records_execution_metadata():
    router = ModelRouter()
    record = router.record_execution(
        task_type="coding",
        model="qwen3-coder:30b",
        latency_ms=450,
        status="success",
        context_length=1200,
        token_usage={"prompt_tokens": 150, "completion_tokens": 300},
    )

    assert record["task"] == "coding"
    assert record["model"] == "qwen3-coder:30b"
    assert record["latency_ms"] == 450
    assert record["token_usage"]["completion_tokens"] == 300
    assert len(router.execution_history) == 1


def test_model_fallback_emits_event():
    queue = event_bus.subscribe()

    try:
        with patch("backend.llm.model_router.requests.get") as mock_get:
            resp = MagicMock()
            resp.status_code = 200
            resp.json.return_value = {"models": [{"name": "qwen2.5-coder:7b"}]}
            mock_get.return_value = resp

            router = ModelRouter(provider="ollama")
            router.available_models = ["qwen2.5-coder:7b"]
            router.get_model("coding")

            events = []
            while not queue.empty():
                events.append(queue.get_nowait())

            fallback_events = [e for e in events if e.get("event") == "MODEL_FALLBACK_TRIGGERED"]
            assert len(fallback_events) >= 1
            assert fallback_events[0]["task_type"] == "coding"
            assert fallback_events[0]["actual_model"] == "qwen2.5-coder:7b"
    finally:
        event_bus.unsubscribe(queue)


def test_docker_model_runner_qwen3_4b_verification():
    router = ModelRouter(provider="docker")
    with patch.object(router, "probe_dmr_health", return_value={"available": True, "version": "v1.2.8"}):
        with patch.object(router, "_fetch_docker_models", return_value=["ai/qwen3:4b-instruct-2507-q4_K_M"]):
            mock_chat = MagicMock()
            mock_resp = MagicMock()
            mock_resp.content = "OK"
            mock_chat.invoke.return_value = mock_resp

            with patch("langchain_openai.ChatOpenAI", return_value=mock_chat):
                res = router.verify_local_model_readiness("ai/qwen3:4b-instruct-2507-q4_K_M")
                assert res["status"] == "PASS"
                assert res["inference_verified"] is True
                assert res["model"] == "ai/qwen3:4b-instruct-2507-q4_K_M"


def test_docker_model_runner_missing_qwen3_4b_honesty():
    router = ModelRouter(provider="docker")
    with patch.object(router, "probe_dmr_health", return_value={"available": True, "version": "v1.2.8"}):
        with patch.object(router, "_fetch_docker_models", return_value=[]):
            res = router.verify_local_model_readiness("ai/qwen3:4b-instruct-2507-q4_K_M")
            assert res["status"] == "LOCAL_MODEL_NOT_AVAILABLE"
            assert res["inference_verified"] is False
            assert "docker model pull ai/qwen3:4b-instruct-2507-q4_K_M" in res["pull_command"]

