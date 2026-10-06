from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class RepositoryFileRecord(BaseModel):
    path: str
    sha: str = ""
    size: int = 0
    type: str = "blob"
    language: str = ""
    last_analyzed_commit: str = ""


class RepositorySnapshot(BaseModel):
    repository: str
    commit_sha: str
    branch: str
    files: List[RepositoryFileRecord] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)


class ChangedFile(BaseModel):
    path: str
    previous_path: Optional[str] = None
    sha: str = ""
    status: str
    additions: int = 0
    deletions: int = 0
    changes: int = 0
    language: str = ""


class RepositoryChangeSet(BaseModel):
    repository: str
    before_sha: str
    after_sha: str
    changed_files: List[ChangedFile] = Field(default_factory=list)
    added_files: List[str] = Field(default_factory=list)
    modified_files: List[str] = Field(default_factory=list)
    deleted_files: List[str] = Field(default_factory=list)
    renamed_files: List[str] = Field(default_factory=list)
    detected_at: str = Field(default_factory=utc_now)


class RepositoryComponentDependency(BaseModel):
    source_component: str
    dependent_component: str
    relationship: str


class RepositoryIntelligence(BaseModel):
    repository: str
    commit_sha: str
    analysis_version: int
    status: str
    last_analyzed_at: str
    technologies: List[str] = Field(default_factory=list)
    architecture_signals: List[str] = Field(default_factory=list)
    api_signals: List[str] = Field(default_factory=list)
    database_signals: List[str] = Field(default_factory=list)
    testing_signals: List[str] = Field(default_factory=list)
    security_observations: List[str] = Field(default_factory=list)
    changed_files: List[str] = Field(default_factory=list)
    affected_components: List[str] = Field(default_factory=list)
    dependencies: List[RepositoryComponentDependency] = Field(default_factory=list)
    context: str = ""


class RepositoryRecord(BaseModel):
    repository_id: str
    owner: str
    name: str
    full_name: str
    clone_url: str = ""
    html_url: str = ""
    default_branch: str = "main"
    current_commit_sha: str = ""
    last_analyzed_commit_sha: str = ""
    analysis_version: int = 0
    last_analyzed_at: Optional[str] = None
    status: str = "NEW"
    stale: bool = False
    github_api_available: bool = True
    file_count: int = 0
    analysis_summary: str = ""
    created_at: str = Field(default_factory=utc_now)
    updated_at: str = Field(default_factory=utc_now)
    latest_change_set: Optional[RepositoryChangeSet] = None
    intelligence: Optional[RepositoryIntelligence] = None

    def freshness_context(self) -> Dict[str, Any]:
        return {
            "repository": self.full_name,
            "commit_sha": self.last_analyzed_commit_sha or self.current_commit_sha,
            "analysis_version": self.analysis_version,
            "status": self.status,
            "last_analyzed_at": self.last_analyzed_at,
        }
