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

QA_PROMPT = """You are an expert QA Engineer for an autonomous framework.
Your job is to validate the generated code against the established project requirements and architecture.

Task ID: {task_id}
Description: {task_description}

Required Requirements to Implement:
{related_requirements}

Project Scale: {project_scale}

Project Architecture & Technology Stack:
{system_design}

GitHub Reference Context:
{github_context}

RAG Context (Organizational Memory):
{rag_context}

Generated Files and Content to Review:
{files_content}

CRITICAL RULES:
1. Verify if the generated code successfully implements the Required Requirements.
2. Verify if the generated code adheres to the specified Technology Stack.
3. Check for architectural violations (e.g., ignoring DB schemas, missing API endpoints).
4. Scale-Aware QA: Adapt your QA stringency to the Project Scale. Ensure ENTERPRISE projects are strictly checked for performance/security, while SMALL stays simple.
5. Do NOT re-write the code. You are strictly providing QA feedback.
6. Produce exactly matching JSON according to the schema.
7. If the code completely fulfills the task, mark status as "passed" and passed=true.
8. If there are major issues, mark status as "failed". If minor, mark "needs_revision".

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
        scale_obj = getattr(state.structured_requirements, "scale_assessment", None)
        project_scale = scale_obj.scale_level.value if scale_obj else "UNKNOWN"
        github_context = state.github_findings.get("context", "No GitHub reference context available.") if state.github_findings else "No GitHub reference context available."
        
        format_instructions = self.parser.get_format_instructions()
        llm = self.model_router.get_model("qa")
        
        attempt = 1
        last_error = None
        result_obj = None
        validation_passed = False
        
        from backend.knowledge.knowledge_service import KnowledgeService
        ks = KnowledgeService()
        rag_context = timed_call(
            "rag_retrieval",
            lambda: ks.retrieve_for_agent("QAAgent", task.description),
            project_id=state.project_id,
            agent=agent_name,
            task_id=task_id,
        )

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
                        "github_context": github_context,
                        "rag_context": rag_context,
                        "files_content": files_content_str,
                        "format_instructions": format_instructions
                    }
                    response = timed_llm_call(
                        lambda: chain.invoke(inputs),
                        project_id=state.project_id,
                        agent=agent_name,
                        task_id=task_id,
                        model=self.model_router.active_models.get("qa", {}).get("actual"),
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
                        model=self.model_router.active_models.get("qa", {}).get("actual"),
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
        if security_issues:
            result_obj.security_issues.extend(security_issues)
            result_obj.status = "failed"
            result_obj.passed = False
            result_obj.severity = "high"
            
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
