import os
import json
import uuid
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.models.state import ProjectState
from backend.utils import slugify

router = APIRouter(prefix="/api/projects", tags=["projects"])

# Global DB mock
projects_db: Dict[str, ProjectState] = {}

def get_project_state(project_id: str) -> ProjectState:
    if project_id not in projects_db:
        try:
            from backend.database import db_engine
            stored = db_engine.get_project(project_id)
            if stored and stored.get("state"):
                projects_db[project_id] = ProjectState(**stored["state"])
        except Exception:
            pass
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
    return projects_db[project_id]

def save_project_state(state: ProjectState) -> None:
    projects_db[state.project_id] = state
    try:
        from backend.database import db_engine
        db_engine.save_project(
            project_id=state.project_id,
            project_name=state.project_name,
            domain=state.domain or state.project_name,
            user_requirement=state.user_requirement,
            state_dict=state.model_dump(),
            workflow_status=state.workflow_status
        )
    except Exception:
        pass

class CreateProjectRequest(BaseModel):
    project_name: str
    requirement: str
    scale: str = "AUTO"
    technology_preferences: List[str] = []
    technology_stack: Optional[Dict[str, Any]] = None
    workspace_location: Optional[str] = None
    github_repository: Optional[str] = None
    github_branch: Optional[str] = "main"
    workflow_type: str = "new_project"  # "new_project" or "enhance_existing"
    additional_constraints: Optional[str] = None

@router.post("")
def create_project(request: CreateProjectRequest):
    project_id = str(uuid.uuid4())
    requirement = request.requirement
    metadata_parts = []
    if request.scale and request.scale != "AUTO":
        metadata_parts.append(f"Requested scale: {request.scale}")
    if request.technology_preferences:
        metadata_parts.append(f"Technology preferences: {', '.join(request.technology_preferences)}")
    if request.technology_stack:
        active_stack = [f"{k}: {v}" for k, v in request.technology_stack.items() if v and v != "None"]
        if active_stack:
            metadata_parts.append(f"Configured Technology Stack: {', '.join(active_stack)}")
    if request.github_repository:
        metadata_parts.append(f"GitHub repository: {request.github_repository}")
    if request.additional_constraints:
        metadata_parts.append(f"Additional constraints: {request.additional_constraints}")
    if metadata_parts:
        requirement = requirement.rstrip() + "\n\n" + "\n".join(metadata_parts)

    state = ProjectState(
        project_id=project_id,
        user_requirement=requirement,
        domain=request.project_name,
        workflow_type=request.workflow_type or "new_project",
        repo_url=request.github_repository,
        repo_branch=request.github_branch or "main",
        technology_stack=request.technology_stack or {},
    )
    
    if request.technology_stack:
        fw = request.technology_stack.get("frontend")
        if fw and fw != "None":
            state.frontend_capabilities = {
                "framework": fw,
                "language": request.technology_stack.get("language", "TypeScript"),
                "build_system": request.technology_stack.get("build_tool", "Vite"),
                "styling": request.technology_stack.get("styling", "TailwindCSS"),
                "auth": request.technology_stack.get("auth", "JWT"),
            }
    
    projects_db[project_id] = state
    try:
        from backend.database import db_engine
        db_engine.save_project(
            project_id=project_id,
            project_name=request.project_name,
            domain=request.project_name,
            user_requirement=requirement,
            state_dict=state.model_dump(),
            workflow_status=state.workflow_status
        )
    except Exception:
        pass

    from backend.foundation.models import AgentStatus, ManagedAgent, ManagedTask, TaskStatus
    from backend.foundation.services import agent_manager, task_manager

    agent_task_pairs = [
        ("AnalysisAgent", "Analysis", "Analyze requirements and domain constraints."),
        ("PlanningAgent", "Architecture", "Create project plan and system design."),
        ("SupervisorAgent", "Supervisor", "Coordinate task execution and dependencies."),
        ("CodingAgent", "Coding", "Generate source files from approved tasks."),
        ("QAAgent", "Testing", "Validate generated project output."),
        ("DeliveryAgent", "Delivery", "Prepare delivery summary and final artifacts."),
    ]
    for priority, (agent_type, title, description) in enumerate(agent_task_pairs):
        task = task_manager.create(ManagedTask(
            project_id=project_id,
            title=title,
            description=description,
            status=TaskStatus.READY if priority == 0 else TaskStatus.PENDING,
            priority=priority,
        ))
        agent_manager.create(ManagedAgent(
            project_id=project_id,
            conversation_id=project_id,
            agent_type=agent_type,
            task_id=task.task_id,
            status=AgentStatus.QUEUED,
        ))
    
    from backend.events import event_bus
    event_bus.emit_sync("PROJECT_CREATED", {"project_id": project_id, "project_name": request.project_name})
    
    return {
        "project_id": project_id,
        "project_name": request.project_name,
        "status": "created"
    }

