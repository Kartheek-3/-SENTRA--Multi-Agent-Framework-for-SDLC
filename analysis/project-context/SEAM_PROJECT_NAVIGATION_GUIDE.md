# SEAM PROJECT NAVIGATION & REPOSITORY DIRECTORY GUIDE
**Practical Developer and Evaluator Source Code Index**

**Document Version:** 1.0.0-nav-guide  
**Date:** October 15, 2026  
**Audience:** Developers, Evaluators, Examiners, and System Maintainers  

---

## 1. Quick Directory Overview

```
c:\Users\Windows 11\Downloads\SEAM1/
├── SEAM/                     # Core Backend Service, Tools & Test Suites
│   ├── backend/              # Python FastAPI Application & Agent Hierarchy
│   ├── tests/                # 78 Test Modules (300 Backend Unit & Integration Tests)
│   ├── knowledge/            # Vertical Domain Knowledge (ChromaDB Vector Seed)
│   └── generated_projects/   # Output directory for Workflow A generated codebases
├── seam-ide/                 # Frontend Developer Studio (React 18 + TypeScript + Vite)
│   ├── src/                  # Component Views, CodeMirror Editor & React Flow Canvas
│   └── package.json          # Dependency Manifest (Vite, CodeMirror, XYFlow React)
├── submission/               # Phase 7 Academic Thesis, Presentation & Viva Deliverables
├── evidence/                 # Empirical Evidence Archive Organized into 14 Categories
│   └── final-submission/     # Categorized Reports, Logs & Playwright Screenshots
├── analysis/                 # Master Context & Analysis Artifacts
│   └── project-context/      # Newly Generated Comprehensive Analysis Documents
└── FINAL_RESEARCH_RESULTS.json # Raw Empirical Research Telemetry (1,621 lines)
```

---

## 2. Core Backend Subsystems (`SEAM/backend/`)

| Subsystem | File Path | Key Classes & Functions | Description |
| :--- | :--- | :--- | :--- |
| **Supervisor Agent** | `SEAM/backend/agents/supervisor_agent.py` | `SupervisorAgent.process()` | Central state automaton controlling lifecycle, approval gates, and rework loops. |
| **Analysis Agent** | `SEAM/backend/agents/analysis_agent.py` | `AnalysisAgent.process()` | AST parsing, cyclomatic complexity, requirement extraction. |
| **Planning Agent** | `SEAM/backend/agents/planning_agent.py` | `PlanningAgent.process()` | Task decomposition into DAGs, API contracts, system design. |
| **Coding Agent** | `SEAM/backend/agents/coding_agent.py` | `CodingAgent.process()` | Synthesizes full-stack code adhering to architectural contracts. |
| **QA Agent** | `SEAM/backend/agents/qa_agent.py` | `QAAgent.process()` | Automated test discovery, execution, defect triage, and fault localization. |
| **Delivery Agent** | `SEAM/backend/agents/delivery_agent.py` | `DeliveryAgent.process()` | Pre-flight validation, release packaging, Dockerfile generation. |
| **State Machine Models** | `SEAM/backend/models/state.py` | `ProjectState`, `Task`, `DefectLocation` | Authoritative Pydantic state container. |
| **Tool Registry & Permissions** | `SEAM/backend/tools/builtin.py` | `_resolve_safe_path()`, `ToolRegistry` | Filesystem sandboxing, path containment, and 4-tier permission matrix. |
| **Model Router** | `SEAM/backend/llm/model_router.py` | `ModelRouter.generate()` | Dynamic inference routing across Ollama, DMR, and deterministic mock. |
| **Diagram Templates & Aliases** | `SEAM/backend/tools/diagram_templates.py`| `CANONICAL_DIAGRAM_TYPES`, `normalize_diagram_identifier()` | Certified definitions for all 10 canonical engineering diagrams. |
| **Diagram Generation** | `SEAM/backend/tools/diagram_generator.py`| `generate_diagram_with_llm()`, `render_diagram_png()` | Pydantic validation, layout coordination, and image rendering. |
| **React Flow Adapter** | `SEAM/backend/tools/diagram_adapter.py` | `adapt_to_react_flow()` | Converts canonical diagram JSON into React Flow node and edge DTOs. |
| **Mermaid Exporter** | `SEAM/backend/tools/diagram_exporter.py`| `export_diagram_to_mermaid()` | Exports validated diagram JSON to Mermaid markup text. |
| **Safe Workspace Service** | `SEAM/backend/github/workspace_service.py`| `SafeWorkspaceService.prepare_workspace()` | Shallow git clone, sandbox isolation, and path containment. |
| **14-Section Understanding** | `SEAM/backend/github/understanding_service.py` | `ProjectUnderstandingService.analyze()` | AST-based architectural comprehension of existing repositories. |
| **Enhancement Planner** | `SEAM/backend/github/enhancement_planner.py` | `EnhancementPlanningService.create_plan()` | Scoped task planning for Workflow B brownfield enhancements. |
| **Projects API Router** | `SEAM/backend/api/projects.py` | `@router.post("")`, `approve_enhancement()` | REST endpoints for project CRUD, diagrams, approval gating, and diffs. |
| **GitHub API Router** | `SEAM/backend/api/github.py` | `@router.post("/connect")` | GitHub repository connection and metadata retrieval. |
| **SQLite Persistence** | `SEAM/backend/database/sqlite.py` | `SQLiteDatabase.save_project()` | WAL-mode transactional event store and state rehydration. |
| **Docker SDXL Provider** | `SEAM/backend/image_gen/docker_sdxl_provider.py` | `DockerSDXLProvider.is_available()` | Capability detection for optional SDXL 1.0 container. |

