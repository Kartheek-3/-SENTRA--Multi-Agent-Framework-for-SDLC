import pytest
from backend.models.github import RepositoryCandidate, RepositoryEvaluation, RepositorySelection

def test_repository_candidate_model():
    candidate = RepositoryCandidate(
        repository_url="https://github.com/example/test",
        owner="example",
        name="test",
        stars=100
    )
    assert candidate.stars == 100
    assert candidate.license == "unknown"
    assert candidate.test_indicators is False

def test_repository_evaluation_model():
    eval = RepositoryEvaluation(repository_url="https://github.com/example/test")
    assert eval.overall_score == 0.0
    assert eval.strengths == []

def test_repository_selection_model():
    sel = RepositorySelection()
    assert sel.reuse_existing is False
    assert sel.confidence == 0.0
