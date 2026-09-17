from concurrent.futures import TimeoutError
from threading import Thread
from fastapi import APIRouter, HTTPException
from backend.api.projects import projects_db
from backend.graph.workflow import create_workflow
from backend.concurrency import workflow_executor
from backend.config import WORKFLOW_TIMEOUT_SECONDS
from backend.performance import performance_recorder, timed_call

router = APIRouter(prefix="/api/projects", tags=["workflow"])

workflow = create_workflow()

from backend.events import event_bus

running_jobs = {}

def run_workflow_background(project_id: str):
    if project_id not in projects_db:
        return
        
    state = projects_db[project_id]
    state.workflow_status = "running"
    event_bus.emit_sync("WORKFLOW_STARTED", {"project_id": project_id})
    performance_recorder.record("workflow_started", project_id=project_id)
    
    try:
        # execute graph
        final_state = timed_call(
            "workflow_execution",
            lambda: workflow.invoke(state.model_dump()),
            project_id=project_id,
            timeout_seconds=WORKFLOW_TIMEOUT_SECONDS,
        )
        if projects_db[project_id].workflow_status == "failed" and any("timed out" in error for error in projects_db[project_id].errors):
            return
        
        # update DB with final state
        # In memory we just assign it back, but state is dict returned by langgraph
        # so we need to merge or replace it properly
        for k, v in final_state.items():
            setattr(projects_db[project_id], k, v)
        performance_recorder.record("workflow_completed", project_id=project_id)
        event_bus.emit_sync("WORKFLOW_COMPLETED", {"project_id": project_id})
            
    except Exception as e:
        projects_db[project_id].workflow_status = "failed"
        projects_db[project_id].errors.append(f"Workflow crashed: {str(e)}")
        performance_recorder.record("workflow_failed", project_id=project_id, error=str(e))
        event_bus.emit_sync("WORKFLOW_FAILED", {"project_id": project_id, "error": str(e)})
    finally:
        running_jobs.pop(project_id, None)


def monitor_workflow(project_id: str):
    future = running_jobs.get(project_id)
    if not future:
        return
    try:
        future.result(timeout=WORKFLOW_TIMEOUT_SECONDS)
    except TimeoutError:
        state = projects_db.get(project_id)
        if state:
            state.workflow_status = "failed"
            state.errors.append(f"Workflow timed out after {WORKFLOW_TIMEOUT_SECONDS} seconds.")
        performance_recorder.record("workflow_timeout", project_id=project_id, timeout_seconds=WORKFLOW_TIMEOUT_SECONDS)
        event_bus.emit_sync("WORKFLOW_FAILED", {"project_id": project_id, "error": f"Workflow timed out after {WORKFLOW_TIMEOUT_SECONDS} seconds."})
    finally:
        running_jobs.pop(project_id, None)

@router.post("/{project_id}/run")
def start_workflow(project_id: str):
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")
        
    state = projects_db[project_id]
    
    if state.workflow_status == "running":
        return {"project_id": project_id, "status": "already running"}
        
    # Start it asynchronously in a bounded local executor so the FastAPI request returns immediately.
    future = workflow_executor.submit(run_workflow_background, project_id)
    running_jobs[project_id] = future
    Thread(target=monitor_workflow, args=(project_id,), daemon=True).start()
    
    return {
        "project_id": project_id,
        "status": "running"
    }

@router.post("/{project_id}/stop")
def stop_workflow(project_id: str):
    if project_id not in projects_db:
        raise HTTPException(status_code=404, detail="Project not found")

    state = projects_db[project_id]
    if state.workflow_status == "running":
        return {
            "project_id": project_id,
            "status": "NOT_AVAILABLE",
            "detail": "This backend executes the current workflow in-process and does not expose safe cancellation yet."
        }

    state.workflow_status = "stopped"
    event_bus.emit_sync("WORKFLOW_STOPPED", {"project_id": project_id})
    return {
        "project_id": project_id,
        "status": "stopped"
    }
