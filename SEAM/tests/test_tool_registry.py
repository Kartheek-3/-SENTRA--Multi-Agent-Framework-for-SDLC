import pytest

from backend.tools.base import SEAMTool
from backend.tools.errors import ToolRegistrationError
from backend.tools.registry import ToolRegistry


class DummyTool(SEAMTool):
    name = "dummy"
    allowed_agents = ["AnalysisAgent"]


def test_tool_registry_registers_and_lists_deterministically():
    registry = ToolRegistry()
    registry.register(DummyTool())

    assert registry.is_registered("dummy")
    assert registry.get("dummy").name == "dummy"
    assert [tool.name for tool in registry.list_tools()] == ["dummy"]
    assert [tool.name for tool in registry.get_agent_tools("AnalysisAgent")] == ["dummy"]


def test_tool_registry_rejects_duplicate_registration():
    registry = ToolRegistry()
    registry.register(DummyTool())

    with pytest.raises(ToolRegistrationError):
        registry.register(DummyTool())
