from typing import List
from backend.knowledge.models import KnowledgeDocument, KnowledgeChunk
from backend.knowledge.sanitizer import KnowledgeSanitizer
import uuid

class DocumentProcessor:
    def __init__(self):
        self.sanitizer = KnowledgeSanitizer()
        self.chunk_size = 1000
        self.chunk_overlap = 100

    def _split_text(self, text: str) -> List[str]:
        if not text:
            return []
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunks.append(text[start:end])
            if end >= len(text):
                break
            start = end - self.chunk_overlap
        return chunks

    def process(self, document: KnowledgeDocument) -> List[KnowledgeChunk]:
        # 1. Sanitize
        clean_text = self.sanitizer.sanitize(document.content)
        
        # 2. Chunk
        texts = self._split_text(clean_text)
        
        # 3. Create Chunks
        chunks = []
        topic = document.topic or (document.tags[0] if document.tags else "")
        source = document.source_metadata
        for i, text in enumerate(texts):
            chunk = KnowledgeChunk(
                chunk_id=f"{document.knowledge_id}_{i}",
                knowledge_id=document.knowledge_id,
                content=text,
                category=document.category,
                source=document.source,
                metadata={
                    "title": document.title,
                    "source_type": document.source_type,
                    "source_id": source.source_id if source else document.knowledge_id,
                    "organization": source.organization if source else "",
                    "url": source.url if source else "",
                    "document_version": source.document_version if source else str(document.version),
                    "publication_date": source.publication_date if source else "",
                    "accessed_date": source.accessed_date if source else "",
                    "license": source.license if source else "",
                    "authors": source.authors if source else "",
                    "publication": source.publication if source else "",
                    "year": source.year if source else "",
                    "doi": source.doi if source else "",
                    "project_name": source.project_name if source else "",
                    "project_version": source.project_version if source else "",
                    "validation_result": source.validation_result if source else "",
                    "project_id": document.project_id or "",
                    "validated": document.validated,
                    "tags": ",".join(document.tags),
                    "version": document.version,
                    "document_id": document.knowledge_id,
                    "topic": topic,
                    "domain": document.domain or "general",
                    "status": document.validated,
                    "updated_at": document.updated_at,
                }
            )
            chunks.append(chunk)
            
        return chunks
