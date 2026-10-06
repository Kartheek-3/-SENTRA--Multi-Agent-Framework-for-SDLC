import datetime
import logging
import os
import requests
from typing import Any, Dict, List, Optional

from langchain_ollama import ChatOllama

from backend.config import (
    DOCKER_MODEL_RUNNER_BASE_URL,
    MODEL_REQUEST_TIMEOUT,
    OLLAMA_BASE_URL,
    SEAM_ANALYSIS_MODEL,
    SEAM_CODING_MODEL,
    SEAM_DOCKER_HIGH_TIER_MODEL,
    SEAM_FALLBACK_MODEL,
    SEAM_FAST_MODEL,
    SEAM_HIGH_TIER_MODEL,
    SEAM_LEGACY_MODEL,
    SEAM_LLM_MODEL,
    SEAM_LLM_PROVIDER,
    SEAM_LOCAL_MODEL,
    SEAM_LOCAL_MODEL_NAME,
    SEAM_PLANNING_MODEL,
    SEAM_QA_MODEL,
)
from backend.llm.hardware_detector import detect_runtime_hardware

logger = logging.getLogger(__name__)


class ModelRouter:
    """Provider-agnostic LLM Model Router for SEAM.
    
    Supports Docker Model Runner (OpenAI-compatible) and Ollama with
    runtime-aware hardware capability detection, fallback tracking, and health probing.
    """

    def __init__(self, provider: Optional[str] = None):
        self.provider = (provider or SEAM_LLM_PROVIDER).lower()
        self.ollama_base_url = OLLAMA_BASE_URL
        self.dmr_base_url = DOCKER_MODEL_RUNNER_BASE_URL
        self.hardware_profile = detect_runtime_hardware()
        self.available_models = self._fetch_available_models()
        self.active_models: Dict[str, Dict[str, Any]] = {}
        self.execution_history: List[Dict[str, Any]] = []

    def _fetch_available_models(self) -> List[str]:
        if self.provider == "docker":
            return self._fetch_docker_models()
        return self._fetch_ollama_models()

    def _fetch_ollama_models(self) -> List[str]:
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
            response.raise_for_status()
            data = response.json()
            models = data.get("models", [])
            return [m.get("name", "") for m in models if m.get("name")]
        except Exception as e:
            logger.debug(f"Failed to fetch models from Ollama: {e}")
            return []

    def _fetch_docker_models(self) -> List[str]:
        try:
            response = requests.get(f"{self.dmr_base_url}/v1/models", timeout=5)
            response.raise_for_status()
            data = response.json()
            models = data.get("data", [])
            model_ids = []
            for m in models:
                mid = m.get("id", "")
                if mid:
                    model_ids.append(mid)
                    if mid.startswith("docker.io/"):
                        model_ids.append(mid[len("docker.io/"):])
            return list(dict.fromkeys(model_ids))
        except Exception as e:
            logger.debug(f"Failed to fetch models from Docker Model Runner: {e}")
            return []

    def model_available(self, model_name: str) -> bool:
        clean_name = model_name[len("docker.io/"):] if model_name.startswith("docker.io/") else model_name
        for m in self.available_models:
            m_clean = m[len("docker.io/"):] if m.startswith("docker.io/") else m
            if clean_name == m_clean or f"{clean_name}:latest" == m_clean or clean_name == f"{m_clean}:latest":
                return True
            if model_name == m or f"{model_name}:latest" == m:
                return True
        return False

    def probe_dmr_health(self) -> Dict[str, Any]:
        """Probes the live Docker Model Runner server."""
        health_info: Dict[str, Any] = {
            "available": False,
            "base_url": self.dmr_base_url,
            "version": None,
            "models": [],
        }
        try:
            ver_resp = requests.get(f"{self.dmr_base_url}/version", timeout=3)
            if ver_resp.status_code == 200:
                health_info["available"] = True
                health_info["version"] = ver_resp.json().get("version")
            models_resp = requests.get(f"{self.dmr_base_url}/v1/models", timeout=3)
            if models_resp.status_code == 200:
                data = models_resp.json()
                raw_models = [m.get("id", "") for m in data.get("data", [])]
                all_ids = []
                for m in raw_models:
                    if m:
                        all_ids.append(m)
                        if m.startswith("docker.io/"):
                            all_ids.append(m[len("docker.io/"):])
                health_info["models"] = list(dict.fromkeys(all_ids))
        except Exception as exc:
            health_info["error"] = str(exc)
        return health_info

    def probe_ollama_health(self) -> Dict[str, Any]:
        """Probes the live Ollama server."""
        health_info: Dict[str, Any] = {
            "available": False,
            "base_url": self.ollama_base_url,
            "version": None,
            "models": [],
        }
        try:
            ver_resp = requests.get(f"{self.ollama_base_url}/api/version", timeout=3)
            if ver_resp.status_code == 200:
                health_info["available"] = True
                health_info["version"] = ver_resp.json().get("version")
            tags_resp = requests.get(f"{self.ollama_base_url}/api/tags", timeout=3)
            if tags_resp.status_code == 200:
                data = tags_resp.json()
                health_info["models"] = [m.get("name", "") for m in data.get("models", [])]
        except Exception as exc:
            health_info["error"] = str(exc)
        return health_info

    def health(self) -> Dict[str, Any]:
        ollama_available = bool(self._fetch_ollama_models()) if self.provider != "ollama" else bool(self.available_models)
        dmr_health = self.probe_dmr_health()

        configured = {
            "provider": self.provider,
            "primary_model": SEAM_LLM_MODEL,
            "coding": SEAM_CODING_MODEL,
            "analysis": SEAM_ANALYSIS_MODEL,
            "planning": SEAM_PLANNING_MODEL,
            "qa": SEAM_QA_MODEL,
            "fast": SEAM_FAST_MODEL,
            "high_tier": SEAM_DOCKER_HIGH_TIER_MODEL if self.provider == "docker" else SEAM_HIGH_TIER_MODEL,
            "fallback": SEAM_FALLBACK_MODEL,
            "legacy": SEAM_LEGACY_MODEL,
        }
        can_run_high_tier = self.hardware_profile.get("can_run_high_tier_locally", False)
        high_tier_in_runner = self.model_available("ai/qwen3.8-flash-next") or self.model_available("qwen3.8-flash-next")
        high_tier_status = "VERIFIED" if high_tier_in_runner else ("NOT_AVAILABLE_ON_CURRENT_HARDWARE" if not can_run_high_tier else "NOT_CONFIGURED")

        local_model = self.hardware_profile.get("recommended_local_model", SEAM_LOCAL_MODEL)
        local_in_dmr = local_model in dmr_health.get("models", []) or f"docker.io/{local_model}" in dmr_health.get("models", [])
        local_available = self.model_available(local_model) or local_in_dmr
        local_status = "VERIFIED" if local_available else "LOCAL_MODEL_NOT_AVAILABLE"

        return {
            "provider": self.provider,
            "primary_model": SEAM_LLM_MODEL,
            "high_tier_model": SEAM_DOCKER_HIGH_TIER_MODEL if self.provider == "docker" else SEAM_HIGH_TIER_MODEL,
            "high_tier_inference_status": high_tier_status,
            "local_fallback_model": local_model,
            "local_fallback_status": local_status,
            "local_model_pull_command": f"docker model pull {local_model}",
            "hardware_profile": self.hardware_profile,
            "ollama_base_url": self.ollama_base_url,
            "ollama_available": ollama_available,
            "docker_model_runner_base_url": self.dmr_base_url,
            "docker_model_runner_available": dmr_health["available"],
            "docker_model_runner_version": dmr_health.get("version"),
            "configured": configured,
            "available_models": self.available_models,
            "qwen3_coder_next_available": self.model_available("qwen3-coder-next"),
            "qwen3_8_flash_next_available": high_tier_in_runner,
            "qwen3_4b_available": local_available,
            "primary_model_available": self.model_available(SEAM_LLM_MODEL),
        }

    def verify_local_model_readiness(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Verifies actual inference execution on the local fallback model in Docker Model Runner.
        
        HTTP 200 from /v1/models is NOT sufficient to report inference readiness.
        If model is missing from DMR or pull is incomplete, reports LOCAL_MODEL_NOT_AVAILABLE
        and provides the exact pull command.
        Only reports PASS when actual tokens are generated via real inference.
        """
        target_model = model_name or self.hardware_profile.get("recommended_local_model", SEAM_LOCAL_MODEL)
        pull_cmd = f"docker model pull {target_model}"

        # 1. Check Docker Model Runner server reachability
        dmr_health = self.probe_dmr_health()
        if not dmr_health.get("available", False):
            return {
                "status": "LOCAL_MODEL_NOT_AVAILABLE",
                "model": target_model,
                "readiness": "NOT_AVAILABLE",
                "reason": f"Docker Model Runner endpoint {self.dmr_base_url} is unreachable.",
                "pull_command": pull_cmd,
                "inference_verified": False,
            }

        # 2. Check if model is listed in runner's available models
        docker_models = self._fetch_docker_models()
        if target_model not in docker_models and f"{target_model}:latest" not in docker_models:
            return {
                "status": "LOCAL_MODEL_NOT_AVAILABLE",
                "model": target_model,
                "readiness": "NOT_AVAILABLE",
                "reason": f"Model '{target_model}' is not loaded in Docker Model Runner.",
                "pull_command": pull_cmd,
                "inference_verified": False,
            }

        # 3. Perform real inference test (HTTP 200 from /v1/models is NOT sufficient)
        import time
        t0 = time.time()
        try:
            from langchain_openai import ChatOpenAI
            chat = ChatOpenAI(
                model=target_model,
                base_url=f"{self.dmr_base_url}/v1",
                api_key="dummy",
                temperature=0.1,
                max_tokens=20,
                timeout=MODEL_REQUEST_TIMEOUT,
            )
            response = chat.invoke("Ping")
            latency_ms = int((time.time() - t0) * 1000)
            content = response.content if hasattr(response, "content") else str(response)

            if not content or not content.strip():
                return {
                    "status": "INFERENCE_FAILED",
                    "model": target_model,
                    "readiness": "FAILED",
                    "reason": "Real inference returned empty response.",
                    "pull_command": pull_cmd,
                    "inference_verified": False,
                    "latency_ms": latency_ms,
                }

            return {
                "status": "PASS",
                "model": target_model,
                "readiness": "PASS",
                "reason": "Real inference verified successfully.",
                "pull_command": pull_cmd,
                "inference_verified": True,
                "latency_ms": latency_ms,
                "response_sample": content.strip()[:60],
            }
        except Exception as exc:
            latency_ms = int((time.time() - t0) * 1000)
            return {
                "status": "INFERENCE_FAILED",
                "model": target_model,
                "readiness": "FAILED",
                "reason": f"Real inference execution error: {str(exc)}",
                "pull_command": pull_cmd,
                "inference_verified": False,
                "latency_ms": latency_ms,
            }

    def verify_model_inference(self, model_name: Optional[str] = None, prompt: str = "Ping") -> Dict[str, Any]:
        """Convenience alias for verify_local_model_readiness."""
        return self.verify_local_model_readiness(model_name=model_name)

    def _get_safe_model_name(self, preferred_model: str, task_type: str) -> str:
        if preferred_model in self.available_models or f"{preferred_model}:latest" in self.available_models:
            return preferred_model

        # Hardware-aware fallback for high-tier model on constrained CPU host
        if preferred_model in ("ai/qwen3.8-flash-next", "qwen3.8-flash-next"):
            if not self.hardware_profile.get("can_run_high_tier_locally", False):
                fallback_target = self.hardware_profile.get("recommended_local_model", SEAM_LOCAL_MODEL)
                reason = "HIGH_TIER_MODEL_NOT_SUPPORTED_ON_CURRENT_HARDWARE"
                self._emit_fallback_event(task_type, preferred_model, fallback_target, reason)
                return fallback_target

        if self.provider == "docker":
            candidates = [f"ai/{preferred_model}", f"ai/{preferred_model.split(':')[0]}"]
            for cand in candidates:
                if cand in self.available_models or f"{cand}:latest" in self.available_models:
                    return cand

        logger.warning(f"Preferred model {preferred_model} not found. Trying fallback {SEAM_FALLBACK_MODEL}")
        fallback_target = None

        if SEAM_FALLBACK_MODEL in self.available_models or f"{SEAM_FALLBACK_MODEL}:latest" in self.available_models:
            fallback_target = SEAM_FALLBACK_MODEL
        elif SEAM_LEGACY_MODEL in self.available_models or f"{SEAM_LEGACY_MODEL}:latest" in self.available_models:
            logger.warning(f"Fallback model {SEAM_FALLBACK_MODEL} not found. Trying legacy {SEAM_LEGACY_MODEL}")
            fallback_target = SEAM_LEGACY_MODEL
        elif self.available_models:
            fallback_target = self.available_models[0]
        else:
            fallback_target = SEAM_LOCAL_MODEL

        if fallback_target:
            self._emit_fallback_event(task_type, preferred_model, fallback_target, f"Preferred model {preferred_model} not available in {self.provider}")
            return fallback_target

        logger.error(f"No suitable models found. Defaulting to {preferred_model}")
        return preferred_model

    def _emit_fallback_event(
        self,
        task_type: str,
        requested: str,
        actual: str,
        reason: str,
        latency: Optional[int] = None,
        tokens: Optional[int] = None,
    ) -> None:
        try:
            from backend.events import event_bus
            payload = {
                "event": "MODEL_FALLBACK_TRIGGERED",
                "task_type": task_type,
                "requested_model": requested,
                "fallback_model": actual,
                "actual_model": actual,
                "provider": self.provider,
                "reason": reason,
                "constraint_reason": reason,
                "hardware_profile": self.hardware_profile.get("profile", "LOW_RESOURCE_CPU"),
                "can_run_high_tier_locally": self.hardware_profile.get("can_run_high_tier_locally", False),
                "timestamp": datetime.datetime.now().isoformat(),
            }
            if latency is not None:
                payload["latency"] = latency
            if tokens is not None:
                payload["tokens"] = tokens
            event_bus.emit_sync("MODEL_FALLBACK_TRIGGERED", payload)
        except Exception as exc:
            logger.debug(f"Could not emit fallback event: {exc}")

    def record_execution(
        self,
        task_type: str,
        model: str,
        latency_ms: int,
        status: str = "success",
        context_length: Optional[int] = None,
        retry_count: int = 0,
        token_usage: Optional[Dict[str, int]] = None,
        error: Optional[str] = None,
        fallback_reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        record = {
            "provider": self.provider,
            "model": model,
            "task": task_type,
            "timestamp": datetime.datetime.now().isoformat(),
            "context_length": context_length,
            "latency_ms": latency_ms,
            "status": status,
            "retry_count": retry_count,
            "token_usage": token_usage or {},
            "error": error,
            "fallback_reason": fallback_reason,
        }
        self.execution_history.append(record)
        return record

    def get_model(self, task_type: str = "coding", provider: Optional[str] = None):
        """Resolves a LangChain Chat Model for the given task.
        
        task_type can be 'coding', 'analysis', 'planning', 'qa', 'fast', 'repair', 'delivery'.
        provider can explicitly override the default provider ('ollama', 'docker').
        """
        effective_provider = (provider or self.provider).lower()

        if effective_provider == "docker":
            from backend.config import (
                SEAM_DOCKER_ANALYSIS_MODEL,
                SEAM_DOCKER_CODING_MODEL,
                SEAM_DOCKER_PLANNING_MODEL,
                SEAM_DOCKER_QA_MODEL,
            )
            if task_type in ("analysis", "fast"):
                preferred = SEAM_DOCKER_ANALYSIS_MODEL
            elif task_type == "planning":
                preferred = SEAM_DOCKER_PLANNING_MODEL
            elif task_type == "qa":
                preferred = SEAM_DOCKER_QA_MODEL
            else:
                preferred = SEAM_DOCKER_CODING_MODEL
        else:
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

        actual_model = self._get_safe_model_name(preferred, task_type)
        fallback_used = actual_model != preferred

        self.active_models[task_type] = {
            "requested": preferred,
            "actual": actual_model,
            "fallback_used": fallback_used,
            "provider": effective_provider,
        }

        if effective_provider == "docker":
            try:
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(
                    model=actual_model,
                    base_url=f"{self.dmr_base_url}/v1",
                    api_key="dummy",
                    temperature=0.1,
                    timeout=MODEL_REQUEST_TIMEOUT,
                )
            except ImportError:
                logger.warning("langchain-openai not installed, falling back to ChatOllama")

        return ChatOllama(
            model=actual_model,
            base_url=self.ollama_base_url,
            temperature=0.1,
            timeout=MODEL_REQUEST_TIMEOUT,
        )

    def get_configured_model(self, task_type: str) -> str:
        if self.provider == "docker":
            from backend.config import (
                SEAM_DOCKER_ANALYSIS_MODEL,
                SEAM_DOCKER_CODING_MODEL,
                SEAM_DOCKER_PLANNING_MODEL,
                SEAM_DOCKER_QA_MODEL,
            )
            mapping = {
                "analysis": SEAM_DOCKER_ANALYSIS_MODEL,
                "planning": SEAM_DOCKER_PLANNING_MODEL,
                "qa": SEAM_DOCKER_QA_MODEL,
                "coding": SEAM_DOCKER_CODING_MODEL,
            }
            return mapping.get(task_type, SEAM_DOCKER_CODING_MODEL)
        else:
            mapping = {
                "analysis": SEAM_ANALYSIS_MODEL,
                "planning": SEAM_PLANNING_MODEL,
                "qa": SEAM_QA_MODEL,
                "coding": SEAM_CODING_MODEL,
                "fast": SEAM_FAST_MODEL,
            }
            return mapping.get(task_type, SEAM_CODING_MODEL)

    def execute_inference(self, task_type: str, prompt: str, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Executes a real or simulated model inference with lifecycle telemetry.
        
        Emits:
          - MODEL_EXECUTION_STARTED
          - MODEL_EXECUTION_COMPLETED
          - MODEL_EXECUTION_FAILED
          - MODEL_FALLBACK_TRIGGERED (when falling back from high-tier candidate)
        """
        import time
        import uuid
        correlation_id = str(uuid.uuid4())
        requested = model_name or self.get_configured_model(task_type)
        actual = self._get_safe_model_name(requested, task_type)

        from backend.events import event_bus
        event_bus.emit_sync("MODEL_EXECUTION_STARTED", {
            "correlation_id": correlation_id,
            "task_type": task_type,
            "requested_model": requested,
            "actual_model": actual,
            "provider": self.provider,
            "timestamp": datetime.datetime.now().isoformat(),
        })

        t0 = time.time()
        try:
            if actual != requested:
                event_bus.emit_sync("MODEL_EXECUTION_FAILED", {
                    "correlation_id": correlation_id,
                    "task_type": task_type,
                    "model": requested,
                    "error": f"High-tier model '{requested}' unavailable on current hardware ({self.hardware_profile.get('profile', 'UNKNOWN')})",
                    "fallback_target": actual,
                    "timestamp": datetime.datetime.now().isoformat(),
                })

            chat_model = self.get_model(task_type=task_type)
            res = chat_model.invoke(prompt)
            latency_ms = int((time.time() - t0) * 1000)
            content = res.content if hasattr(res, "content") else str(res)

            event_bus.emit_sync("MODEL_EXECUTION_COMPLETED", {
                "correlation_id": correlation_id,
                "task_type": task_type,
                "model": actual,
                "latency_ms": latency_ms,
                "status": "success",
                "timestamp": datetime.datetime.now().isoformat(),
            })

            record = self.record_execution(
                task_type=task_type,
                model=actual,
                latency_ms=latency_ms,
                status="success",
                fallback_reason=f"Fell back from {requested}" if actual != requested else None,
            )
            return {
                "status": "success",
                "correlation_id": correlation_id,
                "requested_model": requested,
                "actual_model": actual,
                "latency_ms": latency_ms,
                "response": content,
                "record": record,
            }
        except Exception as exc:
            latency_ms = int((time.time() - t0) * 1000)
            event_bus.emit_sync("MODEL_EXECUTION_FAILED", {
                "correlation_id": correlation_id,
                "task_type": task_type,
                "model": actual,
                "error": str(exc),
                "timestamp": datetime.datetime.now().isoformat(),
            })
            self.record_execution(
                task_type=task_type,
                model=actual,
                latency_ms=latency_ms,
                status="failed",
                error=str(exc),
            )
            return {
                "status": "failed",
                "correlation_id": correlation_id,
                "requested_model": requested,
                "actual_model": actual,
                "error": str(exc),
                "latency_ms": latency_ms,
            }
