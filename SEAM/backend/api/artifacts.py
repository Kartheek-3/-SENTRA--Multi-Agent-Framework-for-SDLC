import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from backend.api.projects import projects_db
from backend.events import event_bus
from backend.foundation.models import ArtifactRecord, ArtifactStatus, ArtifactType
from backend.foundation.services import artifact_registry
from backend.utils import slugify

router = APIRouter(prefix="/api/projects", tags=["artifacts"])
registry_router = APIRouter(prefix="/artifacts", tags=["artifact-registry"])


class ArtifactCreateRequest(BaseModel):
    project_id: str
    conversation_id: str | None = None
    task_id: str | None = None
    agent_id: str | None = None
    type: ArtifactType
    title: str
    path: str | None = None
    metadata: dict = Field(default_factory=dict)


@registry_router.post("")
def create_artifact(request: ArtifactCreateRequest):
    if request.project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    if request.path:
        try:
            artifact = artifact_registry.register_file(
                request.project_id,
                request.path,
                request.type.value,
                request.title,
                task_id=request.task_id,
                agent_id=request.agent_id,
                **request.metadata,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
    else:
        artifact = artifact_registry.create(ArtifactRecord(**request.model_dump()))
    event_bus.emit_sync("ARTIFACT_REGISTERED", {
        "project_id": artifact.project_id,
        "artifact_id": artifact.artifact_id,
        "task_id": artifact.task_id,
        "agent_id": artifact.agent_id,
        "status": artifact.status,
        "summary": artifact.title,
    })
    return artifact


@registry_router.get("")
def list_registered_artifacts(project_id: str | None = None):
    return {"artifacts": artifact_registry.list(project_id)}


@registry_router.get("/{artifact_id}")
def get_registered_artifact(artifact_id: str):
    artifact = artifact_registry.get(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact


def _set_artifact_status(artifact_id: str, status: ArtifactStatus):
    artifact = artifact_registry.set_status(artifact_id, status)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    event_bus.emit_sync("ARTIFACT_STATUS_CHANGED", {
        "project_id": artifact.project_id,
        "artifact_id": artifact.artifact_id,
        "status": artifact.status,
        "summary": artifact.title,
    })
    return artifact


@registry_router.post("/{artifact_id}/approve")
def approve_artifact(artifact_id: str):
    return _set_artifact_status(artifact_id, ArtifactStatus.APPROVED)


@registry_router.post("/{artifact_id}/reject")
def reject_artifact(artifact_id: str):
    return _set_artifact_status(artifact_id, ArtifactStatus.REJECTED)

@router.get("/{project_id}/artifacts")
def list_artifacts(project_id: str):
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
        
    state = projects_db[project_id]
    project_dir = os.path.abspath(os.path.join("generated_projects", state.project_name))
    
    if not os.path.exists(project_dir):
        return {"artifacts": []}
        
    artifacts = []
    for root, dirs, files in os.walk(project_dir):
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, project_dir)
            stats = os.stat(full_path)
            artifacts.append({
                "path": rel_path.replace("\\", "/"),
                "type": "file",
                "modified": stats.st_mtime
            })
            
    return {"artifacts": artifacts, "files": artifacts}

@router.get("/{project_id}/files")
def get_file(project_id: str, path: str):
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
        
    state = projects_db[project_id]
    project_dir = os.path.abspath(os.path.join("generated_projects", state.project_name))
    
    # Security: Path traversal protection
    requested_path = os.path.abspath(os.path.join(project_dir, path))
    
    if os.path.commonpath([project_dir, requested_path]) != project_dir:
        raise HTTPException(status_code=403, detail="Path traversal detected")
        
    if not os.path.exists(requested_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    if not os.path.isfile(requested_path):
        raise HTTPException(status_code=400, detail="Path is not a file")
        
    # Return as file download/response
    return FileResponse(requested_path)
