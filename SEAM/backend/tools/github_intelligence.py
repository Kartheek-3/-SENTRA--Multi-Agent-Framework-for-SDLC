import json
import os
from typing import Any, Dict, List

from backend.events import event_bus
from backend.github.repository_service import GitHubRepositoryService
from backend.tools.artifact_pipeline import write_text_artifact


class GitHubIntelligenceTool:
    def __init__(self, max_repositories: int = 3):
        self.max_repositories = max_repositories

    def should_research(self, state) -> bool:
        requirement = (state.user_requirement or "").lower()
        if len(requirement) < 40:
            return False
        useful_terms = ["react", "fastapi", "django", "spring", "node", "sqlite", "postgres", "api", "dashboard", "management", "tracker", "app"]
        return any(term in requirement for term in useful_terms)

    def research(self, state) -> Dict[str, Any]:
        project_id = state.project_id
        if not os.getenv("GITHUB_TOKEN"):
            state.github_status = "token_missing"
            event_bus.emit_sync("GITHUB_RESEARCH_UNAVAILABLE", {
                "project_id": project_id,
                "status": "token_missing",
                "summary": "GitHub Intelligence unavailable - continuing without repository context.",
            })
            return {"status": "token_missing", "repositories": [], "context": "GitHub token missing. Continue without repository context."}

        if not self.should_research(state):
            state.github_status = "not_needed"
            return {"status": "not_needed", "repositories": [], "context": "GitHub research not needed for this project."}

        event_bus.emit_sync("GITHUB_SEARCH_STARTED", {
            "project_id": project_id,
            "summary": "Searching relevant public repositories.",
        })

        try:
            technologies = self._extract_technologies(state)
            service = GitHubRepositoryService(reuse_threshold=75.0)
            selection = service.search_and_evaluate(state.domain, state.user_requirement, technologies)
            state.github_selection = selection
            repositories = self._selection_to_results(selection)
            findings = {
                "status": "completed" if repositories else "no_relevant_repositories",
                "domain": state.domain,
                "technologies": technologies,
                "repositories": repositories[:self.max_repositories],
                "context": self._context_summary(repositories),
            }
            state.github_findings = findings
            state.github_status = findings["status"]

            event_bus.emit_sync("GITHUB_SEARCH_COMPLETED", {
                "project_id": project_id,
                "summary": f"{len(repositories[:self.max_repositories])} relevant repositories analyzed.",
            })
            if selection.selected_repository:
                event_bus.emit_sync("GITHUB_REPOSITORY_SELECTED", {
                    "project_id": project_id,
                    "repository": f"{selection.selected_repository.owner}/{selection.selected_repository.name}",
                    "url": selection.selected_repository.repository_url,
                    "summary": selection.reason,
                })

            self._write_artifacts(state, findings)
            event_bus.emit_sync("GITHUB_ANALYSIS_COMPLETED", {
                "project_id": project_id,
                "summary": "GitHub repository context added to project state.",
            })
            return findings
        except Exception as exc:
            state.github_status = "failed"
            event_bus.emit_sync("GITHUB_ANALYSIS_FAILED", {
                "project_id": project_id,
                "error": str(exc),
                "summary": "GitHub Intelligence failed - continuing without repository context.",
            })
            return {"status": "failed", "repositories": [], "context": "GitHub analysis failed. Continue without repository context."}

    def _extract_technologies(self, state) -> List[str]:
        text = state.user_requirement.lower()
        known = ["React", "FastAPI", "SQLite", "PostgreSQL", "Python", "TypeScript", "JavaScript", "Node", "Docker"]
        found = [tech for tech in known if tech.lower() in text]
        if state.project_plan and state.project_plan.system_design:
            found.extend(state.project_plan.system_design.technology_stack)
        return sorted(set(found))

    def _selection_to_results(self, selection) -> List[Dict[str, Any]]:
        if not selection or not selection.selected_repository:
            return []
        pairs = [(selection.selected_repository, selection.evaluation)]
        pairs.extend((candidate, None) for candidate in selection.alternatives)
        results = []
        for candidate, evaluation in pairs[:self.max_repositories]:
            results.append({
                "repository": f"{candidate.owner}/{candidate.name}",
                "url": candidate.repository_url,
                "relevance_score": round((evaluation.overall_score if evaluation else 0.0) / 100.0, 3),
                "domain": candidate.description or "",
                "technologies": candidate.detected_technologies,
                "architecture": "Detected from repository structure and dependency files.",
                "testing": "Testing indicators present." if candidate.test_indicators else "No testing indicators found.",
                "security": "Security indicators present." if candidate.security_indicators else "No explicit security indicators found.",
                "documentation": "README/docs found." if candidate.readme_available or candidate.documentation_indicators else "Limited documentation detected.",
                "license": candidate.license,
                "useful_patterns": self._patterns(candidate),
                "limitations": (evaluation.weaknesses if evaluation else []) + (evaluation.risks if evaluation else []),
            })
        return results

    def _patterns(self, candidate) -> List[str]:
        patterns = []
        if candidate.readme_available:
            patterns.append("Project documentation pattern")
        if candidate.test_indicators:
            patterns.append("Testing folder or test naming pattern")
        if candidate.detected_technologies:
            patterns.append("Dependency and technology organization")
        return patterns or ["General repository structure reference"]

    def _context_summary(self, repositories: List[Dict[str, Any]]) -> str:
        if not repositories:
            return "No relevant GitHub repository context available."
        lines = ["GitHub repository context. Use as reference only; do not copy source files blindly."]
        for repo in repositories[:self.max_repositories]:
            lines.append(f"- {repo['repository']} ({repo['url']}), score={repo['relevance_score']}, tech={', '.join(repo['technologies']) or 'unknown'}")
            for pattern in repo["useful_patterns"]:
                lines.append(f"  - pattern: {pattern}")
            for limitation in repo["limitations"][:3]:
                lines.append(f"  - limitation: {limitation}")
        return "\n".join(lines)

    def _write_artifacts(self, state, findings: Dict[str, Any]) -> None:
        json_content = json.dumps(findings, indent=2)
        write_text_artifact(state, "analysis/github_intelligence.json", json_content, "ANALYSIS", "GitHubIntelligence")
        rows = []
        for repo in findings.get("repositories", []):
            rows.append(f"| {repo['repository']} | {repo['relevance_score']} | {', '.join(repo['technologies']) or 'unknown'} | {repo['license']} | {repo['url']} |")
        table = "\n".join(rows) if rows else "| None | 0 | unknown | unknown | - |"
        md = f"""# GitHub Intelligence

## Status
{findings.get('status')}

## Repository Findings
| Repository | Relevance | Technologies | License | URL |
|---|---:|---|---|---|
{table}

## Agent Context
{findings.get('context', 'No repository context available.')}

## Security Boundary
- Repositories are used as static reference only.
- SEAM does not execute repository code.
- SEAM does not copy repository source files automatically.
- GitHub tokens are never written to this artifact.
"""
        write_text_artifact(state, "analysis/github_intelligence.md", md, "ANALYSIS", "GitHubIntelligence")
