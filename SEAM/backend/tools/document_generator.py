import os
import json
from backend.models.analysis import AnalysisResult
from backend.models.planning import ProjectPlan
from backend.utils import slugify
from backend.tools.artifact_pipeline import write_text_artifact


def _items(items):
    return "\n".join(f"- {item}" for item in items) if items else "- None identified"


def _req_table(requirements):
    lines = ["| ID | Requirement |", "|---|---|"]
    for req in requirements:
        desc = req.description.replace("|", "\\|")
        lines.append(f"| {req.id} | {desc} |")
    return "\n".join(lines)


def _cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def generate_analysis_artifacts(state) -> list[dict]:
    analysis = state.structured_requirements
    if not analysis:
        raise ValueError("Analysis artifacts require structured_requirements")

    scale = analysis.scale_assessment.scale_level.value if analysis.scale_assessment else "UNKNOWN"
    all_reqs = analysis.functional_requirements + analysis.non_functional_requirements
    files = [
        ("analysis/README.md", f"""# Analysis - {analysis.application_domain}

## Purpose
This document records the Analysis Agent output for the project and provides the source of truth for downstream planning and implementation.

## Project Overview
{analysis.project_summary}

## Problem Statement
{state.user_requirement}

## Requirements Summary
- Functional requirements: {len(analysis.functional_requirements)}
- Non-functional requirements: {len(analysis.non_functional_requirements)}
- Scale classification: {scale}

## Functional Requirements
{_req_table(analysis.functional_requirements)}

## Non-Functional Requirements
{_req_table(analysis.non_functional_requirements)}

## Technology Requirements And Considerations
{_items(analysis.technical_considerations)}

## Constraints
{_items(analysis.constraints)}

## Assumptions
{_items(analysis.assumptions)}

## Risks
{_items(analysis.risks)}

## AnalysisAgent Completion Status
COMPLETED. Required analysis artifacts were generated, read back, and registered.
""", "ANALYSIS"),
        ("analysis/requirements.md", f"""# Requirements

## Complete Requirement Traceability Table
{_req_table(all_reqs)}

## Actors
{_items(analysis.actors)}

## Domain Entities
{_items(analysis.entities)}
""", "ANALYSIS"),
        ("analysis/functional_requirements.md", f"""# Functional Requirements

{_req_table(analysis.functional_requirements)}

## Requirement Details
{chr(10).join(f'### {req.id}{chr(10)}{req.description}' for req in analysis.functional_requirements)}
""", "ANALYSIS"),
        ("analysis/non_functional_requirements.md", f"""# Non-Functional Requirements

{_req_table(analysis.non_functional_requirements)}

## Quality Attributes
- Scalability: {scale}
- Performance: Derived from the stated requirements and selected scale.
- Availability: Appropriate for the selected scale unless stricter needs are specified.
- Security: {_items([item for item in analysis.technical_considerations if 'security' in item.lower()] or ['Use safe validation and avoid exposing sensitive data.'])}
- Maintainability: Keep the implementation understandable and traceable to requirement IDs.
- Usability: Support the actors identified in analysis.
""", "ANALYSIS"),
        ("analysis/technology_analysis.md", f"""# Technology Analysis

## Frontend
Derived from the user's requested technologies and the analysis constraints.

## Backend
Derived from the user's requested technologies and API needs.

## Database
Selected during Planning based on entities: {', '.join(analysis.entities) if analysis.entities else 'No persistent entities identified yet'}.

## APIs
APIs are planned from functional requirements:
{_req_table(analysis.functional_requirements)}

## Supporting Technologies
{_items(analysis.technical_considerations)}

## Rationale
Technology choices should remain consistent with the project scale ({scale}), constraints, and requirement IDs above.
""", "ANALYSIS"),
    ]
    return [write_text_artifact(state, path, content, kind, "AnalysisAgent") for path, content, kind in files]

