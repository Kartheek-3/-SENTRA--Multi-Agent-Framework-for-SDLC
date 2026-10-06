from datetime import datetime, timezone
from typing import Dict, Optional

from backend.events import event_bus
from backend.integrations.n8n.client import N8NClient
from backend.integrations.n8n.config import N8NConfig, get_n8n_config
from backend.integrations.n8n.events import (
    N8N_CALLBACK_RECEIVED,
    N8N_CALLBACK_REJECTED,
    N8N_CONNECTION_CHECKED,
    N8N_EVENT_DELIVERED,
    N8N_EVENT_FAILED,
    N8N_EVENT_SENT,
    N8N_WEBHOOK_RECEIVED,
    N8N_WEBHOOK_REJECTED,
    N8N_WORKFLOW_COMPLETED,
    N8N_WORKFLOW_FAILED,
    N8N_WORKFLOW_REQUESTED,
    N8N_WORKFLOW_STARTED,
)
from backend.integrations.n8n.schemas import (
    N8NEvent,
    N8NIntegrationRecord,
    N8NStatus,
    N8NWebhookEvent,
    N8NWorkflowTriggerRequest,
    N8NWorkflowTriggerResult,
)
from backend.integrations.n8n.security import redact_payload


class N8NIntegrationService:
    _last_successful_interaction: Optional[str] = None
    _last_failure: Optional[str] = None
    _last_event_type: Optional[str] = None
    _recent_inbound: Dict[str, float] = {}

    def __init__(self, config: Optional[N8NConfig] = None, client: Optional[N8NClient] = None):
        self.config = config or get_n8n_config()
        self.client = client or N8NClient(self.config)

    def status(self) -> N8NStatus:
        reachable = self.client.check_reachable() if self.config.base_url else False
        event_bus.emit_sync(N8N_CONNECTION_CHECKED, {"reachable": reachable, "base_url": self.config.base_url})
        return N8NStatus(
            configured=self.config.configured,
            enabled=self.config.configured,
            reachable=reachable,
            base_url=self.config.base_url,
            authentication_configured=self.config.authentication_configured,
            allowed_workflows=sorted(self.config.allowed_workflows),
            allowed_event_types=sorted(self.config.allowed_event_types),
            workflow_config_status=self._workflow_config_status(),
            last_successful_interaction=self._last_successful_interaction,
            last_success=self._last_successful_interaction,
            last_failure=self._last_failure,
            last_event_type=self._last_event_type,
        )

    def send_event(self, event: N8NEvent) -> N8NWorkflowTriggerResult:
        self.__class__._last_event_type = event.event_type
        event_payload = {
            "project_id": event.project_id,
            "task_id": event.task_id,
            "event_type": event.event_type,
            "correlation_id": event.correlation_id,
            "summary": f"N8N: event requested: {event.event_type}",
        }
        event_bus.emit_sync(N8N_EVENT_SENT, event_payload)
        if event.event_type not in self.config.allowed_event_types:
            result = N8NWorkflowTriggerResult(
                workflow="SEAM_EVENT_ROUTER",
                status="failed",
                correlation_id=event.correlation_id,
                result_summary="Event type is not allowed for n8n emission",
            )
            self._mark_failure(result.result_summary)
            event_bus.emit_sync(N8N_EVENT_FAILED, {**event_payload, "error": result.result_summary})
            return result
        workflow_url = self.config.workflow_url("SEAM_EVENT_ROUTER") or self.config.workflow_url("default")
        if not workflow_url or not self.config.validate_url(workflow_url):
            result = N8NWorkflowTriggerResult(
                workflow="SEAM_EVENT_ROUTER",
                status="failed",
                correlation_id=event.correlation_id,
                result_summary="SEAM_EVENT_ROUTER workflow is not configured or URL is unsafe",
            )
            self._mark_failure(result.result_summary)
            event_bus.emit_sync(N8N_EVENT_FAILED, {**event_payload, "error": result.result_summary})
            return result
        result = self.client.emit_event(workflow_url, redact_payload(event.model_dump()), event.correlation_id)
        self._record_project_integration(event.project_id, "outbound", event.event_type, result)
        if result.status == "completed":
            self._mark_success()
            event_bus.emit_sync(N8N_EVENT_DELIVERED, {**event_payload, "summary": result.result_summary})
        else:
            self._mark_failure(result.result_summary)
            event_bus.emit_sync(N8N_EVENT_FAILED, {**event_payload, "error": result.result_summary})
        self._update_project_n8n_status(event.project_id)
        return result

    def trigger_workflow(self, request: N8NWorkflowTriggerRequest) -> N8NWorkflowTriggerResult:
        workflow_url = self.config.workflow_url(request.workflow)
        event_payload = {
            "project_id": request.project_id,
            "workflow": request.workflow,
            "correlation_id": request.correlation_id,
            "summary": f"N8N: workflow requested: {request.workflow}",
        }
        event_bus.emit_sync(N8N_WORKFLOW_REQUESTED, event_payload)

        if not workflow_url or not self.config.validate_url(workflow_url):
            result = N8NWorkflowTriggerResult(
                workflow=request.workflow,
                status="failed",
                correlation_id=request.correlation_id,
                result_summary="Workflow is not allowed or URL is unsafe",
            )
            self._record_project_integration(request.project_id, "outbound", request.workflow, result)
            event_bus.emit_sync(N8N_WORKFLOW_FAILED, {**event_payload, "error": result.result_summary})
            return result

        event_bus.emit_sync(N8N_WORKFLOW_STARTED, event_payload)
        result = self.client.trigger(request.workflow, workflow_url, redact_payload(request.payload), request.correlation_id)
        self._record_project_integration(request.project_id, "outbound", request.workflow, result)
        if result.status == "completed":
            self._mark_success()
            event_bus.emit_sync(N8N_WORKFLOW_COMPLETED, {**event_payload, "summary": result.result_summary})
        else:
            self._mark_failure(result.result_summary)
            event_bus.emit_sync(N8N_WORKFLOW_FAILED, {**event_payload, "error": result.result_summary})
        return result

    def handle_webhook(self, event: N8NWebhookEvent) -> Dict[str, str]:
        if self._is_rate_limited(event.correlation_id):
            event_bus.emit_sync(
                N8N_WEBHOOK_REJECTED,
                {
                    "project_id": event.project_id,
                    "correlation_id": event.correlation_id,
                    "summary": "N8N: webhook rejected by rate limit",
                },
            )
            event_bus.emit_sync(N8N_CALLBACK_REJECTED, {"correlation_id": event.correlation_id, "reason": "rate_limited"})
            return {"status": "rejected", "reason": "rate_limited", "correlation_id": event.correlation_id}

        summary = self._summary_for_event(event)
        event_bus.emit_sync(
            N8N_WEBHOOK_RECEIVED,
            {
                "project_id": event.project_id,
                "correlation_id": event.correlation_id,
                "source": event.source,
                "event_type": event.event_type,
                "summary": summary,
            },
        )
        event_bus.emit_sync(
            N8N_CALLBACK_RECEIVED,
            {
                "project_id": event.project_id,
                "correlation_id": event.correlation_id,
                "event_type": event.event_type,
                "summary": summary,
            },
        )
        self._record_project_webhook(event, summary)
        self._mark_success()
        self.__class__._last_event_type = event.event_type
        self._update_project_n8n_status(event.project_id)
        return {
            "status": "accepted",
            "event_type": event.event_type,
            "correlation_id": event.correlation_id,
            "summary": summary,
        }

    def reject_webhook(self, reason: str, project_id: Optional[str] = None, correlation_id: Optional[str] = None) -> None:
        event_bus.emit_sync(
            N8N_WEBHOOK_REJECTED,
            {
                "project_id": project_id,
                "correlation_id": correlation_id,
                "summary": f"N8N: webhook rejected: {reason}",
            },
        )
        event_bus.emit_sync(N8N_CALLBACK_REJECTED, {"project_id": project_id, "correlation_id": correlation_id, "summary": reason})

    def _record_project_webhook(self, event: N8NWebhookEvent, summary: str) -> None:
        record = N8NIntegrationRecord(
            direction="inbound",
            workflow=event.event_type,
            status="accepted",
            correlation_id=event.correlation_id,
            result_summary=summary,
        )
        self._append_project_record(event.project_id, record)

    def _record_project_integration(
        self,
        project_id: Optional[str],
        direction: str,
        workflow: str,
        result: N8NWorkflowTriggerResult,
    ) -> None:
        record = N8NIntegrationRecord(
            direction=direction,
            workflow=workflow,
            status=result.status,
            correlation_id=result.correlation_id,
            result_summary=result.result_summary,
        )
        self._append_project_record(project_id, record)

    def _append_project_record(self, project_id: Optional[str], record: N8NIntegrationRecord) -> None:
        if not project_id:
            return
        try:
            from backend.api.projects import projects_db

            state = projects_db.get(project_id)
            if not state:
                return
            state.external_integrations.append(record.model_dump())
            self._update_project_n8n_status(project_id)
        except Exception:
            return

    def _update_project_n8n_status(self, project_id: Optional[str]) -> None:
        if not project_id:
            return
        try:
            from backend.api.projects import projects_db

            state = projects_db.get(project_id)
            if not state:
                return
            state.n8n_integration_status = {
                "enabled": self.config.configured,
                "reachable": self.client.check_reachable() if self.config.base_url else False,
                "base_url": self.config.base_url,
                "last_event_type": self._last_event_type,
                "last_success": self._last_successful_interaction,
                "last_failure": self._last_failure,
            }
        except Exception:
            return

    def _summary_for_event(self, event: N8NWebhookEvent) -> str:
        if event.event_type == "github.push":
            repository = event.payload.get("repository") or event.payload.get("full_name") or "repository"
            return f"N8N: GitHub event received for {repository}"
        if event.event_type in {"jira.issue_created", "external.issue_created"}:
            title = event.payload.get("title") or event.payload.get("key") or "external issue"
            return f"N8N: External issue received: {title}"
        if event.event_type == "qa.failed":
            return "N8N: QA failure notification received"
        if event.event_type == "delivery.completed":
            return "N8N: Delivery completion notification received"
        return "N8N: webhook received"

    def _is_rate_limited(self, correlation_id: str) -> bool:
        now = datetime.now(timezone.utc).timestamp()
        previous = self._recent_inbound.get(correlation_id)
        self._recent_inbound[correlation_id] = now
        return previous is not None and now - previous < 1

    def _mark_success(self) -> None:
        self.__class__._last_successful_interaction = datetime.now(timezone.utc).isoformat()

    def _mark_failure(self, reason: str) -> None:
        self.__class__._last_failure = reason

    def _workflow_config_status(self) -> Dict[str, str]:
        required = [
            "SEAM_EVENT_ROUTER",
            "N8N_TO_SEAM",
            "GITHUB_TO_SEAM",
            "SEAM_TO_GITHUB",
            "SEAM_TO_JIRA",
            "FIGMA_TO_SEAM",
            "SEAM_TO_FIGMA",
            "SEAM_DELIVERY_TO_CICD",
            "SEAM_DELIVERY_NOTIFICATION",
            "SEAM_EXPERIMENT_NOTIFICATION",
            "SEAM_DEFECT_ROUTER",
        ]
        return {name: "CONFIGURED" if self.config.workflow_url(name) else "NOT_CONFIGURED" for name in required}
