from backend.tools.builtin import MermaidGenerateTool
from backend.tools.schemas import ToolExecutionContext


def test_mermaid_tool_generates_source_and_artifact(tmp_path):
    tool = MermaidGenerateTool()

    result = tool.execute(tool.validate_input({
        "diagram_type": "architecture",
        "diagram_data": {"nodes": [{"id": "api", "label": "API"}], "edges": []},
    }), ToolExecutionContext(project_id="p", agent_name="PlanningAgent", project_root=str(tmp_path)))

    assert result.success is True
    assert "flowchart TD" in result.stdout
    assert result.artifacts
