import os
import sys

# Ensure backend can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.models.state import ProjectState
from backend.llm.model_router import ModelRouter
from backend.agents.analysis_agent import AnalysisAgent
from backend.agents.planning_agent import PlanningAgent
from backend.agents.supervisor_agent import SupervisorAgent

def run_real_llm_test(name, requirement):
    print(f"\n{'='*50}\nTEST: {name}\n{'='*50}")
    
    router = ModelRouter()
    analysis = AnalysisAgent(router)
    planning = PlanningAgent(router)
    
    state = ProjectState(project_id=f"test_{name.lower().replace(' ', '_')}", user_requirement=requirement)
    
    print("Running Analysis...")
    state = analysis.process(state)
    
    if state.structured_requirements and state.structured_requirements.scale_assessment:
        scale = state.structured_requirements.scale_assessment.scale_level.value
        print(f"-> ASSESSED SCALE: {scale}")
        for r in state.structured_requirements.scale_assessment.evidence:
            print(f"   Evidence: {r}")
    else:
        print("-> FAILED TO ASSESS SCALE")
        return
        
    print("Running Planning...")
    state = planning.process(state)
    
    if state.project_plan and state.project_plan.system_design:
        arch = state.project_plan.system_design.architecture_style
        print(f"-> ARCHITECTURE: {arch}")
        for d in state.project_plan.system_design.architecture_decisions:
            print(f"   Decision: {d.component} - {d.reason} (Complexity: {d.complexity})")
            
def test_scale_change():
    print(f"\n{'='*50}\nTEST: SCALE CHANGE\n{'='*50}")
    supervisor = SupervisorAgent()
    state = ProjectState(project_id="test_change", user_requirement="Small app")
    state.structured_requirements = "MOCK_DONE"
    state.project_plan = "MOCK_DONE"
    
    print("Initial State -> Supervisor evaluates")
    state = supervisor.process(state)
    print(f"Next Agent: {state.current_agent}")
    
    print("User changes requirement to 5 million users -> scale_changed = True")
    state.scale_changed = True
    
    state = supervisor.process(state)
    print(f"Next Agent: {state.current_agent} (Expected: AnalysisAgent)")
    print(f"Event Logged: {[h.get('event') for h in state.execution_history if 'event' in h]}")

if __name__ == "__main__":
    print("SEAM SCALE-AWARE ENGINEERING TESTS")
    
    req_small = "Build a student attendance application for 100 users."
    run_real_llm_test("SMALL", req_small)
    
    req_medium = "Multi-role business application with several modules, moderate traffic."
    run_real_llm_test("MEDIUM", req_medium)
    
    req_large = "Build a global payment platform serving millions of concurrent users with 99.99% availability."
    run_real_llm_test("LARGE / ENTERPRISE", req_large)
    
    req_anti = "Build a simple todo list app just for my own local computer."
    run_real_llm_test("ANTI-OVERENGINEERING", req_anti)
    
    test_scale_change()
    print("\nDONE.")
