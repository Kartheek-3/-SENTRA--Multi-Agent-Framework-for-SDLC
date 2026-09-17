from typing import List, Optional
from pydantic import BaseModel, Field

class Requirement(BaseModel):
    id: str = Field(..., description="Stable ID like FR-001 or NFR-001")
    description: str = Field(..., description="Description of the requirement")

class AnalysisResult(BaseModel):
    project_summary: str = Field(description="A brief summary of the project")
    application_domain: str = Field(description="The domain of the software application")
    functional_requirements: List[Requirement] = Field(description="List of functional requirements")
    non_functional_requirements: List[Requirement] = Field(description="List of non-functional requirements")
    actors: List[str] = Field(description="List of actors/users in the system")
    entities: List[str] = Field(description="Important entities/domain objects in the system")
    constraints: List[str] = Field(description="Technical or business constraints")
    assumptions: List[str] = Field(description="Assumptions made about the requirements")
    risks: List[str] = Field(description="Potential project or technical risks")
    technical_considerations: List[str] = Field(description="Technical considerations for architecture")
    ambiguities: List[str] = Field(description="Ambiguities detected in the user requirements")
    recommended_capabilities: List[str] = Field(description="Recommended additional capabilities that add value")
    scale_assessment: Optional['ScaleAssessment'] = Field(default=None, description="Detailed scale and engineering complexity assessment")

from backend.models.scale import ScaleAssessment
AnalysisResult.model_rebuild()
