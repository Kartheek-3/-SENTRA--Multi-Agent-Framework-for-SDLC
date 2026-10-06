import hashlib
import hmac
import json
from typing import Any, Dict, List, Optional, Tuple

from backend.config import GITHUB_WEBHOOK_SECRET
from backend.events import event_bus
from backend.github.github_client import GitHubClient
from backend.github.intelligence_models import (
    ChangedFile,
    RepositoryChangeSet,
    RepositoryComponentDependency,
    RepositoryFileRecord,
    RepositoryIntelligence,
    RepositoryRecord,
    RepositorySnapshot,
    utc_now,
)
from backend.github.registry import RepositoryRegistry


TECHNOLOGY_FILES = {
    "package.json": "Node.js",
    "requirements.txt": "Python",
    "pyproject.toml": "Python",
    "pom.xml": "Java/Maven",
    "build.gradle": "Java/Gradle",
    "Dockerfile": "Docker",
    "docker-compose.yml": "Docker Compose",
    "go.mod": "Go",
    "Cargo.toml": "Rust",
}


class GitHubIntelligenceService:
    def __init__(
        self,
        client: Optional[GitHubClient] = None,
        registry: Optional[RepositoryRegistry] = None,
        enable_rag_indexing: bool = False,
    ):
        self.client = client or GitHubClient()
        self.registry = registry or RepositoryRegistry()
        self.enable_rag_indexing = enable_rag_indexing

    def analyze_or_refresh(self, owner: str, name: str) -> RepositoryRecord:
        full_name = f"{owner}/{name}"
        record = self.registry.get(full_name)
        if not record:
            return self._full_analysis(owner, name)

        latest_sha = self.client.get_latest_commit_sha(owner, name, record.default_branch)
        if not latest_sha:
            return self._mark_unavailable_or_stale(record, self.client.last_error or "GitHub API unavailable")

        record.current_commit_sha = latest_sha
        record.github_api_available = True
        if latest_sha == record.last_analyzed_commit_sha:
            record.status = "CURRENT"
            record.stale = False
            event_bus.emit_sync("GITHUB_REPOSITORY_CURRENT", {
                "repository": full_name,
                "commit": latest_sha,
                "analysis_version": record.analysis_version,
                "summary": f"GitHub Intelligence current for {full_name}.",
            })
            return self.registry.save(record)

        return self._incremental_analysis(record, latest_sha)

    def get_agent_context(self, full_name: str) -> Dict[str, Any]:
        record = self.registry.get(full_name)
        if not record:
            return {"repository": full_name, "status": "UNAVAILABLE", "reason": "Repository has not been analyzed."}
        context = record.freshness_context()
        context["summary"] = record.analysis_summary
        context["intelligence"] = record.intelligence.model_dump() if record.intelligence else None
        return context

    def _full_analysis(self, owner: str, name: str) -> RepositoryRecord:
        full_name = f"{owner}/{name}"
        event_bus.emit_sync("GITHUB_REPOSITORY_DISCOVERED", {"repository": full_name, "summary": f"Repository discovered: {full_name}"})
        repo = self.client.get_repository(owner, name)
        if not repo:
            return self.registry.save(RepositoryRecord(
                repository_id=full_name.lower().replace("/", "__"),
                owner=owner,
                name=name,
                full_name=full_name,
                status="UNAVAILABLE",
                stale=True,
                github_api_available=False,
                analysis_summary=self.client.last_error or "GitHub API unavailable",
            ))

        branch = repo.get("default_branch", "main")
        commit_sha = self.client.get_latest_commit_sha(owner, name, branch)
        if not commit_sha:
            record = RepositoryRecord(
                repository_id=full_name.lower().replace("/", "__"),
                owner=owner,
                name=name,
                full_name=full_name,
                clone_url=repo.get("clone_url", ""),
                html_url=repo.get("html_url", ""),
                default_branch=branch,
                status="UNAVAILABLE",
                stale=True,
                github_api_available=False,
                analysis_summary=self.client.last_error or "Could not read default branch commit.",
            )
            return self.registry.save(record)

        event_bus.emit_sync("GITHUB_REPOSITORY_ANALYSIS_STARTED", {"repository": full_name, "commit": commit_sha})
        snapshot = self._build_snapshot(owner, name, branch, commit_sha)
        intelligence = self._build_intelligence(full_name, commit_sha, 1, snapshot.files, None)
        record = RepositoryRecord(
            repository_id=full_name.lower().replace("/", "__"),
            owner=owner,
            name=name,
            full_name=full_name,
            clone_url=repo.get("clone_url", ""),
            html_url=repo.get("html_url", ""),
            default_branch=branch,
            current_commit_sha=commit_sha,
            last_analyzed_commit_sha=commit_sha,
            analysis_version=1,
            last_analyzed_at=utc_now(),
            status="CURRENT",
            stale=False,
            github_api_available=True,
            file_count=len(snapshot.files),
            analysis_summary=intelligence.context,
            intelligence=intelligence,
        )
        self.registry.save_snapshot(snapshot)
        self._index_repository_context(record)
        event_bus.emit_sync("GITHUB_REPOSITORY_ANALYSIS_COMPLETED", {
            "repository": full_name,
            "commit": commit_sha,
            "analysis_version": 1,
            "summary": f"Full GitHub Intelligence completed for {full_name}.",
        })
        return self.registry.save(record)

    def _incremental_analysis(self, record: RepositoryRecord, latest_sha: str) -> RepositoryRecord:
        event_bus.emit_sync("GITHUB_REPOSITORY_CHANGED", {
            "repository": record.full_name,
            "before": record.last_analyzed_commit_sha,
            "after": latest_sha,
        })
        event_bus.emit_sync("GITHUB_INCREMENTAL_ANALYSIS_STARTED", {"repository": record.full_name, "commit": latest_sha})
        change_set = self._detect_changes(record, latest_sha)
        snapshot = self._build_snapshot(record.owner, record.name, record.default_branch, latest_sha)
        new_version = record.analysis_version + 1
        changed_paths = {item.path for item in change_set.changed_files}
        affected_files = [item for item in snapshot.files if item.path in changed_paths]
        intelligence = self._build_intelligence(record.full_name, latest_sha, new_version, affected_files, change_set)
        record.current_commit_sha = latest_sha
        record.last_analyzed_commit_sha = latest_sha
        record.analysis_version = new_version
        record.last_analyzed_at = utc_now()
        record.status = "CURRENT"
        record.stale = False
        record.github_api_available = True
        record.file_count = len(snapshot.files)
        record.latest_change_set = change_set
        record.intelligence = intelligence
        record.analysis_summary = intelligence.context
        self.registry.save_change_set(change_set)
        self.registry.save_snapshot(snapshot)
        self.registry.mark_repository_rag_superseded(record.full_name, latest_sha)
        self._index_repository_context(record)
        event_bus.emit_sync("GITHUB_INCREMENTAL_ANALYSIS_COMPLETED", {
            "repository": record.full_name,
            "commit": latest_sha,
            "changed_files": len(change_set.changed_files),
            "analysis_version": new_version,
            "summary": f"Incremental GitHub Intelligence completed for {record.full_name}.",
        })
        return self.registry.save(record)

    def _detect_changes(self, record: RepositoryRecord, latest_sha: str) -> RepositoryChangeSet:
        payload = self.client.compare_commits(record.owner, record.name, record.last_analyzed_commit_sha, latest_sha) or {}
        changed_files: List[ChangedFile] = []
        for item in payload.get("files", []):
            filename = item.get("filename", "")
            changed_files.append(ChangedFile(
                path=filename,
                previous_path=item.get("previous_filename"),
                sha=item.get("sha", ""),
                status=item.get("status", "modified").upper(),
                additions=item.get("additions", 0),
                deletions=item.get("deletions", 0),
                changes=item.get("changes", 0),
                language=self._language_for_path(filename),
            ))
        return RepositoryChangeSet(
            repository=record.full_name,
            before_sha=record.last_analyzed_commit_sha,
            after_sha=latest_sha,
            changed_files=changed_files,
            added_files=[item.path for item in changed_files if item.status == "ADDED"],
            modified_files=[item.path for item in changed_files if item.status == "MODIFIED"],
            deleted_files=[item.path for item in changed_files if item.status == "REMOVED"],
            renamed_files=[item.path for item in changed_files if item.status == "RENAMED"],
        )

    def _build_snapshot(self, owner: str, name: str, branch: str, commit_sha: str) -> RepositorySnapshot:
        tree = self.client.get_repository_tree_payload(owner, name, branch)
        files = [
            RepositoryFileRecord(
                path=item.get("path", ""),
                sha=item.get("sha", ""),
                size=item.get("size", 0) or 0,
                type=item.get("type", "blob"),
                language=self._language_for_path(item.get("path", "")),
                last_analyzed_commit=commit_sha,
            )
            for item in tree
            if item.get("type") == "blob"
        ]
        return RepositorySnapshot(repository=f"{owner}/{name}", commit_sha=commit_sha, branch=branch, files=files)

    def _build_intelligence(
        self,
        full_name: str,
        commit_sha: str,
        version: int,
        files: List[RepositoryFileRecord],
        change_set: Optional[RepositoryChangeSet],
    ) -> RepositoryIntelligence:
        paths = [item.path for item in files]
        technologies = sorted({TECHNOLOGY_FILES[path.split("/")[-1]] for path in paths if path.split("/")[-1] in TECHNOLOGY_FILES})
        architecture = self._signals(paths, ["app", "backend", "frontend", "api", "service", "controller", "model", "schema"])
        api = self._signals(paths, ["api", "route", "router", "controller", "endpoint"])
        database = self._signals(paths, ["db", "database", "migration", "schema", "models"])
        testing = self._signals(paths, ["test", "tests", "spec", "pytest", "cypress"])
        security = self._signals(paths, ["auth", "security", "jwt", "oauth", "permission", "policy"])
        dependencies = self._dependency_approximation(paths)
        changed = [item.path for item in change_set.changed_files] if change_set else []
        affected = self._affected_components(changed, dependencies)
        mode = "Incremental" if change_set else "Full"
        context = (
            f"{mode} repository intelligence for {full_name} at commit {commit_sha}. "
            f"Analysis version {version}. Technologies: {', '.join(technologies) or 'unknown'}. "
            f"Changed files: {len(changed)}. Affected components: {', '.join(affected) or 'repository baseline'}."
        )
        return RepositoryIntelligence(
            repository=full_name,
            commit_sha=commit_sha,
            analysis_version=version,
            status="CURRENT",
            last_analyzed_at=utc_now(),
            technologies=technologies,
            architecture_signals=architecture,
            api_signals=api,
            database_signals=database,
            testing_signals=testing,
            security_observations=security,
            changed_files=changed,
            affected_components=affected,
            dependencies=dependencies,
            context=context,
        )

    def _mark_unavailable_or_stale(self, record: RepositoryRecord, reason: str) -> RepositoryRecord:
        record.github_api_available = False
        record.stale = bool(record.last_analyzed_commit_sha)
        record.status = "STALE" if record.stale else "UNAVAILABLE"
        record.analysis_summary = reason
        event_bus.emit_sync("GITHUB_REPOSITORY_STALE", {
            "repository": record.full_name,
            "last_analyzed_commit": record.last_analyzed_commit_sha,
            "last_analyzed_at": record.last_analyzed_at,
            "reason": reason,
            "summary": f"GitHub Intelligence for {record.full_name} is {record.status}: {reason}",
        })
        return self.registry.save(record)

    def verify_webhook_signature(self, body: bytes, signature_header: Optional[str]) -> Tuple[bool, str]:
        if not GITHUB_WEBHOOK_SECRET:
            return False, "missing_webhook_secret"
        if not signature_header or not signature_header.startswith("sha256="):
            return False, "missing_or_invalid_signature"
        expected = "sha256=" + hmac.new(GITHUB_WEBHOOK_SECRET.encode("utf-8"), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature_header), "ok"

    def handle_push_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        repo = payload.get("repository") or {}
        full_name = repo.get("full_name", "")
        before = payload.get("before", "")
        after = payload.get("after", "")
        branch = (payload.get("ref", "").split("/")[-1]) or repo.get("default_branch", "main")
        if not full_name or not after:
            return {"status": "ignored", "reason": "missing repository or commit"}
        owner, name = full_name.split("/", 1)
        event_bus.emit_sync("GITHUB_WEBHOOK_RECEIVED", {
            "repository": full_name,
            "branch": branch,
            "before": before,
            "after": after,
            "summary": f"GitHub push webhook received for {full_name}.",
        })
        record = self.registry.get(full_name)
        if not record:
            record = RepositoryRecord(
                repository_id=full_name.lower().replace("/", "__"),
                owner=owner,
                name=name,
                full_name=full_name,
                html_url=repo.get("html_url", ""),
                clone_url=repo.get("clone_url", ""),
                default_branch=repo.get("default_branch", branch),
                current_commit_sha=after,
                status="NEW",
            )
            self.registry.save(record)
        return {"status": "queued", "repository": full_name, "before": before, "after": after}

    def _index_repository_context(self, record: RepositoryRecord) -> None:
        if not self.enable_rag_indexing or not record.intelligence:
            return
        from backend.knowledge.knowledge_service import KnowledgeService
        from backend.knowledge.models import KnowledgeDocument

        KnowledgeService().ingest_document(KnowledgeDocument(
            title=f"GitHub Repository Intelligence: {record.full_name}",
            source=f"github://{record.full_name}@{record.last_analyzed_commit_sha}",
            source_type="GITHUB_REPOSITORY",
            category="repository",
            domain="general",
            topic="github-intelligence",
            content=record.intelligence.context,
            version=record.analysis_version,
            validated="ACTIVE",
            tags=[record.full_name, record.last_analyzed_commit_sha, f"analysis_version:{record.analysis_version}"],
        ))

    def _language_for_path(self, path: str) -> str:
        ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
        return {
            "py": "Python",
            "ts": "TypeScript",
            "tsx": "TypeScript",
            "js": "JavaScript",
            "jsx": "JavaScript",
            "java": "Java",
            "go": "Go",
            "rs": "Rust",
            "cs": "C#",
            "sql": "SQL",
            "md": "Markdown",
            "yml": "YAML",
            "yaml": "YAML",
            "json": "JSON",
        }.get(ext, "")

    def _signals(self, paths: List[str], needles: List[str]) -> List[str]:
        found = []
        for path in paths:
            lower = path.lower()
            if any(needle in lower for needle in needles):
                found.append(path)
            if len(found) >= 20:
                break
        return found

    def _dependency_approximation(self, paths: List[str]) -> List[RepositoryComponentDependency]:
        deps: List[RepositoryComponentDependency] = []
        for path in paths:
            lower = path.lower()
            if "auth" in lower:
                for candidate in paths:
                    c_lower = candidate.lower()
                    if any(token in c_lower for token in ["user", "api", "test", "route"]):
                        deps.append(RepositoryComponentDependency(source_component=path, dependent_component=candidate, relationship="DEPENDS_ON"))
            if "/tests/" in lower or lower.startswith("tests/") or "test" in lower:
                target = path.replace("tests/", "").replace("test_", "").replace("_test", "")
                deps.append(RepositoryComponentDependency(source_component=path, dependent_component=target, relationship="TESTS"))
            if len(deps) >= 50:
                break
        return deps

    def _affected_components(self, changed_paths: List[str], dependencies: List[RepositoryComponentDependency]) -> List[str]:
        affected = set(changed_paths)
        for dep in dependencies:
            if dep.source_component in affected:
                affected.add(dep.dependent_component)
        return sorted(affected)
