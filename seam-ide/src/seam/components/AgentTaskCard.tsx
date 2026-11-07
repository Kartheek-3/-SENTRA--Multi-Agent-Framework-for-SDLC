import React from 'react';

export type AgentTaskCardProps = {
  currentTaskTitle?: string;
  stage: string;
  agentName: string;
  priority?: string;
  status: string;
  completedTasksCount: number;
  totalTasksCount: number;
  defectCount: number;
  repairPlanCount: number;
};

export function AgentTaskCard({
  currentTaskTitle,
  stage,
  agentName,
  priority = 'HIGH',
  status,
  completedTasksCount,
  totalTasksCount,
  defectCount,
  repairPlanCount,
}: AgentTaskCardProps) {
  const percent = totalTasksCount > 0 ? Math.min(100, Math.round((completedTasksCount / totalTasksCount) * 100)) : 0;
  const isExecuting = status === 'EXECUTING' || status === 'RUNNING';

  const defaultTask = isExecuting
    ? `Autonomous execution in progress: ${stage}`
    : 'System standby — Ready for autonomous engineering instruction';

  const displayTitle = currentTaskTitle || defaultTask;

  return (
    <section className="agentTaskCard" aria-label="Current Autonomous Task Details">
      <div className="taskCardHeaderRow">
        <span className="taskCardSubheading">CURRENT TASK</span>
        <span className={`taskPriorityBadge priority-${(priority || 'medium').toLowerCase()}`}>
          {priority.toUpperCase()}
        </span>
      </div>

      <h3 className="taskCardTitle" title={displayTitle}>
        {displayTitle}
      </h3>

      {/* Meta Grid: Stage, Agent, Status */}
      <div className="taskMetaGrid">
        <div className="taskMetaItem">
          <span className="metaLabel">STAGE</span>
          <span className="metaValue monospace">{stage || 'STANDBY'}</span>
        </div>
        <div className="taskMetaItem">
          <span className="metaLabel">AGENT</span>
          <span className="metaValue highlight monospace">{agentName || 'SUPERVISOR'}</span>
        </div>
        <div className="taskMetaItem">
          <span className="metaLabel">STATUS</span>
          <span className={`metaValue status-${(status || 'idle').toLowerCase()}`}>
            {status || 'IDLE'}
          </span>
        </div>
      </div>

      {/* Progress Track */}
      <div className="taskProgressSection">
        <div className="taskProgressLabelRow">
          <span className="progressLabel">EXECUTION PROGRESS</span>
          <span className="progressPercent monospace">
            {completedTasksCount} / {totalTasksCount} tasks ({percent}%)
          </span>
        </div>
        <div className="taskProgressTrack">
          <div
            className={`taskProgressFill ${isExecuting ? 'pulsing' : ''}`}
            style={{ width: `${percent}%` }}
          />
        </div>
      </div>

      {/* Quality & Defect Strip */}
      <div className="taskQualityStrip">
        <div className="qualityBadgeItem">
          <span className="qLabel">Quality Gate:</span>
          <span className={`qValue ${defectCount === 0 ? 'pass' : 'fail'}`}>
            {defectCount === 0 ? '✓ PASS' : `⚠️ ${defectCount} DEFECT(S)`}
          </span>
        </div>
        <div className="qualityBadgeItem">
          <span className="qLabel">Repair Cycles:</span>
          <span className="qValue monospace">{repairPlanCount}</span>
        </div>
      </div>
    </section>
  );
}
