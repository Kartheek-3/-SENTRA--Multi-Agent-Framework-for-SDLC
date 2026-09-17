from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from backend.models.state import ProjectState
from backend.models.planning import ProjectPlan, Task
from backend.performance import estimate_tokens, timed_call, timed_llm_call
import time

PLANNING_PROMPT = """You are an expert Senior Software Architect and Project Planner.
Your task is to convert the following analyzed software requirements into a detailed, machine-readable project plan and system architecture design.

Instructions:
1. Understand the analyzed requirements and the associated Scale Assessment.
2. START SIMPLE → ADD COMPLEXITY ONLY WHEN REQUIRED. Do NOT force complex infrastructure unless justified by the scale.
3. Convert requirements into implementation tasks.
4. Identify task dependencies. A task must only depend on tasks that must be completed BEFORE it.
5. Prioritize tasks.
6. Design the system architecture and specify major components. Provide explicit architecture decisions (purpose, reason, required/optional) for infrastructure components.
7. Define database entities and scalability constraints if applicable.
8. Define API endpoints if applicable.
9. Identify technology choices and security considerations scaled appropriately.
10. Provide a Scale Evolution Plan showing how the architecture can evolve.
11. Output your plan strictly conforming to the provided JSON schema.

CRITICAL TRACEABILITY REQUIREMENT:
Every task you generate MUST reference one or more requirement IDs in `related_requirements`. 
Example: FR-001, NFR-002.
Do NOT create tasks that have no reasonable relationship to the requirements (unless they are foundational infrastructure tasks).

CRITICAL DEPENDENCY REQUIREMENT:
Task dependencies MUST refer to valid `task_id` strings of other tasks you define.
Do NOT create circular dependencies (e.g., Task A depends on Task B, Task B depends on Task A).
A task CANNOT depend on itself.

CRITICAL MILESTONES FORMAT:
The "milestones" field MUST be a flat JSON array of strings.

CORRECT:
"milestones": [
    "Requirement Analysis",
    "System Design",
    "Implementation",
    "Testing"
]

INCORRECT:
"milestones": [
    {{
        "milestone_id": "M1",
        "title": "Requirement Analysis"
    }}
]

Each milestone MUST be a plain string.
Do NOT create milestone objects.
Do NOT add milestone_id.
Do NOT add title fields.
Do NOT add due_date.
Do NOT add nested JSON objects inside milestones.

DO NOT generate implementation code. Your responsibility is architecture and planning.

Analyzed Requirements:
{requirements}

GitHub Repository Context:
{github_context}

RAG Context (Organizational Memory):
{rag_context}

Example expected structure:
{{
  "project_overview": "...",
  "implementation_phases": [],
  "tasks": [
    {{
      "task_id": "TASK-001",
      "title": "...",
      "description": "...",
      "capability": "...",
      "priority": "...",
      "dependencies": [],
      "related_requirements": ["FR-001"],
      "estimated_complexity": "..."
    }}
  ],
  "milestones": [
    "Milestone 1",
    "Milestone 2"
  ],
  "system_design": {{
    "architecture_style": "...",
    "components": [],
    "data_flow": "...",
    "database_schema": [],
    "api_endpoints": [],
    "technology_stack": [],
    "security_considerations": []
  }},
  "implementation_strategy": "...",
  "risks_and_mitigations": []
}}

{format_instructions}
"""

RETRY_PROMPT = """Your previous response failed Pydantic validation or graph validation.

Correct ONLY the structural/schema problems.

Return ONLY a valid ProjectPlan object.

Do not return Markdown.
Do not return explanations.
Do not return code.

Follow the schema exactly.

Important:
- fields expecting lists must always be JSON arrays
- fields expecting objects must be JSON objects
- every task must have a unique task_id
- dependencies must reference valid task IDs
- no self-dependencies
- no circular dependencies
- requirement IDs must match the AnalysisResult
- preserve the original requirements
- do not remove required fields
- do not invent unrelated requirements

VALIDATION ERROR:
ProjectPlan field "milestones" expects List[str].
If validation failed because of milestones, your previous output incorrectly generated milestone objects.
You MUST replace:
{{
    "milestone_id": "...",
    "title": "...",
    "due_date": "..."
}}
with a plain string.
Example:
"milestones": [
    "Requirement Analysis",
    "Architecture Design",
    "Implementation",
    "Testing",
    "Deployment"
]
Return ONLY JSON matching the required Pydantic schema.

Validation Error that caused failure:
{validation_error}

Original Planning Request:
{requirements}

GitHub Repository Context:
{github_context}

RAG Context (Organizational Memory):
{rag_context}

{format_instructions}
"""

MAX_PLANNING_ATTEMPTS = 2

