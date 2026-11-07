"""Provider abstraction and Docker SDXL 1.0 implementation with hardware capability detection.

Adheres strictly to SEAM principles:
1. Canonical Diagram Engine remains the single source of truth for engineering specifications.
2. SDXL outputs are explicitly classified as visual illustrative assets.
3. Accurate detection and honest reporting of hardware/platform constraints (Windows + Integrated GPU).
4. No automated multi-gigabyte model downloads on incompatible hosts.
5. Zero cloud fallback.
"""

from abc import ABC, abstractmethod
import base64
import hashlib
import json
import os
import platform
import subprocess
import time
from typing import Any, Dict, List, Optional
import urllib.request
import urllib.error

from backend.config import (
    DMR_BASE_URL,
    SEAM_SDXL_MODEL,
    SEAM_IMAGE_TIMEOUT_SECONDS,
)
from backend.events import event_bus
from backend.foundation.services import artifact_registry
from backend.foundation.models import ArtifactType
from backend.image_gen.models import (
    CapabilityStatus,
    GenerationStatus,
    ImageArtifactMetadata,
    ImageGenerationRequest,
    ImageGenerationResponse,
    ProviderCapabilityInfo,
)


def detect_host_hardware() -> Dict[str, Any]:
    """Detects current operating system, GPU vendor, and CUDA capabilities."""
    system_os = platform.system()
    has_cuda = False
    gpu_name = "Unknown Graphics"

    # 1. Check Python PyTorch if available
    try:
        import torch
        has_cuda = bool(torch.cuda.is_available())
        if has_cuda:
            gpu_name = torch.cuda.get_device_name(0)
    except Exception:
        has_cuda = False

    # 2. Check via nvidia-smi if torch not installed or CPU-only
    if not has_cuda:
        try:
            res = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"], capture_output=True, text=True, timeout=2, check=False)
            if res.returncode == 0 and res.stdout.strip():
                gpu_name = res.stdout.strip().splitlines()[0]
                has_cuda = True
        except Exception:
            pass

    # 3. On Windows without CUDA, identify the actual display adapter (e.g. Intel UHD)
    if not has_cuda and system_os == "Windows":
        try:
            # Query PowerShell Get-CimInstance for video controller
            ps_cmd = ["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name"]
            res = subprocess.run(ps_cmd, capture_output=True, text=True, timeout=3, check=False)
            if res.returncode == 0 and res.stdout.strip():
                gpu_name = res.stdout.strip().splitlines()[0]
        except Exception:
            gpu_name = "Intel(R) UHD Graphics / Integrated"

    return {
        "system_os": system_os,
        "has_cuda": has_cuda,
        "gpu_name": gpu_name,
    }


class ImageGenerationProvider(ABC):
    """Abstract base provider for image generation."""

    @abstractmethod
    def check_capabilities(self) -> CapabilityStatus:
        """Inspects host, daemon, engine, and models to determine availability."""
        pass

    @abstractmethod
    def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResponse:
        """Executes image generation or returns honest capability denial."""
        pass


