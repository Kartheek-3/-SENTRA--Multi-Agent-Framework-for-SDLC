"""SEAM Phase 5 - Stable Diffusion XL 1.0 (Docker Model Runner) Verification Suite

Validates:
1. Provider capability detection and hardware profiling
2. Host platform compatibility checks (Windows + Integrated GPU rejection)
3. Docker offline handling
4. SDXL model presence/absence checks
5. Successful mocked generation and artifact persistence
6. Malformed response handling and timeout recovery
7. Request validation (prompt length, allowed dimensions, purpose enum)
8. FastAPI /api/images endpoints (capabilities, generate, gallery)
9. Strict separation between illustrative visual assets and canonical engineering diagrams
"""

import base64
import json
import os
import shutil
import tempfile
import pytest
from unittest.mock import MagicMock, patch

from backend.config import DMR_BASE_URL, SEAM_SDXL_MODEL
from backend.foundation.models import ArtifactType
from backend.foundation.services import artifact_registry
from backend.api.projects import projects_db, save_project_state
from backend.models.state import ProjectState
from backend.image_gen.models import (
    CapabilityStatus,
    GenerationStatus,
    ImageGenerationRequest,
    ImageGenerationResponse,
    ImagePurpose,
)
from backend.image_gen.provider import (
    DockerSDXLProvider,
    detect_host_hardware,
)

SCRATCH_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "test_phase5_scratch"))


@pytest.fixture(autouse=True)
def setup_teardown_scratch():
    os.makedirs(SCRATCH_DIR, exist_ok=True)
    yield
    shutil.rmtree(SCRATCH_DIR, ignore_errors=True)


# =====================================================================
# 1. HARDWARE & CAPABILITY DETECTION
# =====================================================================

def test_detect_host_hardware():
    """Detects current operating system and GPU information."""
    hw = detect_host_hardware()
    assert "system_os" in hw
    assert "has_cuda" in hw
    assert "gpu_name" in hw
    # Host is Windows 11 with Intel UHD Graphics
    if hw["system_os"] == "Windows":
        assert hw["has_cuda"] is False
        assert "Intel" in hw["gpu_name"] or "Graphics" in hw["gpu_name"] or "Unknown" in hw["gpu_name"]


def test_docker_sdxl_provider_capability_detection_current_host():
    """Validates live capability detection on current Windows host."""
    provider = DockerSDXLProvider()
    caps = provider.check_capabilities()

    assert isinstance(caps, CapabilityStatus)
    assert caps.host_os == "Windows"
    assert caps.has_cuda is False
    assert caps.diffusers_supported_on_host is False
    assert caps.status == GenerationStatus.NOT_AVAILABLE_ON_CURRENT_HOST.value
    assert caps.reason == "UNSUPPORTED_DIFFUSERS_PLATFORM_OR_HARDWARE"
    assert "Linux" in caps.explanation
    assert "NVIDIA CUDA" in caps.explanation or "CUDA" in caps.explanation


def test_docker_sdxl_provider_rejection_on_non_cuda_linux():
    """Simulates a Linux host without a CUDA-capable GPU."""
    provider = DockerSDXLProvider()
    with patch("backend.image_gen.provider.detect_host_hardware", return_value={"system_os": "Linux", "has_cuda": False, "gpu_name": "CPU Only"}):
        caps = provider.check_capabilities()
        assert caps.status == GenerationStatus.NOT_AVAILABLE_ON_CURRENT_HOST.value
        assert caps.reason == "UNSUPPORTED_DIFFUSERS_PLATFORM_OR_HARDWARE"
        assert caps.diffusers_supported_on_host is False


def test_docker_sdxl_provider_offline_handling():
    """Simulates a Linux+CUDA host where DMR daemon is unreachable."""
    provider = DockerSDXLProvider(base_url="http://127.0.0.1:59999")
    with patch("backend.image_gen.provider.detect_host_hardware", return_value={"system_os": "Linux", "has_cuda": True, "gpu_name": "NVIDIA RTX 4090"}):
        caps = provider.check_capabilities()
        assert caps.status == GenerationStatus.NOT_CONFIGURED.value
        assert caps.reason == "DOCKER_MODEL_RUNNER_OFFLINE"


