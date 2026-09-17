import os
import json
from typing import List, Optional
from backend.models.github import RepositoryCandidate, RepositoryEvaluation, RepositorySelection
from backend.github.github_client import GitHubClient
from backend.github.repository_analyzer import RepositoryAnalyzer
from backend.github.repository_ranker import RepositoryRanker

class GitHubRepositoryService:
    def __init__(self, reuse_threshold: float = 75.0):
        self.client = GitHubClient()
        self.analyzer = RepositoryAnalyzer(self.client)
        self.reuse_threshold = reuse_threshold

    def search_and_evaluate(self, domain: str, requirement: str, technologies: List[str] = None) -> RepositorySelection:
        if not technologies:
            technologies = []
            
        # 1. Search GitHub
        search_query = f"{domain} {requirement[:50]}"
        raw_items = self.client.search_repositories(search_query, limit=5)
        
        selection = RepositorySelection()
        ranker = RepositoryRanker(domain, technologies)
        
        candidates_and_evals = []
        
        for item in raw_items:
            candidate = self.analyzer.analyze_repository(item)
            evaluation = ranker.evaluate(candidate)
            candidates_and_evals.append((candidate, evaluation))
            
        # Sort by overall score
        candidates_and_evals.sort(key=lambda x: x[1].overall_score, reverse=True)
        
        if not candidates_and_evals:
            selection.reason = "No candidate repositories found."
            return selection
            
        best_candidate, best_eval = candidates_and_evals[0]
        
        selection.alternatives = [c for c, _ in candidates_and_evals[1:]]
        selection.selected_repository = best_candidate
        selection.evaluation = best_eval
        
        # Threshold decision
        if best_eval.overall_score >= self.reuse_threshold and best_eval.license_score > 0:
            selection.reuse_existing = True
            selection.confidence = best_eval.overall_score
            selection.reason = f"Repository {best_candidate.owner}/{best_candidate.name} is highly suitable for enhancement (Score: {best_eval.overall_score:.1f})."
        else:
            selection.reuse_existing = False
            selection.confidence = best_eval.overall_score
            selection.reason = f"Best repository {best_candidate.owner}/{best_candidate.name} did not meet reuse threshold or has license issues."
            
        selection.license_notes = best_candidate.license
        selection.risks = best_eval.risks
        
        return selection
        
    def download_baseline(self, project_id: str, project_name: str, candidate: RepositoryCandidate):
        """Downloads baseline context (e.g. README, package config, license) into a controlled directory."""
        # Note: Bounded retrieval. We don't download everything, just structural info and README.
        base_dir = os.path.join(os.getcwd(), "generated_projects", project_name, "repository")
        os.makedirs(base_dir, exist_ok=True)
        
        readme_content = self.client.get_repository_content(candidate.owner, candidate.name, "README.md")
        if readme_content:
            with open(os.path.join(base_dir, "README.md"), "w", encoding="utf-8") as f:
                f.write(readme_content)
                
        # Write metadata
        with open(os.path.join(base_dir, "repository_metadata.json"), "w", encoding="utf-8") as f:
            json.dump(candidate.model_dump(), f, indent=2)
            
        # Write attribution
        with open(os.path.join(base_dir, "ATTRIBUTION.md"), "w", encoding="utf-8") as f:
            f.write(f"# Attribution\n\nThis project enhances the repository: {candidate.repository_url}\n")
            f.write(f"License: {candidate.license}\n")
            f.write("This file must be preserved.\n")
