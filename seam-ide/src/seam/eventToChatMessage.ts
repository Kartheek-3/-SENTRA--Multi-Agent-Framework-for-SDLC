import { ChatMessage, nowIso } from './chatTypes';

const agentLabels: Record<string, string> = {
  AnalysisAgent: 'Analysis Agent',
  PlanningAgent: 'Planning Agent',
  SupervisorAgent: 'Supervisor',
  CodingAgent: 'Coding Agent',
  QAAgent: 'QA Agent',
  DeliveryAgent: 'Delivery Agent',
  GitHubService: 'GitHub Intelligence',
  N8NIntegration: 'N8N',
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
    case 'AGENT_FAILED':
    case 'AGENT_TIMEOUT':
    case 'AGENT_CANCELLED':
      return [{
        ...base,
        role: 'AGENT',
        agent,
        type: 'ERROR',
        status: event.event === 'AGENT_CANCELLED' ? 'BLOCKED' : 'FAILED',
        severity: event.event === 'AGENT_TIMEOUT' ? 'HIGH' : 'MEDIUM',
        content: `${agent} ${event.event === 'AGENT_TIMEOUT' ? 'timed out' : event.event === 'AGENT_CANCELLED' ? 'was cancelled' : 'failed'}.\n${event.error || event.errors?.join('\n') || 'No additional details.'}`,
      }];
    case 'TOOL_REQUESTED':
    case 'TOOL_STARTED':
    case 'TOOL_PERMISSION_CHECKED':
      return [{
        ...base,
        role: 'AGENT',
        agent,
        type: 'PROGRESS',
        status: 'RUNNING',
        content: frontendToolContent(event.tool_name, event.status || 'running') || `${agent}\nUsing ${event.tool_name || 'tool'}\n${event.status || 'running'}`,
      }];
    case 'TOOL_COMPLETED':
      return [{
        ...base,
        role: 'AGENT',
        agent,
        type: 'SUCCESS',
        status: 'COMPLETE',
        content: frontendToolContent(event.tool_name, 'complete', event.duration_ms) || `${agent}\nTool completed: ${event.tool_name || 'tool'}${event.duration_ms ? `\nDuration: ${event.duration_ms} ms` : ''}`,
      }];
    case 'TOOL_FAILED':
    case 'TOOL_TIMEOUT':
    case 'TOOL_PERMISSION_DENIED':
      return [{
        ...base,
        role: 'AGENT',
        agent,
        type: 'WARNING',
        status: event.event === 'TOOL_PERMISSION_DENIED' ? 'BLOCKED' : 'FAILED',
        content: frontendToolContent(event.tool_name, event.event === 'TOOL_PERMISSION_DENIED' ? 'permission denied' : event.event === 'TOOL_TIMEOUT' ? 'timeout' : 'failed') || `${agent}\nTool ${event.event === 'TOOL_TIMEOUT' ? 'timed out' : event.event === 'TOOL_PERMISSION_DENIED' ? 'permission denied' : 'failed'}: ${event.tool_name || 'tool'}\n${event.reason || event.error || ''}`,
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
    case 'GITHUB_REPOSITORY_DISCOVERED':
    case 'GITHUB_REPOSITORY_ANALYSIS_COMPLETED':
    case 'GITHUB_INCREMENTAL_ANALYSIS_COMPLETED':
    case 'GITHUB_REPOSITORY_CURRENT':
      return [{
        ...base,
        role: 'AGENT',
        agent: 'GitHub Intelligence',
        type: 'SUMMARY',
        status: 'COMPLETE',
        artifact: event.path ? { kind: 'file', label: event.path, path: event.path, action: 'openFile' } : undefined,
        content: event.summary || event.repository || 'GitHub Intelligence completed.',
      }];
    case 'GITHUB_REPOSITORY_ANALYSIS_STARTED':
    case 'GITHUB_INCREMENTAL_ANALYSIS_STARTED':
    case 'GITHUB_REPOSITORY_CHANGED':
    case 'GITHUB_WEBHOOK_RECEIVED':
      return [{
        ...base,
        role: 'AGENT',
        agent: 'GitHub Intelligence',
        type: 'PROGRESS',
        status: 'RUNNING',
        content: event.summary || `GitHub Intelligence update for ${event.repository || 'repository'}.`,
      }];
    case 'GITHUB_RESEARCH_UNAVAILABLE':
    case 'GITHUB_RATE_LIMITED':
    case 'GITHUB_ANALYSIS_FAILED':
    case 'GITHUB_REPOSITORY_STALE':
    case 'GITHUB_REPOSITORY_UPDATE_FAILED':
      return [{
        ...base,
        role: 'AGENT',
        agent: 'GitHub Intelligence',
        type: 'WARNING',
        status: 'NOT_AVAILABLE',
        content: event.summary || event.error || 'GitHub Intelligence unavailable - continuing without repository context.',
      }];
    case 'N8N_WORKFLOW_REQUESTED':
    case 'N8N_WORKFLOW_STARTED':
      return [{
        ...base,
        role: 'SEAM',
        agent: 'N8N',
        type: 'PROGRESS',
        status: 'RUNNING',
        content: event.summary || `N8N: Triggering ${event.workflow || 'external workflow'}.`,
      }];
    case 'N8N_WORKFLOW_COMPLETED':
      return [{
        ...base,
        role: 'SEAM',
        agent: 'N8N',
        type: 'SUCCESS',
        status: 'COMPLETE',
        content: event.summary || `N8N: ${event.workflow || 'external workflow'} completed.`,
      }];
    case 'N8N_WEBHOOK_RECEIVED':
      return [{
        ...base,
        role: 'SEAM',
        agent: 'N8N',
        type: 'PROGRESS',
        status: 'RUNNING',
        content: event.summary || `N8N: ${event.event_type || 'external event'} received.`,
      }];
    case 'N8N_WORKFLOW_FAILED':
    case 'N8N_WEBHOOK_REJECTED':
      return [{
        ...base,
        role: 'SEAM',
        agent: 'N8N',
        type: 'WARNING',
        status: 'FAILED',
        content: event.summary || event.error || 'N8N integration event failed.',
      }];
    case 'RELEASE_READINESS_STARTED':
    case 'DEPLOYMENT_ARTIFACT_VALIDATION_STARTED':
    case 'POST_DEPLOYMENT_VERIFICATION_STARTED':
      return [{
        ...base,
        role: 'AGENT',
        agent: 'Delivery Agent',
        type: 'PROGRESS',
        status: 'RUNNING',
        content: event.summary || 'Preparing delivery and deployment evidence.',
      }];
    case 'RELEASE_READINESS_COMPLETED':
    case 'DEPLOYMENT_PROFILE_DETECTED':
    case 'DEPLOYMENT_ARTIFACT_VALIDATION_COMPLETED':
    case 'PACKAGE_CREATED':
    case 'POST_DEPLOYMENT_VERIFICATION_COMPLETED':
    case 'DELIVERY_COMPLETED':
      return [{
        ...base,
        role: 'AGENT',
        agent: 'Delivery Agent',
        type: 'SUMMARY',
        status: event.status === 'FAIL' || event.status === 'BLOCKED' ? 'FAILED' : 'COMPLETE',
        content: event.summary || deliveryDeploymentSummary(state),
      }];
    case 'RELEASE_BLOCKED':
    case 'DELIVERY_BLOCKED':
      return [{
        ...base,
        role: 'AGENT',
        agent: 'Delivery Agent',
        type: 'WARNING',
        status: 'BLOCKED',
        severity: 'HIGH',
        content: event.summary || deliveryDeploymentSummary(state),
      }];
    case 'EVALUATION_STARTED':
      return [{
        ...base,
        role: 'SEAM',
        agent: 'Evaluation',
        type: 'PROGRESS',
        status: 'RUNNING',
        content: event.summary || 'Computing SEAM evaluation metrics.',
      }];
    case 'EVALUATION_METRIC_COMPUTED':
      return [{
        ...base,
        role: 'SEAM',
        agent: 'Evaluation',
        type: 'PROGRESS',
        status: 'RUNNING',
        content: event.summary || `${event.metric || 'metric'}: ${event.value ?? 'NOT_AVAILABLE'}`,
      }];
    case 'EVALUATION_COMPLETED':
      return [{
        ...base,
        role: 'SEAM',
        agent: 'Evaluation',
        type: 'SUMMARY',
        status: 'COMPLETE',
        content: evaluationSummary(state),
      }];
    case 'EVALUATION_FAILED':
      return [{
        ...base,
        role: 'SEAM',
        agent: 'Evaluation',
        type: 'WARNING',
        status: 'FAILED',
        content: event.summary || event.error || 'Evaluation metrics computation failed.',
      }];
    case 'EXPERIMENT_CREATED':
    case 'EXPERIMENT_STARTED':
    case 'EXPERIMENT_RUN_STARTED':
    case 'EXPERIMENT_COMPARISON_STARTED':
      return [{
        ...base,
        role: 'SEAM',
        agent: 'Experiment Harness',
        type: 'PROGRESS',
        status: 'RUNNING',
        content: event.summary || 'Experiment harness update.',
      }];
    case 'EXPERIMENT_RUN_COMPLETED':
    case 'EXPERIMENT_COMPARISON_COMPLETED':
    case 'EXPERIMENT_COMPLETED':
      return [{
        ...base,
        role: 'SEAM',
        agent: 'Experiment Harness',
        type: 'SUMMARY',
        status: 'COMPLETE',
        content: event.summary || experimentSummary(state),
      }];
    case 'EXPERIMENT_RUN_FAILED':
      return [{
        ...base,
        role: 'SEAM',
        agent: 'Experiment Harness',
        type: 'WARNING',
        status: 'FAILED',
        content: event.summary || event.error || 'Experiment run failed.',
      }];
    case 'FRONTEND_DETECTION_STARTED':
      return [{
        ...base,
        role: 'SEAM',
        agent: 'Frontend Intelligence',
        type: 'PROGRESS',
        status: 'RUNNING',
        content: event.summary || 'Frontend capability detection started.',
      }];
    case 'FRONTEND_CAPABILITIES_DETECTED':
      return [{
        ...base,
        role: 'SEAM',
        agent: 'Frontend Intelligence',
        type: 'SUMMARY',
        status: 'COMPLETE',
        content: event.summary || `Frontend detected: ${event.framework || 'UNKNOWN'} / ${event.language || 'UNKNOWN'} / ${event.build_system || 'UNKNOWN'}`,
      }];
    case 'FRONTEND_DETECTION_FAILED':
      return [{
        ...base,
        role: 'SEAM',
        agent: 'Frontend Intelligence',
        type: 'WARNING',
        status: 'FAILED',
        content: event.summary || event.error || 'Frontend capability detection failed.',
      }];
    case 'FRONTEND_PLAN_STARTED':
      return [{
        ...base,
        role: 'AGENT',
        agent: 'Planning Agent',
        type: 'PROGRESS',
        status: 'RUNNING',
        content: event.summary || 'Frontend architecture planning started.',
      }];
    case 'FRONTEND_PLAN_COMPLETED':
      return [{
        ...base,
        role: 'AGENT',
        agent: 'Planning Agent',
        type: 'SUMMARY',
        status: 'COMPLETE',
        content: event.summary || `Frontend architecture planned: ${event.framework || 'UNKNOWN'} / ${event.language || 'UNKNOWN'} / ${event.build_system || 'UNKNOWN'}.`,
      }];
    case 'FRONTEND_PLAN_FAILED':
      return [{
        ...base,
        role: 'AGENT',
        agent: 'Planning Agent',
        type: 'WARNING',
        status: 'FAILED',
        content: event.summary || event.error || 'Frontend architecture planning failed.',
      }];
    case 'CONTRACT_ANALYSIS_STARTED':
      return [{
        ...base,
        role: 'AGENT',
        agent: 'Planning Agent',
        type: 'PROGRESS',
        status: 'RUNNING',
        content: event.summary || 'Full-stack contract analysis started.',
      }];
    case 'CONTRACT_ANALYSIS_COMPLETED':
      return [{
        ...base,
        role: 'AGENT',
        agent: 'Planning Agent',
        type: 'SUMMARY',
        status: event.status === 'FAIL' ? 'FAILED' : 'COMPLETE',
        content: event.summary || `Full-stack contract analysis completed with ${event.issues ?? 0} issue(s).`,
      }];
    case 'CONTRACT_ANALYSIS_FAILED':
      return [{
        ...base,
        role: 'AGENT',
        agent: 'Planning Agent',
        type: 'WARNING',
        status: 'FAILED',
        content: event.summary || event.error || 'Full-stack contract analysis failed.',
      }];
    case 'CONTRACT_MISMATCH_DETECTED':
      return [{
        ...base,
        role: 'AGENT',
        agent: 'QA Agent',
        type: 'WARNING',
        status: event.severity === 'INFO' ? 'COMPLETE' : 'FAILED',
        severity: event.severity || 'WARNING',
        content: event.summary || `${event.category || 'Contract issue'}\nEndpoint: ${event.endpoint || 'NOT_AVAILABLE'}\nExpected: ${event.expected || 'NOT_AVAILABLE'}\nActual: ${event.actual || 'NOT_AVAILABLE'}`,
      }];
    case 'RUNTIME_CONTRACT_VALIDATION_STARTED':
      return [{
        ...base,
        role: 'AGENT',
        agent: 'QA Agent',
        type: 'PROGRESS',
        status: 'RUNNING',
        content: event.summary || 'Runtime contract validation started.',
      }];
    case 'RUNTIME_CONTRACT_VALIDATION_COMPLETED':
      return [{
        ...base,
        role: 'AGENT',
        agent: 'QA Agent',
        type: 'SUMMARY',
        status: event.status === 'PASS' ? 'COMPLETE' : 'FAILED',
        content: event.summary || `Runtime contract validation completed: ${event.status || 'UNKNOWN'}.`,
      }];
    case 'RUNTIME_CONTRACT_VALIDATION_FAILED':
      return [{
        ...base,
        role: 'AGENT',
        agent: 'QA Agent',
        type: 'WARNING',
        status: 'FAILED',
        content: event.summary || event.error || 'Runtime contract validation failed.',
      }];
    case 'RUNTIME_CONTRACT_MISMATCH_DETECTED':
      return [{
        ...base,
        role: 'AGENT',
        agent: 'QA Agent',
        type: 'WARNING',
        status: 'FAILED',
        severity: event.severity || 'ERROR',
        content: event.summary || `${event.category || 'Runtime contract mismatch'}\nEndpoint: ${event.endpoint || 'NOT_AVAILABLE'}\nExpected: ${event.expected || 'NOT_AVAILABLE'}\nActual: ${event.actual || 'NOT_AVAILABLE'}`,
      }];
    case 'RUNTIME_DETECTION_STARTED':
    case 'RUNTIME_START_STARTED':
    case 'RUNTIME_HEALTH_CHECK_STARTED':
    case 'RUNTIME_STOP_STARTED':
      return [{
        ...base,
        role: 'AGENT',
        agent: 'QA Agent',
        type: 'PROGRESS',
        status: 'RUNNING',
        content: event.summary || 'Application runtime operation started.',
      }];
    case 'RUNTIME_DETECTION_COMPLETED':
    case 'RUNTIME_STARTED':
    case 'RUNTIME_READY':
    case 'RUNTIME_STOPPED':
      return [{
        ...base,
        role: 'AGENT',
        agent: 'QA Agent',
        type: 'SUMMARY',
        status: 'COMPLETE',
        content: event.summary || `Application runtime status: ${event.status || 'READY'}.`,
      }];
    case 'RUNTIME_START_FAILED':
    case 'RUNTIME_HEALTH_FAILED':
      return [{
        ...base,
        role: 'AGENT',
        agent: 'QA Agent',
        type: 'WARNING',
        status: 'FAILED',
        content: event.summary || 'Application runtime failed.',
      }];
    case 'E2E_SCENARIO_GENERATION_STARTED':
    case 'E2E_EXECUTION_STARTED':
    case 'E2E_STEP_STARTED':
      return [{
        ...base,
        role: 'AGENT',
        agent: 'QA Agent',
        type: 'PROGRESS',
        status: 'RUNNING',
        content: event.summary || 'E2E validation step started.',
      }];
    case 'E2E_SCENARIO_GENERATED':
    case 'E2E_STEP_COMPLETED':
    case 'E2E_EXECUTION_COMPLETED':
      return [{
        ...base,
        role: 'AGENT',
        agent: 'QA Agent',
        type: 'SUMMARY',
        status: event.status === 'FAIL' ? 'FAILED' : 'COMPLETE',
        content: event.summary || `E2E validation: ${event.status || 'COMPLETE'}.`,
      }];
    case 'E2E_STEP_FAILED':
      return [{
        ...base,
        role: 'AGENT',
        agent: 'QA Agent',
        type: 'WARNING',
        status: 'FAILED',
        content: event.summary || 'E2E step failed.',
      }];
    case 'DEFECT_LOCALIZED':
      return [{
        ...base,
        role: 'AGENT',
        agent: 'QA Agent',
        type: 'WARNING',
        status: event.layer === 'UNKNOWN' ? 'BLOCKED' : 'FAILED',
        content: event.summary || `Defect localized\nLayer: ${event.layer || 'UNKNOWN'}\nConfidence: ${event.confidence || 'LOW'}\nIssue: ${event.issue || 'NOT_AVAILABLE'}`,
      }];
    case 'REPAIR_PLAN_CREATED':
    case 'REPAIR_STARTED':
    case 'TARGETED_VERIFICATION_STARTED':
    case 'REGRESSION_STARTED':
      return [{
        ...base,
        role: 'AGENT',
        agent: event.event === 'REPAIR_STARTED' ? 'Coding Agent' : 'QA Agent',
        type: 'PROGRESS',
        status: 'RUNNING',
        content: event.summary || 'Repair workflow step started.',
      }];
    case 'REPAIR_COMPLETED':
    case 'TARGETED_VERIFICATION_COMPLETED':
    case 'REGRESSION_COMPLETED':
    case 'DEFECT_RESOLVED':
      return [{
        ...base,
        role: 'AGENT',
        agent: event.event === 'REPAIR_COMPLETED' ? 'Coding Agent' : 'QA Agent',
        type: 'SUMMARY',
        status: event.status === 'FAIL' ? 'FAILED' : 'COMPLETE',
        content: event.summary || `Repair workflow status: ${event.status || 'COMPLETE'}.`,
      }];
    case 'REPAIR_FAILED':
    case 'DEFECT_REMAINING':
      return [{
        ...base,
        role: 'AGENT',
        agent: event.event === 'REPAIR_FAILED' ? 'Coding Agent' : 'QA Agent',
        type: 'WARNING',
        status: 'FAILED',
        content: event.summary || 'Repair workflow failed.',
      }];
    case 'RAG_INDEX_STARTED':
    case 'RAG_RETRIEVAL_STARTED':
      return [{
        ...base,
        role: 'SEAM',
        type: 'PROGRESS',
        status: 'RUNNING',
        content: event.summary || 'Using SEAM knowledge repository...',
      }];
    case 'RAG_INDEX_COMPLETED':
    case 'RAG_RETRIEVAL_COMPLETED':
    case 'KNOWLEDGE_UPDATED':
      return [{
        ...base,
        role: 'SEAM',
        type: 'SUMMARY',
        status: 'COMPLETE',
        content: event.summary || 'SEAM knowledge repository updated.',
      }];
    case 'RAG_RETRIEVAL_FAILED':
      return [{
        ...base,
        role: 'SEAM',
        type: 'WARNING',
        status: 'FAILED',
        content: event.summary || event.error || 'RAG retrieval failed.',
      }];
    case 'DOMAIN_CONTEXT_RETRIEVAL_STARTED':
      return [{
        ...base,
        role: 'SEAM',
        agent: 'RAG',
        type: 'PROGRESS',
        status: 'RUNNING',
        content: event.summary || `Retrieving validated ${event.domain || 'domain'} knowledge...`,
      }];
    case 'DOMAIN_CONTEXT_RETRIEVED':
      return [{
        ...base,
        role: 'SEAM',
        agent: 'RAG',
        type: 'SUMMARY',
        status: 'COMPLETE',
        content: `${event.summary || 'Domain-aware retrieval completed.'}${event.sources?.length ? `\n\nSources:\n${event.sources.map((source: string) => `- ${source}`).join('\n')}` : ''}`,
      }];
    case 'DOMAIN_ARTIFACTS_PERSISTED':
      return [{
        ...base,
        role: 'AGENT',
        agent: 'Analysis Agent',
        type: 'FILE',
        status: 'COMPLETE',
        artifact: event.paths?.[0] ? { kind: 'file', label: event.paths[0], path: event.paths[0], action: 'openFile' } : undefined,
        content: `${event.summary || 'Domain context artifacts persisted.'}${event.paths?.length ? `\n${event.paths.join('\n')}` : ''}`,
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
  if (state.frontend_capabilities?.package_json) {
    messages.push({
      id: `state-frontend-${state.project_id}`,
      timestamp,
      role: 'SEAM',
      agent: 'Frontend Intelligence',
      type: 'SUMMARY',
      status: 'COMPLETE',
      content: frontendCapabilitySummary(state.frontend_capabilities),
    });
  }
  if (state.frontend_architecture_plan) {
    messages.push({
      id: `state-frontend-architecture-${state.project_id}`,
      timestamp,
      role: 'AGENT',
      agent: 'Planning Agent',
      type: 'SUMMARY',
      status: 'COMPLETE',
      content: frontendArchitectureSummary(state.frontend_architecture_plan),
    });
  }
  if (state.full_stack_contract) {
    messages.push({
      id: `state-contracts-${state.project_id}`,
      timestamp,
      role: 'AGENT',
      agent: 'Planning Agent',
      type: 'SUMMARY',
      status: state.full_stack_contract.status === 'FAIL' ? 'FAILED' : 'COMPLETE',
      content: fullStackContractSummary(state.full_stack_contract, state.contract_issues || [], state.runtime_contract_results || [], state),
    });
  }
  if (state.e2e_scenarios?.length || state.e2e_results?.length) {
    messages.push({
      id: `state-e2e-${state.project_id}`,
      timestamp,
      role: 'AGENT',
      agent: 'QA Agent',
      type: 'SUMMARY',
      status: state.e2e_results?.some((result: any) => result.status === 'FAIL') ? 'FAILED' : 'COMPLETE',
      content: e2eValidationSummary(state),
    });
  }
  if (state.repair_plans?.length || state.repair_results?.length) {
    messages.push({
      id: `state-repair-${state.project_id}`,
      timestamp,
      role: 'AGENT',
      agent: 'Supervisor',
      type: 'SUMMARY',
      status: state.targeted_verifications?.some((item: any) => item.status === 'FAIL') ? 'FAILED' : 'COMPLETE',
      content: repairSummary(state),
    });
  }
  if (state.release_readiness || state.deployment_profile || state.deployment_result || state.post_deployment_verification || state.rollback_info) {
    messages.push({
      id: `state-delivery-deployment-${state.project_id}`,
      timestamp,
      role: 'AGENT',
      agent: 'Delivery Agent',
      type: 'SUMMARY',
      status: state.release_readiness?.status === 'BLOCKED' || state.release_readiness?.status === 'NOT_READY' ? 'BLOCKED' : 'COMPLETE',
      content: deliveryDeploymentSummary(state),
    });
  }
  if (state.evaluation_summary) {
    messages.push({
      id: `state-evaluation-${state.project_id}`,
      timestamp,
      role: 'SEAM',
      agent: 'Evaluation',
      type: 'SUMMARY',
      status: 'COMPLETE',
      content: evaluationSummary(state),
    });
  }
  if (state.experiment_summary) {
    messages.push({
      id: `state-experiment-${state.project_id}`,
      timestamp,
      role: 'SEAM',
      agent: 'Experiment Harness',
      type: 'SUMMARY',
      status: state.experiment_summary.status === 'COMPLETED' ? 'COMPLETE' : 'RUNNING',
      content: experimentSummary(state),
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
  return `${deliveryDeploymentSummary(state)}\n\nLegacy Delivery Result\nStatus: ${delivery.status || 'completed'}\nQA verified: ${delivery.qa_verified ? 'YES' : 'NO'}\nPackage: ${delivery.package_path || 'NOT_AVAILABLE'}\nManifest: ${delivery.manifest_path || 'NOT_AVAILABLE'}`;
}

function frontendToolContent(toolName?: string, status?: string, durationMs?: number) {
  const labels: Record<string, string> = {
    npm_runner: 'Frontend dependencies/scripts',
    typecheck_runner: 'Frontend typecheck',
    lint_runner: 'Frontend lint',
    frontend_test_runner: 'Frontend tests',
    playwright_runner: 'Browser validation',
    build_runner: 'Frontend build',
    browser_screenshot: 'Browser screenshot',
    accessibility_checker: 'Accessibility check',
  };
  if (!toolName || !labels[toolName]) return '';
  const suffix = durationMs ? `\nDuration: ${durationMs} ms` : '';
  return `Frontend Development\n${labels[toolName]}: ${status || 'running'}${suffix}`;
}

function frontendCapabilitySummary(profile: any) {
  const readable = (value: any) => value === true ? 'Available' : value === false ? 'Not Configured' : value || 'UNKNOWN';
  return `Frontend Environment

Framework: ${readable(profile.framework)}
Language: ${readable(profile.language)}
Build: ${readable(profile.build_system)}
Package Manager: ${readable(profile.package_manager)}
Type Check: ${readable(profile.typecheck_available)}
Lint: ${readable(profile.lint_available)}
Unit Tests: ${readable(profile.frontend_test_framework)}
Browser Tests: ${profile.playwright_available ? 'Playwright' : 'Not Configured'}
Accessibility: ${profile.accessibility_available ? 'Available' : 'Not Configured'}`;
}

function frontendArchitectureSummary(plan: any) {
  const routes = plan.routes || plan.pages?.map((page: any) => page.route).filter(Boolean) || [];
  const pages = plan.pages?.map((page: any) => page.name).filter(Boolean) || [];
  const components = plan.components?.map((component: any) => component.name).filter(Boolean) || [];
  const services = plan.services?.map((service: any) => service.name).filter(Boolean) || [];
  const files = plan.file_structure?.map((file: any) => `${file.operation || 'CREATE'} ${file.path}`).filter(Boolean) || [];
  const order = plan.implementation_order || [];
  const top = (items: string[], count = 6) => items.slice(0, count).map(item => `- ${item}`).join('\n') || '- NOT_AVAILABLE';
  return `Frontend Architecture

Framework: ${plan.framework || 'UNKNOWN'}
Language: ${plan.language || 'UNKNOWN'}
Build System: ${plan.build_system || 'UNKNOWN'}
Routing: ${plan.routing_strategy || 'NOT_AVAILABLE'}
State Management: ${plan.state_management || 'NOT_AVAILABLE'}

Routes:
${top(routes)}

Pages:
${top(pages)}

Components:
${top(components)}

Services:
${top(services)}

API Integration: ${plan.api_integration?.length ?? 0} mappings

File Plan:
${top(files)}

Implementation Order:
${top(order, 10)}`;
}

function fullStackContractSummary(profile: any, issues: any[], runtimeResults: any[], state: any) {
  const mappings = profile.mappings || [];
  const issueLines = (issues?.length ? issues : profile.issues || []).slice(0, 6).map((issue: any) => `- ${issue.severity || 'WARNING'} ${issue.category || 'CONTRACT'}: ${issue.endpoint || issue.field || 'NOT_AVAILABLE'}`).join('\n') || '- None';
  const mapLines = mappings.slice(0, 6).map((mapping: any) => {
    const frontend = mapping.frontend?.frontend_page || mapping.frontend?.service || 'Frontend';
    const api = mapping.api ? `${mapping.api.method} ${mapping.api.endpoint}` : mapping.frontend ? `${mapping.frontend.method} ${mapping.frontend.endpoint}` : 'API';
    const db = mapping.database_entity?.table || mapping.database_entity?.name || 'Database';
    return `- ${frontend} -> ${api} -> ${mapping.backend_model || 'Backend'} -> ${db} (${mapping.status || 'UNKNOWN'})`;
  }).join('\n') || '- NOT_AVAILABLE';
  const runtimeLines = runtimeResults.slice(0, 6).map((result: any) => {
    const status = result.status || 'UNKNOWN';
    const actual = result.actual_status ? `HTTP ${result.actual_status}` : result.request_status || 'NOT_SENT';
    return `- ${result.method || 'METHOD'} ${result.endpoint || 'endpoint'}: ${status} (${actual})`;
  }).join('\n') || '- NOT_CONFIGURED';
  const processLines = (state.runtime_processes || []).slice(0, 4).map((process: any) => `- ${process.name}: ${process.status || 'UNKNOWN'} ${process.url || ''}`).join('\n') || '- NOT_CONFIGURED';
  return `Full-Stack Contracts

Status: ${profile.status || 'UNKNOWN'}
API Contracts: ${profile.api_contracts?.length ?? 0}
Frontend API Usage: ${profile.frontend_api_usage?.length ?? 0}
Database Entities: ${profile.database_entities?.length ?? 0}
Issues: ${(issues?.length ?? profile.issues?.length) || 0}

Mappings:
${mapLines}

Contract Issues:
${issueLines}

Runtime Contract:
${runtimeLines}

Application Runtime:
Status: ${state.runtime_status || 'NOT_CONFIGURED'}
URL: ${state.runtime_base_url || 'NOT_CONFIGURED'}
${processLines}`;
}

function e2eValidationSummary(state: any) {
  const scenarios = state.e2e_scenarios || [];
  const results = state.e2e_results || [];
  const defects = state.defect_locations || [];
  const scenarioLines = scenarios.slice(0, 6).map((scenario: any) => {
    const result = results.find((item: any) => item.scenario_id === scenario.scenario_id);
    return `- ${scenario.scenario_id}: ${scenario.name} (${result?.status || 'PENDING'})`;
  }).join('\n') || '- NOT_CONFIGURED';
  const defectLines = defects.slice(0, 6).map((defect: any) => `- ${defect.layer || 'UNKNOWN'} ${defect.confidence || 'LOW'}: ${defect.issue || 'No issue text'}`).join('\n') || '- None';
  return `E2E Validation

Scenarios: ${scenarios.length}
Results: ${results.length}

Scenarios:
${scenarioLines}

Defect Localization:
${defectLines}`;
}

function repairSummary(state: any) {
  const plans = state.repair_plans || [];
  const results = state.repair_results || [];
  const targeted = state.targeted_verifications || [];
  const regressions = state.regression_results || [];
  const planLines = plans.slice(0, 6).map((plan: any) => `- ${plan.repair_id}: ${plan.status} ${plan.defect_location?.layer || ''} ${plan.affected_endpoint || plan.affected_files?.[0] || ''}`).join('\n') || '- None';
  const verificationLines = targeted.slice(0, 6).map((item: any) => `- ${item.repair_id}: ${item.validation_type} ${item.status}`).join('\n') || '- None';
  const regressionLines = regressions.slice(0, 6).map((item: any) => `- ${item.repair_id}: ${item.status}`).join('\n') || '- None';
  return `Repair & Verification

Repair Plans: ${plans.length}
Repair Results: ${results.length}

Repairs:
${planLines}

Targeted Verification:
${verificationLines}

Regression:
${regressionLines}`;
}

function deliveryDeploymentSummary(state: any) {
  const readiness = state?.release_readiness || {};
  const profile = state?.deployment_profile || {};
  const deployment = state?.deployment_result || {};
  const post = state?.post_deployment_verification || {};
  const rollback = state?.rollback_info || {};
  const artifacts = state?.deployment_artifacts || deployment.artifact_list || [];
  const gates = [
    `QA ${readiness.qa_status || 'NOT_AVAILABLE'}`,
    `Contracts ${readiness.contract_status || 'NOT_CONFIGURED'}`,
    `E2E ${readiness.e2e_status || 'NOT_CONFIGURED'}`,
    `Defects ${readiness.unresolved_defects ? 'UNRESOLVED' : 'RESOLVED'}`,
    `Build ${readiness.build_status || 'NOT_CONFIGURED'}`,
    `Secret Scan ${readiness.security_status || 'NOT_CONFIGURED'}`,
  ].map(item => `- ${item}`).join('\n');
  const artifactLines = artifacts.slice(0, 8).map((artifact: any) => `- ${artifact.artifact_type || 'artifact'}: ${artifact.path || 'NOT_AVAILABLE'} (${artifact.status || 'UNKNOWN'})`).join('\n') || '- NOT_CONFIGURED';
  const envLines = (profile.required_environment_variables || deployment.environment_requirements || []).slice(0, 8).map((env: any) => `- ${env.name} (${env.secret ? 'secret' : env.type || 'environment'}, ${env.required ? 'required' : 'optional'})`).join('\n') || '- NOT_CONFIGURED';
  return `Delivery & Deployment

Release Readiness
Status: ${readiness.status || 'NOT_AVAILABLE'}
${gates}

Deployment Target
${profile.target || deployment.deployment_target || 'NOT_CONFIGURED'}

Artifacts
${artifactLines}

Environment
${envLines}

Post-Deployment
Status: ${post.status || 'NOT_CONFIGURED'}
Health: ${post.application_health || 'NOT_CONFIGURED'}
API Smoke: ${post.api_health || 'NOT_CONFIGURED'}

Rollback
${rollback.rollback_status || 'NOT_CONFIGURED'}

Status
${readiness.status === 'READY' ? 'DELIVERY READY' : readiness.status || 'NOT_AVAILABLE'}`;
}

function evaluationSummary(state: any) {
  const evaluation = state?.evaluation_summary;
  if (!evaluation) return 'SEAM Evaluation\n\nStatus: NOT_AVAILABLE';
  const run = evaluation.run || {};
  const requirements = evaluation.requirements || {};
  const contracts = evaluation.contracts || {};
  const e2e = evaluation.e2e || {};
  const defects = evaluation.defects || {};
  const repairs = evaluation.repairs || {};
  const qa = evaluation.qa || {};
  const delivery = evaluation.delivery || {};
  const performance = evaluation.performance || {};
  const tools = evaluation.tools || [];
  const toolInvocations = run.tool_invocation_count ?? tools.reduce((total: number, tool: any) => total + (tool.tool_invocation_count || 0), 0);
  return `SEAM Evaluation

Requirements
Coverage: ${requirements.requirement_coverage ?? 'NOT_APPLICABLE'}

Contracts
Compliance: ${contracts.contract_compliance_rate ?? 'NOT_APPLICABLE'}

E2E
Pass: ${e2e.scenarios_passed ?? 0} / ${e2e.scenarios_executed ?? 0}

Defects
Found: ${defects.total_defects ?? 0}
Resolved: ${run.resolved_defect_count ?? repairs.successful_repairs ?? 0}

Repairs
Successful: ${repairs.successful_repairs ?? 0}
Resolution Rate: ${repairs.repair_resolution_rate ?? 'NOT_APPLICABLE'}

QA
${qa.final_qa_status || run.qa_status || 'NOT_AVAILABLE'}

Delivery
${delivery.release_ready ? 'READY' : delivery.release_blocked ? 'BLOCKED' : run.delivery_status || 'NOT_AVAILABLE'}

Execution
Duration: ${performance.total_workflow_duration_ms ?? run.duration_ms ?? 0} ms

Tool Invocations
${toolInvocations}`;
}

function experimentSummary(state: any) {
  const experiment = state?.experiment_summary;
  if (!experiment) return 'Experiment\n\nStatus: NOT_AVAILABLE';
  const latest = experiment.metrics?.[experiment.metrics.length - 1] || {};
  return `EXPERIMENT
${experiment.name || experiment.experiment_id || 'NOT_AVAILABLE'}

Scenario
${latest.scenario_id || 'NOT_AVAILABLE'}

Configuration
${latest.configuration_id || 'NOT_AVAILABLE'}

Runs
${experiment.run_count ?? 0}

Status
${experiment.status || 'NOT_AVAILABLE'}

Metrics
Requirement Coverage: ${latest.requirement_coverage ?? 'NOT_APPLICABLE'}
E2E Pass Rate: ${latest.e2e_pass_rate ?? 'NOT_APPLICABLE'}
Repair Resolution Rate: ${latest.repair_resolution_rate ?? 'NOT_APPLICABLE'}
Contract Compliance: ${latest.contract_compliance_rate ?? 'NOT_APPLICABLE'}`;
}

function finalSummary(state: any) {
  const tasks = Object.values(state?.tasks || {}) as any[];
  const completed = state?.completed_tasks?.length ?? tasks.filter(task => task.status === 'completed').length;
  const files = tasks.reduce((count, task: any) => count + (task.result?.files?.length || task.result?.generated_files?.length || 0), 0);
  return `Project generation completed.\n\nProject: ${state?.project_name || 'NOT_AVAILABLE'}\nScale: ${state?.scale_assessment?.scale_level || 'NOT_AVAILABLE'}\nAgents executed: 6\nTasks completed: ${completed}\nFiles generated: ${files || 'NOT_AVAILABLE'}\nQA: ${state?.latest_qa_status || 'NOT_AVAILABLE'}\nDelivery: ${state?.delivery_result?.status || 'NOT_AVAILABLE'}\nRelease readiness: ${state?.release_readiness?.status || 'NOT_AVAILABLE'}\nEvaluation: ${state?.evaluation_summary?.run?.status || 'NOT_AVAILABLE'}`;
}

function taskTitle(state: any, taskId?: string) {
  if (!taskId) return '';
  const task = state?.tasks?.[taskId] || state?.project_plan?.tasks?.find((item: any) => item.task_id === taskId);
  return task?.title || task?.description || '';
}
