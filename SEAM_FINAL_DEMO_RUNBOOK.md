# SEAM FINAL DEMONSTRATION RUNBOOK
**Reproducible 10–15 Minute Live Presentation Guide**

**Audience:** Evaluators, Faculty Examiners, and Software Engineering Leads  
**Target Environment:** Windows 11 / Linux / macOS  
**Default Ports:** Frontend `http://localhost:5173`, Backend `http://localhost:8000`, Ollama `http://localhost:11434`  
**Presentation Duration:** 12 to 15 Minutes  

---

## Pre-Flight Checklist (Run 5 Minutes Before Presentation)

1. **Verify Local Model Service (Ollama):**
   ```powershell
   curl http://127.0.0.1:11434/api/tags
   # Expected response: {"models":[{"name":"qwen2.5-coder:1.5b", ...}]}
   ```
   *Fallback if Ollama is offline:* SEAM automatically cascades to the deterministic mock fallback with zero crashes.

2. **Start Backend API (Terminal 1):**
   ```powershell
   $env:PATH = "C:\Users\Windows 11\AppData\Local\Python\pythoncore-3.14-64;C:\Users\Windows 11\AppData\Local\Python\pythoncore-3.14-64\Scripts;" + $env:PATH
   cd "C:\Users\Windows 11\Downloads\SEAM1\SEAM"
   python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Start Frontend IDE (Terminal 2):**
   ```powershell
   cd "C:\Users\Windows 11\Downloads\SEAM1\seam-ide"
   npm.cmd run dev
   # Vite starts on http://localhost:5173/
   ```

4. **Open Browser:** Navigate to `http://localhost:5173`.

---

## 12-Step Demonstration Script

### Step 1: Landing Page & Authentication (1:00 min)
- **Action:** Open `http://localhost:5173/`. Point out the dark-themed landing page, architectural highlights, and live feature ticker.
- **Narrative:** "SEAM is a multi-agent framework designed to automate the complete software development lifecycle while enforcing strict permission gating and architectural rigor."
- **Interaction:** Click **"Launch IDE"** or **"Sign In"**. Show the login modal supporting Firebase Auth (email/password and Google OAuth) with automatic offline/development session bypass for seamless local evaluation.

### Step 2: Project Dashboard & Selection (0:45 min)
- **Action:** Lands on the Dashboard view. Show the project selector card list.
- **Narrative:** "The Dashboard acts as the project hub, displaying recent local projects, GitHub repositories, and synchronization status."
- **Interaction:** Select the default test project (`InventoryManagement` or `WorkflowB-TestRepo`).

### Step 3: Workspace & Editor Environment (1:00 min)
- **Action:** The workspace view opens with a full IDE interface.
- **Visuals:** 
  - Left: Activity Bar & Project Explorer with file tree.
  - Center: Monaco Code Editor with syntax highlighting, line numbers, and tab management.
  - Bottom: Engineering Consoles (Terminal, Output, Problems, Debug).
  - Floating/Right: Antigravity HUD showing active agent status.
- **Narrative:** "SEAM provides a rich, developer-native environment. Developers retain complete visual control while agents operate in supervised autonomy."

### Step 4: Multi-Agent Workflow & Orchestration (1:30 min)
- **Action:** Open the **SEAM Agent Panel** from the right sidebar or HUD.
- **Interaction:** Enter a task prompt: `"Add rate-limiting middleware to the inventory API."` Click **Dispatch Task**.
- **Live Behavior:**
  1. **Supervisor Agent** breaks the prompt into planning, coding, and QA subtasks.
  2. **Planning Agent** determines file dependencies.
  3. **Coding Agent** generates implementation using local `qwen2.5-coder:1.5b`.
  4. Live stream updates appear in the HUD with step-by-step token generation.
- **Narrative:** "Notice how the Supervisor dynamically routes work across specialized agents rather than relying on a monolithic prompt."

### Step 5: Engineering Diagram Generation (2:00 min)
- **Action:** Click the **Design Studio** icon in the Activity Bar.
- **Interaction:**
  - Select diagram type: **Architecture**, **Sequence**, or **Class**.
  - Click **"Generate from Project"**.
- **Live Behavior:**
  - The deterministic parser extracts components, services, and relationships.
  - Dagre computes an optimal, orthogonal hierarchical layout.
  - React Flow renders interactive, draggable nodes with animated connecting edges.
