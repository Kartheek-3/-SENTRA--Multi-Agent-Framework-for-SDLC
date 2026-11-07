import React from 'react';

export type AgentTabId = 'PLAN' | 'ACTIVITY' | 'TOOLS' | 'FILES' | 'VERIFY' | 'LOGS';

export type AgentPanelTabsProps = {
  activeTab: AgentTabId;
  onSelectTab: (tab: AgentTabId) => void;
  planCount?: number;
  activityCount?: number;
  toolsCount?: number;
  filesCount?: number;
  verifyStatus?: 'PASS' | 'FAIL' | 'PENDING';
  hasApproval?: boolean;
};

const TABS: { id: AgentTabId; label: string }[] = [
  { id: 'PLAN', label: 'PLAN' },
  { id: 'ACTIVITY', label: 'ACTIVITY' },
  { id: 'TOOLS', label: 'TOOLS' },
  { id: 'FILES', label: 'FILES' },
  { id: 'VERIFY', label: 'VERIFY' },
  { id: 'LOGS', label: 'LOGS' },
];

export function AgentPanelTabs({
  activeTab,
  onSelectTab,
  planCount,
  activityCount,
  toolsCount,
  filesCount,
  verifyStatus = 'PASS',
  hasApproval = false,
}: AgentPanelTabsProps) {
  const getBadgeForTab = (tabId: AgentTabId) => {
    switch (tabId) {
      case 'PLAN':
        return planCount ? <span className="tabBadge monospace">{planCount}</span> : null;
      case 'ACTIVITY':
        return activityCount ? <span className="tabBadge monospace">{activityCount}</span> : null;
      case 'TOOLS':
        return hasApproval ? (
          <span className="tabBadge approvalPulse" title="Approval required">!</span>
        ) : toolsCount ? (
          <span className="tabBadge monospace">{toolsCount}</span>
        ) : null;
      case 'FILES':
        return filesCount ? <span className="tabBadge monospace">{filesCount}</span> : null;
      case 'VERIFY':
        return (
          <span className={`tabBadge verifyDot ${verifyStatus.toLowerCase()}`} title={`Verification: ${verifyStatus}`}>
            {verifyStatus === 'PASS' ? '✓' : verifyStatus === 'FAIL' ? '✕' : '●'}
          </span>
        );
      case 'LOGS':
      default:
        return null;
    }
  };

  return (
    <div className="agentTabsNav" role="tablist" aria-label="Agent Panel Navigation Tabs">
      {TABS.map(tab => {
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            role="tab"
            aria-selected={isActive}
            className={`agentTabBtn ${isActive ? 'active' : ''}`}
            onClick={() => onSelectTab(tab.id)}
            title={`Open ${tab.label} tab`}
          >
            <span className="tabLabelText">{tab.label}</span>
            {getBadgeForTab(tab.id)}
          </button>
        );
      })}
    </div>
  );
}
