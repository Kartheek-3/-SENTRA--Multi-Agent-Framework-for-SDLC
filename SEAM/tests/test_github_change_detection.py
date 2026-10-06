from backend.github.intelligence_models import RepositoryRecord
from backend.github.intelligence_service import GitHubIntelligenceService
from backend.github.registry import RepositoryRegistry


class CompareClient:
    last_error = ""

    def compare_commits(self, owner, repo, before, after):
        return {
            "files": [
                {"filename": "backend/auth.py", "sha": "1", "status": "modified", "changes": 2},
                {"filename": "backend/new_api.py", "sha": "2", "status": "added", "changes": 5},
                {"filename": "old.py", "sha": "3", "status": "removed", "changes": 1},
                {"filename": "new_name.py", "previous_filename": "old_name.py", "sha": "4", "status": "renamed"},
            ]
        }


def test_change_detection_classifies_added_modified_deleted_and_renamed(tmp_path):
    service = GitHubIntelligenceService(client=CompareClient(), registry=RepositoryRegistry(base_dir=str(tmp_path)))
    record = RepositoryRecord(
        repository_id="owner__repo",
        owner="owner",
        name="repo",
        full_name="owner/repo",
        last_analyzed_commit_sha="abc",
    )

    change_set = service._detect_changes(record, "def")

    assert change_set.modified_files == ["backend/auth.py"]
    assert change_set.added_files == ["backend/new_api.py"]
    assert change_set.deleted_files == ["old.py"]
    assert change_set.renamed_files == ["new_name.py"]

