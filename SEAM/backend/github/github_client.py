import requests
from typing import List, Dict, Any, Optional
import os

class GitHubClient:
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.headers = {"Accept": "application/vnd.github.v3+json"}
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            self.headers["Authorization"] = f"token {token}"

    def search_repositories(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search GitHub for repositories matching the query."""
        url = f"{self.base_url}/search/repositories"
        params = {"q": query, "per_page": limit, "sort": "stars", "order": "desc"}
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            if response.status_code == 200:
                return response.json().get("items", [])
            else:
                return []
        except Exception:
            return []

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
        url = f"{self.base_url}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                tree = response.json().get("tree", [])
                return [item["path"] for item in tree if item["type"] == "blob"]
            return []
        except Exception:
            return []
