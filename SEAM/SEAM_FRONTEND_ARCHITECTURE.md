# SEAM v1.0.0 — Frontend Engineering & Technical Architecture Specification

**Project:** SEAM (Self-Evolving Autonomous Multi-Agent Framework)  
**Roles:** Principal Frontend Architect, Senior TypeScript / React Engineer, Performance Engineer  
**Status:** **APPROVED & COMPILED (0 TypeScript / 0 Vite Errors)**

---

## 1. Architectural Principles & Technology Stack

The frontend application (`seam-ide`) is engineered as a high-performance, developer-grade software engineering IDE. 

### Core Tech Stack:
- **UI Framework:** React 18.3.1 (Strict Mode)
- **Language:** TypeScript 5.5.3 (Strict type checking, zero implicit `any`)
- **Build Tool:** Vite 5.4.21 (Production bundle compiled in 3.29 seconds)
- **Code Editor Engine:** CodeMirror 6 (`@codemirror/state`, `@codemirror/view`, `@codemirror/language`, multi-language packs)
- **Desktop Shell:** Tauri v2 (`@tauri-apps/api`, `@tauri-apps/cli`)
- **State & Transport:** React hooks + Typed REST Client + Native WebSocket streaming

---

## 2. Directory & Component Architecture

```
seam-ide/src/
├── api/
│   ├── client.ts             # Typed REST API client (seamApi)
│   └── websocket.ts          # Resilient WebSocket connection & reconnect loop
├── components/
│   ├── CommandPalette.tsx    # Accessible modal with fuzzy keyboard navigation (Ctrl+K)
│   ├── ContractsPage.tsx     # 3-way schema parity inspector & drift detector
│   ├── DesignStudioPage.tsx  # 10 canonical diagrams with visual cards, JSON, Mermaid
│   ├── ModelControlPanel.tsx # Inference transparency, Qwen3.8-Flash-Next, task routing
│   ├── RepairCenterPage.tsx  # Closed-loop defect localization & self-healing timeline
│   ├── RuntimeConsolePage.tsx# Process lifecycle manager & socket confinement
│   └── TestLabPage.tsx       # 17-category testing ecosystem with truthful statuses
├── editor/
│   ├── CodeEditor.tsx        # CodeMirror 6 editor wrapper with dirty-state tracking
│   └── languages.ts          # Lazy-loaded language extensions (Py, JS, TS, JSON, MD, CSS, HTML)
├── explorer/
│   └── ProjectExplorer.tsx   # File system tree, file/folder creation, rename, delete
├── layout/
│   └── FlexibleLayout.tsx    # Multi-dock responsive layout grid (Left, Center, Right, Bottom)
├── seam/
│   ├── SeamPanel.tsx         # Agent Cockpit, task progress, tool execution feedback
│   ├── chatTypes.ts          # Structured message schemas & artifact metadata types
│   └── eventToChatMessage.ts # Real-time event translator mapping backend events to UI cards
├── App.tsx                   # Top-level ProductShell, navigation router, state manager
├── main.tsx                  # React DOM root entrypoint
└── styles.css                # Centralized SEAM Design System tokens & layout rules
```

---

## 3. Real Backend Integration & Telemetry Binding

SEAM completely rejects mock dashboards and decorative UI. Every visual component binds directly to live backend state:

| UI View | Primary Backend Endpoint | Real Data Payload |
| :--- | :--- | :--- |
| **Topbar & Health** | `GET /api/system/health` | Backend status, Ollama status, RAG status, GitHub status |
| **Project Selector**| `GET /api/projects` | Active project IDs, domains, workflow statuses |
| **Project Wizard** | `POST /api/projects` | Creates project with domain, scale, technology preferences |
| **Workspace Filetree**| `GET /api/projects/{id}/filesystem/tree` | Real disk file hierarchy under `.seam/workspace/` |
| **Code Editor** | `GET / PUT /api/projects/{id}/filesystem/file` | Reads and writes real source files on disk |
| **Agent Cockpit** | `GET /api/projects/{id}/status` | `ProjectState` tasks, current agent, execution plan |
| **Event Stream** | `WS /api/projects/{id}/events` | Real-time events (`AGENT_STARTED`, `TOOL_EXECUTED`, `FILE_GENERATED`) |
| **Design Studio** | `GET /api/projects/{id}/diagrams` | 10 canonical diagram Pydantic models & SVG/JSON assets |
| **Test Lab** | `GET /api/projects/{id}/status` | `latest_qa_status`, `failed_tasks`, unit/integration results |
| **Contracts View** | `GET /api/projects/{id}/status` | `SystemDesign` OpenAPI models vs `FrontendArchitecturePlan` |
| **Repair Center** | `GET /api/projects/{id}/status` | `defect_locations`, `repair_plans`, `repair_results` |
| **Runtime Console** | `GET /api/system/health` | Tracked processes (FastAPI, Vite, DMR, Ollama) and port bindings |
| **Model Router** | `GET /api/system/models` | Active provider, Docker runner status, Ollama installed models |
| **Integrations** | `GET /api/integrations/n8n/status` | Real n8n webhook reachability and event logging |
| **Experiments** | `GET /api/experiments` | Scenario catalog, ablation runs, and reproducibility data |

---

## 4. Performance & Bundle Metrics

- **Production Build Execution:** `3.29 seconds` (`tsc -b && vite build`)
- **Bundle Footprint:**
  - `dist/index.html`: `0.39 kB`
  - `dist/assets/index-DlIKcCo7.css`: `32.72 kB` (Gzip: `7.06 kB`)
  - `dist/assets/index-BTyDKcH4.js`: `882.99 kB` (Gzip: `297.98 kB`)
- **Rendering Optimizations:**
  - Zero unnecessary re-renders in the CodeMirror editor via isolated update hooks.
  - Event buffer slicing (max 300 messages) preventing browser memory leaks during long autonomous runs.
  - Native scrollbar gutters avoiding layout shifts during dynamic streaming.
