from typing import Any, List, Optional

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import ConfigDict, Field

from backend.knowledge.knowledge_service import KnowledgeService


class SEAMKnowledgeRetriever(BaseRetriever):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    service: KnowledgeService = Field(default_factory=KnowledgeService)
    domain: Optional[str] = None
    category: Optional[str] = None
    top_k: int = 5

    def _get_relevant_documents(self, query: str, *, run_manager: Any = None) -> List[Document]:
        if self.domain:
            result = self.service.retrieve_domain_aware(query=query, domain=self.domain, top_k=self.top_k)
            items = result["results"]
        else:
            result = self.service.retrieve_structured(query=query, category=self.category, top_k=self.top_k)
            items = result["results"]

        documents: List[Document] = []
        for item in items:
            metadata = {
                "document_id": item.get("document_id", ""),
                "chunk_id": item.get("chunk_id", ""),
                "source": item.get("source") or item.get("source_path", ""),
                "source_type": item.get("source_type", ""),
                "organization": item.get("organization", ""),
                "url": item.get("url", ""),
                "domain": item.get("domain", "general"),
                "category": item.get("category", ""),
                "topic": item.get("topic", ""),
                "status": item.get("status", ""),
                "score": item.get("relevance_score", item.get("score", 0.0)),
            }
            documents.append(Document(page_content=item.get("content", ""), metadata=metadata))
        return documents
