import json
import os
import pytest
from fastapi.testclient import TestClient

from backend.models.analysis import AnalysisResult, Requirement
from backend.models.diagram import DiagramEdge, DiagramJSON, DiagramNode
from backend.models.planning import (
    APIEndpoint,
    ArchitectureComponent,
    DatabaseEntity,
    ProjectPlan,
    SystemDesign,
)
from backend.models.state import ProjectState
from backend.tools import diagram_generator
from backend.tools.diagram_templates import (
    CANONICAL_DIAGRAM_TYPES,
    DiagramSelectionService,
    normalize_diagram_identifier,
    registry as template_registry,
)
from backend.tools.diagram_adapter import adapt_to_react_flow
from backend.tools.diagram_validator import DiagramValidator
from backend.tools.diagram_exporter import export_diagram_to_mermaid
from backend.main import app
from backend.api.projects import projects_db


def _mock_analysis_result():
    return AnalysisResult(
        project_summary="E-commerce web system with user management and orders",
        application_domain="E-Commerce System",
        functional_requirements=[
            Requirement(id="FR-001", description="User Authentication and Registration"),
            Requirement(id="FR-002", description="Product Catalog Browsing"),
            Requirement(id="FR-003", description="Checkout and Order Processing"),
        ],
        non_functional_requirements=[Requirement(id="NFR-001", description="Fast API response < 200ms")],
        actors=["Customer", "Administrator", "Payment Gateway"],
        entities=["User", "Order", "Product", "Payment"],
        constraints=["HTTPS strictly enforced"],
        assumptions=["SQLite persistence locally"],
        risks=["Payment service downtime"],
        technical_considerations=["RESTful JSON API"],
        ambiguities=["None"],
        recommended_capabilities=["Auth", "Cart", "Checkout"],
    )


def _mock_project_plan():
    return ProjectPlan(
        project_overview="E-commerce autonomous architecture plan",
        implementation_phases=["Phase 1: Foundation", "Phase 2: Core Services"],
        tasks=[],
        milestones=["M1: MVP Ready"],
        system_design=SystemDesign(
            architecture_style="Modular Microservices",
            components=[
                ArchitectureComponent(
                    component_id="C1",
                    name="AuthService",
                    responsibility="Authentication & Tokens",
                    technologies=["JWT", "FastAPI"],
                    dependencies=["DatabaseService"],
                ),
                ArchitectureComponent(
                    component_id="C2",
                    name="OrderService",
                    responsibility="Order management & Checkout",
                    technologies=["Python"],
                    dependencies=["AuthService", "DatabaseService"],
                ),
                ArchitectureComponent(
                    component_id="C3",
                    name="DatabaseService",
                    responsibility="Relational Data Storage",
                    technologies=["SQLite", "PostgreSQL"],
                    dependencies=[],
                ),
            ],
            data_flow="Client -> API Gateway -> Services -> Database",
            database_schema=[
                DatabaseEntity(name="User", description="User table", fields=["id", "email", "password_hash"], relationships=["1:N with Order"]),
                DatabaseEntity(name="Order", description="Order table", fields=["id", "user_id", "total_amount", "status"], relationships=["N:1 with User"]),
                DatabaseEntity(name="Product", description="Product catalog", fields=["id", "title", "price", "stock"], relationships=[]),
            ],
            api_endpoints=[
                APIEndpoint(
                    method="POST",
                    path="/api/auth/login",
                    purpose="User authentication",
                    request_schema="{}",
                    response_schema="{}",
                    authentication_required=False,
                ),
                APIEndpoint(
                    method="GET",
                    path="/api/orders",
                    purpose="List user orders",
                    request_schema="{}",
                    response_schema="{}",
                    authentication_required=True,
                ),
            ],
            technology_stack=["React", "FastAPI", "SQLite", "Docker"],
            security_considerations=["JWT Auth", "Password Hashing"],
        ),
        implementation_strategy="Agile",
        risks_and_mitigations=["None"],
    )


