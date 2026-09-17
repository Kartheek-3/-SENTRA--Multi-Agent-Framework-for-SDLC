from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.knowledge.knowledge_service import KnowledgeService
from backend.knowledge.models import KnowledgeDocument

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

class SearchRequest(BaseModel):
    query: str
    category: str = None
    top_k: int = 3

class IngestRequest(BaseModel):
    title: str
    content: str
    category: str
    source: str
    source_type: str
    tags: list[str] = []

@router.post("/search")
def search_knowledge(req: SearchRequest):
    ks = KnowledgeService()
    results = ks.repository.search(req.query, req.category, req.top_k, only_validated=True)
    return {"results": [r.model_dump() for r in results]}

@router.post("/ingest")
def ingest_knowledge(req: IngestRequest):
    ks = KnowledgeService()
    doc = KnowledgeDocument(
        title=req.title,
        content=req.content,
        category=req.category,
        source=req.source,
        source_type=req.source_type,
        tags=req.tags,
        validated="PENDING" # Must be validated manually or by delivery
    )
    ks.ingest_document(doc)
    return {"status": "success", "knowledge_id": doc.knowledge_id}

@router.get("/categories")
def get_categories():
    return {
        "categories": [
            "domain", "architecture", "coding", "security", 
            "testing", "reusable_code", "past_project", 
            "lesson_learned", "feedback", "documentation", "deployment"
        ]
    }
