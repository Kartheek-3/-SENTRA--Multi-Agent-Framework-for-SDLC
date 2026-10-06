import pytest

from backend.tools.base import SEAMTool
from backend.tools.builtin import FileDeleteTool, FileReadTool, FileWriteTool
from backend.tools.permissions import PermissionEngine
from backend.tools.registry import ToolRegistry
from backend.tools.schemas import RiskLevel, ToolExecutionContext


class DestructiveCodingTool(SEAMTool):
    name = "destructive_coding_tool"
    allowed_agents = ["CodingAgent"]
    risk_level = RiskLevel.DESTRUCTIVE


def engine_with(*tools):
    registry = ToolRegistry()
    for tool in tools:
        registry.register(tool)
    return PermissionEngine(registry)


def test_read_only_tool_allowed():
    engine = engine_with(FileReadTool())

    permission = engine.check("file_read", ToolExecutionContext(project_id="p", agent_name="CodingAgent"))

    assert permission.allowed is True
    assert permission.requires_approval is False


def test_low_or_medium_write_tool_allowed_for_coding():
    engine = engine_with(FileWriteTool())

    permission = engine.check("file_write", ToolExecutionContext(project_id="p", agent_name="CodingAgent"))

    assert permission.allowed is True
    assert permission.requires_approval is False


def test_permission_denies_disallowed_agent():
    engine = engine_with(FileDeleteTool())

    permission = engine.check("file_delete", ToolExecutionContext(project_id="p", agent_name="AnalysisAgent"))

    assert permission.allowed is False
    assert permission.requires_approval is False
    assert permission.reason == "Agent is not permitted to use this tool"


def test_permission_requires_approval_for_high_risk():
    engine = engine_with(FileDeleteTool())

    permission = engine.check("file_delete", ToolExecutionContext(project_id="p", agent_name="CodingAgent"))

    assert permission.allowed is False
    assert permission.requires_approval is True
    assert permission.reason == "Explicit approval required for HIGH risk operation"


def test_permission_requires_approval_for_destructive_risk():
    engine = engine_with(DestructiveCodingTool())

    permission = engine.check("destructive_coding_tool", ToolExecutionContext(project_id="p", agent_name="CodingAgent"))

    assert permission.allowed is False
    assert permission.requires_approval is True
    assert permission.reason == "Explicit approval required for DESTRUCTIVE risk operation"


def test_high_risk_allowed_after_explicit_approval_for_allowed_agent():
    engine = engine_with(FileDeleteTool())

    permission = engine.check("file_delete", ToolExecutionContext(project_id="p", agent_name="CodingAgent", approved=True))

    assert permission.allowed is True
    assert permission.requires_approval is False


def test_missing_tool_denied_without_approval():
    engine = engine_with()

    permission = engine.check("missing_tool", ToolExecutionContext(project_id="p", agent_name="CodingAgent"))

    assert permission.allowed is False
    assert permission.requires_approval is False


def test_path_traversal_is_prevented(tmp_path):
    engine = engine_with(FileReadTool())

    with pytest.raises(Exception):
        engine.ensure_safe_path("../secret.txt", str(tmp_path))


def test_env_file_access_is_prevented(tmp_path):
    engine = engine_with(FileReadTool())

    with pytest.raises(Exception):
        engine.ensure_safe_path(".env", str(tmp_path))
