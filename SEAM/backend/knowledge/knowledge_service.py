from typing import List, Optional
from backend.knowledge.models import KnowledgeDocument, KnowledgeSearchResult
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

    def validate_document(self, knowledge_id: str):
        self.repository.validate_document(knowledge_id)

    def retrieve_for_agent(self, agent_name: str, query: str, scale: Optional[str] = None) -> str:
        """Retrieves bounded, agent-specific knowledge formatted for context injection."""
        enhanced_query = f"Scale: {scale}. {query}" if scale else query
        
        # Define agent boundaries
        profiles = {
            "AnalysisAgent": {"categories": ["domain"], "top_k": 3},
            "PlanningAgent": {"categories": ["architecture", "past_project"], "top_k": 4},
            "CodingAgent": {"categories": ["coding", "architecture", "reusable_code"], "top_k": 5},
            "QAAgent": {"categories": ["testing", "security", "feedback", "lesson_learned"], "top_k": 5},
            "DeliveryAgent": {"categories": ["deployment", "documentation"], "top_k": 3}
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
                
        sorted_results = sorted(unique_results.values(), key=lambda x: x.score, reverse=True)
        
        # Enforce hard top_k total limit across all categories for token safety
        max_total_chunks = max(profile["top_k"] * 2, 5)
        final_results = sorted_results[:max_total_chunks]
        
        if not final_results:
            return "No relevant organizational knowledge found."
            
        context_parts = ["--- RETRIEVED ORGANIZATIONAL KNOWLEDGE ---"]
        for res in final_results:
            # Simple relevance filtering to avoid poisoning
            if res.score > 0.3:
                context_parts.append(f"Source: {res.source} | Category: {res.category}\n{res.content}\n")
            
        return "\n".join(context_parts)
