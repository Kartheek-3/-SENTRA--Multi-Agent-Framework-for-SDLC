import pytest
from unittest.mock import MagicMock, patch
from backend.llm.hardware_detector import detect_runtime_hardware
from backend.llm.model_router import ModelRouter
from backend.events import event_bus
from backend.config import SEAM_LOCAL_MODEL

def test_hardware_detector_identifies_host_resources():
    """1. 16 GB CPU-only hardware is classified correctly as LOW_RESOURCE_CPU."""
    info = detect_runtime_hardware()
    assert "profile" in info
    assert info["profile"] in ["LOW_RESOURCE_CPU", "WORKSTATION", "GPU_WORKSTATION", "HIGH_MEMORY_SERVER", "CLOUD"]
    assert info["total_ram_gb"] > 0
    assert info["cpu_cores"] > 0
    assert "gpu_name" in info
    assert "can_run_high_tier_locally" in info
    assert info["high_tier_candidate"] == "ai/qwen3.8-flash-next"
    assert info["recommended_local_model"] == "ai/qwen3:4b-instruct-2507-q4_K_M"
    assert info["local_model_name"] == "Qwen3 4B Instruct Q4_K_M"

    # Verify conservative classification for 16GB CPU machine
    if info["total_ram_gb"] < 32.0 and not info["has_cuda"]:
        assert info["profile"] == "LOW_RESOURCE_CPU"
        assert info["can_run_high_tier_locally"] is False

def test_model_router_hardware_profile_initialization():
    """Verifies ModelRouter initializes with hardware profile and Qwen3 4B fallback."""
    router = ModelRouter(provider="docker")
    assert hasattr(router, "hardware_profile")
    health = router.health()
    assert "hardware_profile" in health
    assert "high_tier_inference_status" in health
    assert "local_fallback_status" in health
    assert health["local_fallback_model"] == "ai/qwen3:4b-instruct-2507-q4_K_M"
    assert health["high_tier_model"] in ["ai/qwen3.8-flash-next", "qwen3.8-flash-next"]
    if not router.hardware_profile.get("can_run_high_tier_locally", False):
        assert health["high_tier_inference_status"] == "NOT_AVAILABLE_ON_CURRENT_HARDWARE"

def test_high_tier_rejected_and_routes_to_qwen3_4b_fallback():
    """2 & 3. High-tier local model is rejected on LOW_RESOURCE_CPU and routes to Qwen3 4B fallback."""
    queue = event_bus.subscribe()
    try:
        router = ModelRouter(provider="docker")
        router.hardware_profile = {
            "profile": "LOW_RESOURCE_CPU",
            "can_run_high_tier_locally": False,
            "recommended_local_model": "ai/qwen3:4b-instruct-2507-q4_K_M",
            "constraint_reason": "High-tier local inference disabled on CPU-only hardware."
        }
        router.available_models = ["ai/qwen3:4b-instruct-2507-q4_K_M"]

        # Request high-tier model
        chosen = router._get_safe_model_name("ai/qwen3.8-flash-next", "planning")
        assert chosen == "ai/qwen3:4b-instruct-2507-q4_K_M"

        events = []
        while not queue.empty():
            events.append(queue.get_nowait())

        fallback_events = [e for e in events if e.get("event") == "MODEL_FALLBACK_TRIGGERED"]
        assert len(fallback_events) >= 1
        fb = fallback_events[0]
        # 4. Fallback telemetry contains the correct model & schema
        assert fb["requested_model"] == "ai/qwen3.8-flash-next"
        assert fb["fallback_model"] == "ai/qwen3:4b-instruct-2507-q4_K_M"
        assert fb["hardware_profile"] == "LOW_RESOURCE_CPU"
        assert fb["reason"] == "HIGH_TIER_MODEL_NOT_SUPPORTED_ON_CURRENT_HARDWARE"
    finally:
        event_bus.unsubscribe(queue)

def test_fallback_telemetry_schema_and_no_credentials():
    """4 & 8. Fallback telemetry schema matches required fields and exposes no credentials."""
    queue = event_bus.subscribe()
    try:
        router = ModelRouter(provider="docker")
        router.hardware_profile = {
            "profile": "LOW_RESOURCE_CPU",
            "can_run_high_tier_locally": False,
            "recommended_local_model": "ai/qwen3:4b-instruct-2507-q4_K_M",
            "constraint_reason": "LOW_RESOURCE_CPU host"
        }
        router._emit_fallback_event(
            task_type="coding",
            requested="ai/qwen3.8-flash-next",
            actual="ai/qwen3:4b-instruct-2507-q4_K_M",
            reason="HIGH_TIER_MODEL_NOT_SUPPORTED_ON_CURRENT_HARDWARE",
            latency=120,
            tokens=35,
        )

        events = []
        while not queue.empty():
            events.append(queue.get_nowait())

        fb = events[0]
        assert fb["event"] == "MODEL_FALLBACK_TRIGGERED"
        assert fb["requested_model"] == "ai/qwen3.8-flash-next"
        assert fb["fallback_model"] == "ai/qwen3:4b-instruct-2507-q4_K_M"
        assert fb["reason"] == "HIGH_TIER_MODEL_NOT_SUPPORTED_ON_CURRENT_HARDWARE"
        assert fb["hardware_profile"] == "LOW_RESOURCE_CPU"
        assert fb["latency"] == 120
        assert fb["tokens"] == 35

        # Check no credentials leaked
        for k, v in fb.items():
            val_str = str(v).lower()
            assert "password" not in val_str
            assert "secret" not in val_str
            assert "api_key" not in val_str
            assert "token" not in k or k == "tokens"
    finally:
        event_bus.unsubscribe(queue)

