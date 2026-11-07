# SEAM CONTROLLED EVALUATION PROTOCOL
**Standard Operating Procedures, Experimental Design, and Benchmark Testbed**

**Document Version:** 1.0.0-protocol  
**Date:** October 15, 2026  
**Scope:** Reproducible Experimental Protocol for Autonomous Multi-Agent Software Engineering  
**Target Environments:** Local CPU / Local GPU Workstation Environments  

---

## 1. Experimental Design & Treatment Groups

To isolate the causal contributions of cognitive role decomposition, planning, domain RAG, and autonomous self-healing, the SEAM Evaluation Protocol establishes a four-arm controlled experiment design:

```
                                  [Task Request]
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        ▼                                ▼                                ▼
  [Arm 1: SEAM_FULL]          [Arm 2: Ablation Series]        [Arm 3: Single-Agent Baseline]
  • 6 Cognitive Agents        • ABLATION_NO_RAG               • Monolithic System Prompt
  • 4-Tier Permission Gate    • ABLATION_NO_REPAIR            • Direct Code Modification
  • ChromaDB Domain RAG       • ABLATION_NO_CONTRACTS         • Single Tool Invocation
  • Tripartite Contracts      • ABLATION_NO_PLANNING          • Zero Supervisor Handoffs
  • Autonomous QA Repair
```

### Treatment Arm 1: Full SEAM Framework (`SEAM_FULL`)
The authoritative six-agent architecture with all 58 engineering capabilities active:
- Supervisor state automaton enforcing sequential planning, coding, QA, and delivery.
- Domain-Aware RAG active via ChromaDB vector retrieval.
- Four-tier Permission Engine enforcing workspace confinement.
- Autonomous Self-Healing Repair loop active upon test failure (bounded to $\le 3$ iterations).

### Treatment Arm 2: Systematic Ablation Variants
1. **`ABLATION_NO_DOMAIN_RAG`:** Disables vector database retrieval. Agents operate purely on general pre-trained weights and user prompt instructions.
2. **`ABLATION_NO_AUTONOMOUS_REPAIR`:** Disables defect rework routing. QA failures terminate execution immediately without patch synthesis.
3. **`ABLATION_NO_CONTRACT_INTELLIGENCE`:** Disables cross-layer schema validation between frontend interfaces, OpenAPI routes, and database models.
4. **`ABLATION_NO_SUPERVISOR_PLANNING`:** Bypasses the Analysis and Planning agents; the user prompt is routed directly to the Coding Agent.

### Treatment Arm 3: Single-Agent Monolithic Baseline (`BASELINE_SINGLE_AGENT`)
A single LLM agent operating in an unconstrained loop (analogous to standard ReAct or AutoGPT):
- A single system prompt tasked simultaneously with understanding, coding, and testing.
- Direct access to filesystem tools without permission tier classification.
- No intermediate Pydantic schemas or specialized cognitive roles.

---

## 2. Experimental Controls & Environment Invariants

To guarantee scientific validity, the following variables are strictly held invariant across all arms:

1. **Underlying Foundation Model:** `qwen2.5-coder:1.5b` (Q4_K_M quantization via Ollama v0.5.x on `http://127.0.0.1:11434`), maintaining identical temperature ($T = 0.2$), top-p ($0.9$), and seed configuration.
2. **Compute Environment:** Single host machine (Windows 11, Intel Core i5-1035G1 CPU @ 1.00GHz, 16GB RAM, integrated Intel UHD Graphics).
3. **Task Specifications:** Word-for-word identical requirement descriptions provided to each arm.
4. **Tool Availability:** Equivalent underlying filesystem and test runner tools provided across all arms.
5. **Evaluation Test Suite:** Fixed, pre-written hidden acceptance tests executed in clean virtual environments.

---

## 3. Operational Protocols by Operating Mode

### 3.1 Mode A Protocol: Existing Repository Enhancement (Workflow B)

#### Step 1: Benchmark Repository Selection & Pinning
Select real-world open-source repositories representing diverse languages and frameworks, pinned to specific commit hashes:
- **Repo A1 (FastAPI Backend):** Python REST API with pre-existing pytest suite (pinned commit `a1b2c3d`).
- **Repo A2 (React Frontend):** TypeScript/Vite UI with pre-existing Vitest component tests (pinned commit `e4f5g6h`).
- **Repo A3 (Full-Stack Polyglot):** Python + React multi-tier application with SQLite persistence (pinned commit `i7j8k9l`).

#### Step 2: Baseline State Verification
Before dispatching agent tasks:
1. Clone the repository into an isolated sandbox: `workspaces/repos/test_run_{run_id}/`.
2. Execute the pre-existing test suite: record the baseline test pass count ($T_{\text{pass\_pre}}$).
3. Verify that the baseline build succeeds in under 30 seconds.

#### Step 3: Task Formulation (Bug Fix / Feature Addition)
Formulate task requests with explicit acceptance criteria and hidden validation tests:
- *Bug Fix Task:* Provide an issue description detailing a reproducible edge-case failure.
- *Feature Task:* Request an additive API endpoint or UI component with defined input/output contracts.

#### Step 4: Execution & Gating Audit
1. Trigger Workflow B via `/api/projects` (`workflow_type="enhance_existing"`).
2. Measure time taken for AST analysis and 14-section project understanding generation.
3. Verify that execution pauses at `APPROVAL_GATE`. Record approval response.
4. Apply the approved patch in the sandbox. Capture the unified diff (`git diff -u`).
5. Execute QA test runner. If tests fail, monitor the autonomous repair loop.

