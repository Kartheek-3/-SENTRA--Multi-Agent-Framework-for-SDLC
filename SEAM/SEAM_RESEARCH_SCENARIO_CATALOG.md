# SEAM Research Scenario Catalog

## Purpose

The research scenario catalog provides fixed, reusable, data-driven scenarios for controlled SEAM experiments.

Catalog definitions do not encode expected success or failure outcomes. Results must come from actual experiment runs and EvaluationEngine outputs.

## Scenario Model

Each scenario records:

- `scenario_id`
- `name`
- `description`
- `domain`
- `complexity`
- `complexity_rationale`
- `requirements`
- `required_features`
- `expected_artifacts`
- `expected_validation_layers`
- `evaluation_metrics`
- `seed`
- `version`

## Complexity Categories

`SMALL`: bounded workflows with limited entity and integration surface.

`MEDIUM`: multiple interacting entities, API/frontend/database coordination, or integration-heavy workflows.

`LARGE`: domain constraints, security/audit concerns, multi-role workflows, or broader validation surfaces.

No subjective difficulty score is used.

## Initial Scenarios

`SCENARIO_01`: CRUD Application

- Domain: productivity
- Complexity: SMALL
- Covers identity, CRUD, REST API, persistence, frontend, validation, and tests.

`SCENARIO_02`: Authentication Application

- Domain: identity
- Complexity: SMALL
- Covers registration, login, logout, protected route, auth API, persistent state, and invalid credentials.

`SCENARIO_03`: E-commerce Application

- Domain: commerce
- Complexity: MEDIUM
- Covers products, search, cart, checkout, inventory, orders, API, database, and frontend.

`SCENARIO_04`: Travel Application

- Domain: travel
- Complexity: MEDIUM
- Covers destination search, itinerary planning, transport information, filters, saved trips, frontend, backend API, and database.

`SCENARIO_05`: Domain-Aware Healthcare Application

- Domain: healthcare
- Complexity: LARGE
- Covers appointments, patient/provider workflow, authentication, domain constraints, audit/security, frontend, backend, and database.

## Controlled Configurations

`SEAM_FULL`

- domain RAG
- GitHub intelligence
- contract intelligence
- runtime validation
- E2E
- autonomous repair

`ABLATION_NO_DOMAIN_RAG`

- disables domain-aware RAG metadata for controlled ablation runs

`ABLATION_NO_AUTONOMOUS_REPAIR`

- disables autonomous repair metadata while keeping QA/defect detection active

`ABLATION_NO_CONTRACT_INTELLIGENCE`

- disables full-stack contract intelligence metadata

`BASELINE`

- metadata only unless an actual baseline implementation or recorded baseline result exists

## Ready-To-Run Experiment Definitions

`EXP_DOMAIN_RAG`

- Scenario: `SCENARIO_05`
- Configurations: `SEAM_FULL`, `ABLATION_NO_DOMAIN_RAG`
- Hypothesis: domain-aware retrieval changes domain-specific execution metrics.

`EXP_AUTONOMOUS_REPAIR`

- Scenario: `SCENARIO_02`
- Configurations: `SEAM_FULL`, `ABLATION_NO_AUTONOMOUS_REPAIR`
- Hypothesis: autonomous repair changes defect resolution metrics.

`EXP_CONTRACT_INTELLIGENCE`

- Scenario: `SCENARIO_03`
- Configurations: `SEAM_FULL`, `ABLATION_NO_CONTRACT_INTELLIGENCE`
- Hypothesis: contract intelligence changes contract compliance metrics.

## Experiment Matrix

Each experiment is represented as:

Experiment -> Scenario -> Configuration -> Repeated RunResult

Each run must have a unique experiment id, run id, and project id.

## Reproducibility

Each run records:

- timestamp
- git commit when available
- model name/configuration
- seed
- knowledge version
- repository context version
- Python/Node/environment metadata

Secrets, tokens, cookies, `.env` values, passwords, and hidden reasoning are excluded.

## Limitations

- Catalog definitions are not evidence.
- Hypotheses are not marked as proven automatically.
- No baseline or ablation result is fabricated.
- Causality is not inferred from a single run.
