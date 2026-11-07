from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from backend.models.state import ProjectState
from backend.models.analysis import AnalysisResult
from backend.agents.model_compat import active_model_name, get_model_compat
from backend.performance import estimate_tokens, timed_call, timed_llm_call
import time

ANALYSIS_PROMPT = """You are an expert Software Architect and Business Analyst.
Your task is to analyze the following user requirement and extract a strictly structured analysis.

Instructions:
1. Understand the user's requirement.
2. Identify the software application domain.
3. Extract explicit requirements and assign them a stable ID (e.g., FR-001, NFR-001).
4. Identify implicit requirements carefully.
5. Separate functional and non-functional requirements.
6. Identify actors (users) and important entities (data objects).
7. Identify constraints.
8. Identify assumptions.
9. Identify risks.
10. Detect ambiguities instead of inventing facts.
11. Determine the product scale (SMALL, MEDIUM, LARGE, ENTERPRISE) by evaluating 20 scale dimensions (functional complexity, expected traffic, integration count, security requirements, etc.).
12. If scale-critical information is missing, record it as an assumption or unknown. Do not invent numbers.
13. Distinguish explicit requirements from inferred engineering considerations.
14. Produce machine-readable structured output matching the provided schema.

Do NOT generate any implementation code. Your responsibility is strictly analysis.

RAG Context (Organizational Memory):
{rag_context}

User Requirement:
{requirement}

{format_instructions}
"""

