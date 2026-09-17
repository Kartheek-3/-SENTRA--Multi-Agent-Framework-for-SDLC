from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Optional

class ProjectScale(str, Enum):
    SMALL = "SMALL"
    MEDIUM = "MEDIUM"
    LARGE = "LARGE"
    ENTERPRISE = "ENTERPRISE"

class ArchitectureMaturity(str, Enum):
    LEVEL_1_SIMPLE = "LEVEL_1_SIMPLE"
    LEVEL_2_MODULAR = "LEVEL_2_MODULAR"
    LEVEL_3_DISTRIBUTED = "LEVEL_3_DISTRIBUTED"
    LEVEL_4_ENTERPRISE = "LEVEL_4_ENTERPRISE"

class ScaleAssessment(BaseModel):
    scale_level: ProjectScale
    architecture_maturity: ArchitectureMaturity = ArchitectureMaturity.LEVEL_1_SIMPLE
    confidence: float = Field(default=1.0, description="Confidence in this scale assessment (0.0 to 1.0)")
    evidence: List[str] = Field(default_factory=list, description="Explicit requirements serving as evidence for this scale.")
    factors: List[str] = Field(default_factory=list, description="Engineering factors driving the scale assessment.")
    assumptions: List[str] = Field(default_factory=list, description="Assumptions made when explicit information was missing.")
    risks: List[str] = Field(default_factory=list, description="Risks related to scaling this product.")
    recommended_architecture_style: str = Field(default="", description="e.g. monolithic, modular monolith, microservices, etc.")
    recommended_deployment_style: str = Field(default="", description="e.g. single server, containerized, orchestrated, multi-region.")
    recommended_data_strategy: str = Field(default="", description="e.g. single relational DB, read replicas, sharded, polyglot persistence.")
    recommended_scaling_strategy: List[str] = Field(default_factory=list, description="e.g. horizontal scaling, caching, asynchronous processing.")
