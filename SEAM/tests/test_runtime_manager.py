import json
from unittest.mock import Mock, patch

import pytest

from backend.tools.builtin import RuntimeManagerTool
from backend.tools.registry import default_registry
from backend.tools.schemas import ToolExecutionContext


def test_runtime_manager_is_registered():
    assert default_registry.is_registered("runtime_manager")


def test_runtime_manager_detects_vite_dev_command(tmp_path):
    (tmp_path / "package.json").write_text(json.dumps({
        "scripts": {"dev": "vite"},
        "devDependencies": {"vite": "^5.0.0"},
        "dependencies": {"react": "^18.0.0"},
    }), encoding="utf-8")
    tool = RuntimeManagerTool()

    result = tool.execute(
        tool.validate_input({"action": "DETECT", "project_root": "."}),
        ToolExecutionContext(project_id="p", agent_name="QAAgent", project_root=str(tmp_path)),
    )

    assert result.success is True
    assert result.structured_data["status"] == "READY"
    assert result.structured_data["profile"]["frontend_start_command"][:3] == ["npm", "run", "dev"]


def test_runtime_manager_detects_fastapi_command(tmp_path):
    backend = tmp_path / "backend"
    backend.mkdir()
    (backend / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n", encoding="utf-8")
    tool = RuntimeManagerTool()

    result = tool.execute(
        tool.validate_input({"action": "DETECT", "project_root": "."}),
        ToolExecutionContext(project_id="p", agent_name="QAAgent", project_root=str(tmp_path)),
    )

    assert result.success is True
    assert result.structured_data["profile"]["backend_framework"] == "FastAPI"
    assert result.structured_data["profile"]["backend_start_command"][:3] == ["python", "-m", "uvicorn"]


def test_runtime_manager_blocks_unsafe_command(tmp_path):
    tool = RuntimeManagerTool()

    with pytest.raises(ValueError):
        tool.execute(
            tool.validate_input({
                "action": "START",
                "project_root": ".",
                "profile": {
                    "project_root": str(tmp_path),
                    "backend_start_command": ["python", "-c", "print(1)"],
                    "backend_port": 8401,
                    "readiness_timeout": 1,
                },
            }),
            ToolExecutionContext(project_id="p", agent_name="QAAgent", project_root=str(tmp_path)),
        )


@patch("backend.tools.builtin.requests.get")
@patch("backend.tools.builtin.subprocess.Popen")
def test_runtime_manager_start_and_stop_project_owned_process(mock_popen, mock_get, tmp_path):
    proc = Mock()
    proc.pid = 1234
    proc.poll.return_value = None
    proc.wait.return_value = 0
    mock_popen.return_value = proc
    response = Mock()
    response.status_code = 200
    mock_get.return_value = response
    tool = RuntimeManagerTool()
    profile = {
        "project_root": str(tmp_path),
        "backend_start_command": ["python", "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8401"],
        "backend_port": 8401,
        "expected_health_endpoint": "/health",
        "readiness_timeout": 1,
    }

    started = tool.execute(
        tool.validate_input({"action": "START", "project_root": ".", "profile": profile}),
        ToolExecutionContext(project_id="p", agent_name="QAAgent", project_root=str(tmp_path)),
    )
    stopped = tool.execute(
        tool.validate_input({"action": "STOP", "project_root": "."}),
        ToolExecutionContext(project_id="p", agent_name="QAAgent", project_root=str(tmp_path)),
    )

    assert started.success is True
    assert started.structured_data["base_url"] == "http://127.0.0.1:8401"
    assert stopped.structured_data["status"] == "STOPPED"
    proc.terminate.assert_called_once()

