import os
import json
import re
import hashlib
import zipfile
import datetime
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from backend.events import event_bus
from backend.models.state import ProjectState
from backend.models.delivery import (
    DeliveryResult,
    DeploymentArtifact,
    DeploymentProfile,
    DeploymentResult,
    EnvironmentVariableRequirement,
    PostDeploymentVerification,
    ReleaseReadiness,
    RollbackInfo,
    SecretFinding,
)

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
        try:
            from backend.evaluation.ablation import capability_enabled, mark_disabled
            from backend.knowledge.domain_intelligence import DomainIntelligenceService
            domain_service = DomainIntelligenceService()
            if capability_enabled(state, "domain_rag") and not state.domain_context:
                if state.domain_identification:
                    domain_service.retrieve_context(state, current_task="delivery preparation")
            if capability_enabled(state, "domain_rag"):
                domain_service.persist_traceability(state, "DeliveryAgent", "Delivery preparation used validated domain context where available.")
            else:
                mark_disabled(state, "domain_rag", "DeliveryAgent", "Delivery domain traceability skipped by experiment configuration.")
        except Exception as exc:
            state.errors.append(f"Delivery domain context warning: {exc}")
        
        scale_obj = getattr(state.structured_requirements, "scale_assessment", None)
        project_scale = scale_obj.scale_level.value if scale_obj else "UNKNOWN"
        
        # 1. QA Precondition Checks
        if not state.project_plan:
            result.errors.append("ProjectPlan is missing.")
            return self._finalize(state, result)
        project_dir = os.path.join("generated_projects", state.project_name)
        release_readiness = self._prepare_delivery_intelligence(state, project_dir)
        if release_readiness.status in {"BLOCKED", "NOT_READY"}:
            result.errors.extend(release_readiness.blockers)
            event_bus.emit_sync("DELIVERY_BLOCKED", {
                "project_id": state.project_id,
                "agent": "DeliveryAgent",
                "status": release_readiness.status,
                "summary": "Delivery blocked by release readiness gates.",
                "blockers": release_readiness.blockers,
            })
            return self._finalize(state, result)
        unresolved_repairs = [plan for plan in state.repair_plans if plan.status != "RESOLVED"]
        failed_targeted = [item for item in state.targeted_verifications if item.status in {"FAIL", "BLOCKED"}]
        failed_regressions = [item for item in state.regression_results if item.status in {"FAIL", "BLOCKED"}]
        blocker_defects = [defect for defect in state.defect_locations if defect.confidence == "HIGH" and defect.layer not in {"CONFIGURATION"}]
        if unresolved_repairs or failed_targeted or failed_regressions or blocker_defects:
            result.errors.append("Delivery blocked by unresolved repair, targeted verification, regression, or blocker defect evidence.")
            return self._finalize(state, result)
            
        if not os.path.exists(project_dir):
            result.errors.append(f"Generated project directory not found: {project_dir}")
            return self._finalize(state, result)
        try:
            from backend.tools.agent_tools import run_agent_tool
            dockerfile_path = os.path.join(project_dir, "Dockerfile")
            if os.path.exists(dockerfile_path):
                run_agent_tool(state, "DeliveryAgent", "docker_validate", {"dockerfile": "Dockerfile"})
                run_agent_tool(state, "DeliveryAgent", "docker_build", {"dockerfile": "Dockerfile", "image_tag": f"seam-{state.project_name}:latest"}, approved=True)
            else:
                result.errors.append("Dockerfile not found; Docker tools skipped.")
        except Exception as exc:
            result.errors.append(f"Docker tool execution failed: {exc}")
            
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
        readme_entry = {
            "path": "README.md",
            "size": len(readme_content),
            "sha256": sha256_hash
        }
        existing_idx = next(
            (i for i, f in enumerate(manifest_files) if os.path.normpath(f.get("path", "")) == "README.md"),
            None
        )
        if existing_idx is not None:
            manifest_files[existing_idx] = readme_entry
        else:
            manifest_files.append(readme_entry)
        
        # 4. Manifest Generation
        manifest_path = os.path.join(delivery_dir, "delivery_manifest.json")
        result.manifest_path = manifest_path
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
        self._record_deployment_package(state, result, manifest_files, excluded_files)
        event_bus.emit_sync("PACKAGE_CREATED", {
            "project_id": state.project_id,
            "agent": "DeliveryAgent",
            "path": "delivery/delivery_manifest.json",
            "summary": "Release manifest created.",
        })
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
        result.package_path = zip_path
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                seen_arcnames = set()
                for f_info in manifest_files:
                    rel_fpath = f_info["path"]
                    # Ensure no path traversal in zip entry
                    if ".." in rel_fpath or rel_fpath.startswith("/") or rel_fpath.startswith("\\"):
                        raise ValueError(f"Unsafe path in manifest: {rel_fpath}")
                    arcname = rel_fpath.replace("\\", "/")
                    if arcname in seen_arcnames:
                        continue
                    src_path = os.path.join(project_dir, rel_fpath)
                    if os.path.exists(src_path):
                        zipf.write(src_path, arcname)
                        seen_arcnames.add(arcname)
            result.package_created = True
            result.artifact_paths.append("delivery/project_package.zip")
            if state.deployment_result:
                state.deployment_result.package_path = zip_path
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
            
        self._run_post_deployment_verification(state)
        result.status = "deployed"
        event_bus.emit_sync("DELIVERY_COMPLETED", {
            "project_id": state.project_id,
            "agent": "DeliveryAgent",
            "status": result.status,
            "summary": "Delivery preparation completed.",
        })
        return self._finalize(state, result)

    def _prepare_delivery_intelligence(self, state: ProjectState, project_dir: str) -> ReleaseReadiness:
        event_bus.emit_sync("RELEASE_READINESS_STARTED", {
            "project_id": state.project_id,
            "agent": "DeliveryAgent",
            "summary": "Aggregating QA, repair, runtime, contract, E2E, artifact, and security evidence.",
        })

        profile = self._detect_deployment_profile(state, Path(project_dir))
        state.deployment_profile = profile
        event_bus.emit_sync("DEPLOYMENT_PROFILE_DETECTED", {
            "project_id": state.project_id,
            "agent": "DeliveryAgent",
            "target": profile.target,
            "summary": f"Deployment target detected: {profile.target}",
        })

        secret_findings = self._scan_project_secrets(Path(project_dir)) if Path(project_dir).exists() else []
        readiness = self._build_release_readiness(state, Path(project_dir), secret_findings)
        state.release_readiness = readiness
        state.rollback_info = self._build_rollback_info(state)
        state.post_deployment_verification = PostDeploymentVerification()

        state.deployment_result = DeploymentResult(
            status="BLOCKED" if readiness.status in {"BLOCKED", "NOT_READY"} else "PREPARED",
            deployment_target=profile.target,
            git=self._git_metadata(Path(project_dir)),
            runtime_information={
                "runtime_status": state.runtime_status,
                "runtime_base_url": state.runtime_base_url,
            },
            build_information={
                "build_status": readiness.build_status,
                "dockerfile": profile.dockerfile,
                "containerization_status": profile.containerization_status,
            },
            environment_requirements=profile.required_environment_variables,
            errors=readiness.blockers,
        )

        event_bus.emit_sync("RELEASE_READINESS_COMPLETED", {
            "project_id": state.project_id,
            "agent": "DeliveryAgent",
            "status": readiness.status,
            "summary": f"Release readiness: {readiness.status}",
            "blockers": readiness.blockers,
            "warnings": readiness.warnings,
        })
        if readiness.status in {"BLOCKED", "NOT_READY"}:
            event_bus.emit_sync("RELEASE_BLOCKED", {
                "project_id": state.project_id,
                "agent": "DeliveryAgent",
                "status": readiness.status,
                "summary": "Release readiness has blocking evidence.",
                "blockers": readiness.blockers,
            })
        return readiness

    def _detect_deployment_profile(self, state: ProjectState, project_dir: Path) -> DeploymentProfile:
        profile = DeploymentProfile(application_type=self._detect_application_type(state, project_dir))
        if not project_dir.exists():
            return profile

        dockerfile = self._first_existing(project_dir, ["Dockerfile", "dockerfile"])
        compose_file = self._first_existing(project_dir, ["docker-compose.yml", "docker-compose.yaml", "compose.yml"])
        kubernetes_manifests = [
            str(path.relative_to(project_dir)).replace("\\", "/")
            for path in project_dir.rglob("*.yaml")
            if any(key in path.name.lower() or key in str(path).lower() for key in ["deployment", "service", "k8s", "kubernetes"])
        ]

        if dockerfile:
            profile.target = "Docker"
            profile.containerized = True
            profile.containerization_status = "CONFIGURED"
            profile.dockerfile = dockerfile
        elif kubernetes_manifests:
            profile.target = "Kubernetes"
            profile.kubernetes_manifests = kubernetes_manifests
            profile.containerization_status = "CONFIGURED"
        elif compose_file:
            profile.target = "generic container deployment"
            profile.containerization_status = "CONFIGURED"
        else:
            profile.target = "NOT_CONFIGURED"
            profile.containerization_status = "NOT_CONFIGURED"

        profile.compose_file = compose_file
        if not profile.kubernetes_manifests:
            profile.kubernetes_manifests = kubernetes_manifests
        profile.frontend = self._detect_frontend_deployment(state, project_dir)
        profile.backend = self._detect_backend_deployment(project_dir)
        profile.build_command = profile.frontend.get("build_command")
        profile.artifact_directory = profile.frontend.get("artifact_directory")
        profile.required_environment_variables = self._detect_environment_requirements(project_dir)
        profile.exposed_ports = self._detect_exposed_ports(project_dir, dockerfile)
        profile.health_endpoint = profile.backend.get("health_endpoint") or (state.runtime_base_url if state.runtime_base_url else None)
        profile.start_command = profile.backend.get("start_command")
        profile.rollback_strategy = "git_commit_and_package_redeploy" if profile.target != "NOT_CONFIGURED" else None
        return profile

    def _build_release_readiness(self, state: ProjectState, project_dir: Path, secret_findings: List[SecretFinding]) -> ReleaseReadiness:
        blockers: List[str] = []
        warnings: List[str] = []

        qa_status = "PASS" if self._qa_passed(state) else "FAIL"
        if qa_status != "PASS":
            blockers.append("Task failed QA or QA is missing.")

        unresolved_repairs = [plan for plan in state.repair_plans if plan.status != "RESOLVED"]
        failed_targeted = [item for item in state.targeted_verifications if item.status in {"FAIL", "BLOCKED"}]
        failed_regressions = [item for item in state.regression_results if item.status in {"FAIL", "BLOCKED"}]
        blocker_defects = [defect for defect in state.defect_locations if defect.confidence == "HIGH" and defect.layer not in {"CONFIGURATION"}]
        if unresolved_repairs:
            blockers.append("Unresolved repair plans remain.")
        if failed_targeted:
            blockers.append("Targeted verification failed.")
        if failed_regressions:
            blockers.append("Regression verification failed.")
        if blocker_defects:
            blockers.append("Unresolved blocker defects remain.")

        contract_status = "PASS"
        blocking_contracts = [issue for issue in state.contract_issues if issue.severity in {"ERROR", "BLOCKER"}]
        if blocking_contracts:
            contract_status = "FAIL"
            blockers.append("Blocking full-stack contract issues remain.")
        elif state.full_stack_contract:
            contract_status = state.full_stack_contract.status
        else:
            contract_status = "NOT_CONFIGURED"
            warnings.append("Full-stack contract evidence is not configured.")

        runtime_failures = [result for result in state.runtime_contract_results if result.status == "FAIL"]
        runtime_status = "FAIL" if runtime_failures else (state.runtime_status or "NOT_CONFIGURED")
        if runtime_failures:
            blockers.append("Runtime contract validation failed.")

        e2e_failures = [result for result in state.e2e_results if result.status == "FAIL"]
        e2e_status = "FAIL" if e2e_failures else ("PASS" if state.e2e_results else "NOT_CONFIGURED")
        if e2e_failures:
            blockers.append("E2E validation failed.")

        if secret_findings:
            blockers.append("SECRET_DETECTED in generated project files.")

        if not project_dir.exists():
            blockers.append(f"Generated project directory not found: {project_dir}")

        documentation_status = "PASS" if (project_dir / "README.md").exists() else "PENDING"
        if documentation_status == "PENDING":
            warnings.append("README will be generated during delivery packaging.")

        artifact_status = "PASS" if state.deployment_profile and state.deployment_profile.target != "NOT_CONFIGURED" else "NOT_CONFIGURED"
        build_status = "NOT_CONFIGURED"
        if state.deployment_profile and state.deployment_profile.dockerfile:
            build_status = "PENDING"
        elif state.frontend_execution.get("build_status"):
            build_status = state.frontend_execution.get("build_status")

        status = "READY"
        if blockers:
            status = "BLOCKED"
        elif warnings:
            status = "NEEDS_REVIEW"

        return ReleaseReadiness(
            status=status,
            blockers=blockers,
            warnings=warnings,
            qa_status=qa_status,
            unresolved_defects=len(blocker_defects),
            contract_status=contract_status,
            runtime_status=runtime_status,
            e2e_status=e2e_status,
            build_status=build_status,
            artifact_status=artifact_status,
            security_status="FAIL" if secret_findings else "PASS",
            documentation_status=documentation_status,
        )

    def _record_deployment_package(self, state: ProjectState, result: DeliveryResult, manifest_files: List[Dict[str, Any]], excluded_files: List[str]) -> None:
        profile = state.deployment_profile or DeploymentProfile()
        artifacts = [
            DeploymentArtifact(project=state.project_id, artifact_type="release_manifest", path="delivery/delivery_manifest.json", status="VALID"),
        ]
        if profile.dockerfile:
            artifacts.append(DeploymentArtifact(project=state.project_id, artifact_type="Dockerfile", path=profile.dockerfile, status="VALID"))
        if profile.compose_file:
            artifacts.append(DeploymentArtifact(project=state.project_id, artifact_type="docker_compose", path=profile.compose_file, status="VALID"))
        for path in profile.kubernetes_manifests:
            artifacts.append(DeploymentArtifact(project=state.project_id, artifact_type="kubernetes_manifest", path=path, status="VALID"))
        state.deployment_artifacts = artifacts

        if state.deployment_result:
            state.deployment_result.manifest_path = result.manifest_path
            state.deployment_result.artifact_list = artifacts
            state.deployment_result.build_information.update({
                "files_included": len(manifest_files),
                "files_excluded": len(excluded_files),
            })

    def _run_post_deployment_verification(self, state: ProjectState) -> None:
        event_bus.emit_sync("POST_DEPLOYMENT_VERIFICATION_STARTED", {
            "project_id": state.project_id,
            "agent": "DeliveryAgent",
            "summary": "Checking available runtime and validation evidence.",
        })
        verification = PostDeploymentVerification()
        if state.runtime_base_url:
            verification.application_health = "PASS" if state.runtime_status in {"RUNNING", "READY", "PASS"} else state.runtime_status
            verification.api_health = "PASS" if not any(item.status == "FAIL" for item in state.runtime_contract_results) else "FAIL"
            verification.contract_verification = "PASS" if verification.api_health == "PASS" else "FAIL"
            verification.e2e_smoke = "PASS" if state.e2e_results and not any(item.status == "FAIL" for item in state.e2e_results) else "NOT_CONFIGURED"
            verification.status = "FAIL" if "FAIL" in {verification.application_health, verification.api_health, verification.contract_verification} else "PASS"
            verification.evidence.append(f"Runtime URL: {state.runtime_base_url}")
        else:
            verification.status = "NOT_CONFIGURED"
            verification.errors.append("No reachable deployment/runtime is configured.")
        state.post_deployment_verification = verification
        event_bus.emit_sync("POST_DEPLOYMENT_VERIFICATION_COMPLETED", {
            "project_id": state.project_id,
            "agent": "DeliveryAgent",
            "status": verification.status,
            "summary": f"Post-deployment verification: {verification.status}",
        })

    def _build_rollback_info(self, state: ProjectState) -> RollbackInfo:
        git = self._git_metadata(Path("generated_projects") / state.project_name)
        current_commit = git.get("current_commit")
        return RollbackInfo(
            rollback_status="AVAILABLE" if current_commit else "NOT_CONFIGURED",
            current_version=current_commit,
            git_commit=current_commit,
            rollback_available=bool(current_commit),
            deployment_artifact="delivery/project_package.zip" if current_commit else None,
        )

    def _detect_application_type(self, state: ProjectState, project_dir: Path) -> str:
        stack = " ".join(state.project_plan.system_design.technology_stack if state.project_plan and state.project_plan.system_design else []).lower()
        if "react" in stack and "fastapi" in stack:
            return "full_stack_web"
        if "react" in stack:
            return "frontend"
        if "fastapi" in stack or "flask" in stack:
            return "backend"
        if project_dir.exists() and any((project_dir / name).exists() for name in ["package.json", "backend", "frontend"]):
            return "web_application"
        return "UNKNOWN"

    def _detect_frontend_deployment(self, state: ProjectState, project_dir: Path) -> Dict[str, Any]:
        frontend = dict(state.frontend_capabilities or {})
        package_candidates = [project_dir / "package.json", project_dir / "frontend" / "package.json"]
        for package_path in package_candidates:
            if package_path.exists():
                try:
                    package = json.loads(package_path.read_text(encoding="utf-8"))
                    scripts = package.get("scripts", {})
                    frontend["package_json"] = str(package_path.relative_to(project_dir)).replace("\\", "/")
                    if "build" in scripts:
                        frontend["build_command"] = "npm run build"
                    deps = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
                    if "vite" in deps:
                        frontend["framework"] = frontend.get("framework") or "Vite"
                        if (package_path.parent / "dist").exists():
                            frontend["artifact_directory"] = str((package_path.parent / "dist").relative_to(project_dir)).replace("\\", "/")
                    if "next" in deps:
                        frontend["framework"] = frontend.get("framework") or "Next"
                        if (package_path.parent / ".next").exists():
                            frontend["artifact_directory"] = str((package_path.parent / ".next").relative_to(project_dir)).replace("\\", "/")
                except (OSError, json.JSONDecodeError):
                    frontend["package_json_status"] = "UNREADABLE"
        return frontend

    def _detect_backend_deployment(self, project_dir: Path) -> Dict[str, Any]:
        backend: Dict[str, Any] = {}
        candidates = list(project_dir.rglob("main.py")) + list(project_dir.rglob("app.py"))
        for path in candidates:
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            rel = str(path.relative_to(project_dir)).replace("\\", "/")
            if "FastAPI(" in content:
                backend.update({"framework": "FastAPI", "entry_point": rel, "start_command": f"uvicorn {rel[:-3].replace('/', '.')}:app --host 0.0.0.0 --port 8000", "health_endpoint": "/health"})
                break
            if "Flask(" in content:
                backend.update({"framework": "Flask", "entry_point": rel, "start_command": f"python {rel}", "health_endpoint": "/health"})
                break
        return backend

    def _detect_environment_requirements(self, project_dir: Path) -> List[EnvironmentVariableRequirement]:
        if not project_dir.exists():
            return []
        found: Dict[str, EnvironmentVariableRequirement] = {}
        pattern = re.compile(r"(?:os\.getenv|os\.environ\.get|process\.env)\(['\"]([A-Z][A-Z0-9_]{2,})['\"]")
        env_file_names = {".env.example", ".env.template", "env.example"}
        for path in project_dir.rglob("*"):
            if not path.is_file() or "node_modules" in path.parts or ".git" in path.parts:
                continue
            rel = str(path.relative_to(project_dir)).replace("\\", "/")
            if path.name in env_file_names:
                for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
                    name = line.split("=", 1)[0].strip()
                    if name and re.fullmatch(r"[A-Z][A-Z0-9_]{2,}", name):
                        found[name] = EnvironmentVariableRequirement(name=name, secret=self._env_name_is_secret(name), source=rel)
            elif path.suffix.lower() in {".py", ".js", ".ts", ".tsx", ".jsx"}:
                content = path.read_text(encoding="utf-8", errors="ignore")
                for name in pattern.findall(content):
                    found[name] = EnvironmentVariableRequirement(name=name, secret=self._env_name_is_secret(name), source=rel)
        return sorted(found.values(), key=lambda item: item.name)

    def _detect_exposed_ports(self, project_dir: Path, dockerfile: Optional[str]) -> List[int]:
        ports = set()
        if dockerfile:
            docker_path = project_dir / dockerfile
            if docker_path.exists():
                for match in re.findall(r"(?im)^\s*EXPOSE\s+([0-9]+)", docker_path.read_text(encoding="utf-8", errors="ignore")):
                    ports.add(int(match))
        return sorted(ports)

    def _scan_project_secrets(self, project_dir: Path) -> List[SecretFinding]:
        if not project_dir.exists():
            return []
        patterns: List[Tuple[str, re.Pattern[str]]] = [
            ("api_key", re.compile(r"(?i)\b(api[_-]?key)\s*[:=]\s*['\"]?(?!\$\{)[A-Za-z0-9_\-]{16,}")),
            ("token", re.compile(r"(?i)\b(token|github[_-]?token)\s*[:=]\s*['\"]?(?!\$\{)[A-Za-z0-9_\-]{20,}")),
            ("password", re.compile(r"(?i)\b(password)\s*[:=]\s*['\"](?!\$\{)[^'\"]{8,}['\"]")),
            ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
            ("connection_string", re.compile(r"(?i)(postgres|mysql|mongodb|redis)://[^\\s'\"<>]+:[^\\s'\"<>]+@")),
        ]
        findings: List[SecretFinding] = []
        for path in project_dir.rglob("*"):
            if not path.is_file() or "node_modules" in path.parts or ".git" in path.parts or path.name == ".env":
                continue
            rel = str(path.relative_to(project_dir)).replace("\\", "/")
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeDecodeError):
                continue
            for line_no, line in enumerate(lines, start=1):
                if "${" in line:
                    continue
                for category, pattern in patterns:
                    if pattern.search(line):
                        findings.append(SecretFinding(file=rel, line=line_no, category=category))
        return findings

    def _qa_passed(self, state: ProjectState) -> bool:
        if not state.project_plan:
            return False
        for task in state.project_plan.tasks:
            task_obj = state.tasks.get(task.task_id)
            if not task_obj or task_obj.status != "completed":
                return False
            qa_res = task_obj.result.get("qa_result", {})
            if not qa_res or not qa_res.get("passed"):
                return False
        return True

    def _git_metadata(self, project_dir: Path) -> Dict[str, Any]:
        if not project_dir.exists():
            return {"available": False, "reason": "project directory missing"}
        metadata: Dict[str, Any] = {"available": False}
        commands = {
            "current_branch": ["git", "branch", "--show-current"],
            "current_commit": ["git", "rev-parse", "HEAD"],
            "changed_files": ["git", "status", "--short"],
        }
        for key, command in commands.items():
            try:
                proc = subprocess.run(command, cwd=project_dir, capture_output=True, text=True, timeout=5)
            except (OSError, subprocess.TimeoutExpired):
                continue
            if proc.returncode == 0:
                metadata["available"] = True
                value = proc.stdout.strip()
                metadata[key] = value.splitlines() if key == "changed_files" else value
        metadata["dirty"] = bool(metadata.get("changed_files"))
        return metadata

    def _first_existing(self, project_dir: Path, names: List[str]) -> Optional[str]:
        for name in names:
            path = project_dir / name
            if path.exists():
                return name
        return None

    def _env_name_is_secret(self, name: str) -> bool:
        return any(token in name.upper() for token in ["SECRET", "TOKEN", "KEY", "PASSWORD", "DATABASE_URL"])
        
    def _finalize(self, state: ProjectState, result: DeliveryResult) -> ProjectState:
        if not hasattr(state, 'delivery_result'):
            setattr(state, 'delivery_result', None)
        state.delivery_result = result.model_dump()
        self._write_delivery_artifacts(state, result)
        try:
            from backend.evaluation import EvaluationEngine
            EvaluationEngine().evaluate(state, scenario_id=getattr(state, "domain", None) or state.project_id)
        except Exception as exc:
            state.errors.append(f"Evaluation warning: {exc}")
        
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
        release_readiness = state.release_readiness.model_dump() if state.release_readiness else {}
        deployment_profile = state.deployment_profile.model_dump() if state.deployment_profile else {}
        deployment_result = state.deployment_result.model_dump() if state.deployment_result else {}
        post_deployment = state.post_deployment_verification.model_dump() if state.post_deployment_verification else {}
        rollback = state.rollback_info.model_dump() if state.rollback_info else {}
        write_text_artifact(state, "delivery/README.md", f"""# Delivery Summary

## Delivery Status
{result.status}

## Release Readiness
{release_readiness.get('status', 'NOT_AVAILABLE')}

## Project Summary
{state.project_plan.project_overview}

## QA Result
{'PASS' if result.qa_verified else 'NOT VERIFIED'}

## Package
{result.package_path or 'NOT_AVAILABLE'}

## Deployment Target
{deployment_profile.get('target', 'NOT_CONFIGURED')}

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
        write_text_artifact(state, "delivery/release_readiness.json", json.dumps(release_readiness, indent=2), "DELIVERY", "DeliveryAgent")
        write_text_artifact(state, "delivery/deployment_profile.json", json.dumps(deployment_profile, indent=2), "DELIVERY", "DeliveryAgent")
        write_text_artifact(state, "delivery/deployment_result.json", json.dumps(deployment_result, indent=2), "DELIVERY", "DeliveryAgent")
        write_text_artifact(state, "delivery/post_deployment_verification.json", json.dumps(post_deployment, indent=2), "DELIVERY", "DeliveryAgent")
        write_text_artifact(state, "delivery/rollback_info.json", json.dumps(rollback, indent=2), "DELIVERY", "DeliveryAgent")
        write_text_artifact(state, "delivery/release_readiness.md", f"""# Release Readiness

## Status
{release_readiness.get('status', 'NOT_AVAILABLE')}

## Gates
- QA: {release_readiness.get('qa_status', 'NOT_AVAILABLE')}
- Contracts: {release_readiness.get('contract_status', 'NOT_AVAILABLE')}
- Runtime: {release_readiness.get('runtime_status', 'NOT_AVAILABLE')}
- E2E: {release_readiness.get('e2e_status', 'NOT_AVAILABLE')}
- Build: {release_readiness.get('build_status', 'NOT_AVAILABLE')}
- Artifacts: {release_readiness.get('artifact_status', 'NOT_AVAILABLE')}
- Security: {release_readiness.get('security_status', 'NOT_AVAILABLE')}
- Documentation: {release_readiness.get('documentation_status', 'NOT_AVAILABLE')}

## Blockers
{chr(10).join(f'- {item}' for item in release_readiness.get('blockers', [])) if release_readiness.get('blockers') else 'None'}

## Warnings
{chr(10).join(f'- {item}' for item in release_readiness.get('warnings', [])) if release_readiness.get('warnings') else 'None'}
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

## Deployment Target
{deployment_profile.get('target', 'NOT_CONFIGURED')}

## Post-Deployment Verification
{post_deployment.get('status', 'NOT_CONFIGURED')}

## Rollback
{rollback.get('rollback_status', 'NOT_CONFIGURED')}
""", "DELIVERY", "DeliveryAgent")
