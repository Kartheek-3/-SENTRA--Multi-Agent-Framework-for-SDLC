import ipaddress
import json
import os
import socket
import subprocess
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from pydantic import BaseModel, Field

from backend.github.intelligence_service import GitHubIntelligenceService
from backend.knowledge.knowledge_service import KnowledgeService
from backend.tools.base import SEAMTool
from backend.tools.permissions import PermissionEngine
from backend.tools.registry import default_registry
from backend.tools.schemas import RiskLevel, ToolExecutionContext, ToolResult


class RAGSearchInput(BaseModel):
    query: str
    domain: str = "general"
    top_k: int = Field(default=5, ge=1, le=20)
    source_type: Optional[str] = None


class RAGSearchTool(SEAMTool):
    name = "rag_search"
    description = "Search the existing SEAM ChromaDB/FastEmbed knowledge repository."
    category = "rag"
    input_schema = RAGSearchInput
    allowed_agents = ["AnalysisAgent", "PlanningAgent", "CodingAgent", "QAAgent", "DeliveryAgent"]
    risk_level = RiskLevel.READ_ONLY

    def execute(self, tool_input: RAGSearchInput, context: ToolExecutionContext) -> ToolResult:
        result = KnowledgeService().retrieve_domain_aware(tool_input.query, tool_input.domain, top_k=tool_input.top_k)
        results = result.get("results", [])
        if tool_input.source_type:
            results = [item for item in results if item.get("source_type") == tool_input.source_type]
        return ToolResult(success=True, tool_name=self.name, structured_data={"query": tool_input.query, "results": results})


class GitHubRepositoryInput(BaseModel):
    repository: str


class GitHubCompareInput(BaseModel):
    repository: str
    before_sha: str
    after_sha: str


class GitHubRepositoryContextTool(SEAMTool):
    name = "github_repository_context"
    description = "Return freshness-aware GitHub repository context from GitHub Intelligence v2."
    category = "github"
    input_schema = GitHubRepositoryInput
    allowed_agents = ["AnalysisAgent", "PlanningAgent", "CodingAgent", "QAAgent", "SupervisorAgent"]
    risk_level = RiskLevel.READ_ONLY

    def execute(self, tool_input: GitHubRepositoryInput, context: ToolExecutionContext) -> ToolResult:
        data = GitHubIntelligenceService().get_agent_context(tool_input.repository)
        return ToolResult(success=data.get("status") != "UNAVAILABLE", tool_name=self.name, structured_data=data)


class GitHubFreshnessCheckTool(SEAMTool):
    name = "github_freshness_check"
    description = "Check and refresh GitHub Intelligence v2 freshness for a repository."
    category = "github"
    input_schema = GitHubRepositoryInput
    allowed_agents = ["AnalysisAgent", "PlanningAgent", "CodingAgent", "QAAgent", "SupervisorAgent"]
    risk_level = RiskLevel.READ_ONLY

    def execute(self, tool_input: GitHubRepositoryInput, context: ToolExecutionContext) -> ToolResult:
        owner, name = tool_input.repository.split("/", 1)
        record = GitHubIntelligenceService().analyze_or_refresh(owner, name)
        return ToolResult(success=record.status in {"CURRENT", "STALE"}, tool_name=self.name, structured_data=record.model_dump())


class GitHubCompareCommitsTool(SEAMTool):
    name = "github_compare_commits"
    description = "Compare two GitHub commits using GitHub Intelligence v2 change detection."
    category = "github"
    input_schema = GitHubCompareInput
    allowed_agents = ["AnalysisAgent", "PlanningAgent", "CodingAgent", "QAAgent", "SupervisorAgent"]
    risk_level = RiskLevel.READ_ONLY

    def execute(self, tool_input: GitHubCompareInput, context: ToolExecutionContext) -> ToolResult:
        owner, name = tool_input.repository.split("/", 1)
        payload = GitHubIntelligenceService().client.compare_commits(owner, name, tool_input.before_sha, tool_input.after_sha) or {}
        return ToolResult(success=bool(payload), tool_name=self.name, structured_data=payload)


class N8NEmitEventInput(BaseModel):
    event_type: str
    project_id: Optional[str] = None
    task_id: Optional[str] = None
    status: str = "PENDING"
    payload: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[str] = None


class N8NStatusTool(SEAMTool):
    name = "n8n_status"
    description = "Return configured n8n external automation status without exposing secrets."
    category = "n8n"
    input_schema = BaseModel
    allowed_agents = ["SupervisorAgent", "DeliveryAgent", "QAAgent"]
    risk_level = RiskLevel.READ_ONLY

    def execute(self, tool_input: BaseModel, context: ToolExecutionContext) -> ToolResult:
        from backend.integrations.n8n.service import N8NIntegrationService

        status = N8NIntegrationService().status().model_dump()
        return ToolResult(success=True, tool_name=self.name, structured_data=status)


class N8NEmitEventTool(SEAMTool):
    name = "n8n_emit_event"
    description = "Emit an allowlisted SEAM event to n8n external automation."
    category = "n8n"
    input_schema = N8NEmitEventInput
    allowed_agents = ["DeliveryAgent", "SupervisorAgent"]
    risk_level = RiskLevel.LOW

    def execute(self, tool_input: N8NEmitEventInput, context: ToolExecutionContext) -> ToolResult:
        from backend.integrations.n8n.schemas import N8NEvent
        from backend.integrations.n8n.service import N8NIntegrationService

        event_args = {
            "event_type": tool_input.event_type,
            "project_id": tool_input.project_id or context.project_id,
            "task_id": tool_input.task_id or context.task_id,
            "status": tool_input.status,
            "payload": tool_input.payload,
        }
        correlation_id = tool_input.correlation_id or context.metadata.get("correlation_id")
        if correlation_id:
            event_args["correlation_id"] = correlation_id
        event = N8NEvent(**event_args)
        result = N8NIntegrationService().send_event(event)
        return ToolResult(success=result.status == "completed", tool_name=self.name, structured_data=result.model_dump())


