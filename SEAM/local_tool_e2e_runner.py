import json
import os
import subprocess
import time

os.environ["SEAM_LLM_MODEL"] = "qwen2.5-coder:7b"
os.environ["SEAM_ANALYSIS_MODEL"] = "qwen2.5-coder:7b"
os.environ["SEAM_PLANNING_MODEL"] = "qwen2.5-coder:7b"
os.environ["SEAM_CODING_MODEL"] = "qwen2.5-coder:7b"
os.environ["SEAM_QA_MODEL"] = "qwen2.5-coder:7b"
os.environ["SEAM_MODEL_REQUEST_TIMEOUT"] = "240"

from backend.api.projects import CreateProjectRequest, create_project, projects_db
from backend.api.workflow import run_workflow_background
from backend.foundation.services import artifact_registry, event_store


REQ = """Build a SMALL Expense Tracker.

Technology:
- React frontend
- FastAPI backend
- SQLite database

Features:
- Add expense
- View expenses
- Edit expense
- Delete expense
- id
- title
- amount
- category
- date
- validation
- REST APIs
- error handling
- tests
- README

Do not introduce unnecessary microservices.
"""


def main():
    started = time.time()
    request = CreateProjectRequest(
        project_name="expense_tracker_tool_e2e",
        requirement=REQ,
        scale="SMALL",
        technology_preferences=["React", "FastAPI", "SQLite"],
    )
    created = create_project(request)
    project_id = created["project_id"]
    state = projects_db[project_id]
    project_root = os.path.abspath(os.path.join("generated_projects", state.project_name))
    os.makedirs(project_root, exist_ok=True)
    subprocess.run(["git", "init"], cwd=project_root, capture_output=True, text=True, timeout=30)
    subprocess.run(["git", "config", "user.email", "seam.local@example.com"], cwd=project_root, capture_output=True, text=True, timeout=30)
    subprocess.run(["git", "config", "user.name", "SEAM Local Validation"], cwd=project_root, capture_output=True, text=True, timeout=30)

    run_workflow_background(project_id)
    final_state = projects_db[project_id]
    events = event_store.list(project_id=project_id)
    tool_events = [event for event in events if event.event.startswith("TOOL_")]
    agent_events = [event for event in events if event.event.startswith("AGENT_")]
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=project_root, capture_output=True, text=True, timeout=30)
    branch = subprocess.run(["git", "branch", "--show-current"], cwd=project_root, capture_output=True, text=True, timeout=30)
    files = []
    for root, _, names in os.walk(project_root):
        if ".git" in root.split(os.sep):
            continue
        for name in names:
            files.append(os.path.relpath(os.path.join(root, name), project_root).replace("\\", "/"))

    summary = {
        "project_id": project_id,
        "project_name": final_state.project_name,
        "workflow_status": final_state.workflow_status,
        "current_agent": final_state.current_agent,
        "errors": final_state.errors,
        "completed_tasks": final_state.completed_tasks,
        "failed_tasks": final_state.failed_tasks,
        "retry_count": final_state.retry_count,
        "latest_qa_status": final_state.latest_qa_status,
        "delivery_result": final_state.delivery_result,
        "tool_events": [event.model_dump() for event in tool_events],
        "agent_events": [event.model_dump() for event in agent_events],
        "execution_history": final_state.execution_history,
        "artifact_count": len(artifact_registry.list(project_id)),
        "artifacts": [artifact.model_dump() for artifact in artifact_registry.list(project_id)],
        "files": sorted(files),
        "git_branch": branch.stdout.strip(),
        "git_commit": commit.stdout.strip() if commit.returncode == 0 else "",
        "git_commit_error": commit.stderr.strip() if commit.returncode != 0 else "",
        "duration_seconds": round(time.time() - started, 2),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
