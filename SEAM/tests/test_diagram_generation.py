import json
import os

from backend.models.analysis import AnalysisResult, Requirement
from backend.models.diagram import DiagramEdge, DiagramJSON, DiagramNode
from backend.models.planning import (
    APIEndpoint,
    ArchitectureComponent,
    DatabaseEntity,
    ProjectPlan,
    SystemDesign,
)
from backend.tools import diagram_generator


def _mock_analysis_result():
    return AnalysisResult(
        project_summary="summary",
        application_domain="E-Commerce System",
        functional_requirements=[Requirement(id="FR-001", description="Auth")],
        non_functional_requirements=[Requirement(id="NFR-001", description="Fast")],
        actors=["User", "Admin"],
        entities=["Order", "Product"],
        constraints=["C1"],
        assumptions=["A1"],
        risks=["R1"],
        technical_considerations=["T1"],
        ambiguities=["None"],
        recommended_capabilities=["Cap1"],
    )


def _mock_project_plan():
    return ProjectPlan(
        project_overview="Overview",
        implementation_phases=["Phase 1"],
        tasks=[],
        milestones=["M1"],
        system_design=SystemDesign(
            architecture_style="Microservices",
            components=[
                ArchitectureComponent(
                    component_id="C1",
                    name="Auth",
                    responsibility="Auth",
                    technologies=["JWT"],
                    dependencies=[],
                )
            ],
            data_flow="Flow",
            database_schema=[
                DatabaseEntity(name="User", description="User", fields=["id"], relationships=[]),
                DatabaseEntity(name="Order", description="Order", fields=["id", "userId"], relationships=[]),
            ],
            api_endpoints=[
                APIEndpoint(
                    method="GET",
                    path="/api",
                    purpose="test",
                    request_schema="{}",
                    response_schema="{}",
                    authentication_required=False,
                )
            ],
            technology_stack=["Python"],
            security_considerations=["HTTPS"],
        ),
        implementation_strategy="Agile",
        risks_and_mitigations=["None"],
    )


def test_diagram_generation_writes_structured_json(monkeypatch):
    def fake_generate(diagram_type, analysis, plan):
        return DiagramJSON(
            diagram_type=diagram_type,
            nodes=[
                DiagramNode(
                    id="user",
                    type="input",
                    data={"label": "User"},
                    position={"x": 0, "y": 0},
                ),
                DiagramNode(
                    id="api",
                    data={"label": "/api"},
                    position={"x": 200, "y": 0},
                ),
            ],
            edges=[DiagramEdge(id="e1", source="user", target="api", label="uses")],
        )

    monkeypatch.setattr(diagram_generator, "generate_diagram_with_llm", fake_generate)

    paths = diagram_generator.generate_all_diagrams("proj-1", "domain", _mock_analysis_result(), _mock_project_plan())

    assert len(paths) == 8
    assert {os.path.basename(path) for path in paths} == {
        "architecture.json",
        "use_case.json",
        "class.json",
        "object.json",
        "sequence.json",
        "activity.json",
        "dfd_level_0.json",
        "dfd_level_1.json",
    }

    for path in paths:
        assert os.path.exists(path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["diagram_type"]
        assert data["nodes"][0]["data"]["label"] == "User"
        assert data["edges"][0]["source"] == "user"