class N8NTestConnectionTool(SEAMTool):
    name = "n8n_test_connection"
    description = "Run a lightweight n8n connectivity and test-event check."
    category = "n8n"
    input_schema = BaseModel
    allowed_agents = ["SupervisorAgent", "DeliveryAgent"]
    risk_level = RiskLevel.READ_ONLY

    def execute(self, tool_input: BaseModel, context: ToolExecutionContext) -> ToolResult:
        from backend.integrations.n8n.schemas import N8NEvent
        from backend.integrations.n8n.service import N8NIntegrationService

        service = N8NIntegrationService()
        status = service.status().model_dump()
        event = N8NEvent(event_type="DELIVERY_COMPLETED", project_id=context.project_id, status="TEST", payload={"message": "test"})
        result = service.send_event(event)
        return ToolResult(
            success=result.status == "completed",
            tool_name=self.name,
            structured_data={"status": status, "test_event": result.model_dump()},
        )


class PathInput(BaseModel):
    path: str


class FileSearchInput(BaseModel):
    pattern: str
    root: str = "."


class FileWriteInput(BaseModel):
    path: str
    content: str


class FileReadTool(SEAMTool):
    name = "file_read"
    description = "Read a file within the active project root."
    category = "filesystem"
    input_schema = PathInput
    allowed_agents = ["AnalysisAgent", "PlanningAgent", "CodingAgent", "QAAgent", "DeliveryAgent"]
    risk_level = RiskLevel.READ_ONLY

    def execute(self, tool_input: PathInput, context: ToolExecutionContext) -> ToolResult:
        path = PermissionEngine(default_registry).ensure_safe_path(tool_input.path, context.project_root)
        with open(path, "r", encoding="utf-8") as handle:
            return ToolResult(success=True, tool_name=self.name, stdout=handle.read(), structured_data={"path": path})


class FileSearchTool(SEAMTool):
    name = "file_search"
    description = "Search file names inside the active project root."
    category = "filesystem"
    input_schema = FileSearchInput
    allowed_agents = ["AnalysisAgent", "PlanningAgent", "CodingAgent", "QAAgent", "DeliveryAgent"]
    risk_level = RiskLevel.READ_ONLY

    def execute(self, tool_input: FileSearchInput, context: ToolExecutionContext) -> ToolResult:
        root = PermissionEngine(default_registry).ensure_safe_path(tool_input.root, context.project_root)
        matches = []
        for current, _, files in os.walk(root):
            for filename in files:
                rel = os.path.relpath(os.path.join(current, filename), root)
                if tool_input.pattern.lower() in rel.lower():
                    matches.append(rel)
        return ToolResult(success=True, tool_name=self.name, structured_data={"matches": matches[:200]})


class FileWriteTool(SEAMTool):
    name = "file_write"
    description = "Write a file inside the active project root."
    category = "filesystem"
    input_schema = FileWriteInput
    allowed_agents = ["CodingAgent"]
    risk_level = RiskLevel.MEDIUM

    def execute(self, tool_input: FileWriteInput, context: ToolExecutionContext) -> ToolResult:
        path = PermissionEngine(default_registry).ensure_safe_path(tool_input.path, context.project_root)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(tool_input.content)
        return ToolResult(success=True, tool_name=self.name, structured_data={"path": path})


class FileDeleteTool(SEAMTool):
    name = "file_delete"
    description = "Delete a file inside the active project root."
    category = "filesystem"
    input_schema = PathInput
    allowed_agents = ["CodingAgent"]
    risk_level = RiskLevel.HIGH
    requires_approval = True

    def execute(self, tool_input: PathInput, context: ToolExecutionContext) -> ToolResult:
        path = PermissionEngine(default_registry).ensure_safe_path(tool_input.path, context.project_root)
        if os.path.isdir(path):
            raise ValueError("file_delete does not delete directories")
        os.remove(path)
        return ToolResult(success=True, tool_name=self.name, structured_data={"path": path})


class GitInput(BaseModel):
    args: List[str] = Field(default_factory=list)


class GitBranchNameInput(BaseModel):
    branch_name: str


class GitCheckoutInput(BaseModel):
    ref: str


class GitAddInput(BaseModel):
    paths: List[str] = Field(default_factory=list)


class GitCommitInput(BaseModel):
    message: str


class GitStashInput(BaseModel):
    message: Optional[str] = None


class GitMergeInput(BaseModel):
    branch: str


class GitPushInput(BaseModel):
    remote: str = "origin"
    branch: str
    options: List[str] = Field(default_factory=list)


class GitReadOnlyTool(SEAMTool):
    category = "git"
    input_schema = GitInput
    allowed_agents = ["AnalysisAgent", "PlanningAgent", "SupervisorAgent", "CodingAgent", "QAAgent", "DeliveryAgent"]
    risk_level = RiskLevel.READ_ONLY
    command: List[str] = []

    def execute(self, tool_input: GitInput, context: ToolExecutionContext) -> ToolResult:
        if tool_input.args:
            raise ValueError("Read-only Git tools do not accept arbitrary extra arguments")
        cwd = _safe_git_worktree(context)
        started = time.perf_counter()
        proc = subprocess.run(["git", *self.command, *tool_input.args], cwd=cwd, capture_output=True, text=True, timeout=self.timeout)
        return ToolResult(
            success=proc.returncode == 0,
            tool_name=self.name,
            stdout=proc.stdout,
            stderr=proc.stderr,
            duration_ms=int((time.perf_counter() - started) * 1000),
            structured_data={"exit_code": proc.returncode},
        )


