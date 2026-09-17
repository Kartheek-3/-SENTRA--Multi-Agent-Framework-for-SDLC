import sys
import os
import time
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.graph.workflow import create_workflow
from backend.models.state import ProjectState
from backend.api.projects import projects_db
from backend.utils import slugify

REQUIREMENT = """
Build a production-quality e-commerce application with user registration, JWT authentication, product catalog, shopping cart, order management, PostgreSQL database, REST APIs, frontend, validation, testing and secure error handling.
"""

def inject_defect(project_id: str):
    print(">>> INJECTING SYNTAX DEFECT FOR QA LOOP VALIDATION <<<")
    project_dir = os.path.join("generated_projects", slugify(project_id))
    # Find any python file and inject a syntax error
    for root, _, files in os.walk(project_dir):
        for f in files:
            if f.endswith(".py"):
                filepath = os.path.join(root, f)
                with open(filepath, "a") as file:
                    file.write("\n\ndef injected_defect() this is invalid python syntax syntax_error\n")
                print(f"Defect injected into {filepath}")
                return
    print("Could not find a python file to inject defect.")

def run_validation():
    print("Starting SEAM Quality Validation Benchmark...")
    project_id = "benchmark_ecommerce"
    state = ProjectState(
        project_id=project_id,
        user_requirement=REQUIREMENT
    )
    
    projects_db[project_id] = state
    workflow = create_workflow()
    
    # We will use streaming to intercept the state and inject a defect after the first CodingAgent run
    defect_injected = False
    
    print("\nRunning workflow steps...")
    try:
        # Initial run
        current_state = state.model_dump()
        for output in workflow.stream(current_state):
            for node_name, state_snapshot in output.items():
                print(f"[{node_name}] completed.")
                current_state = state_snapshot
                
                # If CodingAgent just finished and we haven't injected a defect, inject it now
                if node_name == "CodingAgent" and not defect_injected:
                    inject_defect(project_id)
                    defect_injected = True
                    
        print("\nWorkflow execution finished.")
    except Exception as e:
        print(f"Workflow execution crashed: {e}")
        
    final_state = current_state
    
    # Analyze the result
    print("\n=== Validation Results ===")
    history = final_state.get("execution_history", [])
    
    qa_retries = len(final_state.get("qa_feedback", []))
    print(f"QA Feedback count (expected > 0 due to defect): {qa_retries}")
    
    delivery = final_state.get("delivery_result", {})
    if delivery:
        print(f"Delivery Status: {delivery.get('status')}")
    else:
        print("Delivery failed or did not complete.")
        
    print("\nBenchmark Script Completed.")

if __name__ == "__main__":
    run_validation()