class PlanningAgent:
    def __init__(self, model_router):
        self.model_router = model_router
        self.parser = PydanticOutputParser(pydantic_object=ProjectPlan)
        
    def process(self, state: ProjectState) -> ProjectState:
        start_time = time.time()
        agent_name = "PlanningAgent"
        
        if not state.structured_requirements:
            error_msg = "PlanningAgent Error: AnalysisResult (structured_requirements) is missing."
            state.errors.append(error_msg)
            state.execution_history.append({
                "agent": agent_name,
                "status": "error",
                "error": error_msg,
                "duration": time.time() - start_time
            })
            return state

        llm = self.model_router.get_model("planning")
        requirements_json = state.structured_requirements.model_dump_json(indent=2)
        format_instructions = self.parser.get_format_instructions()
        
        github_context = "No GitHub repository context available. Generate from scratch."
        if state.github_findings:
            github_context = state.github_findings.get("context", github_context)
        if state.github_selection and state.github_selection.reuse_existing and state.github_selection.selected_repository:
            repo = state.github_selection.selected_repository
            github_context += f"\nSelected high-relevance reference repository: {repo.owner}/{repo.name}. Use as static engineering reference only; do not copy source files blindly."
            
        from backend.knowledge.knowledge_service import KnowledgeService
        ks = KnowledgeService()
        rag_context = timed_call(
            "rag_retrieval",
            lambda: ks.retrieve_for_agent("PlanningAgent", state.domain + " " + state.user_requirement),
            project_id=state.project_id,
            agent="PlanningAgent",
        )
        
        attempt = 1
        last_error = None
        plan = None
        validation_passed = False
        
        while attempt <= MAX_PLANNING_ATTEMPTS:
            try:
                if attempt == 1:
                    prompt = ChatPromptTemplate.from_template(PLANNING_PROMPT)
                    chain = prompt | llm
                    inputs = {
                        "requirements": requirements_json,
                        "github_context": github_context,
                        "rag_context": rag_context,
                        "format_instructions": format_instructions
                    }
                    response = timed_llm_call(
                        lambda: chain.invoke(inputs),
                        project_id=state.project_id,
                        agent="PlanningAgent",
                        model=self.model_router.active_models.get("planning", {}).get("actual"),
                        input_token_estimate=estimate_tokens(inputs),
                        timeout_seconds=getattr(llm, "timeout", None),
                        retry_count=attempt - 1,
                    )
                else:
                    prompt = ChatPromptTemplate.from_template(RETRY_PROMPT)
                    chain = prompt | llm
                    inputs = {
                        "requirements": requirements_json,
                        "github_context": github_context,
                        "rag_context": rag_context,
                        "format_instructions": format_instructions,
                        "validation_error": str(last_error)
                    }
                    response = timed_llm_call(
                        lambda: chain.invoke(inputs),
                        project_id=state.project_id,
                        agent="PlanningAgent",
                        model=self.model_router.active_models.get("planning", {}).get("actual"),
                        input_token_estimate=estimate_tokens(inputs),
                        timeout_seconds=getattr(llm, "timeout", None),
                        retry_count=attempt - 1,
                    )
                
                current_plan = self.parser.parse(response.content)
                
                # Deterministic Python validation of task graph
                task_ids = set()
                for t in current_plan.tasks:
                    if t.task_id in task_ids:
                        raise ValueError(f"Duplicate task_id found: {t.task_id}")
                    task_ids.add(t.task_id)
                    
                for t in current_plan.tasks:
                    for dep in t.dependencies:
                        if dep not in task_ids:
                            raise ValueError(f"Task {t.task_id} depends on unknown task_id: {dep}")
                        if dep == t.task_id:
                            raise ValueError(f"Task {t.task_id} depends on itself.")
                
                # Simple circular dependency check
                def has_cycle(current, visited, stack):
                    visited.add(current)
                    stack.add(current)
                    
                    current_task = next((x for x in current_plan.tasks if x.task_id == current), None)
                    if current_task:
                        for dep in current_task.dependencies:
                            if dep not in visited:
                                if has_cycle(dep, visited, stack):
                                    return True
                            elif dep in stack:
                                return True
                    stack.remove(current)
                    return False
                    
                visited = set()
                for t in current_plan.tasks:
                    if t.task_id not in visited:
                        if has_cycle(t.task_id, visited, set()):
                            raise ValueError("Circular dependency detected in tasks.")
                
                # Validation passed!
                plan = current_plan
                validation_passed = True
                break
                
            except Exception as e:
                last_error = e
                error_msg = f"Attempt {attempt} failed: {str(e)}"
                state.errors.append(error_msg)
                attempt += 1

        if not validation_passed:
            # Both attempts failed
            error_msg = "PlanningAgent Error: Failed to generate a valid ProjectPlan after maximum attempts."
            state.errors.append(error_msg)
            state.execution_history.append({
                "agent": agent_name,
                "status": "error",
                "error": error_msg,
                "attempts": attempt - 1,
                "duration": time.time() - start_time
            })
            return state
            
        # Update state with valid plan
        state.project_plan = plan
        state.system_design = plan.system_design
        
        # Populate state.tasks
        for t in plan.tasks:
            state.tasks[t.task_id] = t
            
        from backend.models.state import DesignArtifacts
        from backend.tools.document_generator import generate_design_artifacts, generate_design_document
        from backend.tools.diagram_generator import generate_all_diagrams_for_state
        
        if state.design_artifacts is None:
            state.design_artifacts = DesignArtifacts()
            
        doc_path = generate_design_document(state.project_id, state.domain, state.project_plan)
        state.design_artifacts.system_design_document_path = doc_path
        
        design_artifacts = generate_design_artifacts(state)
        diagram_paths = generate_all_diagrams_for_state(state)
        state.design_artifacts.diagram_paths.extend(diagram_paths)
        
        history_record = {
            "agent": agent_name,
            "status": "success",
            "attempts": attempt,
            "artifacts": [artifact["path"] for artifact in design_artifacts] + diagram_paths,
            "duration": time.time() - start_time
        }
        if attempt > 1:
            history_record["initial_validation"] = "failed"
            history_record["self_correction"] = "successful"
            
        state.execution_history.append(history_record)
        
        return state
