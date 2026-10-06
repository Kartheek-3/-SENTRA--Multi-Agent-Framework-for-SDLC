import os
from typing import Iterable, Optional

from backend.tools.errors import ToolPermissionError
from backend.tools.registry import ToolRegistry
from backend.tools.schemas import RiskLevel, ToolExecutionContext, ToolPermission


RISK_ORDER = {
    RiskLevel.READ_ONLY: 0,
    RiskLevel.LOW: 1,
    RiskLevel.MEDIUM: 2,
    RiskLevel.HIGH: 3,
    RiskLevel.DESTRUCTIVE: 4,
}


AGENT_MAX_RISK = {
    "AnalysisAgent": RiskLevel.READ_ONLY,
    "PlanningAgent": RiskLevel.LOW,
    "SupervisorAgent": RiskLevel.READ_ONLY,
    "CodingAgent": RiskLevel.MEDIUM,
    "QAAgent": RiskLevel.MEDIUM,
    "DeliveryAgent": RiskLevel.MEDIUM,
}


class PermissionEngine:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def check(self, tool_name: str, context: ToolExecutionContext, paths: Optional[Iterable[str]] = None) -> ToolPermission:
        if not self.registry.is_registered(tool_name):
            return ToolPermission(allowed=False, reason=f"Tool is not registered: {tool_name}")
        tool = self.registry.get(tool_name)
        if context.agent_name not in tool.allowed_agents:
            return ToolPermission(allowed=False, reason="Agent is not permitted to use this tool")
        max_risk = AGENT_MAX_RISK.get(context.agent_name, RiskLevel.READ_ONLY)
        if (tool.requires_approval or tool.risk_level in {RiskLevel.HIGH, RiskLevel.DESTRUCTIVE}) and not context.approved:
            return ToolPermission(
                allowed=False,
                reason=f"Explicit approval required for {tool.risk_level.value} risk operation",
                requires_approval=True,
            )
        approval_gated_risk = tool.risk_level in {RiskLevel.HIGH, RiskLevel.DESTRUCTIVE}
        if not approval_gated_risk and RISK_ORDER[tool.risk_level] > RISK_ORDER[max_risk]:
            return ToolPermission(allowed=False, reason=f"{tool.risk_level} exceeds {context.agent_name} policy")
        if context.workflow_status in {"failed", "cancelled"}:
            return ToolPermission(allowed=False, reason=f"Workflow state does not allow tool execution: {context.workflow_status}")
        for path in paths or []:
            self.ensure_safe_path(path, context.project_root)
        return ToolPermission(allowed=True)

    def ensure_safe_path(self, path: str, project_root: Optional[str]) -> str:
        if not project_root:
            project_root = os.path.abspath(os.path.join(os.getcwd(), "generated_projects"))
        root = os.path.abspath(project_root)
        candidate = os.path.abspath(os.path.join(root, path)) if not os.path.isabs(path) else os.path.abspath(path)
        if os.path.commonpath([root, candidate]) != root:
            raise ToolPermissionError(f"Path escapes approved project root: {path}")
        blocked = {".env", ".env.local", ".env.production"}
        if os.path.basename(candidate).lower() in blocked:
            raise ToolPermissionError("Secret-bearing environment files are not available to tools")
        return candidate
