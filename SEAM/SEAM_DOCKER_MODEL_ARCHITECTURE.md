# SEAM v1.0.0 — Docker Model Architecture & Containerized Inference Specification

**Project:** SEAM (Self-Evolving Autonomous Multi-Agent Framework)  
**Roles:** Principal Docker Engineer, Principal AI/LLM Engineer, Principal Systems Architect  
**Docker Engine:** Version 29.8.2  
**Docker Compose:** Version 5.5.1  
**Target Provider:** Docker Model Runner (OpenAI REST Compatible)  

---

## 1. Architectural Overview & Provider Abstraction

SEAM establishes a strict architectural boundary: **Docker Model Runner is an inference provider, NOT a replacement for the orchestration layer**. 

The system isolates model execution behind a unified `ModelRouter` interface, decoupling the 6 canonical agents from physical inference engines:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   SEAM AGENTIC EXECUTION LAYER                         │
│  [Analysis]   [Planning]   [Supervisor]   [Coding]   [QA]   [Delivery] │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      SEAM MODEL ROUTER ENGINE                          │
│               (backend/llm/model_router.py)                            │
│  - Task-Based Dynamic Routing     - Latency & Token Telemetry          │
│  - Structured Fallback Policy     - MODEL_FALLBACK_TRIGGERED Events    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│ Docker Model  │           │ Ollama Local  │           │ Enterprise    │
│ Runner        │           │ Engine        │           │ Cloud Gateway │
│ (Port 12434/  │           │ (Port 11434)  │           │ (vLLM / OAI)  │
│  12435)       │           │               │           │               │
└───────┬───────┘           └───────┬───────┘           └───────┬───────┘
        │                           │                           │
        ▼                           ▼                           ▼
  OpenAI Compat               Ollama API                  HTTPS / TLS
  /v1/chat/completions        /api/generate               /v1/chat/completions
  /v1/models                  /api/tags                   /v1/models
```

---

## 2. Docker Model Runner Daemon Specification

Docker Desktop v29.8.2 incorporates an integrated AI inference daemon (`com.docker.backend.exe`), exposing OpenAI-compatible endpoints directly on the host interface.

### Endpoints Verified via Live HTTP Probing:
1. **Engine Version:** `GET http://127.0.0.1:12434/version`
   - **Response:** HTTP 200 `v1.2.8`
2. **Model Catalog:** `GET http://127.0.0.1:12434/v1/models`
   - **Response:** HTTP 200 `{"object": "list", "data": []}`
3. **Inference Execution:** `POST http://127.0.0.1:12434/v1/chat/completions`
   - **Response:** HTTP 404 (Model unpulled error format compliant with OpenAI spec).

---

## 3. TCP Port 12434 Conflict & Multi-Port Resolution

### Forensic Discovery:
During setup, running a secondary Docker Model Runner container failed with a port binding conflict. Investigation via `netstat -ano | findstr :12434` identified PID 18348 (`com.docker.backend.exe`). Docker Desktop's native service had already bound to TCP port 12434.

### Decoupled Dual-Port Architecture:
SEAM resolves this conflict by parameterizing the endpoint in `backend/config.py`:
- **Mode A (Native Docker Desktop Daemon):** Connects directly to `http://localhost:12434`.
- **Mode B (Standalone Containerized Runner):** When running an isolated container from Docker Hub, port forwarding maps host port `12435` to container port `12434`:
  ```bash
  docker run -d --name seam-model-runner -p 12435:12434 --memory=8g docker/model-runner:latest
  ```
  SEAM routes to `http://localhost:12435` via `DOCKER_MODEL_RUNNER_ALT_URL`.

---

## 4. LangChain Integration Model

The integration is implemented through LangChain's `ChatOpenAI` wrapper:

```python
from langchain_openai import ChatOpenAI
from backend.config import settings

class DockerModelRunnerProvider:
    """OpenAI-compatible client pointing to Docker Model Runner."""

    @staticmethod
    def create_chat_client(model_name: str, temperature: float = 0.2) -> ChatOpenAI:
        base_url = f"{settings.DOCKER_MODEL_RUNNER_BASE_URL.rstrip('/')}/v1"
        return ChatOpenAI(
            model=model_name,
            base_url=base_url,
            api_key="docker-model-runner",
            temperature=temperature,
            timeout=120.0,
            max_retries=2,
        )
```

---

## 5. Security & Resource Confinement

1. **Host Memory Boundaries:** Container configurations enforce `--memory=12g` and `--memory-swap=12g` to prevent host OOM on 16GB development environments.
2. **Localhost Confinement:** Docker daemon bindings are restricted to `127.0.0.1`, preventing unauthorized external network access to local LLM inference.
3. **Health Check Probing:** FastAPI periodically pings `/version` and `/v1/models`. If Docker Model Runner is down, SEAM marks the provider as `UNAVAILABLE` and transparently routes to Ollama.