def generate_analysis_document(project_id: str, analysis: AnalysisResult) -> str:
    project_name = slugify(analysis.application_domain) or slugify(project_id)
    doc_dir = f"generated_projects/{project_name}/analysis"
    os.makedirs(doc_dir, exist_ok=True)
    
    path = f"{doc_dir}/requirements_analysis.md"
    
    lines = [
        "# Requirements Analysis\n",
        "## 1. Project Summary",
        f"{analysis.project_summary}\n",
        "## 2. Application Domain",
        f"{analysis.application_domain}\n",
        "## 3. Actors",
        "\n".join(f"- {a}" for a in analysis.actors) + "\n",
        "## 4. Functional Requirements"
    ]
    
    for req in analysis.functional_requirements:
        lines.append(f"**{req.id}**: {req.description}")
    lines.append("")
    
    lines.append("## 5. Non-Functional Requirements")
    for req in analysis.non_functional_requirements:
        lines.append(f"**{req.id}**: {req.description}")
    lines.append("")
    
    lines.append("## 6. Entities")
    lines.append("\n".join(f"- {e}" for e in analysis.entities) + "\n")
    
    lines.append("## 7. Constraints")
    lines.append("\n".join(f"- {c}" for c in analysis.constraints) + "\n")
    
    lines.append("## 8. Assumptions")
    lines.append("\n".join(f"- {a}" for a in analysis.assumptions) + "\n")
    
    lines.append("## 9. Risks")
    lines.append("\n".join(f"- {r}" for r in analysis.risks) + "\n")
    
    lines.append("## 10. Technical Considerations")
    lines.append("\n".join(f"- {t}" for t in analysis.technical_considerations) + "\n")
    
    lines.append("## 11. Ambiguities")
    lines.append("\n".join(f"- {a}" for a in analysis.ambiguities) + "\n")
    
    lines.append("## 12. Recommended Capabilities")
    lines.append("\n".join(f"- {r}" for r in analysis.recommended_capabilities) + "\n")
    
    lines.append("## 13. Requirement Traceability Summary")
    lines.append("| ID | Description |")
    lines.append("|---|---|")
    for req in analysis.functional_requirements + analysis.non_functional_requirements:
        desc = req.description.replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {req.id} | {desc} |")
        
    content = "\n".join(lines)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
        
    return path


def generate_design_artifacts(state) -> list[dict]:
    plan = state.project_plan
    if not plan:
        raise ValueError("Design artifacts require project_plan")
    design = plan.system_design
    components = "\n".join(f"| {c.component_id} | {c.name} | {c.responsibility} | {', '.join(c.technologies)} |" for c in design.components) or "| - | - | - | - |"
    apis = "\n".join(f"| {a.method} | {a.path} | {a.purpose} | `{a.request_schema}` | `{a.response_schema}` | {a.authentication_required} |" for a in design.api_endpoints) or "| - | - | - | - | - | - |"
    db = "\n".join(f"### {entity.name}\n\n{entity.description}\n\n**Fields:** {', '.join(entity.fields) or 'None'}\n\n**Relationships:** {', '.join(entity.relationships) or 'None'}\n" for entity in design.database_schema) or "No database entities are required by the current plan."
    tasks = "\n".join(f"| {task.task_id} | {task.title} | {task.priority} | {', '.join(task.dependencies) or 'None'} | {', '.join(task.related_requirements) or 'None'} |" for task in plan.tasks) or "| - | - | - | - | - |"
    files = [
        ("design/README.md", f"""# Planning And Design - {state.domain}

## Architecture Summary
{plan.project_overview}

## Selected Architecture
{design.architecture_style}

## Components
| ID | Name | Responsibility | Technologies |
|---|---|---|---|
{components}

## Data Flow
{design.data_flow}

## Technology Stack
{_items(design.technology_stack)}

## Implementation Phases
{_items(plan.implementation_phases)}

## Dependencies And Tasks
| Task | Title | Priority | Dependencies | Requirements |
|---|---|---|---|---|
{tasks}

## Project Structure
The Coding Agent must create source files according to this design and task plan.

## Scale Considerations
{_items([d.reason for d in design.architecture_decisions] or plan.risks_and_mitigations)}

## Diagram References
See `design/diagrams/` for PNG diagrams and `design/diagram_source/` for validated JSON sources.
""", "DESIGN"),
        ("design/architecture.md", f"""# Architecture

## Selected Architecture
{design.architecture_style}

## Components And Responsibilities
| ID | Component | Responsibility | Dependencies |
|---|---|---|---|
{chr(10).join(f'| {c.component_id} | {c.name} | {c.responsibility} | {", ".join(c.dependencies) or "None"} |' for c in design.components)}

## Communication And Data Flow
{design.data_flow}

## Deployment Structure
Deployment details are finalized by the Delivery Agent. This phase defines the logical structure.

## Architecture Diagram
See `diagrams/architecture.png`.
""", "DESIGN"),
        ("design/implementation_plan.md", f"""# Implementation Plan

## Milestones
{_items(plan.milestones)}

## Implementation Strategy
{plan.implementation_strategy}

## Ordered Tasks
| Task | Title | Description | Dependencies | Requirement Trace |
|---|---|---|---|---|
{chr(10).join(f'| {t.task_id} | {t.title} | {_cell(t.description)} | {", ".join(t.dependencies) or "None"} | {", ".join(t.related_requirements) or "None"} |' for t in plan.tasks)}
""", "DESIGN"),
        ("design/api_design.md", f"""# API Design

| Method | Path | Purpose | Request Schema | Response Schema | Auth |
|---|---|---|---|---|---|
{apis}
""", "DESIGN"),
        ("design/database_design.md", f"""# Database Design

{db}
""", "DESIGN"),
        ("design/technology_stack.md", f"""# Technology Stack

## Selected Technologies
{_items(design.technology_stack)}

## Security Considerations
{_items(design.security_considerations)}

## Rationale
Technologies are selected from the analyzed requirements, the project scale, and the planned architecture.
""", "DESIGN"),
    ]
    return [write_text_artifact(state, path, content, kind, "PlanningAgent") for path, content, kind in files]

