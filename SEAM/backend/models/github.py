from typing import List, Optional
from pydantic import BaseModel, Field

class RepositoryCandidate(BaseModel):
    repository_url: str
    owner: str
    name: str
    description: Optional[str] = ""
    language: Optional[str] = ""
    stars: int = 0
    forks: int = 0
    open_issues: int = 0
    last_updated: str = ""
    license: str = "unknown"
    topics: List[str] = Field(default_factory=list)
    default_branch: str = "main"
    readme_available: bool = False
    test_indicators: bool = False
    documentation_indicators: bool = False
    security_indicators: bool = False
    detected_technologies: List[str] = Field(default_factory=list)

class RepositoryEvaluation(BaseModel):
    repository_url: str
    domain_match_score: float = 0.0
    technology_match_score: float = 0.0
    architecture_score: float = 0.0
    testing_score: float = 0.0
    security_score: float = 0.0
    maintenance_score: float = 0.0
    documentation_score: float = 0.0
    license_score: float = 0.0
    overall_score: float = 0.0
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    recommendation: str = ""

class RepositorySelection(BaseModel):
    selected_repository: Optional[RepositoryCandidate] = None
    evaluation: Optional[RepositoryEvaluation] = None
    reuse_existing: bool = False
    confidence: float = 0.0
    reason: str = ""
    alternatives: List[RepositoryCandidate] = Field(default_factory=list)
    license_notes: str = ""
    risks: List[str] = Field(default_factory=list)
