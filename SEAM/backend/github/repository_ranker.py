from typing import List, Dict
from backend.models.github import RepositoryCandidate, RepositoryEvaluation
import re

class RepositoryRanker:
    # Deterministic weights
    WEIGHTS = {
        "domain": 0.20,
        "technology": 0.20,
        "architecture": 0.15,
        "testing": 0.15,
        "security": 0.10,
        "maintenance": 0.10,
        "documentation": 0.05,
        "license": 0.05
    }

    def __init__(self, required_domain: str, required_technologies: List[str]):
        self.required_domain = required_domain.lower()
        self.required_technologies = [t.lower() for t in required_technologies]

    def evaluate(self, candidate: RepositoryCandidate) -> RepositoryEvaluation:
        eval = RepositoryEvaluation(repository_url=candidate.repository_url)
        
        # 1. Domain Match
        search_text = f"{candidate.name} {candidate.description} {' '.join(candidate.topics)}".lower()
        domain_tokens = self.required_domain.split()
        matches = sum(1 for t in domain_tokens if t in search_text)
        eval.domain_match_score = (matches / max(len(domain_tokens), 1)) * 100.0
        
        # 2. Technology Match
        tech_matches = sum(1 for req_tech in self.required_technologies 
                           if any(req_tech in t.lower() for t in candidate.detected_technologies))
        if self.required_technologies:
            eval.technology_match_score = (tech_matches / len(self.required_technologies)) * 100.0
        else:
            eval.technology_match_score = 100.0
            
        # 3. Architecture (Heuristic: complex projects often have more files/topics, Docker)
        if "Docker" in candidate.detected_technologies or "Docker Compose" in candidate.detected_technologies:
            eval.architecture_score += 50
        if len(candidate.detected_technologies) > 2:
            eval.architecture_score += 50
        eval.architecture_score = min(eval.architecture_score, 100.0)

        # 4. Testing
        eval.testing_score = 100.0 if candidate.test_indicators else 0.0
        
        # 5. Security
        eval.security_score = 100.0 if candidate.security_indicators else 50.0 # Default to 50 if no explicit config, could be a risk
        
        # 6. Maintenance
        # Simplistic: > 100 stars is active, open issues mean people use it
        activity_score = min((candidate.stars / 100) * 50 + (candidate.open_issues / 10) * 50, 100.0)
        eval.maintenance_score = activity_score

        # 7. Documentation
        eval.documentation_score = 100.0 if candidate.documentation_indicators or candidate.readme_available else 0.0
        
        # 8. License
        acceptable_licenses = ["mit", "apache-2.0", "bsd", "bsd-2-clause", "bsd-3-clause", "gpl", "gpl-3.0", "lgpl", "mpl"]
        if candidate.license.lower() in acceptable_licenses:
            eval.license_score = 100.0
        elif candidate.license == "unknown":
            eval.license_score = 0.0
            eval.risks.append("Unknown or missing license. Legal risk.")
        else:
            eval.license_score = 50.0
            eval.risks.append(f"License {candidate.license} may require compatibility review.")
            
        # Calculate overall score
        eval.overall_score = (
            (eval.domain_match_score * self.WEIGHTS["domain"]) +
            (eval.technology_match_score * self.WEIGHTS["technology"]) +
            (eval.architecture_score * self.WEIGHTS["architecture"]) +
            (eval.testing_score * self.WEIGHTS["testing"]) +
            (eval.security_score * self.WEIGHTS["security"]) +
            (eval.maintenance_score * self.WEIGHTS["maintenance"]) +
            (eval.documentation_score * self.WEIGHTS["documentation"]) +
            (eval.license_score * self.WEIGHTS["license"])
        )

        # Generate recommendation
        if eval.overall_score >= 75:
            eval.recommendation = "SUITABLE FOR ENHANCEMENT"
        elif eval.overall_score >= 50:
            eval.recommendation = "PARTIAL MATCH - HIGH REWORK REQUIRED"
        else:
            eval.recommendation = "NOT SUITABLE"
            
        # Populate strengths and weaknesses
        if eval.domain_match_score > 80: eval.strengths.append("Strong domain alignment.")
        if eval.technology_match_score < 50: eval.weaknesses.append("Poor technology stack match.")
        if not candidate.test_indicators: eval.weaknesses.append("No testing indicators found.")

        return eval
