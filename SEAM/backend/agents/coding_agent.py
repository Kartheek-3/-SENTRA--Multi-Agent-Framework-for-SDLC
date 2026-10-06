import time
import os
from pathlib import Path
from pydantic import ValidationError
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from backend.models.state import ProjectState
from backend.models.coding import CodeGenerationResult
from backend.events import event_bus
from backend.performance import estimate_tokens, timed_call, timed_llm_call
from backend.agents.model_compat import active_model_name, get_model_compat

CODING_PROMPT = """You are an expert Software Engineer executing a coding task for an autonomous framework.
Your job is to generate the physical source code files required to fulfill the assigned task.

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

Active Repair Plans:
{repair_plans}

QA Feedback & Prior Findings:
{qa_feedback}

GitHub Reference Context:
{github_context}

RAG Context (Organizational Memory):
{rag_context}

Domain-Aware Context:
{domain_context}

Existing Project Files:
{existing_files}

CRITICAL RULES:
1. Generate complete, valid source code for each file requested.
2. Ensure you ONLY use technologies specified in the Technology Stack.
3. If this task touches databases, follow the exact provided Database Schema.
4. If this task touches APIs, follow the exact provided API Endpoints schema.
5. Path rule: all file paths must be relative to the root of the generated project.
6. File Collision Protection: If a file already exists in Existing Project Files, you MUST preserve compatible existing functionality. Never blindly overwrite. Integrate your changes with existing code.
7. If Frontend Architecture Plan is present, follow its framework, routes, pages, components, services, API mappings, file plan, and implementation order. Do NOT invent a conflicting frontend architecture.
8. If Full-Stack Contract Profile is present, align frontend service calls, backend routes, request/response schemas, and database fields to it. Do NOT knowingly introduce a contract mismatch that is already identified.
9. If Active Repair Plans are present, make the smallest targeted repair for the affected files/endpoints/components. Do NOT redesign unrelated parts of the project.
10. Return exactly matching the provided JSON schema.
11. IMPORTANT: You must output STRICT, valid JSON. Do NOT use Python triple-quotes (\"\"\") for strings inside the JSON. Use standard JSON escaping.

{format_instructions}
"""

RETRY_PROMPT = """Your previous response failed validation.

Correct ONLY the structural/schema problems or path validation errors.
Return ONLY a valid CodeGenerationResult JSON object.

Validation Error that caused failure:
{validation_error}

Original Coding Task:
Task ID: {task_id}
Description: {task_description}

{format_instructions}
"""

MAX_CODING_ATTEMPTS = 2

