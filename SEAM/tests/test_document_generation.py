import os
import pytest
from backend.models.analysis import AnalysisResult, Requirement
from backend.models.planning import ProjectPlan, SystemDesign, Task, ArchitectureComponent, DatabaseEntity, APIEndpoint
from backend.tools.document_generator import generate_analysis_document, generate_design_document

def _mock_analysis_result():
    return AnalysisResult(
        project_summary="summary",
        application_domain="E-Commerce System",
        functional_requirements=[Requirement(id="FR-001", description="Auth")],
        non_functional_requirements=[Requirement(id="NFR-001", description="Fast")],
        actors=["User"],
        entities=["Order"],
        constraints=["C1"],
        assumptions=["A1"],
        risks=["R1"],
        technical_considerations=["T1"],
        ambiguities=["None"],
        recommended_capabilities=["Cap1"]
    )

def _mock_project_plan():
    return ProjectPlan(
        project_overview="Overview",
        implementation_phases=["Phase 1"],
        tasks=[Task(task_id="T1", title="Task 1", description="Desc", capability="Core", priority="High", estimated_complexity="Low", related_requirements=["FR-001"])],
        milestones=["M1"],
        system_design=SystemDesign(
            architecture_style="Microservices",
            components=[ArchitectureComponent(component_id="C1", name="Auth", responsibility="Auth", technologies=["JWT"], dependencies=[])],
            data_flow="Flow",
            database_schema=[DatabaseEntity(name="User", description="User", fields=["id"], relationships=[])],
            api_endpoints=[APIEndpoint(method="GET", path="/api", purpose="test", request_schema="{}", response_schema="{}", authentication_required=False)],
            technology_stack=["Python"],
            security_considerations=["HTTPS"]
        ),
        implementation_strategy="Agile",
        risks_and_mitigations=["None"]
    )

def test_analysis_document_generation():
    analysis = _mock_analysis_result()
    path = generate_analysis_document("proj-1", analysis)
    assert os.path.exists(path)
    assert "e_commerce_system" in path or "proj-1" in path
    
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    assert "# Requirements Analysis" in content
    assert "E-Commerce System" in content
    assert "FR-001" in content
    assert "Auth" in content
    assert "NFR-001" in content
    assert "| FR-001 | Auth |" in content

def test_design_document_generation():
    plan = _mock_project_plan()
    path = generate_design_document("proj-1", "domain", plan)
    assert os.path.exists(path)
    
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    assert "# System Design" in content
    assert "Microservices" in content
    assert "Auth (C1)" in content
    assert "T1" in content
    assert "FR-001" in content