class GitStatusTool(GitReadOnlyTool):
    name = "git_status"
    description = "Run git status in read-only mode."
    command = ["status", "--short"]


class GitDiffTool(GitReadOnlyTool):
    name = "git_diff"
    description = "Run git diff in read-only mode."
    command = ["diff"]


class GitLogTool(GitReadOnlyTool):
    name = "git_log"
    description = "Run git log in read-only mode."
    command = ["log", "--oneline", "-20"]


class GitBranchTool(GitReadOnlyTool):
    name = "git_branch"
    description = "Run git branch in read-only mode."
    command = ["branch", "--show-current"]
    allowed_agents = ["SupervisorAgent", "CodingAgent", "QAAgent", "DeliveryAgent"]


class GitCommandTool(SEAMTool):
    category = "git"
    timeout = 60

    def _run_git(self, context: ToolExecutionContext, args: List[str]) -> ToolResult:
        cwd = _safe_git_worktree(context)
        _reject_dangerous_git_args(args)
        started = time.perf_counter()
        proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=self.timeout)
        return ToolResult(
            success=proc.returncode == 0,
            tool_name=self.name,
            stdout=proc.stdout,
            stderr=proc.stderr,
            duration_ms=int((time.perf_counter() - started) * 1000),
            structured_data={"exit_code": proc.returncode, "command": ["git", *args]},
        )


class GitCreateBranchTool(GitCommandTool):
    name = "git_create_branch"
    description = "Create a Git branch in the active worktree."
    input_schema = GitBranchNameInput
    allowed_agents = ["CodingAgent"]
    risk_level = RiskLevel.LOW

    def execute(self, tool_input: GitBranchNameInput, context: ToolExecutionContext) -> ToolResult:
        _validate_ref(tool_input.branch_name)
        return self._run_git(context, ["branch", tool_input.branch_name])


class GitCheckoutTool(GitCommandTool):
    name = "git_checkout"
    description = "Checkout an existing Git ref in the active worktree."
    input_schema = GitCheckoutInput
    allowed_agents = ["CodingAgent"]
    risk_level = RiskLevel.LOW

    def execute(self, tool_input: GitCheckoutInput, context: ToolExecutionContext) -> ToolResult:
        _validate_ref(tool_input.ref)
        return self._run_git(context, ["checkout", tool_input.ref])


class GitAddTool(GitCommandTool):
    name = "git_add"
    description = "Stage files in the active worktree."
    input_schema = GitAddInput
    allowed_agents = ["CodingAgent"]
    risk_level = RiskLevel.LOW

    def execute(self, tool_input: GitAddInput, context: ToolExecutionContext) -> ToolResult:
        paths = tool_input.paths or ["."]
        safe_paths = [os.path.relpath(PermissionEngine(default_registry).ensure_safe_path(path, context.project_root), _safe_git_worktree(context)) for path in paths]
        return self._run_git(context, ["add", "--", *safe_paths])


class GitCommitTool(GitCommandTool):
    name = "git_commit"
    description = "Create a Git commit in the active worktree."
    input_schema = GitCommitInput
    allowed_agents = ["CodingAgent", "DeliveryAgent"]
    risk_level = RiskLevel.MEDIUM

    def execute(self, tool_input: GitCommitInput, context: ToolExecutionContext) -> ToolResult:
        if not tool_input.message.strip():
            raise ValueError("Commit message is required")
        return self._run_git(context, ["commit", "-m", tool_input.message])


class GitStashTool(GitCommandTool):
    name = "git_stash"
    description = "Stash local changes in the active worktree."
    input_schema = GitStashInput
    allowed_agents = ["CodingAgent"]
    risk_level = RiskLevel.MEDIUM

    def execute(self, tool_input: GitStashInput, context: ToolExecutionContext) -> ToolResult:
        args = ["stash", "push"]
        if tool_input.message:
            args.extend(["-m", tool_input.message])
        return self._run_git(context, args)


class GitMergeTool(GitCommandTool):
    name = "git_merge"
    description = "Merge a branch into the active worktree. Requires approval."
    input_schema = GitMergeInput
    allowed_agents = ["CodingAgent", "DeliveryAgent"]
    risk_level = RiskLevel.HIGH
    requires_approval = True

    def execute(self, tool_input: GitMergeInput, context: ToolExecutionContext) -> ToolResult:
        _validate_ref(tool_input.branch)
        return self._run_git(context, ["merge", "--no-ff", tool_input.branch])


class GitPushTool(GitCommandTool):
    name = "git_push"
    description = "Push a branch to an existing remote. Requires approval and forbids force push."
    input_schema = GitPushInput
    allowed_agents = ["CodingAgent", "DeliveryAgent"]
    risk_level = RiskLevel.HIGH
    requires_approval = True

    def execute(self, tool_input: GitPushInput, context: ToolExecutionContext) -> ToolResult:
        _validate_ref(tool_input.branch)
        _validate_ref(tool_input.remote)
        forbidden = {"--force", "-f", "--force-with-lease", "--mirror", "--delete"}
        if any(option in forbidden or option.startswith("--force") for option in tool_input.options):
            raise ValueError("git_push rejects force/destructive push options")
        return self._run_git(context, ["push", tool_input.remote, tool_input.branch, *tool_input.options])


