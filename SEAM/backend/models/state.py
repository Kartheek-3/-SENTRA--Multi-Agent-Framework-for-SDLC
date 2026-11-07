from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from backend.models.analysis import AnalysisResult
from backend.models.planning import FrontendArchitecturePlan, ProjectPlan, SystemDesign, Task
from backend.models.github import RepositorySelection
from backend.models.domain import DomainIdentification, DomainContext, DomainTraceability
from backend.models.contracts import (
    DefectLocation,
    E2EResult,
    E2EScenario,
    RegressionResult,
    RepairPlan,
    RepairResult,
    FullStackContractProfile,
    ContractIssue,
    RuntimeContractResult,
    RuntimeProfile,
    RuntimeProcess,
    TargetedVerification,
)
from backend.models.delivery import (
    DeploymentArtifact,
    DeploymentProfile,
    DeploymentResult,
    PostDeploymentVerification,
    ReleaseReadiness,
    RollbackInfo,
)
from backend.models.evaluation import EvaluationSummary

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
    domain_identification: Optional[DomainIdentification] = None
    domain_context: Optional[DomainContext] = None
    domain_traceability: Optional[DomainTraceability] = None
    retrieved_context: List[str] = Field(default_factory=list)
    github_selection: Optional[RepositorySelection] = None
    github_findings: Optional[Dict[str, Any]] = None
    github_status: str = "not_requested"
    github_context: Optional[Dict[str, Any]] = None
    project_plan: Optional[ProjectPlan] = None
    system_design: Optional[SystemDesign] = None
    design_artifacts: Optional[DesignArtifacts] = None
    technology_stack: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    tasks: Dict[str, Task] = Field(default_factory=dict)
    completed_tasks: List[str] = Field(default_factory=list)
    failed_tasks: List[str] = Field(default_factory=list)
    current_task: Optional[str] = None
    current_agent: Optional[str] = None
    
    execution_history: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    qa_feedback: List[str] = Field(default_factory=list)
    pending_qa_knowledge: Dict[str, str] = Field(default_factory=dict)
    delivery_result: Optional[Dict[str, Any]] = None
    external_integrations: List[Dict[str, Any]] = Field(default_factory=list)
    n8n_integration_status: Dict[str, Any] = Field(default_factory=dict)
    frontend_capabilities: Dict[str, Any] = Field(default_factory=dict)
    frontend_architecture_plan: Optional[FrontendArchitecturePlan] = None
    frontend_execution: Dict[str, Any] = Field(default_factory=dict)
    full_stack_contract: Optional[FullStackContractProfile] = None
    contract_issues: List[ContractIssue] = Field(default_factory=list)
    runtime_base_url: Optional[str] = None
    runtime_contract_results: List[RuntimeContractResult] = Field(default_factory=list)
    runtime_profile: Optional[RuntimeProfile] = None
    runtime_processes: List[RuntimeProcess] = Field(default_factory=list)
    runtime_status: str = "NOT_CONFIGURED"
    e2e_scenarios: List[E2EScenario] = Field(default_factory=list)
    e2e_results: List[E2EResult] = Field(default_factory=list)
    defect_locations: List[DefectLocation] = Field(default_factory=list)
    repair_plans: List[RepairPlan] = Field(default_factory=list)
    repair_results: List[RepairResult] = Field(default_factory=list)
    targeted_verifications: List[TargetedVerification] = Field(default_factory=list)
    regression_results: List[RegressionResult] = Field(default_factory=list)
    release_readiness: Optional[ReleaseReadiness] = None
    deployment_profile: Optional[DeploymentProfile] = None
    deployment_artifacts: List[DeploymentArtifact] = Field(default_factory=list)
    deployment_result: Optional[DeploymentResult] = None
    post_deployment_verification: Optional[PostDeploymentVerification] = None
    rollback_info: Optional[RollbackInfo] = None
    evaluation_summary: Optional[EvaluationSummary] = None
    experiment_summary: Optional[Dict[str, Any]] = None
    max_repair_iterations: int = 3
    
    # UI specific fields
    workflow_status: str = "pending" # pending, running, completed, failed
    retry_count: int = 0
    latest_qa_status: str = "pending"
    scale_changed: bool = False
    
    # Workflow Selection & Repository Enhancement (Phase 3)
    workflow_type: str = "new_project"  # "new_project" or "enhance_existing"
    repo_url: Optional[str] = None
    repo_owner: Optional[str] = None
    repo_name: Optional[str] = None
    repo_branch: Optional[str] = "main"
    repo_workspace_path: Optional[str] = None
    repo_profile: Optional[Dict[str, Any]] = None
    project_understanding: Optional[Dict[str, Any]] = None
    enhancement_plan: Optional[Dict[str, Any]] = None
    enhancement_approved: bool = False
    approval_status: str = "pending"  # "pending", "approved", "rejected"
    targeted_changes: List[Dict[str, Any]] = Field(default_factory=list)
    diff_summary: Optional[str] = None
    regression_status: str = "not_started"

    @property
    def is_enhance_workflow(self) -> bool:
        return self.workflow_type == "enhance_existing"

    @property
    def project_name(self) -> str:
        from backend.utils import slugify
        if self.domain:
            return slugify(self.domain)
        return slugify(self.project_id)