class AnalysisAgent:
    def __init__(self, model_router):
        self.model_router = model_router
        self.parser = PydanticOutputParser(pydantic_object=AnalysisResult)
        
    def process(self, state: ProjectState) -> ProjectState:
        start_time = time.time()
        agent_name = "AnalysisAgent"
        
        if not state.user_requirement.strip():
            state.errors.append("AnalysisAgent Error: User requirement is empty.")
            state.execution_history.append({
                "agent": agent_name,
                "status": "error",
                "error": "User requirement is empty.",
                "duration": time.time() - start_time
            })
            return state

        # Workflow B: Enhance Existing Project branch
        if state.is_enhance_workflow:
            try:
                from backend.github.workspace_service import SafeWorkspaceService
                from backend.github.understanding_service import ProjectUnderstandingService
                from backend.models.analysis import Requirement

                if not state.repo_url:
                    raise ValueError("Repository URL is required for Enhance Existing Project workflow.")

                workspace_service = SafeWorkspaceService()
                token = os.getenv("GITHUB_TOKEN")
                prep_result = workspace_service.prepare_workspace(
                    project_id=state.project_id,
                    repo_url_or_slug=state.repo_url,
                    branch=state.repo_branch or "main",
                    token=token,
                )

                state.repo_workspace_path = prep_result["workspace_path"]
                state.repo_owner = prep_result["owner"]
                state.repo_name = prep_result["name"]
                base_sha = prep_result["base_commit_sha"]

                event_bus.emit_sync("REPOSITORY_CONNECTED", {
                    "project_id": state.project_id,
                    "repository": f"{state.repo_owner}/{state.repo_name}",
                    "branch": state.repo_branch or "main",
                    "commit_sha": base_sha,
                    "workspace_path": state.repo_workspace_path,
                })

                # Perform evidence extraction & project understanding
                understanding_service = ProjectUnderstandingService(state.repo_workspace_path)
                profile, understanding = understanding_service.analyze(
                    workspace_path=state.repo_workspace_path,
                    owner=state.repo_owner,
                    name=state.repo_name,
                    branch=state.repo_branch or "main",
                    commit_sha=base_sha,
                )

                state.repo_profile = profile.model_dump()
                state.project_understanding = understanding.model_dump()

                # Persist artifacts
                project_dir = os.path.join("generated_projects", state.project_name)
                understanding_service.write_artifacts(project_dir, profile, understanding)

                event_bus.emit_sync("PROJECT_UNDERSTANDING_GENERATED", {
                    "project_id": state.project_id,
                    "repository": profile.repository,
                    "detected_languages": profile.detected_languages,
                    "api_routes_count": len(profile.api_routes),
                    "summary": understanding.project_purpose,
                })

                # Synthesize structured requirements for downstream planning
                state.structured_requirements = AnalysisResult(
                    project_summary=understanding.project_purpose,
                    application_domain=state.domain or "Software Enhancement",
                    functional_requirements=[
                        Requirement(id="FR-ENH-001", description=f"Enhance existing codebase: {state.user_requirement}")
                    ],
                    non_functional_requirements=[
                        Requirement(id="NFR-ENH-001", description="Maintain backward compatibility and adhere to existing coding conventions")
                    ],
                    actors=["User", "Developer"],
                    entities=[s["entity"] for s in profile.database_schemas] or ["Repository"],
                    constraints=[
                        "Confine modifications strictly to designated repository workspace",
                        "Preserve existing dependency conventions and test suites",
                    ],
                    assumptions=[f"Operating on baseline commit {base_sha[:8]}"],
                    risks=["Potential regression on untested legacy paths"],
                    technical_considerations=profile.frameworks + profile.detected_languages,
                    ambiguities=[],
                    recommended_capabilities=["Targeted Enhancement", "Regression Testing"],
                )

                state.execution_history.append({
                    "agent": agent_name,
                    "status": "success",
                    "workflow": "enhance_existing",
                    "repository": profile.repository,
                    "duration": time.time() - start_time,
                })
                return state

            except Exception as e:
                error_msg = f"AnalysisAgent Repository Enhancement Error: {str(e)}"
                state.errors.append(error_msg)
                state.execution_history.append({
                    "agent": agent_name,
                    "status": "error",
                    "error": error_msg,
                    "duration": time.time() - start_time,
                })
                return state

        prompt = ChatPromptTemplate.from_template(ANALYSIS_PROMPT)
        
        llm = get_model_compat(self.model_router, "analysis")
        
        try:
            # RAG integration through ToolRegistry/ToolExecutor.
            from backend.tools.agent_tools import run_agent_tool
            rag_result = run_agent_tool(
                state,
                "AnalysisAgent",
                "rag_search",
                {"query": state.user_requirement, "domain": state.domain or "general", "top_k": 5},
            )
            rag_context = str(rag_result.structured_data.get("results", [])) if rag_result.success else "No relevant organizational knowledge found."
            
            # We attempt to use with_structured_output if the model supports it natively
            # But ChatOllama with Qwen2.5-coder might need json format with a prompt parser.
            # Using standard parser approach to be safe with all models:
            chain = prompt | llm
            
            inputs = {
                "requirement": state.user_requirement,
                "rag_context": rag_context,
                "format_instructions": self.parser.get_format_instructions()
            }
            response = timed_llm_call(
                lambda: chain.invoke(inputs),
                project_id=state.project_id,
                agent="AnalysisAgent",
                model=active_model_name(self.model_router, "analysis"),
                input_token_estimate=estimate_tokens(inputs),
                timeout_seconds=getattr(llm, "timeout", None),
                retry_count=0,
            )
            
            result = self.parser.parse(response.content)
            
            # Update state
            state.structured_requirements = result
            from backend.knowledge.domain_intelligence import DomainIntelligenceService
            from backend.evaluation.ablation import capability_enabled, mark_disabled
            domain_service = DomainIntelligenceService()
            state.domain_identification = domain_service.identify(state.user_requirement, result)
            result.domain_identification = state.domain_identification
            state.domain = state.domain_identification.domain
            if capability_enabled(state, "domain_rag"):
                domain_context = domain_service.retrieve_context(state)
                state.retrieved_context.append(domain_service.format_for_prompt(domain_context))
            else:
                mark_disabled(state, "domain_rag", agent_name, "Domain-aware retrieval skipped by experiment configuration.")

            from backend.tools.github_intelligence import GitHubIntelligenceTool
            github_tool = GitHubIntelligenceTool()
            if github_tool.should_research(state):
                state.github_findings = github_tool.research(state)
            
            from backend.models.state import DesignArtifacts
            from backend.tools.document_generator import generate_analysis_artifacts, generate_analysis_document
            
            if state.design_artifacts is None:
                state.design_artifacts = DesignArtifacts()
                
            doc_path = generate_analysis_document(state.project_id, state.structured_requirements)
            state.design_artifacts.analysis_document_path = doc_path
            analysis_artifacts = generate_analysis_artifacts(state)
            domain_artifacts = domain_service.persist_artifacts(state) if capability_enabled(state, "domain_rag") else []
            state.execution_history.append({
                "agent": agent_name,
                "status": "artifacts_persisted",
                "artifacts": [artifact["path"] for artifact in analysis_artifacts + domain_artifacts],
                "duration": time.time() - start_time
            })
            
            state.execution_history.append({
                "agent": agent_name,
                "status": "success",
                "duration": time.time() - start_time
            })
            
        except Exception as e:
            error_msg = f"AnalysisAgent Error: Failed to parse LLM output. Details: {str(e)}"
            state.errors.append(error_msg)
            state.execution_history.append({
                "agent": agent_name,
                "status": "error",
                "error": error_msg,
                "duration": time.time() - start_time
            })
            
        return state
