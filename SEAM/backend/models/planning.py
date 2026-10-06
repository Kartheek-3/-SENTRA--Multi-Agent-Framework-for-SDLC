from typing import Any, Dict, List, Optional
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

class FrontendRoutePlan(BaseModel):
    path: str
    page: str
    authentication_required: bool = False
    purpose: str = ""

class FrontendComponentPlan(BaseModel):
    name: str
    responsibility: str = ""
    inputs_props: List[str] = Field(default_factory=list)
    state: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    api_interactions: List[str] = Field(default_factory=list)
    reusable: bool = False

class FrontendPagePlan(BaseModel):
    name: str
    route: str = ""
    purpose: str = ""
    components: List[str] = Field(default_factory=list)
    data_requirements: List[str] = Field(default_factory=list)
    api_dependencies: List[str] = Field(default_factory=list)
    authentication_required: bool = False
    loading_state: str = ""
    error_state: str = ""

class FrontendServicePlan(BaseModel):
    name: str
    responsibility: str = ""
    api_endpoints: List[str] = Field(default_factory=list)
    files: List[str] = Field(default_factory=list)

class FrontendAPIIntegration(BaseModel):
    page: str
    service: str
    endpoints: List[str] = Field(default_factory=list)
    mismatch_notes: List[str] = Field(default_factory=list)

class FrontendFilePlan(BaseModel):
    path: str
    operation: str = "CREATE"
    purpose: str = ""

class FrontendTraceabilityItem(BaseModel):
    requirement_id: str
    requirement: str
    page: str = ""
    component: str = ""
    service: str = ""
    api_endpoint: str = ""
    file: str = ""
    validation: str = ""

class FrontendArchitecturePlan(BaseModel):
    framework: str = "UNKNOWN"
    language: str = "UNKNOWN"
    build_system: str = "UNKNOWN"
    routing_strategy: str = ""
    state_management: str = ""
    styling_strategy: str = ""
    routes: List[FrontendRoutePlan] = Field(default_factory=list)
    pages: List[FrontendPagePlan] = Field(default_factory=list)
    layouts: List[str] = Field(default_factory=list)
    components: List[FrontendComponentPlan] = Field(default_factory=list)
    reusable_components: List[str] = Field(default_factory=list)
    services: List[FrontendServicePlan] = Field(default_factory=list)
    api_integration: List[FrontendAPIIntegration] = Field(default_factory=list)
    authentication: Dict[str, Any] = Field(default_factory=dict)
    forms: List[str] = Field(default_factory=list)
    validation: List[str] = Field(default_factory=list)
    error_handling: List[str] = Field(default_factory=list)
    loading_states: List[str] = Field(default_factory=list)
    responsive_strategy: List[str] = Field(default_factory=list)
    accessibility_strategy: List[str] = Field(default_factory=list)
    testing_strategy: List[str] = Field(default_factory=list)
    file_structure: List[FrontendFilePlan] = Field(default_factory=list)
    implementation_order: List[str] = Field(default_factory=list)
    traceability: List[FrontendTraceabilityItem] = Field(default_factory=list)

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
