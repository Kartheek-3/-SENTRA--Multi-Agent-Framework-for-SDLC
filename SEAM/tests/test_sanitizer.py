import pytest
from backend.knowledge.sanitizer import KnowledgeSanitizer

def test_sanitizer_api_keys():
    sanitizer = KnowledgeSanitizer()
    content = "The service uses FAKE_API_KEY='AKIA1234567890123456' to connect."
    cleaned = sanitizer.sanitize(content)
    assert "AKIA" not in cleaned
    assert "REDACTED" in cleaned

def test_sanitizer_jwt():
    sanitizer = KnowledgeSanitizer()
    # Fake JWT for testing
    content = 'FAKE_JWT="eyJhbGciOiJIUzI1NiIsInR5cCI.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZS.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"'
    cleaned = sanitizer.sanitize(content)
    assert "eyJhbGci" not in cleaned
    assert "REDACTED" in cleaned

def test_sanitizer_passwords():
    sanitizer = KnowledgeSanitizer()
    content = "password = 'FAKE_PASSWORD_123!'"
    cleaned = sanitizer.sanitize(content)
    assert "FAKE_PASSWORD" not in cleaned
    assert "REDACTED" in cleaned

def test_sanitizer_preserves_safe_content():
    sanitizer = KnowledgeSanitizer()
    content = "The authentication uses JWT tokens and API keys."
    cleaned = sanitizer.sanitize(content)
    assert "JWT tokens and API keys" in cleaned
    assert "REDACTED" not in cleaned
