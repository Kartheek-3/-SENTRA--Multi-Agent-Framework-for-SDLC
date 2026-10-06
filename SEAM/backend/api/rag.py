from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.events import event_bus
from backend.knowledge.indexer import KNOWLEDGE_ROOT, index_knowledge
from backend.knowledge.knowledge_service import KnowledgeService


router = APIRouter(prefix="/rag", tags=["rag"])


class RetrieveRequest(BaseModel):
    query: str
    domain: Optional[str] = None
    current_task: Optional[str] = None
    technology_stack: list[str] = []
    agent: Optional[str] = None
    category: Optional[str] = None
    top_k: int = 5


@router.post("/index")
def rag_index():
    try:
        event_bus.emit_sync("RAG_INDEX_STARTED", {"summary": "Indexing SEAM knowledge repository."})
        result = index_knowledge()
        event_bus.emit_sync("RAG_INDEX_COMPLETED", {"summary": f"Indexed {result['documents_indexed']} knowledge documents.", **result})
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/retrieve")
def rag_retrieve(req: RetrieveRequest):
    try:
        query = " ".join(part for part in [
            req.query,
            req.domain or "",
            req.current_task or "",
            " ".join(req.technology_stack),
            req.agent or "",
        ] if part).strip()
        event_bus.emit_sync("RAG_RETRIEVAL_STARTED", {"summary": "Retrieving relevant SEAM knowledge."})
        service = KnowledgeService()
        if req.domain:
            result = service.retrieve_domain_aware(query=query, domain=req.domain, top_k=req.top_k)
        else:
            result = service.retrieve_structured(query=query, category=req.category, top_k=req.top_k)
        event_bus.emit_sync("RAG_RETRIEVAL_COMPLETED", {
            "summary": f"Retrieved {len(result['results'])} relevant knowledge entries.",
            "result_count": len(result["results"]),
        })
        return result
    except Exception as exc:
        event_bus.emit_sync("RAG_RETRIEVAL_FAILED", {"summary": "RAG retrieval failed.", "error": str(exc)})
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/status")
def rag_status():
    try:
        ks = KnowledgeService()
        docs = list(KNOWLEDGE_ROOT.rglob("*.md")) if KNOWLEDGE_ROOT.exists() else []
        return {
            "knowledge_root": str(KNOWLEDGE_ROOT),
            "knowledge_root_exists": KNOWLEDGE_ROOT.exists(),
            "documents_on_disk": len(docs),
            "collection_count": ks.repository.count(),
            "mode": ks.repository.mode,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
