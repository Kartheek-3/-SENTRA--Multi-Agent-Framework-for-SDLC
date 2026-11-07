import React from 'react';

export type StageId =
  | 'Requirements'
  | 'Analysis'
  | 'Planning'
  | 'Coding'
  | 'QA'
  | 'Repair'
  | 'Delivery';

export type ProgressRailProps = {
  currentStage: string;
  hasDefects?: boolean;
  onSelectStage?: (stage: string) => void;
};

const STAGES: { id: StageId; shortLabel: string; viewTarget: string }[] = [
  { id: 'Requirements', shortLabel: 'Req', viewTarget: 'dashboard' },
  { id: 'Analysis', shortLabel: 'Analysis', viewTarget: 'dashboard' },
  { id: 'Planning', shortLabel: 'Planning', viewTarget: 'design' },
  { id: 'Coding', shortLabel: 'Coding', viewTarget: 'editor' },
  { id: 'QA', shortLabel: 'QA', viewTarget: 'testlab' },
  { id: 'Repair', shortLabel: 'Repair', viewTarget: 'repair' },
  { id: 'Delivery', shortLabel: 'Delivery', viewTarget: 'delivery' },
];

export function ProgressRail({ currentStage, hasDefects = false, onSelectStage }: ProgressRailProps) {
  const normCurrent = (currentStage || '').toLowerCase();

  const getStageStatus = (stage: StageId) => {
    const sLower = stage.toLowerCase();
    if (stage === 'Repair' && hasDefects) return 'current-warn';
    if (normCurrent.includes(sLower)) return 'current';

    const stageOrder: StageId[] = ['Requirements', 'Analysis', 'Planning', 'Coding', 'QA', 'Repair', 'Delivery'];
    const currentIdx = stageOrder.findIndex(s => normCurrent.includes(s.toLowerCase()));
    const thisIdx = stageOrder.indexOf(stage);

    if (currentIdx !== -1 && thisIdx < currentIdx) return 'completed';
    return 'pending';
  };

  const getGlyph = (status: string) => {
    switch (status) {
      case 'completed': return '✓';
      case 'current': return '●';
      case 'current-warn': return '!';
      case 'pending':
      default: return '○';
    }
  };

  return (
    <div className="agentProgressRail" role="region" aria-label="Workflow Stage Progress">
      <div className="progressRailHeader">
        <span className="sectionTitleSmall">PROGRESS</span>
      </div>

      <div className="progressRailList">
        {STAGES.map(stage => {
          const status = getStageStatus(stage.id);
          const glyph = getGlyph(status);
          const isCurrent = status === 'current' || status === 'current-warn';

          return (
            <button
              key={stage.id}
              type="button"
              className={`progressStageChip ${status} ${isCurrent ? 'active' : ''}`}
              onClick={() => onSelectStage?.(stage.viewTarget)}
              title={`Stage: ${stage.id} (${status}) — Click to open ${stage.viewTarget}`}
            >
              <span className="stageGlyph monospace">{glyph}</span>
              <span className="stageName">{stage.shortLabel}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
