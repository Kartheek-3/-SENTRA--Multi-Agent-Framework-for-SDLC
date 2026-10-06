# SEAM Model Runtime Policy & Hardware Confinement Specification

## 1. Executive Summary
SEAM v1.0.0 enforces strict runtime awareness, hardware-guided routing, and transparent execution fallback. Autonomous software engineering multi-agent workflows demand significant compute resources. High-tier candidates are preserved in the system architecture, but direct local execution is governed by verified host hardware capabilities to ensure stable local development without swapping or operating system memory exhaustion.

This document establishes the **Runtime-Aware Model Capability Detection and Fallback Policy** implemented in `backend/llm/hardware_detector.py` and `backend/llm/model_router.py`.

---

## 2. Hardware Classification Matrix

At application startup, `detect_runtime_hardware()` inspects host physical memory via Windows kernel APIs (`GlobalMemoryStatusEx`), CPU topology, and display adapter capabilities (`Win32_VideoController` via CIM):

| Profile | Hardware Thresholds | High-Tier Capability | Local Fallback Model | Runtime Engine |
| :--- | :--- | :--- | :--- | :--- |
| **`LOW_RESOURCE_CPU`** | Total RAM $\le$ 16GB, Integrated GPU (No CUDA GPU) | **NOT_AVAILABLE_ON_CURRENT_HARDWARE** | `ai/qwen3:4b-instruct-2507-q4_K_M` (Qwen3 4B Instruct Q4_K_M) | Docker Model Runner (Port 12434) |
| **`WORKSTATION`** | 32 GB – 64 GB RAM, Multi-core CPU ($\ge$16 cores) | Supported via CPU Quantization | `ai/qwen3-coder` / `qwen3:4b` | Docker Model Runner |
| **`GPU_WORKSTATION`** | Dedicated NVIDIA CUDA GPU, $\ge$8 GB VRAM | Supported with GPU Acceleration | `ai/qwen3-coder` | Docker Model Runner (CUDA) |
| **`HIGH_MEMORY_SERVER`**| $\ge$64 GB RAM, Multi-GPU Server | Native High-Tier Inference | `ai/qwen3.8-flash-next` | Docker Model Runner Cluster |
| **`CLOUD`** | External DMR Gateway or Cloud API | Bounded Network Latency (~2.8s) | `qwen3-coder:480b-cloud` | Cloud Gateway |

---

## 3. Current Host Hardware Verification

Live probing of the current development machine confirms:
- **CPU**: 13th Gen Intel(R) Core(TM) i7-13620H (16 logical processors)
- **RAM**: 16 GB installed (15.64 GB usable, 3200 MT/s)
- **GPU**: Intel(R) UHD Graphics (Integrated graphics)
- **Dedicated NVIDIA CUDA GPU**: None (`has_cuda = false`)
- **Classification**: **`LOW_RESOURCE_CPU`**

### Hardware Routing Constraint
High-tier local inference is disabled on this hardware because available system memory and the absence of a CUDA-capable GPU make it unsuitable for stable local execution. Requests automatically route to verified local model `ai/qwen3:4b-instruct-2507-q4_K_M`.

---

## 4. Local Model Configuration & Runtime Architecture

### Preferred Local Fallback
- **Model ID**: `ai/qwen3:4b-instruct-2507-q4_K_M`
- **Human-Readable Name**: Qwen3 4B Instruct Q4_K_M
- **Runtime**: Docker Model Runner (`http://127.0.0.1:12434`)
- **Quantization**: Q4_K_M (~2.50 GB memory footprint)
- **Configurable Environment Variables**:
  - `SEAM_LOCAL_MODEL=ai/qwen3:4b-instruct-2507-q4_K_M`
  - `SEAM_FALLBACK_MODEL=ai/qwen3:4b-instruct-2507-q4_K_M`
  - `SEAM_DMR_BASE_URL=http://127.0.0.1:12434`

### Model Routing Flow
```
High-tier model requested (ai/qwen3.8-flash-next)
        │
        ▼
Check hardware capability (detect_runtime_hardware)
        │
        ├──── capable ────► attempt high-tier execution
        │
        └──── not capable ──► DO NOT execute locally
                              │
                              ▼
                       Emit MODEL_FALLBACK_TRIGGERED
                              │
                              ▼
                       Qwen3 4B Q4_K_M (Docker Model Runner)
                              │
                              ▼
                       Local CPU inference
```

---

## 5. Tripartite Lifecycle & Fallback Telemetry

All inference invocations via `ModelRouter.execute_inference()` maintain structured lifecycle telemetry:
1. `MODEL_EXECUTION_STARTED`
2. `MODEL_FALLBACK_TRIGGERED` (when falling back from high-tier candidate)
3. `MODEL_EXECUTION_FAILED` (recorded for the oversized candidate on constrained hardware)
4. `MODEL_EXECUTION_COMPLETED` (recorded for the active fallback model)

### Fallback Telemetry Schema (`MODEL_FALLBACK_TRIGGERED`)
```json
{
  "event": "MODEL_FALLBACK_TRIGGERED",
  "task_type": "coding",
  "requested_model": "ai/qwen3.8-flash-next",
  "fallback_model": "ai/qwen3:4b-instruct-2507-q4_K_M",
  "provider": "docker",
  "reason": "HIGH_TIER_MODEL_NOT_SUPPORTED_ON_CURRENT_HARDWARE",
  "hardware_profile": "LOW_RESOURCE_CPU",
  "can_run_high_tier_locally": false,
  "latency": 120,
  "tokens": 35,
  "timestamp": "2026-10-06T05:47:00.000000"
}
```
*Security Guarantee: Telemetry payloads never expose credentials, authentication tokens, or private environment variables.*

---

## 6. Docker Model Runner Readiness & Availability

HTTP 200 from `GET /v1/models` is **NOT sufficient** to report inference readiness.
`ModelRouter.verify_local_model_readiness()` enforces real inference validation:
- If `ai/qwen3:4b-instruct-2507-q4_K_M` is missing from the runner store:
  - Reports: `LOCAL_MODEL_NOT_AVAILABLE`
  - Pull Command: `docker model pull ai/qwen3:4b-instruct-2507-q4_K_M`
- Only reports `PASS` after actual token generation from live model invocation.

---

## 7. Context & Memory Safety Defaults
Because the host has 15.6 GB RAM shared across Docker Desktop, IDE, FastAPI backend, React frontend, and OS services:
- Conservative context window defaults (32K max, standard prompts $\le$ 4K).
- Sequential inference queue: simultaneous high-tier and fallback execution is prohibited on this machine.
- Focus: **STABLE LOCAL DEVELOPMENT**.
