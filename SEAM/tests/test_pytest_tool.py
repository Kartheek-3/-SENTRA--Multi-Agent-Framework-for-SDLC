from unittest.mock import patch

from backend.tools.builtin import PytestRunnerTool
from backend.tools.schemas import ToolExecutionContext


@patch("backend.tools.builtin.subprocess.run")
def test_pytest_runner_uses_argument_array(mock_run, tmp_path):
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "1 passed"
    mock_run.return_value.stderr = ""
    tool = PytestRunnerTool()

    result = tool.execute(tool.validate_input({"test_args": ["-q"]}), ToolExecutionContext(project_id="p", agent_name="QAAgent", project_root=str(tmp_path)))

    assert result.success is True
    assert mock_run.call_args.args[0][:3] == ["python", "-m", "pytest"]
