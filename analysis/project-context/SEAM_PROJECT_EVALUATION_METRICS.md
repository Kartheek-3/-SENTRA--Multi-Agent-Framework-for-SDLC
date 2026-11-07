# SEAM PROJECT EVALUATION METRICS FRAMEWORK
**Comprehensive Metric Definitions, Formulations, and Measurement Standards**

**Document Version:** 1.0.0-metrics  
**Date:** October 15, 2026  
**Scope:** Dual-Track Evaluation Framework for Autonomous Multi-Agent Software Engineering  
**Operating Modes:**
- **Mode A:** Existing Repository Enhancement (Workflow B — Brownfield)
- **Mode B:** Greenfield Project Generation (Workflow A — Greenfield)

---

## 1. Executive Summary & Measurement Philosophy

Software engineering evaluations of Large Language Model (LLM) agents have historically over-relied on narrow unit-test patch pass rates (e.g., standard SWE-bench benchmarks) or subjective LLM-as-a-judge scores. Such evaluations fail to assess end-to-end software quality, regression risks, repository architectural preservation, and security sandboxing.

The SEAM Evaluation Metrics Framework establishes a rigorous, multi-dimensional, and evidence-based measurement methodology. In accordance with software engineering research standards:
1. **Separation of Modes:** Mode A (Existing Repository Enhancement) and Mode B (Greenfield Project Generation) maintain dedicated scorecards because their initial states, task objectives, and failure modes are fundamentally distinct.
2. **Rejection of Monolithic Quality Scores:** No opaque composite score is claimed as established. All metrics are reported with explicit mathematical formulations, numerators, denominators, and measurement boundaries.
3. **Traceability to Code:** Metrics are explicitly classified into those currently instrumented in SEAM telemetry versus those requiring extended instrumentation.

---

## 2. Mode A — Existing Repository Enhancement (Workflow B)

In Mode A, an agent is supplied with an existing, pinned Git repository and a concrete task request (bug fix, feature implementation, refactoring, or test addition). All modifications must execute through the isolated sandbox, respect the permission gate, and preserve existing system behavior.

### Metric A1: Task Resolution Rate (TRR)
- **Definition:** Percentage of attempted repository enhancement tasks that completely fulfill acceptance criteria with zero regressions.
- **Mathematical Formulation:**
  $$\text{Resolution Rate (TRR)} = \left( \frac{\text{Tasks fully resolved without regression}}{\text{Total tasks attempted}} \right) \times 100$$
- **Measurement Procedure:** A task is coded as 1 if and only if:
  1. All task-specific acceptance tests pass ($Fail\to Pass = 100\%$).
  2. Pre-existing test suite passes completely ($Pass\to Pass = 100\%$).
  3. No unapproved manual interventions occurred.
  Otherwise, coded as 0.
- **SEAM Capability Status:** **INSTRUMENTED TODAY** (tracked via `ProjectState.latest_qa_status` and `test_phase3_github_enhancement.py`).

### Metric A2: Weighted Requirement Satisfaction (WRS)
- **Definition:** The proportion of weighted functional and non-functional requirements verified after enhancement.
- **Mathematical Formulation:**
  $$\text{Weighted Coverage (WRS)} = \left( \frac{\sum_{i=1}^n w_i \cdot s_i}{\sum_{i=1}^n w_i} \right) \times 100$$
  where $w_i \in [1, 5]$ is the documented importance weight of requirement $i$, and $s_i \in \{0.0, 0.5, 1.0\}$ represents satisfaction verified by behavioral tests.
- **Measurement Procedure:** Mapped directly from the 14-section project plan and acceptance checklist.
- **SEAM Capability Status:** **INSTRUMENTED TODAY** (tracked in `EvaluationEngine` and `FINAL_RESEARCH_RESULTS.json`).

