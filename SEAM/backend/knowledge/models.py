from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import time
import uuid
import hashlib

class KnowledgeDocument(BaseModel):
    knowledge_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    source: str
    source_type: str  # e.g., "github", "project", "manual"
    category: str     # domain, architecture, coding, security, testing, documentation, etc.
    project_id: Optional[str] = None
    content: str
    version: int = 1
    created_at: float = Field(default_factory=time.time)
    validated: str = "PENDING"  # PENDING, VALIDATED, REJECTED
    sensitivity: str = "internal"
    tags: List[str] = Field(default_factory=list)
    
    def generate_hash(self) -> str:
        return hashlib.sha256(f"{self.source}_{self.content}".encode()).hexdigest()

class KnowledgeChunk(BaseModel):
    chunk_id: str
    knowledge_id: str
    content: str
    category: str
    source: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class KnowledgeSearchResult(BaseModel):
    chunk_id: str
    content: str
    score: float
    category: str
    source: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
