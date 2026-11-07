import React, { useState } from 'react';

export type AntigravityHUDProps = {
  state?: any;
  health?: any;
  events?: any[];
  onTriggerAction?: (actionName: string) => void;
  onOpenRepair?: () => void;
  onRunWorkflow?: () => void;
  onOpenAgent?: () => void;
};

export function AntigravityHUD({
  state,
  health,
  events,
  onTriggerAction,
  onOpenRepair,
  onRunWorkflow,
  onOpenAgent,
}: AntigravityHUDProps) {
  const [isDismissed, setIsDismissed] = useState<boolean>(false);
  const [menuOpen, setMenuOpen] = useState<boolean>(false);

  // Derive real state
  const isRunning = state?.workflow_status === 'running';
  const hasDefects = (state?.defect_locations?.length || 0) > 0;
  const currentAgent = state?.current_agent || (isRunning ? 'Coding' : 'Supervisor');
  const taskTitle = state?.current_task?.title || state?.current_task || (isRunning ? `Synthesizing artifacts` : 'Ready');
  const workflowStatus = state?.workflow_status || 'idle';

  // HUD state resolution (IDLE, RUNNING, WAITING, ERROR, SUCCESS)
  let statusBadge = '● SEAM';
  let statusGlyph = '●';
  let statusClass = 'hud-idle';
  let actionText = 'Ready for instructions';

  if (hasDefects) {
    statusBadge = '! SEAM';
    statusGlyph = '!';
    statusClass = 'hud-error';
    actionText = `${state.defect_locations.length} defect(s) detected`;
  } else if (isRunning) {
    statusBadge = '● SEAM';
    statusGlyph = '●';
    statusClass = 'hud-running';
    actionText = `${currentAgent} Agent: ${taskTitle}`;
  } else if (workflowStatus === 'completed') {
    statusBadge = '✓ SEAM';
    statusGlyph = '✓';
    statusClass = 'hud-success';
    actionText = 'Workflow complete';
  } else if (workflowStatus === 'waiting') {
    statusBadge = '◒ SEAM';
    statusGlyph = '◒';
    statusClass = 'hud-waiting';
    actionText = 'Waiting for approval';
  }

  if (isDismissed) {
    return (
      <aside
        className="antigravityFloatingReopenMini"
        onClick={() => setIsDismissed(false)}
        title="Open Antigravity HUD"
        aria-label="Reopen Antigravity HUD"
      >
        <span className="miniDot" />
        <span>SEAM HUD</span>
      </aside>
    );
  }

  return (
    <aside className="antigravityFloatingHUD" aria-label="Antigravity Autonomous Engineering HUD">
      <div className={`hudCardMinimal ${statusClass}`}>
        {/* Top Header Row */}
        <div className="hudHeaderRow">
          <div className="hudTitleCluster">
            <span className="hudStatusGlyph monospace">{statusGlyph}</span>
            <span className="hudBrandName">SEAM</span>
          </div>

          <div className="hudActionsCluster">
            <button
              type="button"
              className="hudIconBtn"
              onClick={() => setIsDismissed(true)}
              title="Hide HUD"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Current Action One-Liner */}
        <div className="hudActionBody" title={actionText}>
          <span className="hudActionText">{actionText}</span>
        </div>

        {/* Bottom Control Buttons */}
        <div className="hudFooterRow">
          <button
            type="button"
            className="hudOpenBtn"
            onClick={() => onOpenAgent ? onOpenAgent() : onTriggerAction?.('open_agent')}
            title="Open Agent Control Center"
          >
            Open Agent →
          </button>

          <div className="hudMoreWrapper">
            <button
              type="button"
              className="hudMoreBtn"
              onClick={() => setMenuOpen(!menuOpen)}
              title="More actions"
            >
              •••
            </button>

            {menuOpen && (
              <div className="hudDropdownMenu">
                <button
                  type="button"
                  onClick={() => {
                    setMenuOpen(false);
                    onRunWorkflow?.();
                  }}
                >
                  Run Autonomous Workflow
                </button>
                {hasDefects && onOpenRepair && (
                  <button
                    type="button"
                    onClick={() => {
                      setMenuOpen(false);
                      onOpenRepair();
                    }}
                  >
                    Open Repair Center
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => {
                    setMenuOpen(false);
                    setIsDismissed(true);
                  }}
                >
                  Dismiss HUD
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </aside>
  );
}
