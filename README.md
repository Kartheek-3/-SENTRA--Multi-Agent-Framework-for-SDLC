# SEAM — Self-Evolving Autonomous Multi-Agent Framework

> **Academic Title:** *An Autonomous Multi-Agent Framework for End-to-End Software Engineering with Domain-Aware Intelligence*  
> **Department:** Computer Science and Engineering  
> **Academic Session:** 2025–2026  
> **Version:** 1.0.1 | **Branch:** `final-validation` | **Verification Status:** VALIDATED

---

## 1. Executive Overview

**SEAM (Self-Evolving Autonomous Multi-Agent Framework)** is a domain-aware autonomous multi-agent software engineering system that transforms high-level user requirements into verified, production-structured software architectures and applications.

Unlike monolithic AI coding assistants or single-prompt code generators that suffer from context drift and hallucination, SEAM decomposes software development into a coordinated, multi-stage state machine operated by **six specialized cognitive agents**. Every agent operates against an authoritative `ProjectState` and adheres to strict permission sandboxing, contract intelligence, and automated self-healing quality assurance.

SEAM features a modern, standalone developer IDE (`seam-ide`) built with React 18, TypeScript, Vite, CodeMirror 6, and a Tauri desktop wrapper, backed by a FastAPI microservices runtime (`SEAM/backend`).

---

## 2. Six Cognitive Agents Architecture

SEAM's intelligence is organized into exactly six authoritative cognitive agents:

```mermaid
graph TD
    User([User Requirements / GitHub URL]) --> Analysis[1. Analysis Agent]
    Analysis -->|Domain Analysis & Constraints| Planning[2. Planning & Design Agent]
    Planning -->|System Design & Task Graph| Supervisor{3. Supervisor / Orchestrator}
    
    Supervisor -->|Approval Gate (Workflow B)| Gate([User Approval])
    Gate -->|Approved| Supervisor
    
    Supervisor -->|Execute Task| Coding[4. Coding Agent]
    Coding -->|Source Code & Diff| QA[5. QA Agent]
    QA -->|Defects Detected / Invariant Failure| Coding
    QA -->|Tests Passed & Verified| Delivery[6. Delivery Agent]
    Delivery -->|Packaging & Release Manifest| Deploy([Deployment / Handover])
```

1. **Analysis Agent**: Synthesizes unstructured requirements, profiles existing repositories, extracts domain entities, and discovers constraints.
2. **Planning & Design Agent**: Generates architecture blueprints, selects data models, and produces all 10 canonical software engineering diagram schemas.
3. **Supervisor / Orchestrator Agent**: Manages the LangGraph state machine, sequences agent tasks, dynamically balances concurrency, and enforces human-in-the-loop approval gates.
4. **Coding Agent**: Implements modular source code, updates manifests, and performs targeted file modifications using unified diffs.
5. **QA Agent**: Executes automated test suites, performs static analysis, detects contract violations, and drives autonomous self-healing repair loops.
6. **Delivery Agent**: Packages deployable artifacts, verifies CI/CD configurations, creates release documentation, and verifies production readiness.

*Note: Infrastructure capabilities (ChromaDB RAG, GitHub Intelligence, Diagram Engine, and n8n webhooks) are tools and services invoked by agents, not independent cognitive agents.*

---

## 3. Supported Engineering Workflows

SEAM natively supports two distinct, end-to-end software development workflows:

### Workflow A: Greenfield Project Generation
- **Input**: User prompt or requirement specification.
- **Execution**: The Analysis Agent builds entity specifications; Planning generates architecture and diagrams; Coding generates complete scaffolding, application logic, and test suites; QA validates 100% test passing; Delivery packages the release.
- **Output**: Clean codebase in `generated_projects/{project_name}/`.

### Workflow B: Brownfield Repository Understanding & Enhancement
- **Input**: Public or authenticated GitHub repository URL and enhancement task.
- **Execution**: The repository is cloned into a secure workspace (`workspaces/repos/{project_id}/`); the 14-section Project Understanding engine profiles the architecture; an Enhancement Plan is generated; the **Supervisor halts at an explicit Approval Gate** for user review; upon approval, Coding applies targeted patches, capturing unified Git diffs (`.patch`), followed by regression QA verification.

