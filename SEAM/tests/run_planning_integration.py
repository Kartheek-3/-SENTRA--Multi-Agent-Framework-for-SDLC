import os
import json
from backend.models.state import ProjectState
from backend.llm.model_router import ModelRouter
from backend.agents.analysis_agent import AnalysisAgent
from backend.agents.planning_agent import PlanningAgent

def main():
    print("Running integration test against Ollama...")
    
    requirement = "Build an e-commerce web application where users can register, log in, browse products, add products to a cart, place orders, and track their orders. Administrators should manage products and orders."
    
    state = ProjectState(project_id="int-test-2", user_requirement=requirement)
    router = ModelRouter()
    
    print("\n--- Running Analysis Agent ---")
    analysis_agent = AnalysisAgent(router)
    state = analysis_agent.process(state)
    
    if not state.structured_requirements:
        print("Analysis failed!")
        for err in state.errors:
            print(err)
        return
        
    print("\nAnalysis Result mapped domain:", state.domain)
    
    print("\n--- Running Planning Agent ---")
    planning_agent = PlanningAgent(router)
    state = planning_agent.process(state)
    
    if state.project_plan:
        print("\nSUCCESS! Parsed Planning Output:")
        print("\n=== SYSTEM ARCHITECTURE ===")
        print(state.project_plan.system_design.model_dump_json(indent=2))
        
        print("\n=== TASK DEPENDENCY GRAPH ===")
        for task in state.project_plan.tasks:
            deps = ", ".join(task.dependencies) if task.dependencies else "None"
            reqs = ", ".join(task.related_requirements) if task.related_requirements else "None"
            print(f"[{task.task_id}] {task.title}")
            print(f"  Requirements: {reqs}")
            print(f"  Depends on:   {deps}")
            print(f"  Capability:   {task.capability}")
    else:
        print("\nPlanning FAILED!")
        for err in state.errors:
            print(err)

if __name__ == "__main__":
    main()
