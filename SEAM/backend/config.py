
import os
import sys
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DOCKER_MODEL_RUNNER_BASE_URL = os.getenv("SEAM_DMR_BASE_URL", os.getenv("DOCKER_MODEL_RUNNER_BASE_URL", "http://localhost:12434"))
SEAM_DMR_PORT = int(os.getenv("SEAM_DMR_PORT", "12434"))
SEAM_LLM_PROVIDER = os.getenv("SEAM_LLM_PROVIDER", "ollama")
SEAM_LLM_MODEL = os.getenv("SEAM_LLM_MODEL", "qwen3-coder-next")

# Model Configuration
SEAM_CODING_MODEL = os.getenv("SEAM_CODING_MODEL", SEAM_LLM_MODEL)
SEAM_ANALYSIS_MODEL = os.getenv("SEAM_ANALYSIS_MODEL", SEAM_LLM_MODEL)
SEAM_PLANNING_MODEL = os.getenv("SEAM_PLANNING_MODEL", SEAM_LLM_MODEL)
SEAM_QA_MODEL = os.getenv("SEAM_QA_MODEL", SEAM_LLM_MODEL)
SEAM_FAST_MODEL = os.getenv("SEAM_FAST_MODEL", SEAM_ANALYSIS_MODEL)

# Docker Model Runner Specific Configurations
SEAM_DOCKER_CODING_MODEL = os.getenv("SEAM_DOCKER_CODING_MODEL", "ai/qwen3-coder")
SEAM_DOCKER_HIGH_TIER_MODEL = os.getenv("SEAM_DOCKER_HIGH_TIER_MODEL", "ai/qwen3.8-flash-next")
SEAM_DOCKER_ANALYSIS_MODEL = os.getenv("SEAM_DOCKER_ANALYSIS_MODEL", "ai/gpt-oss")
SEAM_DOCKER_PLANNING_MODEL = os.getenv("SEAM_DOCKER_PLANNING_MODEL", "ai/gpt-oss")
SEAM_DOCKER_QA_MODEL = os.getenv("SEAM_DOCKER_QA_MODEL", "ai/devstral-small-2")

SEAM_HIGH_TIER_MODEL = os.getenv("SEAM_HIGH_TIER_MODEL", "ai/qwen3.8-flash-next")
SEAM_LOCAL_MODEL = os.getenv("SEAM_LOCAL_MODEL", "ai/qwen3:4b-instruct-2507-q4_K_M")
SEAM_LOCAL_MODEL_NAME = "Qwen3 4B Instruct Q4_K_M"
SEAM_DOCKER_FALLBACK_MODEL = os.getenv("SEAM_DOCKER_FALLBACK_MODEL", SEAM_LOCAL_MODEL)
SEAM_FALLBACK_MODEL = os.getenv("SEAM_FALLBACK_MODEL", SEAM_LOCAL_MODEL)
SEAM_LEGACY_MODEL = os.getenv("SEAM_LEGACY_MODEL", "qwen2.5-coder:7b")
MODEL_REQUEST_TIMEOUT = int(os.getenv("SEAM_MODEL_REQUEST_TIMEOUT", "180"))
WORKFLOW_TIMEOUT_SECONDS = int(os.getenv("SEAM_WORKFLOW_TIMEOUT_SECONDS", "1200"))
GITHUB_TIMEOUT_SECONDS = int(os.getenv("SEAM_GITHUB_TIMEOUT_SECONDS", "8"))
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")
GITHUB_INTELLIGENCE_DIR = os.getenv("SEAM_GITHUB_INTELLIGENCE_DIR", os.path.join(".seam", "github_intelligence"))
RAG_TIMEOUT_SECONDS = int(os.getenv("SEAM_RAG_TIMEOUT_SECONDS", "20"))
DIAGRAM_TIMEOUT_SECONDS = int(os.getenv("SEAM_DIAGRAM_TIMEOUT_SECONDS", "240"))

CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")

# RAG Configuration
SEAM_RAG_MODE = os.getenv("SEAM_RAG_MODE", "REAL") # REAL or TEST
SEAM_EMBEDDING_MODEL = os.getenv("SEAM_EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")

# Persistence Configuration
SEAM_DATABASE_BACKEND = os.getenv("SEAM_DATABASE_BACKEND", "sqlite").lower()
SEAM_SQLITE_PATH = os.getenv("SEAM_SQLITE_PATH", "")
SEAM_POSTGRESQL_URL = os.getenv("SEAM_POSTGRESQL_URL", os.getenv("DATABASE_URL", ""))
SEAM_REDIS_URL = os.getenv("SEAM_REDIS_URL", os.getenv("REDIS_URL", "redis://localhost:6379/0"))

# Figma Configuration
FIGMA_ACCESS_TOKEN = os.getenv("FIGMA_ACCESS_TOKEN", "")
if not FIGMA_ACCESS_TOKEN and sys.platform == "win32":
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as _k:
            _val, _ = winreg.QueryValueEx(_k, "FIGMA_ACCESS_TOKEN")
            if _val:
                FIGMA_ACCESS_TOKEN = _val
                os.environ["FIGMA_ACCESS_TOKEN"] = _val
    except Exception:
        pass
FIGMA_SEAM_FILE_KEY = os.getenv("FIGMA_SEAM_FILE_KEY", "")

# Docker Model Runner Image Generation Configuration (Phase 5)
DMR_BASE_URL = os.getenv("DMR_BASE_URL", DOCKER_MODEL_RUNNER_BASE_URL)
SEAM_SDXL_MODEL = os.getenv("SEAM_SDXL_MODEL", "ai/stable-diffusion")
SEAM_IMAGE_TIMEOUT_SECONDS = int(os.getenv("SEAM_IMAGE_TIMEOUT_SECONDS", "180"))
SEAM_IMAGE_MAX_PROMPT_LENGTH = int(os.getenv("SEAM_IMAGE_MAX_PROMPT_LENGTH", "1000"))
