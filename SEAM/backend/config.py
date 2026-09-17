import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Model Configuration
SEAM_CODING_MODEL = os.getenv("SEAM_CODING_MODEL", "qwen3-coder-next")
SEAM_ANALYSIS_MODEL = os.getenv("SEAM_ANALYSIS_MODEL", "qwen3-coder-next")
SEAM_PLANNING_MODEL = os.getenv("SEAM_PLANNING_MODEL", "qwen3-coder-next")
SEAM_QA_MODEL = os.getenv("SEAM_QA_MODEL", "qwen3-coder-next")
SEAM_FAST_MODEL = os.getenv("SEAM_FAST_MODEL", SEAM_ANALYSIS_MODEL)

SEAM_FALLBACK_MODEL = os.getenv("SEAM_FALLBACK_MODEL", "qwen3-coder:30b")
SEAM_LEGACY_MODEL = os.getenv("SEAM_LEGACY_MODEL", "qwen2.5-coder:7b")
MODEL_REQUEST_TIMEOUT = int(os.getenv("SEAM_MODEL_REQUEST_TIMEOUT", "180"))
WORKFLOW_TIMEOUT_SECONDS = int(os.getenv("SEAM_WORKFLOW_TIMEOUT_SECONDS", "1200"))
GITHUB_TIMEOUT_SECONDS = int(os.getenv("SEAM_GITHUB_TIMEOUT_SECONDS", "8"))
RAG_TIMEOUT_SECONDS = int(os.getenv("SEAM_RAG_TIMEOUT_SECONDS", "20"))
DIAGRAM_TIMEOUT_SECONDS = int(os.getenv("SEAM_DIAGRAM_TIMEOUT_SECONDS", "240"))

CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")

# RAG Configuration
SEAM_RAG_MODE = os.getenv("SEAM_RAG_MODE", "TEST") # REAL or TEST
SEAM_EMBEDDING_MODEL = os.getenv("SEAM_EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
