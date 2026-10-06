import uuid

from backend.evaluation.experiment_harness import EXPERIMENTS, ExperimentHarness
from backend.evaluation.scenario_catalog import controlled_configurations, experiment_catalog, scenario_catalog
from backend.models.evaluation import ExperimentDefinition, RunConfiguration
from tests.test_experiment_harness import _state


def setup_function():
    EXPERIMENTS.clear()


def teardown_function():
    EXPERIMENTS.clear()


def test_scenario_catalog_contains_required_research_scenarios():
    catalog = scenario_catalog()

    assert set(catalog) == {"SCENARIO_01", "SCENARIO_02", "SCENARIO_03", "SCENARIO_04", "SCENARIO_05"}
    healthcare = catalog["SCENARIO_05"]
    assert healthcare.domain == "healthcare"
    assert healthcare.complexity == "LARGE"
    assert healthcare.required_features
    assert healthcare.expected_artifacts
    assert healthcare.expected_validation_layers
    assert "proven" not in healthcare.description.lower()


def test_controlled_configurations_include_ablation_metadata_without_results():
    configs = {config.configuration_id: config for config in controlled_configurations()}

    assert configs["SEAM_FULL"].flags["domain_rag"] is True
    assert "domain-aware RAG" in configs["ABLATION_NO_DOMAIN_RAG"].disabled_capabilities
    assert configs["BASELINE"].baseline_provenance
    assert configs["BASELINE"].baseline_source is None


def test_experiment_catalog_defines_hypotheses_and_matrix_inputs():
    experiments = experiment_catalog()

    assert set(experiments) == {"EXP_DOMAIN_RAG", "EXP_AUTONOMOUS_REPAIR", "EXP_CONTRACT_INTELLIGENCE"}
    domain = experiments["EXP_DOMAIN_RAG"]
    assert domain.scenarios[0].scenario_id == "SCENARIO_05"
    assert {config.configuration_id for config in domain.configurations} == {"SEAM_FULL", "ABLATION_NO_DOMAIN_RAG"}
    assert domain.repetitions == 3
    assert "proven" not in domain.hypothesis.lower()


def test_experiment_matrix_generation_tracks_completed_runs_only():
    harness = ExperimentHarness()
    experiment = harness.create_experiment(experiment_catalog()["EXP_DOMAIN_RAG"])
    state = _state(f"catalog-{uuid.uuid4().hex}")

    harness.record_run(experiment.experiment_id, state, "SCENARIO_05", "SEAM_FULL", repetition_index=1, persist=False)
    matrix = harness.experiment_matrix(experiment.experiment_id)

    seam_full = matrix["scenarios"]["SCENARIO_05"]["configurations"]["SEAM_FULL"]
    ablation = matrix["scenarios"]["SCENARIO_05"]["configurations"]["ABLATION_NO_DOMAIN_RAG"]
    assert seam_full["expected_repetitions"] == 3
    assert seam_full["completed_runs"] == 1
    assert ablation["completed_runs"] == 0


def test_dataset_normalization_contains_required_fields():
    harness = ExperimentHarness()
    experiment = harness.create_experiment(experiment_catalog()["EXP_AUTONOMOUS_REPAIR"])
    harness.record_run(experiment.experiment_id, _state(f"catalog-{uuid.uuid4().hex}"), "SCENARIO_02", "SEAM_FULL", persist=False)

    row = harness.dataset(experiment)[0]

    for field in [
        "experiment_id",
        "scenario_id",
        "configuration_id",
        "run_id",
        "requirements",
        "requirement_coverage",
        "contract_compliance_rate",
        "e2e_pass_rate",
        "defect_count",
        "resolved_defects",
        "repair_iterations",
        "repair_resolution_rate",
        "qa_status",
        "delivery_status",
        "runtime_duration",
        "workflow_duration",
    ]:
        assert field in row


def test_missing_catalog_metric_aggregation_is_not_applicable():
    scenario = scenario_catalog()["SCENARIO_01"]
    config = RunConfiguration(configuration_id="SEAM_FULL", mode="SEAM_FULL")
    definition = ExperimentDefinition(
        experiment_id="EXP_MISSING_METRIC",
        name="Missing Metric",
        scenarios=[scenario],
        configurations=[config],
        metrics=["unknown_metric"],
    )
    harness = ExperimentHarness()
    experiment = harness.create_experiment(definition)
    harness.record_run(experiment.experiment_id, _state(f"catalog-{uuid.uuid4().hex}"), scenario.scenario_id, config.configuration_id, persist=False)

    comparison = harness.compare(experiment.experiment_id)[0]

    assert comparison.aggregate.count == 0
    assert comparison.aggregate.mean == "NOT_APPLICABLE"