class CodingAgent:
    def __init__(self, model_router):
        self.model_router = model_router
        self.parser = PydanticOutputParser(pydantic_object=CodeGenerationResult)
        
    def process(self, state: ProjectState, task_id: str) -> ProjectState:
        start_time = time.time()
        agent_name = "CodingAgent"
        
        if task_id not in state.tasks:
            self._log_error(state, agent_name, f"Task {task_id} not found in state.", start_time)
            return state
            
        task = state.tasks[task_id]
        event_bus.emit_sync("TASK_STARTED", {"project_id": state.project_id, "agent": agent_name, "task_id": task_id})
        
        # 1. Dependency Validation
        for dep in task.dependencies:
            if dep not in state.completed_tasks:
                self._log_error(state, agent_name, f"Cannot execute task {task_id}: Dependency {dep} is not completed.", start_time)
                task.status = "failed"
                if task_id not in state.failed_tasks:
                    state.failed_tasks.append(task_id)
                return state

        # 2. Extract Context
        reqs = "\n".join(task.related_requirements) if task.related_requirements else "None explicitly assigned."
        sys_design = state.project_plan.system_design.model_dump_json(indent=2) if (state.project_plan and state.project_plan.system_design) else "{}"
        frontend_architecture_plan = state.frontend_architecture_plan.model_dump_json(indent=2) if state.frontend_architecture_plan else "{}"
        full_stack_contract = state.full_stack_contract.model_dump_json(indent=2) if state.full_stack_contract else "{}"
        active_repair_plans = [plan for plan in state.repair_plans if plan.status in {"PENDING", "IN_PROGRESS"}]
        repair_plans = "[" + ",".join(plan.model_dump_json() for plan in active_repair_plans) + "]" if active_repair_plans else "[]"
        qa_feedback = "\n".join(state.qa_feedback) if hasattr(state, "qa_feedback") and state.qa_feedback else "No prior QA feedback."
        github_context = state.github_findings.get("context", "No external GitHub context available.") if state.github_findings else "No external GitHub context available."
        scale_obj = getattr(state.structured_requirements, "scale_assessment", None)
        project_scale = scale_obj.scale_level.value if scale_obj else "UNKNOWN"
        
        format_instructions = self.parser.get_format_instructions()
        llm = get_model_compat(self.model_router, "coding")
        
        project_dir = os.path.join("generated_projects", state.project_name)
        existing_files = self._get_existing_files_context(project_dir)
        
        attempt = 1
        last_error = None
        result_obj = None
        validation_passed = False
        
        # 3. Code Generation & Retry Loop
        while attempt <= MAX_CODING_ATTEMPTS:
            try:
                if attempt == 1:
                    from backend.tools.agent_tools import run_agent_tool
                    rag_result = run_agent_tool(
                        state,
                        agent_name,
                        "rag_search",
                        {"query": task.description, "domain": state.domain or "general", "top_k": 5},
                        task_id=task_id,
                    )
                    rag_context = str(rag_result.structured_data.get("results", [])) if rag_result.success else "No relevant organizational knowledge found."
                    from backend.knowledge.domain_intelligence import DomainIntelligenceService
                    from backend.evaluation.ablation import capability_enabled, mark_disabled
                    domain_service = DomainIntelligenceService()
                    if capability_enabled(state, "domain_rag") and not state.domain_context:
                        if state.domain_identification or state.structured_requirements:
                            domain_service.retrieve_context(state, current_task=task.description)
                    if capability_enabled(state, "domain_rag"):
                        domain_context = domain_service.format_for_prompt(state.domain_context)
                    else:
                        mark_disabled(state, "domain_rag", agent_name, "Coding domain-aware context injection skipped by experiment configuration.")
                        domain_context = "Domain-aware context disabled by experiment configuration."

                    prompt = ChatPromptTemplate.from_template(CODING_PROMPT)
                    chain = prompt | llm
                    inputs = {
                        "task_id": task.task_id,
                        "task_description": task.description,
                        "related_requirements": reqs,
                        "project_scale": project_scale,
                        "rag_context": rag_context,
                        "system_design": sys_design,
                        "frontend_architecture_plan": frontend_architecture_plan,
                        "full_stack_contract": full_stack_contract,
                        "repair_plans": repair_plans,
                        "qa_feedback": qa_feedback,
                        "github_context": github_context,
                        "domain_context": domain_context,
                        "existing_files": existing_files,
                        "format_instructions": format_instructions
                    }
                    response = timed_llm_call(
                        lambda: chain.invoke(inputs),
                        project_id=state.project_id,
                        agent=agent_name,
                        task_id=task_id,
                        model=active_model_name(self.model_router, "coding"),
                        input_token_estimate=estimate_tokens(inputs),
                        timeout_seconds=getattr(llm, "timeout", None),
                        retry_count=attempt - 1,
                    )
                else:
                    prompt = ChatPromptTemplate.from_template(RETRY_PROMPT)
                    chain = prompt | llm
                    inputs = {
                        "task_id": task.task_id,
                        "task_description": task.description,
                        "validation_error": str(last_error),
                        "format_instructions": format_instructions
                    }
                    response = timed_llm_call(
                        lambda: chain.invoke(inputs),
                        project_id=state.project_id,
                        agent=agent_name,
                        task_id=task_id,
                        model=active_model_name(self.model_router, "coding"),
                        input_token_estimate=estimate_tokens(inputs),
                        timeout_seconds=getattr(llm, "timeout", None),
                        retry_count=attempt - 1,
                    )
                
                parsed_result = self.parser.parse(response.content)
                
                # 4. Path Validation
                for f in parsed_result.files:
                    path = f.path
                    if os.path.isabs(path):
                        raise ValueError(f"Absolute paths are forbidden: {path}")
                    if ".." in path or path.startswith("/") or path.startswith("\\"):
                        raise ValueError(f"Unsafe path traversal detected: {path}")
                
                # Validation Passed
                result_obj = parsed_result
                validation_passed = True
                break
                
            except Exception as e:
                last_error = e
                error_msg = f"Attempt {attempt} failed: {str(e)}"
                state.errors.append(error_msg)
                attempt += 1

        # 5. Handle Failure or Write Files
        if not validation_passed or result_obj is None:
            self._log_error(state, agent_name, f"Failed to generate valid code for task {task_id} after {MAX_CODING_ATTEMPTS} attempts.", start_time, attempts=attempt - 1)
            task.status = "failed"
            if task_id not in state.failed_tasks:
                state.failed_tasks.append(task_id)
            return state

        # Safe File Writing with Collision Protection
        project_dir = os.path.join("generated_projects", state.project_name)
        
        try:
            from backend.tools.agent_tools import run_agent_tool
            run_agent_tool(state, agent_name, "file_search", {"pattern": "", "root": "."}, task_id=task_id)
            for file_obj in result_obj.files:
                # Resolve absolute path carefully
                full_path = os.path.abspath(os.path.join(project_dir, file_obj.path))
                
                # Double check the resolved path is still inside the project dir
                if not full_path.startswith(os.path.abspath(project_dir)):
                    raise ValueError(f"Path escape attempted after resolution: {file_obj.path}")
                
                file_exists = os.path.exists(full_path)
                directory = os.path.dirname(full_path)
                new_directories = []
                probe = directory
                while probe and not os.path.exists(probe):
                    new_directories.append(probe)
                    parent = os.path.dirname(probe)
                    if parent == probe:
                        break
                    probe = parent

                os.makedirs(directory, exist_ok=True)
                for created_dir in reversed(new_directories):
                    rel_dir = os.path.relpath(created_dir, project_dir).replace("\\", "/")
                    if rel_dir != ".":
                        event_bus.emit_sync("DIRECTORY_CREATED", {
                            "project_id": state.project_id,
                            "agent": agent_name,
                            "task_id": task_id,
                            "path": rel_dir,
                            "operation": "created"
                        })

                # File Collision Check & Preservation
                if file_exists:
                    # In a fully robust implementation, we might parse existing content
                    # and intelligently merge. Here we assume the LLM has provided the COMPLETE
                    # integrated content due to our strict prompt instructions (Rule 6).
                    # We log that we are modifying rather than blindly creating.
                    self._log_error(state, agent_name, f"Modifying existing file: {file_obj.path}", start_time, attempts=attempt)
                
                write_result = run_agent_tool(
                    state,
                    agent_name,
                    "file_write",
                    {"path": file_obj.path, "content": file_obj.content},
                    task_id=task_id,
                )
                if not write_result.success:
                    raise ValueError(write_result.error.message if write_result.error else f"file_write failed for {file_obj.path}")

                event_bus.emit_sync("FILE_UPDATED" if file_exists else "FILE_GENERATED", {
                    "project_id": state.project_id,
                    "agent": agent_name,
                    "task_id": task_id,
                    "path": file_obj.path,
                    "operation": "updated" if file_exists else "created",
                    "size": len(file_obj.content.encode("utf-8"))
                })
                try:
                    from backend.foundation.services import artifact_registry
                    artifact = artifact_registry.register_file(
                        state.project_id,
                        file_obj.path,
                        "CODE",
                        title=file_obj.path,
                        task_id=task_id,
                        agent_id=agent_name,
                        operation="updated" if file_exists else "created",
                    )
                    event_bus.emit_sync("ARTIFACT_REGISTERED", {
                        "project_id": state.project_id,
                        "agent": agent_name,
                        "task_id": task_id,
                        "artifact_id": artifact.artifact_id,
                        "path": file_obj.path,
                        "status": artifact.status,
                        "summary": file_obj.path,
                    })
                except Exception as artifact_error:
                    state.errors.append(f"Artifact registry warning for {file_obj.path}: {artifact_error}")
                    
        except Exception as e:
            self._log_error(state, agent_name, f"Filesystem write failed for task {task_id}: {str(e)}", start_time, attempts=attempt)
            task.status = "failed"
            if task_id not in state.failed_tasks:
                state.failed_tasks.append(task_id)
            return state
        try:
            run_agent_tool(state, agent_name, "git_status", {}, task_id=task_id)
            diff_result = run_agent_tool(state, agent_name, "git_diff", {}, task_id=task_id)
            run_agent_tool(state, agent_name, "git_add", {"paths": ["."],}, task_id=task_id)
            run_agent_tool(state, agent_name, "git_commit", {"message": f"Complete {task_id}"}, task_id=task_id)
        except Exception as exc:
            state.errors.append(f"Git inspection tool warning for {task_id}: {exc}")
            diff_result = None
        self._record_repair_result(state, task_id, result_obj, diff_result)
        self._run_frontend_coding_checks(state, task_id, project_dir)

        # 6. Success State Update
        task.status = "completed"
        event_bus.emit_sync("TASK_COMPLETED", {"project_id": state.project_id, "agent": agent_name, "task_id": task_id})
        task.result = result_obj.model_dump()
        if task_id not in state.completed_tasks:
            state.completed_tasks.append(task_id)
        try:
            from backend.evaluation.ablation import capability_enabled
            if capability_enabled(state, "domain_rag"):
                from backend.knowledge.domain_intelligence import DomainIntelligenceService
                DomainIntelligenceService().persist_traceability(state, agent_name, f"Coding task {task_id} received domain context.")
        except Exception as exc:
            state.errors.append(f"Domain traceability update failed for coding task {task_id}: {exc}")
            
        history_record = {
            "agent": agent_name,
            "task_id": task_id,
            "status": "success",
            "attempts": attempt,
            "duration": time.time() - start_time
        }
        if attempt > 1:
            history_record["initial_validation"] = "failed"
            history_record["self_correction"] = "successful"
            
        state.execution_history.append(history_record)
        return state

    def _record_repair_result(self, state: ProjectState, task_id: str, result_obj, diff_result) -> None:
        from backend.events import event_bus
        from backend.models.contracts import RepairResult

        active = [plan for plan in state.repair_plans if plan.status in {"PENDING", "IN_PROGRESS"}]
        if not active:
            return
        modified_files = [file_obj.path for file_obj in result_obj.files]
        diff_summary = ""
        if diff_result:
            diff_summary = (diff_result.stdout or diff_result.stderr or "")[-2000:]
        for plan in active:
            event_bus.emit_sync("REPAIR_STARTED", {
                "project_id": state.project_id,
                "agent": "CodingAgent",
                "task_id": task_id,
                "repair_id": plan.repair_id,
                "summary": f"Repair started: {plan.repair_id}.",
            })
            affected = set(plan.affected_files or [])
            touched = set(modified_files)
            safe_scope = not affected or bool(affected & touched)
            status = "SUCCESS" if safe_scope else "NEEDS_REVIEW"
            plan.status = "IMPLEMENTED" if status == "SUCCESS" else "NEEDS_REVIEW"
            repair_result = RepairResult(
                repair_id=plan.repair_id,
                status=status,
                modified_files=modified_files,
                diff_summary=diff_summary,
                defect_addressed=status == "SUCCESS",
                remaining_issues=[] if status == "SUCCESS" else ["Repair did not touch the affected file from the repair plan."],
                verification_required=[plan.verification_strategy],
            )
            state.repair_results.append(repair_result)
            event_bus.emit_sync("REPAIR_COMPLETED" if status == "SUCCESS" else "REPAIR_FAILED", {
                "project_id": state.project_id,
                "agent": "CodingAgent",
                "task_id": task_id,
                "repair_id": plan.repair_id,
                "status": status,
                "summary": f"Repair {status}: {plan.repair_id}.",
            })

    def _run_frontend_coding_checks(self, state: ProjectState, task_id: str, project_dir: str) -> None:
        package_path = os.path.join(project_dir, "package.json")
        if not os.path.exists(package_path):
            return
        from backend.tools.agent_tools import run_agent_tool

        detection = run_agent_tool(state, "CodingAgent", "detect_frontend_capabilities", {"project_root": "."}, task_id=task_id)
        if detection.success:
            state.frontend_capabilities = detection.structured_data
        profile = state.frontend_capabilities or {}
        checks = []
        planned_tools = []
        if profile.get("typecheck_available"):
            planned_tools.append("typecheck_runner")
        if profile.get("lint_available"):
            planned_tools.append("lint_runner")
        if profile.get("build_available"):
            planned_tools.append("build_runner")
        for tool_name in planned_tools:
            result = run_agent_tool(state, "CodingAgent", tool_name, {"project_root": "."}, task_id=task_id)
            checks.append({
                "tool": tool_name,
                "success": result.success,
                "status": result.structured_data.get("status", "SUCCESS" if result.success else "FAILED"),
                "error": result.error.message if result.error else result.stderr[-500:],
            })
        state.frontend_execution.setdefault(task_id, {})
        state.frontend_execution[task_id]["capability_profile"] = profile
        state.frontend_execution[task_id]["coding_checks"] = checks
        state.frontend_execution[task_id]["package_detected"] = True

    def _log_error(self, state, agent_name, error_msg, start_time, attempts=1):
        state.errors.append(error_msg)
        state.execution_history.append({
            "agent": agent_name,
            "status": "error",
            "error": error_msg,
            "attempts": attempts,
            "duration": time.time() - start_time
        })

    def _get_existing_files_context(self, project_dir: str) -> str:
        if not os.path.exists(project_dir):
            return "No existing files."
        context = ""
        for root, _, files in os.walk(project_dir):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, project_dir)
                context += f"\n--- {rel_path} ---\n"
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        context += f.read() + "\n"
                except Exception:
                    context += "<Binary or unreadable file>\n"
        return context if context else "No existing files."