### Metric A3: Fail-to-Pass Rate ($F \to P$)
- **Definition:** The proportion of previously failing (or newly introduced target) tests that pass following agent modification.
- **Mathematical Formulation:**
  $$\text{Fail-to-Pass Rate} = \left( \frac{|T_{\text{target}} \cap T_{\text{pass\_post}}|}{|T_{\text{target}}|} \right) \times 100$$
  where $T_{\text{target}}$ is the set of tests asserting the new feature or bug fix.
- **SEAM Capability Status:** **INSTRUMENTED TODAY** (measured in `QA Agent` test triage).

### Metric A4: Pass-to-Pass Preservation Rate ($P \to P$)
- **Definition:** The proportion of baseline passing tests that remain passing without regression.
- **Mathematical Formulation:**
  $$\text{Pass-to-Pass Preservation Rate} = \left( \frac{|T_{\text{pass\_pre}} \cap T_{\text{pass\_post}}|}{|T_{\text{pass\_pre}}|} \right) \times 100$$
  where $T_{\text{pass\_pre}}$ is the suite of passing tests before agent enhancement.
- **Measurement Procedure:** Pre-existing test results are snapshotted in `SafeWorkspaceService` before changes are applied; post-patch test runs compare failures against this baseline.
- **SEAM Capability Status:** **INSTRUMENTED TODAY** (verified in `test_phase3_github_enhancement.py`).

### Metric A5: Repository Understanding Quality (RUQ)
- **Definition:** Precision, Recall, and F1 score of the Analysis Agent in identifying relevant modules, target files, and architectural patterns.
- **Mathematical Formulation:**
  $$\text{Precision} = \frac{|F_{\text{predicted}} \cap F_{\text{ground\_truth}}|}{|F_{\text{predicted}}|}, \quad \text{Recall} = \frac{|F_{\text{predicted}} \cap F_{\text{ground\_truth}}|}{|F_{\text{ground\_truth}}|}, \quad \text{F1} = \frac{2 \cdot P \cdot R}{P + R}$$
  where $F_{\text{predicted}}$ are candidate files identified in the 14-section report, and $F_{\text{ground\_truth}}$ are the files actually modified in a gold-standard patch.
- **SEAM Capability Status:** **REQUIRES EXTENDED INSTRUMENTATION** (requires comparing `DetailedRepositoryProfile.source_references` against benchmark gold-standard file sets).

### Metric A6: Planning Quality & Traceability (PQT)
- **Definition:** Percentage of planned steps directly mapped to stated requirements, measuring plan conciseness and architectural adherence.
- **Mathematical Formulation:**
  $$\text{Plan Traceability} = \left( \frac{|S_{\text{mapped}}|}{|S_{\text{total}}|} \right) \times 100, \quad \text{Over-planning Ratio} = \frac{|S_{\text{unnecessary}}|}{|S_{\text{required}}|}$$
- **SEAM Capability Status:** **INSTRUMENTED TODAY** (tracked via `EnhancementPlan.items` in `enhancement_planner.py`).

### Metric A7: Patch Relevance & Churn Scope Control (PRSC)
- **Definition:** Ratio of relevant, task-related modified lines to total lines changed, penalizing cosmetic reformatting and unrelated churn.
- **Mathematical Formulation:**
  $$\text{Patch Precision} = \left( \frac{L_{\text{relevant\_changed}}}{L_{\text{total\_changed}}} \right) \times 100$$
  where $L_{\text{total\_changed}} = L_{\text{added}} + L_{\text{deleted}}$.
- **SEAM Capability Status:** **INSTRUMENTED TODAY** (captured via `git diff -u` in `workspace_service.py` and `ProjectState.diff_summary`).

### Metric A8: Test Suite Effectiveness
- **Definition:** Coverage and defect-detection capability of newly added tests.
- **Mathematical Formulation:**
  $$\text{New Test Coverage} = \frac{\text{Lines executed by newly added tests}}{\text{Total lines added in patch}} \times 100$$