def _safe_git_worktree(context: ToolExecutionContext) -> str:
    root = context.project_root or os.getcwd()
    root = os.path.abspath(root)
    if not os.path.isdir(root):
        raise ValueError(f"Git worktree does not exist: {root}")
    return root


def _validate_ref(value: str) -> None:
    if not value or any(item in value for item in ["..", "~", "^", ":", "\\", "\n", "\r"]):
        raise ValueError("Invalid Git ref")
    if value.startswith("-"):
        raise ValueError("Git ref cannot be an option")


def _reject_dangerous_git_args(args: List[str]) -> None:
    forbidden = {"--git-dir", "--work-tree", "-C", "--exec-path", "-c"}
    if any(arg in forbidden or arg.startswith("--git-dir=") or arg.startswith("--work-tree=") for arg in args):
        raise ValueError("Git arguments cannot override repository paths or configuration")


class MermaidInput(BaseModel):
    diagram_type: str
    diagram_data: Dict[str, Any]


class MermaidGenerateTool(SEAMTool):
    name = "mermaid_generate"
    description = "Generate Mermaid source as an additional export for SEAM diagrams."
    category = "design"
    input_schema = MermaidInput
    allowed_agents = ["PlanningAgent"]
    risk_level = RiskLevel.LOW

    def execute(self, tool_input: MermaidInput, context: ToolExecutionContext) -> ToolResult:
        title = tool_input.diagram_type.replace("_", " ").title()
        nodes = tool_input.diagram_data.get("nodes", [])
        edges = tool_input.diagram_data.get("edges", [])
        lines = ["flowchart TD", f"%% {title}"]
        for node in nodes:
            node_id = str(node.get("id", "node")).replace("-", "_")
            label = str(node.get("label", node_id)).replace('"', "'")
            lines.append(f'  {node_id}["{label}"]')
        for edge in edges:
            src = str(edge.get("source", "")).replace("-", "_")
            dst = str(edge.get("target", "")).replace("-", "_")
            if src and dst:
                lines.append(f"  {src} --> {dst}")
        source = "\n".join(lines)
        artifact = ""
        if context.project_root:
            out_dir = os.path.join(context.project_root, "design", "diagrams")
            os.makedirs(out_dir, exist_ok=True)
            artifact = os.path.join(out_dir, f"{tool_input.diagram_type}.mmd")
            with open(artifact, "w", encoding="utf-8") as handle:
                handle.write(source)
        return ToolResult(success=True, tool_name=self.name, stdout=source, artifacts=[artifact] if artifact else [], structured_data={"mermaid": source})


class APISpecInput(BaseModel):
    spec: Dict[str, Any]


class APISpecValidateTool(SEAMTool):
    name = "api_spec_validate"
    description = "Validate an OpenAPI JSON specification."
    category = "api"
    input_schema = APISpecInput
    allowed_agents = ["PlanningAgent", "QAAgent"]
    risk_level = RiskLevel.READ_ONLY

    def execute(self, tool_input: APISpecInput, context: ToolExecutionContext) -> ToolResult:
        spec = tool_input.spec
        errors = []
        if "openapi" not in spec:
            errors.append("Missing openapi version")
        if "paths" not in spec or not isinstance(spec.get("paths"), dict):
            errors.append("Missing paths object")
        endpoints = list((spec.get("paths") or {}).keys())
        methods = sorted({method.upper() for path in spec.get("paths", {}).values() for method in path.keys()})
        schema_count = len(((spec.get("components") or {}).get("schemas") or {}))
        return ToolResult(success=not errors, tool_name=self.name, structured_data={
            "valid": not errors,
            "errors": errors,
            "warnings": [],
            "endpoints": endpoints,
            "methods": methods,
            "schema_count": schema_count,
        })


class PytestInput(BaseModel):
    test_path: Optional[str] = None
    test_args: List[str] = Field(default_factory=list)


class PytestRunnerTool(SEAMTool):
    name = "pytest_runner"
    description = "Run pytest safely inside the active project root."
    category = "testing"
    input_schema = PytestInput
    allowed_agents = ["QAAgent"]
    risk_level = RiskLevel.MEDIUM
    timeout = 120

    def execute(self, tool_input: PytestInput, context: ToolExecutionContext) -> ToolResult:
        cwd = context.project_root or os.getcwd()
        command = ["python", "-m", "pytest"]
        if tool_input.test_path:
            command.append(PermissionEngine(default_registry).ensure_safe_path(tool_input.test_path, cwd))
        command.extend(arg for arg in tool_input.test_args if not arg.startswith("-c"))
        started = time.perf_counter()
        proc = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=self.timeout)
        return ToolResult(success=proc.returncode == 0, tool_name=self.name, stdout=proc.stdout, stderr=proc.stderr, duration_ms=int((time.perf_counter() - started) * 1000), structured_data={"exit_code": proc.returncode})


class APITestInput(BaseModel):
    method: str = "GET"
    url: str
    json_body: Optional[Dict[str, Any]] = None


class APITestRunnerTool(SEAMTool):
    name = "api_test_runner"
    description = "Run safe HTTP API checks against localhost services."
    category = "testing"
    input_schema = APITestInput
    allowed_agents = ["QAAgent"]
    risk_level = RiskLevel.READ_ONLY

    def execute(self, tool_input: APITestInput, context: ToolExecutionContext) -> ToolResult:
        if not tool_input.url.startswith(("http://127.0.0.1", "http://localhost")):
            raise ValueError("api_test_runner only allows localhost URLs")
        response = requests.request(tool_input.method.upper(), tool_input.url, json=tool_input.json_body, timeout=10)
        return ToolResult(success=response.status_code < 500, tool_name=self.name, stdout=response.text[:2000], structured_data={"status_code": response.status_code, "headers": dict(response.headers)})


