import pytest
from backend.knowledge.models import KnowledgeDocument
from backend.knowledge.sanitizer import KnowledgeSanitizer
from backend.knowledge.document_processor import DocumentProcessor
from backend.knowledge.knowledge_service import KnowledgeService
import tempfile
import os
import shutil

def test_knowledge_document_model():
    doc = KnowledgeDocument(
        title="Test Doc",
        source="Test",
        source_type="manual",
        category="domain",
        content="This is a test."
    )
    assert doc.validated == "PENDING"
    assert len(doc.knowledge_id) > 10

def test_sanitizer():
    sanitizer = KnowledgeSanitizer()
    bad_text = "Here is my secret= 'AKIA1234567890123456' and password=\"supersecret123\""
    clean = sanitizer.sanitize(bad_text)
    assert "AKIA" not in clean
    assert "supersecret123" not in clean
    assert "REDACTED" in clean

def test_document_processor():
    proc = DocumentProcessor()
    doc = KnowledgeDocument(
        title="Big Doc",
        source="Test",
        source_type="manual",
        category="domain",
        content="A" * 1500
    )
    chunks = proc.process(doc)
    assert len(chunks) > 1
    assert chunks[0].category == "domain"

@pytest.fixture
def temp_chroma_dir():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

def test_knowledge_service_end_to_end(temp_chroma_dir):
    ks = KnowledgeService(persist_dir=temp_chroma_dir)
    doc = KnowledgeDocument(
        title="Domain Rules",
        source="Manual",
        source_type="manual",
        category="domain",
        content="The main currency is SEAM_COIN. Never use USD.",
        validated="VALIDATED"
    )
    ks.ingest_document(doc)
    
    # Test retrieval
    context = ks.retrieve_for_agent("AnalysisAgent", "What currency should I use?")
    assert "SEAM_COIN" in context
    assert "RETRIEVED" in context
    
    # Test bounds (CodingAgent shouldn't retrieve 'domain' directly in its top profile for this query if not specified, 
    # but let's test a category it does retrieve like 'coding')
    doc_code = KnowledgeDocument(
        title="Coding Standard",
        source="Manual",
        source_type="manual",
        category="coding",
        content="Always use standard pydantic models.",
        validated="VALIDATED"
    )
    ks.ingest_document(doc_code)
    
    code_context = ks.retrieve_for_agent("CodingAgent", "How to write models?")
    assert "pydantic" in code_context
