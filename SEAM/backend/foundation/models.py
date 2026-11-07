from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AgentStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    READY = "READY"
    RUNNING = "RUNNING"
    BLOCKED = "BLOCKED"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ArtifactStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class ArtifactType(str, Enum):
    ANALYSIS = "ANALYSIS"
    DESIGN = "DESIGN"
    PLAN = "PLAN"
    REQUIREMENTS = "REQUIREMENTS"
    ARCHITECTURE = "ARCHITECTURE"
    DATABASE = "DATABASE"
    API = "API"
    CODE = "CODE"
    DIFF = "DIFF"
    QA = "QA"
    QA_REPORT = "QA_REPORT"
    TEST = "TEST"
    SECURITY = "SECURITY"
    PERFORMANCE = "PERFORMANCE"
    BROWSER = "BROWSER"
    SCREENSHOT = "SCREENSHOT"
    RECORDING = "RECORDING"
    DIAGRAM = "DIAGRAM"
    IMAGE = "IMAGE"
    VISUAL_ASSET = "VISUAL_ASSET"
    DOCUMENTATION = "DOCUMENTATION"
    DEPLOYMENT = "DEPLOYMENT"
    DELIVERY = "DELIVERY"
    KNOWLEDGE = "KNOWLEDGE"
    ERROR = "ERROR"
    WALKTHROUGH = "WALKTHROUGH"
    SUMMARY = "SUMMARY"


class ManagedAgent(BaseModel):
    agent_id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    conversation_id: Optional[str] = None
    parent_agent_id: Optional[str] = None
    agent_type: str
    task_id: Optional[str] = None
    status: AgentStatus = AgentStatus.QUEUED
    model: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    current_operation: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)
    workspace: Optional[str] = None
    artifacts: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class ManagedTask(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    parent_task_id: Optional[str] = None
    title: str
    description: str = ""
    agent_id: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 0
    dependencies: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress: float = 0
    artifacts: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class ArtifactRecord(BaseModel):
    artifact_id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    conversation_id: Optional[str] = None
    task_id: Optional[str] = None
    agent_id: Optional[str] = None
    type: ArtifactType
    title: str
    path: Optional[str] = None
    status: ArtifactStatus = ArtifactStatus.AVAILABLE
    created_at: str = Field(default_factory=utc_now)
    updated_at: str = Field(default_factory=utc_now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StoredEvent(BaseModel):
    event_id: str
    timestamp: str
    project_id: Optional[str] = None
    conversation_id: Optional[str] = None
    task_id: Optional[str] = None
    agent_id: Optional[str] = None
    event_type: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    sequence_number: int