---

## 3. Frontend Architecture (`seam-ide/src/`)

| View / Module | File Path | Underlying Technology | Purpose |
| :--- | :--- | :--- | :--- |
| **Main App Shell** | `seam-ide/src/App.tsx` | React 18, React Router | Top-level routing, theme provider, and view switching. |
| **Activity Bar** | `seam-ide/src/layout/ActivityBar.tsx` | Lucide React Icons | Left navigation bar switching between IDE modules. |
| **Code Editor** | `seam-ide/src/editor/CodeEditor.tsx` | **CodeMirror 6** (`@codemirror/view`) | Multi-language syntax highlighting, line numbers, search keymaps. |
| **Project Explorer** | `seam-ide/src/explorer/ProjectExplorer.tsx` | Custom Tree Component | Collapsible workspace file hierarchy tree. |
| **Antigravity HUD** | `seam-ide/src/components/AntigravityHUD.tsx` | WebSocket Streaming | Real-time agent status badge and token generation ticker. |
| **Design Studio** | `seam-ide/src/components/DesignStudioPage.tsx` | `@xyflow/react` + `dagre` | Interactive 10-diagram canvas, pan/zoom, and export options. |
| **Test Lab** | `seam-ide/src/components/TestLabPage.tsx` | REST + WebSocket | Test runner triggers, live terminal output, pass/fail metrics. |
| **Repair Center** | `seam-ide/src/components/RepairCenterPage.tsx` | WebSocket Events | Defect triage dashboard, patch previews, and verification history. |
| **Contracts Console** | `seam-ide/src/components/ContractsPage.tsx` | JSON Schema Viewer | OpenAPI and Protobuf interface drift inspection. |
| **Runtime Console** | `seam-ide/src/components/RuntimeConsolePage.tsx` | Process Telemetry | Health probes, memory consumption, active listening ports. |
| **Model Router Panel** | `seam-ide/src/components/ModelControlPanel.tsx` | Telemetry Polling | Provider status (Ollama, DMR, Mock) and latency metrics. |
| **Delivery Center** | `seam-ide/src/components/DeliveryCenterPage.tsx` | Archive Downloader | Release packaging button, Dockerfile viewer, SHA-256 manifest. |
| **Integrations Hub** | `seam-ide/src/components/IntegrationsPage.tsx` | GitHub API Adapter | GitHub connection, repository analyzer, and approval modal. |

---

## 4. Key Test Suites (`SEAM/tests/`)

| Test Suite | File Path | Focus Area | Command to Execute |
| :--- | :--- | :--- | :--- |
| **Diagram Generation** | `SEAM/tests/test_diagram_generation.py` | All 10 canonical diagrams, Pydantic validation, layout. | `pytest SEAM/tests/test_diagram_generation.py` |
| **Local Model Alignment**| `SEAM/tests/test_phase2_model_alignment.py` | Ollama connectivity, ModelRouter cascade, fallback. | `pytest SEAM/tests/test_phase2_model_alignment.py` |
| **GitHub Enhancement** | `SEAM/tests/test_phase3_github_enhancement.py` | Workflow B sandbox, 14-section report, diff capture. | `pytest SEAM/tests/test_phase3_github_enhancement.py` |
| **Integration & State** | `SEAM/tests/test_phase4_integration_certification.py` | SQLite rehydration, tool permissions, workflow states. | `pytest SEAM/tests/test_phase4_integration_certification.py` |
| **Docker SDXL Capability**| `SEAM/tests/test_phase5_docker_sdxl.py` | Capability detection, unavailable state handling. | `pytest SEAM/tests/test_phase5_docker_sdxl.py` |
| **Frontend Unit Suite** | `seam-ide/src/seam/__tests__/` | State hooks, store management, UI components. | `cd seam-ide; npx.cmd vitest run` |
| **Browser E2E Audit** | `SEAM/tests/test_playwright_ui.py` | Headless Playwright verification across 15 screens. | `python tests/test_playwright_ui.py` |

---

## 5. Academic & Submission Deliverables (`submission/`)

| Deliverable | File Path | Description |
| :--- | :--- | :--- |
| **Project Report (DOCX)** | `submission/SEAM_FINAL_YEAR_PROJECT_REPORT.docx` | Native OpenXML Word document containing the complete 12-chapter thesis. |
| **Project Report (Markdown)**| `submission/SEAM_FINAL_YEAR_PROJECT_REPORT.md` | Markdown source for the complete 12-chapter academic report. |
| **Presentation Deck (PPTX)**| `submission/SEAM_FINAL_PRESENTATION.pptx` | 18-slide examination slide deck with embedded speaker notes. |
| **Speaker Notes Guide** | `submission/SEAM_PRESENTATION_SPEAKER_NOTES.md` | Scripted oral defense notes and examiner Q&A for all 18 slides. |
| **Demonstration Runbook** | `submission/SEAM_FINAL_DEMO_RUNBOOK.md` | 12-step live presentation protocol with offline contingency procedures. |
| **Viva Examination Guide** | `submission/SEAM_VIVA_QUESTIONS_AND_ANSWERS.md` | 65 comprehensive questions with technical model answers. |
| **Evidence Traceability Index**| `submission/SEAM_SUBMISSION_EVIDENCE_INDEX.md` | Master mapping between claims, code, tests, and evidence. |