@router.get("")
def list_projects():
    projects_map = {
        state.project_id: {
            "project_id": state.project_id,
            "project_name": state.project_name,
            "domain": state.domain,
            "workflow_status": state.workflow_status,
            "current_agent": state.current_agent,
        }
        for state in projects_db.values()
    }
    try:
        from backend.database import db_engine
        for row in db_engine.list_projects():
            pid = row["project_id"]
            if pid not in projects_map:
                projects_map[pid] = {
                    "project_id": pid,
                    "project_name": row.get("project_name") or pid,
                    "domain": row.get("domain") or pid,
                    "workflow_status": row.get("workflow_status") or "pending",
                    "current_agent": None,
                }
    except Exception:
        pass
    return {"projects": list(projects_map.values())}

@router.get("/{project_id}/status")
def get_project_status(project_id: str):
    state = get_project_state(project_id)
    
    analysis = state.structured_requirements.model_dump() if state.structured_requirements else None
    plan = state.project_plan.model_dump() if state.project_plan else None
    design_artifacts = state.design_artifacts.model_dump() if state.design_artifacts else None
    delivery = state.delivery_result
    tasks = {task_id: task.model_dump() for task_id, task in state.tasks.items()}

    scale_assessment = None
    if state.structured_requirements and state.structured_requirements.scale_assessment:
        scale_assessment = state.structured_requirements.scale_assessment.model_dump()

    agent_names = [
        "AnalysisAgent",
        "PlanningAgent",
        "SupervisorAgent",
        "CodingAgent",
        "QAAgent",
        "DeliveryAgent",
    ]
    agent_status = {}
    for agent in agent_names:
        records = [r for r in state.execution_history if r.get("agent") == agent or r.get("agent") == agent.replace("Agent", "")]
        agent_status[agent] = {
            "status": "running" if state.current_agent == agent else ("complete" if records else "not_available"),
            "history": records[-5:],
        }

    return {
        "project_id": state.project_id,
        "project_name": state.project_name,
        "domain": state.domain,
        "domain_identification": state.domain_identification.model_dump() if state.domain_identification else None,
        "domain_context": state.domain_context.model_dump() if state.domain_context else None,
        "domain_traceability": state.domain_traceability.model_dump() if state.domain_traceability else None,
        "user_requirement": state.user_requirement,
        "workflow_status": state.workflow_status,
        "current_agent": state.current_agent,
        "current_task": state.current_task,
        "completed_tasks": state.completed_tasks,
        "pending_tasks": [t for t in state.tasks if state.tasks[t].status == "pending"],
        "failed_tasks": state.failed_tasks,
        "retry_count": state.retry_count,
        "latest_qa_status": state.latest_qa_status,
        "errors": state.errors,
        "analysis": analysis,
        "scale_assessment": scale_assessment,
        "project_plan": plan,
        "system_design": state.system_design.model_dump() if state.system_design else None,
        "design_artifacts": design_artifacts,
        "tasks": tasks,
        "execution_history": state.execution_history[-100:],
        "github_selection": state.github_selection.model_dump() if state.github_selection else None,
        "github_context": state.github_context,
        "github_status": state.github_status,
        "external_integrations": state.external_integrations[-50:],
        "n8n_integration_status": state.n8n_integration_status,
        "frontend_capabilities": state.frontend_capabilities,
        "frontend_architecture_plan": state.frontend_architecture_plan.model_dump() if state.frontend_architecture_plan else None,
        "frontend_execution": state.frontend_execution,
        "full_stack_contract": state.full_stack_contract.model_dump() if state.full_stack_contract else None,
        "contract_issues": [issue.model_dump() for issue in state.contract_issues],
        "runtime_base_url": state.runtime_base_url,
        "runtime_contract_results": [result.model_dump() for result in state.runtime_contract_results],
        "runtime_profile": state.runtime_profile.model_dump() if state.runtime_profile else None,
        "runtime_processes": [process.model_dump() for process in state.runtime_processes],
        "runtime_status": state.runtime_status,
        "e2e_scenarios": [scenario.model_dump() for scenario in state.e2e_scenarios],
        "e2e_results": [result.model_dump() for result in state.e2e_results],
        "defect_locations": [location.model_dump() for location in state.defect_locations],
        "repair_plans": [plan.model_dump() for plan in state.repair_plans],
        "repair_results": [result.model_dump() for result in state.repair_results],
        "targeted_verifications": [verification.model_dump() for verification in state.targeted_verifications],
        "regression_results": [result.model_dump() for result in state.regression_results],
        "release_readiness": state.release_readiness.model_dump() if state.release_readiness else None,
        "deployment_profile": state.deployment_profile.model_dump() if state.deployment_profile else None,
        "deployment_artifacts": [artifact.model_dump() for artifact in state.deployment_artifacts],
        "deployment_result": state.deployment_result.model_dump() if state.deployment_result else None,
        "post_deployment_verification": state.post_deployment_verification.model_dump() if state.post_deployment_verification else None,
        "rollback_info": state.rollback_info.model_dump() if state.rollback_info else None,
        "evaluation_summary": state.evaluation_summary.model_dump() if state.evaluation_summary else None,
        "experiment_summary": state.experiment_summary,
        "delivery_result": delivery,
        "agent_status": agent_status,
        "technology_stack": state.technology_stack,
    }

