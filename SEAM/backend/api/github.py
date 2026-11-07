import json
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request
from pydantic import BaseModel

from backend.github.intelligence_service import GitHubIntelligenceService
from backend.github.registry import RepositoryRegistry


router = APIRouter(prefix="/api/github", tags=["github"])


import os
from backend.github.github_client import GitHubClient
from backend.github.workspace_service import SafeWorkspaceService, SafeWorkspaceError

class RepositoryRequest(BaseModel):
    owner: str
    name: str

class ConnectRepositoryRequest(BaseModel):
    repo_url: str
    branch: Optional[str] = "main"

@router.get("/status")
def github_integration_status():
    has_token = bool(os.getenv("GITHUB_TOKEN"))
    return {
        "status": "CONFIGURED" if has_token else "NOT_CONFIGURED",
        "has_token": has_token,
        "token_configured": has_token,
    }

@router.post("/connect")
def connect_repository(request: ConnectRepositoryRequest):
    try:
        owner, name, canonical_url = SafeWorkspaceService.parse_github_url(request.repo_url)
    except SafeWorkspaceError as err:
        raise HTTPException(status_code=400, detail=str(err))

    client = GitHubClient()
    repo_data = client.get_repository(owner, name)
    if not repo_data:
        has_token = bool(os.getenv("GITHUB_TOKEN"))
        if not has_token:
            return {
                "status": "NOT_CONFIGURED",
                "connected": False,
                "owner": owner,
                "name": name,
                "url": canonical_url,
                "detail": "Repository not accessible. If private, GITHUB_TOKEN is NOT_CONFIGURED."
            }
        raise HTTPException(status_code=404, detail=client.last_error or "Repository not found on GitHub")

    branch = request.branch or repo_data.get("default_branch", "main")
    commit_sha = client.get_latest_commit_sha(owner, name, branch) or "HEAD"

    return {
        "status": "CONNECTED",
        "connected": True,
        "owner": owner,
        "name": name,
        "url": canonical_url,
        "default_branch": repo_data.get("default_branch", "main"),
        "selected_branch": branch,
        "commit_sha": commit_sha,
        "is_private": repo_data.get("private", False),
        "stars": repo_data.get("stargazers_count", 0),
        "language": repo_data.get("language", "Unknown"),
    }

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
