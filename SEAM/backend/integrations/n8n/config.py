import os
from dataclasses import dataclass, field
from typing import Dict, Optional, Set
from urllib.parse import urlparse


def _parse_workflows(raw: str, default_url: str = "") -> Dict[str, str]:
    workflows: Dict[str, str] = {}
    if default_url:
        workflows["default"] = default_url
    for item in [part.strip() for part in raw.split(",") if part.strip()]:
        if "=" not in item:
            continue
        name, url = item.split("=", 1)
        workflows[name.strip()] = url.strip()
    return workflows


DEFAULT_ALLOWED_EVENT_TYPES = {
    "DEFECT_LOCALIZED",
    "DELIVERY_COMPLETED",
    "DELIVERY_BLOCKED",
    "EVALUATION_COMPLETED",
    "EXPERIMENT_COMPLETED",
    "DEFECT_RESOLVED",
    "DEFECT_REMAINING",
    "GITHUB_CONTEXT_REFRESHED",
    "RELEASE_BLOCKED",
    "FIGMA_CONTEXT_UPDATED",
    "FRONTEND_REQUIREMENT_READY",
    "CICD_REQUESTED",
}


@dataclass(frozen=True)
class N8NConfig:
    base_url: str = ""
    webhook_url: str = ""
    api_key: str = ""
    allowed_workflows: Dict[str, str] = field(default_factory=dict)
    timeout_seconds: float = 8
    max_response_bytes: int = 65536
    require_https: bool = False
    integration_secret: str = ""
    seam_api_url: str = ""
    allowed_event_types: Set[str] = field(default_factory=set)

    def __post_init__(self):
        base_url = self.base_url or os.getenv("N8N_BASE_URL", "")
        webhook_url = self.webhook_url or os.getenv("N8N_WEBHOOK_URL", "")
        api_key = self.api_key or os.getenv("N8N_API_KEY", "")
        timeout_seconds = self.timeout_seconds
        if timeout_seconds == 8:
            timeout_seconds = float(os.getenv("N8N_TIMEOUT_SECONDS", "8"))
        max_response_bytes = self.max_response_bytes
        if max_response_bytes == 65536:
            max_response_bytes = int(os.getenv("N8N_MAX_RESPONSE_BYTES", "65536"))
        require_https = self.require_https or os.getenv("N8N_REQUIRE_HTTPS", "false").lower() == "true"
        integration_secret = self.integration_secret or os.getenv("SEAM_N8N_INTEGRATION_SECRET", "") or os.getenv("N8N_API_KEY", "")
        seam_api_url = self.seam_api_url or os.getenv("SEAM_API_URL", "http://127.0.0.1:8000")
        allowed_event_types = self.allowed_event_types or {
            item.strip()
            for item in os.getenv("N8N_ALLOWED_EVENT_TYPES", ",".join(sorted(DEFAULT_ALLOWED_EVENT_TYPES))).split(",")
            if item.strip()
        }
        object.__setattr__(self, "base_url", base_url.strip().rstrip("/"))
        object.__setattr__(self, "webhook_url", webhook_url.strip())
        object.__setattr__(self, "api_key", api_key.strip())
        object.__setattr__(self, "timeout_seconds", timeout_seconds)
        object.__setattr__(self, "max_response_bytes", max_response_bytes)
        object.__setattr__(self, "require_https", require_https)
        object.__setattr__(self, "integration_secret", integration_secret.strip())
        object.__setattr__(self, "seam_api_url", seam_api_url.strip().rstrip("/"))
        object.__setattr__(self, "allowed_event_types", allowed_event_types)
        workflows = self.allowed_workflows or _parse_workflows(os.getenv("N8N_ALLOWED_WORKFLOWS", ""), webhook_url.strip())
        object.__setattr__(
            self,
            "allowed_workflows",
            workflows,
        )

    @property
    def configured(self) -> bool:
        return bool(self.allowed_workflows)

    @property
    def authentication_configured(self) -> bool:
        return bool(self.api_key or self.integration_secret)

    def workflow_url(self, workflow: str) -> Optional[str]:
        return self.allowed_workflows.get(workflow)

    def validate_url(self, url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return False
        if self.require_https and parsed.scheme != "https":
            return False
        if parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1"}:
            return False
        return True


def get_n8n_config() -> N8NConfig:
    return N8NConfig()
