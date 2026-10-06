from backend.agents.supervisor_agent import SupervisorAgent
from backend.evaluation.ablation import capability_enabled
from backend.evaluation.experiment_harness import EXPERIMENTS, ExperimentHarness
from backend.evaluation.scenario_catalog import experiment_catalog
from backend.models.contracts import DefectLocation, RepairPlan
from backend.models.evaluation import AggregateMetric, ExperimentComparison
from backend.models.state import ProjectState
from tests.test_experiment_harness import _state


def setup_function():
    EXPERIMENTS.clear()


def teardown_function():
    EXPERIMENTS.clear()


def test_ablation_capability_flags_change_execution_gate():
    state = ProjectState(project_id="ablation")
    state.experiment_summary = {
        "configuration_flags": {"domain_rag": False, "contract_intelligence": False, "autonomous_repair": False},
        "disabled_capabilities": ["domain-aware RAG", "full-stack contract intelligence", "autonomous repair"],
    }

    assert capability_enabled(state, "domain_rag") is False
    assert capability_enabled(state, "contract_intelligence") is False
    assert capability_enabled(state, "autonomous_repair") is False


def test_seam_full_leaves_capabilities_enabled():
    state = ProjectState(project_id="full")
    state.experiment_summary = {
        "configuration_flags": {"domain_rag": True, "contract_intelligence": True, "autonomous_repair": True},
        "disabled_capabilities": [],
    }

    assert capability_enabled(state, "domain_rag") is True
    assert capability_enabled(state, "contract_intelligence") is True
    assert capability_enabled(state, "autonomous_repair") is True


def test_no_autonomous_repair_blocks_supervisor_repair_routing():
    state = _state("ablation-repair")
    state.experiment_summary = {
        "configuration_flags": {"autonomous_repair": False},
        "disabled_capabilities": ["autonomous repair"],
    }
    state.repair_plans.append(RepairPlan(repair_id="RP-1", status="PENDING", defect_location=DefectLocation(layer="BACKEND")))

    result = SupervisorAgent().process(state)

    assert result.current_agent == "END"
    assert result.workflow_status == "failed"
    assert result.repair_plans[0].status == "PENDING"


def test_dry_run_reports_domain_rag_ablation_without_execution():
    harness = ExperimentHarness()
    experiment = harness.create_experiment(experiment_catalog()["EXP_DOMAIN_RAG"])

    dry_run = harness.dry_run(experiment.experiment_id)

    assert dry_run["execution"] == "DRY_RUN_ONLY"
    assert dry_run["repetitions"] == 3
    no_rag = next(config for config in dry_run["configurations"] if config["configuration_id"] == "ABLATION_NO_DOMAIN_RAG")
    assert "domain-aware RAG" in no_rag["disabled_capabilities"]
    assert no_rag["status"] == "OPERATIONAL"


def test_invalid_runs_are_excluded_from_aggregation():
    harness = ExperimentHarness()
    experiment = harness.create_experiment(experiment_catalog()["EXP_DOMAIN_RAG"])
    result = harness.record_run(experiment.experiment_id, _state("ablation-invalid"), "SCENARIO_05", "SEAM_FULL", persist=False)
    result.status = "INVALID"
    result.data_quality = {"valid": False, "failures": ["forced invalid"]}

    comparisons = harness.compare(experiment.experiment_id, metrics=["requirement_coverage"])

    assert comparisons[0].aggregate.count == 0
    assert comparisons[0].aggregate.mean == "NOT_APPLICABLE"


def test_quality_validation_detects_project_mismatch():
    harness = ExperimentHarness()
    experiment = harness.create_experiment(experiment_catalog()["EXP_DOMAIN_RAG"])
    state = _state("ablation-quality")
    result = harness.record_run(experiment.experiment_id, state, "SCENARIO_05", "SEAM_FULL", persist=False)
    state.project_id = "different-project"

    quality = harness.validate_run_result(result, state)

    assert quality["valid"] is False
    assert any("project_id" in item for item in quality["failures"])