def test_template_registry_registers_all_10_canonical_types():
    templates = template_registry.list_templates()
    assert len(templates) == 10
    expected_ids = {
        "architecture_diagram",
        "use_case_diagram",
        "class_diagram",
        "object_diagram",
        "sequence_diagram",
        "activity_diagram",
        "dfd_level_0",
        "dfd_level_1",
        "erd_diagram",
        "deployment_diagram",
    }
    assert {t.canonical_id for t in templates} == expected_ids

    # Verify each template has required properties
    for t in templates:
        assert t.canonical_id
        assert t.canonical_name
        assert t.label
        assert t.schema_class
        assert len(t.required_fields) > 0
        assert t.prompt_instruction


def test_canonical_identifier_normalization_handles_aliases():
    # Architecture
    assert normalize_diagram_identifier("architecture")["id"] == "architecture_diagram"
    assert normalize_diagram_identifier("architecture_diagram")["id"] == "architecture_diagram"
    assert normalize_diagram_identifier("architecture-diagram")["id"] == "architecture_diagram"
    assert normalize_diagram_identifier("Architecture")["id"] == "architecture_diagram"

    # ERD
    assert normalize_diagram_identifier("erd")["id"] == "erd_diagram"
    assert normalize_diagram_identifier("erd_diagram")["id"] == "erd_diagram"
    assert normalize_diagram_identifier("ERD (Database)")["id"] == "erd_diagram"
    assert normalize_diagram_identifier("erd database")["id"] == "erd_diagram"

    # Deployment
    assert normalize_diagram_identifier("deployment")["id"] == "deployment_diagram"
    assert normalize_diagram_identifier("deployment_diagram")["id"] == "deployment_diagram"
    assert normalize_diagram_identifier("Deployment")["id"] == "deployment_diagram"

    # DFD
    assert normalize_diagram_identifier("dfd_level_0")["id"] == "dfd_level_0"
    assert normalize_diagram_identifier("DFD Level 0")["id"] == "dfd_level_0"
    assert normalize_diagram_identifier("dfd_level_1")["id"] == "dfd_level_1"

    # Invalid
    assert normalize_diagram_identifier("non_existent_diagram") is None
    assert normalize_diagram_identifier("") is None


def test_selection_service_authoritative_resolution():
    assert DiagramSelectionService.is_valid_diagram_type("architecture") is True
    assert DiagramSelectionService.is_valid_diagram_type("ERD (Database)") is True
    assert DiagramSelectionService.is_valid_diagram_type("unknown_junk") is False
    assert DiagramSelectionService.resolve_canonical_id("erd") == "erd_diagram"
    assert len(DiagramSelectionService.list_canonical_diagrams()) == 10


def test_generation_all_10_canonical_diagrams_from_evidence():
    analysis = _mock_analysis_result()
    plan = _mock_project_plan()

    paths = diagram_generator.generate_all_diagrams("proj-e2e", "e2e_domain", analysis, plan)

    # 10 canonical files + alias files
    assert len(paths) >= 10
    basenames = {os.path.basename(p) for p in paths}

    for d_def in CANONICAL_DIAGRAM_TYPES:
        assert d_def["filename"] in basenames
        assert f"{d_def['id']}.json" in basenames

    # Verify every generated JSON file
    for p in paths:
        assert os.path.exists(p)
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["diagram_type"]
        assert len(data["nodes"]) > 0
        assert "mermaid" in data
        assert any(k in data["mermaid"] for k in ["flowchart", "sequenceDiagram", "classDiagram", "erDiagram"])


def test_all_10_canonical_diagram_generation_individually():
    analysis = _mock_analysis_result()
    plan = _mock_project_plan()

    for d_def in CANONICAL_DIAGRAM_TYPES:
        res = diagram_generator.generate_diagram_with_llm(d_def["id"], analysis, plan)
        assert res.diagram_type
        assert len(res.nodes) > 0
        is_valid, errors = DiagramValidator.validate(res)
        assert is_valid is True, f"Diagram {d_def['id']} failed validation: {errors}"


