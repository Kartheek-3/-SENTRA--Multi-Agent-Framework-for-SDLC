import requests
from fastapi.testclient import TestClient

from backend.api.projects import projects_db
from backend.integrations.n8n.config import N8NConfig
from backend.integrations.n8n.schemas import N8NEvent, N8NWebhookEvent, N8NWorkflowTriggerRequest
from backend.integrations.n8n.security import redact_payload
from backend.integrations.n8n.service import N8NIntegrationService
from backend.main import app
from backend.models.state import ProjectState


class FakeResponse:
    status_code = 200
    content = b'{"ok": true, "token": "secret"}'

    def json(self):
        return {"ok": True, "token": "secret"}


def test_n8n_configuration_from_environment(monkeypatch):
    monkeypatch.setenv("N8N_BASE_URL", "http://localhost:5678")
    monkeypatch.setenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/default")
    monkeypatch.setenv("N8N_API_KEY", "secret")

    status = N8NIntegrationService().status()

    assert status.configured is True
    assert status.enabled is True
    assert status.authentication_configured is True
    assert status.allowed_workflows == ["default"]
    assert "DELIVERY_COMPLETED" in status.allowed_event_types


def test_valid_outbound_workflow_trigger(monkeypatch):
    calls = []

    def fake_post(url, json, headers, timeout):
        calls.append((url, json, headers, timeout))
        return FakeResponse()

    monkeypatch.setattr("backend.integrations.n8n.client.requests.post", fake_post)
    config = N8NConfig(
        api_key="secret",
        allowed_workflows={"qa_notification": "http://localhost:5678/webhook/qa"},
    )

    result = N8NIntegrationService(config=config).trigger_workflow(
        N8NWorkflowTriggerRequest(
            workflow="qa_notification",
            payload={"message": "QA failed", "token": "do-not-log"},
            correlation_id="corr-1",
        )
    )

    assert result.status == "completed"
    assert result.response["token"] == "***REDACTED***"
    assert calls[0][0] == "http://localhost:5678/webhook/qa"
    assert calls[0][1]["payload"]["token"] == "***REDACTED***"
    assert calls[0][2]["X-SEAM-Correlation-ID"] == "corr-1"


def test_url_allowlist_rejects_unknown_workflow():
    config = N8NConfig(allowed_workflows={"known": "http://localhost:5678/webhook/known"})

    result = N8NIntegrationService(config=config).trigger_workflow(
        N8NWorkflowTriggerRequest(workflow="unknown", correlation_id="corr-2")
    )

    assert result.status == "failed"
    assert "not allowed" in result.result_summary


def test_timeout_is_reported(monkeypatch):
    def fake_post(*args, **kwargs):
        raise requests.Timeout()

    monkeypatch.setattr("backend.integrations.n8n.client.requests.post", fake_post)
    config = N8NConfig(allowed_workflows={"known": "http://localhost:5678/webhook/known"})

    result = N8NIntegrationService(config=config).trigger_workflow(
        N8NWorkflowTriggerRequest(workflow="known", correlation_id="corr-timeout")
    )

    assert result.status == "failed"
    assert "timed out" in result.result_summary


def test_unavailable_is_reported(monkeypatch):
    def fake_post(*args, **kwargs):
        raise requests.ConnectionError()

    monkeypatch.setattr("backend.integrations.n8n.client.requests.post", fake_post)
    config = N8NConfig(allowed_workflows={"known": "http://localhost:5678/webhook/known"})

    result = N8NIntegrationService(config=config).trigger_workflow(
        N8NWorkflowTriggerRequest(workflow="known", correlation_id="corr-unavailable")
    )

    assert result.status == "failed"
    assert "unavailable" in result.result_summary


def test_secret_redaction_nested_payload():
    result = redact_payload({"nested": {"github_token": "abc"}, "safe": "ok"})

    assert result["nested"]["github_token"] == "***REDACTED***"
    assert result["safe"] == "ok"


