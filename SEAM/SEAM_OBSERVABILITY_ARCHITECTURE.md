# SEAM v1.0.0 — Observability Architecture & Production Telemetry Specification

**Project:** SEAM (Self-Evolving Autonomous Multi-Agent Framework)  
**Roles:** Principal Observability Engineer, Principal Backend Engineer, Principal DevSecOps Engineer  
**Date:** October 6, 2026  
**Status:** **ACTIVE SPECIFICATION**

---

## 1. Observability Governance Principle

SEAM is an autonomous software engineering engine. In autonomous systems, **observability is the foundation of trust**. 

### The Core Telemetry Rule:
> *"No fake dashboards. No simulated metrics. Every telemetry point, graph, and trace must stem from verifiable runtime events."*

Operators and developers must be able to observe at any moment:
- **WHAT** is executing (Task, Endpoint, or Verification step)
- **WHICH AGENT** is currently active (Analysis, Planning, Supervisor, Coding, QA, Delivery)
- **WHICH MODEL** is processing the request (Ollama, Docker Model Runner, Cloud)
- **WHICH TOOL** was selected and its execution duration
- **WHAT FAILED** and whether autonomous repair was triggered
- **LATENCY & TOKEN CONSUMPTION** across all multi-agent transitions

---

## 2. End-to-End Telemetry Pipeline

```
┌────────────────────────────────────────────────────────────────────────┐
│                      SEAM AGENTIC CORE PLATFORM                        │
│  FastAPI Endpoints   LangGraph State Graph   ToolExecutor   ChromaDB   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    │ (OpenTelemetry SDK Traces & Metrics)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     OPENTELEMETRY COLLECTOR                            │
│  - Trace sampling (W3C standard)  - Secret & token redaction filter    │
│  - Span enrichment (agent, model) - Correlation ID propagation         │
└───────────────────┬───────────────────────────────┬────────────────────┘
                    │                               │
       (Prometheus Scrapes /metrics)    (OTLP Traces via gRPC)
                    │                               │
                    ▼                               ▼
       ┌────────────────────────┐      ┌────────────────────────┐
       │   PROMETHEUS ENGINE    │      │    JAEGER / TEMPO      │
       │  Time-series storage   │      │   Distributed traces   │
       │  Alertmanager rules    │      │   Flamegraphs & spans  │
       └────────────┬───────────┘      └────────────┬───────────┘
                    │                               │
                    └───────────────┬───────────────┘
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │                  GRAFANA DASHBOARDS                    │
       │  - Agent Execution Board    - Model Latency & Tokens   │
       │  - Tool Failure Tracker     - Defect & Repair Metrics  │
       └────────────────────────────────────────────────────────┘
```

---

## 3. Metrics Catalog & Canonical Prometheus Gauges

SEAM instruments 8 dedicated metric families to track agentic performance:

### 1. HTTP & API Layer
- `http_requests_total{method, endpoint, status_code}`: Ingress traffic volume.
- `http_request_duration_seconds{method, endpoint}`: API response latency distribution.

### 2. Multi-Agent Orchestration Layer
- `seam_agent_executions_total{agent_name, status}`: Total agent invocations.
- `seam_agent_duration_seconds{agent_name}`: Time spent inside agent graph nodes.
- `seam_agent_active_gauge{agent_name}`: Currently active executing agents.

### 3. Tool Execution Layer
- `seam_tool_executions_total{tool_name, agent_name, risk_level}`: Tool usage frequency.
- `seam_tool_failures_total{tool_name, error_type}`: Failed tool invocations.
- `seam_tool_duration_seconds{tool_name}`: Tool execution latency (e.g., pytest, git, docker).

### 4. AI & Inference Layer
- `seam_model_tokens_total{provider, model, direction="prompt|completion"}`: Token consumption.
- `seam_model_inference_duration_seconds{provider, model}`: Raw inference response latency.
- `seam_model_fallback_total{requested_model, fallback_model, reason}`: Fallback event count.

### 5. Knowledge & RAG Layer
- `seam_rag_queries_total{collection_name}`: Total semantic search queries.
- `seam_rag_retrieval_duration_seconds{collection_name}`: Vector search latency.
- `seam_rag_documents_retrieved{collection_name}`: Chunk retrieval volume per query.

### 6. Autonomous Defect Repair Layer
- `seam_repairs_attempted_total`: Count of repair cycles initiated by Supervisor.
- `seam_repairs_resolved_total`: Defect tickets successfully resolved.
- `seam_repair_iterations_per_incident`: Number of patch iterations required to pass QA.

---

## 4. Structured Logging & Correlation ID Propagation

All backend log records follow a structured JSON schema:

```json
{
  "timestamp": "2026-10-06T00:55:00.123Z",
  "level": "INFO",
  "correlation_id": "corr-5547c99d-0544-4ab1",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "agent": "CodingAgent",
  "task_id": "task-scaffold-004",
  "provider": "docker",
  "model": "ai/qwen2.5-coder",
  "tool": "write_to_file",
  "message": "Generated source artifact backend/routes/auth.py",
  "duration_ms": 142.5
}
```

### Security Redaction Filter:
Logs and traces pass through an automated sanitizer that replaces patterns matching:
- Bearer tokens (`Bearer [REDACTED]`)
- API keys (`(?i)(api[_-]?key|secret|password)=([^&\s]+)` $\to$ `[REDACTED]`)
- Private cryptographic keys (`-----BEGIN PRIVATE KEY----- ...`)

---

## 5. Frontend Visual Telemetry & Agent Cockpit

In `seam-ide`, the **Agent Cockpit** subscribes to real-time WebSocket telemetry from `/ws`:
- **Current Agent Badge:** Displays active agent with running spinner.
- **Model Card:** Shows currently assigned provider and model name.
- **Latency Meter:** Live milliseconds display for recent tool or LLM executions.
- **Truthful Status Badges:** Displays `PASS`, `FAIL`, `NOT_CONFIGURED`, or `BLOCKED` with direct links to execution logs.
