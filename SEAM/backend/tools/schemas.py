import re
import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


SECRET_PATTERNS = [
    re.compile(r"github_pat_[A-Za-z0-9_]+"),
    re.compile(r"ghp_[A-Za-z0-9_]+"),
    re.compile(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*[^\s,;]+"),
]


class RiskLevel(str, Enum):
    READ_ONLY = "READ_ONLY"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    DESTRUCTIVE = "DESTRUCTIVE"


class ToolPermission(BaseModel):
    allowed: bool
    reason: str = ""
    requires_approval: bool = False


class ToolExecutionContext(BaseModel):
    project_id: str
    agent_name: str
    task_id: Optional[str] = None
    project_root: Optional[str] = None
    workflow_status: str = "running"
    approved: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ToolRequest(BaseModel):
    tool_name: str
    agent_name: str
    project_id: str
    input: Dict[str, Any] = Field(default_factory=dict)
    task_id: Optional[str] = None
    approved: bool = False
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class ToolErrorModel(BaseModel):
    code: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    success: bool
    tool_name: str
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    stdout: str = ""
    stderr: str = ""
    structured_data: Dict[str, Any] = Field(default_factory=dict)
    artifacts: List[str] = Field(default_factory=list)
    duration_ms: int = 0
    error: Optional[ToolErrorModel] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("stdout", "stderr")
    @classmethod
    def redact_streams(cls, value: str) -> str:
        return redact_secret(value or "")


def redact_secret(value: Any) -> Any:
    if isinstance(value, str):
        redacted = value
        for pattern in SECRET_PATTERNS:
            redacted = pattern.sub("[REDACTED]", redacted)
        return redacted
    if isinstance(value, dict):
        return {key: ("[REDACTED]" if _secret_key(key) else redact_secret(val)) for key, val in value.items()}
    if isinstance(value, list):
        return [redact_secret(item) for item in value]
    return value


def _secret_key(key: str) -> bool:
    lowered = key.lower()
    return any(term in lowered for term in ["token", "secret", "password", "authorization", "api_key", "apikey"])


def now_ms() -> int:
    return int(time.time() * 1000)
