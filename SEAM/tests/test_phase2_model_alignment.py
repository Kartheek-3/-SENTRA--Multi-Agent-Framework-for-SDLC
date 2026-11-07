import pytest
import time
from unittest.mock import MagicMock, patch

from backend.llm.model_router import ModelRouter
from backend.events import event_bus
from backend.tools import diagram_generator
from backend.tools.diagram_adapter import adapt_to_react_flow
from backend.tools.diagram_validator import DiagramValidator
from backend.models.diagram import DiagramJSON, DiagramNode, DiagramEdge
from backend.models.analysis import AnalysisResult, Requirement
from backend.models.planning import (
    APIEndpoint,
    ArchitectureComponent,
    DatabaseEntity,
    ProjectPlan,
    SystemDesign,
)

def _get_mock_analysis():
    return AnalysisResult(
        project_summary="Cloud task orchestration system",
        application_domain="Cloud Workflow",
        functional_requirements=[
            Requirement(id="FR-001", description="Submit Workflow"),
            Requirement(id="FR-002", description="Monitor Status"),
        ],
        non_functional_requirements=[],
        actors=["Developer", "Worker Daemon"],
        entities=["Workflow", "TaskRun"],
        constraints=[],
        assumptions=[],
        risks=[],
        technical_considerations=[],
        ambiguities=[],
        recommended_capabilities=["Queue", "Scheduler"],
    )

def _get_mock_plan():
    return ProjectPlan(
        project_overview="High performance workflow engine",
        implementation_phases=["Core"],
        tasks=[],
        milestones=[],
        system_design=SystemDesign(
            architecture_style="Event-Driven Microservices",
            components=[
                ArchitectureComponent(
                    component_id="comp-gw",
                    name="API Gateway",
                    responsibility="REST Ingress and Auth",
                    technologies=["FastAPI"]
                ),
                ArchitectureComponent(
                    component_id="comp-worker",
                    name="Worker Engine",
                    responsibility="Task Execution",
                    technologies=["Python", "Docker"]
                ),
                ArchitectureComponent(
                    component_id="comp-db",
                    name="Telemetry Store",
                    responsibility="State DB and Metrics",
                    technologies=["PostgreSQL"]
                ),
            ],
            database_schema=[
                DatabaseEntity(name="Workflow", fields=["id", "name", "created_at"], relationships=["owns TaskRun"]),
                DatabaseEntity(name="TaskRun", fields=["id", "workflow_id", "status"], relationships=["belongs to Workflow"]),
            ],
            api_endpoints=[
                APIEndpoint(method="POST", path="/api/v1/workflows", purpose="Submit workflow"),
                APIEndpoint(method="GET", path="/api/v1/workflows/{id}", purpose="Get workflow state"),
            ],
            technology_stack=["FastAPI", "PostgreSQL", "React", "Docker"],
            security_considerations=["mTLS", "Role-based access"],
        ),
        implementation_strategy="Continuous Integration",
        risks_and_mitigations=[],
    )

def test_scenario_a_primary_or_live_model_real_inference():
    """Scenario A: Live host model qwen2.5-coder:1.5b executes real inference and measures latency."""
    router = ModelRouter()
    health = router.health()
    if health.get("active_local_available"):
        t0 = time.time()
        res = router.execute_inference(
            task_type="coding",
            prompt="Respond only with the word PONG."
        )
        latency_ms = (time.time() - t0) * 1000
        assert res["status"] == "success"
        assert res["actual_model"] == "qwen2.5-coder:1.5b"
        assert "pong" in res["response"].strip().lower()
        assert res["latency_ms"] > 0
        assert latency_ms > 0
    else:
        pytest.skip("Local Ollama not reachable in this run")

def test_scenario_b_primary_model_missing_routes_to_local_fallback():
    """Scenario B: Primary missing, router selects genuinely available local fallback."""
    router = ModelRouter()
    router.available_models = ["qwen2.5-coder:1.5b"]
    queue = event_bus.subscribe()
    
    # Requesting non-installed high-tier model
    resolved_model = router._get_safe_model_name("qwen3-coder-next", "coding")
    assert resolved_model == "qwen2.5-coder:1.5b"
    
    # Verify fallback event emitted
    events = []
    while not queue.empty():
        events.append(queue.get_nowait())
    fallback_events = [e for e in events if e.get("event") == "MODEL_FALLBACK_TRIGGERED"]
    assert len(fallback_events) >= 1
    assert fallback_events[0]["fallback_model"] == "qwen2.5-coder:1.5b"

