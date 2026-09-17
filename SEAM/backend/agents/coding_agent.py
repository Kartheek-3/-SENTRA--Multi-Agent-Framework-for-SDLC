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

CODING_PROMPT = """You are an expert Software Engineer executing a coding task for an autonomous framework.
Your job is to generate the physical source code files required to fulfill the assigned task.

Task ID: {task_id}
Description: {task_description}

Required Requirements to Implement:
{related_requirements}

Project Scale: {project_scale}

Project Architecture & Technology Stack:
{system_design}

QA Feedback & Prior Findings:
{qa_feedback}

GitHub Reference Context:
{github_context}

Existing Project Files:
{existing_files}

CRITICAL RULES:
1. Generate complete, valid source code for each file requested.
2. Ensure you ONLY use technologies specified in the Technology Stack.
3. If this task touches databases, follow the exact provided Database Schema.
4. If this task touches APIs, follow the exact provided API Endpoints schema.
5. Path rule: all file paths must be relative to the root of the generated project.
6. File Collision Protection: If a file already exists in Existing Project Files, you MUST preserve compatible existing functionality. Never blindly overwrite. Integrate your changes with existing code.
7. Return exactly matching the provided JSON schema.
8. IMPORTANT: You must output STRICT, valid JSON. Do NOT use Python triple-quotes (\"\"\") for strings inside the JSON. Use standard JSON escaping.

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
        qa_feedback = "\n".join(state.qa_feedback) if hasattr(state, "qa_feedback") and state.qa_feedback else "No prior QA feedback."
        github_context = state.github_findings.get("context", "No external GitHub context available.") if state.github_findings else "No external GitHub context available."
        scale_obj = getattr(state.structured_requirements, "scale_assessment", None)
        project_scale = scale_obj.scale_level.value if scale_obj else "UNKNOWN"
        
        format_instructions = self.parser.get_format_instructions()
        llm = self.model_router.get_model("coding")
        
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
                    from backend.knowledge.knowledge_service import KnowledgeService
                    ks = KnowledgeService()
                    rag_context = timed_call(
                        "rag_retrieval",
                        lambda: ks.retrieve_for_agent("CodingAgent", task.description),
                        project_id=state.project_id,
                        agent=agent_name,
                        task_id=task_id,
                    )

                    prompt = ChatPromptTemplate.from_template(CODING_PROMPT)
                    chain = prompt | llm
                    inputs = {
                        "task_id": task.task_id,
                        "task_description": task.description,
                        "related_requirements": reqs,
                        "project_scale": project_scale,
                        "rag_context": rag_context,
                        "system_design": sys_design,
                        "qa_feedback": qa_feedback,
                        "github_context": github_context,
                        "existing_files": existing_files,
                        "format_instructions": format_instructions
                    }
                    response = timed_llm_call(
                        lambda: chain.invoke(inputs),
                        project_id=state.project_id,
                        agent=agent_name,
                        task_id=task_id,
                        model=self.model_router.active_models.get("coding", {}).get("actual"),
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
                        model=self.model_router.active_models.get("coding", {}).get("actual"),
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
                
                # Write file
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(file_obj.content)

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

        # 6. Success State Update
        task.status = "completed"
        event_bus.emit_sync("TASK_COMPLETED", {"project_id": state.project_id, "agent": agent_name, "task_id": task_id})
        task.result = result_obj.model_dump()
        if task_id not in state.completed_tasks:
            state.completed_tasks.append(task_id)
            
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
