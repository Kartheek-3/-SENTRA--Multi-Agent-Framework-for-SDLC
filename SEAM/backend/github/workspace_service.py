import os
import re
import shutil
import subprocess
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Limits for safe workspace operation
MAX_WORKSPACE_FILES = 10000
MAX_WORKSPACE_SIZE_BYTES = 250 * 1024 * 1024  # 250 MB
MAX_CLONE_TIMEOUT_SECONDS = 60
GITHUB_URL_REGEX = re.compile(
    r"^(?:https?://github\.com/|git@github\.com:)?([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+?)(?:\.git)?/?$"
)

class SafeWorkspaceError(Exception):
    pass

class SafeWorkspaceService:
    def __init__(self, base_workspaces_dir: Optional[str] = None):
        self.base_dir = os.path.abspath(base_workspaces_dir or os.path.join(os.getcwd(), "workspaces", "repos"))
        os.makedirs(self.base_dir, exist_ok=True)

    @staticmethod
    def parse_github_url(url_or_slug: str) -> Tuple[str, str, str]:
        """Validates and parses a GitHub repository URL or slug.
        
        Returns: (owner, name, canonical_https_url)
        Raises: SafeWorkspaceError if invalid
        """
        cleaned = (url_or_slug or "").strip()
        match = GITHUB_URL_REGEX.match(cleaned)
        if not match:
            raise SafeWorkspaceError(f"Invalid GitHub repository URL or identifier: '{url_or_slug}'")
        owner, name = match.group(1), match.group(2)
        if ".." in owner or ".." in name or "/" in owner or "/" in name:
            raise SafeWorkspaceError(f"Potentially unsafe repository path detected in: '{url_or_slug}'")
        canonical_url = f"https://github.com/{owner}/{name}"
        return owner, name, canonical_url

    def get_workspace_path(self, project_id: str) -> str:
        safe_pid = re.sub(r"[^a-zA-Z0-9_-]", "_", project_id)
        path = os.path.abspath(os.path.join(self.base_dir, safe_pid))
        if not path.startswith(self.base_dir):
            raise SafeWorkspaceError("Path traversal detected in workspace path resolution")
        return path

    def validate_path_confinement(self, workspace_path: str, relative_path: str) -> str:
        """Confines a relative path strictly within the workspace directory."""
        if os.path.isabs(relative_path):
            raise SafeWorkspaceError(f"Absolute paths forbidden in repository workspace: '{relative_path}'")
        if ".." in relative_path or relative_path.startswith("/") or relative_path.startswith("\\"):
            raise SafeWorkspaceError(f"Path traversal forbidden in repository workspace: '{relative_path}'")
        full_path = os.path.abspath(os.path.join(workspace_path, relative_path))
        if not full_path.startswith(os.path.abspath(workspace_path)):
            raise SafeWorkspaceError(f"Resolved path escapes repository workspace: '{relative_path}'")
        return full_path

    def prepare_workspace(
        self,
        project_id: str,
        repo_url_or_slug: str,
        branch: str = "main",
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Prepares an isolated, safe local workspace for the repository.
        
        Uses safe subprocess arguments, depth=1 shallow clone, and limits execution time.
        """
        owner, name, canonical_url = self.parse_github_url(repo_url_or_slug)
        workspace_path = self.get_workspace_path(project_id)
        
        auth_url = canonical_url
        if token:
            # Mask token in auth_url for subprocess, never logged or leaked
            auth_url = f"https://x-access-token:{token}@github.com/{owner}/{name}.git"

        # If already exists and is a git repository
        git_dir = os.path.join(workspace_path, ".git")
        if os.path.exists(git_dir):
            logger.info(f"Workspace already exists for {project_id} at {workspace_path}")
            base_sha = self._get_head_sha(workspace_path)
            return {
                "workspace_path": workspace_path,
                "owner": owner,
                "name": name,
                "branch": branch,
                "base_commit_sha": base_sha,
                "status": "ready",
                "reused_existing": True
            }

        # Clean any partial directory
        if os.path.exists(workspace_path):
            shutil.rmtree(workspace_path, ignore_errors=True)
        os.makedirs(workspace_path, exist_ok=True)

        # Execute safe shallow clone with argument list (never shell concatenation)
        clone_cmd = [
            "git", "clone",
            "--depth", "1",
            "--branch", branch,
            "--single-branch",
            auth_url,
            workspace_path
        ]

        try:
            res = subprocess.run(
                clone_cmd,
                capture_output=True,
                text=True,
                timeout=MAX_CLONE_TIMEOUT_SECONDS,
                check=False
            )
            if res.returncode != 0:
                # If branch specific clone failed, attempt default branch
                err_msg = res.stderr or res.stdout or "git clone failed"
                # Strip token if present in error message
                if token:
                    err_msg = err_msg.replace(token, "[REDACTED]")
                
                # If branch failed, try cloning without --branch to get default
                if "Remote branch" in err_msg and "not found" in err_msg:
                    fallback_cmd = ["git", "clone", "--depth", "1", auth_url, workspace_path]
                    fb_res = subprocess.run(fallback_cmd, capture_output=True, text=True, timeout=MAX_CLONE_TIMEOUT_SECONDS, check=False)
                    if fb_res.returncode != 0:
                        fb_err = fb_res.stderr or fb_res.stdout
                        if token:
                            fb_err = fb_err.replace(token, "[REDACTED]")
                        shutil.rmtree(workspace_path, ignore_errors=True)
                        raise SafeWorkspaceError(f"Clone failed: {fb_err}")
                else:
                    shutil.rmtree(workspace_path, ignore_errors=True)
                    raise SafeWorkspaceError(f"Clone failed: {err_msg}")
        except subprocess.TimeoutExpired:
            shutil.rmtree(workspace_path, ignore_errors=True)
            raise SafeWorkspaceError(f"Clone timed out after {MAX_CLONE_TIMEOUT_SECONDS}s")
        except FileNotFoundError:
            # git executable not found
            shutil.rmtree(workspace_path, ignore_errors=True)
            raise SafeWorkspaceError("git executable not found on host system")

        # Verify file count and size limits
        self._enforce_workspace_limits(workspace_path)
        base_sha = self._get_head_sha(workspace_path)

        return {
            "workspace_path": workspace_path,
            "owner": owner,
            "name": name,
            "branch": branch,
            "base_commit_sha": base_sha,
            "status": "ready",
            "reused_existing": False
        }

    def _get_head_sha(self, workspace_path: str) -> str:
        try:
            res = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=workspace_path,
                capture_output=True,
                text=True,
                timeout=5,
                check=False
            )
            if res.returncode == 0:
                return res.stdout.strip()
        except Exception:
            pass
        return "unknown_sha"

    def _enforce_workspace_limits(self, workspace_path: str):
        file_count = 0
        total_size = 0
        for root, dirs, files in os.walk(workspace_path):
            if ".git" in dirs:
                dirs.remove(".git")
            file_count += len(files)
            for f in files:
                try:
                    fp = os.path.join(root, f)
                    total_size += os.path.getsize(fp)
                except OSError:
                    pass
            if file_count > MAX_WORKSPACE_FILES:
                raise SafeWorkspaceError(f"Repository file limit exceeded: {file_count} > {MAX_WORKSPACE_FILES}")
            if total_size > MAX_WORKSPACE_SIZE_BYTES:
                raise SafeWorkspaceError(f"Repository size limit exceeded: {total_size} > {MAX_WORKSPACE_SIZE_BYTES} bytes")

    def get_diff(self, workspace_path: str) -> str:
        """Returns the current git diff in the workspace."""
        try:
            # First try diff HEAD (staged + unstaged working tree diff vs last commit)
            res = subprocess.run(
                ["git", "diff", "HEAD"],
                cwd=workspace_path,
                capture_output=True,
                text=True,
                timeout=10,
                check=False
            )
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout

            # Check for newly added / untracked files using intent-to-add
            subprocess.run(["git", "add", "-N", "."], cwd=workspace_path, capture_output=True, check=False)
            res_untracked = subprocess.run(
                ["git", "diff"],
                cwd=workspace_path,
                capture_output=True,
                text=True,
                timeout=10,
                check=False
            )
            if res_untracked.returncode == 0 and res_untracked.stdout.strip():
                return res_untracked.stdout

            # If empty, try git diff HEAD~1 (if a commit was just made)
            res2 = subprocess.run(
                ["git", "diff", "HEAD~1"],
                cwd=workspace_path,
                capture_output=True,
                text=True,
                timeout=10,
                check=False
            )
            if res2.returncode == 0 and res2.stdout.strip():
                return res2.stdout

            # Fallback to plain git diff
            res3 = subprocess.run(
                ["git", "diff"],
                cwd=workspace_path,
                capture_output=True,
                text=True,
                timeout=10,
                check=False
            )
            return res3.stdout if res3.returncode == 0 else ""
        except Exception as exc:
            logger.warning(f"Failed to get git diff in {workspace_path}: {exc}")
            return ""

    def get_changed_files(self, workspace_path: str) -> List[Dict[str, Any]]:
        """Returns list of modified, added, and deleted files in workspace."""
        changed = []
        try:
            res = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=workspace_path,
                capture_output=True,
                text=True,
                timeout=5,
                check=False
            )
            if res.returncode == 0 and res.stdout.strip():
                for line in res.stdout.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    status_code = line[:2].strip()
                    rel_path = line[2:].strip().replace('"', "")
                    changed.append({
                        "path": rel_path,
                        "status": status_code,
                    })
            if not changed:
                # If everything was already committed, check git diff --name-status HEAD~1
                res2 = subprocess.run(
                    ["git", "diff", "--name-status", "HEAD~1"],
                    cwd=workspace_path,
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False
                )
                if res2.returncode == 0 and res2.stdout.strip():
                    for line in res2.stdout.splitlines():
                        parts = line.strip().split("\t")
                        if len(parts) >= 2:
                            changed.append({
                                "path": parts[1].strip(),
                                "status": parts[0].strip(),
                            })
        except Exception as exc:
            logger.warning(f"Failed to get git status in {workspace_path}: {exc}")
        return changed

    def clean_workspace(self, project_id: str):
        workspace_path = self.get_workspace_path(project_id)
        if os.path.exists(workspace_path):
            shutil.rmtree(workspace_path, ignore_errors=True)
