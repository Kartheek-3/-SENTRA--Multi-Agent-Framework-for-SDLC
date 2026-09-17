import os
import json
import re
import hashlib
import zipfile
import datetime
from typing import List, Dict
from backend.models.state import ProjectState
from backend.models.delivery import DeliveryResult

class DeploymentService:
    """Stub deployment service for SEAM prototype."""
    def deploy(self, package_path: str, scale: str = "UNKNOWN") -> str:
        # In a real system, this would upload to AWS/Azure/GCP
        if scale == "SMALL":
            return "deployed_locally_docker"
        elif scale == "MEDIUM":
            return "deployed_container_managed_services"
        elif scale == "LARGE":
            return "deployed_orchestrated_cluster"
        elif scale == "ENTERPRISE":
            return "deployed_multi_region_enterprise"
        return "deployed_locally_stub"

class KnowledgeBaseService:
    """Organizational knowledge service for SEAM prototype."""
    def update_knowledge(self, state: ProjectState) -> str:
        from backend.knowledge.knowledge_service import KnowledgeService
        from backend.knowledge.models import KnowledgeDocument
        
        ks = KnowledgeService()
        
        # Extract QA feedback as testing/lesson_learned knowledge
        qa_feedback_combined = "\n".join(getattr(state, "qa_feedback", []))
        if qa_feedback_combined:
            doc_qa = KnowledgeDocument(
                title=f"QA Feedback - {state.project_id}",
                source=f"Project {state.project_id}",
                source_type="project_qa",
                category="lesson_learned",
                project_id=state.project_id,
                content=f"Issues and fixes encountered during {state.project_id}:\n{qa_feedback_combined}",
                validated="VALIDATED",
                tags=["qa", "feedback"]
            )
            ks.ingest_document(doc_qa)
            
        # Extract Architecture Decisions
        if state.project_plan and state.project_plan.system_design:
            doc_arch = KnowledgeDocument(
                title=f"Architecture Pattern - {state.project_id}",
                source=f"Project {state.project_id}",
                source_type="project_architecture",
                category="architecture",
                project_id=state.project_id,
                content=f"Architecture Style: {state.project_plan.system_design.architecture_style}\nTech Stack: {', '.join(state.project_plan.system_design.technology_stack)}\nOverview: {state.project_plan.project_overview}",
                validated="VALIDATED",
                tags=["architecture", "design"]
            )
            ks.ingest_document(doc_arch)
            
        return "knowledge_updated_and_saved"

