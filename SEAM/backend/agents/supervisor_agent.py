from backend.models.state import ProjectState
from backend.tools.artifact_pipeline import write_text_artifact

class SupervisorAgent:
    def process(self, state: ProjectState) -> ProjectState:
        # If there are global errors that stop the workflow
        if state.errors and len(state.errors) > 5:
            state.workflow_status = "failed"
            state.current_agent = "END"
            self._write_supervisor_artifacts(state, "Workflow failed due to accumulated errors.")
            return state

        # If requirements changed, trigger SCALE_CHANGE_DETECTED
        if getattr(state, "scale_changed", False):
            state.scale_changed = False
            state.execution_history.append({"agent": "Supervisor", "event": "SCALE_CHANGE_DETECTED", "action": "Re-routing to AnalysisAgent"})
            # Reset plan to force re-planning after analysis
            state.project_plan = None
            state.current_agent = "AnalysisAgent"
            self._write_supervisor_artifacts(state, "Scale changed; rerouting to AnalysisAgent.")
            return state

        # 1. Requirements Analysis
        if not state.structured_requirements:
            state.current_agent = "AnalysisAgent"
            self._write_supervisor_artifacts(state, "Analysis required before planning.")
            return state
            
        # 2. Planning
        if not state.project_plan:
            state.current_agent = "PlanningAgent"
            self._write_supervisor_artifacts(state, "Planning required before coding.")
            return state
            
        # 3. Tasks Execution (Coding <-> QA)
        pending_tasks = [t for t_id, t in state.tasks.items() if t.status == "pending"]
        in_progress_tasks = [t for t_id, t in state.tasks.items() if t.status == "in_progress"]
        failed_tasks = [t for t_id, t in state.tasks.items() if t.status == "failed"]
        completed_without_qa = [
            t for t_id, t in state.tasks.items()
            if t.status == "completed" and not ((t.result or {}).get("qa_result") or {}).get("passed")
        ]
        
        scale_obj = getattr(state.structured_requirements, "scale_assessment", None)
        project_scale = scale_obj.scale_level.value if scale_obj else "UNKNOWN"
        
        # If there is a task in progress, check if it needs QA or if it's currently coding
        if in_progress_tasks:
            # simple single-task execution model
            current_task = in_progress_tasks[0]
            state.current_task = current_task.task_id
            
            # If it has a qa_result but it's failed, route to Coding for rework
            qa_res = current_task.result.get("qa_result") if current_task.result else None
            
            if qa_res is None:
                # Need to QA after Coding
                state.current_agent = "QAAgent"
            else:
                # Should not reach here if in progress unless rework or something else
                state.current_agent = "CodingAgent"
            self._write_supervisor_artifacts(state, "Routing in-progress task to next agent.")
            return state
            
        if pending_tasks:
            # Scale-aware parallelization logic
            max_parallel = 1
            if project_scale in ["MEDIUM", "LARGE", "ENTERPRISE"]:
                max_parallel = 3 # In a full parallel graph, we would dispatch multiple here.
                
            next_task = pending_tasks[0]
            next_task.status = "in_progress"
            state.current_task = next_task.task_id
            state.current_agent = "CodingAgent"
            self._write_supervisor_artifacts(state, f"Dispatching task {next_task.task_id} to CodingAgent.")
            return state
            
        if failed_tasks:
            # Rework failed tasks
            if state.retry_count >= 3:
                state.workflow_status = "failed"
                state.current_agent = "END"
                self._write_supervisor_artifacts(state, "Retry limit reached; workflow failed.")
                return state
                
            state.retry_count += 1
            retry_task = failed_tasks[0]
            retry_task.status = "in_progress"
            state.current_task = retry_task.task_id
            state.current_agent = "CodingAgent"
            self._write_supervisor_artifacts(state, f"Retrying failed task {retry_task.task_id}.")
            return state

        if completed_without_qa:
            qa_task = completed_without_qa[0]
            state.current_task = qa_task.task_id
            state.current_agent = "QAAgent"
            self._write_supervisor_artifacts(state, f"Routing completed task {qa_task.task_id} to QAAgent.")
            return state
            
        # 4. Delivery
        if not getattr(state, "delivery_result", None):
            state.current_agent = "DeliveryAgent"
            self._write_supervisor_artifacts(state, "All tasks complete; routing to DeliveryAgent.")
            return state
            
        # 5. End
        state.workflow_status = "completed"
        state.current_agent = "END"
        self._write_supervisor_artifacts(state, "Workflow completed.")
        return state

    def _write_supervisor_artifacts(self, state: ProjectState, decision: str):
        completed_agents = [item.get("agent") for item in state.execution_history if item.get("status") == "success"]
        pending_agents = [agent for agent in ["AnalysisAgent", "PlanningAgent", "CodingAgent", "QAAgent", "DeliveryAgent"] if agent not in completed_agents]
        task_lines = []
        for task_id, task in state.tasks.items():
            task_lines.append(f"| {task_id} | {task.title} | {task.status} | {', '.join(task.dependencies) or 'None'} |")
        if not task_lines:
            task_lines.append("| None | No tasks planned yet | pending | None |")
        readme = f"""# Supervisor Decision

## Current Decision
{decision}

## Workflow State
- Status: {state.workflow_status}
- Current agent: {state.current_agent or 'NOT_AVAILABLE'}
- Current task: {state.current_task or 'NOT_AVAILABLE'}

## Completed Agents
{chr(10).join(f'- {agent}' for agent in completed_agents) if completed_agents else '- None'}

## Pending Agents
{chr(10).join(f'- {agent}' for agent in pending_agents) if pending_agents else '- None'}

## QA/Rework
- Retry count: {state.retry_count}
- Failed tasks: {', '.join(state.failed_tasks) or 'None'}
"""
        plan = f"""# Supervisor Execution Plan

## Ordered Task State
| Task | Title | Status | Dependencies |
|---|---|---|---|
{chr(10).join(task_lines)}

## Rework Rules
- Failed tasks are retried up to 3 times.
- Completed tasks without passing QA are routed to QA.
- Delivery starts only after planned tasks complete and QA passes.

## Current Execution State
{decision}
"""
        write_text_artifact(state, "supervisor/README.md", readme, "DOCUMENTATION", "SupervisorAgent")
        write_text_artifact(state, "supervisor/execution_plan.md", plan, "DOCUMENTATION", "SupervisorAgent")
