from typing import List
from pydantic import BaseModel, Field

class DeliveryResult(BaseModel):
    project_name: str
    status: str = "failed" # ready, packaged, deployed, failed
    qa_verified: bool = False
    documentation_generated: bool = False
    package_created: bool = False
    deployment_status: str = "pending"
    artifact_paths: List[str] = Field(default_factory=list)
    knowledge_update_status: str = "pending"
    errors: List[str] = Field(default_factory=list)
