"""Pydantic data models for optional image generation via Docker Model Runner (SDXL 1.0).

These models separate illustrative visual assets from validated engineering diagrams.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class ImagePurpose(str, Enum):
    PRODUCT_ILLUSTRATION = "product_illustration"
    CONCEPT_ART = "concept_art"
    PRESENTATION_VISUAL = "presentation_visual"
    LANDING_PAGE_ARTWORK = "landing_page_artwork"
    ABSTRACT_SYSTEM_VISUALIZATION = "abstract_system_visualization"
    DECORATIVE_ARCHITECTURE_CONCEPT = "decorative_architecture_concept"
    SUPPORTING_VISUAL_ASSET = "supporting_visual_asset"


class GenerationStatus(str, Enum):
    CHECKING_PROVIDER = "CHECKING_PROVIDER"
    READY = "READY"
    GENERATING = "GENERATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    NOT_AVAILABLE_ON_CURRENT_HOST = "NOT_AVAILABLE_ON_CURRENT_HOST"
    UNSUPPORTED_MODEL = "UNSUPPORTED_MODEL"
    TIMEOUT = "TIMEOUT"


ALLOWED_DIMENSIONS = {512, 768, 832, 896, 1024, 1152, 1216}


class ImageGenerationRequest(BaseModel):
    project_id: str = Field(..., description="Project identifier to bind generated image")
    prompt: str = Field(..., min_length=1, max_length=1000, description="Image generation prompt text")
    image_purpose: ImagePurpose = Field(default=ImagePurpose.PRODUCT_ILLUSTRATION, description="Classification of visual asset")
    width: int = Field(default=1024, description="Image width in pixels")
    height: int = Field(default=1024, description="Image height in pixels")
    model: str = Field(default="ai/stable-diffusion", description="Docker Hub model identifier")
    negative_prompt: Optional[str] = Field(default=None, max_length=500, description="Optional negative prompt")
    steps: Optional[int] = Field(default=30, ge=1, le=100)
    guidance_scale: Optional[float] = Field(default=7.5, ge=1.0, le=20.0)
    seed: Optional[int] = Field(default=None)

    @field_validator("width", "height")
    @classmethod
    def validate_dimension(cls, v: int) -> int:
        if v not in ALLOWED_DIMENSIONS:
            raise ValueError(f"Dimension {v} not in supported SDXL sizes: {sorted(list(ALLOWED_DIMENSIONS))}")
        return v

    @field_validator("prompt")
    @classmethod
    def validate_prompt_not_empty(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Prompt must contain non-whitespace text.")
        return s


class ImageArtifactMetadata(BaseModel):
    project_id: str
    artifact_id: str
    provider: str = "docker_model_runner"
    model: str = "ai/stable-diffusion"
    generation_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    width: int
    height: int
    image_purpose: str
    generation_status: str
    file_path: str
    file_hash: Optional[str] = None
    is_authoritative_diagram: bool = False  # Explicitly distinguished from canonical diagrams


class ImageGenerationResponse(BaseModel):
    status: str
    provider: str = "docker_model_runner"
    model: str = "ai/stable-diffusion"
    artifact_id: Optional[str] = None
    artifact_path: Optional[str] = None
    generation_method: str = "image_inference"
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    message: Optional[str] = None


class ProviderCapabilityInfo(BaseModel):
    id: str
    name: str
    status: str
    reason: Optional[str] = None
    supported: bool = False


class CapabilityStatus(BaseModel):
    status: str
    reason: Optional[str] = None
    host_os: str
    has_cuda: bool = False
    gpu_info: str
    dmr_available: bool = False
    dmr_base_url: str
    dmr_version: Optional[str] = None
    installed_models: List[str] = Field(default_factory=list)
    diffusers_supported_on_host: bool = False
    model_installed: bool = False
    supported_providers: List[ProviderCapabilityInfo] = Field(default_factory=list)
    explanation: str
