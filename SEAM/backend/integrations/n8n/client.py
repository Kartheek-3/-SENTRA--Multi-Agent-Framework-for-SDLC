from typing import Any, Dict

import requests

from backend.integrations.n8n.config import N8NConfig
from backend.integrations.n8n.schemas import N8NWorkflowTriggerResult
from backend.integrations.n8n.security import redact_payload


class N8NClient:
    def __init__(self, config: N8NConfig):
        self.config = config

    def check_reachable(self) -> bool:
        if not self.config.base_url:
            return False
        try:
            response = requests.get(self.config.base_url, timeout=min(self.config.timeout_seconds, 3))
            return response.status_code < 500
        except requests.RequestException:
            return False

    def trigger(self, workflow: str, url: str, payload: Dict[str, Any], correlation_id: str) -> N8NWorkflowTriggerResult:
        headers = {
            "Content-Type": "application/json",
            "X-SEAM-Correlation-ID": correlation_id,
        }
        if self.config.api_key:
            headers["X-N8N-API-Key"] = self.config.api_key
        if self.config.integration_secret:
            headers["X-SEAM-Integration-Secret"] = self.config.integration_secret
        try:
            response = requests.post(
                url,
                json={"correlation_id": correlation_id, "payload": payload},
                headers=headers,
                timeout=self.config.timeout_seconds,
            )
            content = response.content[: self.config.max_response_bytes]
            parsed: Dict[str, Any] = {}
            if content:
                try:
                    parsed = response.json()
                except ValueError:
                    parsed = {"text": content.decode("utf-8", errors="replace")}
            success = 200 <= response.status_code < 300
            return N8NWorkflowTriggerResult(
                workflow=workflow,
                status="completed" if success else "failed",
                correlation_id=correlation_id,
                status_code=response.status_code,
                result_summary="n8n workflow completed" if success else "n8n workflow failed",
                response=redact_payload(parsed),
            )
        except requests.Timeout:
            return N8NWorkflowTriggerResult(
                workflow=workflow,
                status="failed",
                correlation_id=correlation_id,
                result_summary="n8n workflow timed out",
            )
        except requests.RequestException as exc:
            return N8NWorkflowTriggerResult(
                workflow=workflow,
                status="failed",
                correlation_id=correlation_id,
                result_summary=f"n8n unavailable: {exc.__class__.__name__}",
            )

    def emit_event(self, url: str, event: Dict[str, Any], correlation_id: str) -> N8NWorkflowTriggerResult:
        return self.trigger("SEAM_EVENT_ROUTER", url, event, correlation_id)
