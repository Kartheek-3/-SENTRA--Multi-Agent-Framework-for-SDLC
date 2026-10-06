from datetime import datetime, timezone
from typing import Dict, List

from backend.models.evaluation import ExperimentDefinition, RunConfiguration, ScenarioDefinition


CATALOG_VERSION = "1"


def controlled_configurations() -> List[RunConfiguration]:
    return [
        RunConfiguration(
            configuration_id="SEAM_FULL",
            name="Full SEAM configuration",
            mode="SEAM_FULL",
            flags={
                "domain_rag": True,
                "github_intelligence": True,
                "contract_intelligence": True,
                "runtime_validation": True,
                "e2e": True,
                "autonomous_repair": True,
            },
        ),
        RunConfiguration(
            configuration_id="ABLATION_NO_DOMAIN_RAG",
            name="Ablation without domain-aware RAG",
            mode="ABLATION",
            disabled_capabilities=["domain-aware RAG"],
            flags={"domain_rag": False},
        ),
        RunConfiguration(
            configuration_id="ABLATION_NO_AUTONOMOUS_REPAIR",
            name="Ablation without autonomous repair",
            mode="ABLATION",
            disabled_capabilities=["autonomous repair"],
            flags={"autonomous_repair": False},
        ),
        RunConfiguration(
            configuration_id="ABLATION_NO_CONTRACT_INTELLIGENCE",
            name="Ablation without full-stack contract intelligence",
            mode="ABLATION",
            disabled_capabilities=["full-stack contract intelligence"],
            flags={"contract_intelligence": False},
        ),
        RunConfiguration(
            configuration_id="BASELINE",
            name="Baseline metadata placeholder",
            mode="BASELINE",
            baseline_provenance="Requires an actual baseline implementation or recorded baseline result before use.",
        ),
    ]


def scenario_catalog() -> Dict[str, ScenarioDefinition]:
    scenarios = [
        ScenarioDefinition(
            scenario_id="SCENARIO_01",
            name="CRUD Application",
            description="Expense/task management system with identity, CRUD workflows, persistence, UI, validation, and tests.",
            domain="productivity",
            complexity="SMALL",
            complexity_rationale="Single bounded domain with straightforward CRUD operations and common validation paths.",
            requirements=(
                "Build an expense/task management application with user identity, create/read/update/delete operations, "
                "REST APIs, database persistence, frontend UI, validation, API tests, unit tests, and README."
            ),
            required_features=["user identity", "CRUD", "REST API", "database persistence", "frontend UI", "validation", "testing"],
            expected_artifacts=["README.md", "backend source", "frontend source", "tests"],
            expected_validation_layers=["QA", "API", "frontend", "backend"],
            expected_capabilities=["frontend planning", "contract intelligence", "QA"],
            evaluation_metrics=["requirement_coverage", "contract_compliance_rate", "e2e_pass_rate", "tool_invocation_count"],
            seed=101,
            version=CATALOG_VERSION,
        ),
        ScenarioDefinition(
            scenario_id="SCENARIO_02",
            name="Authentication Application",
            description="Authentication application with registration, login, logout, protected route, and invalid credential handling.",
            domain="identity",
            complexity="SMALL",
            complexity_rationale="Authentication has security-sensitive behavior but a narrow feature set.",
            requirements=(
                "Build an authentication application with registration, login, logout, protected route, authentication API, "
                "persistent user state, invalid credentials handling, frontend, backend, database, validation, and tests."
            ),
            required_features=["registration", "login", "logout", "protected route", "auth API", "persistent user state", "invalid credentials"],
            expected_artifacts=["auth API", "frontend auth views", "database model", "tests", "README.md"],
            expected_validation_layers=["QA", "security", "API", "E2E"],
            expected_capabilities=["security validation", "E2E", "autonomous repair"],
            evaluation_metrics=["defect_count", "repair_resolution_rate", "targeted_verification_pass_rate", "regression_pass_rate", "qa_status"],
            seed=202,
            version=CATALOG_VERSION,
        ),
        ScenarioDefinition(
            scenario_id="SCENARIO_03",
            name="E-commerce Application",
            description="Product catalog, search, cart, checkout, inventory, order creation, API, database, and frontend.",
            domain="commerce",
            complexity="MEDIUM",
            complexity_rationale="Multiple interacting entities and workflows increase contract and integration surface.",
            requirements=(
                "Build an e-commerce application with products, search, cart, checkout, inventory, order creation, REST API, "
                "database persistence, frontend UI, validation, API tests, unit tests, and README."
            ),
            required_features=["products", "search", "cart", "checkout", "inventory", "orders", "API", "database", "frontend"],
            expected_artifacts=["API contracts", "database schema", "frontend pages", "tests", "README.md"],
            expected_validation_layers=["contracts", "runtime", "E2E", "QA"],
            expected_capabilities=["contract intelligence", "runtime validation", "E2E"],
            evaluation_metrics=["contract_compliance_rate", "e2e_pass_rate", "repair_iterations", "qa_status"],
            seed=303,
            version=CATALOG_VERSION,
        ),
        ScenarioDefinition(
            scenario_id="SCENARIO_04",
            name="Travel Application",
            description="Destination search, itinerary planning, transport information, filters, and saved trips.",
            domain="travel",
            complexity="MEDIUM",
            complexity_rationale="Search/filtering plus saved itinerary workflows require frontend/backend coordination.",
            requirements=(
                "Build a travel application with destination search, itinerary/trip planning, transport information, filtering, "
                "saved trips, frontend, backend API, database, validation, and tests."
            ),
            required_features=["destination search", "itinerary planning", "transport information", "filtering", "saved trip"],
            expected_artifacts=["frontend pages", "backend API", "database schema", "tests", "README.md"],
            expected_validation_layers=["frontend", "API", "runtime", "E2E"],
            expected_capabilities=["frontend architecture planning", "runtime validation", "E2E"],
            evaluation_metrics=["requirement_coverage", "e2e_pass_rate", "runtime_failures", "tool_invocation_count"],
            seed=404,
            version=CATALOG_VERSION,
        ),
        ScenarioDefinition(
            scenario_id="SCENARIO_05",
            name="Domain-Aware Healthcare Application",
            description="Healthcare appointment workflow with patient/provider roles, domain constraints, audit, and security.",
            domain="healthcare",
            complexity="LARGE",
            complexity_rationale="Domain constraints, audit/security concerns, authentication, and multi-role workflows create a larger validation surface.",
            requirements=(
                "Build a healthcare appointment application with patient/provider workflow, appointment scheduling, authentication, "
                "domain-specific constraints, audit/security requirements, frontend, backend API, database, validation, tests, and README."
            ),
            required_features=["appointments", "patient workflow", "provider workflow", "authentication", "audit", "security", "domain constraints"],
            expected_artifacts=["domain analysis", "API contracts", "database schema", "frontend pages", "security notes", "tests"],
            expected_validation_layers=["domain RAG", "contracts", "security", "runtime", "E2E", "QA"],
            expected_capabilities=["domain-aware intelligence", "RAG", "contract intelligence", "autonomous repair"],
            evaluation_metrics=["domain_retrieval_count", "requirement_coverage", "contract_compliance_rate", "e2e_pass_rate", "repair_resolution_rate"],
            seed=505,
            version=CATALOG_VERSION,
        ),
    ]
    return {scenario.scenario_id: scenario for scenario in scenarios}