def test_scenario_c_provider_offline_handled_gracefully():
    """Scenario C: Provider offline is handled gracefully with clear error status and latency recording."""
    router = ModelRouter()
    mock_chat = MagicMock()
    mock_chat.invoke.side_effect = Exception("Connection to Ollama refused on 127.0.0.1:11434")
    
    with patch.object(router, "get_model", return_value=mock_chat):
        res = router.execute_inference(
            task_type="coding",
            prompt="Hello"
        )
        assert res["status"] == "failed"
        assert "Connection to Ollama refused" in res["error"]
        assert "latency_ms" in res

def test_scenario_d_invalid_model_output_bounded_correction():
    """Scenario D: Invalid model output fails validation honestly and bounded correction triggers fallback."""
    analysis = _get_mock_analysis()
    plan = _get_mock_plan()
    
    # Mock planning chat invocation to return invalid non-JSON output
    mock_chat = MagicMock()
    mock_chat.invoke.return_value = "Sorry, I am an AI and I cannot generate this in JSON right now."
    
    with patch.object(ModelRouter, "get_model", return_value=mock_chat), \
         patch.object(ModelRouter, "model_available", return_value=True):
        res = diagram_generator.generate_diagram_with_llm("sequence_diagram", analysis, plan, force_llm=True)
        # Bounded correction failed to parse JSON, gracefully falls back to deterministic extraction
        assert res.generation_method == "deterministic_extraction"
        assert len(res.nodes) > 0
        assert len(res.edges) > 0
        is_valid, errors = DiagramValidator.validate(res)
        assert is_valid is True

def test_scenario_e_no_local_model_available():
    """Scenario E: No local model available reports unavailable honestly."""
    router = ModelRouter()
    with patch.object(router, "probe_ollama_health", return_value={"available": True, "models": []}), \
         patch.object(router, "_fetch_ollama_models", return_value=[]):
        router.available_models = []
        readiness = router.verify_local_model_readiness("non-existent-model")
        assert readiness["status"] == "LOCAL_MODEL_NOT_AVAILABLE"
        assert readiness["readiness"] == "NOT_AVAILABLE"
        assert readiness["inference_verified"] is False
        assert router.model_available("non-existent-model") is False

def test_four_canonical_diagrams_deterministic_integrity():
    """Validate 4 canonical diagram types (Architecture, Sequence, ERD, Deployment) under authoritative deterministic path."""
    analysis = _get_mock_analysis()
    plan = _get_mock_plan()
    diagram_types = ["architecture_diagram", "sequence_diagram", "erd_diagram", "deployment_diagram"]
    for dtype in diagram_types:
        diag = diagram_generator.generate_diagram_with_llm(dtype, analysis, plan, force_llm=False)
        assert diag.generation_method == "deterministic_extraction"
        assert diag.model_name == "grounded_evidence"
        assert len(diag.nodes) > 0
        
        # Validate schema and structural integrity
        is_valid, errors = DiagramValidator.validate(diag)
        assert is_valid is True, f"Deterministic {dtype} failed validation: {errors}"
        
        # Validate semantic integrity
        sem_valid, sem_errors = DiagramValidator.validate_semantic(diag, dtype)
        assert sem_valid is True, f"Deterministic {dtype} failed semantic validation: {sem_errors}"
        
        # Test React Flow adapter conversion
        rf_nodes, rf_edges = adapt_to_react_flow(diag, dtype)
        assert len(rf_nodes) == len(diag.nodes)
        assert len(rf_edges) == len(diag.edges)

def test_diagram_generator_live_llm_path_metadata_honesty():
    """Validate that when LLM generation succeeds, metadata accurately reflects the model and provider."""
    analysis = _get_mock_analysis()
    plan = _get_mock_plan()
    
    valid_llm_json = """{
        "diagram_type": "Architecture",
        "nodes": [
            {"id": "gw", "data": {"label": "API Gateway"}, "position": {"x": 100, "y": 100}},
            {"id": "svc", "data": {"label": "Worker Engine"}, "position": {"x": 400, "y": 100}}
        ],
        "edges": [
            {"id": "e1", "source": "gw", "target": "svc", "label": "routes"}
        ]
    }"""
    mock_chat = MagicMock()
    mock_chat.model_name = "qwen2.5-coder:1.5b"
    mock_response = MagicMock()
    mock_response.content = valid_llm_json
    mock_chat.invoke.return_value = mock_response

    with patch.object(ModelRouter, "get_model", return_value=mock_chat), \
         patch.object(ModelRouter, "model_available", return_value=True):
        res = diagram_generator.generate_diagram_with_llm("architecture_diagram", analysis, plan, force_llm=True)
        assert res.generation_method == "llm_inference"
        assert res.model_name == "qwen2.5-coder:1.5b"
        assert len(res.nodes) == 2
        assert len(res.edges) == 1
        
        is_valid, errors = DiagramValidator.validate(res)
        assert is_valid is True
        
        rf_nodes, rf_edges = adapt_to_react_flow(res, "architecture_diagram")
        assert len(rf_nodes) == 2