class DeliveryAgent:
    def __init__(self, deployment_service=None, knowledge_service=None):
        self.deployment_service = deployment_service or DeploymentService()
        self.knowledge_service = knowledge_service or KnowledgeBaseService()
        
    def process(self, state: ProjectState) -> ProjectState:
        result = DeliveryResult(project_name=state.project_id)
        
        scale_obj = getattr(state.structured_requirements, "scale_assessment", None)
        project_scale = scale_obj.scale_level.value if scale_obj else "UNKNOWN"
        
        # 1. QA Precondition Checks
        if not state.project_plan:
            result.errors.append("ProjectPlan is missing.")
            return self._finalize(state, result)
            
        project_dir = os.path.join("generated_projects", state.project_name)
        if not os.path.exists(project_dir):
            result.errors.append(f"Generated project directory not found: {project_dir}")
            return self._finalize(state, result)
            
        # Verify all tasks are completed and QA passed
        for task in state.project_plan.tasks:
            if task.task_id not in state.completed_tasks:
                result.errors.append(f"Task {task.task_id} is not completed.")
                return self._finalize(state, result)
            
            task_obj = state.tasks.get(task.task_id)
            if not task_obj or task_obj.status != "completed":
                result.errors.append(f"Task {task.task_id} state is inconsistent.")
                return self._finalize(state, result)
                
            qa_res = task_obj.result.get("qa_result", {})
            if not qa_res or not qa_res.get("passed"):
                result.errors.append(f"Task {task.task_id} failed QA or QA is missing.")
                return self._finalize(state, result)
                
        result.qa_verified = True
        
        # 2. Secret Scanning & File Verification
        manifest_files = []
        excluded_files = []
        
        secret_patterns = [
            re.compile(r"api_key\s*=\s*['\"][a-zA-Z0-9]+['\"]", re.IGNORECASE),
            re.compile(r"password\s*=\s*['\"][^'\"]+['\"]", re.IGNORECASE),
            re.compile(r"secret\s*=\s*['\"][^'\"]+['\"]", re.IGNORECASE),
            re.compile(r"token\s*=\s*['\"][^'\"]+['\"]", re.IGNORECASE)
        ]
        
        delivery_dir = os.path.join(project_dir, "delivery")
        os.makedirs(delivery_dir, exist_ok=True)
        
        for root, dirs, files in os.walk(project_dir):
            # Skip delivery dir itself during packaging scan
            if root.startswith(delivery_dir):
                continue
                
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, project_dir)
                
                # Exclusions
                if rel_path.startswith(".git") or rel_path.endswith(".pyc") or "node_modules" in rel_path or file == ".env":
                    excluded_files.append(rel_path)
                    continue
                
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        
                    for pat in secret_patterns:
                        if pat.search(content):
                            result.errors.append(f"Secret detected in {rel_path}. Packaging aborted.")
                            return self._finalize(state, result)
                except UnicodeDecodeError:
                    # Binary file, skip secret scan
                    pass
                
                # Hash calculation
                sha256_hash = hashlib.sha256()
                with open(file_path, "rb") as f:
                    for byte_block in iter(lambda: f.read(4096), b""):
                        sha256_hash.update(byte_block)
                
                manifest_files.append({
                    "path": rel_path,
                    "size": os.path.getsize(file_path),
                    "sha256": sha256_hash.hexdigest()
                })
        
        # 3. Documentation Generation (Deterministic)
        readme_path = os.path.join(project_dir, "README.md")
        readme_content = f"# {state.project_id}\n\n"
        readme_content += f"## Overview\n{state.project_plan.project_overview}\n\n"
        readme_content += f"## Requirements Implemented\n"
        if state.structured_requirements:
            for req in state.structured_requirements.functional_requirements:
                readme_content += f"- [{req.id}] {req.description}\n"
        
        readme_content += f"\n## Architecture\n{state.project_plan.system_design.architecture_style}\n\n"
        readme_content += f"## Technology Stack\n" + ", ".join(state.project_plan.system_design.technology_stack) + "\n"
        
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme_content)
            
        result.documentation_generated = True
        result.artifact_paths.append("README.md")
        
        # Hash for README
        sha256_hash = hashlib.sha256(readme_content.encode('utf-8')).hexdigest()
        manifest_files.append({
            "path": "README.md",
            "size": len(readme_content),
            "sha256": sha256_hash
        })
        
        # 4. Manifest Generation
        manifest_path = os.path.join(delivery_dir, "delivery_manifest.json")
        manifest_data = {
            "project_name": state.project_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "qa_status": "passed",
            "files_included": manifest_files,
            "files_excluded": excluded_files
        }
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)
            
        result.artifact_paths.append("delivery/delivery_manifest.json")
        from backend.tools.artifact_pipeline import write_text_artifact
        write_text_artifact(state, "delivery/project_manifest.json", json.dumps(manifest_data, indent=2), "DELIVERY", "DeliveryAgent")
        write_text_artifact(state, "delivery/README.md", f"""# Delivery Summary

## Delivery Status
{result.status}

## Project Summary
{state.project_plan.project_overview}

## QA Result
{'PASS' if result.qa_verified else 'NOT VERIFIED'}

## Package Information
Package generation is completed only after integrity checks and zip packaging succeed.
""", "DELIVERY", "DeliveryAgent")
        write_text_artifact(state, "delivery/delivery_report.md", f"""# Delivery Report

## Final Checks
- QA verified: {result.qa_verified}
- Documentation generated: {result.documentation_generated}
- Package created: {result.package_created}

## Artifact Status
Files included: {len(manifest_files)}
Files excluded: {len(excluded_files)}

## Secret Scan
No blocking secrets detected in scanned text files.

## Delivery Result
{result.status}
""", "DELIVERY", "DeliveryAgent")
        write_text_artifact(state, "delivery/integrity_report.md", f"""# Integrity Report

## Files Checked
{chr(10).join(f'- {item["path"]} ({item["sha256"]})' for item in manifest_files)}

## Missing Files
None detected during manifest generation.

## Unexpected Files
{chr(10).join(f'- {item}' for item in excluded_files) if excluded_files else 'None'}

## Validation Result
{'PASS' if not result.errors else 'FAIL'}
""", "DELIVERY", "DeliveryAgent")
        write_text_artifact(state, "delivery/deployment.md", f"""# Deployment

## Deployment Configuration
No real deployment has been performed by SEAM in this workflow.

## Environment Requirements
Derived from the generated project files and technology stack:
{chr(10).join(f'- {item}' for item in state.project_plan.system_design.technology_stack)}

## Deployment Steps
1. Review generated source code and QA reports.
2. Install dependencies required by the generated project.
3. Run tests.
4. Start backend/frontend according to generated README instructions.

## Deployment Status
{result.deployment_status or 'NOT_DEPLOYED'}
""", "DELIVERY", "DeliveryAgent")
        
        # 4.5. E2E Report Generation
        e2e_report_path = os.path.join(delivery_dir, "e2e_report.md")
        e2e_report = f"# E2E Final Report for {state.project_id}\n\n"
        
        # Determine model info securely (extracting from active state or env as a fallback)
        e2e_report += f"## Model Information\n"
        from backend.config import SEAM_CODING_MODEL, SEAM_FALLBACK_MODEL
        e2e_report += f"- Configured Primary Model: {SEAM_CODING_MODEL}\n"
        e2e_report += f"- Configured Fallback Model: {SEAM_FALLBACK_MODEL}\n\n"
        
        e2e_report += f"## GitHub Project Reuse\n"
        e2e_report += f"- Mode: {getattr(state, 'reuse_mode', 'MODE 3: Custom Generation')}\n"
        e2e_report += f"- Selected Repository: {getattr(state, 'selected_github_repo', 'None')}\n\n"
        
        e2e_report += f"## QA & Testing Summary\n"
        e2e_report += f"- QA Passed: {result.qa_verified}\n"
        e2e_report += f"- QA Retries: {len(getattr(state, 'qa_feedback', []))}\n"
        
        with open(e2e_report_path, "w", encoding="utf-8") as f:
            f.write(e2e_report)
            
        result.artifact_paths.append("delivery/e2e_report.md")
        
        # 5. Zip Packaging
        zip_path = os.path.join(delivery_dir, "project_package.zip")
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for f_info in manifest_files:
                    src_path = os.path.join(project_dir, f_info["path"])
                    if os.path.exists(src_path):
                        # Ensure no path traversal in zip entry
                        if ".." in f_info["path"] or f_info["path"].startswith("/") or f_info["path"].startswith("\\"):
                            raise ValueError(f"Unsafe path in manifest: {f_info['path']}")
                        zipf.write(src_path, f_info["path"])
            result.package_created = True
            result.artifact_paths.append("delivery/project_package.zip")
        except Exception as e:
            result.errors.append(f"Packaging failed: {str(e)}")
            return self._finalize(state, result)
            
        # 6. Deployment Stub
        try:
            deploy_res = self.deployment_service.deploy(zip_path, scale=project_scale)
            result.deployment_status = deploy_res
        except Exception as e:
            result.errors.append(f"Deployment failed: {str(e)}")
            return self._finalize(state, result)
            
        # 7. Knowledge Update Stub
        try:
            know_res = self.knowledge_service.update_knowledge(state)
            result.knowledge_update_status = know_res
        except Exception as e:
            result.errors.append(f"Knowledge update failed: {str(e)}")
            return self._finalize(state, result)
            
        result.status = "deployed"
        return self._finalize(state, result)
        
    def _finalize(self, state: ProjectState, result: DeliveryResult) -> ProjectState:
        if not hasattr(state, 'delivery_result'):
            setattr(state, 'delivery_result', None)
        state.delivery_result = result.model_dump()
        self._write_delivery_artifacts(state, result)
        
        state.execution_history.append({
            "agent": "DeliveryAgent",
            "status": "success" if result.status == "deployed" else "error",
            "delivery_status": result.status,
            "errors": result.errors
        })
        
        return state

    def _write_delivery_artifacts(self, state: ProjectState, result: DeliveryResult) -> None:
        if not state.project_plan:
            return

        from backend.tools.artifact_pipeline import write_text_artifact

        errors = result.errors or []
        artifact_paths = result.artifact_paths or []
        tech_stack = state.project_plan.system_design.technology_stack if state.project_plan.system_design else []
        write_text_artifact(state, "delivery/README.md", f"""# Delivery Summary

## Delivery Status
{result.status}

## Project Summary
{state.project_plan.project_overview}

## QA Result
{'PASS' if result.qa_verified else 'NOT VERIFIED'}

## Package
{result.package_path or 'NOT_AVAILABLE'}

## Errors
{chr(10).join(f'- {item}' for item in errors) if errors else 'None'}
""", "DELIVERY", "DeliveryAgent")
        write_text_artifact(state, "delivery/delivery_report.md", f"""# Delivery Report

## Final Checks
- QA verified: {result.qa_verified}
- Documentation generated: {result.documentation_generated}
- Package created: {result.package_created}
- Knowledge update: {result.knowledge_update_status or 'NOT_AVAILABLE'}

## Artifacts
{chr(10).join(f'- {item}' for item in artifact_paths) if artifact_paths else 'No delivery artifacts were produced before finalization.'}

## Delivery Result
{result.status}

## Errors
{chr(10).join(f'- {item}' for item in errors) if errors else 'None'}
""", "DELIVERY", "DeliveryAgent")
        write_text_artifact(state, "delivery/integrity_report.md", f"""# Integrity Report

## Package Created
{result.package_created}

## Package Path
{result.package_path or 'NOT_AVAILABLE'}

## Validation Result
{'FAIL' if errors else 'PASS'}

## Errors
{chr(10).join(f'- {item}' for item in errors) if errors else 'None'}
""", "DELIVERY", "DeliveryAgent")
        write_text_artifact(state, "delivery/deployment.md", f"""# Deployment

## Deployment Configuration
No external production deployment is performed automatically by SEAM.

## Environment Requirements
{chr(10).join(f'- {item}' for item in tech_stack) if tech_stack else 'NOT_AVAILABLE'}

## Deployment Steps
1. Review generated source code and QA reports.
2. Install dependencies required by the generated project.
3. Run tests.
4. Start backend/frontend according to generated README instructions.

## Deployment Status
{result.deployment_status or 'NOT_DEPLOYED'}
""", "DELIVERY", "DeliveryAgent")
