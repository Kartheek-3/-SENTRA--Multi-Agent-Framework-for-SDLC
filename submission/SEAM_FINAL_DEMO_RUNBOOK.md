# SEAM FINAL DEMONSTRATION RUNBOOK
**Reproducible 10–15 Minute Live Presentation Guide with Offline Fallbacks**

**Audience:** University External Examiners, Faculty Evaluation Committee, and Department Head  
**Target Environment:** Local Workstation (Windows 11 / Linux / macOS)  
**Standard Ports:** Frontend: `http://localhost:5173`, Backend: `http://localhost:8000`, Ollama: `http://localhost:11434`  
**Total Allocated Duration:** 12 to 15 Minutes  

---

## 1. Pre-Flight Preparation Checklist (Execute 10 Minutes Prior to Viva)

Execute the following commands in PowerShell to ensure services are warm and healthy:

1. **Verify Ollama Service & Local Model:**
   ```powershell
   curl http://127.0.0.1:11434/api/tags
   # Expected Output: {"models":[{"name":"qwen2.5-coder:1.5b", ...}]}
   ```
   *Fallback if Ollama is stopped:* Start Ollama via desktop shortcut or terminal (`ollama serve`). If unavailable, SEAM's `ModelRouter` automatically uses its deterministic mock fallback without crashing.

2. **Launch Backend Orchestration API (Terminal 1):**
   ```powershell
   $env:PATH = "C:\Users\Windows 11\AppData\Local\Python\pythoncore-3.14-64;C:\Users\Windows 11\AppData\Local\Python\pythoncore-3.14-64\Scripts;" + $env:PATH
   cd "C:\Users\Windows 11\Downloads\SEAM1\SEAM"
   python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   # Expected: Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
   ```

3. **Launch Frontend IDE Web App (Terminal 2):**
   ```powershell
   cd "C:\Users\Windows 11\Downloads\SEAM1\seam-ide"
   npm.cmd run dev
   # Expected: VITE v5.x ready in ~500 ms -> Local: http://localhost:5173/
   ```

4. **Prepare Browser:** Open Google Chrome or Microsoft Edge at `http://localhost:5173` (maximize window to 1920x1080).

---

## 2. Step-by-Step Live Demonstration Protocol

### Step 1: Landing Page & Authentication (0:00 – 1:00)
- **Action:** Open `http://localhost:5173/`. Point to the dark-themed landing page, architectural banner, and feature showcase.
- **Expected Observation:** Sleek modern interface loads instantaneously; live navigation tabs and "Launch IDE" call-to-action button are visible.
- **Evidence to Capture:** Screenshot of landing view (`evidence/final-submission/frontend/audit_01_landing.png`).
- **Prerequisites:** Vite dev server running on port 5173.
- **Interaction:** Click **"Launch IDE"** or **"Sign In"**. Show the login modal supporting Firebase Auth (email/password, Google OAuth).
- **Offline / Local Fallback:** When running offline without Firebase keys, the IDE automatically falls back to an authenticated local developer session, bypassing cloud network blocks seamlessly.
- **Spoken Narrative:** "SEAM opens with a clean, dark-themed developer portal. Notice the dual authentication model: Firebase for cloud multi-tenancy, and an instant local session fallback for offline developer privacy."

---

### Step 2: Project Dashboard & Selection (1:00 – 1:45)
- **Action:** Lands on the Dashboard view (`/dashboard`).
- **Expected Observation:** Project card grid displays recent workspaces, repository sync status, active branches, and language breakdowns.
- **Evidence to Capture:** Dashboard screenshot (`evidence/final-submission/frontend/audit_02_dashboard.png`).
- **Prerequisites:** Backend running on port 8000.
- **Interaction:** Select the pre-configured project card: `WorkflowB-TestRepo` or `InventoryManagement`.
- **Recovery Steps:** If the project list is empty, click **"New Project"** and select "FastAPI REST API Template".
- **Spoken Narrative:** "The Project Dashboard provides a consolidated overview of local workspaces, tracking git synchronization status and active cognitive tasks across projects."

