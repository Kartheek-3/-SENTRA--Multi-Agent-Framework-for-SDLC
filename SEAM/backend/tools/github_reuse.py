
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class GitHubReuseManager:
    """
    Manages GitHub repository search, evaluation, and quality scoring
    for deterministic project reuse decisions.
    """
    
    def __init__(self):
        # We could initialize a GitHub client here if a token is provided in env
        pass
        
    def calculate_quality_score(self, repo_info: Dict[str, Any], requirement: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a repository deterministically based on key factors:
        domain_match       20%
        technology_match   20%
        architecture       15%
        testing            15%
        security           10%
        maintenance        10%
        documentation       5%
        license             5%
        """
        score_details = {}
        total_score = 0.0
        
        # 1. Domain Match (0-20) - Simulation (In a real scenario, compare repo topics/description with requirement domain)
        domain_score = 15.0 if "ecommerce" in repo_info.get("description", "").lower() else 5.0
        score_details["domain_match"] = domain_score
        total_score += domain_score
        
        # 2. Technology Match (0-20)
        tech_score = 15.0 # Stubbed evaluation
        score_details["technology_match"] = tech_score
        total_score += tech_score
        
        # 3. Architecture (0-15)
        arch_score = 10.0 # Stubbed evaluation
        score_details["architecture"] = arch_score
        total_score += arch_score
        
        # 4. Testing (0-15)
        test_score = 15.0 if repo_info.get("has_tests", False) else 0.0
        score_details["testing"] = test_score
        total_score += test_score
        
        # 5. Security (0-10)
        sec_score = 8.0 # Stubbed evaluation
        score_details["security"] = sec_score
        total_score += sec_score
        
        # 6. Maintenance (0-10)
        maint_score = 8.0 if repo_info.get("updated_recently", True) else 2.0
        score_details["maintenance"] = maint_score
        total_score += maint_score
        
        # 7. Documentation (0-5)
        doc_score = 5.0 if repo_info.get("has_readme", True) else 0.0
        score_details["documentation"] = doc_score
        total_score += doc_score
        
        # 8. License (0-5)
        license_score = 5.0 if repo_info.get("license") in ["MIT", "Apache-2.0"] else 0.0
        score_details["license"] = license_score
        total_score += license_score
        
        return {
            "total_score": total_score,
            "details": score_details,
            "is_suitable": total_score >= 70.0,
            "reuse_mode": self._determine_mode(total_score)
        }
        
    def _determine_mode(self, score: float) -> str:
        if score >= 80.0:
            return "MODE 1: High-quality matching repository"
        elif score >= 50.0:
            return "MODE 2: Partially relevant repository"
        else:
            return "MODE 3: No suitable repository exists"
            
    def evaluate_candidates(self, candidates: List[Dict[str, Any]], requirement: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Rank a list of candidates based on quality score.
        """
        evaluated = []
        for candidate in candidates:
            eval_result = self.calculate_quality_score(candidate, requirement)
            candidate["evaluation"] = eval_result
            evaluated.append(candidate)
            
        return sorted(evaluated, key=lambda x: x["evaluation"]["total_score"], reverse=True)
