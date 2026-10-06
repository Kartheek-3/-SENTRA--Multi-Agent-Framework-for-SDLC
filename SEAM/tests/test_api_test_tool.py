from unittest.mock import patch

import pytest

from backend.tools.builtin import APITestRunnerTool
from backend.tools.schemas import ToolExecutionContext


@patch("backend.tools.builtin.requests.request")
def test_api_test_runner_allows_localhost_only(mock_request):
    mock_request.return_value.status_code = 200
    mock_request.return_value.text = "ok"
    mock_request.return_value.headers = {}
    tool = APITestRunnerTool()

    result = tool.execute(tool.validate_input({"url": "http://127.0.0.1:8000/"}), ToolExecutionContext(project_id="p", agent_name="QAAgent"))

    assert result.success is True


def test_api_test_runner_blocks_external_network():
    tool = APITestRunnerTool()

    with pytest.raises(ValueError):
        tool.execute(tool.validate_input({"url": "https://example.com"}), ToolExecutionContext(project_id="p", agent_name="QAAgent"))