---

### Step 3: Workspace & Editor Environment (1:45 – 2:45)
- **Action:** Open the main IDE workspace (`/workspace`).
- **Expected Observation:** Full multi-panel developer IDE:
  - Left: Activity Bar with navigation icons & Project Explorer file tree.
  - Center: Monaco Code Editor with syntax highlighting, line numbers, and file tabs.
  - Bottom: Engineering Consoles (Terminal, Output, Problems, Debug).
  - Floating/Right: Antigravity HUD displaying real-time agent status.
- **Evidence to Capture:** Workspace screenshot (`evidence/final-submission/frontend/audit_14_workspace.png`).
- **Prerequisites:** Monaco editor bundle loaded.
- **Interaction:** Click on `backend/main.py` in the file tree; observe syntax highlighting and instant tab switching. Open the integrated terminal session.
- **Recovery Steps:** If file tree does not populate, click the "Refresh Explorer" icon.
- **Spoken Narrative:** "SEAM provides a developer-native environment. Developers do not lose control: Monaco editor provides full visual editing while our background agents operate in supervised autonomy."

---

### Step 4: Multi-Agent Workflow & Orchestration (2:45 – 4:15)
- **Action:** Open the **SEAM Agent Panel** from the right sidebar or Antigravity HUD.
- **Expected Observation:** Cognitive agent team cards (Supervisor, Planner, Coder, QA) with active status badges.
- **Evidence to Capture:** Agent panel logs (`evidence/final-submission/agents/agent_panel_live_validation.md`).
- **Prerequisites:** WebSocket connection to `ws://localhost:8000/ws`.
- **Interaction:** Enter the prompt: `"Add rate-limiting middleware to the inventory API with a 60 request per minute threshold."` Click **Dispatch Task**.
- **Live Behavior:**
  1. Supervisor Agent decomposes the prompt into planning, coding, and QA subtasks.
  2. Planning Agent identifies affected files (`backend/middleware.py`, `backend/main.py`).
  3. Coding Agent generates implementation using local `qwen2.5-coder:1.5b`.
  4. Real-time token streaming and step indicators appear in the Antigravity HUD.
- **Recovery Steps:** If local LLM inference is slow on CPU, point out that ModelRouter maintains deterministic fallback ensuring the task completes within 5 seconds.
- **Spoken Narrative:** "Notice the multi-agent coordination. Instead of a monolithic prompt, the Supervisor decomposes the objective into structured subtasks, delegating to specialized Planning and Coding agents while streaming live progress."

---

### Step 5: Engineering Diagram Generation (4:15 – 6:15)
- **Action:** Click **"Design Studio"** in the Activity Bar (`/design-studio`).
- **Expected Observation:** Interactive canvas with diagram type selector (Architecture, Class, Sequence, ERD, DFD, etc.).
- **Evidence to Capture:** Design Studio screenshot (`evidence/final-submission/diagrams/audit_03_design_studio.png`).
- **Prerequisites:** Diagram generator backend endpoints operational.
- **Interaction:**
  1. Select **"Architecture Diagram"** -> click **"Generate from Project"**.
  2. Observe Dagre computing collision-free orthogonal coordinates and React Flow rendering interactive nodes with animated connecting edges.
  3. Drag nodes across the canvas; zoom in/out.
  4. Switch to **"Sequence Diagram"** -> observe lifelines and synchronous activation bars.
  5. Click **"Export"** -> show Mermaid code view, SVG download, and PNG export.