def test_erd_and_deployment_specific_structural_evidence():
    analysis = _mock_analysis_result()
    plan = _mock_project_plan()

    # 1. ERD
    erd_res = diagram_generator.generate_diagram_with_llm("erd_diagram", analysis, plan)
    assert erd_res.diagram_type == "ERD (Database)"
    node_labels = [n.data.get("label", "") for n in erd_res.nodes]
    assert any("User" in l for l in node_labels)
    assert any("Order" in l for l in node_labels)
    assert any("Product" in l for l in node_labels)
    assert len(erd_res.edges) >= 1

    # 2. Deployment
    dep_res = diagram_generator.generate_diagram_with_llm("deployment_diagram", analysis, plan)
    assert dep_res.diagram_type == "Deployment"
    dep_labels = [n.data.get("label", "") for n in dep_res.nodes]
    assert any("Browser" in l or "Client" in l for l in dep_labels)
    assert any("Backend" in l or "FastAPI" in l for l in dep_labels)
    assert any("Database" in l or "SQLite" in l for l in dep_labels)
    assert len(dep_res.edges) >= 2


def test_diagram_validator_detects_structural_defects():
    # Valid diagram
    valid_diag = DiagramJSON(
        diagram_type="Architecture",
        nodes=[DiagramNode(id="n1", data={"label": "N1"}), DiagramNode(id="n2", data={"label": "N2"})],
        edges=[DiagramEdge(id="e1", source="n1", target="n2")],
    )
    is_valid, errors = DiagramValidator.validate(valid_diag)
    assert is_valid is True
    assert len(errors) == 0

    # Duplicate node ID
    dup_diag = DiagramJSON(
        diagram_type="Architecture",
        nodes=[DiagramNode(id="dup", data={"label": "N1"}), DiagramNode(id="dup", data={"label": "N2"})],
        edges=[],
    )
    is_valid, errors = DiagramValidator.validate(dup_diag)
    assert is_valid is False
    assert any(e["code"] == "DUPLICATE_NODE_ID" for e in errors)

    # Dangling edge endpoint
    dangling_diag = DiagramJSON(
        diagram_type="Architecture",
        nodes=[DiagramNode(id="n1", data={"label": "N1"})],
        edges=[DiagramEdge(id="e1", source="n1", target="missing_target")],
    )
    is_valid, errors = DiagramValidator.validate(dangling_diag)
    assert is_valid is False
    assert any(e["code"] == "DANGLING_EDGE_TARGET" for e in errors)

    # Empty nodes
    empty_diag = DiagramJSON(diagram_type="Architecture", nodes=[], edges=[])
    is_valid, errors = DiagramValidator.validate(empty_diag)
    assert is_valid is False
    assert any(e["code"] == "EMPTY_NODES" for e in errors)


def test_semantic_validation_rules():
    # Sequence with 0 edges and 1 participant fails
    bad_seq = DiagramJSON(
        diagram_type="Sequence",
        nodes=[DiagramNode(id="p1", data={"label": "Lone Participant"})],
        edges=[],
    )
    is_valid, errors = DiagramValidator.validate_semantic(bad_seq, "sequence_diagram")
    assert is_valid is False
    assert any("TOO_FEW_PARTICIPANTS" in e["code"] for e in errors)

    # Sequence with 2 participants passes
    good_seq = DiagramJSON(
        diagram_type="Sequence",
        nodes=[DiagramNode(id="p1", data={"label": "P1"}), DiagramNode(id="p2", data={"label": "P2"})],
        edges=[DiagramEdge(id="e1", source="p1", target="p2", label="call")],
    )
    is_valid, errors = DiagramValidator.validate_semantic(good_seq, "sequence_diagram")
    assert is_valid is True


