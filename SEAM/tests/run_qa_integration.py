import os
import shutil
from backend.models.state import ProjectState, DesignArtifacts
from backend.models.analysis import AnalysisResult, Requirement
from backend.models.planning import ProjectPlan, SystemDesign, Task, ArchitectureComponent, DatabaseEntity, APIEndpoint
from backend.agents.qa_agent import QAAgent
from backend.llm.model_router import ModelRouter
from backend.utils import slugify

def setup_mock_qa_state():
    state = ProjectState(
        project_id="E-Commerce QA Test",
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
    
    t1 = Task(task_id="TASK-001", title="Setup DB", description="Create the Product model.", related_requirements=["FR-001"])
    t1.status = "completed"
    t1.result = {
        "files": [{"path": "backend/main.py", "content": "from pydantic import BaseModel\nclass Product(BaseModel):\n    id: int\n    name: str\n    price: float\n"}]
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
    print("Running integration test for QAAgent...")
    
    state = setup_mock_qa_state()
    router = ModelRouter()
    
    print("\n====================================")
    print("QA AGENT - TASK-001")
    print("====================================")
    
    qa_agent = QAAgent(router)
    state = qa_agent.process(state, "TASK-001")
    
    task1 = state.tasks["TASK-001"]
    qa_res = task1.result.get("qa_result", {})
    
    if task1.status == "completed":
        print(f"Task TASK-001 Passed QA!")
    else:
        print(f"Task TASK-001 Failed QA!")
        
    print(f"Status: {qa_res.get('status')}")
    print(f"Passed: {qa_res.get('passed')}")
    print(f"Issues:")
    for key in ['functional_issues', 'requirement_violations', 'architecture_violations', 'security_issues', 'syntax_errors']:
        for issue in qa_res.get(key, []):
            print(f"- [{key}] {issue}")
            
    print("\n====================================")
    print("RETRY INFORMATION")
    print("====================================")
    for h in state.execution_history:
        if h["agent"] == "QAAgent":
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
