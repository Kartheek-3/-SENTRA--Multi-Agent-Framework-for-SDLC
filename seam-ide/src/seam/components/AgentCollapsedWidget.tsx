import React from 'react';

export type AgentCollapsedWidgetProps = {
  currentAgent: string;
  workflowStatus: string;
  onExpand: () => void;
};

export function AgentCollapsedWidget({
  currentAgent,
  workflowStatus,
  onExpand,
}: AgentCollapsedWidgetProps) {
  const isExecuting = workflowStatus === 'EXECUTING' || workflowStatus === 'RUNNING';

  return (
    <aside
      className="agentCollapsedEdgeWidget"
      onClick={onExpand}
      title="Expand SEAM Agent Panel (Ctrl+Shift+A)"
      role="button"
      tabIndex={0}
      onKeyDown={e => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onExpand();
        }
      }}
      aria-label="Expand SEAM Agent Panel"
    >
      <div className="collapsedBrand">
        <span className="collapsedGlyph">⚡</span>
        <span className="collapsedTitle">SEAM</span>
      </div>

      <div className={`collapsedStatusBadge ${isExecuting ? 'executing' : 'ready'}`}>
        <span className="collapsedPulseDot" aria-hidden="true" />
        <span className="collapsedStatusText">
          {isExecuting ? '● EXECUTING' : '✓ READY'}
        </span>
      </div>

      <div className="collapsedAgent monospace">
        {currentAgent || 'Supervisor'}
      </div>
    </aside>
  );
}