class RuntimeAPIValidatorInput(BaseModel):
    project_root: str = "."
    base_url: str
    contract_id: str = ""
    endpoint: str
    method: str = "GET"
    request: Dict[str, Any] = Field(default_factory=dict)
    expected_request_schema: Dict[str, Any] = Field(default_factory=dict)
    expected_response_schema: Dict[str, Any] = Field(default_factory=dict)
    expected_status_codes: List[int] = Field(default_factory=lambda: [200])
    authentication_required: bool = False
    timeout_seconds: int = Field(default=10, ge=1, le=30)


class RuntimeAPIValidatorTool(SEAMTool):
    name = "runtime_api_validator"
    description = "Validate a running local API endpoint against an existing contract."
    category = "testing"
    input_schema = RuntimeAPIValidatorInput
    allowed_agents = ["QAAgent"]
    risk_level = RiskLevel.READ_ONLY

    def execute(self, tool_input: RuntimeAPIValidatorInput, context: ToolExecutionContext) -> ToolResult:
        started = time.perf_counter()
        method = tool_input.method.upper()
        if method not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
            raise ValueError("Unsupported HTTP method")
        base_url = _safe_runtime_base_url(tool_input.base_url)
        endpoint = "/" + tool_input.endpoint.lstrip("/")
        target_url = urljoin(base_url.rstrip("/") + "/", endpoint.lstrip("/"))
        _assert_same_runtime_origin(base_url, target_url)

        issues = []
        request_issues = _validate_payload(tool_input.request, tool_input.expected_request_schema, source="request", endpoint=endpoint)
        issues.extend(request_issues)
        if request_issues:
            result = {
                "contract_id": tool_input.contract_id,
                "endpoint": endpoint,
                "method": method,
                "request_status": "INVALID",
                "expected_status": tool_input.expected_status_codes,
                "actual_status": None,
                "schema_valid": False,
                "response_valid": False,
                "authentication_valid": False,
                "latency_ms": int((time.perf_counter() - started) * 1000),
                "issues": issues,
                "status": "FAIL",
            }
            return ToolResult(success=False, tool_name=self.name, structured_data=result, duration_ms=result["latency_ms"])

        try:
            json_payload = tool_input.request if method in {"POST", "PUT", "PATCH"} and tool_input.request else None
            response = requests.request(
                method,
                target_url,
                json=json_payload,
                timeout=tool_input.timeout_seconds,
                headers={"Accept": "application/json"},
            )
        except requests.Timeout:
            result = _runtime_result(tool_input, endpoint, method, started, "TIMEOUT", issues=[_runtime_issue("TIMEOUT", "ERROR", endpoint, "response before timeout", "timeout", "Runtime request timed out.")])
            return ToolResult(success=False, tool_name=self.name, structured_data=result, duration_ms=result["latency_ms"])
        except requests.RequestException as exc:
            result = _runtime_result(tool_input, endpoint, method, started, "UNAVAILABLE", issues=[_runtime_issue("CONNECTION_FAILURE", "ERROR", endpoint, "reachable runtime", type(exc).__name__, "Runtime service is unavailable.")])
            return ToolResult(success=False, tool_name=self.name, structured_data=result, duration_ms=result["latency_ms"])

        status_ok = response.status_code in tool_input.expected_status_codes
        if not status_ok:
            issues.append(_runtime_issue("STATUS_CODE_MISMATCH", "ERROR", endpoint, str(tool_input.expected_status_codes), str(response.status_code), "Runtime status code did not match the contract."))
        content_type = response.headers.get("content-type", "")
        response_data = None
        if response.text:
            if "application/json" not in content_type.lower():
                issues.append(_runtime_issue("CONTENT_TYPE_MISMATCH", "ERROR", endpoint, "application/json", content_type or "missing", "Runtime response content type is not JSON."))
            else:
                try:
                    response_data = response.json()
                except ValueError:
                    issues.append(_runtime_issue("RESPONSE_SCHEMA_MISMATCH", "ERROR", endpoint, "valid JSON body", "invalid JSON", "Runtime response body is not valid JSON."))
        response_issues = _validate_payload(response_data or {}, tool_input.expected_response_schema, source="response", endpoint=endpoint)
        issues.extend(response_issues)
        authentication_valid = True
        if tool_input.authentication_required and response.status_code not in {401, 403} and not status_ok:
            authentication_valid = False
            issues.append(_runtime_issue("AUTHENTICATION_MISMATCH", "ERROR", endpoint, "401/403 or successful authorized response", str(response.status_code), "Protected endpoint did not show expected authentication behavior."))
        status = "PASS" if not any(issue["severity"] in {"ERROR", "BLOCKER"} for issue in issues) else "FAIL"
        latency_ms = int((time.perf_counter() - started) * 1000)
        result = {
            "contract_id": tool_input.contract_id,
            "endpoint": endpoint,
            "method": method,
            "request_status": "SENT",
            "expected_status": tool_input.expected_status_codes,
            "actual_status": response.status_code,
            "schema_valid": not response_issues,
            "response_valid": status_ok and not response_issues,
            "authentication_valid": authentication_valid,
            "latency_ms": latency_ms,
            "issues": issues,
            "status": status,
        }
        return ToolResult(success=status == "PASS", tool_name=self.name, structured_data=result, duration_ms=latency_ms)


