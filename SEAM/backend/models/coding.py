from typing import List, Optional
from pydantic import BaseModel, Field

class GeneratedFile(BaseModel):
    path: str
    content: str

class CodeGenerationResult(BaseModel):
    task_id: str
    summary: str = ""
    requirements_implemented: List[str] = Field(default_factory=list)
    dependencies_used: List[str] = Field(default_factory=list)
    files: List[GeneratedFile] = Field(default_factory=list)
