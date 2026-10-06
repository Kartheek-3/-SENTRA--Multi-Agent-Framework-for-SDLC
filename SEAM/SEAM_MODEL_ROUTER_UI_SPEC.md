# SEAM v1.0.0 — Model Router UI & Inference Control Specification

**Project:** SEAM (Self-Evolving Autonomous Multi-Agent Framework)  
**Roles:** Principal AI/LLM Engineer, Principal UI/UX Designer, Senior Agentic AI Engineer  
**Status:** **ACTIVE SPECIFICATION & IMPLEMENTED IN FRONTEND**

---

## 1. Transparency & Trust Principles

In autonomous engineering systems, **the engineer must always know which model is executing their code**. 

### Core Inference Rules:
1. **Never Silently Switch Models:** If a model fails or is unpulled, the system transparently logs a `MODEL_FALLBACK_TRIGGERED` event with the reason, requested model, and fallback model.
2. **Real-Time Telemetry:** The UI displays the provider (`docker`, `ollama`, `cloud`), latency in milliseconds, token counts, and completion status.
3. **Hardware-Grounding:** The UI explicitly flags high-parameter models ($\ge$30B) as `BLOCKED (RAM)` on machines with $\le$16 GB RAM without discrete GPUs.

---

## 2. High-Tier Model Candidate: `ai/qwen3.8-flash-next`

SEAM integrates **`ai/qwen3.8-flash-next`** as a premier high-tier model candidate:

- **Context Window:** 128,000 tokens
- **Inference Speed:** Ultra-fast flash attention architecture
- **Strengths:** Rapid architectural decomposition, high-fidelity tool selection, low latency
- **Execution Policy:**
  - **Capable Hardware (>=24GB VRAM or High-Spec Workstation):** Recommended as default for Planning, Analysis, and Delivery.
  - **Constrained Hardware (15.6 GB RAM / CPU-Only Host):** Transparently falls back to verified local lightweight model **`qwen2.5-coder:1.5b`** (Ollama), running at ~28.3 tokens/second on CPU without swapping.
  - **Fallback Event Emission:** The backend emits a structured telemetry event, immediately reflected in the frontend Agent Cockpit:
    ```
    [TELEMETRY] MODEL_FALLBACK_TRIGGERED
    Requested: ai/qwen3.8-flash-next
    Actual:    qwen2.5-coder:1.5b
    Reason:    High-tier candidate requires GPU acceleration; local CPU fallback active.
    ```

---

## 3. Dynamic Task-Based Routing Architecture

SEAM's `ModelRouter` (`backend/llm/model_router.py`) maps canonical tasks to specialized models:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   TASK-BASED INFERENCE ROUTING TABLE                   │
└────────────────────────────────────────────────────────────────────────┘

 [AnalysisAgent]    ──► High-Tier:  ai/qwen3.8-flash-next
                         Fallback:   qwen2.5-coder:1.5b
                         Cloud:      gpt-oss:120b-cloud

 [PlanningAgent]    ──► High-Tier:  ai/qwen3.8-flash-next
                         Fallback:   qwen2.5-coder:1.5b
                         Cloud:      qwen3-coder:480b-cloud

 [SupervisorAgent]  ──► Agentic:    ai/devstral-small-2
                         Fallback:   qwen2.5-coder:1.5b
                         Cloud:      qwen3-coder:480b-cloud

 [CodingAgent]      ──► Primary:    qwen3-coder:30b
                         Fallback:   qwen2.5-coder:1.5b (Verified Local CPU)
                         Cloud:      qwen3-coder:480b-cloud

 [QAAgent]          ──► Primary:    qwen3-coder:30b
                         Fallback:   qwen2.5-coder:1.5b (Verified Local CPU)
                         Cloud:      qwen3-coder:480b-cloud

 [DeliveryAgent]    ──► High-Tier:  ai/qwen3.8-flash-next
                         Fallback:   qwen2.5-coder:1.5b
                         Cloud:      qwen3-coder:480b-cloud
```

---

## 4. UI Specification: Model Control Panel (`/models`)

The dedicated **Model Router** view in `seam-ide` provides 4 key zones:

1. **Active Engine Badge Bar:**
   - Displays active provider (`ollama` or `docker`), Docker Model Runner port probe (`12434` / `12435`), and Ollama daemon health (`11434`).
2. **Transparent Fallback Notice:**
   - Informational banner detailing fallback behavior, preventing silent model substitutions.
3. **Model Capability Cards Grid:**
   - Model title, provider badge, status (`AVAILABLE`, `RUNNING`, `BLOCKED (RAM)`, `NOT_CONFIGURED`), context window size, resource class, latency profile, tool-calling capability, and recommended agents.
4. **Interactive Routing Matrix Table:**
   - Full tabular breakdown mapping agents to candidate, local fallback, and cloud escalation tiers.
