import hashlib
import hmac

import backend.github.intelligence_service as intelligence_service
from backend.github.intelligence_service import GitHubIntelligenceService
from backend.github.registry import RepositoryRegistry


def test_valid_webhook_signature(monkeypatch, tmp_path):
    monkeypatch.setattr(intelligence_service, "GITHUB_WEBHOOK_SECRET", "secret")
    body = b'{"zen":"ok"}'
    signature = "sha256=" + hmac.new(b"secret", body, hashlib.sha256).hexdigest()
    service = GitHubIntelligenceService(registry=RepositoryRegistry(base_dir=str(tmp_path)))

    valid, reason = service.verify_webhook_signature(body, signature)

    assert valid is True
    assert reason == "ok"


def test_invalid_webhook_signature(monkeypatch, tmp_path):
    monkeypatch.setattr(intelligence_service, "GITHUB_WEBHOOK_SECRET", "secret")
    service = GitHubIntelligenceService(registry=RepositoryRegistry(base_dir=str(tmp_path)))

    valid, reason = service.verify_webhook_signature(b"{}", "sha256=bad")

    assert valid is False
    assert reason == "ok"


def test_missing_webhook_secret_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setattr(intelligence_service, "GITHUB_WEBHOOK_SECRET", "")
    service = GitHubIntelligenceService(registry=RepositoryRegistry(base_dir=str(tmp_path)))

    valid, reason = service.verify_webhook_signature(b"{}", None)

    assert valid is False
    assert reason == "missing_webhook_secret"