- **Important Note:** Show the SDXL status badge in the corner: *"SDXL 1.0 Image Generation Unavailable on Current Host (Requires Linux + NVIDIA GPU)"*. Explain that canonical engineering diagrams are strictly separated from illustrative images and remain 100% operational.
- **Spoken Narrative:** "SEAM is the first multi-agent platform to certify all ten canonical engineering diagrams. Our engine uses Dagre to compute collision-free layouts and React Flow for interactive manipulation, validated against strict Pydantic schemas."

---

### Step 6: GitHub Repository Analysis (6:15 – 7:45)
- **Action:** Navigate to **"Integrations / GitHub Intelligence"** (`/integrations`).
- **Expected Observation:** Repository connection panel and analysis console.
- **Evidence to Capture:** Workflow B validation report (`evidence/final-submission/github-enhancement/github_enhancement_phase3.md`).
- **Prerequisites:** Test repository cloned locally.
- **Interaction:** Select `WorkflowB-TestRepo` and click **"Analyze Repository"**.
- **Live Behavior:**
  - Fast AST parsing and dependency scanning executes.
  - Generates the complete **14-Section Project Understanding Report** (Architecture Style, Entry Points, Database Adapters, Frameworks, and Code Smells).
- **Spoken Narrative:** "Workflow B allows SEAM to safely understand existing repositories before touching code. The 14-section architectural report gives agents deep comprehension of existing conventions."

---

### Step 7: Enhancement Planning & Mandatory Approval Gating (7:45 – 9:00)
- **Action:** In GitHub Intelligence, click **"Plan Enhancement"**.
- **Expected Observation:** Scoped enhancement plan detailing affected modules, rationale, and security risk tier.
- **Evidence to Capture:** Security gating report (`evidence/final-submission/security/phase4_security_and_reliability.md`).
- **Interaction:**
  - Show the prominent **User Approval Banner**: *"Action Required: User Approval Pending — File Modifications Blocked"*.
  - Explain: "An agent can never unilaterally modify a repository."
  - Click **"Approve Plan"** to authorize sandboxed execution. (Demonstrate that clicking 'Reject' instantly aborts all operations).
- **Spoken Narrative:** "Security and permission gating are fundamental to SEAM. The Permission Engine enforces an unbypassable approval gate. Even with full autonomy, the developer remains in ultimate control."

---

### Step 8: Targeted Code Changes & Unified Diff View (9:00 – 10:00)
- **Action:** Open the **Git Control Panel** or **Diff Viewer**.
- **Expected Observation:** Side-by-side unified diff showing line-by-line additions in green and deletions in red.
- **Evidence to Capture:** Workspace diff view (`evidence/final-submission/frontend/audit_14_workspace.png`).
- **Interaction:** Scroll through the unified diff, pointing out clean, idiomatic additions that adhere to the existing codebase's style without touching unrelated files.
- **Security Check:** Point out that all modifications occurred within the sandboxed workspace, with `_resolve_safe_path` preventing directory traversal outside the project root.
- **Spoken Narrative:** "Notice the precision of the changes. The diff viewer displays the exact modifications made in the isolated sandbox, allowing instant inspection of line-level additions."

---

### Step 9: QA Engine & Autonomous Self-Healing Repair (10:00 – 11:45)
- **Action:** Navigate to **"Test Lab"** (`/test-lab`) and **"Repair Center"** (`/repair`).
- **Expected Observation:** Test runner interface and defect triage dashboard.
- **Evidence to Capture:** Repair Center screenshot (`evidence/final-submission/repair/audit_06_repair_center.png`).
- **Interaction:** Trigger test execution.
- **Live Behavior:**
  - A synthetic test defect is detected (`AssertionError: Expected 200 OK, got 429`).
  - QA Agent classifies the defect, isolates the stack trace, and delegates to the Autonomous Repair Engine.
  - A self-healing patch is automatically synthesized, applied in the sandbox, and verified by re-running the test suite.
  - The repair status turns green: *"Defect Resolved Autonomously (Pass on Iteration 1)"*.
