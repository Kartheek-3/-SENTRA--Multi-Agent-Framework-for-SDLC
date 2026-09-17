import { ChatMessage, nowIso } from './chatTypes';

const agentLabels: Record<string, string> = {
  AnalysisAgent: 'Analysis Agent',
  PlanningAgent: 'Planning Agent',
  SupervisorAgent: 'Supervisor',
  CodingAgent: 'Coding Agent',
  QAAgent: 'QA Agent',
  DeliveryAgent: 'Delivery Agent',
  GitHubService: 'GitHub Intelligence',
};

export function eventToChatMessages(event: any, state: any): ChatMessage[] {
  const id = event.event_id || `${event.event}-${event.agent || ''}-${event.task_id || ''}-${event.path || ''}`;
  const timestamp = event.timestamp || nowIso();
  const agent = agentLabels[event.agent] || event.agent || 'SEAM';
  const base = { id, timestamp };

  switch (event.event) {
    case 'PROJECT_CREATED':
      return [{
        ...base,
        role: 'SEAM',
        type: 'MESSAGE',
        status: 'WAITING',
        content: `Project created: ${event.project_name || state?.project_name || 'SEAM project'}.\nI'll analyze this project and build it step by step when you run the workflow.`,
      }];
    case 'WORKFLOW_STARTED':
      return [{
        ...base,
        role: 'SEAM',
        type: 'PROGRESS',
        status: 'RUNNING',
        content: "I'll analyze the requirements, design the architecture, generate the code, validate it with QA, and prepare delivery artifacts.",
      }];
    case 'WORKFLOW_STOPPED':
      return [{
        ...base,
        role: 'SEAM',
        type: 'WARNING',
        status: 'BLOCKED',
        content: 'Workflow stopped. Completed artifacts are preserved.',
      }];
    case 'WORKFLOW_FAILED':
      return [{
        ...base,
        role: 'SEAM',
        type: 'ERROR',
        status: 'FAILED',
        severity: 'HIGH',
        content: `I could not continue because the workflow failed.\n\nError:\n${event.error || 'Unknown backend error'}`,
      }];
    case 'WORKFLOW_COMPLETED':
      return [{
        ...base,
        role: 'SEAM',
        type: 'SUMMARY',
        status: 'COMPLETE',
        artifact: { kind: 'project', label: 'Open generated files', action: 'openGeneratedFiles' },
        content: finalSummary(state),
      }];
    case 'AGENT_STARTED':
      return [{
        ...base,
        role: 'AGENT',
        agent,
        type: event.agent === 'QAAgent' ? 'QA' : 'PROGRESS',
        status: 'RUNNING',
        content: startedContent(event.agent, state),
      }];
    case 'AGENT_COMPLETED':
      return [{
        ...base,
        id: `${id}-complete`,
        role: 'AGENT',
        agent,
        type: event.agent === 'QAAgent' ? 'QA' : 'SUCCESS',
        status: 'COMPLETE',
        content: completedContent(event.agent, state),
      }];
    case 'TASK_STARTED':
      return [{
        ...base,
        role: 'AGENT',
        agent,
        type: 'TASK',
        status: 'RUNNING',
        taskId: event.task_id,
        content: `Starting ${event.task_id || 'task'}.\n${taskTitle(state, event.task_id)}`,
      }];
    case 'TASK_COMPLETED':
      return [{
        ...base,
        role: 'AGENT',
        agent,
        type: 'TASK',
        status: 'COMPLETE',
        taskId: event.task_id,
        content: `${event.task_id || 'Task'} completed.\n${taskTitle(state, event.task_id)}`,
      }];
    case 'DIRECTORY_CREATED':
      return [{
        ...base,
        role: 'AGENT',
        agent: agentLabels[event.agent] || 'Coding Agent',
        type: 'FILE',
        status: 'COMPLETE',
        taskId: event.task_id,
        artifact: { kind: 'project', label: event.path, action: 'showProjectStructure' },
        content: `Created folder: ${event.path}`,
      }];
    case 'FILE_GENERATED':
    case 'FILE_CREATED':
    case 'FILE_UPDATED':
      return [{
        ...base,
        role: 'AGENT',
        agent: agentLabels[event.agent] || 'Coding Agent',
        type: 'FILE',
        status: 'COMPLETE',
        taskId: event.task_id,
        artifact: { kind: 'file', label: event.path, path: event.path, action: 'openFile' },
        content: `${event.operation === 'updated' ? 'Updated' : 'Created'} ${event.path}`,
      }];
    case 'ARTIFACT_CREATED':
    case 'ARTIFACT_REGISTERED':
    case 'DIAGRAM_GENERATED':
      return [{
        ...base,
        role: 'AGENT',
        agent,
        type: event.artifact_type === 'DIAGRAM' ? 'DIAGRAM' : 'FILE',
        status: 'COMPLETE',
        taskId: event.task_id,
        artifact: event.path ? { kind: 'file', label: event.path, path: event.path, action: 'openFile' } : undefined,
        content: `Artifact created: ${event.path || event.summary || event.artifact_id || 'artifact'}${event.artifact_type ? `\nType: ${event.artifact_type}` : ''}`,
      }];
    case 'GITHUB_SEARCH_STARTED':
      return [{
        ...base,
        role: 'AGENT',
        agent: 'GitHub Intelligence',
        type: 'PROGRESS',
        status: 'RUNNING',
        content: event.summary || 'Searching relevant public repositories...',
      }];
    case 'GITHUB_SEARCH_COMPLETED':
    case 'GITHUB_ANALYSIS_COMPLETED':
    case 'GITHUB_REPOSITORY_SELECTED':
      return [{
        ...base,
        role: 'AGENT',
        agent: 'GitHub Intelligence',
        type: 'SUMMARY',
        status: 'COMPLETE',
        artifact: event.path ? { kind: 'file', label: event.path, path: event.path, action: 'openFile' } : undefined,
        content: event.summary || event.repository || 'GitHub Intelligence completed.',
      }];
    case 'GITHUB_RESEARCH_UNAVAILABLE':
    case 'GITHUB_RATE_LIMITED':
    case 'GITHUB_ANALYSIS_FAILED':
      return [{
        ...base,
        role: 'AGENT',
        agent: 'GitHub Intelligence',
        type: 'WARNING',
        status: 'NOT_AVAILABLE',
        content: event.summary || event.error || 'GitHub Intelligence unavailable - continuing without repository context.',
      }];
    default:
      return [];
  }
}

