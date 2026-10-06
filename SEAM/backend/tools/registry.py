from typing import Dict, List

from backend.tools.base import SEAMTool
from backend.tools.errors import ToolRegistrationError


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, SEAMTool] = {}

    def register(self, tool: SEAMTool) -> None:
        if not tool.name:
            raise ToolRegistrationError("Tool name is required")
        if tool.name in self._tools:
            raise ToolRegistrationError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> None:
        self._tools.pop(name, None)

    def get(self, name: str) -> SEAMTool:
        if name not in self._tools:
            raise ToolRegistrationError(f"Tool is not registered: {name}")
        return self._tools[name]

    def list_tools(self) -> List[SEAMTool]:
        return [self._tools[name] for name in sorted(self._tools)]

    def get_agent_tools(self, agent_name: str) -> List[SEAMTool]:
        return [tool for tool in self.list_tools() if agent_name in tool.allowed_agents]

    def is_registered(self, name: str) -> bool:
        return name in self._tools


default_registry = ToolRegistry()