---

## 4. Repository Structure

```
SEAM1/
├── README.md                                # [Canonical Root Entrypoint] Monorepo architecture & quickstart
├── firestore.rules                          # Canonical Firebase Firestore security rules (61 lines)
│
├── SEAM/                                    # [Backend Domain] FastAPI application & AI multi-agent runtime
│   ├── README.md                            # Backend-specific architecture, virtualenv, and setup guide
│   ├── requirements.txt                     # Python dependencies (FastAPI, LangGraph, ChromaDB, etc.)
│   ├── backend/                             # Core Python backend package
│   │   ├── agents/                          # 6 cognitive agent implementations
│   │   ├── api/                             # REST endpoints (projects, artifacts, github, filesystem)
│   │   ├── database/                        # SQLite embedded persistence (seam.db)
│   │   ├── llm/                             # ModelRouter (Ollama local inference & fallbacks)
│   │   ├── rag/                             # ChromaDB vector store & knowledge retriever
│   │   └── tools/                           # Sandboxed agent tools & 10 diagram generators
│   ├── knowledge/                           # Curated domain knowledge store for RAG
│   ├── n8n/                                 # Optional n8n Docker orchestration & workflow JSONs
│   └── tests/                               # Backend test suite (pytest)
│
├── seam-ide/                                # [Frontend Domain] Standalone IDE & Developer UI
│   ├── README.md                            # Frontend development, Vite build, and Tauri desktop guide
│   ├── package.json                         # Node dependencies (React 18, TypeScript, CodeMirror 6, Lucide)
│   ├── src/                                 # IDE UI components (Studio, Test Lab, Contracts, Repair)
│   └── vitest.config.ts                     # Frontend unit testing configuration
│
├── submission/                              # [Academic Submission Package]
│   ├── SEAM_FINAL_YEAR_PROJECT_REPORT.docx  # Formatted thesis manuscript
│   ├── SEAM_FINAL_YEAR_PROJECT_REPORT.md    # Source markdown thesis
│   ├── SEAM_FINAL_PRESENTATION.pptx         # Defense slide presentation
│   ├── SEAM_PRESENTATION_SPEAKER_NOTES.md   # Scripted presentation notes
│   ├── SEAM_FINAL_DEMO_RUNBOOK.md           # Demonstration test runbook
│   ├── SEAM_VIVA_QUESTIONS_AND_ANSWERS.md   # Viva voce preparation guide
│   └── SEAM_SUBMISSION_EVIDENCE_INDEX.md    # Academic claim-to-evidence matrix
│
├── analysis/                                # [Research & Evaluation Domain]
│   ├── project-context/                     # Research papers, benchmarks, and gap analyses
│   └── project-context/file-audit/          # Repository deduplication and file audit records
│
├── evidence/                                # [Immutable Historical Evidence Freeze]
│   └── final-submission/                    # Phase 4 & Phase 6 validation evidence snapshot
│
└── generated_projects/                      # Generated software projects created by SEAM
```

---

## 5. System Prerequisites

- **Operating System**: Windows 10/11, macOS, or Ubuntu Linux 22.04+
- **Python**: Version 3.10, 3.11, or 3.12 (standard virtual environment)
- **Node.js**: Version 18.x or 20.x LTS with `npm`
- **Ollama** *(Optional for local AI inference)*: Running locally on `http://127.0.0.1:11434` with model `qwen2.5-coder:1.5b` (or uses deterministic template fallback).
- **Docker** *(Optional)*: Required only if running n8n workflows or optional SDXL 1.0 image generation.

---

## 6. Quickstart: Running SEAM Locally

Launch SEAM using two terminal windows:

### Terminal 1: FastAPI Backend
```bash
# Navigate to backend directory
cd SEAM

# Create and activate virtual environment (Windows PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Start FastAPI backend service
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
*Backend verification: Visit `http://127.0.0.1:8000/docs` to inspect the Swagger UI.*

