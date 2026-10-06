from typing import Any, Dict, List, Type

from langchain_core.tools import StructuredTool
from pydantic import BaseModel

from backend.tools.schemas import RiskLevel, ToolExecutionContext, ToolResult


class SEAMTool:
    name: str = ""
    description: str = ""
    category: str = "general"
    input_schema: Type[BaseModel] = BaseModel
    output_schema: Type[BaseModel] = ToolResult
    allowed_agents: List[str] = []
    risk_level: RiskLevel = RiskLevel.READ_ONLY
    timeout: int = 30
    requires_approval: bool = False

    def validate_input(self, payload: Dict[str, Any]) -> BaseModel:
        return self.input_schema.model_validate(payload)

    def execute(self, tool_input: BaseModel, context: ToolExecutionContext) -> ToolResult:
        raise NotImplementedError

    def to_langchain_tool(self, executor):
        def invoke(**kwargs):
            request = {
                "tool_name": self.name,
                "agent_name": kwargs.pop("agent_name"),
                "project_id": kwargs.pop("project_id"),
                "task_id": kwargs.pop("task_id", None),
                "approved": kwargs.pop("approved", False),
                "input": kwargs,
            }
            return executor.execute_dict(request).model_dump()

        return StructuredTool.from_function(
            name=self.name,
            description=self.description,
            args_schema=self.input_schema,
            func=invoke,
        )
