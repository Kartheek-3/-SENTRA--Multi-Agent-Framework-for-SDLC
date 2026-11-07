# SEAM IDE — Standalone Developer Interface

> **Frontend Client**: React 18 + TypeScript + Vite + CodeMirror 6 + Tauri Desktop Scaffold  
> **Backend Integration**: Communicates with FastAPI backend on `http://127.0.0.1:8000`

---

## 1. Overview

**SEAM IDE** is a high-performance standalone developer environment tailored specifically for autonomous multi-agent software engineering. It provides rich visual telemetry, real-time agent observability, interactive software architecture diagrams, contract validation, and autonomous defect repair consoles.

### Core Architectural Features
- **Code Editor**: Integrated CodeMirror 6 editor supporting multi-file tabs, syntax highlighting, and inline diagnostic linting.
- **Visual Design Studio**: Interactive rendering of all 10 canonical software engineering diagrams powered by Mermaid.js and React Flow.
- **Antigravity HUD**: Live agent execution status, cognitive trace streaming, and phase progression indicator.
- **Contract & Repair Consoles**: Dedicated views for OpenAPI/Protobuf contract drift analysis and autonomous QA defect remediation.
- **Tauri Desktop Wrapper**: Native desktop application packaging scaffold using Rust and Tauri.

---

## 2. Directory Layout

```
seam-ide/
├── index.html                   # Single-page application entrypoint
├── package.json                 # Dependencies and npm scripts
├── tsconfig.json                # Strict TypeScript configuration
├── vite.config.ts               # Vite build configuration and proxy setup
├── vitest.config.ts             # Vitest unit test configuration
├── src/
│   ├── App.tsx                  # Root application router and shell
│   ├── api/                     # Backend API client adapters (Axios/Fetch)
│   ├── components/              # IDE panels and consoles
│   │   ├── AntigravityHUD.tsx   # Real-time agent status HUD
│   │   ├── ContractsPage.tsx    # API & Protobuf contract analyzer
│   │   ├── DeliveryCenterPage.tsx# Release packaging & manifest viewer
│   │   ├── DesignStudioPage.tsx # 10-diagram architecture visualizer
│   │   ├── ModelControlPanel.tsx# LLM router & provider selector
│   │   ├── RepairCenterPage.tsx # Autonomous QA repair console
│   │   ├── RuntimeConsolePage.tsx# Real-time event log streamer
│   │   └── TestLabPage.tsx      # Automated test runner console
│   ├── explorer/                # File tree explorer with backend filesystem sync
│   ├── layout/                  # ActivityBar, AppShell, and StatusBar
│   └── seam/                    # Authoritative agent state stores & hooks
└── src-tauri/                   # Tauri desktop packaging configuration (Rust)
```

---

## 3. Environment Configuration

The frontend connects to the SEAM FastAPI backend via HTTP and WebSocket/SSE streams. Configuration can be customized via `.env.local` or environment variables:

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `VITE_API_BASE_URL` | `http://127.0.0.1:8000` | Base URL of the SEAM FastAPI backend |
| `VITE_WS_BASE_URL` | `ws://127.0.0.1:8000` | WebSocket endpoint for live agent telemetry |

---

## 4. Getting Started

### Prerequisites
- **Node.js**: Version 18.x or 20.x LTS
- **npm**: Version 9.x or higher

### Installation
```bash
# Navigate to the IDE directory
cd seam-ide

# Install dependencies
npm install
```

### Running the Development Server
```bash
npm run dev
```
The IDE will launch locally at:
```text
http://127.0.0.1:5173
```

---

## 5. Testing and Validation

```bash
# 1. Type Checking
npx tsc --noEmit

# 2. Run Unit Test Suite (Vitest)
npm run test

# 3. Production Bundle Build
npm run build
```

---

## 6. Desktop Packaging (Tauri)

When building the native desktop executable (requires Rust and `cargo` installed):

```bash
# Run in desktop development mode
npm run tauri:dev

# Compile release desktop bundle
npm run tauri:build
```
The resulting binary will be emitted to `src-tauri/target/release/`.
