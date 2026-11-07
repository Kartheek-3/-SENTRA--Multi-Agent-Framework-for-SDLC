# SEAM DUPLICATE FILE AUDIT & TAXONOMY CLASSIFICATION

**Document Version:** 1.0.0-duplicates  
**Date:** October 15, 2026  
**Auditor Roles:** Senior Software Architect, Repository Auditor  
**Scope:** Exhaustive Deduplication Analysis across 1,607 Inspected Files  
**Duplicate Classification System:**
- **D1 — Exact Duplicate:** Identical SHA-256 byte-for-byte content.
- **D2 — Near Duplicate:** Substantially overlapping text/structure with minor edits or formatting variance.
- **D3 — Outdated Version:** Superseded by a demonstrably newer authoritative version.
- **D4 — Functional Redundancy:** Similar architectural purpose but differing implementations or paths.
- **D5 — Legitimate Same-Name Files:** Distinct files required by separate module contexts.
- **D6 — Unresolved:** Insufficient evidence to safely determine relationship.

---

## 1. Audit Summary Statistics

- **Total Exact Duplicate Groups (D1):** **174 distinct groups**
- **Total Files Involved in Exact Duplicates:** **459 files**
- **Total Near-Duplicate & Functional Redundancy Candidates (D2–D4):** **38 groups**
- **Legitimate Same-Name Files (D5):** **86 groups** (e.g., per-project `main.py`, `package.json`, `index.html`)

---

## 2. Category D1 — Exact Duplicates (Hash Verified)

The following tables document high-impact exact duplicates across the primary codebase domains:

### Group D1-A: Core Architecture & Validation Reports (Root vs. `SEAM/`)
These files were duplicated between the workspace root and the `SEAM/` backend subdirectory:

| File Group | SHA-256 Hash | Size | File Path 1 (Root) | File Path 2 (`SEAM/`) | Recommended Action |
| :--- | :---: | :---: | :--- | :--- | :--- |
| **Backend Architecture Audit** | `51498153701b...` | 16,754 B | `FINAL_BACKEND_ARCHITECTURE_AUDIT.md` | `SEAM/FINAL_BACKEND_ARCHITECTURE_AUDIT.md` | Keep Root; Archive `SEAM/` copy |
| **Experimental Evaluation** | `a3a3fec8deb0...` | 12,510 B | `FINAL_EXPERIMENTAL_EVALUATION.md` | `SEAM/FINAL_EXPERIMENTAL_EVALUATION.md` | Keep Root; Archive `SEAM/` copy |
| **Research Results JSON** | `e0cca6bcab35...` | 61,549 B | `FINAL_RESEARCH_RESULTS.json` | `SEAM/FINAL_RESEARCH_RESULTS.json` | Keep Root; Archive `SEAM/` copy |
| **Runtime Certification** | `e2c8a5d50d48...` | 5,065 B | `FINAL_RUNTIME_CERTIFICATION.md` | `SEAM/FINAL_RUNTIME_CERTIFICATION.md` | Keep Root; Archive `SEAM/` copy |
| **Test Evidence Summary** | `ebd6766b9ce5...` | 7,565 B | `FINAL_TEST_EVIDENCE.md` | `SEAM/FINAL_TEST_EVIDENCE.md` | Keep Root; Archive `SEAM/` copy |
| **Audit Summary** | `737b0b29f809...` | 6,219 B | `FINAL_AUDIT_SUMMARY.md` | `SEAM/FINAL_AUDIT_SUMMARY.md` | Keep Root; Archive `SEAM/` copy |
| **Database Architecture** | `6da49f08dc60...` | 8,064 B | `SEAM_DATABASE_ARCHITECTURE.md` | `SEAM/SEAM_DATABASE_ARCHITECTURE.md` | Keep Root; Archive `SEAM/` copy |
| **Docker Model Runner** | `4f152847eb27...` | 3,495 B | `SEAM_DOCKER_MODEL_RUNNER_FINAL.md` | `SEAM/SEAM_DOCKER_MODEL_RUNNER_FINAL.md` | Keep Root; Archive `SEAM/` copy |
| **Figma Final Integration** | `38b2be95fc23...` | 10,595 B | `SEAM_FIGMA_FINAL_INTEGRATION.md` | `SEAM/SEAM_FIGMA_FINAL_INTEGRATION.md` | Keep Root; Archive `SEAM/` copy |
| **Final Engineering Audit** | `d604b1a1b715...` | 12,103 B | `SEAM_FINAL_ENGINEERING_AUDIT.md` | `SEAM/SEAM_FINAL_ENGINEERING_AUDIT.md` | Keep Root; Archive `SEAM/` copy |

### Group D1-B: Submission Evidence Duplicates (Root vs. `evidence/final-submission/`)
During Phase 6, authoritative reports were intentionally copied into `evidence/final-submission/` to form a self-contained, immutable academic submission package:

| Document Role | SHA-256 Hash | Size | Canonical Source (Root) | Immutable Evidence Copy | Disposition |
| :--- | :---: | :---: | :--- | :--- | :--- |
| **Agent Panel Validation** | `82ee068b4178...` | 2,897 B | `AGENT_PANEL_LIVE_VALIDATION.md` | `evidence/final-submission/agents/agent_panel_live_validation.md` | **KEEP BOTH (Legitimate)** |
| **Diagram Validation** | `776a584e87d1...` | 10,037 B | `DIAGRAM_ENGINE_PHASE1_VALIDATION.md` | `evidence/final-submission/diagrams/diagram_engine_phase1_validation.md` | **KEEP BOTH (Legitimate)** |
| **GitHub Enhancement** | `c6b5cfd7ee97...` | 19,108 B | `GITHUB_EXISTING_PROJECT_ENHANCEMENT_PHASE3.md` | `evidence/final-submission/github-enhancement/github_enhancement_phase3.md` | **KEEP BOTH (Legitimate)** |
| **Model Alignment** | `3b16b1b300f0...` | 12,413 B | `LOCAL_MODEL_ALIGNMENT_VALIDATION.md` | `evidence/final-submission/models/local_model_alignment_validation.md` | **KEEP BOTH (Legitimate)** |
| **SDXL Validation** | `767891f8f078...` | 16,103 B | `SEAM_DOCKER_SDXL_IMAGE_GENERATION_VALIDATION.md` | `evidence/final-submission/limitations/docker_sdxl_validation_limitation.md`| **KEEP BOTH (Legitimate)** |

*Disposition Rationale:* The copies in `evidence/final-submission/` are explicitly indexed by `SEAM_SUBMISSION_EVIDENCE_INDEX.md` and `SEAM_FINAL_EVIDENCE_INDEX.md` as frozen submission evidence. Removing them would break academic traceability links.

---

## 3. Category D2 & D3 — Near Duplicates & Outdated Versions

These files represent drafts, superseded versions, or partial subsets of later authoritative documents:

### Group D2/D3-1: Firebase Security Rules
- **Candidate 1:** `firestore.rules` (Root — 61 lines, 1,855 B, Hash: `E05C2ECB...`)
- **Candidate 2:** `seam-ide/firestore.rules` (Frontend — 43 lines, 1,385 B, Hash: `E6E4A4ED...`)
- **Differences:** Root `firestore.rules` contains complete system rules including `/system_config/` and `/public_templates/` collections. `seam-ide/firestore.rules` is a truncated subset.
- **Classification:** **D3 (Outdated Version in `seam-ide/`)**.
- **Recommended Action:** Retain Root `firestore.rules` as canonical; update `seam-ide/firestore.rules` to match root or symlink.

### Group D2/D3-2: Diagram Engine Validation Reports
- **Candidate 1:** `DIAGRAM_ENGINE_PHASE1_VALIDATION.md` (Root — 250 lines, 10,037 B, Hash: `776A584E...`)
- **Candidate 2:** `SEAM/DIAGRAM_ENGINE_VALIDATION.md` (SEAM — 31 lines, 1,225 B, Hash: `25D64752...`)
- **Differences:** `SEAM/DIAGRAM_ENGINE_VALIDATION.md` is an early 31-line initial draft that references outdated model `ai/qwen3:4b-instruct-2507-q4_K_M`. The root report is the comprehensive Phase 1 validation report covering all 10 diagrams.
- **Classification:** **D3 (Outdated Version in `SEAM/`)**.
- **Recommended Action:** Root `DIAGRAM_ENGINE_PHASE1_VALIDATION.md` is canonical; archive `SEAM/DIAGRAM_ENGINE_VALIDATION.md`.

### Group D2/D3-3: GitHub Existing Project Validation Reports
- **Candidate 1:** `GITHUB_EXISTING_PROJECT_ENHANCEMENT_PHASE3.md` (Root — 450+ lines, 19,108 B)
- **Candidate 2:** `SEAM/EXISTING_PROJECT_ENHANCEMENT_VALIDATION.md` (SEAM — 17 lines, 840 B)
- **Candidate 3:** `SEAM/GITHUB_INTELLIGENCE_VALIDATION.md` (SEAM — 35 lines, 1,410 B)
- **Differences:** Candidates 2 and 3 are early test stubs from initial prototyping. Candidate 1 is the comprehensive Phase 3 report detailing Workflow B, safe sandboxing, and unified diff verification.
- **Classification:** **D3 (Outdated Versions in `SEAM/`)**.
- **Recommended Action:** Root file is canonical; archive the two early stubs in `SEAM/`.

---

## 4. Category D4 — Functional Redundancy in `generated_projects/`

### The Dual-Directory Working Directory Anomaly
During test executions, the relative directory string `"generated_projects"` was created relative to the process working directory:
- Running from Workspace Root created projects in `C:\Users\Windows 11\Downloads\SEAM1\generated_projects\`.
- Running from Backend Directory created projects in `C:\Users\Windows 11\Downloads\SEAM1\SEAM\generated_projects\`.

### Redundancy Finding:
Over **1,200 files** in `generated_projects/` and `SEAM/generated_projects/` represent ephemeral outputs from synthetic test runs (e.g., `project_exp_*`, `phase1_runtime_verification_temp`, `test_wf_a_proj`, `test_wf_b_proj`).
- **Classification:** **D4 (Functional Redundancy / Test Outputs)**.
- **Recommended Action:** Retain authoritative reference projects used in demonstrations (such as `InventoryManagement` and `WorkflowB-TestRepo`); archive or clean transient test scratch runs only after user authorization.

---

## 5. Category D5 — Legitimate Same-Name Files

These files share identical basenames but serve strictly independent, legitimate roles in separate architectural modules:

1. `package.json` (`seam-ide/package.json` vs. generated node projects): Frontend IDE dependency manifest vs. user-generated projects.
2. `pyproject.toml` / `requirements.txt` (`SEAM/requirements.txt` vs. generated python projects): Backend service dependencies vs. generated project dependencies.
3. `main.py` (`SEAM/backend/main.py` vs. generated projects): FastAPI core backend application vs. generated microservices.
4. `config.py` (`SEAM/backend/config.py` vs. test fixtures): Core framework configuration vs. isolated test stubs.
