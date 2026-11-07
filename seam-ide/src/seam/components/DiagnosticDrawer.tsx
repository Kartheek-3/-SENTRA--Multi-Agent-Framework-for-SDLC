import React from 'react';

export type DiagnosticDrawerProps = {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  category?: string;
  summary: string;
  technicalDetails?: string;
  onRetry?: () => void;
};

export function DiagnosticDrawer({
  isOpen,
  onClose,
  title = 'Environment Diagnostic Details',
  category = 'INFRASTRUCTURE / RUNTIME',
  summary,
  technicalDetails,
  onRetry,
}: DiagnosticDrawerProps) {
  if (!isOpen) return null;

  return (
    <div className="diagnosticDrawerOverlay" role="dialog" aria-modal="true" aria-label="Technical Diagnostics">
      <div className="diagnosticDrawerBackdrop" onClick={onClose} />
      <div className="diagnosticDrawerContent">
        <div className="diagHeader">
          <div className="diagHeaderTitles">
            <span className="diagCategory monospace">{category}</span>
            <h3 className="diagTitle">{title}</h3>
          </div>
          <button type="button" className="diagCloseBtn" onClick={onClose} title="Close diagnostics">
            ✕
          </button>
        </div>

        <div className="diagBody">
          <div className="diagSummaryCard">
            <span className="summaryLabel">Issue Summary:</span>
            <p className="summaryText">{summary}</p>
          </div>

          {technicalDetails && (
            <div className="diagTechnicalBlock">
              <div className="techHeaderRow">
                <span className="techLabel monospace">RAW ENVIRONMENT TRACE / STACK:</span>
                <button
                  type="button"
                  className="copyTechBtn monospace"
                  onClick={() => navigator.clipboard.writeText(technicalDetails)}
                >
                  Copy Trace
                </button>
              </div>
              <pre className="techPre monospace">{technicalDetails}</pre>
            </div>
          )}

          <div className="diagActionRow">
            {onRetry && (
              <button
                type="button"
                className="diagRetryBtn"
                onClick={() => {
                  onClose();
                  onRetry();
                }}
              >
                ↻ Retry Environment Probe
              </button>
            )}
            <button type="button" className="diagDismissBtn" onClick={onClose}>
              Dismiss
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
