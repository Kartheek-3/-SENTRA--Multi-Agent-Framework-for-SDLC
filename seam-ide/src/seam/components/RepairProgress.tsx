import React from 'react';

export type RepairStep =
  | 'DEFECT'
  | 'LOCALIZING'
  | 'ROOT CAUSE'
  | 'PATCH'
  | 'TARGETED VERIFICATION'
  | 'REGRESSION'
  | 'RESOLVED';

export type RepairProgressProps = {
  issueTitle: string;
  isResolved?: boolean;
  repairedCount?: number;
  regressionCount?: number;
  currentStep?: string;
  onViewDetails: () => void;
  onViewChanges?: () => void;
};

export const REPAIR_STEPS: string[] = [
  'DEFECT',
  'LOCALIZING',
  'ROOT CAUSE',
  'PATCH',
  'TARGETED VERIFICATION',
  'REGRESSION',
  'RESOLVED',
];

export function RepairProgress({
  issueTitle,
  isResolved = false,
  repairedCount = 1,
  regressionCount = 0,
  currentStep = 'LOCALIZING',
  onViewDetails,
  onViewChanges,
}: RepairProgressProps) {
  if (isResolved) {
    return (
      <div className="agentRepairResolvedCard" role="region" aria-label="Repair Complete">
        <div className="repairTop">
          <span className="repairTitle resolved">REPAIR COMPLETE ✓</span>
        </div>
        <div className="repairStatsText monospace">
          <span>{repairedCount} issue repaired</span>
          <span>•</span>
          <span>{regressionCount} regressions</span>
        </div>
        {onViewChanges && (
          <button type="button" className="repairActionBtn" onClick={onViewChanges}>
            View changes →
          </button>
        )}
      </div>
    );
  }

  const stepUpper = currentStep.toUpperCase();
  const currentIdx = Math.max(0, REPAIR_STEPS.findIndex(s => s === stepUpper || s.startsWith(stepUpper) || stepUpper.startsWith(s)));

  return (
    <div className="agentRepairActiveCard" role="region" aria-label="Autonomous Repair In Progress">
      <div className="repairTop">
        <span className="repairTitle active">REPAIRING</span>
        <span className="repairIssueName">{issueTitle}</span>
      </div>

      <div className="repairStepsRail">
        {REPAIR_STEPS.map((step, idx) => {
          const isPassed = idx < currentIdx;
          const isCurrent = idx === currentIdx;
          const glyph = isPassed ? '✓' : isCurrent ? '●' : '○';

          return (
            <div key={step} className={`repairStepChip ${isCurrent ? 'active' : isPassed ? 'passed' : 'pending'}`}>
              <span className="stepGlyph monospace">{glyph}</span>
              <span className="stepLabel">{step}</span>
            </div>
          );
        })}
      </div>

      <div className="repairCurrentActionRow monospace">
        <span className="rLabel">Current:</span>
        <span className="rVal">{currentStep} defect</span>
      </div>

      <button type="button" className="repairDetailsLinkBtn" onClick={onViewDetails}>
        View details →
      </button>
    </div>
  );
}
