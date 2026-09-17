from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.events import event_bus
from backend.foundation.models import AgentStatus, ManagedAgent
from backend.foundation.services import agent_manager

router = APIRouter(prefix="/agents", tags=["agent-manager"])


class AgentCreateRequest(BaseModel):
    project_id: str
    conversation_id: str | None = None
    parent_agent_id: str | None = None
    agent_type: str
    task_id: str | None = None
    model: str | None = None
    workspace: str | None = None


@router.post("")
def create_agent(request: AgentCreateRequest):
    agent = agent_manager.create(ManagedAgent(**request.model_dump()))
    event_bus.emit_sync("AGENT_CREATED", {"project_id": agent.project_id, "agent_id": agent.agent_id, "agent": agent.agent_type, "status": agent.status})
    return agent


@router.get("")
def list_agents(project_id: str | None = None):
    return {"agents": agent_manager.list(project_id)}


@router.get("/{agent_id}")
def get_agent(agent_id: str):
    agent = agent_manager.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


def _transition(agent_id: str, status: AgentStatus):
    agent = agent_manager.set_status(agent_id, status)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    event_bus.emit_sync("AGENT_STATUS_CHANGED", {"project_id": agent.project_id, "agent_id": agent.agent_id, "agent": agent.agent_type, "status": agent.status})
    return agent


@router.post("/{agent_id}/pause")
def pause_agent(agent_id: str):
    return _transition(agent_id, AgentStatus.PAUSED)


@router.post("/{agent_id}/resume")
def resume_agent(agent_id: str):
    return _transition(agent_id, AgentStatus.RUNNING)


@router.post("/{agent_id}/cancel")
def cancel_agent(agent_id: str):
    return _transition(agent_id, AgentStatus.CANCELLED)


@router.post("/{agent_id}/retry")
def retry_agent(agent_id: str):
    return _transition(agent_id, AgentStatus.QUEUED)

