from backend.graph.workflow import create_workflow


def test_langgraph_workflow_compiles():
    workflow = create_workflow()

    assert workflow is not None


def test_langgraph_contains_seam_agent_nodes():
    workflow = create_workflow()
    graph = workflow.get_graph()

    assert {"Supervisor", "AnalysisAgent", "PlanningAgent", "CodingAgent", "QAAgent", "DeliveryAgent"}.issubset(
        set(graph.nodes)
    )
