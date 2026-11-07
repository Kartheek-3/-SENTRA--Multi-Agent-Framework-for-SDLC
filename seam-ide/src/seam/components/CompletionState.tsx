import React from 'react';

export type CompletionStateProps = {
  workflowName?: string;
  onOpenResult: () => void;
  onViewDetails: () => void;
};

export function CompletionState({
  workflowName = 'Autonomous Engineering Workflow',
  onOpenResult,
  onViewDetails,
}: CompletionStateProps) {
  const steps = [
    { label: 'Analysis', done: true },
    { label: 'Coding', done: true },
    { label: 'QA', done: true },
    { label: 'Repair', done: true },
    { label: 'Regression', done: true },
  ];

  return (
    <div className="agentCompletionMinimalCard" role="region" aria-label="Workflow Complete">
      <div className="completionTop">
        <span className="completionBadge">✓ WORKFLOW COMPLETE</span>
      </div>

      <h4 className="completionWorkflowName">{workflowName}</h4>

      <div className="completionMiniChecklist">
        {steps.map(s => (
          <div key={s.label} className="completionMiniRow">
            <span className="stepText">{s.label}</span>
            <span className="stepPassGlyph">✓</span>
          </div>
        ))}
      </div>

      <div className="completionActionsRow">
        <button type="button" className="completionPrimaryBtn" onClick={onOpenResult}>
          Open result
        </button>
        <button type="button" className="completionSecondaryBtn" onClick={onViewDetails}>
          View details →
        </button>
      </div>
    </div>
  );
}
