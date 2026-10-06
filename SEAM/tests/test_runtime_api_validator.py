from unittest.mock import Mock, patch

import pytest

from backend.tools.builtin import RuntimeAPIValidatorTool
from backend.tools.registry import default_registry
from backend.tools.schemas import ToolExecutionContext


def test_runtime_api_validator_is_registered():
    assert default_registry.is_registered("runtime_api_validator")


def test_runtime_api_validator_blocks_external_network():
    tool = RuntimeAPIValidatorTool()

    with pytest.raises(ValueError):
        tool.execute(
            tool.validate_input({
                "base_url": "https://example.com",
                "endpoint": "/api/users",
                "method": "GET",
            }),
            ToolExecutionContext(project_id="p", agent_name="QAAgent"),
        )


@patch("backend.tools.builtin.requests.request")
def test_runtime_api_validator_detects_response_schema_mismatch(mock_request):
    response = Mock()
    response.status_code = 200
    response.text = '{"id":"123"}'
    response.headers = {"content-type": "application/json"}
    response.json.return_value = {"id": "123"}
    mock_request.return_value = response
    tool = RuntimeAPIValidatorTool()

    result = tool.execute(
        tool.validate_input({
            "base_url": "http://127.0.0.1:8000",
            "endpoint": "/api/users",
            "method": "GET",
            "expected_response_schema": {"properties": {"id": {"type": "integer"}}},
            "expected_status_codes": [200],
        }),
        ToolExecutionContext(project_id="p", agent_name="QAAgent"),
    )

    assert result.success is False
    assert result.structured_data["status"] == "FAIL"
    assert result.structured_data["issues"][0]["category"] == "RESPONSE_SCHEMA_MISMATCH"
    assert "string" in result.structured_data["issues"][0]["actual"]


@patch("backend.tools.builtin.requests.request")
def test_runtime_api_validator_passes_matching_response(mock_request):
    response = Mock()
    response.status_code = 200
    response.text = '{"id":123}'
    response.headers = {"content-type": "application/json"}
    response.json.return_value = {"id": 123}
    mock_request.return_value = response
    tool = RuntimeAPIValidatorTool()

    result = tool.execute(
        tool.validate_input({
            "base_url": "http://localhost:8000",
            "endpoint": "/api/users",
            "method": "GET",
            "expected_response_schema": {"properties": {"id": {"type": "integer"}}},
            "expected_status_codes": [200],
        }),
        ToolExecutionContext(project_id="p", agent_name="QAAgent"),
    )

    assert result.success is True
    assert result.structured_data["status"] == "PASS"

