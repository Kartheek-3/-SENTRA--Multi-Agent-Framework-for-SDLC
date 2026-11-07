import React from 'react';

export type ToolItem = {
  name: string;
  status: 'completed' | 'running' | 'failed' | 'pending';
  target?: string;
  duration?: string;
  details?: string;
};

export type ToolListProps = {
  tools?: ToolItem[];
  onSelectTool?: (tool: ToolItem) => void;
};

export function ToolList({ tools, onSelectTool }: ToolListProps) {
  if (!tools || tools.length === 0) {
    return (
      <div className="toolListMinimal">
        <div className="emptyStateSubtle monospace" style={{ padding: '8px 12px', color: 'var(--text-muted, #71717a)', fontSize: '11px' }}>
          No tools executed in current session (IDLE)
        </div>
      </div>
    );
  }

  const displayTools = tools;

  const getGlyph = (status: ToolItem['status']) => {
    switch (status) {
      case 'completed': return <span className="tGlyph pass">✓</span>;
      case 'running': return <span className="tGlyph run">●</span>;
      case 'failed': return <span className="tGlyph fail">×</span>;
      case 'pending':
      default: return <span className="tGlyph pending">○</span>;
    }
  };

  return (
    <div className="toolListMinimal">
      {displayTools.map((tool, idx) => (
        <div
          key={`${tool.name}-${idx}`}
          className={`toolRowMinimal ${tool.status}`}
          onClick={() => onSelectTool?.(tool)}
        >
          <div className="toolLeftCluster">
            {getGlyph(tool.status)}
            <span className="toolName monospace">{tool.name}</span>
          </div>

          <div className="toolRightCluster">
            {tool.duration && <span className="toolDuration monospace">{tool.duration}</span>}
            <button
              type="button"
              className="toolDetailsTrigger"
              onClick={e => {
                e.stopPropagation();
                onSelectTool?.(tool);
              }}
              title="View tool details"
            >
              Details →
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
