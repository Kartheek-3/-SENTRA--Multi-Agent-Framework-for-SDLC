from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.evaluation.experiment_harness import EXPERIMENTS, ExperimentHarness
from backend.evaluation.scenario_catalog import experiment_catalog, scenario_catalog
from backend.models.evaluation import ExperimentDefinition

router = APIRouter(prefix="/api/experiments", tags=["experiments"])


class CreateExperimentRequest(BaseModel):
    definition: ExperimentDefinition


class CompareExperimentRequest(BaseModel):
    metrics: Optional[List[str]] = None


class ExecuteRunRequest(BaseModel):
    scenario_id: str
    configuration_id: str
    repetition_index: int = 1


@router.post("")
def create_experiment(request: CreateExperimentRequest):
    experiment = ExperimentHarness().create_experiment(request.definition)
    return experiment.model_dump()


@router.get("/scenarios")
def list_scenarios():
    return {
        "scenarios": [scenario.model_dump() for scenario in scenario_catalog().values()]
    }


@router.get("/scenarios/{scenario_id}")
def get_scenario(scenario_id: str):
    scenarios = scenario_catalog()
    if scenario_id not in scenarios:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenarios[scenario_id].model_dump()


@router.get("/catalog")
def get_experiment_catalog():
    return {
        "experiments": [experiment.model_dump() for experiment in experiment_catalog().values()]
    }


@router.get("")
def list_experiments():
    return {
        "experiments": [
            {
                "experiment_id": experiment.experiment_id,
                "name": experiment.definition.name,
                "status": experiment.status,
                "run_count": len(experiment.runs),
                "created_at": experiment.created_at,
            }
            for experiment in EXPERIMENTS.values()
        ]
    }


@router.get("/{experiment_id}")
def get_experiment(experiment_id: str):
    if experiment_id not in EXPERIMENTS:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return EXPERIMENTS[experiment_id].model_dump()


@router.get("/{experiment_id}/runs")
def get_experiment_runs(experiment_id: str):
    if experiment_id not in EXPERIMENTS:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return {
        "experiment_id": experiment_id,
        "runs": [run.model_dump() for run in EXPERIMENTS[experiment_id].runs],
    }


@router.get("/{experiment_id}/comparison")
def get_experiment_comparison(experiment_id: str):
    if experiment_id not in EXPERIMENTS:
        raise HTTPException(status_code=404, detail="Experiment not found")
    experiment = EXPERIMENTS[experiment_id]
    if not experiment.comparisons:
        ExperimentHarness().compare(experiment_id)
    return {
        "experiment_id": experiment_id,
        "comparisons": [comparison.model_dump() for comparison in experiment.comparisons],
    }


@router.get("/{experiment_id}/matrix")
def get_experiment_matrix(experiment_id: str):
    if experiment_id not in EXPERIMENTS:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return ExperimentHarness().experiment_matrix(experiment_id)


@router.get("/{experiment_id}/dry-run")
def dry_run_experiment(experiment_id: str):
    if experiment_id not in EXPERIMENTS:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return ExperimentHarness().dry_run(experiment_id)


@router.post("/{experiment_id}/runs")
def execute_experiment_run(experiment_id: str, request: ExecuteRunRequest):
    if experiment_id not in EXPERIMENTS:
        raise HTTPException(status_code=404, detail="Experiment not found")
    result = ExperimentHarness().execute_controlled_run(
        experiment_id,
        request.scenario_id,
        request.configuration_id,
        repetition_index=request.repetition_index,
    )
    return result.model_dump()


@router.post("/{experiment_id}/comparison")
def compare_experiment(experiment_id: str, request: CompareExperimentRequest):
    if experiment_id not in EXPERIMENTS:
        raise HTTPException(status_code=404, detail="Experiment not found")
    comparisons = ExperimentHarness().compare(experiment_id, metrics=request.metrics)
    return {
        "experiment_id": experiment_id,
        "comparisons": [comparison.model_dump() for comparison in comparisons],
    }
