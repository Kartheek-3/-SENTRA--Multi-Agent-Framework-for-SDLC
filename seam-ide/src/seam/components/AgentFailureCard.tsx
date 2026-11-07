import React from 'react';

export type AgentFailureCardProps = {
  agent: string;
  taskTitle: string;
  errorSummary: string;
  affectedTarget?: string;
  verificationState?: string;
  onRetry: () => void;
  onRepair: () => void;
  onViewLogs: () => void;
  onOpenFile?: (path: string) => void;
};

export function AgentFailureCard({
  agent,
  taskTitle,
  errorSummary,
  affectedTarget,
  verificationState = 'FAILED',
  onRetry,
  onRepair,
  onViewLogs,
  onOpenFile,
}: AgentFailureCardProps) {
  return (
    <div className="agentFailureCard" role="alert" aria-label="Workflow Failure Alert">
      <div className="failureHeader">
        <span className="failureWarningGlyph">✕</span>
        <div>
          <strong className="failureTitle">WORKFLOW FAILED</strong>
          <span className="failureSub">Autonomous execution interrupted</span>
        </div>
      </div>

      <div className="failureDetailsGrid">
        <div className="failureItem">
          <span className="failKey">AGENT:</span>
          <span className="failVal monospace">{agent}</span>
        </div>
        <div className="failureItem">
          <span className="failKey">TASK:</span>
          <span className="failVal">{taskTitle}</span>
        </div>
        <div className="failureItem">
          <span className="failKey">VERIFICATION:</span>
          <span className="failVal statusFail monospace">{verificationState}</span>
        </div>
        {affectedTarget && (
          <div className="failureItem">
            <span className="failKey">TARGET:</span>
            {onOpenFile ? (
              <button
                type="button"
                className="failTargetBtn monospace"
                onClick={() => onOpenFile(affectedTarget)}
              >
                📄 {affectedTarget}
              </button>
            ) : (
              <span className="failVal monospace">{affectedTarget}</span>
            )}
          </div>
        )}
      </div>

      <div className="failureErrorBox monospace">
        <span className="errorLabel">Error:</span>
        <pre className="errorText">{errorSummary}</pre>
      </div>

      <div className="failureActionsRow">
        <button type="button" className="failBtn retryBtn" onClick={onRetry}>
          ↻ Retry
        </button>
        <button type="button" className="failBtn repairBtn" onClick={onRepair}>
          ⚡ Repair
        </button>
        <button type="button" className="failBtn logsBtn" onClick={onViewLogs}>
          View Logs
        </button>
        {affectedTarget && onOpenFile && (
          <button
            type="button"
            className="failBtn fileBtn"
            onClick={() => onOpenFile(affectedTarget)}
          >
            Open File
          </button>
        )}
      </div>
    </div>
  );
}
