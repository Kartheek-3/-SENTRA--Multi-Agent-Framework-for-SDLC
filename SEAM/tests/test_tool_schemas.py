from backend.tools.schemas import ToolResult, redact_secret


def test_tool_result_redacts_secret_streams():
    result = ToolResult(success=True, tool_name="x", stdout="token=abc123")

    assert "[REDACTED]" in result.stdout


def test_nested_secret_redaction():
    data = redact_secret({"github_token": "github_pat_secret", "safe": "ok"})

    assert data["github_token"] == "[REDACTED]"
    assert data["safe"] == "ok"
