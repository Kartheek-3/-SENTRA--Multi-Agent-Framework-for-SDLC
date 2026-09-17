import os
from backend.models.state import ProjectState, DesignArtifacts
from backend.models.analysis import AnalysisResult, Requirement
from backend.models.planning import ProjectPlan, SystemDesign, Task, ArchitectureComponent, DatabaseEntity, APIEndpoint
from backend.agents.delivery_agent import DeliveryAgent
from backend.utils import slugify

def setup_mock_delivery_state():
    state = ProjectState(
        project_id="E-Commerce Delivery Test",
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
    
    t1 = Task(task_id="TASK-001", title="Setup DB", description="Create the Product model.", related_requirements=["FR-001"])
    t1.status = "completed"
    t1.result = {
        "files": [{"path": "backend/main.py", "content": "print('Code')"}],
        "qa_result": {"status": "passed", "passed": True}
    }
    state.project_plan.tasks.append(t1)
    state.tasks[t1.task_id] = t1
    state.completed_tasks.append(t1.task_id)
    
    proj_dir = os.path.join("generated_projects", slugify(state.project_id))
    os.makedirs(os.path.join(proj_dir, "backend"), exist_ok=True)
    with open(os.path.join(proj_dir, "backend", "main.py"), "w", encoding="utf-8") as f:
        f.write(t1.result["files"][0]["content"])
        
    return state

def main():
    print("Running integration test for DeliveryAgent...")
    
    state = setup_mock_delivery_state()
    agent = DeliveryAgent()
    
    print("\n====================================")
    print("DELIVERY AGENT EXECUTION")
    print("====================================")
    
    state = agent.process(state)
    
    res = state.delivery_result
    
    if res and res.get("status") == "deployed":
        print(f"Delivery Passed!")
    else:
        print(f"Delivery Failed!")
        
    print(f"Status: {res.get('status')}")
    print(f"QA Verified: {res.get('qa_verified')}")
    print(f"Docs Generated: {res.get('documentation_generated')}")
    print(f"Package Created: {res.get('package_created')}")
    print(f"Deployment Status: {res.get('deployment_status')}")
    print(f"Knowledge Update: {res.get('knowledge_update_status')}")
    print(f"Errors: {res.get('errors')}")
    print(f"Artifact Paths:")
    for p in res.get('artifact_paths', []):
        print(f"- {p}")
            
    print("\n====================================")
    print("VALIDATION")
    print("====================================")
    print("Integration complete.")

if __name__ == "__main__":
    main()
