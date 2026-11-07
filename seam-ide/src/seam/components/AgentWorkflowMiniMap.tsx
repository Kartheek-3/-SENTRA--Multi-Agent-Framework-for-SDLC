import React from 'react';

export type WorkflowStage =
  | 'REQUIREMENTS'
  | 'ANALYSIS'
  | 'PLANNING'
  | 'CODING'
  | 'QA'
  | 'REPAIR'
  | 'DELIVERY';

export type AgentWorkflowMiniMapProps = {
  currentStage: string;
  onSelectStage?: (stage: string) => void;
  hasDefects?: boolean;
};

const STAGES: { id: WorkflowStage; label: string; viewTarget?: string }[] = [
  { id: 'REQUIREMENTS', label: 'REQ', viewTarget: 'dashboard' },
  { id: 'ANALYSIS', label: 'ANL', viewTarget: 'dashboard' },
  { id: 'PLANNING', label: 'PLAN', viewTarget: 'design' },
  { id: 'CODING', label: 'CODE', viewTarget: 'editor' },
  { id: 'QA', label: 'QA', viewTarget: 'testlab' },
  { id: 'REPAIR', label: 'RPR', viewTarget: 'repair' },
  { id: 'DELIVERY', label: 'DLV', viewTarget: 'delivery' },
];

export function AgentWorkflowMiniMap({
  currentStage,
  onSelectStage,
  hasDefects = false,
}: AgentWorkflowMiniMapProps) {
  // Normalize current stage string
  const normalized = (currentStage || '').toUpperCase();

  const getStageStatus = (stageId: WorkflowStage) => {
    if (stageId === 'REPAIR' && hasDefects) {
      return 'activeWarn';
    }
    if (normalized.includes(stageId)) {
      return 'active';
    }
    const stageOrder: WorkflowStage[] = [
      'REQUIREMENTS',
      'ANALYSIS',
      'PLANNING',
      'CODING',
      'QA',
      'REPAIR',
      'DELIVERY',
    ];
    const currentIndex = stageOrder.findIndex(s => normalized.includes(s));
    const thisIndex = stageOrder.indexOf(stageId);
    if (currentIndex !== -1 && thisIndex < currentIndex) {
      return 'completed';
    }
    return 'pending';
  };

  return (
    <div className="agentWorkflowMiniMap" role="navigation" aria-label="Workflow Lifecycle Strip">
      <div className="miniMapHeader">
        <span className="miniMapLabel">LIFECYCLE PIPELINE</span>
        <span className="miniMapCurrent">STAGE: {normalized || 'IDLE'}</span>
      </div>

      <div className="miniMapStrip">
        {STAGES.map((stage, idx) => {
          const status = getStageStatus(stage.id);
          return (
            <React.Fragment key={stage.id}>
              <button
                type="button"
                className={`miniMapNode ${status}`}
                onClick={() => onSelectStage?.(stage.viewTarget || stage.id.toLowerCase())}
                title={`Lifecycle stage: ${stage.id} (Click to open ${stage.viewTarget || 'view'})`}
                aria-label={`Lifecycle stage ${stage.id}`}
              >
                <span className="nodeDot" />
                <span className="nodeLabel">{stage.label}</span>
              </button>
              {idx < STAGES.length - 1 && (
                <span className={`miniMapConnector ${status === 'completed' ? 'passed' : ''}`} aria-hidden="true">
                  ›
                </span>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}
