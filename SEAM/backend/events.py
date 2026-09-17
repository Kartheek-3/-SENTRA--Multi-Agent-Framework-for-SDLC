import asyncio
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List

class EventBus:
    def __init__(self):
        self.subscribers: List[asyncio.Queue] = []
        
    def subscribe(self) -> asyncio.Queue:
        queue = asyncio.Queue()
        self.subscribers.append(queue)
        return queue
        
    def unsubscribe(self, queue: asyncio.Queue):
        if queue in self.subscribers:
            self.subscribers.remove(queue)
            
    def emit_sync(self, event_type: str, payload: Dict[str, Any]):
        event = {
            "event_id": payload.get("event_id") or str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event_type,
            **payload
        }
        self._sync_foundation(event)
        try:
            from backend.foundation.services import event_store
            stored_event = event_store.append(event)
            event["sequence_number"] = stored_event.sequence_number
        except Exception:
            pass
        self._persist_event(event)
        for queue in self.subscribers:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                pass

    async def emit(self, event_type: str, payload: Dict[str, Any]):
        self.emit_sync(event_type, payload)

    def _persist_event(self, event: Dict[str, Any]):
        project_id = event.get("project_id")
        if not project_id:
            return
        try:
            from backend.api.projects import projects_db
            state = projects_db.get(project_id)
            if not state:
                return
            log_dir = os.path.join("generated_projects", state.project_name, "logs")
            os.makedirs(log_dir, exist_ok=True)
            safe_event = {
                "event_id": event.get("event_id"),
                "timestamp": event.get("timestamp"),
                "event": event.get("event"),
                "agent": event.get("agent"),
                "task_id": event.get("task_id"),
                "status": event.get("status"),
                "path": event.get("path"),
                "operation": event.get("operation"),
                "summary": event.get("summary"),
                "error": event.get("error"),
            }
            with open(os.path.join(log_dir, "execution_events.jsonl"), "a", encoding="utf-8") as handle:
                handle.write(json.dumps({k: v for k, v in safe_event.items() if v is not None}) + "\n")
        except Exception:
            pass

    def _sync_foundation(self, event: Dict[str, Any]):
        project_id = event.get("project_id")
        if not project_id:
            return
        try:
            from backend.foundation.models import AgentStatus, TaskStatus
            from backend.foundation.services import agent_manager, task_manager

            event_type = event.get("event")
            agent_type = event.get("agent")
            task_id = event.get("task_id")
            agent = None
            if agent_type:
                for candidate in agent_manager.list(project_id):
                    if candidate.agent_type == agent_type:
                        agent = candidate
                        event["agent_id"] = candidate.agent_id
                        break

            if event_type == "AGENT_STARTED" and agent:
                agent_manager.set_status(agent.agent_id, AgentStatus.RUNNING, "Running workflow node")
            elif event_type == "AGENT_COMPLETED" and agent:
                agent_manager.set_status(agent.agent_id, AgentStatus.COMPLETED, "Completed workflow node")
            elif event_type == "WORKFLOW_FAILED" and agent:
                agent_manager.set_status(agent.agent_id, AgentStatus.FAILED, "Workflow failed")

            if task_id:
                if event_type == "TASK_STARTED":
                    task_manager.set_status(task_id, TaskStatus.RUNNING, 0)
                elif event_type == "TASK_COMPLETED":
                    task_manager.set_status(task_id, TaskStatus.COMPLETED, 100)
        except Exception:
            pass

# Global singleton event bus
event_bus = EventBus()
