import shutil
from pathlib import Path

import pytest

from backend.api.projects import projects_db
from backend.knowledge.domain_intelligence import DomainIntelligenceService
from backend.knowledge.indexer import index_knowledge
from backend.knowledge.knowledge_service import KnowledgeService
from backend.models.state import ProjectState


@pytest.fixture()
def indexed_service(tmp_path):
    service = KnowledgeService(persist_dir=str(tmp_path / "chroma"))
    index_knowledge(service=service)
    return service


@pytest.fixture(autouse=True)
def clean_projects_db():
    original = dict(projects_db)
    yield
    projects_db.clear()
    projects_db.update(original)


def _state(project_id: str, requirement: str) -> ProjectState:
    state = ProjectState(project_id=project_id, user_requirement=requirement)
    projects_db[project_id] = state
    return state


def test_healthcare_domain_identification_retrieval_and_artifacts(indexed_service):
    state = _state(
        "domain-healthcare",
        "Build a hospital appointment management system with patient registration, doctor availability and appointment booking.",
    )
    service = DomainIntelligenceService()

    context = service.retrieve_context(state, service=indexed_service)
    artifacts = service.persist_artifacts(state)

    assert context.detected_domain.domain == "healthcare"
    assert "appointment" in context.retrieval_query.lower()
    assert context.status == "VALIDATED_DOMAIN_KNOWLEDGE_FOUND"
    assert context.retrieved_documents
    assert all(item.status in {"VALIDATED", "ACTIVE"} for item in context.retrieved_documents)
    assert any(item.domain == "healthcare" for item in context.retrieved_documents)
    assert any("healthcare/" in item.source for item in context.retrieved_documents)
    assert any(artifact["path"] == "analysis/domain_context.md" for artifact in artifacts)
    assert Path("generated_projects/healthcare/analysis/domain_context.md").exists()
    assert Path("generated_projects/healthcare/analysis/domain_traceability.md").exists()
    shutil.rmtree("generated_projects/healthcare", ignore_errors=True)


def test_ecommerce_domain_identification_and_retrieval(indexed_service):
    state = _state(
        "domain-ecommerce",
        "Build an e-commerce shopping application with product catalog, cart, checkout, payment status and inventory updates.",
    )
    context = DomainIntelligenceService().retrieve_context(state, service=indexed_service)

    assert context.detected_domain.domain == "ecommerce"
    assert "checkout" in context.retrieval_query.lower()
    assert any(item.domain == "ecommerce" for item in context.retrieved_documents)
    assert all(item.domain in {"ecommerce", "general"} for item in context.retrieved_documents)


def test_finance_domain_identification_and_retrieval(indexed_service):
    state = _state(
        "domain-finance",
        "Build a financial expense and transaction tracking app with audit reports and account-level authorization.",
    )
    context = DomainIntelligenceService().retrieve_context(state, service=indexed_service)

    assert context.detected_domain.domain == "finance"
    assert "transaction" in context.retrieval_query.lower()
    assert any(item.domain == "finance" for item in context.retrieved_documents)
    assert all(item.domain in {"finance", "general"} for item in context.retrieved_documents)


def test_cross_domain_isolation(indexed_service):
    cases = [
        ("healthcare", "Build a hospital patient appointment booking system.", {"finance", "ecommerce"}),
        ("ecommerce", "Build a product catalog shopping cart and checkout application.", {"healthcare", "finance"}),
        ("finance", "Build an expense transaction ledger with reporting.", {"healthcare", "ecommerce"}),
    ]

    service = DomainIntelligenceService()
    for expected, requirement, forbidden_domains in cases:
        state = _state(f"isolation-{expected}", requirement)
        context = service.retrieve_context(state, service=indexed_service)
        returned_domains = {item.domain for item in context.retrieved_documents}

        assert context.detected_domain.domain == expected
        assert forbidden_domains.isdisjoint(returned_domains)
        assert returned_domains.issubset({expected, "general"})


def test_no_unvalidated_domain_knowledge_is_returned(tmp_path):
    from backend.knowledge.models import KnowledgeDocument

    service = KnowledgeService(persist_dir=str(tmp_path / "chroma"))
    service.ingest_document(KnowledgeDocument(
        title="Unvalidated Healthcare Claim",
        source="manual/unvalidated_healthcare.md",
        source_type="manual",
        category="domain",
        domain="healthcare",
        topic="unsafe_claim",
        content="This pending healthcare knowledge must never be returned.",
        validated="PENDING",
        tags=["unsafe_claim", "healthcare"],
    ))

    state = _state("domain-pending", "Build a hospital appointment system.")
    context = DomainIntelligenceService().retrieve_context(state, service=service)

    assert context.detected_domain.domain == "healthcare"
    assert context.status == "NO_VALIDATED_DOMAIN_KNOWLEDGE_FOUND"
    assert context.retrieved_documents == []