- **SEAM Capability Status:** **REQUIRES EXTENDED INSTRUMENTATION** (requires integrating `pytest-cov` / `coverage.py` into `qa_agent.py`).

### Metric A9: Code Quality & Complexity Delta ($\Delta CC$)
- **Definition:** Change in cyclomatic complexity ($CC$) and maintainability index ($MI$) across modified files.
- **Mathematical Formulation:**
  $$\Delta CC = CC_{\text{post}} - CC_{\text{pre}}$$
- **SEAM Capability Status:** **INSTRUMENTED TODAY** (Analysis Agent AST parser computes McCabe cyclomatic complexity).

### Metric A10: Workflow Safety & Confinement Compliance (WSCC)
- **Definition:** Binary verification of security boundaries:
  1. Approval Gate Enforcement: Zero modifications if approval is rejected ($1 = \text{Pass}, 0 = \text{Fail}$).
  2. Directory Confinement: Zero reads or writes escaping project root ($1 = \text{Pass}, 0 = \text{Fail}$).
  3. Credential Redaction: Zero unmasked secrets in logs ($1 = \text{Pass}, 0 = \text{Fail}$).
- **SEAM Capability Status:** **INSTRUMENTED TODAY** (verified in `test_phase4_security_and_reliability.py`).

### Metric A11: Operational Efficiency & Autonomy
- **Definition:** Resource expenditure required to reach task completion:
  - Total Wall-Clock Execution Time (seconds)
  - Number of Agent Invocations & Tool Calls
  - Cumulative LLM Token Consumption (Prompt + Completion)
  - Repair Iteration Count (bounded to $\le 3$)
  - Human Interventions (excluding standard approval gate)
- **SEAM Capability Status:** **INSTRUMENTED TODAY** (tracked in `ProjectState.execution_history` and `FINAL_RESEARCH_RESULTS.json`).

---

## 3. Mode B — Greenfield Project Generation (Workflow A)

In Mode B, SEAM generates a complete application from scratch given an ungrounded prompt or specification document. Credit is awarded strictly on working, runnable behavior, not file quantity.

### Metric B1: Full-Project Resolution Rate / Pass@1
- **Definition:** Percentage of independent generation runs that produce a project passing 100% of mandatory behavioral acceptance tests on first execution.
- **Mathematical Formulation:**
  $$\text{Pass@1} = \left( \frac{\text{Runs where all mandatory acceptance tests pass}}{\text{Total independent generation runs}} \right) \times 100$$
- **SEAM Capability Status:** **INSTRUMENTED TODAY** (measured across benchmark scenarios in `FINAL_RESEARCH_RESULTS.json`).

### Metric B2: Full-Stack Requirement Coverage
- **Definition:** Proportion of specified functional modules, data models, and API endpoints delivered and functionally verified.
- **Mathematical Formulation:**
  $$\text{Coverage} = \left( \frac{R_{\text{verified}}}{R_{\text{specified}}} \right) \times 100$$
- **SEAM Capability Status:** **INSTRUMENTED TODAY** (e.g., Scenario 1: 71.4%, Scenario 4: 100.0% in `FINAL_RESEARCH_RESULTS.json`).

### Metric B3: Clean-Environment Build & Install Success (BIS)
- **Definition:** Binary indicator whether the generated project installs dependencies and builds in a fresh, isolated virtual environment without manual intervention.
- **Mathematical Formulation:**
  $$\text{BIS} \in \{0, 1\}$$
- **SEAM Capability Status:** **INSTRUMENTED TODAY** (validated via Delivery Agent container synthesis and `run_delivery_integration.py`).

### Metric B4: End-to-End Workflow Success (E2E-WS)
- **Definition:** Percentage of multi-tier user journeys (UI $\to$ API $\to$ Database $\to$ Response) executed without uncaught exceptions.
- **Mathematical Formulation:**
  $$\text{E2E Pass Rate} = \left( \frac{\text{Passing E2E test journeys}}{\text{Total defined E2E test journeys}} \right) \times 100$$