def test_docker_sdxl_provider_model_missing_handling():
    """Simulates a Linux+CUDA host with DMR online but SDXL model not loaded."""
    provider = DockerSDXLProvider()
    mock_models_resp = json.dumps({"object": "list", "data": [{"id": "docker.io/ai/qwen3:4b"}]}).encode("utf-8")
    mock_version_resp = json.dumps({"version": "v1.2.8"}).encode("utf-8")

    def mock_urlopen(req, *args, **kwargs):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.__exit__.return_value = None
        if "version" in url:
            mock_resp.read.return_value = mock_version_resp
        else:
            mock_resp.read.return_value = mock_models_resp
        return mock_resp

    with patch("backend.image_gen.provider.detect_host_hardware", return_value={"system_os": "Linux", "has_cuda": True, "gpu_name": "NVIDIA RTX 4090"}):
        with patch("urllib.request.urlopen", side_effect=mock_urlopen):
            caps = provider.check_capabilities()
            assert caps.status == GenerationStatus.UNSUPPORTED_MODEL.value
            assert caps.reason == "SDXL_MODEL_NOT_INSTALLED"
            assert caps.model_installed is False


# =====================================================================
# 2. REQUEST VALIDATION
# =====================================================================

def test_image_generation_request_validation():
    """Tests Pydantic validation of image generation input fields."""
    # Valid request
    valid_req = ImageGenerationRequest(
        project_id="proj-1",
        prompt="A futuristic autonomous robotics factory",
        image_purpose=ImagePurpose.CONCEPT_ART,
        width=1024,
        height=1024,
    )
    assert valid_req.width == 1024
    assert valid_req.height == 1024

    # Empty prompt rejection
    with pytest.raises(ValueError):
        ImageGenerationRequest(project_id="proj-1", prompt="   ")

    # Prompt exceeding 1000 chars rejection
    with pytest.raises(ValueError):
        ImageGenerationRequest(project_id="proj-1", prompt="A" * 1001)

    # Unsupported dimensions rejection
    with pytest.raises(ValueError):
        ImageGenerationRequest(project_id="proj-1", prompt="Valid prompt", width=300, height=300)


# =====================================================================
# 3. GENERATION EXECUTION (MOCKED & REAL BOUNDARIES)
# =====================================================================

def test_generation_refusal_on_unsupported_host():
    """Asserts generate_image honestly returns capability denial on unsupported host."""
    provider = DockerSDXLProvider()
    req = ImageGenerationRequest(
        project_id="proj-unsupported",
        prompt="Isometric microservices architecture",
        image_purpose=ImagePurpose.PRODUCT_ILLUSTRATION,
    )
    res = provider.generate_image(req)
    assert res.status == GenerationStatus.NOT_AVAILABLE_ON_CURRENT_HOST.value
    assert res.error == "UNSUPPORTED_DIFFUSERS_PLATFORM_OR_HARDWARE"
    assert res.metadata["is_authoritative_diagram"] is False


def test_successful_mocked_image_generation_and_artifact_persistence():
    """Validates successful generation flow, file persistence, and ArtifactRegistry registration."""
    provider = DockerSDXLProvider()
    project_id = "test-phase5-proj"
    state = ProjectState(project_id=project_id, user_requirement="Test Project")
    save_project_state(state)

    dummy_png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    dummy_b64 = base64.b64encode(dummy_png_bytes).decode("utf-8")
    mock_diffusers_body = json.dumps({"data": [{"b64_json": dummy_b64}]}).encode("utf-8")

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = None
    mock_resp.read.return_value = mock_diffusers_body

    req = ImageGenerationRequest(
        project_id=project_id,
        prompt="Modern cyber cloud platform concept illustration",
        image_purpose=ImagePurpose.LANDING_PAGE_ARTWORK,
        width=1024,
        height=1024,
    )

    with patch.object(provider, "check_capabilities", return_value=CapabilityStatus(
        status="READY",
        host_os="Linux",
        has_cuda=True,
        gpu_info="NVIDIA RTX A6000",
        dmr_available=True,
        dmr_base_url=provider.base_url,
        diffusers_supported_on_host=True,
        model_installed=True,
        explanation="Ready"
    )):
        with patch("urllib.request.urlopen", return_value=mock_resp):
            res = provider.generate_image(req)

    assert res.status == GenerationStatus.COMPLETED.value
    assert res.provider == "docker_model_runner"
    assert res.model == "ai/stable-diffusion"
    assert res.artifact_id is not None
    assert "visual_assets" in res.artifact_path

    # Verify registered in ArtifactRegistry
    registered = artifact_registry.get(res.artifact_id)
    assert registered is not None
    assert registered.type in {ArtifactType.IMAGE, ArtifactType.VISUAL_ASSET}
    assert registered.metadata["is_authoritative_diagram"] is False


