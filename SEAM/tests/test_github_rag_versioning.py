from backend.github.registry import RepositoryRegistry


def test_repository_rag_supersession_marker_is_persisted(tmp_path):
    registry = RepositoryRegistry(base_dir=str(tmp_path))

    marker = registry.mark_repository_rag_superseded("owner/repo", "def")

    assert marker["repository"] == "owner/repo"
    assert marker["active_commit_sha"] == "def"
    assert marker["status"] == "SUPERSEDED_PREVIOUS_REPOSITORY_CONTEXT"
