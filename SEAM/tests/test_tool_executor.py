from pydantic import BaseModel

from backend.tools.base import SEAMTool
from backend.tools.executor import ToolExecutor
from backend.tools.registry import ToolRegistry
from backend.tools.schemas import RiskLevel, ToolExecutionContext, ToolResult


class EchoInput(BaseModel):
    text: str


class EchoTool(SEAMTool):
    name = "echo"
    input_schema = EchoInput
    allowed_agents = ["AnalysisAgent"]
    risk_level = RiskLevel.READ_ONLY

    def execute(self, tool_input, context: ToolExecutionContext):
        return ToolResult(success=True, tool_name=self.name, stdout=tool_input.text)


def test_tool_executor_runs_registered_tool():
    registry = ToolRegistry()
    registry.register(EchoTool())

    result = ToolExecutor(registry).execute_dict({
        "tool_name": "echo",
        "agent_name": "AnalysisAgent",
        "project_id": "p",
        "input": {"text": "hello"},
    })

    assert result.success is True
    assert result.stdout == "hello"


def test_tool_executor_returns_permission_denial():
    registry = ToolRegistry()
    registry.register(EchoTool())

    result = ToolExecutor(registry).execute_dict({
        "tool_name": "echo",
        "agent_name": "CodingAgent",
        "project_id": "p",
        "input": {"text": "hello"},
    })

    assert result.success is False
    assert result.error.code == "PERMISSION_DENIED"
