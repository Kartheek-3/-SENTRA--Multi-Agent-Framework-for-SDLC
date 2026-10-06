import React from 'react';

export type StatusClusterProps = {
  currentAgent?: string;
  workflowStatus?: string;
  modelName?: string;
  suggestionsCount?: number;
  onOpenSuggestions?: () => void;
};

export function StatusCluster({
  currentAgent = 'Supervisor',
  workflowStatus = 'READY',
  modelName = 'qwen3:4b-instruct',
  suggestionsCount = 2,
  onOpenSuggestions,
}: StatusClusterProps) {
  return (
    <div className="antigravityStatusCluster" aria-label="Agent status cluster">
      {/* Status Card */}
      <div className="antigravityStatusCard">
        <div className="statusCardHeader">AGENT STATUS</div>
        <div className="statusCardRow">
          <span className="statusDot green" />
          <span className="statusRowLabel">Agent:</span>
          <span className="statusRowValue">{currentAgent}</span>
        </div>
        <div className="statusCardRow">
          <span className="statusDot blue" />
          <span className="statusRowLabel">State:</span>
          <span className="statusRowValue">{workflowStatus}</span>
        </div>
        <div className="statusCardRow">
          <span className="statusDot purple" />
          <span className="statusRowLabel">Runtime:</span>
          <span className="statusRowValue">{modelName}</span>
        </div>
      </div>

      {/* Status Chip (Pill) */}
      <button
        className="antigravityStatusChip"
        onClick={onOpenSuggestions}
        title="View suggestions"
        aria-label={`${suggestionsCount} suggestions ready`}
      >
        <span className="chipPulsingDot" />
        <span className="chipText">{suggestionsCount} suggestions ready</span>
      </button>
    </div>
  );
}
