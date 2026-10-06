from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class APIParameter(BaseModel):
    name: str
    location: str = "query"
    type: str = "UNKNOWN"
    required: bool = False
    description: str = ""


class APIRequestSchema(BaseModel):
    name: str = ""
    fields: Dict[str, Any] = Field(default_factory=dict)
    raw_schema: str = "{}"


class APIResponseSchema(BaseModel):
    name: str = ""
    fields: Dict[str, Any] = Field(default_factory=dict)
    raw_schema: str = "{}"
    status_codes: List[int] = Field(default_factory=list)


class APIContract(BaseModel):
    method: str
    endpoint: str
    purpose: str = ""
    path_parameters: List[APIParameter] = Field(default_factory=list)
    query_parameters: List[APIParameter] = Field(default_factory=list)
    request_body: Optional[APIRequestSchema] = None
    response_body: Optional[APIResponseSchema] = None
    authentication_required: bool = False
    status_codes: List[int] = Field(default_factory=list)
    backend_implementation: str = ""


class FrontendAPIUsage(BaseModel):
    frontend_page: str = ""
    frontend_component: str = ""
    frontend_file: str = ""
    service: str = ""
    function: str = ""
    method: str = ""
    endpoint: str = ""
    request_schema: str = ""
    response_schema: str = ""


class DatabaseEntityContract(BaseModel):
    name: str
    table: str = ""
    fields: List[str] = Field(default_factory=list)
    relationships: List[str] = Field(default_factory=list)


class ContractMapping(BaseModel):
    requirement_id: str = ""
    requirement: str = ""
    frontend: Optional[FrontendAPIUsage] = None
    api: Optional[APIContract] = None
    backend_model: str = ""
    database_entity: Optional[DatabaseEntityContract] = None
    field_mappings: Dict[str, str] = Field(default_factory=dict)
    status: str = "UNKNOWN"


class ContractIssue(BaseModel):
    issue_id: str
    category: str
    severity: str = "WARNING"
    source: str = ""
    target: str = ""
    file: str = ""
    endpoint: str = ""
    field: str = ""
    expected: str = ""
    actual: str = ""
    description: str = ""
    suggested_fix: str = ""


class FullStackContractProfile(BaseModel):
    api_contracts: List[APIContract] = Field(default_factory=list)
    frontend_api_usage: List[FrontendAPIUsage] = Field(default_factory=list)
    database_entities: List[DatabaseEntityContract] = Field(default_factory=list)
    mappings: List[ContractMapping] = Field(default_factory=list)
    issues: List[ContractIssue] = Field(default_factory=list)
    traceability: List[Dict[str, Any]] = Field(default_factory=list)
    source_summary: Dict[str, Any] = Field(default_factory=dict)
    status: str = "UNKNOWN"


class RuntimeContractResult(BaseModel):
    contract_id: str = ""
    endpoint: str
    method: str
    request_status: str = "NOT_SENT"
    expected_status: List[int] = Field(default_factory=list)
    actual_status: Optional[int] = None
    schema_valid: bool = False
    response_valid: bool = False
    authentication_valid: bool = False
    latency_ms: int = 0
    issues: List[ContractIssue] = Field(default_factory=list)
    status: str = "NOT_CONFIGURED"


class RuntimeProcess(BaseModel):
    name: str
    pid: Optional[int] = None
    command: List[str] = Field(default_factory=list)
    project_root: str = ""
    port: Optional[int] = None
    url: str = ""
    start_time: float = 0
    status: str = "NOT_RUNNING"


class RuntimeProfile(BaseModel):
    project_root: str = ""
    frontend_framework: str = "UNKNOWN"
    frontend_start_command: Optional[List[str]] = None
    backend_framework: str = "UNKNOWN"
    backend_start_command: Optional[List[str]] = None
    frontend_port: Optional[int] = None
    backend_port: Optional[int] = None
    expected_health_endpoint: str = "/health"
    readiness_timeout: int = 20
    startup_timeout: int = 30


