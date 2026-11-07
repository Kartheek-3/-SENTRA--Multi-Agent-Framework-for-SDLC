import React from 'react';

export type AgentQuickActionsProps = {
  currentAgent: string;
  isRunning: boolean;
  onExecuteCommand: (cmd: string) => Promise<void> | void;
  onSelectAgent?: (agent: string) => void;
};

const QUICK_COMMANDS = [
  { id: 'analyze', label: 'Analyze', command: '/analyze', agent: 'Analysis Agent' },
  { id: 'plan', label: 'Plan', command: '/plan', agent: 'Planning Agent' },
  { id: 'code', label: 'Code', command: '/code', agent: 'Coding Agent' },
  { id: 'qa', label: 'QA', command: '/qa', agent: 'QA Agent' },
  { id: 'repair', label: 'Repair', command: '/repair', agent: 'Coding Agent' },
  { id: 'review', label: 'Review', command: '/review', agent: 'Supervisor' },
  { id: 'deliver', label: 'Deliver', command: '/deliver', agent: 'Delivery Agent' },
];

const RECENT_AGENTS = ['ANALYSIS', 'PLANNING', 'CODING', 'QA', 'DELIVERY'];

export function AgentQuickActions({
  currentAgent,
  isRunning,
  onExecuteCommand,
  onSelectAgent,
}: AgentQuickActionsProps) {
  const normalizedCurrent = (currentAgent || 'Supervisor').toUpperCase();

  return (
    <div className="agentQuickControlsSection" aria-label="Agent Quick Actions & Switcher">
      {/* 1. Agent Switcher Strip */}
      <div className="agentSwitcherStrip">
        <div className="switcherCurrent">
          <span className="swLabel">CURRENT:</span>
          <span className={`swBadge active ${isRunning ? 'pulse' : ''} monospace`}>
            {normalizedCurrent}
          </span>
        </div>

        <div className="switcherRecent">
          <span className="swLabel">RECENT:</span>
          <div className="recentAgentsList">
            {RECENT_AGENTS.map(agent => (
              <button
                key={agent}
                type="button"
                className={`recentAgentBtn monospace ${normalizedCurrent.includes(agent) ? 'executing' : ''}`}
                onClick={() => onSelectAgent?.(agent)}
                title={`Switch focus to ${agent} agent`}
              >
                {agent}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 2. Quick Workflow Action Buttons */}
      <div className="quickActionsRow" role="group" aria-label="Workflow quick triggers">
        {QUICK_COMMANDS.map(item => (
          <button
            key={item.id}
            type="button"
            className={`quickActionChip ${item.id === 'repair' ? 'repairChip' : ''}`}
            onClick={() => onExecuteCommand(item.command)}
            disabled={isRunning}
            title={`Trigger ${item.label} (${item.command}) via ${item.agent}`}
          >
            {item.label}
          </button>
        ))}
      </div>
    </div>
  );
}