_RUNTIME_PROCESSES: Dict[str, subprocess.Popen] = {}


class RuntimeManagerInput(BaseModel):
    action: str = "DETECT"
    project_root: str = "."
    profile: Dict[str, Any] = Field(default_factory=dict)
    process_name: Optional[str] = None


class RuntimeManagerTool(SEAMTool):
    name = "runtime_manager"
    description = "Detect, start, health-check, status-check, and stop project-owned local runtimes."
    category = "testing"
    input_schema = RuntimeManagerInput
    allowed_agents = ["QAAgent"]
    risk_level = RiskLevel.MEDIUM

    def execute(self, tool_input: RuntimeManagerInput, context: ToolExecutionContext) -> ToolResult:
        action = tool_input.action.upper()
        root = PermissionEngine(default_registry).ensure_safe_path(tool_input.project_root, context.project_root)
        if action == "DETECT":
            profile = _detect_runtime_profile(root)
            status = "READY" if profile.get("frontend_start_command") or profile.get("backend_start_command") else "NOT_CONFIGURED"
            return ToolResult(success=status == "READY", tool_name=self.name, structured_data={"status": status, "profile": profile})
        if action == "START":
            profile = tool_input.profile or _detect_runtime_profile(root)
            return _runtime_start(self.name, root, profile)
        if action == "HEALTH_CHECK":
            profile = tool_input.profile or _detect_runtime_profile(root)
            health = _runtime_health(profile)
            ready = bool(health) and all(item["status"] == "READY" for item in health)
            return ToolResult(success=ready, tool_name=self.name, structured_data={"status": "READY" if ready else "NOT_READY", "health": health})
        if action == "STATUS":
            return ToolResult(success=True, tool_name=self.name, structured_data=_runtime_status(root))
        if action == "STOP":
            return ToolResult(success=True, tool_name=self.name, structured_data=_runtime_stop(root, tool_input.process_name))
        raise ValueError("Unsupported runtime_manager action")


class DockerInput(BaseModel):
    dockerfile: str = "Dockerfile"
    image_tag: str = "seam-project:latest"


def _safe_runtime_base_url(base_url: str) -> str:
    parsed = urlparse(base_url)
    if parsed.scheme != "http":
        raise ValueError("runtime_api_validator only allows http project runtime URLs")
    host = (parsed.hostname or "").lower()
    if host not in {"127.0.0.1", "localhost"}:
        raise ValueError("runtime_api_validator only allows explicitly configured localhost runtimes")
    if parsed.port is None:
        raise ValueError("runtime_api_validator requires an explicit runtime port")
    if host == "127.0.0.1":
        ip = ipaddress.ip_address(host)
        if not ip.is_loopback:
            raise ValueError("runtime host must be loopback")
    return base_url


def _assert_same_runtime_origin(base_url: str, target_url: str) -> None:
    base = urlparse(base_url)
    target = urlparse(target_url)
    if (base.scheme, base.hostname, base.port) != (target.scheme, target.hostname, target.port):
        raise ValueError("runtime endpoint escapes the configured project runtime origin")


def _validate_payload(payload: Any, schema: Dict[str, Any], source: str, endpoint: str) -> List[Dict[str, Any]]:
    if not schema:
        return []
    issues = []
    if not isinstance(payload, dict):
        return [_runtime_issue(f"{source.upper()}_SCHEMA_MISMATCH", "ERROR", endpoint, "object", type(payload).__name__, f"Runtime {source} body is not an object.")]
    properties = schema.get("properties", schema if isinstance(schema, dict) else {})
    required = set(schema.get("required", [])) if isinstance(schema, dict) else set()
    for field in required:
        if field not in payload:
            issues.append(_runtime_issue(f"{source.upper()}_SCHEMA_MISMATCH", "ERROR", endpoint, f"{field}: required", "missing", f"Runtime {source} is missing required field {field}.", field=field))
    for field, expected in properties.items():
        if field not in payload:
            continue
        expected_type = expected.get("type", "UNKNOWN") if isinstance(expected, dict) else str(expected)
        actual_type = _json_type(payload[field])
        if expected_type != "UNKNOWN" and expected_type != actual_type:
            issues.append(_runtime_issue(f"{source.upper()}_SCHEMA_MISMATCH", "ERROR", endpoint, f"{field}: {expected_type}", f"{field}: {actual_type}", f"Runtime {source} field {field} type mismatch.", field=field))
    return issues


def _json_type(value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int) and not isinstance(value, bool):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    if value is None:
        return "null"
    return type(value).__name__


def _runtime_issue(category: str, severity: str, endpoint: str, expected: str, actual: str, description: str, field: str = "") -> Dict[str, Any]:
    return {
        "issue_id": f"RCI-{abs(hash((category, endpoint, field, expected, actual))) % 100000:05d}",
        "category": category,
        "severity": severity,
        "source": "runtime_api_validator",
        "target": "running application",
        "file": "",
        "endpoint": endpoint,
        "field": field,
        "expected": expected,
        "actual": actual,
        "description": description,
        "suggested_fix": "Align the running API behavior with the static contract or update the contract intentionally.",
    }


