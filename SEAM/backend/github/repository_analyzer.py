import re
from typing import List, Dict, Any
from backend.models.github import RepositoryCandidate
from backend.github.github_client import GitHubClient

class RepositoryAnalyzer:
    def __init__(self, client: GitHubClient):
        self.client = client

    def analyze_repository(self, item: Dict[str, Any]) -> RepositoryCandidate:
        owner = item.get("owner", {}).get("login", "")
        name = item.get("name", "")
        
        candidate = RepositoryCandidate(
            repository_url=item.get("html_url", ""),
            owner=owner,
            name=name,
            description=item.get("description", ""),
            language=item.get("language", ""),
            stars=item.get("stargazers_count", 0),
            forks=item.get("forks_count", 0),
            open_issues=item.get("open_issues_count", 0),
            last_updated=item.get("updated_at", ""),
            topics=item.get("topics", []),
            default_branch=item.get("default_branch", "main")
        )
        
        # License detection
        license_data = item.get("license")
        if license_data and isinstance(license_data, dict):
            candidate.license = license_data.get("spdx_id", "unknown")
            if candidate.license == "NOASSERTION":
                candidate.license = "unknown"
        
        # Structure analysis using tree
        tree_paths = self.client.get_repository_tree(owner, name, candidate.default_branch)
        
        candidate.readme_available = any(p.lower().startswith("readme") for p in tree_paths)
        
        # Detect testing
        test_indicators = ["test", "tests", "spec", "cypress", "__tests__", "pytest"]
        candidate.test_indicators = any(any(ind in p.lower() for ind in test_indicators) for p in tree_paths)
        
        # Detect documentation
        doc_indicators = ["docs", "doc", "wiki", "swagger", "openapi"]
        candidate.documentation_indicators = any(any(ind in p.lower() for ind in doc_indicators) for p in tree_paths)
        
        # Detect security indicators (basic static check without execution)
        security_indicators = ["security.md", "dependabot.yml", "snyk", ".github/workflows/codeql", "sonar-project"]
        candidate.security_indicators = any(any(ind in p.lower() for ind in security_indicators) for p in tree_paths)
        
        # Detect technologies from package files
        technologies = set()
        if candidate.language:
            technologies.add(candidate.language)
            
        package_files = {
            "package.json": "Node.js",
            "requirements.txt": "Python",
            "pyproject.toml": "Python",
            "pom.xml": "Java/Maven",
            "build.gradle": "Java/Gradle",
            "Dockerfile": "Docker",
            "docker-compose.yml": "Docker Compose",
            "go.mod": "Go",
            "Cargo.toml": "Rust"
        }
        
        for p in tree_paths:
            basename = p.split("/")[-1]
            if basename in package_files:
                technologies.add(package_files[basename])
                
        candidate.detected_technologies = list(technologies)
        
        return candidate
