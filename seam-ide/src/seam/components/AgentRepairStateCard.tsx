import React from 'react';

export type RepairStage =
  | 'DEFECT DETECTED'
  | 'LOCALIZING'
  | 'ROOT CAUSE'
  | 'REPAIR PLAN'
  | 'PATCHING'
  | 'TARGETED VERIFICATION'
  | 'REGRESSION'
  | 'RESOLVED';

export type AgentRepairStateCardProps = {
  defectLocations: any[];
  repairPlans: any[];
  onTriggerRepair: () => void;
  onOpenRepairCenter?: () => void;
};

const REPAIR_STEPS: RepairStage[] = [
  'DEFECT DETECTED',
  'LOCALIZING',
  'ROOT CAUSE',
  'REPAIR PLAN',
  'PATCHING',
  'TARGETED VERIFICATION',
  'REGRESSION',
  'RESOLVED',
];

export function AgentRepairStateCard({
  defectLocations,
  repairPlans,
  onTriggerRepair,
  onOpenRepairCenter,
}: AgentRepairStateCardProps) {
  if (defectLocations.length === 0) return null;

  const currentDefect = defectLocations[0] || {};
  // Derive repair stage:
  // If repairPlans exists and has candidate patch -> PATCHING or TARGETED VERIFICATION
  let activeStage: RepairStage = 'DEFECT DETECTED';
  if (repairPlans.length > 0) {
    activeStage = 'REPAIR PLAN';
  } else if (currentDefect.root_cause) {
    activeStage = 'ROOT CAUSE';
  } else if (currentDefect.file) {
    activeStage = 'LOCALIZING';
  }

  const activeIndex = REPAIR_STEPS.indexOf(activeStage);

  return (
    <div className="agentRepairStateCard" role="region" aria-label="Autonomous Defect Repair Progression">
      <div className="repairCardHeader">
        <div className="repairHeaderTitle">
          <span className="repairWarningPulse">⚠️</span>
          <strong>AUTONOMOUS REPAIR LOOP</strong>
        </div>
        <span className="repairDefectCount monospace">
          {defectLocations.length} DEFECT(S)
        </span>
      </div>

      {/* Lifecycle Flow Indicator */}
      <div className="repairProgressionStrip">
        {REPAIR_STEPS.map((step, idx) => {
          const isPassed = idx < activeIndex;
          const isCurrent = idx === activeIndex;
          return (
            <div
              key={step}
              className={`repairStepNode ${isPassed ? 'passed' : ''} ${isCurrent ? 'current' : 'pending'}`}
              title={step}
            >
              <div className="stepDot" />
              <span className="stepText">{step}</span>
            </div>
          );
        })}
      </div>

      {/* Defect Diagnostics */}
      <div className="repairDiagnosticBox">
        <div className="diagRow">
          <span className="diagKey">File:</span>
          <span className="diagVal monospace highlight">{currentDefect.file || 'src/auth/AuthContext.tsx'}</span>
        </div>
        <div className="diagRow">
          <span className="diagKey">Error Type:</span>
          <span className="diagVal monospace warn">{currentDefect.error_type || 'AssertionError / NullPointer'}</span>
        </div>
        <div className="diagRow">
          <span className="diagKey">Candidate Patch:</span>
          <span className="diagVal monospace">
            {repairPlans.length > 0 ? `${repairPlans.length} patch candidates ready` : 'Generating AST fix'}
          </span>
        </div>
      </div>

      <div className="repairActionRow">
        <button
          type="button"
          className="repairPrimaryBtn"
          onClick={onTriggerRepair}
          title="Apply candidate patch and verify"
        >
          ⚡ Execute Autonomous Repair
        </button>
        {onOpenRepairCenter && (
          <button
            type="button"
            className="repairSecondaryBtn"
            onClick={onOpenRepairCenter}
            title="Open dedicated Repair Center console"
          >
            Open Repair Center
          </button>
        )}
      </div>
    </div>
  );
}
