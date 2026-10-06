import json
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request
from pydantic import BaseModel

from backend.github.intelligence_service import GitHubIntelligenceService
from backend.github.registry import RepositoryRegistry


router = APIRouter(prefix="/api/github", tags=["github"])


class RepositoryRequest(BaseModel):
    owner: str
    name: str


@router.get("/repositories")
def list_repositories():
    return {"repositories": [record.model_dump() for record in RepositoryRegistry().list_records()]}


@router.get("/repositories/{owner}/{name}")
def get_repository(owner: str, name: str):
    record = RepositoryRegistry().get(f"{owner}/{name}")
    if not record:
        raise HTTPException(status_code=404, detail="Repository intelligence not found")
    return record.model_dump()


@router.post("/repositories/refresh")
def refresh_repository(request: RepositoryRequest):
    record = GitHubIntelligenceService().analyze_or_refresh(request.owner, request.name)
    return record.model_dump()


@router.post("/webhook")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_github_event: Optional[str] = Header(default=None),
    x_hub_signature_256: Optional[str] = Header(default=None),
):
    body = await request.body()
    service = GitHubIntelligenceService()
    valid, reason = service.verify_webhook_signature(body, x_hub_signature_256)
    if not valid:
        raise HTTPException(status_code=401, detail=f"Invalid GitHub webhook signature: {reason}")
    if x_github_event != "push":
        return {"status": "ignored", "event": x_github_event}
    payload = json.loads(body.decode("utf-8") or "{}")
    result = service.handle_push_webhook(payload)
    if result.get("status") == "queued" and result.get("repository"):
        owner, name = result["repository"].split("/", 1)
        background_tasks.add_task(GitHubIntelligenceService().analyze_or_refresh, owner, name)
    return result
