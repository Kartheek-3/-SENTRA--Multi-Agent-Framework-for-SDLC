import React from 'react';

export type AgentRecommendationProps = {
  defectCount: number;
  workflowStatus: string;
  hasUnverifiedContracts?: boolean;
  onRunAction: (actionCommand: string) => Promise<void> | void;
  onDismiss: () => void;
  isDismissed: boolean;
};

export function AgentRecommendation({
  defectCount,
  workflowStatus,
  hasUnverifiedContracts = false,
  onRunAction,
  onDismiss,
  isDismissed,
}: AgentRecommendationProps) {
  if (isDismissed) return null;

  // Derive genuine recommendation based on backend state
  let actionTitle = 'Run Static Contract Audit';
  let reason = 'Frontend, API, and DB schema synchronization has not been verified against latest models.';
  let command = '/review';
  let badge = 'CONTRACT AUDIT';

  if (defectCount > 0) {
    actionTitle = `Execute Autonomous Defect Repair (${defectCount} issue${defectCount > 1 ? 's' : ''})`;
    reason = `QA Agent localized ${defectCount} test failure(s). Repair Center has candidate patches ready for targeted regression.`;
    command = '/repair';
    badge = 'DEFECT REPAIR';
  } else if (workflowStatus === 'COMPLETED' || workflowStatus === 'complete') {
    actionTitle = 'Evaluate Release Gates & Prepare Delivery';
    reason = 'All coding and QA validation passes are complete. Ready for artifact bundling and release certification.';
    command = '/deliver';
    badge = 'DELIVERY GATE';
  } else if (workflowStatus === 'IDLE' || workflowStatus === 'pending') {
    actionTitle = 'Formulate Architecture Plan & Diagrams';
    reason = 'Requirements analysis is complete. Generate 10 canonical architecture diagrams and engineering steps.';
    command = '/plan';
    badge = 'PLANNING';
  }

  return (
    <div className="agentRecommendationCard" role="region" aria-label="Autonomous Recommendation">
      <div className="recommendationHeader">
        <div className="recLabelCluster">
          <span className="recSparkle">✨</span>
          <span className="recHeading">NEXT ACTION</span>
        </div>
        <span className="recBadge monospace">{badge}</span>
      </div>

      <h4 className="recActionTitle">{actionTitle}</h4>
      <p className="recReasonBody">
        <span className="recWhyTag">WHY:</span> {reason}
      </p>

      <div className="recButtonsRow">
        <button
          type="button"
          className="recRunBtn"
          onClick={() => onRunAction(command)}
          title={`Execute recommendation (${command})`}
        >
          ▶ RUN
        </button>
        <button
          type="button"
          className="recDismissBtn"
          onClick={onDismiss}
          title="Dismiss this recommendation"
        >
          DISMISS
        </button>
      </div>
    </div>
  );
}