def test_authenticated_webhook_updates_project_state(monkeypatch):
    monkeypatch.setenv("N8N_API_KEY", "secret")
    project = ProjectState(project_id="n8n-project", user_requirement="req")
    projects_db[project.project_id] = project

    client = TestClient(app)
    response = client.post(
        "/api/integrations/n8n/webhook",
        headers={"X-N8N-API-Key": "secret"},
        json={
            "event_type": "github.push",
            "project_id": project.project_id,
            "correlation_id": "corr-webhook",
            "payload": {"repository": "owner/repo"},
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
    assert project.external_integrations[-1]["correlation_id"] == "corr-webhook"
    assert project.external_integrations[-1]["workflow"] == "github.push"
    assert project.n8n_integration_status["last_event_type"] == "github.push"


def test_unauthenticated_webhook_rejected(monkeypatch):
    monkeypatch.setenv("N8N_API_KEY", "secret")
    client = TestClient(app)

    response = client.post(
        "/api/integrations/n8n/webhook",
        json={"event_type": "github.push", "payload": {}},
    )

    assert response.status_code == 401


def test_malformed_webhook_rejected(monkeypatch):
    monkeypatch.setenv("N8N_API_KEY", "secret")
    client = TestClient(app)

    response = client.post(
        "/api/integrations/n8n/webhook",
        headers={"X-N8N-API-Key": "secret"},
        content="{",
    )

    assert response.status_code == 422


def test_invalid_event_type_rejected(monkeypatch):
    monkeypatch.setenv("N8N_API_KEY", "secret")
    client = TestClient(app)

    response = client.post(
        "/api/integrations/n8n/webhook",
        headers={"X-N8N-API-Key": "secret"},
        json={"event_type": "shell.execute", "payload": {}},
    )

    assert response.status_code == 422


def test_eventstore_integration(monkeypatch):
    emitted = []
    monkeypatch.setattr("backend.integrations.n8n.service.event_bus.emit_sync", lambda event, payload: emitted.append(event))
    config = N8NConfig(allowed_workflows={"known": "http://evil.example/webhook"})

    N8NIntegrationService(config=config).trigger_workflow(
        N8NWorkflowTriggerRequest(workflow="known", correlation_id="corr-events")
    )

    assert "N8N_WORKFLOW_REQUESTED" in emitted
    assert "N8N_WORKFLOW_FAILED" in emitted


def test_correlation_id_preserved():
    result = N8NIntegrationService(config=N8NConfig()).handle_webhook(
        N8NWebhookEvent(event_type="jira.issue_created", correlation_id="corr-keep", payload={"key": "JIRA-1"})
    )

    assert result["correlation_id"] == "corr-keep"


def test_send_allowlisted_seam_event(monkeypatch):
    calls = []

    def fake_post(url, json, headers, timeout):
        calls.append((url, json, headers, timeout))
        return FakeResponse()

    monkeypatch.setattr("backend.integrations.n8n.client.requests.post", fake_post)
    config = N8NConfig(
        integration_secret="shared",
        allowed_workflows={"SEAM_EVENT_ROUTER": "http://localhost:5678/webhook/seam-event-router"},
    )

    result = N8NIntegrationService(config=config).send_event(
        N8NEvent(
            event_type="DELIVERY_COMPLETED",
            project_id="proj",
            task_id="task",
            status="SUCCESS",
            payload={"token": "hide-me", "summary": "done"},
            correlation_id="corr-event",
        )
    )

    assert result.status == "completed"
    assert calls[0][1]["payload"]["payload"]["token"] == "***REDACTED***"
    assert calls[0][2]["X-SEAM-Integration-Secret"] == "shared"


def test_send_disallowed_seam_event_rejected_without_http(monkeypatch):
    def fake_post(*args, **kwargs):
        raise AssertionError("HTTP should not be called for disallowed events")

    monkeypatch.setattr("backend.integrations.n8n.client.requests.post", fake_post)
    config = N8NConfig(allowed_workflows={"SEAM_EVENT_ROUTER": "http://localhost:5678/webhook/seam-event-router"})

    result = N8NIntegrationService(config=config).send_event(N8NEvent(event_type="SHELL_EXECUTE", correlation_id="corr-no"))

    assert result.status == "failed"
    assert "not allowed" in result.result_summary


def test_events_api_uses_allowlist(monkeypatch):
    def fake_post(url, json, headers, timeout):
        return FakeResponse()

    monkeypatch.setenv("N8N_ALLOWED_WORKFLOWS", "SEAM_EVENT_ROUTER=http://localhost:5678/webhook/seam-event-router")
    monkeypatch.setenv("SEAM_N8N_INTEGRATION_SECRET", "shared")
    monkeypatch.setattr("backend.integrations.n8n.client.requests.post", fake_post)
    client = TestClient(app)

    response = client.post(
        "/api/integrations/n8n/events",
        json={"event_type": "DELIVERY_COMPLETED", "status": "SUCCESS", "correlation_id": "corr-api", "payload": {}},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "completed"


def test_webhook_accepts_canonical_shared_secret(monkeypatch):
    monkeypatch.setenv("SEAM_N8N_INTEGRATION_SECRET", "shared")
    client = TestClient(app)

    response = client.post(
        "/api/integrations/n8n/webhook",
        headers={"X-SEAM-Integration-Secret": "shared"},
        json={"event_type": "delivery.completed", "correlation_id": "corr-shared", "payload": {}},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "accepted"


def test_workflow_assets_and_docker_files_exist():
    from pathlib import Path
    import json

    root = Path(__file__).resolve().parents[1]
    expected = [
        "SEAM_EVENT_ROUTER.json",
        "N8N_TO_SEAM.json",
        "GITHUB_TO_SEAM.json",
        "SEAM_DELIVERY_NOTIFICATION.json",
        "SEAM_EXPERIMENT_NOTIFICATION.json",
        "SEAM_DEFECT_ROUTER.json",
    ]

    assert (root / "n8n" / "docker-compose.yml").exists()
    assert (root / "n8n" / ".env.example").exists()
    for filename in expected:
        data = json.loads((root / "n8n" / "workflows" / filename).read_text(encoding="utf-8"))
        assert data["name"] == filename.removesuffix(".json")
