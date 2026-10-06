from pathlib import Path

from fastapi.testclient import TestClient

from backend.knowledge.indexer import (
    discover_documents,
    document_id_for,
    index_knowledge,
    load_document,
)
from backend.knowledge.knowledge_service import KnowledgeService
from backend.main import app


def test_knowledge_repository_documents_are_discoverable():
    documents = discover_documents()

    assert len(documents) >= 27
    assert Path("domains/web_applications.md") in {
        path.relative_to(Path(__file__).resolve().parents[1] / "knowledge")
        for path in documents
    }


def test_indexer_loads_validated_metadata():
    root = Path(__file__).resolve().parents[1] / "knowledge"
    document = load_document(root / "security" / "authentication.md")

    assert document.validated == "VALIDATED"
    assert document.category == "security"
    assert "authentication" in document.tags
    assert document.knowledge_id == document_id_for(root / "security" / "authentication.md")


def test_index_and_retrieve_from_chromadb(tmp_path):
    service = KnowledgeService(persist_dir=str(tmp_path / "chroma"))
    result = index_knowledge(service=service)

    assert result["documents_indexed"] >= 27
    assert result["chunks_indexed"] >= 27
    assert result["collection_count"] >= 27

    retrieval = service.retrieve_structured(
        "FastAPI React JWT authentication SQLite API validation",
        category="security",
        top_k=3,
    )

    assert retrieval["results"]
    assert all(item["category"] == "security" for item in retrieval["results"])
    assert any("authentication" in item["source_path"] for item in retrieval["results"])


def test_rag_routes_are_registered():
    paths = set(app.openapi()["paths"].keys())

    assert "/rag/index" in paths
    assert "/rag/retrieve" in paths
    assert "/rag/status" in paths


def test_rag_status_endpoint():
    client = TestClient(app)
    response = client.get("/rag/status")

    assert response.status_code == 200
    data = response.json()
    assert data["knowledge_root_exists"] is True
    assert data["documents_on_disk"] >= 27
