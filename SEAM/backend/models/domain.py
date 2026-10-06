from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DomainIdentification(BaseModel):
    domain: str = Field(description="Normalized project domain, such as healthcare, ecommerce, finance, or general")
    subdomain: Optional[str] = Field(default=None, description="More specific business area when identifiable")
    relevant_technologies: List[str] = Field(default_factory=list)
    domain_requirements: List[str] = Field(default_factory=list)
    domain_constraints: List[str] = Field(default_factory=list)
    domain_sensitive_concerns: List[str] = Field(default_factory=list)
    retrieval_terms: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence: List[str] = Field(default_factory=list)


class RetrievedKnowledge(BaseModel):
    document_id: str
    chunk_id: str
    content: str
    domain: str = "general"
    category: str
    topic: str = ""
    source: str
    source_type: str = ""
    source_id: str = ""
    organization: str = ""
    url: str = ""
    document_version: str = ""
    publication_date: str = ""
    accessed_date: str = ""
    license: str = ""
    version: int = 1
    status: str = "VALIDATED"
    relevance_score: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DomainContext(BaseModel):
    detected_domain: DomainIdentification
    retrieval_query: str
    retrieved_documents: List[RetrievedKnowledge] = Field(default_factory=list)
    status: str = "NO_VALIDATED_DOMAIN_KNOWLEDGE_FOUND"
    generated_at: str


class DomainTraceability(BaseModel):
    user_requirement: str
    detected_domain: str
    subdomain: Optional[str] = None
    retrieval_query: str
    retrieved_sources: List[str] = Field(default_factory=list)
    planning_impact: List[str] = Field(default_factory=list)
    coding_impact: List[str] = Field(default_factory=list)
    qa_impact: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
