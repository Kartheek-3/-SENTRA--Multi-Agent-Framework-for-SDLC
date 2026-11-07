import React from 'react';

export type TaskDetailModalProps = {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  stage: string;
  agent: string;
  status: string;
  priority?: string;
  description?: string;
  actionDetails?: string;
};

export function TaskDetailModal({
  isOpen,
  onClose,
  title,
  stage,
  agent,
  status,
  priority = 'HIGH',
  description,
  actionDetails,
}: TaskDetailModalProps) {
  if (!isOpen) return null;

  return (
    <div className="taskDetailModalOverlay" role="dialog" aria-modal="true" aria-label="Task Details">
      <div className="taskDetailModalBackdrop" onClick={onClose} />
      <div className="taskDetailModalContent">
        <div className="taskModalHeader">
          <div>
            <span className="taskModalEyebrow monospace">STAGE: {stage}</span>
            <h3 className="taskModalTitle">{title}</h3>
          </div>
          <button type="button" className="taskModalCloseBtn" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="taskModalGrid">
          <div className="modalGridItem">
            <span className="mKey">ASSIGNED AGENT:</span>
            <span className="mVal monospace highlight">{agent}</span>
          </div>
          <div className="modalGridItem">
            <span className="mKey">EXECUTION STATUS:</span>
            <span className="mVal monospace">{status}</span>
          </div>
          <div className="modalGridItem">
            <span className="mKey">PRIORITY LEVEL:</span>
            <span className="mVal monospace warn">{priority}</span>
          </div>
          <div className="modalGridItem">
            <span className="mKey">RUNTIME SCOPE:</span>
            <span className="mVal monospace">SANDBOXED</span>
          </div>
        </div>

        {description && (
          <div className="taskModalSection">
            <span className="sectionHeading">Task Scope & Objectives:</span>
            <p className="sectionParagraph">{description}</p>
          </div>
        )}

        {actionDetails && (
          <div className="taskModalSection monospace">
            <span className="sectionHeading">Current Action Context:</span>
            <div className="actionCodeBlock">{actionDetails}</div>
          </div>
        )}

        <div className="taskModalFooter">
          <button type="button" className="modalDismissBtn" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
