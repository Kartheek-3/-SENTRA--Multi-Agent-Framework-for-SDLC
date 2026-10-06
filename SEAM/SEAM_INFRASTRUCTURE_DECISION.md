# SEAM v1.0.0 — Infrastructure & Architectural Decision Record (ADR)

**Project:** SEAM (Self-Evolving Autonomous Multi-Agent Framework)  
**Roles:** Principal Software Architect, Principal Database Architect, Principal Cloud Architect, Principal DevSecOps Engineer  
**Date:** October 6, 2026  
**Status:** **APPROVED & ADOPTED**

---

## 1. Context & Architectural Governance Principle

A primary directive of the SEAM Engineering Board is the **Simplicity & Minimum Complexity Rule**:
> *"Choose the simplest architecture that satisfies the requirements. Do not introduce unnecessary microservices, duplicate databases, duplicate model runtimes, or redundant service layers."*

Every infrastructure component must serve a distinct, empirically validated purpose.

---

## 2. Decision Matrix: Persistence & Storage Strategy

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PERSISTENCE TIER DIVISION                       │
└────────────────────────────────────────────────────────────────────────┘

 [Relational & Operational State]  ──► PostgreSQL 16
                                        - Project metadata & configurations
                                        - Append-only EventStore
                                        - Artifact metadata & file registry
                                        - Evaluation & experiment history

 [Semantic Vector Knowledge]       ──► ChromaDB + FastEmbed
                                        - 4 domain-aware collections
                                        - Provenance & validated chunks
                                        - FastEmbed CPU-optimized embeddings

 [Distributed Cache & Ephemeral]   ──► Redis 7
                                        - Rate limiting & circuit breakers
                                        - Distributed task locking
                                        - Real-time WebSocket pub/sub buffers
```

### Explicitly Rejected Persistent Stores:
1. **MongoDB / Document DBs:** **REJECTED.** JSON-centric workflows are natively and reliably supported via PostgreSQL `jsonb` with GIN indexing, eliminating the operational overhead of a separate NoSQL cluster.
2. **MySQL:** **REJECTED.** Redundant with PostgreSQL. PostgreSQL provides superior JSON querying, CTE performance, and concurrent indexing.
3. **InfluxDB / TimeSeries:** **REJECTED.** Metrics are routed to Prometheus via OpenTelemetry, which handles time-series scrapes natively.
4. **Neo4j Graph Database:** **POSTPONED TO v1.2.** Knowledge graph relationships in v1.0 are represented via relational foreign keys and RAG metadata. Graph databases are not required for core SDLC agent loops.

---

## 3. Decision Matrix: Browser Automation & E2E Testing

```
                    ┌────────────────────────────┐
                    │ BROWSER AUTOMATION SYSTEM  │
                    └─────────────┬──────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
            [PLAYWRIGHT (ADOPTED)]     [SELENIUM (REJECTED)]
            - Headless Chromium/Firefox - Heavy Java/WebDriver dependency
            - High-fidelity network log - Fragile selector waits
            - Visual trace & screenshot - Slower execution latency
            - Native async Python API   - Higher container memory footprint
```

### Decision:
**Playwright is adopted as the sole browser automation engine** across SEAM's QA Agent and E2E runner. Selenium is completely excluded from core infrastructure.

---

## 4. Decision Matrix: Container & Infrastructure Ecosystem

| Category | Component | Status | Architectural Rationale |
| :--- | :--- | :--- | :--- |
| **Model Inference** | Docker Model Runner | **CORE** | Standardized containerized OpenAI REST inference. |
| **Model Inference** | Ollama | **CORE** | Fast local CPU/GPU execution of open quantized models. |
| **Vector DB** | ChromaDB | **CORE** | Lightweight, embedded/HTTP persistent vector store. |
| **Relational DB** | PostgreSQL 16 | **CORE (PROD)**| Durable ACID transaction store for multi-user deployments. |
| **Cache/Locking** | Redis 7 | **CORE (PROD)**| High-throughput distributed lock and ephemeral caching. |
| **Automation** | n8n | **CORE** | Decoupled external automation layer for webhooks. |
| **Observability** | OpenTelemetry | **CORE** | Universal tracing, spans, and metrics instrumentation. |
| **Observability** | Prometheus | **CORE** | Time-series metrics collection and alert evaluation. |
| **Observability** | Grafana | **CORE** | Real-time operations and agent telemetry dashboards. |
| **Testing** | Playwright | **CORE** | Deterministic browser automation and screenshot capture. |

### Target Project Tools Boundary:
Project-specific build and test tools (e.g., `gradle`, `maven`, `cargo`, `go`, `npm`, `dotnet`) are treated strictly as **target workspace tools** dynamically invoked by `CodingAgent` and `QAAgent`. They are **NOT** bundled as SEAM infrastructure services.

---

## 5. Scale-Aware Architecture Matrix

SEAM enforces scale-awareness to prevent premature microservice bloat:

| Scale Tier | Deployment Archetype | Persistence | Model Provider | Observability |
| :--- | :--- | :--- | :--- | :--- |
| **SMALL** (Solo Dev / PoC) | Single Host / SQLite | Local SQLite + ChromaDB | Local Ollama (1.5B/7B) | Local logging |
| **MEDIUM** (Startup Team) | Docker Compose | PostgreSQL + ChromaDB | Docker Runner / Ollama | OTel + Prometheus |
| **LARGE** (Enterprise Dept)| Kubernetes (Helm) | Managed RDS + Redis | Hybrid Local + Cloud | Full OTel + Grafana |
| **ENTERPRISE** (Global Org) | Multi-Region K8s | Distributed Aurora + Redis | Cloud Gateway (480B) | Datadog / Grafana Cloud |