def generate_design_document(project_id: str, domain: str, plan: ProjectPlan) -> str:
    project_name = slugify(domain) or slugify(project_id)
    doc_dir = f"generated_projects/{project_name}/design"
    os.makedirs(doc_dir, exist_ok=True)
    
    path = f"{doc_dir}/system_design.md"
    
    lines = [
        "# System Design\n",
        "## 1. Project Overview",
        f"{plan.project_overview}\n",
        "## 2. Architecture Style",
        f"{plan.system_design.architecture_style}\n",
        "## 3. System Architecture",
        f"{plan.system_design.data_flow}\n",
        "## 4. Architecture Components"
    ]
    
    for comp in plan.system_design.components:
        lines.append(f"### {comp.name} ({comp.component_id})")
        lines.append(f"- **Responsibility**: {comp.responsibility}")
        lines.append(f"- **Technologies**: {', '.join(comp.technologies)}")
        lines.append(f"- **Dependencies**: {', '.join(comp.dependencies)}\n")
        
    lines.append("## 5. Data Flow")
    lines.append(f"{plan.system_design.data_flow}\n")
    
    lines.append("## 6. Database Design")
    for db in plan.system_design.database_schema:
        lines.append(f"### Entity: {db.name}")
        lines.append(f"**Description**: {db.description}")
        lines.append("**Fields**: " + ", ".join(db.fields))
        lines.append("**Relationships**: " + ", ".join(db.relationships) + "\n")
        
    lines.append("## 7. API Design")
    for api in plan.system_design.api_endpoints:
        lines.append(f"### {api.method} {api.path}")
        lines.append(f"- **Purpose**: {api.purpose}")
        lines.append(f"- **Request**: {api.request_schema}")
        lines.append(f"- **Response**: {api.response_schema}")
        lines.append(f"- **Auth Required**: {api.authentication_required}\n")
        
    lines.append("## 8. Security Considerations")
    lines.append("\n".join(f"- {s}" for s in plan.system_design.security_considerations) + "\n")
    
    lines.append("## 9. Technology Stack")
    lines.append("\n".join(f"- {t}" for t in plan.system_design.technology_stack) + "\n")
    
    lines.append("## 10. Task Dependency Graph")
    for t in plan.tasks:
        deps = ", ".join(t.dependencies) if t.dependencies else "None"
        lines.append(f"- **{t.task_id}**: {t.title} (Depends on: {deps})")
    lines.append("")
    
    lines.append("## 11. Requirement-to-Task Traceability")
    for t in plan.tasks:
        reqs = ", ".join(t.related_requirements) if t.related_requirements else "None"
        lines.append(f"- **{t.task_id}**: {t.title} -> Requirements: {reqs}")
    lines.append("")
        
    lines.append("## 12. Implementation Strategy")
    lines.append(f"{plan.implementation_strategy}\n")
    
    content = "\n".join(lines)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
        
    arch_path = f"{doc_dir}/architecture.md"
    arch_lines = [
        "# Architecture\n",
        "## Architecture Style",
        f"{plan.system_design.architecture_style}\n",
        "## Components"
    ]
    for comp in plan.system_design.components:
        arch_lines.append(f"### {comp.name}")
        arch_lines.append(f"{comp.responsibility}\n")
    
    with open(arch_path, "w", encoding="utf-8") as f:
        f.write("\n".join(arch_lines))
        
    return path