class RuntimeHealthResult(BaseModel):
    name: str
    url: str = ""
    status: str = "NOT_CONFIGURED"
    status_code: Optional[int] = None
    latency_ms: int = 0
    error: str = ""


class RuntimeStartResult(BaseModel):
    status: str = "NOT_CONFIGURED"
    base_url: Optional[str] = None
    profile: Optional[RuntimeProfile] = None
    processes: List[RuntimeProcess] = Field(default_factory=list)
    health: List[RuntimeHealthResult] = Field(default_factory=list)
    message: str = ""


class RuntimeStatus(BaseModel):
    status: str = "NOT_CONFIGURED"
    base_url: Optional[str] = None
    processes: List[RuntimeProcess] = Field(default_factory=list)
    health: List[RuntimeHealthResult] = Field(default_factory=list)


class E2EStep(BaseModel):
    step_id: str
    action: str
    target: str = ""
    value: str = ""
    expected: str = ""


class E2EScenario(BaseModel):
    scenario_id: str
    name: str
    source_requirement: str = ""
    preconditions: List[str] = Field(default_factory=list)
    steps: List[E2EStep] = Field(default_factory=list)
    expected_outcome: str = ""
    priority: str = "MEDIUM"
    frontend_page: str = ""
    api_endpoint: str = ""


class E2EStepResult(BaseModel):
    step_id: str
    action: str
    status: str = "NOT_RUN"
    expected: str = ""
    actual: str = ""
    duration_ms: int = 0
    screenshot: Optional[str] = None


class DefectLocation(BaseModel):
    layer: str = "UNKNOWN"
    confidence: str = "LOW"
    file: str = ""
    endpoint: str = ""
    component: str = ""
    evidence: List[str] = Field(default_factory=list)
    issue: str = ""
    suggested_investigation: str = ""


class E2EResult(BaseModel):
    scenario_id: str
    status: str = "NOT_CONFIGURED"
    steps: List[E2EStepResult] = Field(default_factory=list)
    duration_ms: int = 0
    screenshots: List[str] = Field(default_factory=list)
    network_failures: List[Dict[str, Any]] = Field(default_factory=list)
    console_errors: List[Dict[str, Any]] = Field(default_factory=list)
    final_url: str = ""
    defect_locations: List[DefectLocation] = Field(default_factory=list)


class RepairAction(BaseModel):
    action_id: str
    description: str
    target_file: str = ""
    target_endpoint: str = ""
    target_component: str = ""


class RepairPlan(BaseModel):
    repair_id: str
    defect_id: str = ""
    source_requirement: str = ""
    defect_location: Optional[DefectLocation] = None
    affected_files: List[str] = Field(default_factory=list)
    affected_endpoint: str = ""
    affected_component: str = ""
    expected_behavior: str = ""
    actual_behavior: str = ""
    repair_strategy: str = ""
    verification_strategy: str = ""
    risk: str = "MEDIUM"
    status: str = "PENDING"
    actions: List[RepairAction] = Field(default_factory=list)


class RepairResult(BaseModel):
    repair_id: str
    status: str = "BLOCKED"
    modified_files: List[str] = Field(default_factory=list)
    diff_summary: str = ""
    defect_addressed: bool = False
    remaining_issues: List[str] = Field(default_factory=list)
    verification_required: List[str] = Field(default_factory=list)


class TargetedVerification(BaseModel):
    repair_id: str
    validation_type: str
    target: str = ""
    expected: str = ""
    actual: str = ""
    status: str = "NOT_CONFIGURED"
    evidence: List[str] = Field(default_factory=list)


class RegressionResult(BaseModel):
    repair_id: str
    validation_type: str = "RELATED_REGRESSION"
    target: str = ""
    status: str = "NOT_CONFIGURED"
    evidence: List[str] = Field(default_factory=list)
