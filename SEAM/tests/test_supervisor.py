from backend.models.state import ProjectState
from backend.models.planning import Task, ProjectPlan, SystemDesign
from backend.agents.supervisor_agent import SupervisorAgent
from backend.models.analysis import AnalysisResult

def test_supervisor_routes_to_analysis():
    state = ProjectState(project_id="1", user_requirement="req")
    supervisor = SupervisorAgent()
    new_state = supervisor.process(state)
    assert new_state.current_agent == "AnalysisAgent"

def _mock_analysis_result():
    return AnalysisResult(
        project_summary="test",
        application_domain="test",
        functional_requirements=[],
        non_functional_requirements=[],
        actors=[],
        entities=[],
        constraints=[],
        assumptions=[],
        risks=[],
        technical_considerations=[],
        ambiguities=[],
        recommended_capabilities=[]
    )

def test_supervisor_routes_to_planning():
    state = ProjectState(project_id="1", user_requirement="req")
    state.structured_requirements = _mock_analysis_result()
    supervisor = SupervisorAgent()
    new_state = supervisor.process(state)
    assert new_state.current_agent == "PlanningAgent"

def test_supervisor_routes_to_task():
    state = ProjectState(project_id="1", user_requirement="req")
    state.structured_requirements = _mock_analysis_result()
    state.project_plan = ProjectPlan(
        project_overview="Overview",
        implementation_phases=[],
        tasks=[],
        milestones=[],
        system_design=SystemDesign(
            architecture_style="test",
            components=[],
            data_flow="",
            database_schema=[],
            api_endpoints=[],
            technology_stack=[],
            security_considerations=[]
        ),
        implementation_strategy="",
        risks_and_mitigations=[]
    )
    
    state.tasks["t1"] = Task(
        task_id="t1", 
        title="Test task",
        description="desc", 
        capability="Core",
        priority="High",
        estimated_complexity="Low",
        assigned_agent="CodingAgent"
    )
    
    supervisor = SupervisorAgent()
    new_state = supervisor.process(state)
    assert new_state.current_agent == "CodingAgent"
    assert new_state.current_task == "t1"
    assert new_state.tasks["t1"].status == "in_progress"