class DockerSDXLProvider(ImageGenerationProvider):
    """Docker Model Runner implementation for Stable Diffusion XL 1.0 (ai/stable-diffusion)."""

    def __init__(self, base_url: Optional[str] = None, timeout_seconds: Optional[int] = None):
        self.base_url = (base_url or DMR_BASE_URL).rstrip("/")
        self.timeout_seconds = timeout_seconds or SEAM_IMAGE_TIMEOUT_SECONDS
        self.diffusers_endpoint = f"{self.base_url}/engines/diffusers/v1/images/generations"

    def check_capabilities(self) -> CapabilityStatus:
        """Checks platform and Docker Model Runner capabilities."""
        hw = detect_host_hardware()
        system_os = hw["system_os"]
        has_cuda = hw["has_cuda"]
        gpu_name = hw["gpu_name"]

        dmr_available = False
        dmr_version = None
        installed_models: List[str] = []
        model_installed = False

        # 1. Probe Docker Model Runner daemon on configured port (12434)
        try:
            req = urllib.request.Request(f"{self.base_url}/version", method="GET")
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    dmr_available = True
                    body = json.loads(resp.read().decode("utf-8"))
                    dmr_version = body.get("version")
        except Exception:
            dmr_available = False

        # 2. Check installed models catalog if DMR is reachable
        if dmr_available:
            try:
                req = urllib.request.Request(f"{self.base_url}/v1/models", method="GET")
                with urllib.request.urlopen(req, timeout=2) as resp:
                    if resp.status == 200:
                        body = json.loads(resp.read().decode("utf-8"))
                        for item in body.get("data", []):
                            mid = item.get("id", "")
                            installed_models.append(mid)
                            if "stable-diffusion" in mid or SEAM_SDXL_MODEL in mid:
                                model_installed = True
            except Exception:
                pass

        # 3. Assess Docker Diffusers engine compatibility:
        # Docker's documented Diffusers backend is not supported on Windows and does not support CPU-only inference.
        # It requires a Linux host with an NVIDIA CUDA-capable GPU.
        diffusers_supported_on_host = (system_os == "Linux") and has_cuda

        if not diffusers_supported_on_host:
            status = GenerationStatus.NOT_AVAILABLE_ON_CURRENT_HOST.value
            reason = "UNSUPPORTED_DIFFUSERS_PLATFORM_OR_HARDWARE"
            explanation = (
                f"Docker Model Runner Diffusers backend is not supported on {system_os} with {gpu_name}. "
                "Local Stable Diffusion XL 1.0 requires a Linux host with an NVIDIA CUDA-capable GPU. "
                "Visual image generation is disabled on this host to prevent system instability."
            )
        elif not dmr_available:
            status = GenerationStatus.NOT_CONFIGURED.value
            reason = "DOCKER_MODEL_RUNNER_OFFLINE"
            explanation = f"Docker Model Runner is not reachable at {self.base_url}."
        elif not model_installed:
            status = GenerationStatus.UNSUPPORTED_MODEL.value
            reason = "SDXL_MODEL_NOT_INSTALLED"
            explanation = f"Docker Model Runner is active but '{SEAM_SDXL_MODEL}' is not currently loaded in catalog."
        else:
            status = GenerationStatus.READY.value
            reason = None
            explanation = "Docker Model Runner SDXL provider is ready for image generation."

        provider_info = ProviderCapabilityInfo(
            id="docker_sdxl",
            name="Docker SDXL 1.0 (ai/stable-diffusion)",
            status=status,
            reason=reason,
            supported=diffusers_supported_on_host and dmr_available and model_installed,
        )

        return CapabilityStatus(
            status=status,
            reason=reason,
            host_os=system_os,
            has_cuda=has_cuda,
            gpu_info=gpu_name,
            dmr_available=dmr_available,
            dmr_base_url=self.base_url,
            dmr_version=dmr_version,
            installed_models=installed_models,
            diffusers_supported_on_host=diffusers_supported_on_host,
            model_installed=model_installed,
            supported_providers=[provider_info],
            explanation=explanation,
        )

    def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResponse:
        """Executes image generation via Docker Model Runner or reports unavailability."""
        caps = self.check_capabilities()

        # If host cannot support Diffusers or DMR is unavailable, report honestly
        if not caps.diffusers_supported_on_host or caps.status != GenerationStatus.READY.value:
            event_bus.emit_sync("IMAGE_GENERATION_UNAVAILABLE", {
                "project_id": request.project_id,
                "provider": "docker_model_runner",
                "model": request.model,
                "status": caps.status,
                "reason": caps.reason,
                "host_os": caps.host_os,
                "gpu_info": caps.gpu_info,
            })
            return ImageGenerationResponse(
                status=caps.status,
                provider="docker_model_runner",
                model=request.model,
                generation_method="image_inference",
                error=caps.reason or "IMAGE_GENERATION_UNAVAILABLE",
                message=caps.explanation,
                metadata={
                    "host_os": caps.host_os,
                    "gpu_info": caps.gpu_info,
                    "has_cuda": caps.has_cuda,
                    "is_authoritative_diagram": False,
                }
            )

        # Notify generation start
        start_time = time.time()
        event_bus.emit_sync("IMAGE_GENERATION_STARTED", {
            "project_id": request.project_id,
            "provider": "docker_model_runner",
            "model": request.model,
            "prompt": request.prompt[:100],
            "purpose": request.image_purpose.value,
            "width": request.width,
            "height": request.height,
        })

        payload: Dict[str, Any] = {
            "model": request.model,
            "prompt": request.prompt,
            "size": f"{request.width}x{request.height}",
            "n": 1,
            "response_format": "b64_json",
        }
        if request.negative_prompt:
            payload["negative_prompt"] = request.negative_prompt

        try:
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self.diffusers_endpoint,
                data=req_data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                resp_body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as http_err:
            err_msg = http_err.read().decode("utf-8", errors="replace")
            event_bus.emit_sync("IMAGE_GENERATION_FAILED", {
                "project_id": request.project_id,
                "error": f"HTTP {http_err.code}: {err_msg}",
            })
            return ImageGenerationResponse(
                status=GenerationStatus.FAILED.value,
                provider="docker_model_runner",
                model=request.model,
                error=f"HTTP_{http_err.code}",
                message=f"Docker Diffusers endpoint error: {err_msg}",
            )
        except Exception as exc:
            event_bus.emit_sync("IMAGE_GENERATION_FAILED", {
                "project_id": request.project_id,
                "error": str(exc),
            })
            return ImageGenerationResponse(
                status=GenerationStatus.FAILED.value,
                provider="docker_model_runner",
                model=request.model,
                error="NETWORK_OR_TIMEOUT_ERROR",
                message=f"Failed to communicate with Docker Model Runner: {str(exc)}",
            )

        # Extract b64 or url from OpenAI-compatible image response
        data_items = resp_body.get("data", [])
        if not data_items:
            return ImageGenerationResponse(
                status=GenerationStatus.FAILED.value,
                provider="docker_model_runner",
                model=request.model,
                error="EMPTY_IMAGE_DATA",
                message="Docker Model Runner returned an empty image list.",
            )

        first_item = data_items[0]
        b64_data = first_item.get("b64_json")
        image_bytes = base64.b64decode(b64_data) if b64_data else b""
        file_hash = hashlib.sha256(image_bytes).hexdigest() if image_bytes else None

        # Persist visual asset into project directory
        from backend.api.projects import projects_db
        state = projects_db.get(request.project_id)
        proj_name = state.project_name if state else request.project_id
        assets_dir = os.path.join("generated_projects", proj_name, "visual_assets")
        os.makedirs(assets_dir, exist_ok=True)

        asset_filename = f"{request.image_purpose.value}_{int(time.time())}.png"
        rel_path = os.path.join("visual_assets", asset_filename).replace("\\", "/")
        abs_path = os.path.join(assets_dir, asset_filename)

        if image_bytes:
            with open(abs_path, "wb") as f:
                f.write(image_bytes)

        # Register in ArtifactRegistry as IMAGE artifact
        artifact = artifact_registry.register_file(
            project_id=request.project_id,
            path=rel_path,
            artifact_type=ArtifactType.IMAGE.value,
            title=f"Visual Asset: {request.image_purpose.value.replace('_', ' ').title()}",
            provider="docker_model_runner",
            model=request.model,
            width=request.width,
            height=request.height,
            image_purpose=request.image_purpose.value,
            file_hash=file_hash,
            is_authoritative_diagram=False,
        )

        metadata = ImageArtifactMetadata(
            project_id=request.project_id,
            artifact_id=artifact.artifact_id,
            provider="docker_model_runner",
            model=request.model,
            width=request.width,
            height=request.height,
            image_purpose=request.image_purpose.value,
            generation_status="COMPLETED",
            file_path=rel_path,
            file_hash=file_hash,
            is_authoritative_diagram=False,
        ).model_dump()

        event_bus.emit_sync("IMAGE_GENERATION_COMPLETED", {
            "project_id": request.project_id,
            "artifact_id": artifact.artifact_id,
            "path": rel_path,
            "duration": time.time() - start_time,
        })
        event_bus.emit_sync("IMAGE_ARTIFACT_PERSISTED", {
            "project_id": request.project_id,
            "artifact_id": artifact.artifact_id,
            "path": rel_path,
            "purpose": request.image_purpose.value,
        })

        return ImageGenerationResponse(
            status=GenerationStatus.COMPLETED.value,
            provider="docker_model_runner",
            model=request.model,
            artifact_id=artifact.artifact_id,
            artifact_path=rel_path,
            generation_method="image_inference",
            image_base64=b64_data,
            metadata=metadata,
        )


# Singleton provider instance
default_image_provider = DockerSDXLProvider()
