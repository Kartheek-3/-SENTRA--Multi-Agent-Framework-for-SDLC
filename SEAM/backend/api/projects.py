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

class CreateProjectRequest(BaseModel):
    project_name: str
    requirement: str
    scale: str = "AUTO"
    technology_preferences: List[str] = []
    workspace_location: Optional[str] = None
    github_repository: Optional[str] = None
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
    if request.github_repository:
        metadata_parts.append(f"GitHub repository: {request.github_repository}")
    if request.additional_constraints:
        metadata_parts.append(f"Additional constraints: {request.additional_constraints}")
    if metadata_parts:
        requirement = requirement.rstrip() + "\n\n" + "\n".join(metadata_parts)

    state = ProjectState(
        project_id=project_id,
        user_requirement=requirement,
        domain=request.project_name
    )
    
    projects_db[project_id] = state

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
    return {
        "projects": [
            {
                "project_id": state.project_id,
                "project_name": state.project_name,
                "domain": state.domain,
                "workflow_status": state.workflow_status,
                "current_agent": state.current_agent,
            }
            for state in projects_db.values()
        ]
    }

@router.get("/{project_id}/status")
def get_project_status(project_id: str):
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
        
    state = projects_db[project_id]
    
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
        "delivery_result": delivery,
        "agent_status": agent_status,
    }

@router.get("/{project_id}/repositories")
def get_project_repositories(project_id: str):
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
        
    state = projects_db[project_id]
    if not state.github_selection:
        return {"has_selection": False, "selection": None}
        
    return {
        "has_selection": True,
        "selection": state.github_selection.model_dump()
    }

@router.get("/{project_id}/diagrams")
def get_diagrams(project_id: str):
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
        
    state = projects_db[project_id]
    diagrams_dir = os.path.abspath(os.path.join("generated_projects", state.project_name, "design", "diagrams"))
    
    if not os.path.exists(diagrams_dir):
        return {"diagrams": []}
        
    diagrams = []
    for f in os.listdir(diagrams_dir):
        if f.endswith(".png"):
            diagrams.append(f.replace(".png", ""))
            
    return {"diagrams": diagrams}

@router.get("/{project_id}/diagrams/{diagram_type}")
def get_diagram(project_id: str, diagram_type: str):
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
        
    state = projects_db[project_id]
    diagrams_dir = os.path.abspath(os.path.join("generated_projects", state.project_name, "design", "diagram_source"))
    diagram_path = os.path.abspath(os.path.join(diagrams_dir, f"{slugify(diagram_type)}.json"))

    if os.path.commonpath([diagrams_dir, diagram_path]) != diagrams_dir:
        raise HTTPException(status_code=403, detail="Unsafe diagram path")
    
    if not os.path.exists(diagram_path):
        raise HTTPException(status_code=404, detail="Diagram not found")
        
    with open(diagram_path, "r", encoding="utf-8") as f:
        return json.load(f)

@router.post("/{project_id}/diagrams/{diagram_type}/regenerate")
def regenerate_diagram(project_id: str, diagram_type: str):
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
        
    state = projects_db[project_id]
    if not state.structured_requirements or not state.project_plan:
        raise HTTPException(status_code=400, detail="Cannot regenerate before planning is complete")
        
    from backend.tools.artifact_pipeline import write_bytes_artifact, write_text_artifact
    from backend.tools.diagram_generator import generate_diagram_with_llm, render_diagram_png
    try:
        res = generate_diagram_with_llm(diagram_type, state.structured_requirements, state.project_plan)
        name = slugify(diagram_type)
        source_path = f"design/diagram_source/{name}.json"
        image_path = f"design/diagrams/{name}.png"
        write_text_artifact(state, source_path, res.model_dump_json(indent=2), "DIAGRAM", "PlanningAgent", diagram_type=diagram_type)
        write_bytes_artifact(state, image_path, render_diagram_png(res, f"{state.project_name} {diagram_type}"), "DIAGRAM", "PlanningAgent", diagram_type=diagram_type)
        return {"status": "regenerated", "type": diagram_type, "source_path": source_path, "image_path": image_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
