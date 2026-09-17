import os
import json
from backend.models.state import ProjectState
from backend.llm.model_router import ModelRouter
from backend.agents.analysis_agent import AnalysisAgent
from backend.agents.planning_agent import PlanningAgent

def main():
    print("Running integration test for documentation and diagram generation...")
    
    requirement = "Build an e-commerce web application where users can register, log in, browse products, add products to a cart, place orders, and track their orders. Administrators should manage products and orders."
    
    state = ProjectState(project_id="ecommerce", user_requirement=requirement)
    router = ModelRouter()
    
    print("\n--- Running Analysis Agent ---")
    analysis_agent = AnalysisAgent(router)
    state = analysis_agent.process(state)
    
    print("\n====================================")
    print("ANALYSIS RESULT")
    print("====================================")
    if not state.structured_requirements:
        print("Analysis failed!")
        for err in state.errors:
            print(err)
        return
    print(f"Domain: {state.domain}")
    print(f"Entities: {len(state.structured_requirements.entities)}")
        
    print("\n--- Running Planning Agent ---")
    planning_agent = PlanningAgent(router)
    state = planning_agent.process(state)
    
    print("\n====================================")
    print("PLANNING RESULT")
    print("====================================")
    if not state.project_plan:
        print("Planning FAILED!")
        for err in state.errors:
            print(err)
    else:
        print("Planning SUCCESS!")
        print(f"Tasks Generated: {len(state.project_plan.tasks)}")
        
    print("\n====================================")
    print("RETRY INFORMATION")
    print("====================================")
    for h in state.execution_history:
        if h["agent"] == "PlanningAgent":
            print(f"Attempts: {h.get('attempts', 1)}")
            print(f"Initial Validation: {h.get('initial_validation', 'passed')}")
            print(f"Self Correction: {h.get('self_correction', 'N/A')}")
            print(f"Final Status: {h['status']}")

    artifacts = state.design_artifacts
    if artifacts:
        print("\n====================================")
        print("GENERATED DOCUMENTS")
        print("====================================")
        if artifacts.analysis_document_path:
            print(f"- {artifacts.analysis_document_path}")
        if artifacts.system_design_document_path:
            print(f"- {artifacts.system_design_document_path}")
            
        print("\n====================================")
        print("GENERATED DIAGRAMS")
        print("====================================")
        for path in artifacts.diagram_paths:
            print(f"- {path}")
            
    print("\n====================================")
    print("VALIDATION")
    print("====================================")
    print("Complete. Validation successful." if state.project_plan else "Failed validation.")

if __name__ == "__main__":
    main()