@router.get("/{project_id}/evaluation")
def get_project_evaluation(project_id: str):
    state = get_project_state(project_id)
    if not state.evaluation_summary:
        from backend.evaluation import EvaluationEngine
        EvaluationEngine().evaluate(state, scenario_id=state.domain or state.project_id)
    return {
        "project_id": state.project_id,
        "evaluation_summary": state.evaluation_summary.model_dump() if state.evaluation_summary else None,
    }

@router.get("/{project_id}/repositories")
def get_project_repositories(project_id: str):
    state = get_project_state(project_id)
    if not state.github_selection:
        return {"has_selection": False, "selection": None}
        
    return {
        "has_selection": True,
        "selection": state.github_selection.model_dump()
    }

@router.get("/{project_id}/diagrams")
def get_diagrams(project_id: str):
    state = get_project_state(project_id)
    diagrams_dir = os.path.abspath(os.path.join("generated_projects", state.project_name, "design", "diagrams"))
    source_dir = os.path.abspath(os.path.join("generated_projects", state.project_name, "design", "diagram_source"))
    
    from backend.tools.diagram_templates import normalize_diagram_identifier

    diagrams = set()
    raw_files = []
    if os.path.exists(diagrams_dir):
        for f in os.listdir(diagrams_dir):
            if f.endswith(".png"):
                raw_files.append(f.replace(".png", ""))

    if os.path.exists(source_dir):
        for f in os.listdir(source_dir):
            if f.endswith(".json"):
                raw_files.append(f.replace(".json", ""))

    for stem in raw_files:
        norm = normalize_diagram_identifier(stem)
        if norm:
            diagrams.add(norm["id"])
            diagrams.add(norm["canonical_name"])
        else:
            diagrams.add(stem)
            
    return {"diagrams": sorted(list(diagrams))}

