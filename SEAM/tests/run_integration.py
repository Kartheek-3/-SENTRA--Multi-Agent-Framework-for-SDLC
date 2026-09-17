import os
import json
import asyncio
from backend.models.state import ProjectState
from backend.llm.model_router import ModelRouter
from backend.agents.analysis_agent import AnalysisAgent

def main():
    print("Running integration test against Ollama...")
    
    requirement = "Build an e-commerce application where users can register, login, browse products, add products to a cart, place orders, and make payments."
    
    state = ProjectState(project_id="int-test-1", user_requirement=requirement)
    router = ModelRouter()
    agent = AnalysisAgent(router)
    
    new_state = agent.process(state)
    
    if new_state.structured_requirements:
        print("\nSUCCESS! Parsed Output:")
        # Print nicely formatted
        print(new_state.structured_requirements.model_dump_json(indent=2))
        print("\nDomain mapped to state:", new_state.domain)
    else:
        print("\nFAILED!")
        for err in new_state.errors:
            print(err)

if __name__ == "__main__":
    main()
