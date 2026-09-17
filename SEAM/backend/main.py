from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api import agent_manager, artifacts, event_store, filesystem, knowledge, performance, projects, task_groups, workflow, ws

app = FastAPI(title="SEAM API")

# Add CORS for IDE integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)
app.include_router(agent_manager.router)
app.include_router(task_groups.router)
app.include_router(artifacts.router)
app.include_router(artifacts.registry_router)
app.include_router(event_store.router)
app.include_router(performance.router)
app.include_router(workflow.router)
app.include_router(ws.router)
app.include_router(knowledge.router)
app.include_router(filesystem.router)

@app.get("/")
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "SEAM"
    }

@app.get("/api/system/models")
def get_system_models():
    from backend.llm.model_router import ModelRouter
    from backend.config import (
        OLLAMA_BASE_URL,
        SEAM_CODING_MODEL,
        SEAM_ANALYSIS_MODEL,
        SEAM_PLANNING_MODEL,
        SEAM_QA_MODEL,
        SEAM_FALLBACK_MODEL
    )
    import requests
    
    ollama_status = "offline"
    try:
        res = requests.get(f"{OLLAMA_BASE_URL}/", timeout=2)
        if res.status_code == 200:
            ollama_status = "online"
    except Exception:
        pass
        
    router = ModelRouter()
    
    return {
        "ollama_status": ollama_status,
        "installed_models": router.available_models,
        "configured_coding_model": SEAM_CODING_MODEL,
        "configured_planning_model": SEAM_PLANNING_MODEL,
        "configured_qa_model": SEAM_QA_MODEL,
        "selected_fallback_model": SEAM_FALLBACK_MODEL,
        "active_session_models": router.active_models
    }

@app.get("/api/system/health")
def get_system_health():
    import os
    import requests
    from backend.config import OLLAMA_BASE_URL
    from backend.knowledge.knowledge_service import KnowledgeService

    ollama_status = "offline"
    try:
        res = requests.get(f"{OLLAMA_BASE_URL}/", timeout=2)
        if res.status_code == 200:
            ollama_status = "online"
    except Exception:
        pass

    rag_status = "unknown"
    try:
        KnowledgeService()
        rag_status = "online"
    except Exception:
        rag_status = "error"

    return {
        "backend": "online",
        "qwen": ollama_status,
        "rag": rag_status,
        "github": "configured" if os.getenv("GITHUB_TOKEN") else "token_missing",
    }
