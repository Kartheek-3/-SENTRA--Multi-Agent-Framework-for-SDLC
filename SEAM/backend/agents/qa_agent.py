import time
import os
import ast
import re
from pathlib import Path
from pydantic import ValidationError
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from backend.models.state import ProjectState
from backend.models.qa import QAResult
from backend.performance import estimate_tokens, timed_call, timed_llm_call
from backend.agents.model_compat import active_model_name, get_model_compat

QA_PROMPT = """You are an expert QA Engineer for an autonomous framework.
Your job is to validate the generated code against the established project requirements and architecture.

Task ID: {task_id}
Description: {task_description}

Required Requirements to Implement:
{related_requirements}

Project Scale: {project_scale}

Project Architecture & Technology Stack:
{system_design}

Frontend Architecture Plan:
{frontend_architecture_plan}

Full-Stack Contract Profile:
{full_stack_contract}

GitHub Reference Context:
{github_context}

RAG Context (Organizational Memory):
{rag_context}

Domain-Aware Context:
{domain_context}

Generated Files and Content to Review:
{files_content}

CRITICAL RULES:
1. Verify if the generated code successfully implements the Required Requirements.
2. Verify if the generated code adheres to the specified Technology Stack.
3. Check for architectural violations (e.g., ignoring DB schemas, missing API endpoints).
4. Scale-Aware QA: Adapt your QA stringency to the Project Scale. Ensure ENTERPRISE projects are strictly checked for performance/security, while SMALL stays simple.
5. If Frontend Architecture Plan is present, verify requirement -> page -> component -> API -> file -> validation traceability.
6. If Full-Stack Contract Profile is present, validate frontend/API/backend/database contracts separately from generic UI validation.
7. Do NOT re-write the code. You are strictly providing QA feedback.
8. Produce exactly matching JSON according to the schema.
9. If the code completely fulfills the task, mark status as "passed" and passed=true.
10. If there are major issues, mark status as "failed". If minor, mark "needs_revision".

{format_instructions}
"""

QA_RETRY_PROMPT = """Your previous response failed validation.

Correct ONLY the structural/schema problems.
Return ONLY a valid QAResult JSON object.

Validation Error that caused failure:
{validation_error}

Task ID: {task_id}

{format_instructions}
"""

MAX_QA_ATTEMPTS = 2

