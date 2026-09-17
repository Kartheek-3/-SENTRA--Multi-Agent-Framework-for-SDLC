from typing import List, Optional
from pydantic import BaseModel, Field

class ArchitectureComponent(BaseModel):
    component_id: str
    name: str
    responsibility: str
    technologies: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)

class DatabaseEntity(BaseModel):
    name: str
    description: str = ""
    fields: List[str] = Field(default_factory=list)
    relationships: List[str] = Field(default_factory=list)

class APIEndpoint(BaseModel):
    method: str
    path: str
    purpose: str
    request_schema: str = "{}"
    response_schema: str = "{}"
    authentication_required: bool = False

class ArchitectureDecision(BaseModel):
    component: str
    purpose: str
    reason: str
    complexity: str
    required: bool

class ScaleEvolutionStage(BaseModel):
    stage: str
    architecture_changes: List[str] = Field(default_factory=list)
    database_changes: List[str] = Field(default_factory=list)
    caching: str = ""
    scaling: str = ""
    deployment: str = ""
    observability: str = ""

class SystemDesign(BaseModel):
    architecture_style: str
    components: List[ArchitectureComponent] = Field(default_factory=list)
    data_flow: str = ""
    database_schema: List[DatabaseEntity] = Field(default_factory=list)
    api_endpoints: List[APIEndpoint] = Field(default_factory=list)
    technology_stack: List[str] = Field(default_factory=list)
    security_considerations: List[str] = Field(default_factory=list)
    architecture_decisions: List[ArchitectureDecision] = Field(default_factory=list, description="Reasoning for infrastructure choices")
    scale_evolution_plan: List[ScaleEvolutionStage] = Field(default_factory=list, description="Plan to evolve architecture as scale increases")

class Task(BaseModel):
    task_id: str
    title: str
    description: str = ""
    capability: str = ""
    priority: str = "Medium"
    dependencies: List[str] = Field(default_factory=list)
    related_requirements: List[str] = Field(default_factory=list)
    estimated_complexity: str = "Medium"
    
    # State tracking fields (populated by Supervisor/Workflow, not LLM initially)
    assigned_agent: Optional[str] = None
    status: str = "pending" # pending, in_progress, completed, failed
    result: Optional[dict] = None

    @property
    def id(self) -> str:
        return self.task_id

class ProjectPlan(BaseModel):
    project_overview: str
    implementation_phases: List[str] = Field(default_factory=list)
    tasks: List[Task] = Field(default_factory=list)
    milestones: List[str] = Field(default_factory=list)
    system_design: SystemDesign
    implementation_strategy: str = ""
    risks_and_mitigations: List[str] = Field(default_factory=list)
