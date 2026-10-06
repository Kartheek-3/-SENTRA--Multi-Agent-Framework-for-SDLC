import os
from typing import Any, Dict, Optional

from backend.models.state import ProjectState
from backend.tools.executor import ToolExecutor
from backend.tools.registry import default_registry
from backend.tools.schemas import ToolRequest, ToolResult


class AgentToolContext:
    def __init__(self, state: ProjectState, agent_name: str, task_id: Optional[str] = None):
        self.state = state
        self.agent_name = agent_name
        self.task_id = task_id
        self.executor = ToolExecutor(default_registry)

    @property
    def project_root(self) -> str:
        return os.path.abspath(os.path.join("generated_projects", self.state.project_name))

    def run(self, tool_name: str, payload: Dict[str, Any], approved: bool = False) -> ToolResult:
        request = ToolRequest(
            tool_name=tool_name,
            agent_name=self.agent_name,
            project_id=self.state.project_id,
            task_id=self.task_id,
            input=payload,
            approved=approved,
        )
        result = self.executor.execute(request, project_root=self.project_root)
        self.state.execution_history.append({
            "agent": self.agent_name,
            "event": "tool_invocation",
            "tool_name": tool_name,
            "success": result.success,
            "execution_id": result.execution_id,
            "duration_ms": result.duration_ms,
            "error": result.error.message if result.error else None,
        })
        return result


def run_agent_tool(
    state: ProjectState,
    agent_name: str,
    tool_name: str,
    payload: Dict[str, Any],
    task_id: Optional[str] = None,
    approved: bool = False,
) -> ToolResult:
    return AgentToolContext(state, agent_name, task_id=task_id).run(tool_name, payload, approved=approved)