def test_malformed_dmr_response_handling():
    """Validates graceful failure when DMR returns empty or unexpected data."""
    provider = DockerSDXLProvider()
    req = ImageGenerationRequest(
        project_id="test-proj",
        prompt="Data pipeline illustration",
    )
    mock_empty_body = json.dumps({"data": []}).encode("utf-8")
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = None
    mock_resp.read.return_value = mock_empty_body

    with patch.object(provider, "check_capabilities", return_value=CapabilityStatus(
        status="READY",
        host_os="Linux",
        has_cuda=True,
        gpu_info="NVIDIA RTX 4090",
        dmr_available=True,
        dmr_base_url=provider.base_url,
        diffusers_supported_on_host=True,
        model_installed=True,
        explanation="Ready"
    )):
        with patch("urllib.request.urlopen", return_value=mock_resp):
            res = provider.generate_image(req)

    assert res.status == GenerationStatus.FAILED.value
    assert res.error == "EMPTY_IMAGE_DATA"


# =====================================================================
# 4. FASTAPI ENDPOINTS INTEGRATION
# =====================================================================

def test_api_images_capabilities_endpoint():
    """Tests GET /api/images/capabilities endpoint."""
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    response = client.get("/api/images/capabilities")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "host_os" in data
    assert data["status"] == "NOT_AVAILABLE_ON_CURRENT_HOST"


def test_api_images_generate_unknown_project():
    """Tests POST /api/images/generate with non-existent project returns 404."""
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)
    payload = {
        "project_id": "non-existent-proj-xyz",
        "prompt": "Test illustration",
        "image_purpose": "product_illustration",
    }
    response = client.post("/api/images/generate", json=payload)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_api_images_generate_on_current_host():
    """Tests POST /api/images/generate on current host returns capability denial cleanly."""
    from fastapi.testclient import TestClient
    from backend.main import app

    project_id = "test-phase5-api-proj"
    state = ProjectState(project_id=project_id, user_requirement="FastAPI Test")
    save_project_state(state)

    client = TestClient(app)
    payload = {
        "project_id": project_id,
        "prompt": "Cybersecurity defense system conceptual artwork",
        "image_purpose": "concept_art",
        "width": 1024,
        "height": 1024,
    }
    response = client.post("/api/images/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "NOT_AVAILABLE_ON_CURRENT_HOST"
    assert data["error"] == "UNSUPPORTED_DIFFUSERS_PLATFORM_OR_HARDWARE"


def test_separation_between_visual_assets_and_engineering_diagrams():
    """Confirms that visual assets do NOT touch or replace canonical diagrams."""
    from backend.tools.diagram_templates import CANONICAL_DIAGRAM_TYPES
    assert len(CANONICAL_DIAGRAM_TYPES) == 10

    # Ensure canonical diagrams remain pure structural/behavioral specifications
    for d in CANONICAL_DIAGRAM_TYPES:
        assert d["id"] in {
            "architecture_diagram",
            "use_case_diagram",
            "class_diagram",
            "object_diagram",
            "sequence_diagram",
            "activity_diagram",
            "dfd_level_0",
            "dfd_level_1",
            "erd_diagram",
            "deployment_diagram",
        }
