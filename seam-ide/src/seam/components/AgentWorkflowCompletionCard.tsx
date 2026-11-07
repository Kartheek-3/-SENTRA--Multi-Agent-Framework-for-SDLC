import React from 'react';

export type AgentWorkflowCompletionCardProps = {
  onViewChanges?: () => void;
  onViewTests?: () => void;
  onViewArtifacts?: () => void;
  onOpenDelivery?: () => void;
};

const COMPLETED_CHECKLIST = [
  'Requirements',
  'Planning',
  'Coding',
  'QA',
  'Repair',
  'Regression',
  'Delivery',
];

export function AgentWorkflowCompletionCard({
  onViewChanges,
  onViewTests,
  onViewArtifacts,
  onOpenDelivery,
}: AgentWorkflowCompletionCardProps) {
  return (
    <div className="agentCompletionCard" role="region" aria-label="Workflow Completion Notice">
      <div className="completionHeader">
        <span className="completionCheckGlyph">✓</span>
        <div>
          <strong className="completionTitle">WORKFLOW COMPLETED</strong>
          <span className="completionSub">All autonomous engineering gates passed</span>
        </div>
      </div>

      <div className="completionChecklistGrid">
        {COMPLETED_CHECKLIST.map(item => (
          <div key={item} className="completionCheckItem">
            <span className="checkMark">✓</span>
            <span className="checkLabel">{item}</span>
          </div>
        ))}
      </div>

      <div className="completionButtonsRow">
        {onViewChanges && (
          <button type="button" className="compBtn" onClick={onViewChanges}>
            View Changes
          </button>
        )}
        {onViewTests && (
          <button type="button" className="compBtn" onClick={onViewTests}>
            View Tests
          </button>
        )}
        {onViewArtifacts && (
          <button type="button" className="compBtn" onClick={onViewArtifacts}>
            View Artifacts
          </button>
        )}
        {onOpenDelivery && (
          <button type="button" className="compBtn primary" onClick={onOpenDelivery}>
            Open Delivery
          </button>
        )}
      </div>
    </div>
  );
}
