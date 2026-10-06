from unittest.mock import patch

from backend.tools.builtin import RAGSearchTool
from backend.tools.schemas import ToolExecutionContext


@patch("backend.tools.builtin.KnowledgeService")
def test_rag_tool_uses_existing_knowledge_service(mock_service):
    mock_service.return_value.retrieve_domain_aware.return_value = {"results": [{"content": "FastAPI", "source_type": "SEAM_CURATED"}]}
    tool = RAGSearchTool()

    result = tool.execute(tool.validate_input({"query": "api", "domain": "general"}), ToolExecutionContext(project_id="p", agent_name="AnalysisAgent"))

    assert result.success is True
    assert result.structured_data["results"][0]["content"] == "FastAPI"
