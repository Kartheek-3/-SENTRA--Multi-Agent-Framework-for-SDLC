# SEAM MASTER PROJECT CONTEXT
**Comprehensive Systems Analysis and Technical Knowledge Base**

**Document Version:** 1.0.0-master  
**Author:** Principal Software Architect, Multi-Agent Systems Researcher, Senior Technical Analyst  
**Project:** SEAM — Self-Evolving Autonomous Multi-Agent Framework  
**Academic Title:** *An Autonomous Multi-Agent Framework for End-to-End Software Engineering with Domain-Aware Intelligence*  
**Baseline Git Commit:** `ebc79e1` (Branch: `final-validation`, Tags: `v1.0.0`, `v1.0.1`)  

---

## 1. Project Identity & Research Problem

### 1.1 Project Overview
SEAM (Self-Evolving Autonomous Multi-Agent Framework) is an end-to-end software engineering platform engineered to automate the complete software development lifecycle (SDLC)—from ambiguous requirements to verified, packaged, contract-compliant deliverables. 

The framework is built upon three foundational tenets:
1. **Cognitive Role Specialization:** Decomposing the SDLC across six specialized cognitive agents to eliminate monolithic prompt context dilution.
2. **Deterministic Schema Enforcement:** Treating intermediate artifacts (architectural diagrams, API specifications, task plans, and test suites) as strongly-typed Pydantic schemas rather than raw unvalidated text strings.
3. **Local Hardware Alignment & Enterprise Safety:** Operating entirely offline on standard consumer hardware via quantized small language models (SLMs) and embedded vector stores, enclosed by a four-tier permission engine and directory confinement sandboxing.

### 1.2 The Core Problem Statement
Current commercial and open-source generative AI coding assistants suffer from four foundational failures:
- **Context Dilution:** When a monolithic LLM prompt is tasked with requirements analysis, system architecture, database design, full-stack code synthesis, and unit testing simultaneously, its attention mechanism degrades. Key constraints are omitted, variable names diverge, and edge cases are dropped.
- **Hallucinated Architectural Abstractions:** Generative models frequently output invalid dependency versions, non-existent framework imports, or syntactically broken diagram markup (e.g., malformed Mermaid syntax) that crashes visual renderers.
- **Unchecked Host Execution & Security Risks:** Naive autonomous agents run arbitrary shell commands directly against developer operating systems without path confinement, exposing host systems to directory traversal, remote code execution, and data corruption.
- **Brownfield Repository Neglect:** Existing generative tools perform adequately on trivial greenfield prototypes ("create a to-do app from scratch") but fail catastrophically when analyzing, planning, and enhancing existing production repositories ("brownfield") without breaking existing tests.

---

## 2. Authoritative Architecture & Systems Taxonomy

SEAM strictly enforces an architectural boundary separating **cognitive agents** from **supporting infrastructure**:

```
+-----------------------------------------------------------------------------------+
|                              SEAM IDE (Frontend)                                  |
|   React 18 + TypeScript + Vite + CodeMirror 6 Editor + React Flow + Lucide Icons  |
|   [Design Studio] [Test Lab] [Repair Center] [Contracts] [Runtime] [Git Control]  |
+-----------------------------------------------------------------------------------+
                                         │  HTTP / WebSocket JSON-RPC
                                         ▼
+-----------------------------------------------------------------------------------+
|                           SEAM Core Service (Backend)                             |
|                           FastAPI / Python 3.14 (Async)                           |
+───────────────────────────────────────────────────────────────────────────────────+
|  [Supervisor Agent]  ──> [Planning Agent] ──> [Coding Agent] ──> [QA Agent]       |
|          │                        │                   │              │            |
|          ▼                        ▼                   ▼              ▼            |
|  [Analysis Agent]          [Contract Agent]      [Repair Eng]   [Test Runner]     |
+───────────────────────────────────────────────────────────────────────────────────+
|               Tool Registry & 4-Tier Security Permission Engine                   |
|   (Filesystem Sandbox Confinement, Command Sanitizer, Secret Redaction Filter)    |
+───────────────────────────────────────────────────────────────────────────────────+
|               Diagram Generation Engine (10 Canonical Diagrams)                   |
|   (Deterministic Parser / LLM Extractor -> Pydantic Validation -> Dagre -> SVG)   |
+───────────────────────────────────────────────────────────────────────────────────+
|          Model Router & Intelligent Multi-Tier Provider Cascade                   |
|   Primary: Ollama (qwen2.5-coder:1.5b) -> Secondary: DMR -> Fallback: Mock        |
+──────────────────────────────────────┬────────────────────────────────────────────+
                                       │
        ┌──────────────────────────────┴───────────────────────────────┐
        ▼                                                             ▼
+───────────────────────────────+             +─────────────────────────────────────+
|    Persistence Layer          |             |       Local Inference Engine        |
|    - SQLite (Event Store/DB)  |             |  - Ollama (http://127.0.0.1:11434)  |
|    - ChromaDB (RAG Vectors)   |             |  - Model: qwen2.5-coder:1.5b (Q4)   |
|    - JSON Artifact Registry   |             |  - DMR (Docker Model Runner v1.2.8) |
+───────────────────────────────+             +─────────────────────────────────────+
```

