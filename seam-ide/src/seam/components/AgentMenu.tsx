import React, { useState, useRef, useEffect } from 'react';

export type AgentMenuProps = {
  onTriggerCommand: (cmd: string) => void;
  onOpenLogs: () => void;
  onOpenSettings?: () => void;
  onStopWorkflow: () => void;
  isRunning: boolean;
};

export function AgentMenu({
  onTriggerCommand,
  onOpenLogs,
  onOpenSettings,
  onStopWorkflow,
  isRunning,
}: AgentMenuProps) {
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    if (open) document.addEventListener('mousedown', handleOutside);
    return () => document.removeEventListener('mousedown', handleOutside);
  }, [open]);

  const handleSelect = (action: () => void) => {
    setOpen(false);
    action();
  };

  return (
    <div className="agentMenuWrapper" ref={menuRef}>
      <button
        type="button"
        className="agentMoreBtn"
        onClick={() => setOpen(!open)}
        title="More agent actions & tools"
        aria-expanded={open}
        aria-haspopup="menu"
      >
        ⋯ More
      </button>

      {open && (
        <div className="agentDropdownMenu" role="menu">
          <div className="menuSectionLabel">QUICK WORKFLOWS</div>
          <button
            type="button"
            className="menuItemBtn"
            onClick={() => handleSelect(() => onTriggerCommand('/analyze'))}
            role="menuitem"
          >
            Analyze Requirements
          </button>
          <button
            type="button"
            className="menuItemBtn"
            onClick={() => handleSelect(() => onTriggerCommand('/plan'))}
            role="menuitem"
          >
            Plan Architecture
          </button>
          <button
            type="button"
            className="menuItemBtn"
            onClick={() => handleSelect(() => onTriggerCommand('/code'))}
            role="menuitem"
          >
            Synthesize Code
          </button>
          <button
            type="button"
            className="menuItemBtn"
            onClick={() => handleSelect(() => onTriggerCommand('/qa'))}
            role="menuitem"
          >
            Run QA Test Lab
          </button>
          <button
            type="button"
            className="menuItemBtn"
            onClick={() => handleSelect(() => onTriggerCommand('/repair'))}
            role="menuitem"
          >
            Defect Repair Loop
          </button>
          <button
            type="button"
            className="menuItemBtn"
            onClick={() => handleSelect(() => onTriggerCommand('/review'))}
            role="menuitem"
          >
            Review & Audit
          </button>
          <button
            type="button"
            className="menuItemBtn"
            onClick={() => handleSelect(() => onTriggerCommand('/deliver'))}
            role="menuitem"
          >
            Deliver & Package
          </button>

          <div className="menuDivider" />
          <div className="menuSectionLabel">DIAGNOSTICS & SYSTEM</div>
          <button
            type="button"
            className="menuItemBtn"
            onClick={() => handleSelect(onOpenLogs)}
            role="menuitem"
          >
            Open Full Log Drawer
          </button>
          {isRunning && (
            <button
              type="button"
              className="menuItemBtn danger"
              onClick={() => handleSelect(onStopWorkflow)}
              role="menuitem"
            >
              Stop Current Execution
            </button>
          )}
          {onOpenSettings && (
            <button
              type="button"
              className="menuItemBtn"
              onClick={() => handleSelect(onOpenSettings)}
              role="menuitem"
            >
              Workspace Settings
            </button>
          )}
        </div>
      )}
    </div>
  );
}
