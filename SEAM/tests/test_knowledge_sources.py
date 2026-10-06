import pytest

from backend.knowledge.indexer import index_knowledge, load_document
from backend.knowledge.knowledge_service import KnowledgeService
from backend.knowledge.models import (
    KnowledgeSource,
    KnowledgeSourceValidationError,
    validate_knowledge_source,
)


@pytest.fixture()
def indexed_service(tmp_path):
    service = KnowledgeService(persist_dir=str(tmp_path / "chroma"))
    index_knowledge(service=service)
    return service


def test_authoritative_healthcare_source_metadata_survives_retrieval(indexed_service):
    result = indexed_service.retrieve_domain_aware(
        query="hospital healthcare digital health patient authorization audit",
        domain="healthcare",
        top_k=6,
    )

    assert result["results"]
    who_items = [item for item in result["results"] if item["organization"] == "World Health Organization"]
    assert who_items
    assert who_items[0]["source_type"] == "AUTHORITATIVE"
    assert who_items[0]["url"] == "https://www.who.int/publications/i/item/9789241550505"
    assert who_items[0]["status"] == "ACTIVE"
    assert who_items[0]["source_id"]


def test_official_technical_documentation_can_be_retrieved(indexed_service):
    result = indexed_service.retrieve_domain_aware(
        query="FastAPI typed request response models API validation",
        domain="general",
        top_k=6,
    )

    organizations = {item["organization"] for item in result["results"]}
    source_types = {item["source_type"] for item in result["results"]}

    assert "FastAPI" in organizations
    assert "OFFICIAL_TECHNICAL_DOCUMENTATION" in source_types


def test_academic_source_can_be_ingested_and_retrieved(indexed_service):
    result = indexed_service.retrieve_domain_aware(
        query="retrieval augmented generation provenance source metadata vector index",
        domain="general",
        top_k=8,
    )

    academic = [item for item in result["results"] if item["source_type"] == "ACADEMIC"]
    assert academic
    assert any("10.48550/arXiv.2005.11401" in item["metadata"].get("doi", "") for item in academic)


def test_validated_project_knowledge_can_be_retrieved(indexed_service):
    result = indexed_service.retrieve_domain_aware(
        query="finance expense tracker concurrent transactions reporting PostgreSQL auditability",
        domain="finance",
        top_k=8,
    )

    assert any(item["source_type"] == "VALIDATED_PROJECT_KNOWLEDGE" for item in result["results"])


def test_unvalidated_document_excluded_from_production_retrieval(tmp_path):
    from backend.knowledge.models import KnowledgeDocument

    service = KnowledgeService(persist_dir=str(tmp_path / "chroma"))
    service.ingest_document(KnowledgeDocument(
        title="Pending OWASP-like Claim",
        source="manual/pending.md",
        source_type="AUTHORITATIVE",
        category="security",
        domain="general",
        topic="input_validation",
        content="This pending source must not be returned.",
        validated="PENDING",
        tags=["input_validation", "security", "general"],
    ))

    result = service.retrieve_domain_aware("pending source input validation", "general", top_k=3)
    assert result["results"] == []


def test_invalid_fake_authoritative_url_rejected():
    source = KnowledgeSource(
        source_type="AUTHORITATIVE",
        organization="OWASP",
        title="Fake OWASP Document",
        url="https://fake.example.com/owasp",
        domain="general",
        category="security",
        topic="input_validation",
        status="ACTIVE",
    )

    with pytest.raises(KnowledgeSourceValidationError):
        validate_knowledge_source(source)


def test_missing_required_source_metadata_rejected():
    source = KnowledgeSource(
        source_type="SEAM_CURATED",
        organization=None,
        title="Missing Organization",
        domain="general",
        category="coding",
        topic="python",
        status="ACTIVE",
    )

    with pytest.raises(KnowledgeSourceValidationError):
        validate_knowledge_source(source)


def test_indexer_loads_authoritative_metadata():
    from pathlib import Path

    doc = load_document(Path("knowledge/authoritative/security/owasp_input_validation.md"))

    assert doc.source_metadata is not None
    assert doc.source_metadata.source_type == "AUTHORITATIVE"
    assert doc.source_metadata.organization == "OWASP"
    assert doc.source_metadata.url.startswith("https://cheatsheetseries.owasp.org/")


def test_indexer_loads_project_relative_knowledge_path_from_parent_cwd(monkeypatch):
    from pathlib import Path

    parent_root = Path(__file__).resolve().parents[2]
    monkeypatch.chdir(parent_root)

    doc = load_document(Path("knowledge/authoritative/security/owasp_input_validation.md"))

    assert doc.source == "authoritative/security/owasp_input_validation.md"
    assert doc.source_metadata is not None
    assert doc.source_metadata.organization == "OWASP"