export function projectStateToChatMessages(state: any): ChatMessage[] {
  const messages: ChatMessage[] = [];
  if (!state?.project_id) return messages;
  const timestamp = nowIso();
  if (state.analysis) {
    messages.push({
      id: `state-analysis-${state.project_id}`,
      timestamp,
      role: 'AGENT',
      agent: 'Analysis Agent',
      type: 'SUMMARY',
      status: 'COMPLETE',
      content: analysisSummary(state),
    });
  }
  if (state.project_plan) {
    messages.push({
      id: `state-planning-${state.project_id}`,
      timestamp,
      role: 'AGENT',
      agent: 'Planning Agent',
      type: 'SUMMARY',
      status: 'COMPLETE',
      content: planningSummary(state),
    });
  }
  if (state.github_selection || state.github_status === 'token_missing') {
    messages.push({
      id: `state-github-${state.project_id}`,
      timestamp,
      role: 'SEAM',
      type: 'WARNING',
      status: state.github_selection ? 'COMPLETE' : 'NOT_AVAILABLE',
      content: state.github_selection ? 'GitHub Intelligence completed.' : 'GitHub Intelligence is unavailable because no GitHub token is configured. The core workflow can continue.',
    });
  }
  return messages;
}

function startedContent(agent?: string, state?: any) {
  if (agent === 'AnalysisAgent') return 'Analyzing requirements...\n- Extracting functional requirements\n- Extracting non-functional requirements\n- Identifying actors, entities, constraints, risks\n- Determining project scale';
  if (agent === 'PlanningAgent') return 'Planning the system architecture...\n- Selecting architecture style\n- Identifying components\n- Designing database and API contracts\n- Generating implementation tasks';
  if (agent === 'SupervisorAgent') return `Checking workflow state and task dependencies...\nCurrent task: ${state?.current_task || 'NOT_AVAILABLE'}`;
  if (agent === 'CodingAgent') return `Generating project files for ${state?.current_task || 'the selected task'}...`;
  if (agent === 'QAAgent') return 'Reviewing generated implementation...\n- Syntax validation\n- Requirement traceability\n- Architecture validation\n- Security validation\n- Test execution when available';
  if (agent === 'DeliveryAgent') return 'Preparing project for delivery...\n- Documentation\n- Manifest\n- Integrity validation\n- Secret scan\n- Package\n- Knowledge update';
  if (agent === 'GitHubService') return 'Checking GitHub Intelligence availability and repository context...';
  return 'Processing...';
}