- **SEAM Capability Status:** **INSTRUMENTED TODAY** (measured via Playwright headless journeys in `test_playwright_ui.py`).

### Metric B5: Tripartite Contract Correctness
- **Definition:** Rate of synchronization between frontend data interfaces, OpenAPI backend schemas, and database ORM models.
- **Mathematical Formulation:**
  $$\text{Contract Divergence Rate} = \left( \frac{\text{Mismatched endpoint / model attributes}}{\text{Total defined schema attributes}} \right) \times 100$$
- **SEAM Capability Status:** **INSTRUMENTED TODAY** (measured in `EXP_CONTRACT_INTELLIGENCE`: 0 mismatches for `SEAM_FULL` vs. 1.0 for ablated).

### Metric B6: Diagram Schema Conformance Rate
- **Definition:** Percentage of generated canonical diagrams adhering 100% to Pydantic schemas and rendering collision-free in React Flow.
- **Mathematical Formulation:**
  $$\text{Diagram Conformance Rate} = \left( \frac{D_{\text{valid}}}{10} \right) \times 100$$
- **SEAM Capability Status:** **INSTRUMENTED TODAY** (100% pass across all 10 canonical diagrams in `test_diagram_generation.py`).

### Metric B7: Architecture & Separation of Concerns (SoC)
- **Definition:** Adherence to layered software design principles (e.g., controllers do not execute raw SQL queries; business logic decoupled from presentation).
- **Measurement Procedure:** Static AST linter verifying that database models are imported only in service/repository layers.
- **SEAM Capability Status:** **REQUIRES EXTENDED INSTRUMENTATION** (currently assessed via manual code audit; automated rule engine planned).

### Metric B8: Application Security Posture
- **Definition:** Static scan of generated code assessing:
  1. SQL injection vulnerabilities (use of parameterized queries vs. string concatenation).
  2. Hardcoded secrets or credentials.
  3. Input validation presence (Pydantic schema validation on route parameters).
- **SEAM Capability Status:** **INSTRUMENTED TODAY** (Delivery Agent `SecretScanner` and `test_sanitizer.py`).

### Metric B9: Setup Reproducibility & Documentation Completeness
- **Definition:** Ability of an independent developer to run the project using only the generated `README.md` and configuration files.
- **SEAM Capability Status:** **INSTRUMENTED TODAY** (verified in `run_end_to_end.py`).

### Metric B10: Autonomous Generation Efficiency
- **Definition:** Total elapsed wall-clock time, LLM tokens consumed, and self-healing repair attempts during project synthesis.
- **SEAM Capability Status:** **INSTRUMENTED TODAY** (tracked per project in SQLite event store).

---

## 4. Shared Reporting Layer & Cross-Mode Rules

While Mode A and Mode B address different software engineering archetypes, they report along a unified set of twelve qualitative and quantitative dimensions:

| Dimension | Mode A (Existing Repository Enhancement) | Mode B (Greenfield Project Generation) |
| :--- | :--- | :--- |
| **1. Functional Correctness** | Task Resolution Rate ($TRR$) & $Fail \to Pass$ | Pass@1 on hidden acceptance test suite |
| **2. Requirements Coverage** | Weighted Requirement Satisfaction ($WRS$) | Full-Stack Requirement Coverage (%) |
| **3. Regression Safety** | Pass-to-Pass Preservation Rate ($P \to P$) | N/A (No pre-existing baseline codebase) |
| **4. Integration Reliability** | Backward API contract preservation | Tripartite (UI-API-DB) contract alignment |
| **5. Test Quality** | New test coverage over modified lines | Acceptance test suite generation & execution |
| **6. Software Architecture** | Respect for existing architectural patterns | Clean separation of concerns (Layered/Hexagonal) |
| **7. Code Maintainability** | Cyclomatic complexity delta ($\Delta CC$) | Maintainability index and absence of dead code |
| **8. Security & Sandboxing** | Workspace containment & approval gate | Input validation & absence of hardcoded secrets |
| **9. Performance & Latency** | Execution time delta on existing benchmarks | Endpoint response latency under simulated load |
| **10. Reproducibility** | Clean git patch application without conflicts | Clean environment build & install success ($BIS$) |
| **11. Self-Healing Autonomy** | Repair iteration count on failing regressions | Self-healing repair rate on initial syntax/unit bugs |
| **12. Operational Cost** | Wall-clock time, token usage, tool call count | Total generation duration and token expenditure |

