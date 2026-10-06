from backend.github.intelligence_models import RepositoryRecord
from backend.github.intelligence_service import GitHubIntelligenceService
from backend.github.registry import RepositoryRegistry


class FailingClient:
    last_error = "GitHub API unavailable"

    def get_latest_commit_sha(self, owner, repo, branch):
        return None


def test_api_failure_marks_cached_repository_stale(tmp_path):
    registry = RepositoryRegistry(base_dir=str(tmp_path))
    registry.save(RepositoryRecord(
        repository_id="owner__repo",
        owner="owner",
        name="repo",
        full_name="owner/repo",
        default_branch="main",
        last_analyzed_commit_sha="abc",
        analysis_version=1,
        status="CURRENT",
    ))
    service = GitHubIntelligenceService(client=FailingClient(), registry=registry)

    record = service.analyze_or_refresh("owner", "repo")
    context = service.get_agent_context("owner/repo")

    assert record.status == "STALE"
    assert record.stale is True
    assert context["status"] == "STALE"
    assert context["commit_sha"] == "abc"