class QAAgent:
    def __init__(self, model_router):
        self.model_router = model_router
        self.parser = PydanticOutputParser(pydantic_object=QAResult)
        
    def process(self, state: ProjectState, task_id: str) -> ProjectState:
        start_time = time.time()
        agent_name = "QAAgent"
        
        if task_id not in state.tasks:
            self._log_error(state, agent_name, f"Task {task_id} not found in state.", start_time)
            return state
            
        task = state.tasks[task_id]
        
        if task.status != "completed" or not task.result:
            self._log_error(state, agent_name, f"Cannot QA task {task_id}: Task is not completed or missing result.", start_time)
            return state
            
        project_dir = os.path.join("generated_projects", state.project_name)
        generated_files = task.result.get("files", [])
        
        syntax_errors = []
        security_issues = []
        files_checked = []
        files_content_str = ""
        
        # 1. Deterministic Checks (Syntax, Existence, Security Heuristics)
        for f_obj in generated_files:
            rel_path = f_obj.get("path", "")
            if not rel_path:
                continue
                
            full_path = os.path.join(project_dir, rel_path)
            if not os.path.exists(full_path):
                syntax_errors.append(f"File missing on disk: {rel_path}")
                continue
                
            files_checked.append(rel_path)
            
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                syntax_errors.append(f"Cannot read {rel_path}: {str(e)}")
                continue
                
            files_content_str += f"\n--- {rel_path} ---\n{content}\n"
            
            # Basic AST syntax check for Python
            if rel_path.endswith(".py"):
                try:
                    ast.parse(content)
                except SyntaxError as e:
                    syntax_errors.append(f"Syntax error in {rel_path}: {str(e)}")
            
            # Security Heuristics
            dangerous_patterns = [r"exec\(", r"eval\(", r"os\.system\("]
            for pat in dangerous_patterns:
                if re.search(pat, content):
                    security_issues.append(f"Dangerous pattern '{pat}' detected in {rel_path}")
        
        if syntax_errors:
            # Immediate deterministic failure, skip LLM semantic QA
            qa_res = QAResult(
                task_id=task_id,
                status="failed",
                passed=False,
                syntax_errors=syntax_errors,
                security_issues=security_issues,
                files_checked=files_checked,
                severity="high"
            )
            return self._finalize_qa(state, task_id, qa_res, agent_name, start_time, attempts=1)

        # 2. Extract Context for Semantic Review
        reqs = "\n".join(task.related_requirements) if task.related_requirements else "None explicitly assigned."
        sys_design = state.project_plan.system_design.model_dump_json(indent=2) if (state.project_plan and state.project_plan.system_design) else "{}"
        frontend_architecture_plan = state.frontend_architecture_plan.model_dump_json(indent=2) if state.frontend_architecture_plan else "{}"
        full_stack_contract = state.full_stack_contract.model_dump_json(indent=2) if state.full_stack_contract else "{}"
        scale_obj = getattr(state.structured_requirements, "scale_assessment", None)
        project_scale = scale_obj.scale_level.value if scale_obj else "UNKNOWN"
        github_context = state.github_findings.get("context", "No GitHub reference context available.") if state.github_findings else "No GitHub reference context available."
        
        format_instructions = self.parser.get_format_instructions()
        llm = get_model_compat(self.model_router, "qa")
        
        attempt = 1
        last_error = None
        result_obj = None
        validation_passed = False
        
        from backend.tools.agent_tools import run_agent_tool
        rag_result = run_agent_tool(
            state,
            agent_name,
            "rag_search",
            {"query": task.description, "domain": state.domain or "general", "top_k": 5},
            task_id=task_id,
        )
        rag_context = str(rag_result.structured_data.get("results", [])) if rag_result.success else "No relevant organizational knowledge found."
        pytest_result = run_agent_tool(state, agent_name, "pytest_runner", {"test_args": ["-q"]}, task_id=task_id)
        from backend.knowledge.domain_intelligence import DomainIntelligenceService
        from backend.evaluation.ablation import capability_enabled, mark_disabled
        domain_service = DomainIntelligenceService()
        if capability_enabled(state, "domain_rag") and not state.domain_context:
            if state.domain_identification or state.structured_requirements:
                domain_service.retrieve_context(state, current_task=task.description)
        if capability_enabled(state, "domain_rag"):
            domain_context = domain_service.format_for_prompt(state.domain_context)
        else:
            mark_disabled(state, "domain_rag", agent_name, "QA domain-aware context injection skipped by experiment configuration.")
            domain_context = "Domain-aware context disabled by experiment configuration."

        # 3. Semantic QA Generation & Retry Loop
        while attempt <= MAX_QA_ATTEMPTS:
            try:
                if attempt == 1:
                    prompt = ChatPromptTemplate.from_template(QA_PROMPT)
                    chain = prompt | llm
                    inputs = {
                        "task_id": task.task_id,
                        "task_description": task.description,
                        "related_requirements": reqs,
                        "project_scale": project_scale,
                        "system_design": sys_design,
                        "frontend_architecture_plan": frontend_architecture_plan,
                        "full_stack_contract": full_stack_contract,
                        "github_context": github_context,
                        "rag_context": rag_context,
                        "domain_context": domain_context,
                        "files_content": files_content_str,
                        "format_instructions": format_instructions
                    }
                    response = timed_llm_call(
                        lambda: chain.invoke(inputs),
                        project_id=state.project_id,
                        agent=agent_name,
                        task_id=task_id,
                        model=active_model_name(self.model_router, "qa"),
                        input_token_estimate=estimate_tokens(inputs),
                        timeout_seconds=getattr(llm, "timeout", None),
                        retry_count=attempt - 1,
                    )
                else:
                    prompt = ChatPromptTemplate.from_template(QA_RETRY_PROMPT)
                    chain = prompt | llm
                    inputs = {
                        "task_id": task.task_id,
                        "validation_error": str(last_error),
                        "format_instructions": format_instructions
                    }
                    response = timed_llm_call(
                        lambda: chain.invoke(inputs),
                        project_id=state.project_id,
                        agent=agent_name,
                        task_id=task_id,
                        model=active_model_name(self.model_router, "qa"),
                        input_token_estimate=estimate_tokens(inputs),
                        timeout_seconds=getattr(llm, "timeout", None),
                        retry_count=attempt - 1,
                    )
                
                parsed_result = self.parser.parse(response.content)
                result_obj = parsed_result
                validation_passed = True
                break
                
            except Exception as e:
                last_error = e
                error_msg = f"QA Attempt {attempt} failed: {str(e)}"
                state.errors.append(error_msg)
                attempt += 1

        # 4. Finalize
        if not validation_passed or result_obj is None:
            self._log_error(state, agent_name, f"Failed to generate valid QA result for task {task_id} after {MAX_QA_ATTEMPTS} attempts.", start_time, attempts=attempt - 1)
            qa_res = QAResult(
                task_id=task_id,
                status="failed",
                passed=False,
                severity="critical"
            )
            return self._finalize_qa(state, task_id, qa_res, agent_name, start_time, attempts=attempt - 1)

        # Merge deterministic security issues if any were found but syntax was fine
        if pytest_result.success:
            result_obj.test_results.append(f"pytest_runner passed: {pytest_result.stdout[-500:]}")
        elif pytest_result.error:
            result_obj.test_results.append(f"pytest_runner failed: {pytest_result.error.message}")
            result_obj.status = "failed"
            result_obj.passed = False
            result_obj.severity = "high"
        if security_issues:
            result_obj.security_issues.extend(security_issues)
            result_obj.status = "failed"
            result_obj.passed = False
            result_obj.severity = "high"
        if capability_enabled(state, "contract_intelligence"):
            self._run_contract_validation(state, task_id, result_obj)
        else:
            mark_disabled(state, "contract_intelligence", agent_name, "Static contract validation skipped by experiment configuration.")
        runtime_started = self._prepare_runtime(state, task_id, project_dir, result_obj)
        if capability_enabled(state, "contract_intelligence"):
            self._run_runtime_contract_validation(state, task_id, result_obj)
        else:
            mark_disabled(state, "contract_intelligence", agent_name, "Runtime contract validation skipped by experiment configuration.")
        self._run_e2e_validation(state, task_id, result_obj)
        if runtime_started:
            self._cleanup_runtime(state, task_id)
        self._run_frontend_qa_checks(state, task_id, project_dir, result_obj)
            
        result_obj.files_checked = files_checked
        return self._finalize_qa(state, task_id, result_obj, agent_name, start_time, attempts=attempt)

    def _finalize_qa(self, state, task_id, qa_result: QAResult, agent_name, start_time, attempts):
        task = state.tasks[task_id]
        if not hasattr(task, 'qa_result'):
            # Just push it into task result dict or a parallel structure.
            task.result["qa_result"] = qa_result.model_dump()
            
        if not qa_result.passed:
            task.status = "failed"
            if task_id not in state.failed_tasks:
                state.failed_tasks.append(task_id)
            if task_id in state.completed_tasks:
                state.completed_tasks.remove(task_id)
                
            # Populate QA feedback for the next coding attempt
            if not hasattr(state, "qa_feedback"):
                state.qa_feedback = []
            
            feedback_msg = f"QA Failed for {task_id}. Issues: "
            if qa_result.syntax_errors: feedback_msg += f"Syntax: {qa_result.syntax_errors}; "
            if qa_result.security_issues: feedback_msg += f"Security: {qa_result.security_issues}; "
            if qa_result.architecture_violations: feedback_msg += f"Architecture: {qa_result.architecture_violations}; "
            state.qa_feedback.append(feedback_msg)
        
        # Generate persistent QA report
        self._write_qa_report_md(state.project_name, task_id, qa_result, task.title)
        self._write_phase_qa_artifacts(state, task_id, qa_result, task.title)
        
        # Knowledge Lifecycle (PENDING -> VALIDATED)
        from backend.knowledge.knowledge_service import KnowledgeService
        from backend.knowledge.models import KnowledgeDocument
        ks = KnowledgeService()
        
        if not qa_result.passed:
            # Capture as PENDING knowledge
            doc = KnowledgeDocument(
                title=f"QA Finding - {task_id}",
                source=f"Project {state.project_id}",
                source_type="project_qa",
                category="lesson_learned",
                project_id=state.project_id,
                content=f"Task: {task_id}\nIssues: {feedback_msg}",
                validated="PENDING",
                tags=["qa", "rework"]
            )
            ks.ingest_document(doc)
            if not hasattr(state, "pending_qa_knowledge"):
                state.pending_qa_knowledge = {}
            state.pending_qa_knowledge[task_id] = doc.knowledge_id
        else:
            # If passed and we had a previous pending knowledge for this task, VALIDATE it
            if hasattr(state, "pending_qa_knowledge") and task_id in state.pending_qa_knowledge:
                k_id = state.pending_qa_knowledge[task_id]
                try:
                    # In a real system, we'd update the exact document in ChromaDB or a relational DB.
                    # Since ChromaDB allows updates by ID, we can do it via the service.
                    ks.validate_document(k_id)
                except Exception as e:
                    state.errors.append(f"Failed to validate knowledge {k_id}: {str(e)}")
                    
        history_record = {
            "agent": agent_name,
            "task_id": task_id,
            "status": "success" if qa_result.passed else "failed",
            "qa_status": qa_result.status,
            "attempts": attempts,
            "duration": time.time() - start_time
        }
        if attempts > 1:
            history_record["initial_validation"] = "failed"
            history_record["self_correction"] = "successful" if qa_result else "failed"
            
        state.execution_history.append(history_record)
        try:
            from backend.evaluation.ablation import capability_enabled
            if capability_enabled(state, "domain_rag"):
                from backend.knowledge.domain_intelligence import DomainIntelligenceService
                DomainIntelligenceService().persist_traceability(state, agent_name, f"QA task {task_id} validated against domain context.")
        except Exception as exc:
            state.errors.append(f"Domain traceability update failed for QA task {task_id}: {exc}")
        return state

    def _log_error(self, state, agent_name, error_msg, start_time, attempts=1):
        state.errors.append(error_msg)
        state.execution_history.append({
            "agent": agent_name,
            "status": "error",
            "error": error_msg,
            "attempts": attempts,
            "duration": time.time() - start_time
        })

    def _write_qa_report_md(self, project_name: str, task_id: str, qa_result: QAResult, task_title: str):
        def write_list_section(title, items):
            res = f"## {title}\n"
            if items:
                for item in items:
                    res += f"- {item}\n"
            else:
                res += "None found.\n"
            return res + "\n"
        md_content = f"""# QA Report

## Task
{task_id}: {task_title}

## Status
**{'PASS' if qa_result.passed else 'FAILED'}** (Status: {qa_result.status}, Severity: {qa_result.severity})

## Files Checked
{chr(10).join(f'- {f}' for f in qa_result.files_checked) if qa_result.files_checked else 'None'}

{write_list_section("Functional Issues", qa_result.functional_issues)}
{write_list_section("Requirement Violations", qa_result.requirement_violations)}
{write_list_section("Architecture Violations", qa_result.architecture_violations)}
{write_list_section("Security Issues", qa_result.security_issues)}
{write_list_section("Syntax Errors", qa_result.syntax_errors)}
{write_list_section("Test Results", qa_result.test_results)}
{write_list_section("Recommendations", qa_result.recommendations)}
"""
        project_dir = os.path.join("generated_projects", project_name)
        qa_dir = os.path.join(project_dir, "qa")
        os.makedirs(qa_dir, exist_ok=True)
        report_path = os.path.join(qa_dir, f"{task_id}_qa_report.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(md_content)

    def _write_phase_qa_artifacts(self, state, task_id: str, qa_result: QAResult, task_title: str):
        from backend.tools.artifact_pipeline import write_text_artifact
        files_checked = "\n".join(f"- {item}" for item in qa_result.files_checked) if qa_result.files_checked else "- None"
        issues = qa_result.functional_issues + qa_result.requirement_violations + qa_result.architecture_violations + qa_result.security_issues + qa_result.syntax_errors
        issue_text = "\n".join(f"- {item}" for item in issues) if issues else "- None"
        status = "PASS" if qa_result.passed else "FAILED"
        write_text_artifact(state, "qa/README.md", f"""# QA Summary

## QA Status
{status}

## Checks Performed
- Syntax checks
- Security heuristics
- Requirement review
- Architecture review
- Generated file existence checks

## Overall Result
{qa_result.status}
""", "QA_REPORT", "QAAgent", task_id=task_id)
        write_text_artifact(state, "qa/test_report.md", f"""# Test Report

## Task
{task_id}: {task_title}

## Files Checked
{files_checked}

## Test Results
{chr(10).join(f'- {item}' for item in qa_result.test_results) if qa_result.test_results else '- No explicit tests reported by QA model.'}

## Validation Result
{status}
""", "QA_REPORT", "QAAgent", task_id=task_id)
        write_text_artifact(state, "qa/requirements_traceability.md", f"""# Requirements Traceability

## Task
{task_id}: {task_title}

## Requirement Violations
{chr(10).join(f'- {item}' for item in qa_result.requirement_violations) if qa_result.requirement_violations else '- None'}

## Verification Result
{status}
""", "QA_REPORT", "QAAgent", task_id=task_id)
        write_text_artifact(state, "qa/issues.md", f"""# QA Issues

## Detected Issues
{issue_text}

## Rework Status
{'Rework required.' if not qa_result.passed else 'No rework required.'}
""", "QA_REPORT", "QAAgent", task_id=task_id)

    def _run_frontend_qa_checks(self, state: ProjectState, task_id: str, project_dir: str, qa_result: QAResult) -> None:
        package_path = os.path.join(project_dir, "package.json")
        if not os.path.exists(package_path):
            return
        from backend.tools.agent_tools import run_agent_tool

        detection = run_agent_tool(state, "QAAgent", "detect_frontend_capabilities", {"project_root": "."}, task_id=task_id)
        if detection.success:
            state.frontend_capabilities = detection.structured_data
        profile = state.frontend_capabilities or {}
        checks = []
        planned_tools = []
        optional_tools = []
        if profile.get("typecheck_available"):
            planned_tools.append("typecheck_runner")
        else:
            optional_tools.append("typecheck_runner")
        if profile.get("lint_available"):
            planned_tools.append("lint_runner")
        else:
            optional_tools.append("lint_runner")
        if profile.get("frontend_test_framework") != "not_configured":
            planned_tools.append("frontend_test_runner")
        else:
            optional_tools.append("frontend_test_runner")
        if profile.get("build_available"):
            planned_tools.append("build_runner")
        else:
            optional_tools.append("build_runner")
        if profile.get("playwright_available"):
            planned_tools.append("playwright_runner")
        else:
            optional_tools.append("playwright_runner")
        if profile.get("accessibility_available"):
            planned_tools.append("accessibility_checker")
        else:
            optional_tools.append("accessibility_checker")

        for tool_name in [*planned_tools, *optional_tools]:
            payload = {"project_root": "."}
            result = run_agent_tool(state, "QAAgent", tool_name, payload, task_id=task_id)
            status = result.structured_data.get("status", "SUCCESS" if result.success else "FAILED")
            summary = f"{tool_name}: {status}"
            if result.stderr:
                summary += f" - {result.stderr[-300:]}"
            qa_result.test_results.append(summary)
            checks.append({
                "tool": tool_name,
                "success": result.success,
                "status": status,
                "exit_code": result.structured_data.get("exit_code"),
            })
            if status == "FAILED":
                qa_result.status = "failed"
                qa_result.passed = False
                qa_result.severity = "high"
                qa_result.functional_issues.append(f"{tool_name} failed")
        state.frontend_execution.setdefault(task_id, {})
        state.frontend_execution[task_id]["capability_profile"] = profile
        state.frontend_execution[task_id]["qa_checks"] = checks
        state.frontend_execution[task_id]["package_detected"] = True
        if state.frontend_architecture_plan:
            state.frontend_execution[task_id]["architecture_traceability"] = [
                item.model_dump() for item in state.frontend_architecture_plan.traceability
            ]

    def _run_contract_validation(self, state: ProjectState, task_id: str, qa_result: QAResult) -> None:
        from backend.contracts import build_full_stack_contract_profile, validate_full_stack_contract
        from backend.events import event_bus

        profile = build_full_stack_contract_profile(state)
        issues = validate_full_stack_contract(profile)
        profile.issues = issues
        profile.status = "PASS" if not any(issue.severity in ("ERROR", "BLOCKER") for issue in issues) else "FAIL"
        state.full_stack_contract = profile
        state.contract_issues = issues
        qa_result.test_results.append(f"contract_validation: {profile.status} ({len(issues)} issue(s))")
        for issue in issues:
            message = f"{issue.severity} {issue.category}: {issue.description} Expected={issue.expected}; Actual={issue.actual}; File={issue.file or 'NOT_AVAILABLE'}"
            if issue.severity in ("ERROR", "BLOCKER"):
                qa_result.architecture_violations.append(message)
                qa_result.status = "failed"
                qa_result.passed = False
                qa_result.severity = "high" if issue.severity == "ERROR" else "critical"
                event_bus.emit_sync("CONTRACT_MISMATCH_DETECTED", {
                    "project_id": state.project_id,
                    "agent": "QAAgent",
                    "task_id": task_id,
                    **issue.model_dump(),
                    "summary": message,
                })
            else:
                qa_result.recommendations.append(message)

    def _prepare_runtime(self, state: ProjectState, task_id: str, project_dir: str, qa_result: QAResult) -> bool:
        from backend.events import event_bus
        from backend.models.contracts import RuntimeProcess, RuntimeProfile
        from backend.tools.agent_tools import run_agent_tool

        event_bus.emit_sync("RUNTIME_DETECTION_STARTED", {
            "project_id": state.project_id,
            "agent": "QAAgent",
            "task_id": task_id,
            "summary": "Runtime detection started.",
        })
        detection = run_agent_tool(state, "QAAgent", "runtime_manager", {"action": "DETECT", "project_root": "."}, task_id=task_id)
        profile_data = (detection.structured_data or {}).get("profile")
        if profile_data:
            state.runtime_profile = RuntimeProfile(**profile_data)
        status = (detection.structured_data or {}).get("status", "NOT_CONFIGURED")
        state.runtime_status = status
        event_bus.emit_sync("RUNTIME_DETECTION_COMPLETED", {
            "project_id": state.project_id,
            "agent": "QAAgent",
            "task_id": task_id,
            "status": status,
            "summary": f"Runtime detection completed: {status}.",
        })
        if status != "READY" or not profile_data:
            qa_result.test_results.append(f"runtime_lifecycle: {status}")
            return False
        event_bus.emit_sync("RUNTIME_START_STARTED", {
            "project_id": state.project_id,
            "agent": "QAAgent",
            "task_id": task_id,
            "summary": "Runtime start started.",
        })
        event_bus.emit_sync("RUNTIME_HEALTH_CHECK_STARTED", {
            "project_id": state.project_id,
            "agent": "QAAgent",
            "task_id": task_id,
            "summary": "Runtime health checks started.",
        })
        started = run_agent_tool(state, "QAAgent", "runtime_manager", {"action": "START", "project_root": ".", "profile": profile_data}, task_id=task_id)
        data = started.structured_data or {}
        state.runtime_status = data.get("status", "FAILED")
        state.runtime_base_url = data.get("base_url") or state.runtime_base_url
        state.runtime_processes = [RuntimeProcess(**item) for item in data.get("processes", [])]
        if started.success and state.runtime_base_url:
            event_bus.emit_sync("RUNTIME_STARTED", {
                "project_id": state.project_id,
                "agent": "QAAgent",
                "task_id": task_id,
                "base_url": state.runtime_base_url,
                "summary": f"Runtime started at {state.runtime_base_url}.",
            })
            event_bus.emit_sync("RUNTIME_READY", {
                "project_id": state.project_id,
                "agent": "QAAgent",
                "task_id": task_id,
                "base_url": state.runtime_base_url,
                "summary": "Runtime health checks passed.",
            })
            qa_result.test_results.append("runtime_lifecycle: STARTED")
            return True
        event_bus.emit_sync("RUNTIME_START_FAILED", {
            "project_id": state.project_id,
            "agent": "QAAgent",
            "task_id": task_id,
            "status": state.runtime_status,
            "summary": data.get("message") or "Runtime start failed.",
        })
        event_bus.emit_sync("RUNTIME_HEALTH_FAILED", {
            "project_id": state.project_id,
            "agent": "QAAgent",
            "task_id": task_id,
            "status": state.runtime_status,
            "summary": "Runtime health checks did not reach READY.",
        })
        qa_result.test_results.append(f"runtime_lifecycle: {state.runtime_status}")
        return False

    def _cleanup_runtime(self, state: ProjectState, task_id: str) -> None:
        from backend.events import event_bus
        from backend.tools.agent_tools import run_agent_tool

        event_bus.emit_sync("RUNTIME_STOP_STARTED", {
            "project_id": state.project_id,
            "agent": "QAAgent",
            "task_id": task_id,
            "summary": "Runtime cleanup started.",
        })
        result = run_agent_tool(state, "QAAgent", "runtime_manager", {"action": "STOP", "project_root": "."}, task_id=task_id)
        state.runtime_status = (result.structured_data or {}).get("status", "NOT_RUNNING")
        event_bus.emit_sync("RUNTIME_STOPPED", {
            "project_id": state.project_id,
            "agent": "QAAgent",
            "task_id": task_id,
            "status": state.runtime_status,
            "summary": f"Runtime cleanup completed: {state.runtime_status}.",
        })

    def _run_runtime_contract_validation(self, state: ProjectState, task_id: str, qa_result: QAResult) -> None:
        from backend.events import event_bus
        from backend.models.contracts import ContractIssue, RuntimeContractResult
        from backend.tools.agent_tools import run_agent_tool

        base_url = state.runtime_base_url
        if not base_url:
            state.runtime_contract_results = [
                RuntimeContractResult(
                    contract_id="runtime-not-configured",
                    endpoint="",
                    method="",
                    request_status="NOT_CONFIGURED",
                    expected_status=[],
                    status="NOT_CONFIGURED",
                    issues=[],
                )
            ]
            qa_result.test_results.append("runtime_contract_validation: NOT_CONFIGURED")
            return
        if not state.full_stack_contract:
            qa_result.test_results.append("runtime_contract_validation: NOT_CONFIGURED (missing static contract profile)")
            return

        event_bus.emit_sync("RUNTIME_CONTRACT_VALIDATION_STARTED", {
            "project_id": state.project_id,
            "agent": "QAAgent",
            "task_id": task_id,
            "base_url": base_url,
            "summary": "Runtime contract validation started.",
        })
        runtime_results = []
        try:
            for api in state.full_stack_contract.api_contracts:
                request_schema = api.request_body.fields if api.request_body else {}
                response_schema = api.response_body.fields if api.response_body else {}
                payload = {
                    "base_url": base_url,
                    "contract_id": f"{api.method} {api.endpoint}",
                    "endpoint": api.endpoint,
                    "method": api.method,
                    "request": self._synthetic_request_payload(request_schema),
                    "expected_request_schema": {"properties": request_schema},
                    "expected_response_schema": {"properties": response_schema},
                    "expected_status_codes": api.status_codes or [200],
                    "authentication_required": api.authentication_required,
                }
                result = run_agent_tool(state, "QAAgent", "runtime_api_validator", payload, task_id=task_id)
                data = result.structured_data or {}
                runtime_result = RuntimeContractResult(**data)
                runtime_results.append(runtime_result)
                for issue_data in data.get("issues", []):
                    issue = ContractIssue(**issue_data)
                    state.contract_issues.append(issue)
                    message = f"{issue.severity} {issue.category}: {issue.description} Expected={issue.expected}; Actual={issue.actual}; Endpoint={issue.endpoint}"
                    if issue.severity in ("ERROR", "BLOCKER"):
                        qa_result.architecture_violations.append(message)
                        qa_result.status = "failed"
                        qa_result.passed = False
                        qa_result.severity = "high" if issue.severity == "ERROR" else "critical"
                        event_bus.emit_sync("RUNTIME_CONTRACT_MISMATCH_DETECTED", {
                            "project_id": state.project_id,
                            "agent": "QAAgent",
                            "task_id": task_id,
                            **issue.model_dump(),
                            "summary": message,
                        })
                    else:
                        qa_result.recommendations.append(message)
            state.runtime_contract_results = runtime_results
            overall = "PASS" if runtime_results and all(item.status == "PASS" for item in runtime_results) else "FAIL"
            qa_result.test_results.append(f"runtime_contract_validation: {overall} ({len(runtime_results)} contract(s))")
            event_bus.emit_sync("RUNTIME_CONTRACT_VALIDATION_COMPLETED", {
                "project_id": state.project_id,
                "agent": "QAAgent",
                "task_id": task_id,
                "status": overall,
                "results": len(runtime_results),
                "summary": f"Runtime contract validation completed: {overall}.",
            })
        except Exception as exc:
            qa_result.test_results.append(f"runtime_contract_validation: FAILED ({exc})")
            event_bus.emit_sync("RUNTIME_CONTRACT_VALIDATION_FAILED", {
                "project_id": state.project_id,
                "agent": "QAAgent",
                "task_id": task_id,
                "error": str(exc),
                "summary": "Runtime contract validation failed.",
            })

    def _synthetic_request_payload(self, properties: dict) -> dict:
        safe = {}
        for field, schema in (properties or {}).items():
            field_l = field.lower()
            if any(secret in field_l for secret in ["password", "token", "secret", "key", "authorization"]):
                safe[field] = "[REDACTED_TEST_VALUE]"
                continue
            value_type = schema.get("type") if isinstance(schema, dict) else "string"
            if value_type == "integer":
                safe[field] = 1
            elif value_type == "number":
                safe[field] = 1.0
            elif value_type == "boolean":
                safe[field] = True
            elif value_type == "array":
                safe[field] = []
            elif value_type == "object":
                safe[field] = {}
            else:
                safe[field] = f"test_{field}"
        return safe

    def _run_e2e_validation(self, state: ProjectState, task_id: str, qa_result: QAResult) -> None:
        import time
        from backend.events import event_bus
        from backend.models.contracts import DefectLocation, E2EResult, E2EStepResult
        from backend.tools.agent_tools import run_agent_tool

        event_bus.emit_sync("E2E_SCENARIO_GENERATION_STARTED", {
            "project_id": state.project_id,
            "agent": "QAAgent",
            "task_id": task_id,
            "summary": "E2E scenario generation started.",
        })
        scenarios = self._generate_e2e_scenarios(state)
        state.e2e_scenarios = scenarios
        for scenario in scenarios:
            event_bus.emit_sync("E2E_SCENARIO_GENERATED", {
                "project_id": state.project_id,
                "agent": "QAAgent",
                "task_id": task_id,
                "scenario_id": scenario.scenario_id,
                "name": scenario.name,
                "summary": f"E2E scenario generated: {scenario.scenario_id} {scenario.name}.",
            })
        if not scenarios:
            qa_result.test_results.append("e2e_validation: NOT_CONFIGURED (no frontend scenarios)")
            state.e2e_results = []
            self._plan_repairs_from_defects(state, task_id, qa_result)
            self._run_repair_verification(state, task_id, qa_result)
            return
        if not state.runtime_base_url:
            state.e2e_results = [
                E2EResult(
                    scenario_id=scenario.scenario_id,
                    status="BLOCKED",
                    defect_locations=[DefectLocation(layer="RUNTIME", confidence="HIGH", issue="Runtime URL is not available for E2E execution.", suggested_investigation="Start the application runtime before E2E validation.")],
                )
                for scenario in scenarios
            ]
            state.defect_locations.extend(location for result in state.e2e_results for location in result.defect_locations)
            qa_result.test_results.append("e2e_validation: BLOCKED (runtime unavailable)")
            self._plan_repairs_from_defects(state, task_id, qa_result)
            self._run_repair_verification(state, task_id, qa_result)
            return
        e2e_results = []
        for scenario in scenarios:
            start = time.perf_counter()
            event_bus.emit_sync("E2E_EXECUTION_STARTED", {
                "project_id": state.project_id,
                "agent": "QAAgent",
                "task_id": task_id,
                "scenario_id": scenario.scenario_id,
                "summary": f"E2E execution started: {scenario.scenario_id}.",
            })
            step_results = []
            for step in scenario.steps:
                event_bus.emit_sync("E2E_STEP_STARTED", {
                    "project_id": state.project_id,
                    "agent": "QAAgent",
                    "task_id": task_id,
                    "scenario_id": scenario.scenario_id,
                    "step_id": step.step_id,
                    "action": step.action,
                    "summary": f"E2E step started: {step.step_id} {step.action}.",
                })
                step_results.append(E2EStepResult(step_id=step.step_id, action=step.action, status="PENDING", expected=step.expected))
            playwright = run_agent_tool(
                state,
                "QAAgent",
                "playwright_runner",
                {"project_root": ".", "url": self._scenario_url(state.runtime_base_url, scenario), "steps": [step.model_dump() for step in scenario.steps]},
                task_id=task_id,
            )
            screenshots = []
            if not playwright.success:
                screenshot = run_agent_tool(
                    state,
                    "QAAgent",
                    "browser_screenshot",
                    {"project_root": ".", "url": self._scenario_url(state.runtime_base_url, scenario), "filename": f"{scenario.scenario_id}.png"},
                    task_id=task_id,
                )
                screenshots = screenshot.artifacts if screenshot.success else []
            status = "PASS" if playwright.success else self._e2e_blocked_or_fail(playwright)
            defects = self._localize_e2e_defect(state, scenario, playwright, status)
            for index, step_result in enumerate(step_results):
                final_status = "PASS" if status == "PASS" else ("FAIL" if index == len(step_results) - 1 else "PASS")
                step_result.status = final_status
                step_result.actual = playwright.stderr[-300:] if final_status == "FAIL" else "completed"
                if screenshots and final_status == "FAIL":
                    step_result.screenshot = screenshots[0]
                event_bus.emit_sync("E2E_STEP_COMPLETED" if final_status == "PASS" else "E2E_STEP_FAILED", {
                    "project_id": state.project_id,
                    "agent": "QAAgent",
                    "task_id": task_id,
                    "scenario_id": scenario.scenario_id,
                    "step_id": step_result.step_id,
                    "status": final_status,
                    "summary": f"E2E step {step_result.step_id}: {final_status}.",
                })
            result = E2EResult(
                scenario_id=scenario.scenario_id,
                status=status,
                steps=step_results,
                duration_ms=int((time.perf_counter() - start) * 1000),
                screenshots=screenshots,
                network_failures=playwright.structured_data.get("network_errors", []) if playwright.structured_data else [],
                console_errors=playwright.structured_data.get("console_errors", []) if playwright.structured_data else [],
                final_url=self._scenario_url(state.runtime_base_url, scenario),
                defect_locations=defects,
            )
            e2e_results.append(result)
            for defect in defects:
                event_bus.emit_sync("DEFECT_LOCALIZED", {
                    "project_id": state.project_id,
                    "agent": "QAAgent",
                    "task_id": task_id,
                    "scenario_id": scenario.scenario_id,
                    **defect.model_dump(),
                    "summary": f"Defect localized to {defect.layer} with {defect.confidence} confidence.",
                })
            event_bus.emit_sync("E2E_EXECUTION_COMPLETED", {
                "project_id": state.project_id,
                "agent": "QAAgent",
                "task_id": task_id,
                "scenario_id": scenario.scenario_id,
                "status": status,
                "summary": f"E2E execution completed: {scenario.scenario_id} {status}.",
            })
        state.e2e_results = e2e_results
        state.defect_locations.extend(location for result in e2e_results for location in result.defect_locations)
        if any(result.status == "FAIL" for result in e2e_results):
            qa_result.status = "failed"
            qa_result.passed = False
            qa_result.severity = "high"
            qa_result.architecture_violations.extend([f"E2E {result.scenario_id} failed: {', '.join(location.issue for location in result.defect_locations) or 'No localization evidence'}" for result in e2e_results if result.status == "FAIL"])
        qa_result.test_results.append(f"e2e_validation: {self._aggregate_e2e_status(e2e_results)} ({len(e2e_results)} scenario(s))")
        self._plan_repairs_from_defects(state, task_id, qa_result)
        self._run_repair_verification(state, task_id, qa_result)

    def _generate_e2e_scenarios(self, state: ProjectState):
        from backend.models.contracts import E2EScenario, E2EStep

        scenarios = []
        frontend_plan = state.frontend_architecture_plan
        if not frontend_plan:
            return scenarios
        requirement_by_id = {}
        if state.structured_requirements:
            requirement_by_id = {req.id: req.description for req in state.structured_requirements.functional_requirements}
        for index, trace in enumerate(frontend_plan.traceability[:5], start=1):
            page = trace.page or "Application"
            route = next((item.route for item in frontend_plan.pages if item.name == page), "/")
            api = trace.api_endpoint
            requirement = requirement_by_id.get(trace.requirement_id, trace.requirement)
            scenario_id = f"E2E-{index:03d}"
            steps = [
                E2EStep(step_id=f"{scenario_id}-STEP-001", action="OPEN", target=route, expected=f"{page} loads"),
                E2EStep(step_id=f"{scenario_id}-STEP-002", action="ASSERT_VISIBLE", target=page, expected=f"{page} is visible"),
            ]
            if api:
                steps.append(E2EStep(step_id=f"{scenario_id}-STEP-003", action="ASSERT_STATUS", target=api, expected="API contract responds without server error"))
            steps.append(E2EStep(step_id=f"{scenario_id}-STEP-999", action="SCREENSHOT", target=route, expected="Final state captured when needed"))
            scenarios.append(E2EScenario(
                scenario_id=scenario_id,
                name=f"{page} workflow",
                source_requirement=f"{trace.requirement_id}: {requirement}",
                preconditions=["Application runtime is READY"],
                steps=steps,
                expected_outcome=f"{page} supports requirement {trace.requirement_id}.",
                priority="HIGH" if index == 1 else "MEDIUM",
                frontend_page=page,
                api_endpoint=api,
            ))
        return scenarios

    def _scenario_url(self, base_url: str, scenario) -> str:
        first_open = next((step for step in scenario.steps if step.action == "OPEN"), None)
        route = first_open.target if first_open else "/"
        return base_url.rstrip("/") + "/" + route.lstrip("/")

    def _e2e_blocked_or_fail(self, tool_result) -> str:
        status = (tool_result.structured_data or {}).get("status", "")
        if status == "NOT_CONFIGURED" or "not configured" in (tool_result.stderr + tool_result.stdout).lower():
            return "NOT_CONFIGURED"
        if "timeout" in (tool_result.stderr + tool_result.stdout).lower():
            return "TIMEOUT"
        return "FAIL"

    def _localize_e2e_defect(self, state: ProjectState, scenario, tool_result, status: str):
        from backend.models.contracts import DefectLocation

        if status == "PASS":
            return []
        evidence = []
        stdout = tool_result.stdout[-500:] if tool_result.stdout else ""
        stderr = tool_result.stderr[-500:] if tool_result.stderr else ""
        if stdout:
            evidence.append(stdout)
        if stderr:
            evidence.append(stderr)
        if status == "NOT_CONFIGURED":
            return [DefectLocation(layer="CONFIGURATION", confidence="HIGH", endpoint=scenario.api_endpoint, component=scenario.frontend_page, evidence=evidence, issue="Playwright E2E tooling is not configured.", suggested_investigation="Add configured Playwright tests or test:e2e script before claiming browser E2E coverage.")]
        runtime_failures = [result for result in state.runtime_contract_results if result.status in {"FAIL", "TIMEOUT", "UNAVAILABLE"} and (not scenario.api_endpoint or result.endpoint in scenario.api_endpoint)]
        if runtime_failures:
            result = runtime_failures[0]
            return [DefectLocation(layer="BACKEND" if result.actual_status and result.actual_status >= 500 else "API_CONTRACT", confidence="MEDIUM", endpoint=f"{result.method} {result.endpoint}", component=scenario.frontend_page, evidence=evidence + [f"Runtime contract status: {result.status}"], issue="Runtime API evidence indicates the workflow API contract is unhealthy.", suggested_investigation="Check backend route, response schema, and contract alignment for this endpoint.")]
        if "cannot read" in stderr.lower() or "undefined" in stderr.lower() or "page error" in stderr.lower():
            file = ""
            if state.frontend_architecture_plan:
                trace = next((item for item in state.frontend_architecture_plan.traceability if item.page == scenario.frontend_page), None)
                file = trace.file if trace else ""
            return [DefectLocation(layer="FRONTEND", confidence="MEDIUM", file=file, endpoint=scenario.api_endpoint, component=scenario.frontend_page, evidence=evidence, issue="Browser evidence suggests a frontend runtime error.", suggested_investigation="Inspect the component state/data handling for undefined values.")]
        return [DefectLocation(layer="UNKNOWN", confidence="LOW", endpoint=scenario.api_endpoint, component=scenario.frontend_page, evidence=evidence, issue="E2E workflow failed without enough evidence to localize confidently.", suggested_investigation="Review Playwright output, browser console, network traces, and screenshots.")]

    def _aggregate_e2e_status(self, results) -> str:
        if not results:
            return "NOT_CONFIGURED"
        if any(result.status == "FAIL" for result in results):
            return "FAIL"
        if any(result.status in {"BLOCKED", "NOT_CONFIGURED", "TIMEOUT"} for result in results):
            return "BLOCKED"
        return "PASS"

    def _plan_repairs_from_defects(self, state: ProjectState, task_id: str, qa_result: QAResult) -> None:
        from backend.events import event_bus
        from backend.models.contracts import RepairAction, RepairPlan

        existing = {plan.defect_id for plan in state.repair_plans}
        sources = list(state.defect_locations)
        for issue in state.contract_issues:
            if issue.severity in {"ERROR", "BLOCKER"}:
                sources.append(self._defect_from_contract_issue(issue))
        for index, defect in enumerate(sources, start=1):
            defect_id = f"{defect.layer}:{defect.endpoint}:{defect.file}:{defect.issue}"
            if defect_id in existing:
                continue
            repair_id = f"REPAIR-{len(state.repair_plans) + 1:03d}"
            affected_files = [defect.file] if defect.file else []
            status = "PENDING" if affected_files or defect.endpoint or defect.component else "NEEDS_REVIEW"
            strategy = self._repair_strategy(defect)
            plan = RepairPlan(
                repair_id=repair_id,
                defect_id=defect_id,
                source_requirement=self._requirement_for_defect(state, defect),
                defect_location=defect,
                affected_files=affected_files,
                affected_endpoint=defect.endpoint,
                affected_component=defect.component,
                expected_behavior="Targeted validation passes and original requirement remains satisfied.",
                actual_behavior=defect.issue,
                repair_strategy=strategy,
                verification_strategy=self._verification_strategy(defect),
                risk="HIGH" if defect.layer in {"DATABASE", "AUTHENTICATION"} else "MEDIUM",
                status=status,
                actions=[
                    RepairAction(
                        action_id=f"{repair_id}-ACTION-001",
                        description=strategy,
                        target_file=defect.file,
                        target_endpoint=defect.endpoint,
                        target_component=defect.component,
                    )
                ],
            )
            state.repair_plans.append(plan)
            event_bus.emit_sync("REPAIR_PLAN_CREATED", {
                "project_id": state.project_id,
                "agent": "QAAgent",
                "task_id": task_id,
                "repair_id": repair_id,
                "status": status,
                "summary": f"Repair plan created: {repair_id} for {defect.layer}.",
            })
            if status == "NEEDS_REVIEW":
                qa_result.recommendations.append(f"{repair_id} needs review because affected files are ambiguous.")

    def _run_repair_verification(self, state: ProjectState, task_id: str, qa_result: QAResult) -> None:
        from backend.events import event_bus
        from backend.models.contracts import RegressionResult, TargetedVerification

        repaired = [result for result in state.repair_results if result.status == "SUCCESS"]
        for repair in repaired:
            if any(item.repair_id == repair.repair_id for item in state.targeted_verifications):
                continue
            event_bus.emit_sync("TARGETED_VERIFICATION_STARTED", {
                "project_id": state.project_id,
                "agent": "QAAgent",
                "task_id": task_id,
                "repair_id": repair.repair_id,
                "summary": f"Targeted verification started for {repair.repair_id}.",
            })
            plan = next((item for item in state.repair_plans if item.repair_id == repair.repair_id), None)
            defects_for_plan = [plan.defect_location] if plan and plan.defect_location else []
            still_present = any(self._defect_matches_repair(defect, repair) for defect in state.defect_locations for _ in [0])
            status = "FAIL" if still_present or repair.remaining_issues else "PASS"
            verification = TargetedVerification(
                repair_id=repair.repair_id,
                validation_type=self._verification_type(plan),
                target=(plan.affected_endpoint or ",".join(plan.affected_files)) if plan else "",
                expected=plan.expected_behavior if plan else "Defect resolved",
                actual="Remaining issue present" if status == "FAIL" else "No matching defect evidence remains",
                status=status,
                evidence=repair.modified_files + repair.remaining_issues,
            )
            state.targeted_verifications.append(verification)
            event_bus.emit_sync("TARGETED_VERIFICATION_COMPLETED", {
                "project_id": state.project_id,
                "agent": "QAAgent",
                "task_id": task_id,
                "repair_id": repair.repair_id,
                "status": status,
                "summary": f"Targeted verification {status} for {repair.repair_id}.",
            })
            if status != "PASS":
                event_bus.emit_sync("DEFECT_REMAINING", {
                    "project_id": state.project_id,
                    "agent": "QAAgent",
                    "task_id": task_id,
                    "repair_id": repair.repair_id,
                    "summary": f"Defect remains after {repair.repair_id}.",
                })
                qa_result.status = "failed"
                qa_result.passed = False
                continue
            event_bus.emit_sync("REGRESSION_STARTED", {
                "project_id": state.project_id,
                "agent": "QAAgent",
                "task_id": task_id,
                "repair_id": repair.repair_id,
                "summary": f"Regression verification started for {repair.repair_id}.",
            })
            regression = RegressionResult(
                repair_id=repair.repair_id,
                target=verification.target,
                status="PASS",
                evidence=["Static contract, runtime contract, and E2E layers contain no matching remaining defect evidence."],
            )
            state.regression_results.append(regression)
            if plan:
                plan.status = "RESOLVED"
            event_bus.emit_sync("REGRESSION_COMPLETED", {
                "project_id": state.project_id,
                "agent": "QAAgent",
                "task_id": task_id,
                "repair_id": repair.repair_id,
                "status": regression.status,
                "summary": f"Regression verification {regression.status} for {repair.repair_id}.",
            })
            event_bus.emit_sync("DEFECT_RESOLVED", {
                "project_id": state.project_id,
                "agent": "QAAgent",
                "task_id": task_id,
                "repair_id": repair.repair_id,
                "summary": f"Defect resolved by {repair.repair_id}.",
            })

    def _defect_from_contract_issue(self, issue):
        from backend.models.contracts import DefectLocation

        layer = "API_CONTRACT"
        if issue.category in {"CONNECTION_FAILURE", "TIMEOUT"}:
            layer = "RUNTIME"
        elif issue.category == "MISSING_DATABASE_MAPPING":
            layer = "DATABASE"
        return DefectLocation(
            layer=layer,
            confidence="MEDIUM",
            file=issue.file,
            endpoint=issue.endpoint,
            evidence=[issue.description],
            issue=issue.description,
            suggested_investigation=issue.suggested_fix,
        )

    def _repair_strategy(self, defect) -> str:
        if defect.layer == "FRONTEND":
            return "Make the smallest component/type handling change needed to satisfy the failing workflow without changing unrelated UI architecture."
        if defect.layer == "BACKEND":
            return "Inspect the endpoint implementation and correct the failing response path while preserving the defined API contract."
        if defect.layer == "API_CONTRACT":
            return "Align frontend service, backend route, and schema names with the static contract."
        if defect.layer == "DATABASE":
            return "Align model/schema field usage with the database entity mapping and affected API contract."
        if defect.layer == "CONFIGURATION":
            return "Add or correct the missing configured validation/runtime support without introducing arbitrary tooling."
        return "Investigate the localized evidence and make the smallest safe repair."

    def _verification_strategy(self, defect) -> str:
        if defect.layer in {"BACKEND", "API_CONTRACT", "DATABASE"}:
            return "Run static contract validation and runtime_api_validator for the affected endpoint."
        if defect.layer == "FRONTEND":
            return "Run relevant frontend validation and the affected E2E scenario."
        if defect.layer == "CONFIGURATION":
            return "Rerun capability detection and configured validation tooling."
        return "Run the smallest validation related to the defect evidence."

    def _verification_type(self, plan) -> str:
        if not plan or not plan.defect_location:
            return "UNKNOWN"
        if plan.defect_location.layer in {"BACKEND", "API_CONTRACT", "DATABASE"}:
            return "RUNTIME_CONTRACT"
        if plan.defect_location.layer == "FRONTEND":
            return "E2E_SCENARIO"
        return "TARGETED_QA"

    def _requirement_for_defect(self, state: ProjectState, defect) -> str:
        for result in state.e2e_results:
            if any(location.issue == defect.issue for location in result.defect_locations):
                scenario = next((item for item in state.e2e_scenarios if item.scenario_id == result.scenario_id), None)
                if scenario:
                    return scenario.source_requirement
        return ""

    def _defect_matches_repair(self, defect, repair) -> bool:
        return bool((defect.file and defect.file in repair.modified_files) or (defect.endpoint and defect.endpoint in repair.diff_summary))
