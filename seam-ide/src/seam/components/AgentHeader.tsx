import React from 'react';
import { AgentStatus } from './AgentStatus';

export type AgentHeaderProps = {
  currentAgent: string;
  workflowStatus: string;
  modelName: string;
  providerName?: string;
  wsStatus: string;
  panelWidthMode: 'compact' | 'normal' | 'expanded';
  onWidthModeChange: (mode: 'compact' | 'normal' | 'expanded') => void;
  onRefresh?: () => void;
  onClose?: () => void;
};

export function AgentHeader({
  currentAgent,
  workflowStatus,
  modelName,
  providerName = 'LOCAL',
  wsStatus,
  panelWidthMode,
  onWidthModeChange,
  onRefresh,
  onClose,
}: AgentHeaderProps) {
  const isLive = wsStatus === 'CONNECTED';

  return (
    <header className="seamAgentHeaderMinimal" aria-label="SEAM Agent Header">
      {/* Top Row: SEAM ● | Current Agent | LIVE */}
      <div className="headerRowPrimary">
        <div className="headerLeftCluster">
          <span className="brandWordmark">SEAM</span>
          <AgentStatus status={workflowStatus} showText={false} />
        </div>

        <div className="headerCenterAgent" title={`${currentAgent} Agent`}>
          <span className="agentNameText">{currentAgent} Agent</span>
        </div>

        <div className="headerRightCluster">
          <span className={`livePill ${isLive ? 'online' : 'offline'}`} title={`WebSocket: ${wsStatus}`}>
            {isLive ? 'LIVE' : 'OFFLINE'}
          </span>
          {onClose && (
            <button
              type="button"
              className="headerCloseBtn"
              onClick={onClose}
              title="Collapse panel (Ctrl+Shift+A)"
              aria-label="Collapse panel"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* Bottom Sub-Row: Model, Provider, Sizing */}
      <div className="headerRowSecondary">
        <div className="modelTelemetryCompact monospace">
          <span className="modelNameTag">{modelName || 'qwen3:4b'}</span>
          <span className="providerTag">{providerName}</span>
        </div>

        <div className="headerWidthControls" role="group" aria-label="Panel size controls">
          <button
            type="button"
            className={`sizeBtn ${panelWidthMode === 'compact' ? 'active' : ''}`}
            onClick={() => onWidthModeChange('compact')}
            title="Compact width (280px)"
          >
            280
          </button>
          <button
            type="button"
            className={`sizeBtn ${panelWidthMode === 'normal' ? 'active' : ''}`}
            onClick={() => onWidthModeChange('normal')}
            title="Normal width (340px)"
          >
            340
          </button>
          <button
            type="button"
            className={`sizeBtn ${panelWidthMode === 'expanded' ? 'active' : ''}`}
            onClick={() => onWidthModeChange('expanded')}
            title="Expanded width (480px)"
          >
            480
          </button>
        </div>
      </div>
    </header>
  );
}