- **Interaction:** Click **"Export"** -> show Mermaid code, SVG, and PNG generation options.
- **Narrative:** "SEAM supports all ten canonical engineering diagram types, certified for UML and data flow accuracy."

### Step 6: GitHub Repository Analysis (1:30 min)
- **Action:** Open **Integrations / GitHub Intelligence** view.
- **Interaction:** Connect a sample repository URL or select existing cloned repo. Click **"Analyze Repository"**.
- **Live Behavior:**
  - Fast AST and dependency scanning executes.
  - 14-section Project Understanding report generates, highlighting frameworks, database drivers, architecture style, and potential code debt.
- **Narrative:** "Workflow B allows SEAM to deeply comprehend an existing codebase before attempting modifications."

### Step 7: Enhancement Planning & Approval Gating (1:15 min)
- **Action:** In GitHub Intelligence, click **"Plan Enhancement"**.
- **Narrative:** "Security and permission gating are fundamental to SEAM. An agent is never allowed to unilaterally push changes."
- **Interaction:**
  - Review the proposed Enhancement Plan: scoped file modifications, rationale, risk tier.
  - Show the **Approval Gating Banner**: "Action Required: User Approval Pending".
  - Demonstrate clicking **"Approve Plan"**. (Mention that rejection completely aborts the operation).

### Step 8: Targeted Code Changes & Unified Diff View (1:00 min)
- **Action:** Navigate to the **Git Control Panel** or **Diff View**.
- **Live Behavior:**
  - Show the isolated sandbox workspace modification.
  - Display unified diff showing green additions and red deletions.
  - Emphasize that modifications are confined via `_resolve_safe_path()` to prevent traversal outside the project directory.

### Step 9: QA Engine & Autonomous Repair (1:45 min)
- **Action:** Click **"Test Lab"** or **"Repair Center"**.
- **Interaction:** Trigger the test runner.
- **Live Behavior:**
  - A synthetic test defect is detected (`AssertionError: Expected 200 OK, got 429`).
  - **QA Agent** classifies the defect, isolates the stack trace, and delegates to the **Autonomous Repair Engine**.
  - A self-healing patch is automatically proposed, verified against the test suite, and passed.
- **Narrative:** "Autonomous repair closes the loop between testing and implementation, reducing manual debugging cycles."

### Step 10: Contract Intelligence Validation (1:00 min)
- **Action:** Click **"Contracts"** in the Activity Bar.
- **Live Behavior:**
  - Inspect OpenAPI and protobuf interface schemas.
  - Highlight breaking change detection (e.g., modified request payload fields).
- **Narrative:** "Contract intelligence safeguards downstream consumers by preventing unversioned breaking changes."

### Step 11: Delivery & Artifact Packaging (0:45 min)
- **Action:** Navigate to **"Delivery Center"**.
- **Interaction:** Click **"Package Release"**.
- **Live Behavior:**
  - Packages project files, Dockerfile, release notes, and canonical diagrams into a timestamped, signed `.zip` bundle.
  - Display the generated release checksum and manifest.

### Step 12: Empirical Research & Evaluation Dashboard (1:00 min)
- **Action:** Open the **"Evaluation"** and **"Experiments"** consoles.
- **Live Behavior:**
  - Present empirical metrics backed by `FINAL_RESEARCH_RESULTS.json`.
  - Highlight Domain-Aware RAG ablation: requirement coverage, token efficiency, and QA defect reduction across multiple runs.
- **Narrative:** "All research claims are backed by persisted, reproducible experimental runs with rigorous statistical validation."

---

## Troubleshooting & Contingency Actions

| Symptom | Cause | Instant Fix |
| :--- | :--- | :--- |
| Ollama connection timeout | Service stopped or busy | Backend automatically falls back to deterministic mock. No crash occurs. |
| Port 8000 already in use | Stale uvicorn process | Run `taskkill /F /IM python.exe` then restart uvicorn. |
| Vite dev server port conflict | Default 5173 occupied | Run `npx.cmd vite --port 5174` and open `http://localhost:5174`. |
| SDXL Image Gen shows unavailable | Expected on Windows non-CUDA | Point to informational badge: accurately reports host hardware constraint while diagrams remain functional. |