def _runtime_result(tool_input: RuntimeAPIValidatorInput, endpoint: str, method: str, started: float, status: str, issues: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    return {
        "contract_id": tool_input.contract_id,
        "endpoint": endpoint,
        "method": method,
        "request_status": "NOT_SENT" if status in {"TIMEOUT", "UNAVAILABLE"} else "SENT",
        "expected_status": tool_input.expected_status_codes,
        "actual_status": None,
        "schema_valid": False,
        "response_valid": False,
        "authentication_valid": False,
        "latency_ms": int((time.perf_counter() - started) * 1000),
        "issues": issues or [],
        "status": status,
    }


def _detect_runtime_profile(root: str) -> Dict[str, Any]:
    profile = {
        "project_root": root,
        "frontend_framework": "UNKNOWN",
        "frontend_start_command": None,
        "backend_framework": "UNKNOWN",
        "backend_start_command": None,
        "frontend_port": None,
        "backend_port": None,
        "expected_health_endpoint": "/health",
        "readiness_timeout": 20,
        "startup_timeout": 30,
    }
    package_path = os.path.join(root, "package.json")
    if os.path.exists(package_path):
        try:
            with open(package_path, "r", encoding="utf-8") as handle:
                package = json.load(handle)
            scripts = package.get("scripts") or {}
            deps = {**(package.get("dependencies") or {}), **(package.get("devDependencies") or {})}
            if "vite" in deps:
                profile["frontend_framework"] = "Vite"
                profile["frontend_port"] = _available_port(5173)
            if "react" in deps and profile["frontend_framework"] == "UNKNOWN":
                profile["frontend_framework"] = "React"
            package_manager = "npm"
            if os.path.exists(os.path.join(root, "pnpm-lock.yaml")):
                package_manager = "pnpm"
            elif os.path.exists(os.path.join(root, "yarn.lock")):
                package_manager = "yarn"
            if "dev" in scripts:
                profile["frontend_start_command"] = [package_manager, "run", "dev", "--", "--host", "127.0.0.1", "--port", str(profile["frontend_port"] or _available_port(5173))]
            elif "start" in scripts:
                profile["frontend_start_command"] = [package_manager, "start"]
                profile["frontend_port"] = profile["frontend_port"] or _available_port(3000)
        except Exception:
            pass
    backend_candidates = [
        ("backend/main.py", "backend.main:app"),
        ("main.py", "main:app"),
        ("app/main.py", "app.main:app"),
    ]
    for rel_path, module in backend_candidates:
        path = os.path.join(root, rel_path)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8", errors="ignore") as handle:
                content = handle.read()
            if "FastAPI(" in content:
                port = _available_port(8401)
                profile["backend_framework"] = "FastAPI"
                profile["backend_port"] = port
                profile["backend_start_command"] = ["python", "-m", "uvicorn", module, "--host", "127.0.0.1", "--port", str(port)]
                break
            if "Flask(" in content:
                port = _available_port(8401)
                profile["backend_framework"] = "Flask"
                profile["backend_port"] = port
                profile["backend_start_command"] = ["python", "-m", "flask", "run", "--host", "127.0.0.1", "--port", str(port)]
                break
    return profile


def _available_port(preferred: int) -> int:
    for port in [preferred, *range(max(1024, preferred + 1), min(65535, preferred + 50))]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise ValueError("No available local runtime port found")


def _validate_runtime_command(command: List[str]) -> None:
    if not command:
        raise ValueError("Runtime command is empty")
    allowed = {"python", "npm", "pnpm", "yarn"}
    exe = os.path.basename(command[0]).lower()
    if exe.endswith(".cmd"):
        exe = exe[:-4]
    if exe not in allowed:
        raise ValueError("Runtime executable is not allowlisted")
    blocked = {"&&", "|", ";", ">", "<", "$(", "`", "--git-dir", "--work-tree", "-C", "-c"}
    for arg in command:
        if any(token in str(arg) for token in blocked):
            raise ValueError("Unsafe runtime command argument")


def _runtime_start(tool_name: str, root: str, profile: Dict[str, Any]) -> ToolResult:
    started = time.perf_counter()
    processes = []
    for name, key, port_key in [
        ("backend", "backend_start_command", "backend_port"),
        ("frontend", "frontend_start_command", "frontend_port"),
    ]:
        command = profile.get(key)
        if not command:
            continue
        _validate_runtime_command(command)
        proc = subprocess.Popen(command, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=False)
        process_key = _process_key(root, name)
        _RUNTIME_PROCESSES[process_key] = proc
        port = profile.get(port_key)
        processes.append({
            "name": name,
            "pid": proc.pid,
            "command": command,
            "project_root": root,
            "port": port,
            "url": f"http://127.0.0.1:{port}" if port else "",
            "start_time": time.time(),
            "status": "STARTED",
        })
    if not processes:
        return ToolResult(success=False, tool_name=tool_name, structured_data={"status": "NOT_CONFIGURED", "profile": profile, "processes": [], "message": "No configured runtime command found."})
    deadline = time.time() + int(profile.get("readiness_timeout") or 20)
    health = []
    while time.time() < deadline:
        health = _runtime_health(profile)
        if health and all(item["status"] == "READY" for item in health):
            base_url = _preferred_base_url(profile)
            return ToolResult(success=True, tool_name=tool_name, duration_ms=int((time.perf_counter() - started) * 1000), structured_data={"status": "STARTED", "base_url": base_url, "profile": profile, "processes": processes, "health": health, "message": "Runtime started."})
        time.sleep(0.5)
    _runtime_stop(root, None)
    return ToolResult(success=False, tool_name=tool_name, duration_ms=int((time.perf_counter() - started) * 1000), structured_data={"status": "TIMEOUT", "profile": profile, "processes": processes, "health": health, "message": "Runtime health check timed out."})


def _runtime_health(profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    checks = []
    endpoint = profile.get("expected_health_endpoint") or "/health"
    for name, port_key in [("backend", "backend_port"), ("frontend", "frontend_port")]:
        port = profile.get(port_key)
        command_key = f"{name}_start_command"
        if not port or not profile.get(command_key):
            continue
        started = time.perf_counter()
        url = f"http://127.0.0.1:{port}{endpoint if name == 'backend' else '/'}"
        try:
            response = requests.get(url, timeout=2)
            status = "READY" if response.status_code < 500 else "NOT_READY"
            checks.append({"name": name, "url": f"http://127.0.0.1:{port}", "status": status, "status_code": response.status_code, "latency_ms": int((time.perf_counter() - started) * 1000), "error": ""})
        except requests.RequestException as exc:
            checks.append({"name": name, "url": f"http://127.0.0.1:{port}", "status": "UNAVAILABLE", "status_code": None, "latency_ms": int((time.perf_counter() - started) * 1000), "error": type(exc).__name__})
    return checks


def _runtime_status(root: str) -> Dict[str, Any]:
    processes = []
    for key, proc in list(_RUNTIME_PROCESSES.items()):
        proc_root, name = key.rsplit(":", 1)
        if proc_root != os.path.abspath(root):
            continue
        processes.append({"name": name, "pid": proc.pid, "command": [], "project_root": root, "port": None, "url": "", "start_time": 0, "status": "RUNNING" if proc.poll() is None else "STOPPED"})
    return {"status": "RUNNING" if any(item["status"] == "RUNNING" for item in processes) else "NOT_RUNNING", "processes": processes}


def _runtime_stop(root: str, process_name: Optional[str]) -> Dict[str, Any]:
    stopped = []
    for key, proc in list(_RUNTIME_PROCESSES.items()):
        proc_root, name = key.rsplit(":", 1)
        if proc_root != os.path.abspath(root):
            continue
        if process_name and name != process_name:
            continue
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
                status = "STOPPED"
            except subprocess.TimeoutExpired:
                proc.kill()
                status = "STOPPED"
        else:
            status = "NOT_RUNNING"
        stopped.append({"name": name, "pid": proc.pid, "status": status})
        _RUNTIME_PROCESSES.pop(key, None)
    return {"status": "STOPPED" if stopped else "NOT_RUNNING", "processes": stopped}


def _preferred_base_url(profile: Dict[str, Any]) -> Optional[str]:
    if profile.get("backend_port"):
        return f"http://127.0.0.1:{profile['backend_port']}"
    if profile.get("frontend_port"):
        return f"http://127.0.0.1:{profile['frontend_port']}"
    return None


def _process_key(root: str, name: str) -> str:
    return f"{os.path.abspath(root)}:{name}"


class DockerValidateTool(SEAMTool):
    name = "docker_validate"
    description = "Validate Dockerfile presence and basic safety."
    category = "docker"
    input_schema = DockerInput
    allowed_agents = ["DeliveryAgent"]
    risk_level = RiskLevel.READ_ONLY

    def execute(self, tool_input: DockerInput, context: ToolExecutionContext) -> ToolResult:
        path = PermissionEngine(default_registry).ensure_safe_path(tool_input.dockerfile, context.project_root)
        warnings = []
        with open(path, "r", encoding="utf-8") as handle:
            content = handle.read()
        if "USER root" in content:
            warnings.append("Dockerfile explicitly uses root")
        if ":latest" in content:
            warnings.append("Base image uses latest tag")
        return ToolResult(success=True, tool_name=self.name, structured_data={"valid": True, "warnings": warnings})


class DockerBuildTool(SEAMTool):
    name = "docker_build"
    description = "Build a Docker image without pushing or deploying."
    category = "docker"
    input_schema = DockerInput
    allowed_agents = ["DeliveryAgent"]
    risk_level = RiskLevel.MEDIUM
    requires_approval = True
    timeout = 300

    def execute(self, tool_input: DockerInput, context: ToolExecutionContext) -> ToolResult:
        cwd = context.project_root or os.getcwd()
        PermissionEngine(default_registry).ensure_safe_path(tool_input.dockerfile, cwd)
        proc = subprocess.run(["docker", "build", "-f", tool_input.dockerfile, "-t", tool_input.image_tag, "."], cwd=cwd, capture_output=True, text=True, timeout=self.timeout)
        return ToolResult(success=proc.returncode == 0, tool_name=self.name, stdout=proc.stdout, stderr=proc.stderr, structured_data={"exit_code": proc.returncode, "image_tag": tool_input.image_tag})


def register_default_tools(registry=default_registry) -> None:
    for tool in [
        RAGSearchTool(),
        GitHubRepositoryContextTool(),
        GitHubFreshnessCheckTool(),
        GitHubCompareCommitsTool(),
        N8NStatusTool(),
        N8NEmitEventTool(),
        N8NTestConnectionTool(),
        FileReadTool(),
        FileSearchTool(),
        FileWriteTool(),
        FileDeleteTool(),
        GitStatusTool(),
        GitDiffTool(),
        GitLogTool(),
        GitBranchTool(),
        GitCreateBranchTool(),
        GitCheckoutTool(),
        GitAddTool(),
        GitCommitTool(),
        GitStashTool(),
        GitMergeTool(),
        GitPushTool(),
        MermaidGenerateTool(),
        APISpecValidateTool(),
        PytestRunnerTool(),
        APITestRunnerTool(),
        RuntimeAPIValidatorTool(),
        RuntimeManagerTool(),
        DockerValidateTool(),
        DockerBuildTool(),
    ]:
        if not registry.is_registered(tool.name):
            registry.register(tool)
    from backend.tools.frontend import register_frontend_tools

    register_frontend_tools(registry)
