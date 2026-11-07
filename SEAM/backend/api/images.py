"""API routes for optional visual image generation via Docker Model Runner (SDXL 1.0).

Exposes capability inspection, input validation, execution, and artifact retrieval.
Keeps visual image generation cleanly separated from the canonical Diagram Engine.
"""

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
import os

from backend.api.projects import projects_db, get_project_state
from backend.foundation.services import artifact_registry
from backend.foundation.models import ArtifactType
from backend.image_gen.models import (
    CapabilityStatus,
    ImageGenerationRequest,
    ImageGenerationResponse,
)
from backend.image_gen.provider import default_image_provider

router = APIRouter(prefix="/api/images", tags=["image-generation"])


@router.get("/capabilities", response_model=CapabilityStatus)
def get_image_generation_capabilities() -> CapabilityStatus:
    """Inspects platform, hardware, and Docker Model Runner to report image generation status."""
    return default_image_provider.check_capabilities()


@router.post("/generate", response_model=ImageGenerationResponse)
def generate_visual_asset(request: ImageGenerationRequest) -> ImageGenerationResponse:
    """Generates an illustrative visual asset (product illustration, concept art, etc.).

    Note: This is strictly for visual illustrative assets and does NOT generate
    authoritative engineering diagrams.
    """
    # 1. Project ownership / existence validation
    state = projects_db.get(request.project_id)
    if not state:
        try:
            state = get_project_state(request.project_id)
        except Exception:
            state = None

    if not state:
        raise HTTPException(
            status_code=404,
            detail=f"Project '{request.project_id}' not found. Cannot bind visual asset to unknown project."
        )

    # 2. Execute via provider
    return default_image_provider.generate_image(request)


@router.get("/gallery/{project_id}")
def list_project_visual_assets(project_id: str) -> Dict[str, Any]:
    """Retrieves all visual assets registered for the given project."""
    artifacts = artifact_registry.list(project_id)
    image_artifacts = [
        art for art in artifacts
        if art.type in {ArtifactType.IMAGE, ArtifactType.VISUAL_ASSET}
    ]
    return {
        "project_id": project_id,
        "count": len(image_artifacts),
        "visual_assets": image_artifacts,
    }
