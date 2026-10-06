# SEAM v1.0.0 — Product UX & Information Architecture Specification

**Project:** SEAM (Self-Evolving Autonomous Multi-Agent Framework)  
**Roles:** Principal Product Architect, Principal UI/UX Designer, Senior Product Manager  
**Status:** **ACTIVE PRODUCT SPECIFICATION**

---

## 1. Product Positioning & UX North Star

SEAM is positioned as **an autonomous software engineering platform that turns human requirements into designed, implemented, tested, repaired, and delivery-ready software**.

### Core UX Principles:
1. **Observable Autonomy:** Never hide autonomous decision-making behind vague spinners. The engineer must see *which agent* is acting, *which model* is reasoning, *which tool* is invoked, and *what evidence* was produced.
2. **Truthful States:** Never display `PASS` simply because a testing tool or integration exists. Unconfigured dependencies display `NOT_CONFIGURED`; untestable modules display `BLOCKED`; running jobs display `RUNNING`.
3. **Developer-First Ergonomics:** Professional code-oriented density, keyboard shortcuts (`Ctrl+K`), CodeMirror 6 syntax editing, and low-latency interaction.

---

## 2. Information Architecture & Navigation Map

```
┌────────────────────────────────────────────────────────────────────────┐
│                        SEAM PRODUCT NAVIGATION                         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
    ┌───────────────┬───────────────┼───────────────┬────────────────┐
    ▼               ▼               ▼               ▼                ▼
[1. Home /      [2. Dashboard]  [3. Projects]   [4. Workspace]   [5. Design Studio]
 Landing]       - Active Run    - Wizard        - Explorer       - 10 Diagrams
 - 6 Agents     - Health Matrix - Scale         - CodeMirror     - Visual Nodes
 - Workflow     - Activity Feed - Tech Prefs    - SEAM Cockpit   - JSON/Mermaid
    │               │               │               │                │
    ├───────────────┼───────────────┼───────────────┼────────────────┤
    ▼               ▼               ▼               ▼                ▼
[6. Test Lab]   [7. Contracts]  [8. Repair]     [9. Runtime]     [10. Models]
 - 17 Categories- 3-Way Parity  - Defect Tracing- Process State  - Qwen3.8-Flash
 - Truthful     - Drift Check   - Closed-Loop   - Port Tracker   - Docker Runner
 - Logs/Duration- OpenAPI Spec  - Targeted Test - Confinement    - Fallback Logs
    │               │               │               │                │
    ├───────────────┴───────────────┴───────────────┴────────────────┤
    ▼
[11. Delivery]      [12. Evaluation]    [13. Experiments]
 - Release Gate      - Neutral Metrics   - 4 Ablations
 - Docker / K8s      - Tool Telemetry    - Scenario Catalog
    │
    ▼
[14. Integrations]  [15. Readiness]     [16. Settings]
 - GitHub / n8n      - System Gates      - Config Specs
 - Port Probes       - Hardware Notice   - Secrets Scrubbed
```

---

## 3. Detailed View Specifications

### View 1: Home / Landing Page (`/home`)
- **Hero Section:** High-contrast title *"Build Software End-to-End with Autonomous AI Agents"*, primary CTA to Start Building, secondary CTA to Open Architecture.
- **Workflow Map:** Visual 7-step sequence (`Requirement` $\to$ `Analysis` $\to$ `Planning` $\to$ `Coding` $\to$ `QA` $\to$ `Repair` $\to$ `Delivery`).
- **Six Canonical Agents Grid:** Highlights AnalysisAgent, PlanningAgent, SupervisorAgent, CodingAgent, QAAgent, DeliveryAgent with exact roles and artifacts.
- **Autonomous Repair Highlight:** Explains closed-loop defect localization and targeted test recovery.
- **Integrations Strip:** Live indicators for GitHub, n8n, Docker, Ollama, ChromaDB, FastAPI.

### View 2: Dashboard (`/dashboard`)
- **KPI Metrics Strip:** Total Projects, Active Runs, Completed Runs, QA Status.
- **Recent Activity Feed:** Event stream from `EventStore` showing recent agent actions with relative timestamps.
- **Subsystem Integrations Card:** Live health status of Backend, RAG, GitHub, and n8n.

