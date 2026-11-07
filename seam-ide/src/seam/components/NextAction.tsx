import React from 'react';

export type NextActionProps = {
  label: string;
  command: string;
  onRun: (cmd: string) => void;
};

export function NextAction({ label, command, onRun }: NextActionProps) {
  return (
    <div className="agentNextActionSection" role="region" aria-label="Next Suggested Action">
      <div className="nextActionTop">
        <span className="sectionTitleSmall">NEXT</span>
      </div>

      <div className="nextActionRow">
        <span className="nextActionLabel">{label}</span>
        <button
          type="button"
          className="nextRunBtn"
          onClick={() => onRun(command)}
          title={`Execute next action (${command})`}
        >
          ▶ Run
        </button>
      </div>
    </div>
  );
}