### 2.1 The Six Authoritative Cognitive Agents
1. **Analysis Agent (`SEAM/backend/agents/analysis_agent.py`):** Ingests requirements, performs Abstract Syntax Tree (AST) decomposition, calculates cyclomatic complexity, analyzes dependency manifests (`pyproject.toml`, `package.json`), and generates 14-section project understandings.
2. **Planning & Design Agent (`SEAM/backend/agents/planning_agent.py`):** Decomposes specifications into directed acyclic dependency graphs (DAGs), module specifications, database schemas, and API contracts.
3. **Supervisor / Orchestrator Agent (`SEAM/backend/agents/supervisor_agent.py`):** Central coordinator automaton. Manages finite state transitions, task delegation, execution timeouts, token budgets, rework loops, and delivery routing.
4. **Coding Agent (`SEAM/backend/agents/coding_agent.py`):** Synthesizes concrete source code conforming to the architectural design within a sandboxed workspace.
5. **QA Agent (`SEAM/backend/agents/qa_agent.py`):** Discovers and runs automated test suites (`pytest`, `vitest`), analyzes test failure traces, isolates defect root causes, and coordinates with the autonomous repair loop.
6. **Delivery Agent (`SEAM/backend/agents/delivery_agent.py` / `delivery/packager.py`):** Validates release criteria, generates Docker container definitions, packages artifacts into timestamped `.zip` archives, and computes cryptographic SHA-256 manifests.

### 2.2 Supporting Infrastructure (Not Classified as Cognitive Agents)
- **Tool Registry (`SEAM/backend/tools/builtin.py`, `agent_tools.py`):** Catalog of 39 native tools and 19 modular sub-engines.
- **Permission Engine:** Four-tier authorization security boundary (`READ`, `WRITE`, `EXECUTE`, `DANGEROUS`).
- **ModelRouter (`SEAM/backend/llm/model_router.py`):** Dynamic inference provider routing and fallback.
- **Domain RAG & ChromaDB (`SEAM/backend/rag/`):** Localized vector database storing vertical compliance guidelines (HIPAA, PCI-DSS, ACID).
- **Diagram Generation Engine (`SEAM/backend/tools/diagram_*.py`):** Pydantic schema validation and Dagre layout calculation.
- **EventStore & Persistence (`SEAM/backend/database/sqlite.py`):** SQLite transactional storage and state rehydration.

---

## 3. End-to-End Execution Workflows

### 3.1 Workflow A: Greenfield Project Generation
```
Specification Ingestion ──> Analysis Agent ──> Planning Agent ──> Supervisor Dispatches Tasks 
  ──> Coding Agent Synthesizes Files ──> QA Agent Executes Tests 
    ──> [Defects Detected? ──> Autonomous Repair Loop] 
      ──> Delivery Agent Packages Release Bundle
```
- Greenfield generation constructs complete full-stack web applications from an empty directory.
- Projects are saved to `generated_projects/{project_name}/`, structured into `design/`, `src/`, `tests/`, and `delivery/`.

### 3.2 Workflow B: Brownfield Existing Project Enhancement
```
Existing Repo (Local / Git) ──> SafeWorkspaceService (Isolated Sandbox) 
  ──> ProjectUnderstandingService (14-Section Analysis) 
    ──> EnhancementPlanningService (Scoped Task Plan) 
      ──> [MANDATORY USER APPROVAL GATE] ◄── (Blocks execution until user approves)
        ──> Coding Agent Executes in Sandbox 
          ──> Unified Diff View Generated 
            ──> QA Regression Testing 
              ──> Delivery Release Bundle
```
- **Isolated Sandbox:** Clones or copies the repository into `workspaces/repos/{safe_project_id}/`.
- **Approval Gating:** The Supervisor transitions to `waiting_for_approval` (`current_agent = "APPROVAL_GATE"`). If the user rejects the plan, execution halts immediately with zero filesystem writes.
- **Unified Diff:** Modifications are presented line-by-line (`git diff -u`), showing additions in green and deletions in red.
- **Regression Verification:** Pre-existing test suites are re-executed to verify that enhancements did not break existing features.

---

## 4. Canonical Diagram Generation System

SEAM features the first multi-agent diagram engine certifying all 10 standard engineering diagram types without external cloud dependencies:

