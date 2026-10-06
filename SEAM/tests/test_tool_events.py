from unittest.mock import patch

from pydantic import BaseModel

from backend.tools.base import SEAMTool
from backend.tools.executor import ToolExecutor
from backend.tools.registry import ToolRegistry
from backend.tools.schemas import ToolExecutionContext, ToolResult


class EventInput(BaseModel):
    value: str


class EventTool(SEAMTool):
    name = "event_tool"
    input_schema = EventInput
    allowed_agents = ["AnalysisAgent"]

    def execute(self, tool_input, context: ToolExecutionContext):
        return ToolResult(success=True, tool_name=self.name, stdout=tool_input.value)


@patch("backend.tools.executor.event_bus.emit_sync")
def test_tool_executor_emits_lifecycle_events(mock_emit):
    registry = ToolRegistry()
    registry.register(EventTool())

    ToolExecutor(registry).execute_dict({
        "tool_name": "event_tool",
        "agent_name": "AnalysisAgent",
        "project_id": "p",
        "input": {"value": "ok"},
    })

    events = [call.args[0] for call in mock_emit.call_args_list]
    assert "TOOL_REQUESTED" in events
    assert "TOOL_STARTED" in events
    assert "TOOL_COMPLETED" in events
