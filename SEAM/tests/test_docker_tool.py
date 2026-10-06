from unittest.mock import patch

from backend.tools.builtin import DockerBuildTool, DockerValidateTool
from backend.tools.schemas import ToolExecutionContext


def test_docker_validate_reports_warnings(tmp_path):
    (tmp_path / "Dockerfile").write_text("FROM python:latest\nUSER root\n", encoding="utf-8")
    tool = DockerValidateTool()

    result = tool.execute(tool.validate_input({}), ToolExecutionContext(project_id="p", agent_name="DeliveryAgent", project_root=str(tmp_path)))

    assert result.success is True
    assert result.structured_data["warnings"]


@patch("backend.tools.builtin.subprocess.run")
def test_docker_build_does_not_push_or_deploy(mock_run, tmp_path):
    (tmp_path / "Dockerfile").write_text("FROM python:3.12\n", encoding="utf-8")
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "built"
    mock_run.return_value.stderr = ""
    tool = DockerBuildTool()

    result = tool.execute(tool.validate_input({"image_tag": "demo:latest"}), ToolExecutionContext(project_id="p", agent_name="DeliveryAgent", project_root=str(tmp_path), approved=True))

    assert result.success is True
    assert mock_run.call_args.args[0][:2] == ["docker", "build"]
