from backend.github.intelligence_models import RepositoryRecord, RepositorySnapshot
from backend.github.intelligence_service import GitHubIntelligenceService
from backend.github.registry import RepositoryRegistry


def test_repository_registry_persists_record_and_snapshot(tmp_path):
    registry = RepositoryRegistry(base_dir=str(tmp_path))
    record = RepositoryRecord(
        repository_id="owner__repo",
        owner="owner",
        name="repo",
        full_name="owner/repo",
        current_commit_sha="abc",
        last_analyzed_commit_sha="abc",
        analysis_version=1,
        status="CURRENT",
    )
    snapshot = RepositorySnapshot(repository="owner/repo", commit_sha="abc", branch="main")

    registry.save(record)
    registry.save_snapshot(snapshot)

    loaded = registry.get("owner/repo")
    loaded_snapshot = registry.latest_snapshot("owner/repo")

    assert loaded is not None
    assert loaded.status == "CURRENT"
    assert loaded_snapshot is not None
    assert loaded_snapshot.commit_sha == "abc"


class NewRepositoryClient:
    last_error = ""

    def get_repository(self, owner, repo):
        return {
            "default_branch": "main",
            "clone_url": "https://github.com/owner/repo.git",
            "html_url": "https://github.com/owner/repo",
        }

    def get_latest_commit_sha(self, owner, repo, branch):
        return "abc"

    def get_repository_tree_payload(self, owner, repo, branch):
        return [
            {"path": "README.md", "sha": "readme", "size": 10, "type": "blob"},
            {"path": "requirements.txt", "sha": "req", "size": 20, "type": "blob"},
            {"path": "backend/api.py", "sha": "api", "size": 30, "type": "blob"},
        ]


def test_new_repository_triggers_full_analysis(tmp_path):
    service = GitHubIntelligenceService(
        client=NewRepositoryClient(),
        registry=RepositoryRegistry(base_dir=str(tmp_path)),
    )

    record = service.analyze_or_refresh("owner", "repo")

    assert record.status == "CURRENT"
    assert record.analysis_version == 1
    assert record.last_analyzed_commit_sha == "abc"
    assert record.file_count == 3
    assert "Python" in record.intelligence.technologies


class UnchangedClient:
    last_error = ""

    def get_latest_commit_sha(self, owner, repo, branch):
        return "abc"


def test_existing_unchanged_repository_uses_cached_intelligence(tmp_path):
    registry = RepositoryRegistry(base_dir=str(tmp_path))
    registry.save(RepositoryRecord(
        repository_id="owner__repo",
        owner="owner",
        name="repo",
        full_name="owner/repo",
        default_branch="main",
        current_commit_sha="abc",
        last_analyzed_commit_sha="abc",
        analysis_version=3,
        status="CURRENT",
    ))
    service = GitHubIntelligenceService(client=UnchangedClient(), registry=registry)

    record = service.analyze_or_refresh("owner", "repo")

    assert record.status == "CURRENT"
    assert record.analysis_version == 3
    assert record.last_analyzed_commit_sha == "abc"
