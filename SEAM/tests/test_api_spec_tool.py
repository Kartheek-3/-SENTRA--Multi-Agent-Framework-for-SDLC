from backend.tools.builtin import APISpecValidateTool
from backend.tools.schemas import ToolExecutionContext


def test_api_spec_validate_reports_openapi_details():
    tool = APISpecValidateTool()
    spec = {"openapi": "3.0.0", "paths": {"/users": {"get": {}}}, "components": {"schemas": {"User": {}}}}

    result = tool.execute(tool.validate_input({"spec": spec}), ToolExecutionContext(project_id="p", agent_name="QAAgent"))

    assert result.structured_data["valid"] is True
    assert result.structured_data["methods"] == ["GET"]
    assert result.structured_data["schema_count"] == 1
