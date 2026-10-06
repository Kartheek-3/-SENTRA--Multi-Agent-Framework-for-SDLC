from typing import Any, Dict


SECRET_KEYS = ("api_key", "token", "secret", "password", "authorization", "credential")


def redact_secret(value: str) -> str:
    if not value:
        return ""
    return "***REDACTED***"


def redact_payload(payload: Any) -> Any:
    if isinstance(payload, dict):
        sanitized: Dict[str, Any] = {}
        for key, value in payload.items():
            if any(secret in key.lower() for secret in SECRET_KEYS):
                sanitized[key] = redact_secret(str(value))
            else:
                sanitized[key] = redact_payload(value)
        return sanitized
    if isinstance(payload, list):
        return [redact_payload(item) for item in payload]
    return payload


def constant_time_match(actual: str, expected: str) -> bool:
    import hmac

    if not actual or not expected:
        return False
    return hmac.compare_digest(actual, expected)