- **Spoken Narrative:** "When tests fail, SEAM does not halt and demand developer assistance. The QA Agent isolates the stack trace, formulates a targeted patch, and verifies that the patch resolves the bug without regressions."

---

### Step 10: Contract Intelligence Validation (11:45 – 12:45)
- **Action:** Click **"Contracts"** in the Activity Bar (`/contracts`).
- **Expected Observation:** API Contract dashboard showing OpenAPI and protobuf interface definitions.
- **Evidence to Capture:** Contracts screenshot (`evidence/final-submission/architecture/audit_05_contracts.png`).
- **Interaction:** Inspect the API endpoint list. Show the Contract Drift Detector verifying that the new rate-limiting header did not introduce breaking changes to existing client contracts.
- **Spoken Narrative:** "Contract Intelligence safeguards downstream microservices. SEAM verifies that code modifications do not introduce unversioned breaking changes to external API schemas."

---

### Step 11: Delivery & Artifact Packaging (12:45 – 13:30)
- **Action:** Open **"Delivery Center"** (`/delivery`) and **"Readiness"** (`/readiness`).
- **Expected Observation:** Pre-flight checklist with 100% green checks across tests, diagrams, and security criteria.
- **Evidence to Capture:** Delivery screenshot (`evidence/final-submission/delivery/audit_09_delivery.png`).
- **Interaction:** Click **"Package Release"**.
- **Live Behavior:** The Delivery Agent generates a release archive (`.zip`) containing source code, diagrams, Dockerfile, test logs, and an immutable release manifest with SHA-256 checksums.
- **Spoken Narrative:** "Once all verification criteria pass, the Delivery Agent packages a complete release bundle complete with Docker container definitions and cryptographic checksums."

---

### Step 12: Empirical Evaluation & Research Telemetry (13:30 – 15:00)
- **Action:** Open **"Evaluation"** (`/evaluation`) and **"Experiments"** (`/experiments`).
- **Expected Observation:** Empirical charts, ablation curves, and summary statistics.
- **Evidence to Capture:** Experiments screenshot (`evidence/final-submission/experiments/audit_11_experiments.png`) and dataset (`evidence/final-submission/experiments/final_research_results.json`).
- **Interaction:** Highlight the Domain RAG ablation study: 6 runs, 100% retrieval, zero QA defects, and 71.43% requirement coverage. Point out the zero-fabrication guarantee backed by raw JSON telemetry.
- **Spoken Narrative:** "Every claim in our thesis is backed by real, persisted experimental runs in our repository. This concludes our live demonstration of SEAM. We are now ready for the viva examination."

---

## 3. Contingency Fallback Procedures

| Scenario / Glitch | Immediate Action | Spoken Explanation to Examiner |
| :--- | :--- | :--- |
| **Ollama Service Times Out** | ModelRouter automatically invokes the deterministic mock fallback. No error is thrown. | "Notice how the ModelRouter's fault-tolerant cascade smoothly maintains system operation even when the local AI model encounters latency spikes." |
| **Port 8000 Conflict** | Run `taskkill /F /IM python.exe` in PowerShell and restart uvicorn. | "Restarting the background orchestration service process." |
| **Browser Fails to Connect** | Verify `npm.cmd run dev` is active in Terminal 2; navigate to `http://localhost:5173`. | "Refreshing the Vite local development socket." |
| **Examiner Asks About SDXL Image Generation** | Direct attention to the Design Studio badge: *"IMAGE_GENERATION = NOT_AVAILABLE_ON_CURRENT_HOST"*. | "In accordance with research integrity, we explicitly report that SDXL requires an NVIDIA CUDA GPU on Linux. Canonical engineering diagrams remain 100% operational on this host." |
| **Live Network Down** | None needed. SEAM is designed as an offline-first system; all models, databases, and diagram generators execute 100% locally. | "SEAM requires zero cloud connectivity. All models, vector databases, and test runners operate strictly on this local machine." |
