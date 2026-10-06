from unittest.mock import patch

from backend.github.intelligence_models import RepositoryRecord
from backend.tools.builtin import GitHubFreshnessCheckTool, GitHubRepositoryContextTool
from backend.tools.schemas import ToolExecutionContext


@patch("backend.tools.builtin.GitHubIntelligenceService")
def test_github_repository_context_tool_uses_v2_service(mock_service):
    mock_service.return_value.get_agent_context.return_value = {"repository": "owner/repo", "status": "CURRENT"}
    tool = GitHubRepositoryContextTool()

    result = tool.execute(tool.validate_input({"repository": "owner/repo"}), ToolExecutionContext(project_id="p", agent_name="AnalysisAgent"))

    assert result.success is True
    assert result.structured_data["status"] == "CURRENT"


@patch("backend.tools.builtin.GitHubIntelligenceService")
def test_github_freshness_check_returns_record(mock_service):
    mock_service.return_value.analyze_or_refresh.return_value = RepositoryRecord(repository_id="owner__repo", owner="owner", name="repo", full_name="owner/repo", status="CURRENT")
    tool = GitHubFreshnessCheckTool()

    result = tool.execute(tool.validate_input({"repository": "owner/repo"}), ToolExecutionContext(project_id="p", agent_name="SupervisorAgent"))

    assert result.success is True
    assert result.structured_data["full_name"] == "owner/repo"
