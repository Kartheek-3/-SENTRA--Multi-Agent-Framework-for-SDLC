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
