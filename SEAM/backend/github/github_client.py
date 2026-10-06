import requests
from typing import List, Dict, Any, Optional
import os
import time

from backend.config import GITHUB_TIMEOUT_SECONDS

class GitHubClient:
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.headers = {"Accept": "application/vnd.github.v3+json"}
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            self.headers["Authorization"] = f"token {token}"
        self.last_error = ""
        self.rate_limited = False

    def _request(self, path: str, params: Optional[Dict[str, Any]] = None, retries: int = 2) -> Optional[Dict[str, Any]]:
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        self.last_error = ""
        self.rate_limited = False
        for attempt in range(retries + 1):
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=GITHUB_TIMEOUT_SECONDS)
                if response.status_code == 403 and response.headers.get("X-RateLimit-Remaining") == "0":
                    self.rate_limited = True
                    self.last_error = "GitHub API rate limit exceeded"
                    return None
                if response.status_code == 404:
                    self.last_error = "GitHub resource not found"
                    return None
                if response.status_code >= 500 and attempt < retries:
                    time.sleep(0.25 * (2 ** attempt))
                    continue
                if response.status_code != 200:
                    self.last_error = f"GitHub API returned HTTP {response.status_code}"
                    return None
                return response.json()
            except requests.Timeout:
                self.last_error = "GitHub API request timed out"
                if attempt < retries:
                    time.sleep(0.25 * (2 ** attempt))
                    continue
                return None
            except Exception as exc:
                self.last_error = f"GitHub API request failed: {exc.__class__.__name__}"
                return None
        return None

    def search_repositories(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search GitHub for repositories matching the query."""
        params = {"q": query, "per_page": limit, "sort": "stars", "order": "desc"}
        payload = self._request("/search/repositories", params=params)
        return payload.get("items", []) if payload else []

    def get_repository_content(self, owner: str, repo: str, path: str) -> Optional[str]:
        """Fetch raw content of a file from a repository."""
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/{path}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return response.text
            return None
        except Exception:
            return None

    def get_repository_tree(self, owner: str, repo: str, branch: str = "HEAD") -> List[str]:
        """Fetch the top-level tree of a repository to check for file existence."""
        payload = self.get_repository_tree_payload(owner, repo, branch)
        return [item["path"] for item in payload if item.get("type") == "blob"]

    def get_repository(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        return self._request(f"/repos/{owner}/{repo}")

    def get_branch(self, owner: str, repo: str, branch: str) -> Optional[Dict[str, Any]]:
        return self._request(f"/repos/{owner}/{repo}/branches/{branch}")

    def get_latest_commit_sha(self, owner: str, repo: str, branch: str) -> Optional[str]:
        payload = self.get_branch(owner, repo, branch)
        if not payload:
            return None
        return ((payload.get("commit") or {}).get("sha")) or None

    def get_repository_tree_payload(self, owner: str, repo: str, branch: str = "HEAD") -> List[Dict[str, Any]]:
        payload = self._request(f"/repos/{owner}/{repo}/git/trees/{branch}", params={"recursive": "1"})
        return payload.get("tree", []) if payload else []

    def compare_commits(self, owner: str, repo: str, before_sha: str, after_sha: str) -> Optional[Dict[str, Any]]:
        return self._request(f"/repos/{owner}/{repo}/compare/{before_sha}...{after_sha}")
