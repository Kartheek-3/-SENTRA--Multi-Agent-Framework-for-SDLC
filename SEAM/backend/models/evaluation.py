from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


MetricValue = Union[int, float, str, bool, None]


class EvaluationRun(BaseModel):
    evaluation_id: str
    project_id: str
    scenario_id: str = "UNSPECIFIED"
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_ms: int = 0
    status: str = "COMPLETED"
    requirement_count: int = 0
    task_count: int = 0
    agent_count: int = 0
    tool_invocation_count: int = 0
    artifact_count: int = 0
    defect_count: int = 0
    resolved_defect_count: int = 0
    unresolved_defect_count: int = 0
    repair_iterations: int = 0
    e2e_pass_rate: Union[float, str] = "NOT_APPLICABLE"
    contract_pass_rate: Union[float, str] = "NOT_APPLICABLE"
    qa_status: str = "NOT_AVAILABLE"
    delivery_status: str = "NOT_AVAILABLE"


class RequirementMetrics(BaseModel):
    total_requirements: int = 0
    analyzed_requirements: int = 0
    planned_requirements: int = 0
    implemented_requirements: int = 0
    tested_requirements: int = 0
    delivered_requirements: int = 0
    requirement_coverage: Union[float, str] = "NOT_APPLICABLE"
    traceability_evidence: List[Dict[str, Any]] = Field(default_factory=list)


class AgentMetric(BaseModel):
    agent: str
    invocation_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    timeout_count: int = 0
    average_duration_ms: Union[float, str] = "NOT_APPLICABLE"
    total_duration_ms: int = 0
    rework_count: int = 0


class ToolMetric(BaseModel):
    category: str
    tool_invocation_count: int = 0
    success_rate: Union[float, str] = "NOT_APPLICABLE"
    failure_rate: Union[float, str] = "NOT_APPLICABLE"
    blocked_count: int = 0
    permission_denied_count: int = 0
    average_duration_ms: Union[float, str] = "NOT_APPLICABLE"


class QAMetrics(BaseModel):
    static_validation_result: str = "NOT_AVAILABLE"
    contract_result: str = "NOT_CONFIGURED"
    runtime_contract_result: str = "NOT_CONFIGURED"
    frontend_validation_result: str = "NOT_CONFIGURED"
    backend_validation_result: str = "NOT_CONFIGURED"
    e2e_result: str = "NOT_CONFIGURED"
    security_result: str = "NOT_AVAILABLE"
    final_qa_status: str = "NOT_AVAILABLE"
    qa_defect_count: int = 0
    blocker_count: int = 0
    error_count: int = 0
    warning_count: int = 0


class DefectMetrics(BaseModel):
    total_defects: int = 0
    frontend_defects: int = 0
    backend_defects: int = 0
    api_contract_defects: int = 0
    database_defects: int = 0
    runtime_defects: int = 0
    authentication_defects: int = 0
    unknown_defects: int = 0


class RepairMetrics(BaseModel):
    repair_plans: int = 0
    successful_repairs: int = 0
    failed_repairs: int = 0
    blocked_repairs: int = 0
    needs_review_repairs: int = 0
    average_repair_iterations: Union[float, str] = "NOT_APPLICABLE"
    maximum_repair_iterations: int = 0
    targeted_verification_pass_rate: Union[float, str] = "NOT_APPLICABLE"
    regression_pass_rate: Union[float, str] = "NOT_APPLICABLE"
    repair_resolution_rate: Union[float, str] = "NOT_APPLICABLE"


class E2EMetrics(BaseModel):
    scenarios_generated: int = 0
    scenarios_executed: int = 0
    scenarios_passed: int = 0
    scenarios_failed: int = 0
    scenarios_blocked: int = 0
    scenarios_not_configured: int = 0
    execution_duration_ms: int = 0
    step_failure_count: int = 0
    e2e_pass_rate: Union[float, str] = "NOT_APPLICABLE"


class ContractMetrics(BaseModel):
    total_contracts: int = 0
    static_contract_issues: int = 0
    runtime_contract_issues: int = 0
    resolved_contract_issues: int = 0
    endpoint_mismatches: int = 0
    method_mismatches: int = 0
    request_mismatches: int = 0
    response_mismatches: int = 0
    database_mapping_issues: int = 0
    contract_compliance_rate: Union[float, str] = "NOT_APPLICABLE"


class DeliveryMetrics(BaseModel):
    release_ready: bool = False
    release_blocked: bool = False
    deployment_target: str = "NOT_CONFIGURED"
    artifact_generation: str = "NOT_AVAILABLE"
    secret_scan_result: str = "NOT_AVAILABLE"
    packaging_result: str = "NOT_AVAILABLE"
    post_deployment_verification: str = "NOT_CONFIGURED"
    rollback_availability: str = "NOT_CONFIGURED"


class PerformanceMetrics(BaseModel):
    total_workflow_duration_ms: int = 0
    agent_processing_time_ms: int = 0
    tool_execution_time_ms: int = 0
    qa_time_ms: int = 0
    repair_time_ms: int = 0
    delivery_time_ms: int = 0
    breakdown_by_stage: Dict[str, int] = Field(default_factory=dict)


class AutonomyMetrics(BaseModel):
    user_interventions: int = 0
    approval_requests: int = 0
    blocked_actions: int = 0
    manual_fixes: int = 0
    autonomous_repair_iterations: int = 0
    autonomous_successful_repairs: int = 0


