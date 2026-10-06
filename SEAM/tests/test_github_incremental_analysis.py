from backend.github.intelligence_models import RepositoryRecord
from backend.github.intelligence_service import GitHubIntelligenceService
from backend.github.registry import RepositoryRegistry


class IncrementalClient:
    last_error = ""

    def get_latest_commit_sha(self, owner, repo, branch):
        return "def"

    def compare_commits(self, owner, repo, before, after):
        return {"files": [{"filename": "backend/auth.py", "sha": "new", "status": "modified", "changes": 3}]}

    def get_repository_tree_payload(self, owner, repo, branch):
        return [
            {"path": "backend/auth.py", "sha": "new", "size": 100, "type": "blob"},
            {"path": "backend/users.py", "sha": "same", "size": 90, "type": "blob"},
            {"path": "tests/test_auth.py", "sha": "test", "size": 70, "type": "blob"},
        ]


def test_existing_changed_repository_runs_incremental_analysis(tmp_path):
    registry = RepositoryRegistry(base_dir=str(tmp_path))
    registry.save(RepositoryRecord(
        repository_id="owner__repo",
        owner="owner",
        name="repo",
        full_name="owner/repo",
        default_branch="main",
        current_commit_sha="abc",
        last_analyzed_commit_sha="abc",
        analysis_version=1,
        status="CURRENT",
    ))
    service = GitHubIntelligenceService(client=IncrementalClient(), registry=registry)

    record = service.analyze_or_refresh("owner", "repo")

    assert record.status == "CURRENT"
    assert record.analysis_version == 2
    assert record.last_analyzed_commit_sha == "def"
    assert record.latest_change_set is not None
    assert record.latest_change_set.modified_files == ["backend/auth.py"]
    assert "backend/auth.py" in record.intelligence.changed_files

