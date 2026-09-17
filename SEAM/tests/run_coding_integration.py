import os
import shutil
from backend.models.state import ProjectState, DesignArtifacts
from backend.models.analysis import AnalysisResult, Requirement
from backend.models.planning import ProjectPlan, SystemDesign, Task, ArchitectureComponent, DatabaseEntity, APIEndpoint
from backend.agents.coding_agent import CodingAgent
from backend.llm.model_router import ModelRouter
from backend.utils import slugify

def setup_mock_plan():
    state = ProjectState(
        project_id="E-Commerce",
        user_requirement="Build a simple backend",
        domain="E-Commerce",
        design_artifacts=DesignArtifacts()
    )
    
    state.structured_requirements = AnalysisResult(
        project_summary="Simple E-commerce",
        application_domain="E-Commerce",
        functional_requirements=[Requirement(id="FR-001", description="Manage Products")],
        non_functional_requirements=[],
        actors=["User"],
        entities=["Product"],
        constraints=[],
        assumptions=[],
        risks=[],
        technical_considerations=[],
        ambiguities=[],
        recommended_capabilities=[]
    )
    
    state.project_plan = ProjectPlan(
        project_overview="Backend system",
        system_design=SystemDesign(
            architecture_style="RESTful API",
            components=[
                ArchitectureComponent(component_id="COMP-01", name="Database", responsibility="Storage"),
                ArchitectureComponent(component_id="COMP-02", name="API", responsibility="Endpoints")
            ],
            database_schema=[
                DatabaseEntity(name="Product", description="Product model", fields=["id", "name", "price"])
            ],
            api_endpoints=[
                APIEndpoint(method="GET", path="/products", purpose="List products")
            ],
            technology_stack=["Python", "FastAPI", "SQLite"],
            security_considerations=["No auth for now"]
        ),
        tasks=[],
        milestones=[]
    )
    
    # Task 1: DB Setup
    t1 = Task(task_id="TASK-001", title="Setup DB", description="Create the Product model and DB connection using SQLite and Python.", related_requirements=["FR-001"], dependencies=[])
    state.project_plan.tasks.append(t1)
    state.tasks[t1.task_id] = t1
    
    # Task 2: API Setup
    t2 = Task(task_id="TASK-002", title="Setup API", description="Create FastAPI app with /products GET endpoint.", related_requirements=["FR-001"], dependencies=["TASK-001"])
    state.project_plan.tasks.append(t2)
    state.tasks[t2.task_id] = t2
    
    return state

def main():
    print("Running integration test for CodingAgent...")
    
    proj_dir = os.path.join("generated_projects", slugify("E-Commerce"))
    if os.path.exists(proj_dir):
        shutil.rmtree(proj_dir)
        
    state = setup_mock_plan()
    router = ModelRouter()
    
    print("\n====================================")
    print("CODING AGENT - TASK-001")
    print("====================================")
    
    coding_agent = CodingAgent(router)
    state = coding_agent.process(state, "TASK-001")
    
    task1 = state.tasks["TASK-001"]
    if task1.status == "completed":
        print(f"Task TASK-001 Completed!")
        for file in task1.result.get("files", []):
            print(f"- Written: {file['path']}")
    else:
        print(f"Task TASK-001 Failed!")
        for err in state.errors:
            print(err)
        return
        
    print("\n====================================")
    print("CODING AGENT - TASK-002")
    print("====================================")
    
    state = coding_agent.process(state, "TASK-002")
    
    task2 = state.tasks["TASK-002"]
    if task2.status == "completed":
        print(f"Task TASK-002 Completed!")
        for file in task2.result.get("files", []):
            print(f"- Written: {file['path']}")
    else:
        print(f"Task TASK-002 Failed!")
        for err in state.errors:
            print(err)
            
    print("\n====================================")
    print("RETRY INFORMATION")
    print("====================================")
    for h in state.execution_history:
        if h["agent"] == "CodingAgent":
            print(f"Task ID: {h.get('task_id')}")
            print(f"Attempts: {h.get('attempts', 1)}")
            print(f"Initial Validation: {h.get('initial_validation', 'passed')}")
            print(f"Self Correction: {h.get('self_correction', 'N/A')}")
            print(f"Final Status: {h['status']}")
            print("---")
            
    print("\n====================================")
    print("VALIDATION")
    print("====================================")
    print("Integration complete.")

if __name__ == "__main__":
    main()