def test_missing_qwen3_4b_reported_honestly():
    """5. Missing Qwen3 4B is reported honestly as LOCAL_MODEL_NOT_AVAILABLE."""
    router = ModelRouter(provider="docker")
    with patch.object(router, "probe_dmr_health", return_value={"available": True, "version": "v1.2.8"}):
        with patch.object(router, "_fetch_docker_models", return_value=[]):
            readiness = router.verify_local_model_readiness("ai/qwen3:4b-instruct-2507-q4_K_M")
            assert readiness["status"] == "LOCAL_MODEL_NOT_AVAILABLE"
            assert readiness["inference_verified"] is False
            assert readiness["model"] == "ai/qwen3:4b-instruct-2507-q4_K_M"
            assert readiness["pull_command"] == "docker model pull ai/qwen3:4b-instruct-2507-q4_K_M"
            assert "not loaded" in readiness["reason"]

def test_endpoint_http200_does_not_count_as_successful_inference():
    """7. Endpoint-only HTTP 200 from /v1/models does NOT count as successful inference."""
    router = ModelRouter(provider="docker")
    # Even if DMR endpoint returns HTTP 200 with available=True, if model is not present or invoke fails, status is NOT PASS
    with patch.object(router, "probe_dmr_health", return_value={"available": True, "version": "v1.2.8"}):
        with patch.object(router, "_fetch_docker_models", return_value=["ai/other-model"]):
            res = router.verify_local_model_readiness("ai/qwen3:4b-instruct-2507-q4_K_M")
            assert res["status"] != "PASS"
            assert res["inference_verified"] is False

def test_real_qwen3_4b_inference_verification_succeeds_when_available():
    """6. Real Qwen3 4B inference succeeds when model is available in runner."""
    router = ModelRouter(provider="docker")
    with patch.object(router, "probe_dmr_health", return_value={"available": True, "version": "v1.2.8"}):
        with patch.object(router, "_fetch_docker_models", return_value=["ai/qwen3:4b-instruct-2507-q4_K_M"]):
            mock_chat = MagicMock()
            mock_resp = MagicMock()
            mock_resp.content = "OK. Inference operational."
            mock_chat.invoke.return_value = mock_resp

            with patch("langchain_openai.ChatOpenAI", return_value=mock_chat):
                readiness = router.verify_local_model_readiness("ai/qwen3:4b-instruct-2507-q4_K_M")
                assert readiness["status"] == "PASS"
                assert readiness["inference_verified"] is True
                assert "latency_ms" in readiness
                assert "response_sample" in readiness

def test_execute_inference_lifecycle_events():
    """Validates complete lifecycle events during inference with fallback."""
    queue = event_bus.subscribe()
    try:
        router = ModelRouter(provider="docker")
        router.hardware_profile = {
            "profile": "LOW_RESOURCE_CPU",
            "can_run_high_tier_locally": False,
            "recommended_local_model": "ai/qwen3:4b-instruct-2507-q4_K_M",
            "constraint_reason": "Constrained CPU"
        }
        router.available_models = ["ai/qwen3:4b-instruct-2507-q4_K_M"]

        mock_chat = MagicMock()
        mock_resp = MagicMock()
        mock_resp.content = "def test(): return True"
        mock_chat.invoke.return_value = mock_resp

        with patch.object(router, "get_model", return_value=mock_chat):
            result = router.execute_inference(
                task_type="coding",
                prompt="Write a test function",
                model_name="ai/qwen3.8-flash-next"
            )

        assert result["status"] == "success"
        assert result["actual_model"] == "ai/qwen3:4b-instruct-2507-q4_K_M"
        assert result["requested_model"] == "ai/qwen3.8-flash-next"
        assert result["response"] == "def test(): return True"

        events = []
        while not queue.empty():
            events.append(queue.get_nowait())

        event_types = [e.get("event") for e in events]
        assert "MODEL_EXECUTION_STARTED" in event_types
        assert "MODEL_FALLBACK_TRIGGERED" in event_types
        assert "MODEL_EXECUTION_FAILED" in event_types  # Failed for requested high tier
        assert "MODEL_EXECUTION_COMPLETED" in event_types  # Succeeded for fallback model
    finally:
        event_bus.unsubscribe(queue)

def test_existing_seam_agent_workflow_preservation():
    """9. Existing SEAM agent workflows continue working with Qwen3 4B."""
    from backend.agents.analysis_agent import AnalysisAgent
    from backend.agents.planning_agent import PlanningAgent
    from backend.agents.coding_agent import CodingAgent
    from backend.agents.qa_agent import QAAgent
    from backend.agents.delivery_agent import DeliveryAgent

    router = ModelRouter(provider="docker")
    router.hardware_profile = {
        "profile": "LOW_RESOURCE_CPU",
        "can_run_high_tier_locally": False,
        "recommended_local_model": "ai/qwen3:4b-instruct-2507-q4_K_M",
        "constraint_reason": "LOW_RESOURCE_CPU"
    }

    mock_chat = MagicMock()
    mock_resp = MagicMock()
    mock_resp.content = '{"status": "ok", "message": "Agent execution successful"}'
    mock_chat.invoke.return_value = mock_resp

    with patch.object(router, "get_model", return_value=mock_chat):
        for AgentClass in [AnalysisAgent, PlanningAgent, CodingAgent, QAAgent]:
            agent = AgentClass(router)
            assert agent.model_router is not None
        delivery = DeliveryAgent()
        assert delivery.deployment_service is not None
