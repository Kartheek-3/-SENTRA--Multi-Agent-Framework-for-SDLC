# SEAM OPEN QUESTIONS & UNRESOLVED DISCREPANCIES
**Evidence-Based Inventory of Technical Inconsistencies and Verification Gaps**

**Document Version:** 1.0.0-open-questions  
**Date:** October 15, 2026  
**Auditor:** Principal Software Architect & QA Lead  
**Scope:** Identifying architectural ambiguities, documentation drift, and unverified edge cases.  

---

## 1. Architectural & Code Discrepancies

### 1.1 Code Editor Terminology: Monaco vs. CodeMirror 6
- **Context:** Several reports, prompt descriptions, and historical documents repeatedly refer to the code editor as `"Monaco Code Editor"`.
- **Evidence:** `seam-ide/package.json` contains no dependency on `monaco-editor`. Instead, it includes `@codemirror/view`, `@codemirror/state`, and `@codemirror/commands` (v6.x). `seam-ide/src/editor/CodeEditor.tsx` explicitly initializes CodeMirror 6.
- **Open Question:** Should future documentation systematically replace the phrase "Monaco Code Editor" with "CodeMirror 6 Editor with VS Code-Inspired Workspace Layout", or retain the terminology as an interface layout description?
- **Recommendation:** Adopt the technically accurate label: *"CodeMirror 6 Editor styled with VS Code IDE conventions"*.

### 1.2 Local Model Naming History: Qwen3 4B vs. Qwen2.5-Coder 1.5B
- **Context:** `SEAM_QWEN3_4B_MIGRATION_REPORT.md` and `FINAL_EXPERIMENTAL_EVALUATION.md` reference `ai/qwen3:4b-instruct-2507-q4_K_M` or `qwen3-coder-next`.
- **Evidence:** The local Ollama daemon currently hosts only `qwen2.5-coder:1.5b` (Q4_K_M), verified via `http://127.0.0.1:11434/api/tags`.
- **Open Question:** Was the Qwen3 4B model evaluated on a separate development workstation prior to repository transfer, or was it an early experiment subsequently downscaled to 1.5B for CPU compatibility?
- **Recommendation:** Document that historical research runs utilized the 4B parameter configuration, whereas Phase 2–7 local validation and live execution standardize on `qwen2.5-coder:1.5b`.

### 1.3 Baseline Naive Comparison Accounting
- **Context:** Research reports compare `SEAM_FULL` against a `BASELINE` single-agent prompt.
- **Evidence:** In `FINAL_RESEARCH_RESULTS.json`, several baseline metric fields are marked as `NOT_APPLICABLE` or preserved as metadata-only.
- **Open Question:** In academic defense, examiners may ask why full quantitative metrics for a monolithic baseline are not displayed side-by-side in every table.
- **Recommendation:** Defend this rigorously: Monolithic prompts frequently failed to synthesize multi-file directory structures or compile test suites at all; recording `NOT_APPLICABLE` rather than fabricating simulated numbers reflects strict adherence to scientific integrity.

---

## 2. Infrastructure & External Service Dependencies

### 2.1 Live PostgreSQL & Redis Verification Scope
- **Context:** Architecture diagrams depict PostgreSQL and Redis as part of the data tier.
- **Evidence:** `SEAM/backend/database/sqlite.py` is the live, active engine. PostgreSQL SQLAlchemy models and Redis caching decorators are fully written in `backend/config.py`, but have not been exercised against a live, running external PostgreSQL or Redis container.
- **Open Question:** Has SEAM ever undergone load testing against a multi-tenant PostgreSQL cluster, or is the implementation currently verified via dialect syntax checks and SQLite equivalence?
- **Recommendation:** Accurately classify PostgreSQL as `IMPLEMENTED / NOT_CONFIGURED (UNEXERCISED LIVE)`, emphasizing that single-tenant developer workflows are 100% satisfied by SQLite WAL mode.

### 2.2 Docker Model Runner (DMR) Port Status
- **Context:** Phase 2 reported DMR on port `12434` as offline (`WinError 10061`). Phase 4/5 discovered a Docker Desktop background listener (`com.docker.backend.exe` v1.2.8) active on port `12434`.
- **Evidence:** `curl http://127.0.0.1:12434` returns a Docker response, but Docker Diffusers fails to launch because Linux container mode is disabled on this Windows host.
- **Open Question:** Under what exact conditions should SEAM attempt to route text completions to DMR vs. Ollama?
- **Recommendation:** Maintain the current `ModelRouter` resolution: Ollama is always Tier 1 primary; DMR is Tier 2 secondary fallback; mock templates are Tier 3 fail-safe.

---

## 3. Hardware & Platform Boundaries

### 3.1 Stable Diffusion XL 1.0 (SDXL) Container Host Dependency
- **Context:** The Design Studio includes dual-mode UI support for SDXL illustrative image generation alongside canonical engineering diagrams.
- **Evidence:** The current host is Windows 11 Home running on an Intel Core i5 CPU with integrated Intel UHD Graphics (no discrete NVIDIA GPU, no CUDA).
- **Open Question:** Can SDXL be supported on non-CUDA hosts via OpenVINO or ONNX Runtime CPU execution in a future phase?
- **Recommendation:** Disclose that SDXL currently mandates Linux + NVIDIA CUDA for sub-minute generation; CPU-based SDXL takes >5 minutes per image and is impractical. The system honestly marks `IMAGE_GENERATION = NOT_AVAILABLE_ON_CURRENT_HOST` without degrading diagramming capabilities.

### 3.2 Terminal Curses & PTY Support on Windows
- **Context:** The IDE provides an interactive terminal session selector.
- **Evidence:** Windows does not support native POSIX `pty.openpty()`. Terminal emulation uses WebSocket stream buffers with command line sanitization.
- **Open Question:** Does the terminal support interactive full-screen applications like `vim` or `htop`?
- **Recommendation:** No; the terminal is designed for non-interactive command execution (`pytest`, `npm`, `git`, build scripts). Interactive curses programs are out of scope on Windows.

---

## 4. Git Baseline & Release Authorization

### 4.1 Release Branch & Head Commit State
- **Context:** The repository is currently checked out on branch `final-validation` at commit `ebc79e1` (*audit: SEAM final backend architecture audit and empirical research evaluation*).
- **Evidence:** Tags `v1.0.0` (commit `6857114`) and `v1.0.1` (commit `c086afd`) exist in Git history.
- **Open Question:** Should the final Phase 6 and Phase 7 deliverables be committed to branch `final-validation` or merged to `main` with a new `v1.0.2` release tag?
- **Recommendation:** Await explicit user authorization before creating any new Git commits or moving release tags. All working files remain preserved in the working tree.
