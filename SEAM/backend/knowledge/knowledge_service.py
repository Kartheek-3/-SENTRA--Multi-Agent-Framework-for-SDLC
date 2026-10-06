from typing import List, Optional, Dict, Any
from backend.knowledge.models import KnowledgeDocument, KnowledgeSearchResult, SOURCE_TYPE_PRIORITY, PRODUCTION_KNOWLEDGE_STATUSES
from backend.knowledge.document_processor import DocumentProcessor
from backend.knowledge.chroma_repository import ChromaRepository

class KnowledgeService:
    def __init__(self, persist_dir: Optional[str] = None):
        if persist_dir:
            self.repository = ChromaRepository(persist_dir=persist_dir)
        else:
            self.repository = ChromaRepository()
        self.processor = DocumentProcessor()

    def ingest_document(self, document: KnowledgeDocument):
        """Processes and adds a document to the knowledge base."""
        chunks = self.processor.process(document)
        if not chunks:
            return
        self.repository.add_chunks(chunks)
        return len(chunks)

    def validate_document(self, knowledge_id: str):
        self.repository.validate_document(knowledge_id)

    def retrieve_for_agent(self, agent_name: str, query: str, scale: Optional[str] = None, project_id: Optional[str] = None) -> str:
        """Retrieves bounded, agent-specific knowledge formatted for context injection."""
        from backend.events import event_bus

        if project_id:
            event_bus.emit_sync("RAG_RETRIEVAL_STARTED", {"project_id": project_id, "agent": agent_name, "summary": "Retrieving relevant SEAM knowledge."})
        enhanced_query = f"Scale: {scale}. {query}" if scale else query
        
        # Define agent boundaries
        profiles = {
            "AnalysisAgent": {"categories": ["domain", "security"], "top_k": 3},
            "PlanningAgent": {"categories": ["architecture", "past_project", "domain"], "top_k": 4},
            "CodingAgent": {"categories": ["coding", "architecture", "reusable_code"], "top_k": 5},
            "QAAgent": {"categories": ["testing", "security", "feedback", "lesson_learned"], "top_k": 5},
            "DeliveryAgent": {"categories": ["deployment", "documentation", "security", "testing"], "top_k": 3}
        }
        
        profile = profiles.get(agent_name)
        if not profile:
            return ""
            
        results = []
        for cat in profile["categories"]:
            cat_results = self.repository.search(query=enhanced_query, category=cat, top_k=profile["top_k"], only_validated=True)
            results.extend(cat_results)
            
        # Deduplicate and sort by score
        unique_results = {}
        for r in results:
            if r.chunk_id not in unique_results:
                unique_results[r.chunk_id] = r
                
        sorted_results = sorted(
            unique_results.values(),
            key=lambda x: (x.score, SOURCE_TYPE_PRIORITY.get(x.metadata.get("source_type", ""), 0)),
            reverse=True,
        )
        
        # Enforce hard top_k total limit across all categories for token safety
        max_total_chunks = max(profile["top_k"] * 2, 5)
        final_results = sorted_results[:max_total_chunks]
        
        if not final_results:
            if project_id:
                event_bus.emit_sync("RAG_RETRIEVAL_COMPLETED", {"project_id": project_id, "agent": agent_name, "summary": "Retrieved 0 relevant knowledge entries.", "result_count": 0})
            return "No relevant organizational knowledge found."
            
        context_parts = ["--- RETRIEVED ORGANIZATIONAL KNOWLEDGE ---"]
        for res in final_results:
            # Simple relevance filtering to avoid poisoning
            if res.score > 0.3:
                context_parts.append(
                    f"Source: {res.source} | Title: {res.metadata.get('title', '')} | "
                    f"Organization: {res.metadata.get('organization', '')} | "
                    f"Source Type: {res.metadata.get('source_type', '')} | "
                    f"URL: {res.metadata.get('url', '')} | Category: {res.category}\n{res.content}\n"
                )
            
        if project_id:
            event_bus.emit_sync("RAG_RETRIEVAL_COMPLETED", {"project_id": project_id, "agent": agent_name, "summary": f"Retrieved {len(final_results)} relevant knowledge entries.", "result_count": len(final_results)})
        return "\n".join(context_parts)

    def retrieve_structured(self, query: str, category: Optional[str] = None, top_k: int = 5) -> Dict[str, Any]:
        results = self.repository.search(query=query, category=category, top_k=top_k, only_validated=True)
        return {
            "query": query,
            "results": [
                {
                    "document_id": result.metadata.get("document_id", result.metadata.get("knowledge_id", "")),
                    "chunk_id": result.chunk_id,
                    "source_path": result.source,
                    "domain": result.metadata.get("domain", "general"),
                    "category": result.category,
                    "topic": result.metadata.get("topic", ""),
                    "source_type": result.metadata.get("source_type", ""),
                    "status": result.metadata.get("status", result.metadata.get("validated", "")),
                    "source_id": result.metadata.get("source_id", ""),
                    "organization": result.metadata.get("organization", ""),
                    "url": result.metadata.get("url", ""),
                    "version": result.metadata.get("document_version", result.metadata.get("version", "")),
                    "publication_date": result.metadata.get("publication_date", ""),
                    "accessed_date": result.metadata.get("accessed_date", ""),
                    "license": result.metadata.get("license", ""),
                    "score": result.score,
                    "content": result.content,
                }
                for result in results
            ],
        }

    def retrieve_domain_aware(
        self,
        query: str,
        domain: str,
        top_k: int = 6,
        relevance_threshold: float = 0.25,
        categories: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        normalized_domain = (domain or "general").lower()
        allowed_domains = [normalized_domain, "general"]
        categories = categories or ["domain", "architecture", "security", "testing", "coding"]
        candidates: List[KnowledgeSearchResult] = []
        for category in categories:
            candidates.extend(
                self.repository.search(
                    query=query,
                    category=category,
                    top_k=top_k,
                    only_validated=True,
                    domain=normalized_domain,
                    allowed_domains=allowed_domains,
                )
            )

        unique: Dict[str, KnowledgeSearchResult] = {}
        for item in candidates:
            item_domain = item.metadata.get("domain", "general")
            status = item.metadata.get("status", item.metadata.get("validated", "PENDING"))
            if status not in PRODUCTION_KNOWLEDGE_STATUSES:
                continue
            if item_domain not in allowed_domains:
                continue
            if item.score < relevance_threshold:
                continue
            existing = unique.get(item.chunk_id)
            if not existing or item.score > existing.score:
                unique[item.chunk_id] = item

        ordered = sorted(
            unique.values(),
            key=lambda item: (
                1 if item.metadata.get("domain", "general") == normalized_domain else 0,
                item.score,
                SOURCE_TYPE_PRIORITY.get(item.metadata.get("source_type", ""), 0),
            ),
            reverse=True,
        )[:top_k]

        return {
            "query": query,
            "domain": normalized_domain,
            "results": [
                {
                    "document_id": item.metadata.get("document_id", item.metadata.get("knowledge_id", "")),
                    "chunk_id": item.chunk_id,
                    "content": item.content,
                    "domain": item.metadata.get("domain", "general"),
                    "category": item.category,
                    "topic": item.metadata.get("topic", ""),
                    "source": item.source,
                    "source_type": item.metadata.get("source_type", ""),
                    "source_id": item.metadata.get("source_id", ""),
                    "organization": item.metadata.get("organization", ""),
                    "url": item.metadata.get("url", ""),
                    "version": item.metadata.get("version", 1),
                    "document_version": item.metadata.get("document_version", ""),
                    "publication_date": item.metadata.get("publication_date", ""),
                    "accessed_date": item.metadata.get("accessed_date", ""),
                    "license": item.metadata.get("license", ""),
                    "status": item.metadata.get("status", item.metadata.get("validated", "")),
                    "relevance_score": item.score,
                    "metadata": item.metadata,
                }
                for item in ordered
            ],
        }
