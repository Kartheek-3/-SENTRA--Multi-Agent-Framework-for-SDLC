from unittest.mock import MagicMock, patch

from backend.models.state import ProjectState
from backend.tools.agent_tools import run_agent_tool
from backend.tools.schemas import ToolResult


def test_analysis_agent_tool_bridge_delegates_rag_search_to_executor():
    state = ProjectState(project_id="p", domain="general")
    with patch("backend.tools.agent_tools.ToolExecutor") as executor_cls:
        executor_cls.return_value.execute.return_value = ToolResult(success=True, tool_name="rag_search", structured_data={"results": []})

        result = run_agent_tool(state, "AnalysisAgent", "rag_search", {"query": "expense", "domain": "general"})

    assert result.success is True
    request = executor_cls.return_value.execute.call_args.args[0]
    assert request.tool_name == "rag_search"
    assert request.agent_name == "AnalysisAgent"
    assert state.execution_history[-1]["tool_name"] == "rag_search"


def test_planning_agent_tool_bridge_delegates_mermaid_generate_to_executor():
    state = ProjectState(project_id="p", domain="general")
    with patch("backend.tools.agent_tools.ToolExecutor") as executor_cls:
        executor_cls.return_value.execute.return_value = ToolResult(success=True, tool_name="mermaid_generate", artifacts=["diagram.mmd"])

        result = run_agent_tool(state, "PlanningAgent", "mermaid_generate", {"diagram_type": "architecture", "diagram_data": {"nodes": [], "edges": []}})

    assert result.artifacts == ["diagram.mmd"]
    assert executor_cls.return_value.execute.call_args.args[0].tool_name == "mermaid_generate"


def test_coding_agent_tool_bridge_delegates_file_write_and_git_status_to_executor():
    state = ProjectState(project_id="p", domain="general")
    with patch("backend.tools.agent_tools.ToolExecutor") as executor_cls:
        executor_cls.return_value.execute.side_effect = [
            ToolResult(success=True, tool_name="file_write"),
            ToolResult(success=True, tool_name="git_status"),
        ]

        run_agent_tool(state, "CodingAgent", "file_write", {"path": "app.py", "content": "print('ok')"}, task_id="T-1")
        run_agent_tool(state, "CodingAgent", "git_status", {}, task_id="T-1")

    tools = [call.args[0].tool_name for call in executor_cls.return_value.execute.call_args_list]
    assert tools == ["file_write", "git_status"]


def test_qa_agent_tool_bridge_delegates_pytest_runner_to_executor():
    state = ProjectState(project_id="p", domain="general")
    with patch("backend.tools.agent_tools.ToolExecutor") as executor_cls:
        executor_cls.return_value.execute.return_value = ToolResult(success=True, tool_name="pytest_runner", stdout="1 passed")

        result = run_agent_tool(state, "QAAgent", "pytest_runner", {"test_args": ["-q"]}, task_id="T-1")

    assert "1 passed" in result.stdout
    assert executor_cls.return_value.execute.call_args.args[0].tool_name == "pytest_runner"


def test_delivery_agent_tool_bridge_delegates_docker_validate_to_executor():
    state = ProjectState(project_id="p", domain="general")
    with patch("backend.tools.agent_tools.ToolExecutor") as executor_cls:
        executor_cls.return_value.execute.return_value = ToolResult(success=True, tool_name="docker_validate")

        result = run_agent_tool(state, "DeliveryAgent", "docker_validate", {"dockerfile": "Dockerfile"})

    assert result.success is True
    assert executor_cls.return_value.execute.call_args.args[0].tool_name == "docker_validate"


def test_agent_tool_bridge_records_tool_failure():
    state = ProjectState(project_id="p", domain="general")
    with patch("backend.tools.agent_tools.ToolExecutor") as executor_cls:
        executor_cls.return_value.execute.return_value = ToolResult(success=False, tool_name="git_push")

        result = run_agent_tool(state, "CodingAgent", "git_push", {"branch": "main"})

    assert result.success is False
    assert state.execution_history[-1]["success"] is False
