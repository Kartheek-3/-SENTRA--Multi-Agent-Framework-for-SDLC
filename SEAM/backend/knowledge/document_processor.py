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
                    "project_id": document.project_id or "",
                    "validated": document.validated,
                    "tags": ",".join(document.tags)
                }
            )
            chunks.append(chunk)
            
        return chunks