class DomainRAGMetrics(BaseModel):
    domain_detected: str = "NOT_AVAILABLE"
    knowledge_retrieved: bool = False
    knowledge_sources_used: int = 0
    source_types: List[str] = Field(default_factory=list)
    domain_specific_constraints_included: int = 0
    domain_related_qa_issues: int = 0
    retrieval_count: int = 0
    retrieval_success: int = 0
    documents_retrieved: int = 0
    domain_retrieval_count: int = 0
    repository_knowledge_retrieval_count: int = 0


class EvaluationComparison(BaseModel):
    metric: str
    baseline_value: MetricValue
    seam_value: MetricValue
    absolute_difference: Optional[float] = None
    relative_difference: Optional[float] = None


class EvaluationSummary(BaseModel):
    run: EvaluationRun
    requirements: RequirementMetrics
    agents: List[AgentMetric] = Field(default_factory=list)
    tools: List[ToolMetric] = Field(default_factory=list)
    qa: QAMetrics
    defects: DefectMetrics
    repairs: RepairMetrics
    e2e: E2EMetrics
    contracts: ContractMetrics
    delivery: DeliveryMetrics
    performance: PerformanceMetrics
    autonomy: AutonomyMetrics
    domain_rag: DomainRAGMetrics
    baseline_comparison: List[EvaluationComparison] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)


class ScenarioDefinition(BaseModel):
    scenario_id: str
    name: str
    description: str = ""
    domain: str = ""
    complexity: str = "SMALL"
    complexity_rationale: str = ""
    requirements: str = ""
    required_features: List[str] = Field(default_factory=list)
    expected_artifacts: List[str] = Field(default_factory=list)
    expected_validation_layers: List[str] = Field(default_factory=list)
    expected_capabilities: List[str] = Field(default_factory=list)
    seed: Optional[int] = None
    configuration: Dict[str, Any] = Field(default_factory=dict)
    evaluation_metrics: List[str] = Field(default_factory=list)
    version: str = "1"


class RunConfiguration(BaseModel):
    configuration_id: str
    name: str = ""
    mode: str = "SEAM_FULL"
    disabled_capabilities: List[str] = Field(default_factory=list)
    flags: Dict[str, Any] = Field(default_factory=dict)
    baseline_source: Optional[str] = None
    baseline_version: Optional[str] = None
    baseline_configuration: Dict[str, Any] = Field(default_factory=dict)
    baseline_provenance: Optional[str] = None


class ExperimentDefinition(BaseModel):
    experiment_id: str
    name: str
    description: str = ""
    hypothesis: str = ""
    scenarios: List[ScenarioDefinition] = Field(default_factory=list)
    configurations: List[RunConfiguration] = Field(default_factory=list)
    repetitions: int = 1
    metrics: List[str] = Field(default_factory=list)
    version: str = "1"
    created_at: str = ""


class ReproducibilityMetadata(BaseModel):
    experiment_id: str
    scenario_id: str
    run_id: str
    timestamp: str
    project_version: str = ""
    git_commit: Optional[str] = None
    model_name: str = ""
    model_configuration: Dict[str, Any] = Field(default_factory=dict)
    knowledge_base_version: str = "NOT_AVAILABLE"
    repository_context_version: str = "NOT_AVAILABLE"
    configuration_flags: Dict[str, Any] = Field(default_factory=dict)
    operating_environment: Dict[str, Any] = Field(default_factory=dict)
    python_version: str = ""
    node_version: str = "NOT_AVAILABLE"
    package_versions: Dict[str, str] = Field(default_factory=dict)
    seed: Optional[int] = None
    nondeterminism_limitations: List[str] = Field(default_factory=list)


class RunResult(BaseModel):
    run_id: str
    experiment_id: str
    scenario_id: str
    configuration_id: str
    repetition_index: int = 1
    project_id: str
    status: str = "RECORDED"
    evaluation: EvaluationSummary
    reproducibility: ReproducibilityMetadata
    data_quality: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)


class AggregateMetric(BaseModel):
    metric: str
    count: int = 0
    mean: MetricValue = "NOT_APPLICABLE"
    median: MetricValue = "NOT_APPLICABLE"
    minimum: MetricValue = "NOT_APPLICABLE"
    maximum: MetricValue = "NOT_APPLICABLE"
    standard_deviation: MetricValue = "NOT_APPLICABLE"


class ExperimentComparison(BaseModel):
    experiment_id: str
    metric: str
    scenario_id: str = "ALL"
    configuration_id: str = "ALL"
    baseline_configuration_id: Optional[str] = None
    values: List[MetricValue] = Field(default_factory=list)
    aggregate: AggregateMetric
    comparisons: List[EvaluationComparison] = Field(default_factory=list)
    data_sources: List[str] = Field(default_factory=list)


class ExperimentRun(BaseModel):
    experiment_id: str
    definition: ExperimentDefinition
    status: str = "CREATED"
    runs: List[RunResult] = Field(default_factory=list)
    comparisons: List[ExperimentComparison] = Field(default_factory=list)
    created_at: str = ""
    completed_at: Optional[str] = None
    failed_runs: int = 0
    blocked_runs: int = 0
    limitations: List[str] = Field(default_factory=list)
