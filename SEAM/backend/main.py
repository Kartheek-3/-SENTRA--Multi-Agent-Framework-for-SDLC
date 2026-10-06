from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api import agent_manager, artifacts, event_store, experiments, filesystem, github, knowledge, n8n, performance, projects, rag, task_groups, workflow, ws

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
app.include_router(experiments.router)
app.include_router(performance.router)
app.include_router(workflow.router)
app.include_router(ws.router)
app.include_router(knowledge.router)
app.include_router(rag.router)
app.include_router(github.router)
app.include_router(filesystem.router)
app.include_router(n8n.router)

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
        SEAM_FALLBACK_MODEL,
        SEAM_LLM_PROVIDER,
        SEAM_LLM_MODEL,
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
        "llm_provider": SEAM_LLM_PROVIDER,
        "primary_model": SEAM_LLM_MODEL,
        "primary_model_available": router.model_available(SEAM_LLM_MODEL),
        "qwen3_coder_next_available": router.model_available("qwen3-coder-next"),
        "installed_models": router.available_models,
        "configured_coding_model": SEAM_CODING_MODEL,
        "configured_planning_model": SEAM_PLANNING_MODEL,
        "configured_qa_model": SEAM_QA_MODEL,
        "selected_fallback_model": SEAM_FALLBACK_MODEL,
        "local_fallback_model": SEAM_FALLBACK_MODEL,
        "local_fallback_name": "Qwen3 4B Instruct Q4_K_M",
        "qwen3_4b_available": router.health().get("qwen3_4b_available", False),
        "qwen3_4b_status": "PASS" if router.health().get("qwen3_4b_available", False) else "LOCAL_MODEL_NOT_AVAILABLE",
        "local_model_pull_command": f"docker model pull {SEAM_FALLBACK_MODEL}",
        "high_tier_model": "ai/qwen3.8-flash-next" if SEAM_LLM_PROVIDER == "docker" else "qwen3.8-flash-next",
        "qwen3_8_flash_next_available": router.model_available("ai/qwen3.8-flash-next") or router.model_available("qwen3.8-flash-next"),
        "docker_model_runner_available": router.probe_dmr_health().get("available", False),
        "docker_model_runner_base_url": router.dmr_base_url,
        "active_session_models": router.active_models
    }

@app.get("/api/system/models/verify-readiness")
def verify_system_model_readiness():
    from backend.llm.model_router import ModelRouter
    router = ModelRouter()
    return router.verify_local_model_readiness()

@app.get("/api/system/health")
def get_system_health():
    import os
    import requests
    from backend.config import OLLAMA_BASE_URL, SEAM_LLM_MODEL
    from backend.knowledge.knowledge_service import KnowledgeService
    from backend.llm.model_router import ModelRouter

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

    router = ModelRouter()

    from backend.database import db_engine
    db_val = db_engine.validate_connection()
    db_schema = db_engine.validate_schema()

    return {
        "backend": "online",
        "ollama": ollama_status,
        "qwen": "available" if router.model_available("qwen3-coder-next") else "unavailable",
        "primary_model": SEAM_LLM_MODEL,
        "primary_model_available": router.model_available(SEAM_LLM_MODEL),
        "llm": router.health(),
        "rag": rag_status,
        "github": "configured" if os.getenv("GITHUB_TOKEN") else "token_missing",
        "figma": "configured" if os.getenv("FIGMA_ACCESS_TOKEN") else "token_missing",
        "database": {
            "development": "SQLite (.seam/runtime/seam.db)",
            "production": "PostgreSQL",
            "active_backend": db_val["backend"],
            "status": db_val["status"],
            "url": db_val["url"],
            "writable": db_val["writable"],
            "schema_valid": db_schema.get("valid", False),
            "postgresql_live": "PASS" if (db_val["backend"] == "postgresql" and db_val["status"] == "PASS") else "NOT_CONFIGURED",
        },
    }
