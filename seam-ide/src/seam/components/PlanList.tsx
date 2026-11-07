import React from 'react';

export type PlanItem = {
  id: string;
  title: string;
  agent: string;
  status: 'completed' | 'active' | 'pending' | 'blocked' | 'failed';
  summary?: string;
};

export type PlanListProps = {
  tasks: PlanItem[];
  isRunning: boolean;
  onOpenFullPlan?: () => void;
};

export function PlanList({ tasks, isRunning, onOpenFullPlan }: PlanListProps) {
  if (!tasks || tasks.length === 0) {
    return (
      <div className="planListMinimal">
        <div className="emptyStateSubtle monospace" style={{ padding: '8px 12px', color: 'var(--text-muted, #71717a)', fontSize: '11px' }}>
          {isRunning ? 'Synthesizing task graph...' : 'No planned tasks yet (IDLE)'}
        </div>
        {onOpenFullPlan && (
          <button type="button" className="detailsLinkBtn" onClick={onOpenFullPlan}>
            View architectural plan →
          </button>
        )}
      </div>
    );
  }

  const displayTasks = tasks;

  const getStatusIcon = (status: PlanItem['status']) => {
    switch (status) {
      case 'completed': return <span className="pIcon pass">✓</span>;
      case 'active': return <span className="pIcon active">●</span>;
      case 'blocked': return <span className="pIcon blocked">!</span>;
      case 'failed': return <span className="pIcon fail">×</span>;
      case 'pending':
      default: return <span className="pIcon pending">○</span>;
    }
  };

  return (
    <div className="planListMinimal">
      {displayTasks.map(task => (
        <div key={task.id} className={`planRowMinimal ${task.status}`}>
          <span className="planStatusCol">{getStatusIcon(task.status)}</span>
          <span className="planTitleCol">{task.title}</span>
          <span className="planAgentCol monospace">{task.agent.replace(' Agent', '')}</span>
        </div>
      ))}
      {onOpenFullPlan && (
        <button type="button" className="detailsLinkBtn" onClick={onOpenFullPlan}>
          View full architectural plan →
        </button>
      )}
    </div>
  );
}
