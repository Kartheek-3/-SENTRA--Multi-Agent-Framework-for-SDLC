import pytest
from backend.models.github import RepositoryCandidate
from backend.github.repository_ranker import RepositoryRanker

def test_repository_ranker_perfect_match():
    ranker = RepositoryRanker("e-commerce", ["python", "fastapi"])
    candidate = RepositoryCandidate(
        repository_url="https://github.com/test/ecommerce-api",
        owner="test",
        name="ecommerce-api",
        description="A python fastapi e-commerce backend",
        stars=1000,
        open_issues=5,
        license="mit",
        test_indicators=True,
        documentation_indicators=True,
        security_indicators=True,
        detected_technologies=["python", "fastapi", "docker"]
    )
    
    evaluation = ranker.evaluate(candidate)
    
    assert evaluation.domain_match_score > 0
    assert evaluation.technology_match_score == 100.0
    assert evaluation.testing_score == 100.0
    assert evaluation.security_score == 100.0
    assert evaluation.license_score == 100.0
    assert evaluation.overall_score > 80.0
    assert evaluation.recommendation == "SUITABLE FOR ENHANCEMENT"

def test_repository_ranker_poor_match():
    ranker = RepositoryRanker("e-commerce", ["java", "spring"])
    candidate = RepositoryCandidate(
        repository_url="https://github.com/test/random-script",
        owner="test",
        name="random-script",
        description="A random python script for data processing",
        stars=5,
        license="unknown",
        detected_technologies=["python"]
    )
    
    evaluation = ranker.evaluate(candidate)
    
    assert evaluation.domain_match_score == 0.0
    assert evaluation.technology_match_score == 0.0
    assert evaluation.license_score == 0.0
    assert evaluation.overall_score < 50.0
    assert evaluation.recommendation == "NOT SUITABLE"
    assert any("Legal risk" in r for r in evaluation.risks)