### Terminal 2: Standalone IDE Frontend
```bash
# Navigate to frontend directory
cd seam-ide

# Install Node dependencies
npm install

# Start Vite development server
npm run dev
```
*Frontend verification: Open your browser at `http://127.0.0.1:5173` to access the SEAM IDE.*

---

## 7. Verification and Testing

Execute the multi-layered test hierarchy across backend and frontend:

```bash
# 1. Backend Test Suite (pytest)
cd SEAM
pytest tests/ -v

# 2. Frontend Strict TypeScript Type Check
cd seam-ide
npx tsc --noEmit

# 3. Frontend Unit & Store Suite (vitest)
cd seam-ide
npm run test

# 4. Frontend Production Compilation
cd seam-ide
npm run build
```

---

## 8. Authoritative Documentation Index

| Topic / Requirement | Authoritative File Path |
| :--- | :--- |
| **Backend Technical Guide** | [`SEAM/README.md`](file:///c:/Users/Windows%2011/Downloads/SEAM1/SEAM/README.md) |
| **Frontend IDE Guide** | [`seam-ide/README.md`](file:///c:/Users/Windows%2011/Downloads/SEAM1/seam-ide/README.md) |
| **Academic Thesis Manuscript** | [`submission/SEAM_FINAL_YEAR_PROJECT_REPORT.md`](file:///c:/Users/Windows%2011/Downloads/SEAM1/submission/SEAM_FINAL_YEAR_PROJECT_REPORT.md) |
| **Evaluator Demo Runbook** | [`submission/SEAM_FINAL_DEMO_RUNBOOK.md`](file:///c:/Users/Windows%2011/Downloads/SEAM1/submission/SEAM_FINAL_DEMO_RUNBOOK.md) |
| **Comprehensive Viva Q&A** | [`submission/SEAM_VIVA_QUESTIONS_AND_ANSWERS.md`](file:///c:/Users/Windows%2011/Downloads/SEAM1/submission/SEAM_VIVA_QUESTIONS_AND_ANSWERS.md) |
| **Claim-to-Evidence Matrix** | [`submission/SEAM_SUBMISSION_EVIDENCE_INDEX.md`](file:///c:/Users/Windows%2011/Downloads/SEAM1/submission/SEAM_SUBMISSION_EVIDENCE_INDEX.md) |
| **System Architecture Audit** | [`FINAL_BACKEND_ARCHITECTURE_AUDIT.md`](file:///c:/Users/Windows%2011/Downloads/SEAM1/FINAL_BACKEND_ARCHITECTURE_AUDIT.md) |
| **Empirical Benchmarks & Metrics** | [`FINAL_EXPERIMENTAL_EVALUATION.md`](file:///c:/Users/Windows%2011/Downloads/SEAM1/FINAL_EXPERIMENTAL_EVALUATION.md) |
| **Repository File Audit** | [`analysis/project-context/file-audit/SEAM_FILE_AUDIT_SUMMARY.md`](file:///c:/Users/Windows%2011/Downloads/SEAM1/analysis/project-context/file-audit/SEAM_FILE_AUDIT_SUMMARY.md) |

---

## 9. Disclosed Limitations & Deployment Status

- **Embedded Database**: SEAM operates natively with an embedded SQLite WAL database (`seam.db`). While PostgreSQL and Redis adapters are implemented in code, they are optional and not configured by default in local developer mode.
- **Local Model Constraints**: Designed to run efficiently on standard consumer hardware (e.g., 16GB RAM laptops without discrete GPUs) via `qwen2.5-coder:1.5b`. When local Ollama is offline, the system safely falls back to deterministic template generation.
- **Image Generation (SDXL 1.0)**: Stable Diffusion XL is an optional Dockerized provider that requires Linux and CUDA acceleration. On Windows machines lacking NVIDIA GPU Docker runtime, it gracefully reports `NOT_AVAILABLE_ON_CURRENT_HOST`; structured Mermaid and diagram rendering remain fully operational.