@router.get("/{project_id}/diagrams/{diagram_type}")
def get_diagram(project_id: str, diagram_type: str):
    state = get_project_state(project_id)
    diagrams_dir = os.path.abspath(os.path.join("generated_projects", state.project_name, "design", "diagram_source"))
    if not os.path.exists(diagrams_dir):
        raise HTTPException(status_code=404, detail=f"Diagram '{diagram_type}' not found (directory missing)")

    from backend.tools.diagram_templates import normalize_diagram_identifier
    from backend.tools.diagram_adapter import adapt_to_react_flow
    from backend.tools.diagram_exporter import export_diagram_to_mermaid

    norm = normalize_diagram_identifier(diagram_type)
    if not norm:
        raise HTTPException(status_code=404, detail=f"Diagram '{diagram_type}' not found")

    candidate_names = []
    candidate_names.append(norm["filename"])
    candidate_names.append(f"{norm['id']}.json")
    for alias in norm["aliases"]:
        candidate_names.append(f"{alias}.json")
    candidate_names.append(f"{slugify(diagram_type)}.json")
    candidate_names.append(f"{diagram_type}.json")

    chosen_path = None
    for cand in candidate_names:
        p = os.path.abspath(os.path.join(diagrams_dir, cand))
        if os.path.commonpath([diagrams_dir, p]) != diagrams_dir:
            raise HTTPException(status_code=403, detail="Unsafe diagram path")
        if os.path.exists(p):
            chosen_path = p
            break

    if not chosen_path:
        raise HTTPException(status_code=404, detail=f"Diagram '{diagram_type}' not found")
        
    with open(chosen_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    data["canonical_id"] = norm["id"]
    data["diagram_type"] = norm["label"]

    # Ensure nodes and edges exist in response
    adapted_nodes, adapted_edges = adapt_to_react_flow(data, norm["id"])
    data["nodes"] = [n.model_dump() for n in adapted_nodes]
    data["edges"] = [e.model_dump() for e in adapted_edges]

    if "mermaid" not in data or not data["mermaid"]:
        data["mermaid"] = export_diagram_to_mermaid(data)

    return data

@router.post("/{project_id}/diagrams/{diagram_type}/regenerate")
def regenerate_diagram(project_id: str, diagram_type: str):
    state = get_project_state(project_id)
    if not state.structured_requirements or not state.project_plan:
        raise HTTPException(status_code=400, detail="Cannot regenerate before planning is complete")
        
    from backend.tools.diagram_templates import normalize_diagram_identifier
    from backend.tools.diagram_generator import generate_diagram_with_llm, render_diagram_png
    from backend.tools.diagram_exporter import export_diagram_to_mermaid
    from backend.tools.artifact_pipeline import write_bytes_artifact, write_text_artifact

    norm = normalize_diagram_identifier(diagram_type)
    if not norm:
        raise HTTPException(status_code=400, detail=f"Invalid diagram identifier '{diagram_type}'")

    try:
        label = norm["label"]
        cid = norm["id"]
        res = generate_diagram_with_llm(cid, state.structured_requirements, state.project_plan)

        payload = res.model_dump()
        payload["mermaid"] = export_diagram_to_mermaid(res)
        payload["canonical_id"] = cid
        payload["diagram_type"] = label
        json_content = json.dumps(payload, indent=2)

        # Write canonical JSON artifact
        canonical_source_path = f"design/diagram_source/{norm['filename']}"
        write_text_artifact(state, canonical_source_path, json_content, "DIAGRAM", "PlanningAgent", diagram_type=label, canonical_id=cid)

        # Write alias JSON artifact
        alias_source_path = f"design/diagram_source/{cid}.json"
        if alias_source_path != canonical_source_path:
            write_text_artifact(state, alias_source_path, json_content, "DIAGRAM", "PlanningAgent", diagram_type=label, canonical_id=cid)

        # Render PNG visual artifact
        png = render_diagram_png(res, f"{state.project_name} {label}")
        canonical_image_path = f"design/diagrams/{norm['png_filename']}"
        write_bytes_artifact(state, canonical_image_path, png, "DIAGRAM", "PlanningAgent", diagram_type=label, canonical_id=cid)

        alias_image_path = f"design/diagrams/{cid}.png"
        if alias_image_path != canonical_image_path:
            write_bytes_artifact(state, alias_image_path, png, "DIAGRAM", "PlanningAgent", diagram_type=label, canonical_id=cid)

        return {
            "status": "regenerated",
            "type": label,
            "canonical_id": cid,
            "source_path": canonical_source_path,
            "image_path": canonical_image_path,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Regeneration failed: {str(e)}")


@router.post("/{project_id}/approve_enhancement")
def approve_enhancement(project_id: str):
    state = get_project_state(project_id)
    state.enhancement_approved = True
    state.approval_status = "approved"
    if state.workflow_status == "waiting_for_approval":
        state.workflow_status = "running"
    save_project_state(state)
    from backend.events import event_bus
    event_bus.emit_sync("ENHANCEMENT_PLAN_APPROVED", {
        "project_id": project_id,
        "status": "approved",
    })
    return {"status": "approved", "project_id": project_id}


@router.post("/{project_id}/reject_enhancement")
def reject_enhancement(project_id: str, reason: Optional[str] = None):
    state = get_project_state(project_id)
    state.enhancement_approved = False
    state.approval_status = "rejected"
    state.workflow_status = "rejected"
    save_project_state(state)
    from backend.events import event_bus
    event_bus.emit_sync("ENHANCEMENT_PLAN_REJECTED", {
        "project_id": project_id,
        "reason": reason or "User rejected the enhancement plan",
    })
    return {"status": "rejected", "project_id": project_id}


@router.get("/{project_id}/understanding")
def get_project_understanding(project_id: str):
    state = get_project_state(project_id)
    return {
        "project_id": project_id,
        "understanding": state.project_understanding,
        "profile": state.repo_profile,
    }


@router.get("/{project_id}/enhancement_plan")
def get_enhancement_plan(project_id: str):
    state = get_project_state(project_id)
    return {
        "project_id": project_id,
        "enhancement_plan": state.enhancement_plan,
        "approved": state.enhancement_approved,
        "approval_status": state.approval_status,
    }


@router.get("/{project_id}/diff")
def get_enhancement_diff(project_id: str):
    state = get_project_state(project_id)
    return {
        "project_id": project_id,
        "diff": state.diff_summary or "",
        "targeted_changes": state.targeted_changes or [],
    }
