from fastapi import APIRouter

from backend.foundation.services import event_store

router = APIRouter(prefix="/events", tags=["event-store"])


@router.get("")
def list_events(project_id: str | None = None, since: int | None = None):
    return {"events": event_store.list(project_id=project_id, since=since)}


@router.get("/{project_id}")
def list_project_events(project_id: str, since: int | None = None):
    return {"events": event_store.list(project_id=project_id, since=since)}


@router.get("/replay/{conversation_id}")
def replay_conversation_events(conversation_id: str, since: int | None = None):
    return {"events": event_store.list(conversation_id=conversation_id, since=since)}
