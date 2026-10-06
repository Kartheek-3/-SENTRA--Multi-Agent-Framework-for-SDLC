from backend.knowledge.langchain_retriever import SEAMKnowledgeRetriever
from backend.knowledge.models import KnowledgeDocument
from backend.knowledge.knowledge_service import KnowledgeService


def test_langchain_retriever_returns_documents_with_source_metadata(tmp_path):
    service = KnowledgeService(persist_dir=str(tmp_path / "chroma"))
    service.ingest_document(KnowledgeDocument(
        title="Healthcare Auth",
        source="manual/healthcare_auth.md",
        source_type="SEAM_CURATED",
        category="security",
        domain="healthcare",
        topic="authentication",
        content="Healthcare appointment systems need patient and doctor authorization checks.",
        validated="ACTIVE",
        tags=["authentication", "security", "healthcare"],
    ))
    retriever = SEAMKnowledgeRetriever(service=service, domain="healthcare", top_k=3)

    docs = retriever.invoke("patient doctor authorization")

    assert docs
    assert docs[0].metadata["domain"] == "healthcare"
    assert docs[0].metadata["source_type"] == "SEAM_CURATED"
    assert "authorization" in docs[0].page_content
