import React from 'react';

export type AgentStatusType =
  | 'IDLE'
  | 'THINKING'
  | 'PLANNING'
  | 'EXECUTING'
  | 'WAITING'
  | 'VERIFYING'
  | 'REPAIRING'
  | 'COMPLETED'
  | 'FAILED';

export type AgentStatusProps = {
  status: AgentStatusType | string;
  showText?: boolean;
};

export function AgentStatus({ status, showText = true }: AgentStatusProps) {
  const norm = (status || 'IDLE').toUpperCase();

  // Subtle animated glyphs from specification:
  // IDLE ●, THINKING ◌, PLANNING ◐, EXECUTING ●, WAITING ◒, VERIFYING ◌, REPAIRING ◉, COMPLETED ✓, FAILED ×
  let glyph = '●';
  let statusClass = 'status-idle';

  switch (norm) {
    case 'THINKING':
      glyph = '◌';
      statusClass = 'status-thinking';
      break;
    case 'PLANNING':
      glyph = '◐';
      statusClass = 'status-planning';
      break;
    case 'EXECUTING':
    case 'RUNNING':
      glyph = '●';
      statusClass = 'status-executing';
      break;
    case 'WAITING':
    case 'APPROVAL REQUIRED':
      glyph = '◒';
      statusClass = 'status-waiting';
      break;
    case 'VERIFYING':
      glyph = '◌';
      statusClass = 'status-verifying';
      break;
    case 'REPAIRING':
      glyph = '◉';
      statusClass = 'status-repairing';
      break;
    case 'COMPLETED':
    case 'COMPLETE':
      glyph = '✓';
      statusClass = 'status-completed';
      break;
    case 'FAILED':
    case 'ERROR':
      glyph = '×';
      statusClass = 'status-failed';
      break;
    case 'IDLE':
    default:
      glyph = '●';
      statusClass = 'status-idle';
      break;
  }

  return (
    <span className={`agentStatusIndicator ${statusClass}`} title={`Status: ${norm}`} aria-label={`Status: ${norm}`}>
      <span className="statusGlyph" aria-hidden="true">{glyph}</span>
      {showText && <span className="statusLabel">{norm}</span>}
    </span>
  );
}