def test_diagram_adapter_converts_specialized_schemas():
    # Sequence schema
    seq_data = {
        "diagram_type": "sequence",
        "participants": [{"id": "user", "name": "User"}, {"id": "api", "name": "API"}],
        "messages": [{"id": "m1", "from_node": "user", "to_node": "api", "message": "GET /data"}],
    }
    nodes, edges = adapt_to_react_flow(seq_data, "sequence_diagram")
    assert len(nodes) == 2
    assert nodes[0].id == "user"
    assert nodes[1].id == "api"
    assert len(edges) == 1
    assert edges[0].source == "user"
    assert edges[0].target == "api"
    assert edges[0].label == "GET /data"

    # Architecture layer schema
    arch_data = {
        "diagram_type": "architecture",
        "layers": [
            {"id": "l1", "name": "Frontend", "nodes": [{"id": "ui", "label": "WebUI"}]},
            {"id": "l2", "name": "Backend", "nodes": [{"id": "api", "label": "API"}]},
        ],
        "connections": [{"id": "c1", "source": "ui", "target": "api", "label": "HTTPS"}],
    }
    nodes, edges = adapt_to_react_flow(arch_data, "architecture_diagram")
    assert len(nodes) == 2
    assert len(edges) == 1
    assert edges[0].label == "HTTPS"


def test_api_diagram_retrieval_with_legacy_and_canonical_names():
    client = TestClient(app)
    project_id = "test-proj-diag-api"

    # Setup project in memory DB
    state = ProjectState(
        project_id=project_id,
        user_requirement="Build e-commerce system",
        domain="diag_api_test",
        structured_requirements=_mock_analysis_result(),
        project_plan=_mock_project_plan(),
    )
    projects_db[project_id] = state

    # Generate diagrams
    diagram_generator.generate_all_diagrams(project_id, "diag_api_test", state.structured_requirements, state.project_plan)

    # 1. Test get_diagrams list endpoint
    list_resp = client.get(f"/api/projects/{project_id}/diagrams")
    assert list_resp.status_code == 200
    available = list_resp.json()["diagrams"]
    assert "architecture" in available or "architecture_diagram" in available
    assert "erd_diagram" in available or "erd" in available
    assert "deployment_diagram" in available or "deployment" in available

    # 2. Test retrieval using frontend canonical ID (e.g., architecture_diagram)
    resp1 = client.get(f"/api/projects/{project_id}/diagrams/architecture_diagram")
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["diagram_type"] == "Architecture"
    assert len(data1["nodes"]) > 0
    assert len(data1["edges"]) >= 0

    # 3. Test retrieval using legacy alias (e.g., architecture)
    resp2 = client.get(f"/api/projects/{project_id}/diagrams/architecture")
    assert resp2.status_code == 200
    assert resp2.json()["diagram_type"] == "Architecture"

    # 4. Test ERD retrieval
    resp_erd = client.get(f"/api/projects/{project_id}/diagrams/erd_diagram")
    assert resp_erd.status_code == 200
    assert "ERD" in resp_erd.json()["diagram_type"]

    # 5. Test Deployment retrieval
    resp_dep = client.get(f"/api/projects/{project_id}/diagrams/deployment_diagram")
    assert resp_dep.status_code == 200
    assert resp_dep.json()["diagram_type"] == "Deployment"

    # 6. Test invalid diagram returns 404
    resp_inv = client.get(f"/api/projects/{project_id}/diagrams/invalid_random_diagram")
    assert resp_inv.status_code == 404


def test_api_regenerate_diagram_endpoint():
    client = TestClient(app)
    project_id = "test-proj-regen"

    state = ProjectState(
        project_id=project_id,
        user_requirement="Build order management",
        domain="regen_test",
        structured_requirements=_mock_analysis_result(),
        project_plan=_mock_project_plan(),
    )
    projects_db[project_id] = state

    # Regenerate ERD
    resp = client.post(f"/api/projects/{project_id}/diagrams/erd_diagram/regenerate")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "regenerated"
    assert body["canonical_id"] == "erd_diagram"
    assert "erd_diagram.json" in body["source_path"]

    # Retrieval after regenerate
    fetch_resp = client.get(f"/api/projects/{project_id}/diagrams/erd_diagram")
    assert fetch_resp.status_code == 200
    data = fetch_resp.json()
    assert len(data["nodes"]) > 0