### View 3: Project Wizard (`/projects`)
- **Creation Form:** Project Name, Requirements Specification (multi-line textarea), Domain Selector (`General`, `E-commerce`, `Healthcare`, `Finance`, `Travel`, `Custom`), Technology Preferences (`FastAPI, React, SQLite`).
- **Scale-Aware Engine:** Selects architecture scale (`SMALL`, `MEDIUM`, `LARGE`, `ENTERPRISE`) based on requirement complexity.
- **Project Cards Grid:** Lists all projects on disk with domain tag, current workflow status, and quick-open actions.

### View 4: Workspace IDE (`/workspace`)
- **Dock Layout:**
  - **Left Dock (240px):** Project Explorer with file tree, file creation, folder creation, rename, delete, and filtering.
  - **Center Dock (Flexible):** CodeMirror 6 Editor supporting Python, JavaScript, TypeScript, JSON, Markdown, CSS, and HTML with syntax highlighting, search/replace, line numbers, word wrap, and dirty state tracking.
  - **Right Dock (320px):** SEAM Assistant / Agent Cockpit displaying active agent, model, current task, progress bar, tools executed, and chat history.
  - **Bottom Dock (Expanded):** Multi-tab console featuring Logs (real-time stream), Agents summary, Tasks progress, Problems (errors/warnings), and Output.

### View 5: Design Studio (`/design`)
- **10 Canonical Diagrams:** Architecture, Use Case, Class, Object, Sequence, Activity, DFD Level 0, DFD Level 1, ERD (Database), Deployment.
- **Canvas Features:** Sugiyama hierarchical layout, visual nodes with attributes and connections, strict JSON view, Mermaid export with 1-click clipboard copy.
- **Validation Badges:** Displays `VALID`, `INVALID`, `STALE`, or `REGENERATE REQUIRED`.

### View 6: Test Lab (`/testlab`)
- **17 Test Categories:** Unit, Integration, Smoke, Regression, API, Contract, E2E, Accessibility, Security, Dependency, Coverage, Performance, Load, Database, Migration, Mutation, Runtime.
- **Truthful Status Engine:** Distinct color badges for `PASS`, `FAIL`, `RUNNING`, `NOT_CONFIGURED`, `NOT_APPLICABLE`, `UNKNOWN`.
- **Detail Drawer:** Shows tool runner, execution duration in milliseconds, and full verified evidence text.

### View 7: Full-Stack Contract Intelligence (`/contracts`)
- **Three-Way Parity Grid:**
  - **Column 1:** Frontend Architecture Plan (UI components, stores, API hooks).
  - **Column 2:** OpenAPI 3.1 Endpoints (Method, Path, Summary, Request/Response models).
  - **Column 3:** Database Relational Schemas (Tables, Primary/Foreign keys, Columns).
- **Drift Detector:** Displays issue count and flags endpoint/schema mismatches.

### View 8: Autonomous Defect Repair Center (`/repair`)
- **Pipeline Progress Bar:** 6 sequential stages (`Defect Detected` $\to$ `AST Localized` $\to$ `Repair Planned` $\to$ `Patch Injected` $\to$ `Targeted Test` $\to$ `Regression Pass`).
- **Defect Inspector:** Deep-dive cards showing defect location, failure evidence, root cause analysis, automated repair plan, targeted test result, and full regression verification.

### View 9: Runtime & Process Console (`/runtime`)
- **Process Tracker:** Real-time PID, port binding, and status for FastAPI (8000), Vite (5173), Docker Model Runner (12434), and Ollama (11434).
- **Security Confinement:** Confirms localhost socket confinement and project-root directory boundary enforcement.

### View 10: Model Router & Inference Control (`/models`)
- **Model Catalog:** Detailed cards for `qwen2.5-coder:1.5b` (Local verified), `ai/qwen3.8-flash-next` (High-tier candidate), `ai/devstral-small-2` (Agentic workstation), `qwen3-coder:30b` (Workstation), and `qwen3-coder:480b-cloud` (Cloud escalation).
- **Transparent Fallback Banner:** Explains automated fallback routing and `MODEL_FALLBACK_TRIGGERED` event emission.
- **Task Routing Table:** Full matrix mapping agents to high-tier candidates and local fallbacks.

### View 11: Command Palette (`Ctrl+K`)
- Accessible search modal with instant keyboard navigation for all primary workflow triggers, views, and system operations.
