from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class DeliveryResult(BaseModel):
    project_name: str
    status: str = "failed" # ready, packaged, deployed, failed
    qa_verified: bool = False
    documentation_generated: bool = False
    package_created: bool = False
    package_path: str = ""
    manifest_path: str = ""
    deployment_status: str = "pending"
    artifact_paths: List[str] = Field(default_factory=list)
    knowledge_update_status: str = "pending"
    errors: List[str] = Field(default_factory=list)


class EnvironmentVariableRequirement(BaseModel):
    name: str
    type: str = "environment"
    required: bool = True
    secret: bool = False
    description: str = ""
    source: str = ""


class SecretFinding(BaseModel):
    status: str = "SECRET_DETECTED"
    file: str
    line: Optional[int] = None
    category: str
    remediation: str = "Move the value to environment configuration and rotate the exposed credential."


class ReleaseReadiness(BaseModel):
    status: str = "NOT_READY"
    blockers: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    qa_status: str = "NOT_AVAILABLE"
    unresolved_defects: int = 0
    contract_status: str = "NOT_CONFIGURED"
    runtime_status: str = "NOT_CONFIGURED"
    e2e_status: str = "NOT_CONFIGURED"
    build_status: str = "NOT_CONFIGURED"
    artifact_status: str = "NOT_CONFIGURED"
    security_status: str = "NOT_CONFIGURED"
    documentation_status: str = "NOT_CONFIGURED"


class DeploymentProfile(BaseModel):
    target: str = "NOT_CONFIGURED"
    application_type: str = "UNKNOWN"
    frontend: Dict[str, Any] = Field(default_factory=dict)
    backend: Dict[str, Any] = Field(default_factory=dict)
    containerized: bool = False
    containerization_status: str = "NOT_CONFIGURED"
    build_command: Optional[str] = None
    artifact_directory: Optional[str] = None
    dockerfile: Optional[str] = None
    compose_file: Optional[str] = None
    kubernetes_manifests: List[str] = Field(default_factory=list)
    required_environment_variables: List[EnvironmentVariableRequirement] = Field(default_factory=list)
    exposed_ports: List[int] = Field(default_factory=list)
    health_endpoint: Optional[str] = None
    start_command: Optional[str] = None
    deployment_command: Optional[str] = None
    rollback_strategy: Optional[str] = None


class DeploymentArtifact(BaseModel):
    project: str
    artifact_type: str
    path: str
    version: str = "1"
    status: str = "PENDING"


class DeploymentResult(BaseModel):
    status: str = "PREPARED"
    deployment_target: str = "NOT_CONFIGURED"
    package_path: str = ""
    manifest_path: str = ""
    git: Dict[str, Any] = Field(default_factory=dict)
    build_information: Dict[str, Any] = Field(default_factory=dict)
    runtime_information: Dict[str, Any] = Field(default_factory=dict)
    artifact_list: List[DeploymentArtifact] = Field(default_factory=list)
    environment_requirements: List[EnvironmentVariableRequirement] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class PostDeploymentVerification(BaseModel):
    status: str = "NOT_CONFIGURED"
    application_health: str = "NOT_CONFIGURED"
    api_health: str = "NOT_CONFIGURED"
    frontend_availability: str = "NOT_CONFIGURED"
    contract_verification: str = "NOT_CONFIGURED"
    e2e_smoke: str = "NOT_CONFIGURED"
    evidence: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class RollbackInfo(BaseModel):
    rollback_status: str = "NOT_CONFIGURED"
    previous_version: Optional[str] = None
    current_version: Optional[str] = None
    git_commit: Optional[str] = None
    deployment_artifact: Optional[str] = None
    rollback_command_reference: Optional[str] = None
    rollback_available: bool = False
