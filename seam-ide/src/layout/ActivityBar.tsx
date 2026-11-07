import React, { useState } from 'react';

export type ActivityTool =
  | 'explorer'
  | 'search'
  | 'git'
  | 'debug'
  | 'modules'
  | 'account'
  | 'settings';

export type ActivityBarProps = {
  activeTool: string;
  onSelectTool: (tool: string) => void;
  gitBranch?: string;
  modifiedCount?: number;
  defectCount?: number;
  onOpenCommandPalette?: () => void;
  onOpenSettings?: () => void;
  onSelectConsole?: (page: string) => void;
  onOpenAccount?: () => void;
  userInitial?: string;
};

export function ActivityBar({
  activeTool,
  onSelectTool,
  gitBranch = 'final-validation',
  modifiedCount = 0,
  defectCount = 0,
  onOpenCommandPalette,
  onOpenSettings,
  onSelectConsole,
  onOpenAccount,
  userInitial = 'S',
}: ActivityBarProps) {
  const [modulesMenuOpen, setModulesMenuOpen] = useState(false);

  const consoles = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'design', label: 'Design Studio (10 Diagrams)', icon: '📐' },
    { id: 'testlab', label: 'Test Lab (17 Categories)', icon: '🧪' },
    { id: 'contracts', label: 'Contracts (Drift Detector)', icon: '📜' },
    { id: 'repair', label: 'Autonomous Defect Repair', icon: '🔧' },
    { id: 'runtime', label: 'Runtime Console', icon: '⚡' },
    { id: 'models', label: 'Model Control Panel', icon: '🧠' },
    { id: 'delivery', label: 'Delivery Center', icon: '📦' },
    { id: 'evaluation', label: 'Evaluation Console', icon: '📈' },
    { id: 'experiments', label: 'Experiments Console', icon: '🔬' },
    { id: 'integrations', label: 'Integrations Manager', icon: '🔌' },
    { id: 'readiness', label: 'Readiness & Health', icon: '🛡️' },
  ];

  return (
    <aside className="activityBar" role="navigation" aria-label="Activity Bar">
      {/* Top action icons */}
      <div className="activityBarTop">
        {/* Explorer */}
        <button
          className={`activityBarItem ${activeTool === 'explorer' ? 'active' : ''}`}
          onClick={() => onSelectTool('explorer')}
          title="Explorer (Files, Open Editors, Outline)"
          aria-label="Explorer"
          aria-pressed={activeTool === 'explorer'}
        >
          {activeTool === 'explorer' && <div className="activityActiveIndicator" />}
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
            <polyline points="10 9 9 9 8 9" />
          </svg>
        </button>

        {/* Search */}
        <button
          className={`activityBarItem ${activeTool === 'search' ? 'active' : ''}`}
          onClick={() => onSelectTool('search')}
          title="Search in files (Ctrl+Shift+F)"
          aria-label="Search"
          aria-pressed={activeTool === 'search'}
        >
          {activeTool === 'search' && <div className="activityActiveIndicator" />}
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
        </button>

        {/* Source Control */}
        <button
          className={`activityBarItem ${activeTool === 'git' ? 'active' : ''}`}
          onClick={() => onSelectTool('git')}
          title={`Source Control (${gitBranch})`}
          aria-label="Source Control"
          aria-pressed={activeTool === 'git'}
        >
          {activeTool === 'git' && <div className="activityActiveIndicator" />}
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
            <line x1="6" y1="3" x2="6" y2="15" />
            <circle cx="18" cy="6" r="3" />
            <circle cx="6" cy="18" r="3" />
            <path d="M18 9a9 9 0 0 1-9 9" />
          </svg>
          {modifiedCount > 0 && <span className="activityBadge">{modifiedCount}</span>}
        </button>

        {/* Run & Debug / Runtime */}
        <button
          className={`activityBarItem ${activeTool === 'debug' ? 'active' : ''}`}
          onClick={() => onSelectTool('debug')}
          title="Run & Debug / Runtime Services"
          aria-label="Run & Debug"
          aria-pressed={activeTool === 'debug'}
        >
          {activeTool === 'debug' && <div className="activityActiveIndicator" />}
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
            <polygon points="5 3 19 12 5 21 5 3" />
          </svg>
          {defectCount > 0 && <span className="activityBadge warning">{defectCount}</span>}
        </button>

        {/* SEAM Consoles & Modules Dropdown */}
        <div className="activityBarModulesContainer">
          <button
            className={`activityBarItem ${activeTool === 'modules' || modulesMenuOpen ? 'active' : ''}`}
            onClick={() => setModulesMenuOpen(!modulesMenuOpen)}
            title="SEAM Consoles & Architecture Modules"
            aria-label="SEAM Consoles"
            aria-haspopup="true"
            aria-expanded={modulesMenuOpen}
          >
            {(activeTool === 'modules' || modulesMenuOpen) && <div className="activityActiveIndicator" />}
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
              <rect x="3" y="3" width="7" height="7" />
              <rect x="14" y="3" width="7" height="7" />
              <rect x="14" y="14" width="7" height="7" />
              <rect x="3" y="14" width="7" height="7" />
            </svg>
          </button>

          {modulesMenuOpen && (
            <div className="activityModulesMenu" role="menu">
              <div className="modulesMenuHeader">SEAM ARCHITECTURE CONSOLES</div>
              {consoles.map(c => (
                <button
                  key={c.id}
                  className="modulesMenuItem"
                  role="menuitem"
                  onClick={() => {
                    onSelectConsole?.(c.id);
                    setModulesMenuOpen(false);
                  }}
                >
                  <span className="modulesMenuIcon">{c.icon}</span>
                  <span className="modulesMenuLabel">{c.label}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Bottom action icons */}
      <div className="activityBarBottom">
        {/* User Account */}
        <button
          className="activityBarItem"
          onClick={onOpenAccount}
          title="User Account & Firebase Profile"
          aria-label="User Account"
        >
          <div className="activityUserAvatar">
            <span>{userInitial}</span>
          </div>
        </button>

        {/* Settings */}
        <button
          className="activityBarItem"
          onClick={onOpenSettings}
          title="Settings (Ctrl+,)"
          aria-label="Settings"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
          </svg>
        </button>
      </div>
    </aside>
  );
}
