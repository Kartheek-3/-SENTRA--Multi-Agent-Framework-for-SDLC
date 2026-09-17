from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.foundation.models import (
    AgentStatus,
    ArtifactRecord,
    ArtifactStatus,
    ManagedAgent,
    ManagedTask,
    StoredEvent,
    TaskStatus,
    utc_now,
)
from backend.foundation.store import JsonTable, runtime_dir


class EventStore:
    def __init__(self):
        self.table = JsonTable(runtime_dir / "events.json", StoredEvent, "event_id")

    def append(self, event: Dict[str, Any]) -> StoredEvent:
        rows = self.table.list()
        sequence_number = rows[-1].sequence_number + 1 if rows else 1
        stored = StoredEvent(
            event_id=event["event_id"],
            timestamp=event["timestamp"],
            project_id=event.get("project_id"),
            conversation_id=event.get("conversation_id"),
            task_id=event.get("task_id"),
            agent_id=event.get("agent_id"),
            event_type=event.get("event", event.get("event_type", "UNKNOWN")),
            payload=event,
            sequence_number=sequence_number,
        )
        self.table.upsert(stored)
        return stored

    def list(self, project_id: Optional[str] = None, conversation_id: Optional[str] = None, since: Optional[int] = None) -> List[StoredEvent]:
        events = self.table.list()
        if project_id:
            events = [event for event in events if event.project_id == project_id]
        if conversation_id:
            events = [event for event in events if event.conversation_id == conversation_id]
        if since is not None:
            events = [event for event in events if event.sequence_number > since]
        return sorted(events, key=lambda event: event.sequence_number)


class AgentManager:
    def __init__(self):
        self.table = JsonTable(runtime_dir / "agents.json", ManagedAgent, "agent_id")

    def create(self, agent: ManagedAgent) -> ManagedAgent:
        return self.table.upsert(agent)

    def list(self, project_id: Optional[str] = None) -> List[ManagedAgent]:
        return self.table.filter(project_id=project_id) if project_id else self.table.list()

    def get(self, agent_id: str) -> Optional[ManagedAgent]:
        return self.table.get(agent_id)

    def set_status(self, agent_id: str, status: AgentStatus, operation: Optional[str] = None) -> Optional[ManagedAgent]:
        def update(agent: ManagedAgent) -> ManagedAgent:
            agent.status = status
            if operation is not None:
                agent.current_operation = operation
            if status == AgentStatus.RUNNING and not agent.started_at:
                agent.started_at = utc_now()
            if status in {AgentStatus.COMPLETED, AgentStatus.FAILED, AgentStatus.CANCELLED}:
                agent.completed_at = utc_now()
            return agent

        return self.table.update(agent_id, update)


class TaskManager:
    def __init__(self):
        self.table = JsonTable(runtime_dir / "tasks.json", ManagedTask, "task_id")

    def create(self, task: ManagedTask) -> ManagedTask:
        return self.table.upsert(task)

    def list(self, project_id: Optional[str] = None) -> List[ManagedTask]:
        return self.table.filter(project_id=project_id) if project_id else self.table.list()

    def get(self, task_id: str) -> Optional[ManagedTask]:
        return self.table.get(task_id)

    def set_status(self, task_id: str, status: TaskStatus, progress: Optional[float] = None) -> Optional[ManagedTask]:
        def update(task: ManagedTask) -> ManagedTask:
            task.status = status
            if progress is not None:
                task.progress = max(0, min(100, progress))
            if status == TaskStatus.RUNNING and not task.started_at:
                task.started_at = utc_now()
            if status in {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED}:
                task.completed_at = utc_now()
            return task

        return self.table.update(task_id, update)


class ArtifactRegistry:
    def __init__(self):
        self.table = JsonTable(runtime_dir / "artifacts.json", ArtifactRecord, "artifact_id")

    def create(self, artifact: ArtifactRecord) -> ArtifactRecord:
        return self.table.upsert(artifact)

    def list(self, project_id: Optional[str] = None) -> List[ArtifactRecord]:
        return self.table.filter(project_id=project_id) if project_id else self.table.list()

    def get(self, artifact_id: str) -> Optional[ArtifactRecord]:
        return self.table.get(artifact_id)

    def set_status(self, artifact_id: str, status: ArtifactStatus) -> Optional[ArtifactRecord]:
        def update(artifact: ArtifactRecord) -> ArtifactRecord:
            artifact.status = status
            artifact.updated_at = utc_now()
            return artifact

        return self.table.update(artifact_id, update)

    def register_file(self, project_id: str, path: str, artifact_type: str = "CODE", title: Optional[str] = None, **metadata: Any) -> ArtifactRecord:
        from backend.api.projects import projects_db

        state = projects_db.get(project_id)
        if not state:
            raise ValueError("Project not found")
        project_name = metadata.pop("project_name", state.project_name)
        file_path = Path("generated_projects") / project_name / path
        if not file_path.exists() or not file_path.is_file():
            raise ValueError(f"Artifact path does not exist: {path}")
        artifact = ArtifactRecord(
            project_id=project_id,
            task_id=metadata.pop("task_id", None),
            agent_id=metadata.pop("agent_id", None),
            type=artifact_type,
            title=title or path,
            path=path.replace("\\", "/"),
            metadata={"size": file_path.stat().st_size, **metadata},
        )
        return self.create(artifact)


event_store = EventStore()
agent_manager = AgentManager()
task_manager = TaskManager()
artifact_registry = ArtifactRegistry()
