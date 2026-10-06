import React, { useState } from 'react';
import { StatusCluster } from './StatusCluster';

export type AntigravityHUDProps = {
  state?: any;
  health?: any;
  events?: any[];
  onTriggerAction?: (actionName: string) => void;
  onOpenRepair?: () => void;
  onRunWorkflow?: () => void;
};

export function AntigravityHUD({
  state,
  health,
  events,
  onTriggerAction,
  onOpenRepair,
  onRunWorkflow,
}: AntigravityHUDProps) {
  const [isMinimized, setIsMinimized] = useState<boolean>(false);
  const [isDismissed, setIsDismissed] = useState<boolean>(false);

  // Derive dynamic context from real SEAM state
  const currentAgent = state?.current_agent || (state?.workflow_status === 'running' ? 'Coding' : 'Supervisor');
  const workflowStatus = (state?.workflow_status || 'READY').toUpperCase();
  const modelName = health?.docker_model_runner ? 'qwen3:4b (DMR)' : 'qwen3:4b (CPU)';
  
  // Real or contextual recommendation
  const hasDefects = (state?.defect_locations?.length || 0) > 0;
  const isRunning = state?.workflow_status === 'running';

  let title = 'Suggested period change';
  let message =
    "Antigravity noticed the 30d button is active, but the current period state is still '30d'. The agent recommends keeping the overview in sync with the selected period.";
  let primaryActionLabel = 'Sync Overview';
  let primaryActionHandler = () => onTriggerAction?.('sync_overview');

  if (hasDefects) {
    title = `Autonomous Defect Repair: ${state.defect_locations.length} finding(s)`;
    message = `QA Agent detected ${state.defect_locations.length} issue(s). Repair Center has candidate patches ready for review.`;
    primaryActionLabel = 'Review in Repair Center';
    primaryActionHandler = () => onOpenRepair?.();
  } else if (isRunning) {
    title = `${currentAgent} Agent Active`;
    message = `SEAM workflow is currently synthesizing artifacts under ${currentAgent} agent supervision.`;
    primaryActionLabel = 'Monitor Execution';
    primaryActionHandler = () => onTriggerAction?.('monitor');
  }

  if (isDismissed) {
    return (
      <aside
        className="antigravityFloatingReopen"
        onClick={() => setIsDismissed(false)}
        title="Open Antigravity Agent HUD"
        aria-label="Open Antigravity agent HUD"
      >
        <span className="chipPulsingDot" />
        <span>Antigravity HUD</span>
      </aside>
    );
  }

  if (isMinimized) {
    return (
      <aside className="antigravityHUDOverlay minimized" aria-label="Antigravity agent status" style={{ pointerEvents: 'auto', zIndex: 10000 }}>
        <button
          className="antigravityStatusChip"
          onClick={() => setIsMinimized(false)}
          title="Expand Antigravity HUD"
          aria-label="Expand Antigravity HUD"
          style={{ pointerEvents: 'auto' }}
        >
          <span className="chipPulsingDot" />
          <span className="chipText">2 suggestions ready (Click to expand)</span>
        </button>
      </aside>
    );
  }

  return (
    <aside className="antigravityHUDOverlay" aria-label="Antigravity agent assistant HUD">
      <div className="antigravityBottomRow">
        {/* Antigravity Agent Card */}
        <div className="antigravityAgentCard">
          <div className="agentCardHeader">
            <div className="agentIdentity">
              <div className="agentAvatar" aria-hidden="true">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 2a2 2 0 0 1 2 2v2a2 2 0 0 1-2 2 2 2 0 0 1-2-2V4a2 2 0 0 1 2-2z" />
                  <rect x="3" y="8" width="18" height="12" rx="2" />
                  <path d="M7 13h.01M17 13h.01M8 17h8" />
                </svg>
              </div>
              <div className="agentIdentityText">
                <span className="agentName">Antigravity</span>
                <span className="agentSub">v1.0.1 • {state?.project_name || 'orbit-dashboard'}</span>
              </div>
            </div>

            <div className="agentConfidenceBadge">
              <span className="confidenceDot" />
              <span>98% Confidence</span>
              <button
                className="hudMinimizeBtn"
                onClick={() => setIsMinimized(true)}
                title="Minimize HUD"
                aria-label="Minimize HUD"
              >
                _
              </button>
              <button
                className="hudCloseBtn"
                onClick={() => setIsDismissed(true)}
                title="Close HUD"
                aria-label="Close HUD"
              >
                ×
              </button>
            </div>
          </div>

          <div className="agentCardMessage">
            <h4 className="agentMessageTitle">{title}</h4>
            <p className="agentMessageBody">{message}</p>
          </div>

          <div className="agentCardActions">
            <button
              className="agentActionBtn primary"
              onClick={primaryActionHandler}
            >
              {primaryActionLabel}
            </button>
            <button
              className="agentActionBtn secondary"
              onClick={() => onRunWorkflow?.()}
            >
              Run SEAM Workflow
            </button>
            <button
              className="agentActionBtn ghost"
              onClick={() => setIsDismissed(true)}
            >
              Dismiss
            </button>
          </div>
        </div>

        {/* Antigravity Status Cluster */}
        <StatusCluster
          currentAgent={currentAgent}
          workflowStatus={workflowStatus}
          modelName={modelName}
          suggestionsCount={hasDefects ? state.defect_locations.length : 2}
          onOpenSuggestions={() => {}}
        />
      </div>
    </aside>
  );
}
