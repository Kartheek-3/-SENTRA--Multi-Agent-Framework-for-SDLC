from backend.agents.supervisor_agent import SupervisorAgent
from backend.models.analysis import AnalysisResult, Requirement
from backend.models.planning import ProjectPlan, SystemDesign, Task
from backend.models.state import ProjectState


def test_supervisor_routes_failed_task_back_to_coding_for_langgraph_rework():
    failed_task = Task(task_id="T-001", title="Create API", status="failed")
    state = ProjectState(
        project_id="langgraph-rework",
        user_requirement="Build a small API",
        structured_requirements=AnalysisResult(
            project_summary="Small API",
            application_domain="general",
            functional_requirements=[Requirement(id="FR-001", description="Create API")],
            non_functional_requirements=[],
            actors=["User"],
            entities=["Item"],
            constraints=[],
            assumptions=[],
            risks=[],
            technical_considerations=[],
            ambiguities=[],
            recommended_capabilities=[],
        ),
        project_plan=ProjectPlan(
            project_overview="Small API",
            tasks=[failed_task],
            system_design=SystemDesign(architecture_style="REST API"),
        ),
        tasks={"T-001": failed_task},
        failed_tasks=["T-001"],
    )

    result = SupervisorAgent().process(state)

    assert result.current_agent == "CodingAgent"
    assert result.current_task == "T-001"
    assert result.tasks["T-001"].status == "in_progress"
    assert result.retry_count == 1
