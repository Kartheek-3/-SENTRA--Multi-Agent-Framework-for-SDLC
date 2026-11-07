import os
import json
import uuid
import logging
from typing import Dict, Any, List, Optional

from backend.github.intelligence_models import (
    DetailedRepositoryProfile,
    EnhancementPlan,
    EnhancementPlanItem,
    ProjectUnderstanding,
    utc_now,
)

logger = logging.getLogger(__name__)

class EnhancementPlanningService:
    def create_plan(
        self,
        project_id: str,
        user_requirement: str,
        profile: DetailedRepositoryProfile,
        understanding: ProjectUnderstanding
    ) -> EnhancementPlan:
        """Generates a structured, targeted enhancement plan based on real repository evidence."""
        plan_id = f"plan-{uuid.uuid4().hex[:8]}"

        # Extract target candidate files from profile and user requirement
        req_lower = user_requirement.lower()
        candidate_files = []
        for ref in profile.source_references:
            f = ref.get("file", "")
            if f and f not in candidate_files:
                candidate_files.append(f)

        # Look for entry points or route files
        if profile.application_entry_points:
            candidate_files.extend([ep for ep in profile.application_entry_points if ep not in candidate_files])

        target_files = candidate_files[:4] if candidate_files else ["src/index.ts" if "TypeScript" in profile.detected_languages else "main.py"]

        # Formulate targeted improvement item
        primary_item = EnhancementPlanItem(
            item_id="ENH-001",
            title=f"Targeted Enhancement: {user_requirement[:60]}",
            current_behavior=(
                f"Repository '{profile.repository}' currently operates on baseline commit {profile.commit_sha[:8]}. "
                f"Existing entry points: {', '.join(profile.application_entry_points) or 'Standard structure'}."
            ),
            proposed_improvement=(
                f"Implement user requirement without breaking existing APIs or modifying unrelated files: {user_requirement}."
            ),
            why_needed=(
                "Fulfills the user's enhancement goal while strictly maintaining backward compatibility and existing conventions."
            ),
            files_expected_to_change=target_files,
            dependencies=profile.frameworks,
            compatibility_risks=[
                "Ensure exported functions and existing endpoints retain backward compatibility",
                "Do not modify or remove existing tests unless explicitly updating test assertions",
            ],
            tests_required=profile.test_commands or ["python -m pytest" if "Python" in profile.detected_languages else "npm test"],
            verification_steps=[
                "1. Apply targeted patch to specified files only.",
                "2. Run automated test suite and type check.",
                "3. Verify git diff confines changes strictly to expected files.",
                "4. Confirm clean status before marking complete.",
            ],
            rollback_considerations=(
                f"Revert changes using git reset/checkout to base commit {profile.commit_sha[:8]}."
            ),
            approved=False,
        )

        plan = EnhancementPlan(
            plan_id=plan_id,
            repository=profile.repository,
            branch=profile.branch,
            base_commit_sha=profile.commit_sha,
            summary=f"Enhancement plan for {profile.repository}: {user_requirement[:100]}",
            items=[primary_item],
            status="pending_approval",
            created_at=utc_now(),
        )

        return plan

    def write_artifacts(self, project_dir: str, plan: EnhancementPlan) -> Dict[str, str]:
        """Writes enhancement_plan.json and enhancement_plan.md artifacts."""
        os.makedirs(project_dir, exist_ok=True)
        json_path = os.path.join(project_dir, "enhancement_plan.json")
        md_path = os.path.join(project_dir, "enhancement_plan.md")

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(plan.model_dump(), f, indent=2)

        items_md = []
        for idx, item in enumerate(plan.items, start=1):
            items_md.append(f"""### {idx}. {item.title} (ID: `{item.item_id}`)
- **Current Behavior**: {item.current_behavior}
- **Proposed Improvement**: {item.proposed_improvement}
- **Why Needed**: {item.why_needed}
- **Files Expected to Change**: {', '.join(f'`{f}`' for f in item.files_expected_to_change)}
- **Dependencies**: {', '.join(item.dependencies) or 'None'}
- **Compatibility Risks**: {', '.join(item.compatibility_risks)}
- **Tests Required**: {', '.join(item.tests_required)}
- **Verification Steps**:
{chr(10).join(f'  {step}' for step in item.verification_steps)}
- **Rollback Consideration**: {item.rollback_considerations}
- **Approval Status**: `{"APPROVED" if item.approved else "PENDING USER APPROVAL"}`
""")

        md_content = f"""# Enhancement Plan

**Repository**: `{plan.repository}`  
**Base Commit**: `{plan.base_commit_sha}`  
**Plan Status**: `{plan.status.upper()}`  
**Created At**: `{plan.created_at}`  

## Executive Summary
{plan.summary}

---

## Detailed Enhancement Items
{chr(10).join(items_md)}

---

> [!IMPORTANT]
> User approval is required before any source files in the repository workspace are modified.
"""
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        return {"json": json_path, "md": md_path}
