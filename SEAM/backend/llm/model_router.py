import requests
from langchain_ollama import ChatOllama
import logging
from requests import Session

from backend.config import (
    OLLAMA_BASE_URL,
    SEAM_CODING_MODEL,
    SEAM_ANALYSIS_MODEL,
    SEAM_PLANNING_MODEL,
    SEAM_QA_MODEL,
    SEAM_FAST_MODEL,
    SEAM_FALLBACK_MODEL,
    SEAM_LEGACY_MODEL,
    MODEL_REQUEST_TIMEOUT,
)

logger = logging.getLogger(__name__)

class ModelRouter:
    _session = Session()

    def __init__(self):
        self.available_models = self._fetch_available_models()
        self.active_models = {}

    def _fetch_available_models(self):
        try:
            response = self._session.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
            response.raise_for_status()
            models = response.json().get("models", [])
            return [m["name"] for m in models]
        except Exception as e:
            logger.error(f"Failed to fetch models from Ollama: {e}")
            return []
            
    def _get_safe_model_name(self, preferred_model: str):
        if preferred_model in self.available_models or f"{preferred_model}:latest" in self.available_models:
            return preferred_model
            
        logger.warning(f"Preferred model {preferred_model} not found. Trying fallback {SEAM_FALLBACK_MODEL}")
        if SEAM_FALLBACK_MODEL in self.available_models or f"{SEAM_FALLBACK_MODEL}:latest" in self.available_models:
            return SEAM_FALLBACK_MODEL
            
        logger.warning(f"Fallback model {SEAM_FALLBACK_MODEL} not found. Trying legacy {SEAM_LEGACY_MODEL}")
        if SEAM_LEGACY_MODEL in self.available_models or f"{SEAM_LEGACY_MODEL}:latest" in self.available_models:
            return SEAM_LEGACY_MODEL
            
        # If none of the configured models are found, return the preferred one anyway and let it fail at generation
        logger.error(f"No suitable models found. Defaulting to {preferred_model}")
        return preferred_model

    def get_model(self, task_type: str = "coding"):
        """
        task_type can be 'coding', 'analysis', 'planning', 'qa'
        """
        if task_type == "fast":
            preferred = SEAM_FAST_MODEL
        elif task_type == "analysis":
            preferred = SEAM_ANALYSIS_MODEL
        elif task_type == "planning":
            preferred = SEAM_PLANNING_MODEL
        elif task_type == "qa":
            preferred = SEAM_QA_MODEL
        else:
            preferred = SEAM_CODING_MODEL
            
        actual_model = self._get_safe_model_name(preferred)
        self.active_models[task_type] = {
            "requested": preferred,
            "actual": actual_model,
            "fallback_used": actual_model != preferred
        }
        
        return ChatOllama(
            model=actual_model,
            base_url=OLLAMA_BASE_URL,
            temperature=0.1,
            timeout=MODEL_REQUEST_TIMEOUT,
        )