### Composite Scoring Rules & Disclaimer
> **Academic Integrity Notice:**  
> SEAM does not publish an arbitrary single composite score (e.g., "Quality Score = 92/100"). Single composite scores obscure critical trade-offs (e.g., high code readability concealing a failed functional test).  
> If an evaluator desires a composite index, the proposed **SEAM Balanced Quality Index (BQI)** may be evaluated as a tentative research metric:
> $$\text{BQI}_{\text{Mode A}} = 0.35(TRR) + 0.25(P \to P) + 0.15(WRS) + 0.15(WSCC) + 0.10(1 - \text{Churn})$$
> $$\text{BQI}_{\text{Mode B}} = 0.40(\text{Pass@1}) + 0.25(\text{Coverage}) + 0.15(\text{BIS}) + 0.10(\text{Contract}) + 0.10(\text{Security})$$
> Any publication of BQI must disclose the full constituent metric vector and report sensitivity bounds.

---

## 5. Instrumentation Status: Current vs. Required

| Metric Area | Specific Metric | Current Implementation Status in SEAM | Where Found in Source Code |
| :--- | :--- | :---: | :--- |
| **Mode A** | Task Resolution Rate | **INSTRUMENTED** | `SEAM/backend/agents/supervisor_agent.py` |
| **Mode A** | Pass-to-Pass Preservation | **INSTRUMENTED** | `SEAM/tests/test_phase3_github_enhancement.py` |
| **Mode A** | Fail-to-Pass Rate | **INSTRUMENTED** | `SEAM/backend/agents/qa_agent.py` |
| **Mode A** | Patch Scope & Git Churn | **INSTRUMENTED** | `SEAM/backend/github/workspace_service.py` |
| **Mode A** | Approval Gate Compliance | **INSTRUMENTED** | `SEAM/backend/api/projects.py` (`approve_enhancement`) |
| **Mode A** | Relevant File Localization (F1) | **NEEDS EXTENSION** | Requires ground-truth file tagging in benchmark |
| **Mode A** | Mutation Testing Score | **NEEDS EXTENSION** | Requires `mutmut` integration in test runner |
| **Mode B** | Pass@1 Acceptance Rate | **INSTRUMENTED** | `SEAM/backend/evaluation/` & `FINAL_RESEARCH_RESULTS.json`|
| **Mode B** | Requirement Coverage | **INSTRUMENTED** | `SEAM/backend/evaluation/evaluator.py` |
| **Mode B** | Clean Build & Install (BIS) | **INSTRUMENTED** | `SEAM/backend/delivery/packager.py` |
| **Mode B** | Tripartite Contract Drift | **INSTRUMENTED** | `SEAM/backend/contracts/` |
| **Mode B** | 10 Canonical Diagram Conformance| **INSTRUMENTED** | `SEAM/backend/tools/diagram_generator.py` |
| **Mode B** | Dynamic Workload Benchmarking | **NEEDS EXTENSION** | Requires `locust` / `wrk` load-generation harness |
| **Shared** | Secret & Credential Redaction | **INSTRUMENTED** | `SEAM/backend/tools/builtin.py` |
| **Shared** | Token & Latency Telemetry | **INSTRUMENTED** | `SEAM/backend/llm/model_router.py` |
