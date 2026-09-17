from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.events import event_bus
from backend.foundation.models import ManagedTask, TaskStatus
from backend.foundation.services import task_manager

router = APIRouter(prefix="/tasks", tags=["task-groups"])


class TaskCreateRequest(BaseModel):
    project_id: str
    parent_task_id: str | None = None
    title: str
    description: str = ""
    agent_id: str | None = None
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 0
    dependencies: list[str] = []


@router.post("")
def create_task(request: TaskCreateRequest):
    task = task_manager.create(ManagedTask(**request.model_dump()))
    event_bus.emit_sync("TASK_REGISTERED", {"project_id": task.project_id, "task_id": task.task_id, "status": task.status, "summary": task.title})
    return task


@router.get("")
def list_tasks(project_id: str | None = None):
    return {"tasks": task_manager.list(project_id)}


@router.get("/{task_id}")
def get_task(task_id: str):
    task = task_manager.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/{task_id}/status/{status}")
def set_task_status(task_id: str, status: TaskStatus):
    task = task_manager.set_status(task_id, status)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    event_bus.emit_sync("TASK_STATUS_CHANGED", {"project_id": task.project_id, "task_id": task.task_id, "status": task.status, "summary": task.title})
    return task