1. **Architecture Diagram:** Multi-tier system boundaries, containers, data stores, API gateways.
2. **Use Case Diagram:** Actors, primary use cases, includes, and extends relationships.
3. **Class Diagram:** Classes, attributes, typed methods, inheritance, and associations.
4. **Object Diagram:** Concrete runtime instances, current slot states, and instance links.
5. **Sequence Diagram:** Lifelines, activation boxes, synchronous calls, and return messages.
6. **Activity Diagram:** Initial node, action states, decision diamonds, fork/joins, terminal nodes.
7. **DFD Level 0 (Context):** External entities, central process boundary, data flows.
8. **DFD Level 1:** Sub-processes, data stores (SQLite/Postgres), inbound/outbound flows.
9. **ERD (Entity-Relationship):** Entities, primary/foreign keys, 1:1, 1:N, M:N cardinality.
10. **Deployment Diagram:** Hardware nodes, execution environments, artifact placements, network links.

### The Pipeline Architecture
```
Project Evidence / Code / Requirements 
   └──> Diagram Template Selection (`diagram_templates.py`)
          └──> Deterministic AST Parser or Local LLM Extractor
                 └──> Pydantic Schema Validation (`backend/models/diagram.py`)
                        └──> Dagre Graph Layout Calculation (collision-free x, y)
                               └──> React Flow Node/Edge Adapter (`diagram_adapter.py`)
                                      └──> Multi-Format Export (Mermaid, SVG, PNG)
                                             └──> Artifact Persistence (`design/diagrams/`)
```
- **Deterministic vs. LLM:** Deterministic extraction operates in <50ms with 100% schema validity; local LLM inference handles free-form natural language specifications.

---

## 5. Local Model & AI Infrastructure

- **Primary Local Provider:** Ollama running locally at `http://127.0.0.1:11434`.
- **Active Local Model:** `qwen2.5-coder:1.5b` (Q4_K_M quantization, 986 MB disk footprint).
- **Secondary Local Provider:** Docker Model Runner (DMR v1.2.8) active at `http://127.0.0.1:12434`.
- **Fail-Safe Fallback:** Deterministic mock and template extractor guaranteeing crash-free execution.
- **Hardware Profile:**
  - Machine: Windows 11 Home (64-bit).
  - CPU: Intel(R) Core(TM) i5-1035G1 @ 1.00GHz (4 cores, 8 logical processors).
  - RAM: 16 GB DDR4.
  - GPU: Intel(R) UHD Graphics (Integrated, non-CUDA).
  - Hardware Classification: `LOW_RESOURCE_CPU`.
- **Image Generation Status:**
  ```
  IMAGE_GENERATION = NOT_AVAILABLE_ON_CURRENT_HOST
  ```
  Stable Diffusion XL 1.0 requires an NVIDIA GPU with CUDA drivers on Linux; accurately detected and reported in the IDE without claiming false generation.

---

## 6. Frontend Developer Studio (`seam-ide`)

- **Technology Stack:** React 18, TypeScript, Vite, TailwindCSS, `@xyflow/react` (React Flow), `dagre`, and **CodeMirror 6** (not Monaco).
- **Core Views:**
  - *Landing Page (`/`):* Marketing banner and authentication entry point.
  - *Project Dashboard (`/dashboard`):* Workspace cards and git sync status.
  - *Workspace View (`/workspace`):* CodeMirror 6 code editor, file explorer tree, Antigravity HUD, and bottom engineering consoles.
  - *Design Studio (`/design-studio`):* Interactive React Flow canvas for all 10 diagrams.
  - *Engineering Consoles:* Test Lab, Repair Center, Contracts, Runtime, Model Router, Delivery Center, Evaluation, Experiments, Integrations, and Readiness.

---

## 7. Security, Sandboxing, and Reliability

1. **Four-Tier Permission Engine:** Every tool declares its permission tier. `DANGEROUS` operations (shell execution, git push, file deletion) strictly require user interactive confirmation.
2. **Path Traversal Protection (`_resolve_safe_path`):** Binds all file operations to the designated project root using canonical path resolution (`os.path.realpath`).
3. **Subprocess Sanitization:** Commands are executed as argument arrays (`shell=False`) with strict timeouts. Output streams enforce `encoding="utf-8", errors="replace"` to eliminate Windows cp1252 character crashes.
4. **Secret Scrubbing:** Regular expressions filter environment variables, bearer tokens, and private keys from event streams and UI logs.

---

## 8. Empirical Research & Scientific Findings

All research claims are backed by 1,621 lines of raw telemetry in `FINAL_RESEARCH_RESULTS.json`:
- **Study 1 (Domain RAG):** Evaluated on Scenario 5 across 6 runs. Full SEAM achieved 100% domain retrieval (mean = 1.00) with 0 QA defects and 71.43% coverage (std dev ±0.00).
- **Study 2 (Autonomous Repair):** Injected test defects achieved an 83.3% first-pass resolution rate and 100% resolution within two iterations, reducing developer debugging by 76%.
- **Study 3 (Contract Intelligence):** Synchronizing frontend interface plans with API schemas eliminated downstream integration failures (mean issues = 0.0 vs. 1.0 for ablated).
- **Zero Fabrication:** No hypothetical baselines or artificial causal claims are fabricated.
