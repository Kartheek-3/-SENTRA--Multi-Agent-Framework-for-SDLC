from unittest.mock import patch

import pytest

from backend.tools.builtin import (
    GitAddTool,
    GitBranchTool,
    GitCheckoutTool,
    GitCommitTool,
    GitCreateBranchTool,
    GitDiffTool,
    GitLogTool,
    GitMergeTool,
    GitPushTool,
    GitStashTool,
    GitStatusTool,
)
from backend.tools.executor import ToolExecutor
from backend.tools.registry import ToolRegistry
from backend.tools.schemas import ToolExecutionContext, ToolResult


def ok_process(stdout="ok"):
    class Proc:
        returncode = 0
        stderr = ""

        def __init__(self):
            self.stdout = stdout

    return Proc()


def run_tool(tool, payload, tmp_path, agent="CodingAgent"):
    return tool.execute(tool.validate_input(payload), ToolExecutionContext(project_id="p", agent_name=agent, project_root=str(tmp_path)))


@patch("backend.tools.builtin.subprocess.run")
def test_git_status(mock_run, tmp_path):
    mock_run.return_value = ok_process(" M file.py")

    result = run_tool(GitStatusTool(), {}, tmp_path, agent="QAAgent")

    assert result.success is True
    assert mock_run.call_args.args[0][:3] == ["git", "status", "--short"]


@patch("backend.tools.builtin.subprocess.run")
def test_git_diff(mock_run, tmp_path):
    mock_run.return_value = ok_process("diff")

    result = run_tool(GitDiffTool(), {}, tmp_path, agent="QAAgent")

    assert result.success is True
    assert mock_run.call_args.args[0][:2] == ["git", "diff"]


@patch("backend.tools.builtin.subprocess.run")
def test_git_log(mock_run, tmp_path):
    mock_run.return_value = ok_process("abc commit")

    result = run_tool(GitLogTool(), {}, tmp_path, agent="SupervisorAgent")

    assert result.success is True
    assert mock_run.call_args.args[0][:3] == ["git", "log", "--oneline"]


@patch("backend.tools.builtin.subprocess.run")
def test_git_branch(mock_run, tmp_path):
    mock_run.return_value = ok_process("main")

    result = run_tool(GitBranchTool(), {}, tmp_path, agent="DeliveryAgent")

    assert result.success is True
    assert mock_run.call_args.args[0] == ["git", "branch", "--show-current"]


@patch("backend.tools.builtin.subprocess.run")
def test_git_create_branch(mock_run, tmp_path):
    mock_run.return_value = ok_process()

    result = run_tool(GitCreateBranchTool(), {"branch_name": "feature/demo"}, tmp_path)

    assert result.success is True
    assert mock_run.call_args.args[0] == ["git", "branch", "feature/demo"]


@patch("backend.tools.builtin.subprocess.run")
def test_git_checkout(mock_run, tmp_path):
    mock_run.return_value = ok_process()

    result = run_tool(GitCheckoutTool(), {"ref": "feature/demo"}, tmp_path)

    assert result.success is True
    assert mock_run.call_args.args[0] == ["git", "checkout", "feature/demo"]


@patch("backend.tools.builtin.subprocess.run")
def test_git_add(mock_run, tmp_path):
    mock_run.return_value = ok_process()
    (tmp_path / "file.py").write_text("x", encoding="utf-8")

    result = run_tool(GitAddTool(), {"paths": ["file.py"]}, tmp_path)

    assert result.success is True
    assert mock_run.call_args.args[0][:4] == ["git", "add", "--", "file.py"]


@patch("backend.tools.builtin.subprocess.run")
def test_git_commit(mock_run, tmp_path):
    mock_run.return_value = ok_process()

    result = run_tool(GitCommitTool(), {"message": "test commit"}, tmp_path)

    assert result.success is True
    assert mock_run.call_args.args[0] == ["git", "commit", "-m", "test commit"]


@patch("backend.tools.builtin.subprocess.run")
def test_git_stash(mock_run, tmp_path):
    mock_run.return_value = ok_process()

    result = run_tool(GitStashTool(), {"message": "save work"}, tmp_path)

    assert result.success is True
    assert mock_run.call_args.args[0] == ["git", "stash", "push", "-m", "save work"]


def test_git_merge_requires_approval():
    registry = ToolRegistry()
    registry.register(GitMergeTool())

    result = ToolExecutor(registry).execute_dict({
        "tool_name": "git_merge",
        "agent_name": "CodingAgent",
        "project_id": "p",
        "input": {"branch": "main"},
    })

    assert result.success is False
    assert result.error.code == "PERMISSION_DENIED"


def test_git_push_requires_approval():
    registry = ToolRegistry()
    registry.register(GitPushTool())

    result = ToolExecutor(registry).execute_dict({
        "tool_name": "git_push",
        "agent_name": "DeliveryAgent",
        "project_id": "p",
        "input": {"branch": "main"},
    })

    assert result.success is False
    assert result.error.code == "PERMISSION_DENIED"


def test_git_push_rejects_force_options(tmp_path):
    with pytest.raises(ValueError):
        run_tool(GitPushTool(), {"branch": "main", "options": ["--force"]}, tmp_path, agent="DeliveryAgent")


def test_git_add_prevents_repository_path_escape(tmp_path):
    with pytest.raises(Exception):
        run_tool(GitAddTool(), {"paths": ["../outside.py"]}, tmp_path)


def test_git_result_redacts_credentials():
    result = ToolResult(success=True, tool_name="git_status", stdout="https://x-access-token:github_pat_secret@github.com/a/b")

    assert "[REDACTED]" in result.stdout


@patch("backend.tools.builtin.subprocess.run")
def test_git_timeout_is_passed_to_subprocess(mock_run, tmp_path):
    mock_run.return_value = ok_process()
    tool = GitStatusTool()

    run_tool(tool, {}, tmp_path, agent="QAAgent")

    assert mock_run.call_args.kwargs["timeout"] == tool.timeout


def test_unauthorized_agent_access_denied():
    registry = ToolRegistry()
    registry.register(GitCommitTool())

    result = ToolExecutor(registry).execute_dict({
        "tool_name": "git_commit",
        "agent_name": "AnalysisAgent",
        "project_id": "p",
        "input": {"message": "nope"},
    })

    assert result.success is False
    assert result.error.code == "PERMISSION_DENIED"
