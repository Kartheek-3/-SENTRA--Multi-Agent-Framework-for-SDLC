import React from 'react';

export type CurrentActionProps = {
  verb: string; // e.g. "Editing", "Running", "Verifying", "Waiting"
  target: string; // e.g. "src/auth/AuthContext.tsx", "Authentication tests", "Approval required"
  onViewActivity: () => void;
  onOpenTarget?: (path: string) => void;
};

export function CurrentAction({
  verb,
  target,
  onViewActivity,
  onOpenTarget,
}: CurrentActionProps) {
  const isFilePath = target.includes('.') || target.includes('/');

  return (
    <div className="agentCurrentActionSection" role="region" aria-label="Current Engineering Action">
      <div className="actionSectionTop">
        <span className="sectionTitleSmall">CURRENT ACTION</span>
        <button
          type="button"
          className="viewActivityBtn"
          onClick={onViewActivity}
          title="Open activity stream"
        >
          View activity →
        </button>
      </div>

      <div className="actionContentRow">
        <span className="actionVerb monospace">{verb}</span>
        {isFilePath && onOpenTarget ? (
          <button
            type="button"
            className="actionTargetLink monospace"
            onClick={() => onOpenTarget(target)}
            title={`Open ${target} in editor`}
          >
            {target}
          </button>
        ) : (
          <span className="actionTargetText monospace">{target}</span>
        )}
      </div>
    </div>
  );
}
