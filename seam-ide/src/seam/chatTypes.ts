export type ChatRole = 'USER' | 'SEAM' | 'AGENT' | 'SYSTEM';
export type ChatType = 'MESSAGE' | 'THINKING' | 'PROGRESS' | 'TASK' | 'CODE' | 'FILE' | 'QA' | 'ERROR' | 'SUCCESS' | 'WARNING' | 'DIAGRAM' | 'SUMMARY';
export type ChatStatus = 'WAITING' | 'RUNNING' | 'COMPLETE' | 'FAILED' | 'BLOCKED' | 'NOT_AVAILABLE';

export type ChatArtifact = {
  kind: 'file' | 'diagram' | 'qa' | 'delivery' | 'architecture' | 'project';
  label: string;
  path?: string;
  action?: string;
};

export type ChatMessage = {
  id: string;
  timestamp: string;
  role: ChatRole;
  agent?: string;
  type: ChatType;
  content: string;
  status: ChatStatus;
  metadata?: Record<string, unknown>;
  taskId?: string;
  artifact?: ChatArtifact;
  severity?: 'INFO' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
};

export function nowIso() {
  return new Date().toISOString();
}
