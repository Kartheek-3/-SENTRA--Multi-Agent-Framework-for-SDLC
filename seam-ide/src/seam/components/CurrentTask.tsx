import React from 'react';

export type CurrentTaskProps = {
  title: string;
  description?: string;
  status: string;
  currentActionText?: string;
  onOpenDetails: () => void;
};

export function CurrentTask({
  title,
  description,
  status,
  currentActionText,
  onOpenDetails,
}: CurrentTaskProps) {
  const isExecuting = status === 'EXECUTING' || status === 'RUNNING';

  return (
    <div className="agentCurrentTaskCard" role="region" aria-label="Current Engineering Task">
      <div className="taskCardTop">
        <span className="taskCardEyebrow">CURRENT TASK</span>
        <span className={`taskStatusPill ${isExecuting ? 'executing' : 'idle'} monospace`}>
          {status || 'IDLE'}
        </span>
      </div>

      <h3 className="taskHeading" title={title}>
        {title}
      </h3>

      {description && (
        <p className="taskShortDescription">
          {description}
        </p>
      )}

      {currentActionText && (
        <div className="taskActionSnippet monospace">
          <span className="snippetLabel">Action:</span>
          <span className="snippetText">{currentActionText}</span>
        </div>
      )}

      <div className="taskCardActions">
        <button
          type="button"
          className="taskDetailsBtn"
          onClick={onOpenDetails}
          title="Open detailed task inspection"
        >
          View details →
        </button>
      </div>
    </div>
  );
}
