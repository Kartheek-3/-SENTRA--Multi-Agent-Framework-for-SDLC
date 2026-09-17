from typing import List
from pydantic import BaseModel, Field

class QAResult(BaseModel):
    task_id: str
    status: str = "failed" # passed, failed, needs_revision
    passed: bool = False
    functional_issues: List[str] = Field(default_factory=list)
    requirement_violations: List[str] = Field(default_factory=list)
    architecture_violations: List[str] = Field(default_factory=list)
    security_issues: List[str] = Field(default_factory=list)
    syntax_errors: List[str] = Field(default_factory=list)
    test_results: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    severity: str = "none" # none, low, medium, high, critical
    files_checked: List[str] = Field(default_factory=list)
