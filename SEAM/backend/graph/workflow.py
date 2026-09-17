from langgraph.graph import StateGraph, END
from backend.models.state import ProjectState
from backend.llm.model_router import ModelRouter
from backend.agents.analysis_agent import AnalysisAgent
from backend.agents.planning_agent import PlanningAgent
from backend.agents.coding_agent import CodingAgent
from backend.agents.qa_agent import QAAgent
from backend.agents.delivery_agent import DeliveryAgent
from backend.agents.supervisor_agent import SupervisorAgent
from backend.events import event_bus
from backend.performance import performance_recorder

def create_workflow():
    router = ModelRouter()
    analysis_agent = AnalysisAgent(router)
    planning_agent = PlanningAgent(router)
    coding_agent = CodingAgent(router)
    qa_agent = QAAgent(router)
    delivery_agent = DeliveryAgent()
    supervisor = SupervisorAgent()

    workflow = StateGraph(ProjectState)

    def wrap_node(agent_name, func):
        def wrapper(state: ProjectState) -> ProjectState:
            event_bus.emit_sync("AGENT_STARTED", {"project_id": state.project_id, "agent": agent_name})
            performance_recorder.record("agent_started", project_id=state.project_id, agent=agent_name)
            span_start = __import__("time").perf_counter()
            previous_error_count = len(state.errors)
            new_state = func(state)
            try:
                from backend.api.projects import projects_db
                projects_db[new_state.project_id] = new_state
            except Exception:
                pass
            failed = len(new_state.errors) > previous_error_count or new_state.workflow_status == "failed"
            performance_recorder.record(
                "agent_completed" if not failed else "agent_failed",
                project_id=new_state.project_id,
                agent=agent_name,
                duration_seconds=__import__("time").perf_counter() - span_start,
                errors=new_state.errors[previous_error_count:] if failed else [],
            )
            event_bus.emit_sync(
                "AGENT_FAILED" if failed else "AGENT_COMPLETED",
                {
                    "project_id": new_state.project_id,
                    "agent": agent_name,
                    "errors": new_state.errors[previous_error_count:] if failed else [],
                },
            )
            return new_state
        return wrapper

    # Add nodes
    workflow.add_node("Supervisor", wrap_node("SupervisorAgent", supervisor.process))
    workflow.add_node("AnalysisAgent", wrap_node("AnalysisAgent", analysis_agent.process))
    workflow.add_node("PlanningAgent", wrap_node("PlanningAgent", planning_agent.process))
    
    # Note: QAAgent expects process(state, task_id), but LangGraph nodes take just `state`.
    def qa_node(state: ProjectState) -> ProjectState:
        return qa_agent.process(state, state.current_task)
    
    workflow.add_node("QAAgent", wrap_node("QAAgent", qa_node))
    
    # Note: CodingAgent expects process(state, task_id)
    def coding_node(state: ProjectState) -> ProjectState:
        return coding_agent.process(state, state.current_task)
    
    workflow.add_node("CodingAgent", wrap_node("CodingAgent", coding_node))
    workflow.add_node("DeliveryAgent", wrap_node("DeliveryAgent", delivery_agent.process))

    # Edge routing logic
    def router_logic(state: ProjectState):
        if state.current_agent == "END":
            return END
        return state.current_agent

    # Connections
    workflow.set_entry_point("Supervisor")
    
    workflow.add_conditional_edges(
        "Supervisor",
        router_logic,
        {
            "AnalysisAgent": "AnalysisAgent",
            "PlanningAgent": "PlanningAgent",
            "CodingAgent": "CodingAgent",
            "QAAgent": "QAAgent",
            "DeliveryAgent": "DeliveryAgent",
            END: END
        }
    )

    # Agents return control to the Supervisor
    workflow.add_edge("AnalysisAgent", "Supervisor")
    workflow.add_edge("PlanningAgent", "Supervisor")
    workflow.add_edge("CodingAgent", "Supervisor")
    workflow.add_edge("QAAgent", "Supervisor")
    workflow.add_edge("DeliveryAgent", "Supervisor")

    return workflow.compile()
