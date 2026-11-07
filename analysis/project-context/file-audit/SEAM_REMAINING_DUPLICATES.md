# SEAM Remaining Duplicates & Long-Term Consolidation Plan

## Executive Overview

This report documents the specific duplicate candidates and near-duplicate groups that were **intentionally retained** during the cleanup phase. Every retention decision was guided by safety constraints: preserving experimental reproducibility, protecting untracked files from irreversible deletion, preventing disruptions to active experiment scripts, and safeguarding academic submission records.

---

## 1. Intentionally Retained Duplicate Groups

### Group 1: Dual `FINAL_RESEARCH_RESULTS.json`
- **Locations**:
  - `FINAL_RESEARCH_RESULTS.json` (Workspace Root, 61,549 bytes)
  - `SEAM/FINAL_RESEARCH_RESULTS.json` (Backend Root, 61,549 bytes)
- **Hash**: `E0CCA6BCAB35075C0A18567FA605261A3A22D44FD5091663A79CCF1C25DA39FA` (Exact Match)
- **Reason for Retention**: Active code dependency in `SEAM/run_experiments.py` (lines 338–346). When the research benchmark harness executes, it explicitly writes to both paths:
  ```python
  root_json_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "FINAL_RESEARCH_RESULTS.json"))
  seam_json_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "FINAL_RESEARCH_RESULTS.json"))
  ```
  Deleting the `SEAM/` copy would immediately cause recreation on subsequent harness runs or break scripts executing strictly from within `SEAM/`.
- **Proposed Code Consolidation**: Update `run_experiments.py` to write exclusively to the monorepo root via an environment variable (`SEAM_RESULTS_DIR`), or resolve `FINAL_RESEARCH_RESULTS.json` relative to the repository root.

---

### Group 2: Submission Evidence Freeze (`evidence/final-submission/`)
- **Locations**:
  - `evidence/final-submission/architecture/backend_architecture_audit.md`
  - `evidence/final-submission/testing/final_test_evidence.md`
  - `evidence/final-submission/experiments/final_experimental_evaluation.md`
  - `evidence/final-submission/experiments/final_research_results.json`
- **Reason for Retention**: Immutable audit snapshot. `evidence/final-submission/` was established in Phase 6 as a frozen evidence archive explicitly indexed by `submission/SEAM_SUBMISSION_EVIDENCE_INDEX.md`. Even though their contents mirror root technical reports, these files provide archival provenance for examiners and peer reviewers.
- **Action**: Retain permanently as an immutable evidence record.

---

### Group 3: Obsolete Technical Stubs (Marked `REVIEW_REQUIRED`)
- **Files**:
  - `SEAM/DIAGRAM_ENGINE_VALIDATION.md` (31 lines, 1,225 bytes)
  - `SEAM/EXISTING_PROJECT_ENHANCEMENT_VALIDATION.md` (17 lines, 840 bytes)
  - `SEAM/GITHUB_INTELLIGENCE_VALIDATION.md` (18 lines, 830 bytes)
- **Superseding Reports**:
  - `DIAGRAM_ENGINE_PHASE1_VALIDATION.md` (Root, 10,037 bytes)
  - `GITHUB_EXISTING_PROJECT_ENHANCEMENT_PHASE3.md` (Root, 19,108 bytes)
- **Reason for Retention**: These files are untracked (`??`) in the current Git working tree. Deleting untracked files using automated tools is permanent and cannot be undone via `git checkout`. To honor the Master Prompt's cardinal rule (*"Never delete or overwrite a file that is untracked user work... exclude from automatic cleanup and report for manual review"*), they are preserved pending explicit user sign-off.
- **Recommended User Action**: Once reviewed, the user can safely remove these 3 files manually or move them to an archive directory.

---

### Group 4: Dual Firestore Rules (`firestore.rules` vs `seam-ide/firestore.rules`)
- **Locations**:
  - `firestore.rules` (Root, 61 lines, 1,855 bytes)
  - `seam-ide/firestore.rules` (Frontend, 43 lines, 1,385 bytes)
- **Content Comparison**:
  - Functionally identical rules governing user profiles, permissions, and project subcollections.
  - The root file contains multiline formatting and inline comments, while the `seam-ide` file contains concise single-line match statements.
  - No `firebase.json` deployment manifest currently exists in the repository to define the authoritative deployment path.
- **Reason for Retention**: Prevent unverified deployment assumptions. Both files are safe and aligned with user ownership security invariants.
- **Proposed Future Action**: Add a root `firebase.json` designating `firestore.rules` as canonical, and remove `seam-ide/firestore.rules`.

---

### Group 5: Dual `generated_projects/` Directories
- **Locations**:
  - `generated_projects/` (Root)
  - `SEAM/generated_projects/` (Backend root)
- **Reason for Retention**:
  - Multiple backend services (`coding_agent.py`, `filesystem.py`, `artifact_pipeline.py`, `diagram_generator.py`) resolve output directories using relative paths like `Path("generated_projects")`.
  - When commands run from `SEAM1/`, artifacts are generated in `SEAM1/generated_projects/`. When run from `SEAM1/SEAM/`, artifacts are generated in `SEAM1/SEAM/generated_projects/`.
  - Deleting either folder during a file-level cleanup without code changes risks breaking active test fixtures or project loaders.
- **Proposed Future Code-Level Consolidation**:
  1. Add a centralized configuration variable in `SEAM/backend/config.py`:
     ```python
     GENERATED_PROJECTS_DIR = os.getenv("SEAM_PROJECTS_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "generated_projects")))
     ```
  2. Refactor all backend modules to consume `GENERATED_PROJECTS_DIR` rather than `Path("generated_projects")`.
  3. Merge test outputs into the root `generated_projects/` folder.
