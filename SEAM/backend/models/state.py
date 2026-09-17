from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from backend.models.analysis import AnalysisResult
from backend.models.planning import ProjectPlan, SystemDesign, Task
from backend.models.github import RepositorySelection

class DesignArtifacts(BaseModel):
    analysis_document_path: Optional[str] = None
    system_design_document_path: Optional[str] = None
    diagram_paths: List[str] = Field(default_factory=list)
    rendered_diagram_paths: List[str] = Field(default_factory=list)
    generation_status: str = "pending"
    validation_errors: List[str] = Field(default_factory=list)

class ProjectState(BaseModel):
    project_id: str
    user_requirement: str = ""
    structured_requirements: Optional[AnalysisResult] = None
    domain: str = ""
    retrieved_context: List[str] = Field(default_factory=list)
    github_selection: Optional[RepositorySelection] = None
    github_findings: Optional[Dict[str, Any]] = None
    github_status: str = "not_requested"
    project_plan: Optional[ProjectPlan] = None
    system_design: Optional[SystemDesign] = None
    design_artifacts: Optional[DesignArtifacts] = None
    
    tasks: Dict[str, Task] = Field(default_factory=dict)
    completed_tasks: List[str] = Field(default_factory=list)
    failed_tasks: List[str] = Field(default_factory=list)
    current_task: Optional[str] = None
    current_agent: Optional[str] = None
    
    execution_history: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    delivery_result: Optional[Dict[str, Any]] = None
    
    # UI specific fields
    workflow_status: str = "pending" # pending, running, completed, failed
    retry_count: int = 0
    latest_qa_status: str = "pending"
    scale_changed: bool = False
    
    @property
    def project_name(self) -> str:
        from backend.utils import slugify
        if self.domain:
            return slugify(self.domain)
        return slugify(self.project_id)
