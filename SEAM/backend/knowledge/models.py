from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import time
import uuid
import hashlib
from urllib.parse import urlparse


PRODUCTION_KNOWLEDGE_STATUSES = {"VALIDATED", "ACTIVE"}


SOURCE_TYPE_PRIORITY = {
    "AUTHORITATIVE": 6,
    "OFFICIAL_TECHNICAL_DOCUMENTATION": 5,
    "ACADEMIC": 4,
    "VALIDATED_PROJECT_KNOWLEDGE": 3,
    "SEAM_CURATED": 2,
    "LESSON_LEARNED": 1,
    "GITHUB_REPOSITORY": 1,
}


OFFICIAL_SOURCE_DOMAINS = {
    "OWASP": ["owasp.org", "cheatsheetseries.owasp.org"],
    "NIST": ["nist.gov"],
    "AWS": ["docs.aws.amazon.com", "aws.amazon.com"],
    "Google Cloud": ["cloud.google.com", "docs.cloud.google.com"],
    "Python Software Foundation": ["docs.python.org", "python.org"],
    "FastAPI": ["fastapi.tiangolo.com"],
    "React": ["react.dev"],
    "PostgreSQL Global Development Group": ["postgresql.org", "www.postgresql.org"],
    "World Health Organization": ["who.int", "www.who.int"],
    "Reserve Bank of India": ["rbi.org.in", "www.rbi.org.in", "systemhealth.rbi.org.in"],
}


class KnowledgeSource(BaseModel):
    source_type: str
    organization: Optional[str] = None
    title: str
    url: Optional[str] = None
    document_version: Optional[str] = None
    publication_date: Optional[str] = None
    accessed_date: Optional[str] = None
    domain: str
    category: str
    topic: str
    status: str
    license: Optional[str] = None
    authors: Optional[str] = None
    publication: Optional[str] = None
    year: Optional[str] = None
    doi: Optional[str] = None
    project_name: Optional[str] = None
    project_version: Optional[str] = None
    validation_result: Optional[str] = None

    @property
    def source_id(self) -> str:
        identity = "|".join([
            self.source_type,
            self.organization or "",
            self.title,
            self.url or "",
            self.domain,
            self.category,
            self.topic,
        ])
        return hashlib.sha256(identity.encode("utf-8")).hexdigest()


class KnowledgeSourceValidationError(ValueError):
    pass


def validate_knowledge_source(source: KnowledgeSource) -> None:
    if source.source_type not in SOURCE_TYPE_PRIORITY:
        raise KnowledgeSourceValidationError(f"Unsupported source_type: {source.source_type}")
    if not source.title or not source.organization or not source.domain or not source.category or not source.topic or not source.status:
        raise KnowledgeSourceValidationError("Missing required source metadata")
    if source.status not in {"PENDING", "REVIEWED", "VALIDATED", "ACTIVE", "REJECTED", "ARCHIVED", "SOURCE_UNAVAILABLE"}:
        raise KnowledgeSourceValidationError(f"Unsupported source status: {source.status}")
    if source.source_type in {"AUTHORITATIVE", "OFFICIAL_TECHNICAL_DOCUMENTATION"}:
        if not source.url:
            raise KnowledgeSourceValidationError("External authoritative/official sources require a URL")
        parsed = urlparse(source.url)
        if parsed.scheme not in {"https", "http"} or not parsed.netloc:
            raise KnowledgeSourceValidationError(f"Invalid source URL: {source.url}")
        allowed_hosts = OFFICIAL_SOURCE_DOMAINS.get(source.organization)
        if allowed_hosts:
            host = parsed.netloc.lower()
            if not any(host == item or host.endswith(f".{item}") for item in allowed_hosts):
                raise KnowledgeSourceValidationError(f"URL host {host} does not match organization {source.organization}")

class KnowledgeDocument(BaseModel):
    knowledge_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    source: str
    source_type: str  # e.g., "github", "project", "manual"
    source_metadata: Optional[KnowledgeSource] = None
    category: str     # domain, architecture, coding, security, testing, documentation, etc.
    domain: str = "general"
    topic: str = ""
    project_id: Optional[str] = None
    content: str
    version: int = 1
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
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