#### Step 5: Post-Enhancement Measurement
1. Execute the hidden acceptance test suite: record $Fail \to Pass$ rate.
2. Re-execute the pre-existing baseline test suite: calculate $Pass \to Pass$ preservation rate.
3. Compute patch churn: lines added, lines deleted, and unrelated files modified.
4. Run security scanner to verify that zero path traversal attempts or secret leaks occurred.

---

### 3.2 Mode B Protocol: Greenfield Project Generation (Workflow A)

#### Step 1: Specification Ingestion & Hidden Testbed Preparation
Define human-reviewed requirement specifications paired with **hidden behavioral tests** that validate externally observable outputs (HTTP status codes, JSON payload schemas, database mutations) rather than internal code structure.

#### Step 2: Clean Environment Scaffolding
Initialize an empty directory in `generated_projects/{project_name}_{run_id}/`. Ensure zero pre-existing code, caches, or virtual environments exist.

#### Step 3: Autonomous Synthesis Execution
1. Dispatch the specification to the Supervisor Agent via `create_project()`.
2. Record real-time token streaming and state progression via WebSocket events:
   `IDLE → ANALYZING → PLANNING → EXECUTING → TESTING → REPAIRING → PACKAGING → COMPLETED`.
3. Capture the generated canonical diagrams in `design/diagram_source/` and verify Pydantic validity.

#### Step 4: Clean-Environment Build & Behavioral Verification
1. Spin up a clean subshell / virtual environment.
2. Execute dependency installation (`pip install -r requirements.txt` or `npm install`). Record build success ($BIS$).
3. Launch the generated service process on an ephemeral port.
4. Execute the hidden behavioral test harness against the live service endpoints.
5. Launch Playwright headless browser to execute end-to-end user journeys against frontend routes.
6. Verify release packaging: inspect generated `.zip` archive, Dockerfile, and SHA-256 manifest.

---

## 4. Stratification & Non-Determinism Control

### 4.1 Task Complexity Stratification
Tasks are stratified into three distinct complexity tiers:
- **Low Complexity (Tier 1):** Single-file modifications, CRUD endpoint addition, unit test generation (<100 lines changed).
- **Medium Complexity (Tier 2):** Multi-file feature addition, database schema migration, authentication middleware (100–300 lines changed across 2–4 modules).
- **High Complexity (Tier 3):** Full-stack architectural enhancement, cross-layer contract synchronization, asynchronous event queues (>300 lines changed across $\ge 5$ modules).

### 4.2 Statistical Rigor & Repetition Protocol
To account for LLM non-determinism:
- Every scenario and ablation condition must be repeated across **$N \ge 3$ independent runs** with pinned seeds.
- Report sample size ($N$), arithmetic mean, median, standard deviation ($\sigma$), and 95% bootstrap confidence intervals where applicable.
- In accordance with research integrity, all individual run outcomes must be cataloged in machine-readable JSON/CSV with unique run UUIDs.

---

## 5. Blinded Human Review Guidelines

For quality dimensions that cannot be reliably evaluated by automated test assertions (such as architectural elegance, code readability, and documentation clarity):
1. **Blinded Code Review:** Two independent software engineering reviewers evaluate anonymized patches/projects with all system identification tags stripped.
2. **Standardized Rubric (1–5 Likert Scale):**
   - *Architectural Fit:* Does the code respect existing design patterns? (1 = Severe divergence, 5 = Flawless alignment).
   - *Readability & Style:* Does the code follow standard language idioms? (1 = Obfuscated/redundant, 5 = Clean/idiomatic).
   - *Scope Discipline:* Are changes restricted strictly to necessary files? (1 = Extensive unrelated churn, 5 = Highly surgical patch).
3. **Inter-Rater Reliability:** Calculate Cohen's Kappa ($\kappa$) across reviewer ratings. Discrepancies $>1$ point trigger a joint adjudication session.

---

## 6. Step-by-Step Evaluator Execution Checklist

```powershell
# ==============================================================================
# SEAM CONTROLLED EVALUATION RUNNER (POWERSHELL PROTOCOL)
# ==============================================================================

# 1. Prepare Environment & Reset PATH
$env:PATH = "C:\Users\Windows 11\AppData\Local\Python\pythoncore-3.14-64;C:\Users\Windows 11\AppData\Local\Python\pythoncore-3.14-64\Scripts;" + $env:PATH
$env:PYTHONPATH = "C:\Users\Windows 11\Downloads\SEAM1\SEAM"

# 2. Verify Ollama Health & Active Model
curl http://127.0.0.1:11434/api/tags
# Assert: qwen2.5-coder:1.5b is present

# 3. Execute Mode A (Repository Enhancement Benchmark)
cd "C:\Users\Windows 11\Downloads\SEAM1\SEAM"
python -m pytest tests/test_phase3_github_enhancement.py -v --tb=short

# 4. Execute Mode B (Greenfield Full-Cycle Scenarios)
python -m pytest tests/test_e2e_validation.py -v --tb=short

# 5. Execute Empirical Ablation Harness
python -m pytest tests/test_ablation_wiring.py -v --tb=short

# 6. Capture Telemetry & Update Dataset
# Results automatically stream to FINAL_RESEARCH_RESULTS.json
```