def experiment_catalog() -> Dict[str, ExperimentDefinition]:
    scenarios = scenario_catalog()
    configs = {config.configuration_id: config for config in controlled_configurations()}
    created_at = datetime.now(timezone.utc).isoformat()
    experiments = [
        ExperimentDefinition(
            experiment_id="EXP_DOMAIN_RAG",
            name="Domain-Aware RAG Study",
            description="Compares recorded domain-aware metrics between full SEAM and no-domain-RAG configuration.",
            hypothesis="H1: Domain-aware retrieval changes domain-specific execution metrics.",
            scenarios=[scenarios["SCENARIO_05"]],
            configurations=[configs["SEAM_FULL"], configs["ABLATION_NO_DOMAIN_RAG"]],
            repetitions=3,
            metrics=["requirement_coverage", "domain_retrieval_count", "qa_defect_count", "contract_compliance_rate", "e2e_pass_rate", "repair_resolution_rate"],
            version=CATALOG_VERSION,
            created_at=created_at,
        ),
        ExperimentDefinition(
            experiment_id="EXP_AUTONOMOUS_REPAIR",
            name="Autonomous Repair Study",
            description="Compares recorded repair and verification metrics with and without autonomous repair configuration.",
            hypothesis="H2: Autonomous repair changes defect resolution metrics.",
            scenarios=[scenarios["SCENARIO_02"]],
            configurations=[configs["SEAM_FULL"], configs["ABLATION_NO_AUTONOMOUS_REPAIR"]],
            repetitions=3,
            metrics=["defect_count", "repair_count", "repair_resolution_rate", "targeted_verification_pass_rate", "regression_pass_rate", "qa_status"],
            version=CATALOG_VERSION,
            created_at=created_at,
        ),
        ExperimentDefinition(
            experiment_id="EXP_CONTRACT_INTELLIGENCE",
            name="Contract Intelligence Study",
            description="Compares recorded contract, runtime, E2E, repair, and QA metrics with and without contract intelligence.",
            hypothesis="H3: Contract intelligence changes contract compliance metrics.",
            scenarios=[scenarios["SCENARIO_03"]],
            configurations=[configs["SEAM_FULL"], configs["ABLATION_NO_CONTRACT_INTELLIGENCE"]],
            repetitions=3,
            metrics=["contract_issues", "runtime_failures", "e2e_failures", "repair_iterations", "qa_status", "contract_compliance_rate"],
            version=CATALOG_VERSION,
            created_at=created_at,
        ),
    ]
    return {experiment.experiment_id: experiment for experiment in experiments}
