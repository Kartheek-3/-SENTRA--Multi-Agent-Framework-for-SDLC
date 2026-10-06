from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from backend.models.state import ProjectState
from backend.models.planning import (
    FrontendAPIIntegration,
    FrontendArchitecturePlan,
    FrontendComponentPlan,
    FrontendFilePlan,
    FrontendPagePlan,
    FrontendRoutePlan,
    FrontendServicePlan,
    FrontendTraceabilityItem,
    ProjectPlan,
    Task,
)
from backend.events import event_bus
from backend.agents.model_compat import active_model_name, get_model_compat
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

Domain-Aware Context:
{domain_context}

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

Domain-Aware Context:
{domain_context}

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

        llm = get_model_compat(self.model_router, "planning")
        requirements_json = state.structured_requirements.model_dump_json(indent=2)
        format_instructions = self.parser.get_format_instructions()
        
        github_context = "No GitHub repository context available. Generate from scratch."
        if state.github_findings:
            github_context = state.github_findings.get("context", github_context)
        if state.github_selection and state.github_selection.reuse_existing and state.github_selection.selected_repository:
            repo = state.github_selection.selected_repository
            github_context += f"\nSelected high-relevance reference repository: {repo.owner}/{repo.name}. Use as static engineering reference only; do not copy source files blindly."
            
        from backend.tools.agent_tools import run_agent_tool
        rag_result = run_agent_tool(
            state,
            "PlanningAgent",
            "rag_search",
            {"query": state.domain + " " + state.user_requirement, "domain": state.domain or "general", "top_k": 5},
        )
        rag_context = str(rag_result.structured_data.get("results", [])) if rag_result.success else "No relevant organizational knowledge found."
        from backend.knowledge.domain_intelligence import DomainIntelligenceService
        from backend.evaluation.ablation import capability_enabled, mark_disabled
        domain_service = DomainIntelligenceService()
        if capability_enabled(state, "domain_rag") and not state.domain_context:
            domain_service.retrieve_context(state)
        if capability_enabled(state, "domain_rag"):
            domain_context = domain_service.format_for_prompt(state.domain_context)
        else:
            mark_disabled(state, "domain_rag", agent_name, "Planning domain-aware context injection skipped by experiment configuration.")
            domain_context = "Domain-aware context disabled by experiment configuration."
        
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
                        "domain_context": domain_context,
                        "format_instructions": format_instructions
                    }
                    response = timed_llm_call(
                        lambda: chain.invoke(inputs),
                        project_id=state.project_id,
                        agent="PlanningAgent",
                        model=active_model_name(self.model_router, "planning"),
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
                        "domain_context": domain_context,
                        "format_instructions": format_instructions,
                        "validation_error": str(last_error)
                    }
                    response = timed_llm_call(
                        lambda: chain.invoke(inputs),
                        project_id=state.project_id,
                        agent="PlanningAgent",
                        model=active_model_name(self.model_router, "planning"),
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
        if capability_enabled(state, "domain_rag"):
            domain_service.persist_traceability(state, agent_name, f"Planning used domain context for {plan.system_design.architecture_style}.")
        
        # Populate state.tasks
        for t in plan.tasks:
            state.tasks[t.task_id] = t
        self._plan_frontend_architecture(state, agent_name)
        if capability_enabled(state, "contract_intelligence"):
            self._analyze_full_stack_contracts(state, agent_name)
        else:
            mark_disabled(state, "contract_intelligence", agent_name, "Full-stack contract analysis skipped by experiment configuration.")
            
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
        try:
            architecture_tool = run_agent_tool(
                state,
                agent_name,
                "mermaid_generate",
                {
                    "diagram_type": "architecture",
                    "diagram_data": {
                        "nodes": [{"id": component.component_id or component.name, "label": component.name} for component in state.project_plan.system_design.components],
                        "edges": [
                            {"source": component.component_id or component.name, "target": dependency}
                            for component in state.project_plan.system_design.components
                            for dependency in component.dependencies
                        ],
                    },
                },
            )
            sequence_tool = run_agent_tool(
                state,
                agent_name,
                "mermaid_generate",
                {
                    "diagram_type": "sequence",
                    "diagram_data": {
                        "nodes": [{"id": "user", "label": "User"}, {"id": "api", "label": "API"}, {"id": "db", "label": "Database"}],
                        "edges": [{"source": "user", "target": "api"}, {"source": "api", "target": "db"}],
                    },
                },
            )
            for tool_result in [architecture_tool, sequence_tool]:
                for artifact in tool_result.artifacts:
                    if artifact:
                        state.design_artifacts.diagram_paths.append(artifact)
        except Exception as exc:
            state.errors.append(f"Mermaid tool generation warning: {exc}")
        
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

    def _plan_frontend_architecture(self, state: ProjectState, agent_name: str) -> None:
        if not self._has_frontend_scope(state):
            return
        event_bus.emit_sync("FRONTEND_PLAN_STARTED", {
            "project_id": state.project_id,
            "agent": agent_name,
            "summary": "Frontend architecture planning started.",
        })
        try:
            if not state.frontend_capabilities:
                from backend.tools.agent_tools import run_agent_tool
                detection = run_agent_tool(state, agent_name, "detect_frontend_capabilities", {"project_root": "."})
                if detection.success:
                    state.frontend_capabilities = detection.structured_data
            state.frontend_architecture_plan = self._build_frontend_architecture_plan(state)
            plan = state.frontend_architecture_plan
            event_bus.emit_sync("FRONTEND_PLAN_COMPLETED", {
                "project_id": state.project_id,
                "agent": agent_name,
                "framework": plan.framework,
                "language": plan.language,
                "build_system": plan.build_system,
                "pages": len(plan.pages),
                "components": len(plan.components),
                "services": len(plan.services),
                "summary": f"Frontend architecture planned: {plan.framework} / {plan.language} / {plan.build_system}.",
            })
        except Exception as exc:
            state.errors.append(f"Frontend architecture planning failed: {exc}")
            event_bus.emit_sync("FRONTEND_PLAN_FAILED", {
                "project_id": state.project_id,
                "agent": agent_name,
                "error": str(exc),
                "summary": "Frontend architecture planning failed.",
            })

    def _analyze_full_stack_contracts(self, state: ProjectState, agent_name: str) -> None:
        event_bus.emit_sync("CONTRACT_ANALYSIS_STARTED", {
            "project_id": state.project_id,
            "agent": agent_name,
            "summary": "Full-stack contract analysis started.",
        })
        try:
            from backend.contracts import build_full_stack_contract_profile
            profile = build_full_stack_contract_profile(state)
            state.full_stack_contract = profile
            state.contract_issues = profile.issues
            event_bus.emit_sync("CONTRACT_ANALYSIS_COMPLETED", {
                "project_id": state.project_id,
                "agent": agent_name,
                "status": profile.status,
                "api_contracts": len(profile.api_contracts),
                "frontend_api_usage": len(profile.frontend_api_usage),
                "database_entities": len(profile.database_entities),
                "issues": len(profile.issues),
                "summary": f"Full-stack contract analysis completed with {len(profile.issues)} issue(s).",
            })
        except Exception as exc:
            state.errors.append(f"Full-stack contract analysis failed: {exc}")
            event_bus.emit_sync("CONTRACT_ANALYSIS_FAILED", {
                "project_id": state.project_id,
                "agent": agent_name,
                "error": str(exc),
                "summary": "Full-stack contract analysis failed.",
            })

    def _has_frontend_scope(self, state: ProjectState) -> bool:
        capability = state.frontend_capabilities or {}
        if capability.get("package_json") or capability.get("framework") not in (None, "", "UNKNOWN", "not_configured"):
            return True
        text_parts = [state.user_requirement or ""]
        if state.structured_requirements:
            text_parts.extend(req.description for req in state.structured_requirements.functional_requirements)
            text_parts.extend(req.description for req in state.structured_requirements.non_functional_requirements)
            text_parts.extend(state.structured_requirements.technical_considerations)
        if state.system_design:
            text_parts.extend(state.system_design.technology_stack)
        text = " ".join(text_parts).lower()
        markers = ["frontend", "ui", "page", "screen", "dashboard", "react", "vite", "vue", "angular", "next", "form", "responsive", "login", "search"]
        return any(marker in text for marker in markers)

    def _build_frontend_architecture_plan(self, state: ProjectState) -> FrontendArchitecturePlan:
        profile = state.frontend_capabilities or {}
        framework = self._read_profile_value(profile, "framework")
        language = self._read_profile_value(profile, "language")
        build_system = self._read_profile_value(profile, "build_system")
        requirements = list(getattr(state.structured_requirements, "functional_requirements", []) or [])
        api_endpoints = list(getattr(getattr(state.project_plan, "system_design", None), "api_endpoints", []) or [])
        detected_pages = self._derive_pages(requirements, state.user_requirement)
        if not detected_pages:
            detected_pages = [{"name": "HomePage", "route": "/", "purpose": "Primary user entry point.", "auth": False, "requirements": requirements[:1]}]
        auth_required = any("login" in req.description.lower() or "auth" in req.description.lower() for req in requirements)
        components = self._derive_components(detected_pages, requirements)
        services = self._derive_services(api_endpoints, detected_pages)
        pages = []
        api_integrations = []
        traceability = []
        for page in detected_pages:
            endpoints = self._match_endpoints(page["name"], page["purpose"], api_endpoints)
            service_name = self._service_name_for_page(page["name"], services)
            component_names = [component.name for component in components if page["name"].replace("Page", "") in component.name or component.name in ("Navbar", "AppShell")]
            if not component_names:
                component_names = ["AppShell"]
            pages.append(FrontendPagePlan(
                name=page["name"],
                route=page["route"],
                purpose=page["purpose"],
                components=component_names,
                data_requirements=[req.description for req in page["requirements"]],
                api_dependencies=[self._endpoint_label(endpoint) for endpoint in endpoints],
                authentication_required=page["auth"],
                loading_state=f"Show non-blocking loading feedback while {page['name']} data is requested.",
                error_state=f"Show meaningful recovery text when {page['name']} requests fail.",
            ))
            api_integrations.append(FrontendAPIIntegration(
                page=page["name"],
                service=service_name,
                endpoints=[self._endpoint_label(endpoint) for endpoint in endpoints],
                mismatch_notes=[] if endpoints else ["No matching backend API endpoint was present in the current system design."],
            ))
            for req in page["requirements"]:
                traceability.append(FrontendTraceabilityItem(
                    requirement_id=req.id,
                    requirement=req.description,
                    page=page["name"],
                    component=component_names[0],
                    service=service_name,
                    api_endpoint=self._endpoint_label(endpoints[0]) if endpoints else "",
                    file=self._page_file(page["name"], framework, language),
                    validation=f"QA verifies {page['name']} implements {req.id} through component, API, and file checks.",
                ))
        return FrontendArchitecturePlan(
            framework=framework,
            language=language,
            build_system=build_system,
            routing_strategy=self._routing_strategy(framework, profile),
            state_management=self._state_management_strategy(profile, requirements),
            styling_strategy="Use existing styling dependencies and project conventions; do not add a new UI framework unless already present.",
            routes=[
                FrontendRoutePlan(
                    path=page.route,
                    page=page.name,
                    authentication_required=page.authentication_required,
                    purpose=page.purpose,
                )
                for page in pages
            ],
            pages=pages,
            layouts=["AppShell"],
            components=components,
            reusable_components=[component.name for component in components if component.reusable],
            services=services,
            api_integration=api_integrations,
            authentication=self._authentication_plan(auth_required, pages, api_endpoints),
            forms=self._forms(requirements),
            validation=["Validate required fields before submit.", "Render field-level errors and server validation messages."],
            error_handling=["Centralize API error normalization in the service layer.", "Show page-level fallback states for failed loads."],
            loading_states=["Disable submit buttons during writes.", "Use inline loading indicators for page data requests."],
            responsive_strategy=["Use fluid layouts for desktop, tablet, and mobile.", "Keep forms single-column on narrow screens.", "Avoid fixed pixel-heavy layouts."],
            accessibility_strategy=["Use semantic HTML landmarks.", "Associate labels with inputs.", "Maintain keyboard navigation and visible focus.", "Use meaningful button text and error messages."],
            testing_strategy=self._testing_strategy(profile),
            file_structure=self._file_plan(pages, components, services, framework, language),
            implementation_order=["application shell", "routing", "service/API layer", "shared components", "pages", "forms and validation", "error/loading states", "responsive/accessibility polish", "frontend checks"],
            traceability=traceability,
        )

    def _read_profile_value(self, profile: dict, key: str) -> str:
        value = profile.get(key)
        if value in (None, "", "not_configured"):
            return "UNKNOWN"
        return str(value)

    def _derive_pages(self, requirements, user_requirement: str):
        rules = [
            ("login", "LoginPage", "/login", "Authenticate users.", True),
            ("auth", "LoginPage", "/login", "Authenticate users.", True),
            ("search", "SearchPage", "/search", "Search and filter records.", False),
            ("filter", "ResultsPage", "/results", "Review filtered results.", False),
            ("booking", "BookingPage", "/booking", "Capture booking details.", True),
            ("dashboard", "DashboardPage", "/dashboard", "Summarize user activity and key metrics.", True),
            ("profile", "ProfilePage", "/profile", "Manage user profile details.", True),
            ("add", "ManagePage", "/manage", "Create and manage records.", False),
            ("edit", "ManagePage", "/manage", "Create and manage records.", False),
            ("delete", "ManagePage", "/manage", "Create and manage records.", False),
            ("view", "ListPage", "/items", "View records.", False),
        ]
        pages = {}
        for req in requirements:
            text = req.description.lower()
            for marker, name, route, purpose, auth in rules:
                if marker in text:
                    pages.setdefault(name, {"name": name, "route": route, "purpose": purpose, "auth": auth, "requirements": []})
                    pages[name]["requirements"].append(req)
        if not pages and any(word in (user_requirement or "").lower() for word in ["frontend", "ui", "react", "page", "form"]):
            pages["HomePage"] = {"name": "HomePage", "route": "/", "purpose": "Primary user workflow.", "auth": False, "requirements": list(requirements[:1])}
        return list(pages.values())

    def _derive_components(self, pages, requirements):
        components = [FrontendComponentPlan(name="AppShell", responsibility="Provide layout, navigation container, and shared page structure.", reusable=True)]
        if any(page["auth"] for page in pages):
            components.append(FrontendComponentPlan(name="Navbar", responsibility="Expose navigation and session actions.", state=["current route", "auth status"], reusable=True))
        for page in pages:
            stem = page["name"].replace("Page", "")
            if "Search" in page["name"]:
                components.append(FrontendComponentPlan(name="SearchForm", responsibility="Collect search criteria.", inputs_props=["initial values"], state=["form values", "validation errors"], api_interactions=["search endpoints"], reusable=True))
                components.append(FrontendComponentPlan(name="FilterPanel", responsibility="Apply result filters.", state=["selected filters"], reusable=True))
            elif "Booking" in page["name"] or "Manage" in page["name"]:
                components.append(FrontendComponentPlan(name=f"{stem}Form", responsibility=f"Capture and validate {stem.lower()} input.", state=["form values", "validation errors", "submit status"], api_interactions=["write endpoints"], reusable=False))
            elif "List" in page["name"] or "Results" in page["name"] or "Dashboard" in page["name"]:
                components.append(FrontendComponentPlan(name=f"{stem}List", responsibility=f"Render {stem.lower()} data for scanning and selection.", inputs_props=["items"], api_interactions=["read endpoints"], reusable=True))
            else:
                components.append(FrontendComponentPlan(name=f"{stem}Content", responsibility=f"Render {stem.lower()} workflow content.", reusable=False))
        return components

    def _derive_services(self, endpoints, pages):
        services = {}
        for endpoint in endpoints:
            stem = endpoint.path.strip("/").split("/")[-2 if "{" in endpoint.path and len(endpoint.path.strip("/").split("/")) > 1 else -1] or "api"
            name = "".join(part.capitalize() for part in stem.replace("-", "_").split("_")) + "Service"
            services.setdefault(name, FrontendServicePlan(name=name, responsibility=f"Call {stem} backend APIs.", api_endpoints=[]))
            services[name].api_endpoints.append(self._endpoint_label(endpoint))
        if not services:
            for page in pages:
                stem = page["name"].replace("Page", "")
                services[f"{stem}Service"] = FrontendServicePlan(name=f"{stem}Service", responsibility=f"Encapsulate API calls for {page['name']}.")
        return list(services.values())

    def _match_endpoints(self, page_name, purpose, endpoints):
        haystack = f"{page_name} {purpose}".lower()
        matches = []
        for endpoint in endpoints:
            text = f"{endpoint.path} {endpoint.purpose}".lower()
            if any(part in text for part in haystack.replace("page", "").split() if len(part) > 3):
                matches.append(endpoint)
        return matches

    def _service_name_for_page(self, page_name, services):
        stem = page_name.replace("Page", "")
        for service in services:
            if stem.lower() in service.name.lower():
                return service.name
        return services[0].name if services else f"{stem}Service"

    def _endpoint_label(self, endpoint) -> str:
        return f"{endpoint.method.upper()} {endpoint.path}"

    def _page_file(self, page_name, framework, language):
        ext = "tsx" if language.lower() == "typescript" else "jsx" if framework.lower() in ("react", "next") else "js"
        if framework.lower() == "next":
            route = page_name.replace("Page", "").lower()
            return f"app/{route}/page.{ext}"
        return f"src/pages/{page_name}.{ext}" if framework != "UNKNOWN" else f"frontend/pages/{page_name}.{ext}"

    def _file_plan(self, pages, components, services, framework, language):
        ext = "tsx" if language.lower() == "typescript" else "jsx" if framework.lower() in ("react", "next") else "js"
        base = "src" if framework != "UNKNOWN" else "frontend"
        files = [FrontendFilePlan(path=f"{base}/App.{ext}", operation="MODIFY", purpose="Wire application shell and planned routes.")]
        files.extend(FrontendFilePlan(path=self._page_file(page.name, framework, language), purpose=page.purpose) for page in pages)
        files.extend(FrontendFilePlan(path=f"{base}/components/{component.name}.{ext}", purpose=component.responsibility) for component in components)
        files.extend(FrontendFilePlan(path=f"{base}/services/{service.name[0].lower() + service.name[1:]}.{ 'ts' if language.lower() == 'typescript' else 'js'}", purpose=service.responsibility) for service in services)
        return files

    def _routing_strategy(self, framework, profile):
        deps = " ".join(profile.get("dependencies", []) + profile.get("dev_dependencies", [])).lower()
        if framework.lower() == "next":
            return "Use existing Next.js file-system routing."
        if "react-router" in deps:
            return "Use existing React Router configuration for planned routes."
        if framework.lower() in ("angular", "vue"):
            return f"Use existing {framework} routing conventions."
        if framework == "UNKNOWN":
            return "No routing library assumed; CodingAgent must use the detected project convention or keep routing minimal."
        return "Use framework-native routing only if already present; otherwise keep a minimal single-page flow."

    def _state_management_strategy(self, profile, requirements):
        deps = " ".join(profile.get("dependencies", []) + profile.get("dev_dependencies", [])).lower()
        for candidate in ("redux", "zustand", "pinia", "mobx"):
            if candidate in deps:
                return f"Use existing {candidate} state management."
        if len(requirements) > 6:
            return "Use local state plus existing context/provider patterns for shared UI state."
        return "Use local component state and service responses; do not add a new state dependency."

    def _authentication_plan(self, auth_required, pages, endpoints):
        if not auth_required:
            return {"required": False}
        auth_endpoints = [self._endpoint_label(endpoint) for endpoint in endpoints if "auth" in endpoint.path.lower() or "login" in endpoint.path.lower()]
        return {
            "required": True,
            "login_page": "LoginPage",
            "protected_routes": [page.route for page in pages if page.authentication_required],
            "token_or_session_handling": "Use the mechanism described by the backend/API design; do not invent a separate auth store.",
            "logout": "Expose logout through shared navigation when supported by the API contract.",
            "unauthorized_handling": "Redirect or block access to protected routes with clear feedback.",
            "api_endpoints": auth_endpoints,
        }

    def _forms(self, requirements):
        forms = []
        for req in requirements:
            text = req.description.lower()
            if any(word in text for word in ["add", "edit", "create", "booking", "login", "form"]):
                forms.append(req.description)
        return forms

    def _testing_strategy(self, profile):
        strategy = []
        if profile.get("typecheck_available"):
            strategy.append("Run configured frontend typecheck.")
        if profile.get("lint_available"):
            strategy.append("Run configured frontend lint.")
        if profile.get("frontend_test_framework") not in (None, "", "not_configured"):
            strategy.append(f"Run {profile.get('frontend_test_framework')} unit tests for pages, components, and services.")
        if profile.get("playwright_available"):
            strategy.append("Run Playwright browser tests for critical routes.")
        if profile.get("accessibility_available"):
            strategy.append("Run configured accessibility checks.")
        return strategy or ["No configured frontend test tooling detected; QA records NOT_CONFIGURED for optional checks."]
