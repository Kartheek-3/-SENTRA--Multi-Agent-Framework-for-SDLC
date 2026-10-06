from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


N8NEventType = Literal[
    "github.push",
    "jira.issue_created",
    "external.issue_created",
    "qa.failed",
    "delivery.completed",
]


class N8NWorkflowTriggerRequest(BaseModel):
    workflow: str = Field(min_length=1, max_length=80)
    payload: Dict[str, Any] = Field(default_factory=dict)
    project_id: Optional[str] = None
    correlation_id: str = Field(default_factory=lambda: str(uuid4()))

    @field_validator("workflow")
    @classmethod
    def workflow_is_safe(cls, value: str) -> str:
        if not value.replace("_", "").replace("-", "").replace(".", "").isalnum():
            raise ValueError("workflow contains unsupported characters")
        return value


class N8NWorkflowTriggerResult(BaseModel):
    workflow: str
    status: Literal["completed", "failed"]
    correlation_id: str
    status_code: Optional[int] = None
    result_summary: str
    response: Optional[Dict[str, Any]] = None


class N8NWebhookEvent(BaseModel):
    event_type: N8NEventType
    correlation_id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: Optional[str] = None
    source: str = Field(default="n8n", max_length=80)
    payload: Dict[str, Any] = Field(default_factory=dict)


class N8NEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str = Field(min_length=1, max_length=120)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    project_id: Optional[str] = None
    task_id: Optional[str] = None
    status: str = "PENDING"
    payload: Dict[str, Any] = Field(default_factory=dict)
    source: str = "SEAM"
    correlation_id: str = Field(default_factory=lambda: str(uuid4()))


class N8NIntegrationRecord(BaseModel):
    provider: str = "n8n"
    direction: Literal["inbound", "outbound"]
    workflow: str
    status: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    correlation_id: str
    result_summary: str = ""


class N8NStatus(BaseModel):
    configured: bool
    enabled: bool
    reachable: bool
    base_url: str = ""
    authentication_configured: bool
    allowed_workflows: list[str]
    allowed_event_types: list[str] = Field(default_factory=list)
    workflow_config_status: Dict[str, str] = Field(default_factory=dict)
    last_successful_interaction: Optional[str] = None
    last_success: Optional[str] = None
    last_failure: Optional[str] = None
    last_event_type: Optional[str] = None