function completedContent(agent?: string, state?: any) {
  if (agent === 'AnalysisAgent') return analysisSummary(state);
  if (agent === 'PlanningAgent') return planningSummary(state);
  if (agent === 'SupervisorAgent') return `Supervisor decision complete.\nCurrent agent: ${state?.current_agent || 'NOT_AVAILABLE'}\nCurrent task: ${state?.current_task || 'NOT_AVAILABLE'}`;
  if (agent === 'CodingAgent') return `Coding completed for ${state?.current_task || 'the current task'}.\nQA is pending unless already reported by ProjectState.`;
  if (agent === 'QAAgent') return qaSummary(state);
  if (agent === 'DeliveryAgent') return deliverySummary(state);
  if (agent === 'GitHubService') return state?.github_selection ? 'GitHub repository analysis completed.' : 'GitHub Intelligence is unavailable or no repository was selected. The core workflow can continue.';
  return 'Completed.';
}

function analysisSummary(state: any) {
  const analysis = state?.analysis;
  const functional = analysis?.functional_requirements?.length ?? 'NOT_AVAILABLE';
  const nonFunctional = analysis?.non_functional_requirements?.length ?? 'NOT_AVAILABLE';
  const entities = analysis?.entities?.length ?? 'NOT_AVAILABLE';
  const actors = analysis?.actors?.length ?? 'NOT_AVAILABLE';
  const scale = state?.scale_assessment?.scale_level || analysis?.scale_assessment?.scale_level || 'NOT_AVAILABLE';
  return `Analysis completed.\n\nFunctional requirements: ${functional}\nNon-functional requirements: ${nonFunctional}\nEntities: ${entities}\nActors: ${actors}\n\nScale assessment: ${scale}`;
}

function planningSummary(state: any) {
  const plan = state?.project_plan;
  const design = plan?.system_design;
  const tasks = plan?.tasks?.length ?? 'NOT_AVAILABLE';
  const db = design?.database_design?.database_type || design?.database?.type || 'NOT_AVAILABLE';
  const apiCount = design?.api_contracts?.length ?? design?.api_endpoints?.length ?? 'NOT_AVAILABLE';
  const style = design?.architecture_style || 'NOT_AVAILABLE';
  return `Planning completed.\n\nArchitecture: ${style}\nTasks: ${tasks}\nDatabase: ${db}\nAPI endpoints: ${apiCount}`;
}

function qaSummary(state: any) {
  const tasks = Object.values(state?.tasks || {}) as any[];
  const latest = tasks.find(task => task.result?.qa_result)?.result?.qa_result;
  if (!latest) return 'QA status: NOT_AVAILABLE';
  const tests = latest.test_results?.length ? 'AVAILABLE' : 'NOT_AVAILABLE';
  return `QA validation ${latest.passed ? 'completed' : 'found issues'}.\n\nSyntax: ${latest.syntax_errors?.length ? 'FAILED' : 'COMPLETE'}\nArchitecture: ${latest.architecture_violations?.length ? 'FAILED' : 'COMPLETE'}\nSecurity: ${latest.security_issues?.length ? 'FAILED' : 'COMPLETE'}\nTests: ${tests}\n\nStatus: ${latest.passed ? 'READY FOR DELIVERY' : 'FAILED'}`;
}

function deliverySummary(state: any) {
  const delivery = state?.delivery_result;
  if (!delivery) return 'Delivery status: NOT_AVAILABLE';
  return `Delivery ${delivery.status || 'completed'}.\n\nQA verified: ${delivery.qa_verified ? 'YES' : 'NO'}\nPackage: ${delivery.package_path || 'NOT_AVAILABLE'}\nManifest: ${delivery.manifest_path || 'NOT_AVAILABLE'}`;
}

function finalSummary(state: any) {
  const tasks = Object.values(state?.tasks || {}) as any[];
  const completed = state?.completed_tasks?.length ?? tasks.filter(task => task.status === 'completed').length;
  const files = tasks.reduce((count, task: any) => count + (task.result?.files?.length || task.result?.generated_files?.length || 0), 0);
  return `Project generation completed.\n\nProject: ${state?.project_name || 'NOT_AVAILABLE'}\nScale: ${state?.scale_assessment?.scale_level || 'NOT_AVAILABLE'}\nAgents executed: 6\nTasks completed: ${completed}\nFiles generated: ${files || 'NOT_AVAILABLE'}\nQA: ${state?.latest_qa_status || 'NOT_AVAILABLE'}\nDelivery: ${state?.delivery_result?.status || 'NOT_AVAILABLE'}`;
}

function taskTitle(state: any, taskId?: string) {
  if (!taskId) return '';
  const task = state?.tasks?.[taskId] || state?.project_plan?.tasks?.find((item: any) => item.task_id === taskId);
  return task?.title || task?.description || '';
}
