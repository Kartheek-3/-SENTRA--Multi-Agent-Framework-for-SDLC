import React, { useState, useEffect, useRef } from 'react';

export type MenuAction = {
  label: string;
  shortcut?: string;
  action: () => void;
  separator?: boolean;
};

export type VSCodeMenuBarProps = {
  projectName?: string;
  onOpenCommandPalette: () => void;
  onRunWorkflow?: () => void;
  onStopWorkflow?: () => void;
  onSaveFile?: () => void;
  onToggleSidebar?: () => void;
  onToggleTerminal?: () => void;
  onToggleAgentPanel?: () => void;
  onToggleTheme?: () => void;
  onGoHome?: () => void;
  onSelectConsole?: (page: string) => void;
  onOpenAccount?: () => void;
  userDisplayName?: string;
  userEmail?: string;
  activePath?: string;
};

export function VSCodeMenuBar({
  projectName = 'SEAM Workspace',
  onOpenCommandPalette,
  onRunWorkflow,
  onStopWorkflow,
  onSaveFile,
  onToggleSidebar,
  onToggleTerminal,
  onToggleAgentPanel,
  onToggleTheme,
  onGoHome,
  onSelectConsole,
  onOpenAccount,
  userDisplayName = 'SEAM Engineer',
  userEmail = 'engineer@seam.internal',
  activePath,
}: VSCodeMenuBarProps) {
  const [activeMenu, setActiveMenu] = useState<string | null>(null);
  const menuBarRef = useRef<HTMLDivElement>(null);

  // Close menu when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuBarRef.current && !menuBarRef.current.contains(event.target as Node)) {
        setActiveMenu(null);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Close menu on Escape
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setActiveMenu(null);
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const closeMenu = () => setActiveMenu(null);

  const menus: Record<string, MenuAction[]> = {
    File: [
      { label: 'Create New Project (Project Builder)...', shortcut: 'Ctrl+N', action: () => { onSelectConsole?.('builder'); closeMenu(); } },
      { label: 'Save File', shortcut: 'Ctrl+S', action: () => { onSaveFile?.(); closeMenu(); } },
      { label: 'Close Active Editor', shortcut: 'Ctrl+W', action: closeMenu },
      { label: 'Quick Open...', shortcut: 'Ctrl+P', action: () => { onOpenCommandPalette(); closeMenu(); } },
      { label: 'SEAM Landing Page', action: () => { onGoHome?.(); closeMenu(); } },
    ],
    Edit: [
      { label: 'Undo', shortcut: 'Ctrl+Z', action: closeMenu },
      { label: 'Redo', shortcut: 'Ctrl+Y', action: closeMenu },
      { label: 'Find in Files', shortcut: 'Ctrl+Shift+F', action: () => { onOpenCommandPalette(); closeMenu(); } },
    ],
    Selection: [
      { label: 'Select All', shortcut: 'Ctrl+A', action: closeMenu },
      { label: 'Expand Selection', shortcut: 'Shift+Alt+Right', action: closeMenu },
    ],
    View: [
      { label: 'Command Palette...', shortcut: 'Ctrl+K', action: () => { onOpenCommandPalette(); closeMenu(); } },
      { label: 'Project Builder (Create & Stacks)', action: () => { onSelectConsole?.('builder'); closeMenu(); } },
      { label: 'Toggle Primary Sidebar', shortcut: 'Ctrl+B', action: () => { onToggleSidebar?.(); closeMenu(); } },
      { label: 'Toggle Terminal Panel', shortcut: 'Ctrl+`', action: () => { onToggleTerminal?.(); closeMenu(); } },
      { label: 'Toggle SEAM Agent Panel', shortcut: 'Ctrl+J', action: () => { onToggleAgentPanel?.(); closeMenu(); } },
      { label: 'Design Studio (10 Diagrams)', action: () => { onSelectConsole?.('design'); closeMenu(); } },
      { label: 'Test Lab (17 Categories)', action: () => { onSelectConsole?.('testlab'); closeMenu(); } },
      { label: 'Contracts Console', action: () => { onSelectConsole?.('contracts'); closeMenu(); } },
      { label: 'Repair Center', action: () => { onSelectConsole?.('repair'); closeMenu(); } },
      { label: 'Runtime Console', action: () => { onSelectConsole?.('runtime'); closeMenu(); } },
      { label: 'Model Router & Hardware', action: () => { onSelectConsole?.('models'); closeMenu(); } },
      { label: 'Delivery Center', action: () => { onSelectConsole?.('delivery'); closeMenu(); } },
      { label: 'Toggle Theme (Dark/Light)', action: () => { onToggleTheme?.(); closeMenu(); } },
    ],
    Go: [
      { label: 'Go to File...', shortcut: 'Ctrl+P', action: () => { onOpenCommandPalette(); closeMenu(); } },
      { label: 'Go to Symbol...', shortcut: 'Ctrl+Shift+O', action: () => { onOpenCommandPalette(); closeMenu(); } },
    ],
    Run: [
      { label: 'Start SEAM Workflow', shortcut: 'Ctrl+Enter', action: () => { onRunWorkflow?.(); closeMenu(); } },
      { label: 'Stop Workflow', action: () => { onStopWorkflow?.(); closeMenu(); } },
      { label: 'Run Full Test Lab', action: () => { onSelectConsole?.('testlab'); closeMenu(); } },
    ],
    SEAM: [
      { label: 'SEAM: Analyze Requirements', action: () => { onSelectConsole?.('dashboard'); closeMenu(); } },
      { label: 'SEAM: Generate Architecture Plan', action: () => { onSelectConsole?.('design'); closeMenu(); } },
      { label: 'SEAM: Autonomous Coding Cycle', action: () => { onRunWorkflow?.(); closeMenu(); } },
      { label: 'SEAM: Run Full QA Verification', action: () => { onSelectConsole?.('testlab'); closeMenu(); } },
      { label: 'SEAM: Start Autonomous Repair', action: () => { onSelectConsole?.('repair'); closeMenu(); } },
      { label: 'SEAM: Review Release Gates', action: () => { onSelectConsole?.('delivery'); closeMenu(); } },
      { label: 'SEAM: Open Model Router', action: () => { onSelectConsole?.('models'); closeMenu(); } },
    ],
    Agents: [
      { label: 'Analysis Agent', action: () => { onSelectConsole?.('agents'); closeMenu(); } },
      { label: 'Planning & Design Agent', action: () => { onSelectConsole?.('design'); closeMenu(); } },
      { label: 'Supervisor Agent (Orchestration)', action: () => { onSelectConsole?.('dashboard'); closeMenu(); } },
      { label: 'Coding Agent', action: () => { onSelectConsole?.('editor'); closeMenu(); } },
      { label: 'QA Agent', action: () => { onSelectConsole?.('testlab'); closeMenu(); } },
      { label: 'Delivery Agent', action: () => { onSelectConsole?.('delivery'); closeMenu(); } },
    ],
    Tools: [
      { label: 'Tool Registry (39 Registered Native Tools)', action: () => { onSelectConsole?.('readiness'); closeMenu(); } },
      { label: 'Permission Engine (Sandboxed)', action: () => { onSelectConsole?.('settings'); closeMenu(); } },
      { label: 'ChromaDB Semantic Memory', action: () => { onSelectConsole?.('integrations'); closeMenu(); } },
      { label: 'Docker Model Runner (Port 12434)', action: () => { onSelectConsole?.('models'); closeMenu(); } },
    ],
    Terminal: [
      { label: 'New Terminal Session', shortcut: 'Ctrl+Shift+`', action: () => { onToggleTerminal?.(); closeMenu(); } },
      { label: 'Clear Terminal Output', action: closeMenu },
    ],
    Help: [
      { label: 'SEAM Architecture Documentation', action: closeMenu },
      { label: 'Keyboard Shortcuts Reference', action: () => { onOpenCommandPalette(); closeMenu(); } },
      { label: 'About SEAM Framework v1.0.1', action: () => { alert('SEAM v1.0.1 — Autonomous Multi-Agent Framework for SDLC\nConnected to FastAPI, Docker Model Runner & Firestore'); closeMenu(); } },
    ],
  };

  const initial = userDisplayName.charAt(0).toUpperCase();

  return (
    <div className="vscodeTitleBar" ref={menuBarRef} role="menubar" aria-label="Application menu bar">
      {/* Left: App Logo & Menus */}
      <div className="vscodeTitleBarLeft">
        <div className="vscodeLogo" title="SEAM IDE — Self-Evolving Autonomous Multi-Agent Framework" onClick={onGoHome} style={{ cursor: 'pointer', display: 'flex', alignItems: 'center' }}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="seamLogoGrad" x1="2" y1="2" x2="22" y2="22" gradientUnits="userSpaceOnUse">
                <stop stopColor="#38bdf8" />
                <stop offset="0.5" stopColor="#6366f1" />
                <stop offset="1" stopColor="#a855f7" />
              </linearGradient>
            </defs>
            <polygon points="12,2 21,7.2 21,16.8 12,22 3,16.8 3,7.2" stroke="url(#seamLogoGrad)" strokeWidth="1.75" fill="rgba(99,102,241,0.12)" strokeLinejoin="round" />
            <circle cx="12" cy="12" r="2.5" fill="#38bdf8" />
            <circle cx="12" cy="5" r="1.5" fill="#a855f7" />
            <circle cx="18" cy="8.5" r="1.5" fill="#6366f1" />
            <circle cx="18" cy="15.5" r="1.5" fill="#6366f1" />
            <circle cx="12" cy="19" r="1.5" fill="#a855f7" />
            <circle cx="6" cy="15.5" r="1.5" fill="#6366f1" />
            <circle cx="6" cy="8.5" r="1.5" fill="#6366f1" />
            <line x1="12" y1="12" x2="12" y2="5" stroke="#38bdf8" strokeWidth="1" strokeOpacity="0.6" />
            <line x1="12" y1="12" x2="18" y2="8.5" stroke="#38bdf8" strokeWidth="1" strokeOpacity="0.6" />
            <line x1="12" y1="12" x2="18" y2="15.5" stroke="#38bdf8" strokeWidth="1" strokeOpacity="0.6" />
            <line x1="12" y1="12" x2="12" y2="19" stroke="#38bdf8" strokeWidth="1" strokeOpacity="0.6" />
            <line x1="12" y1="12" x2="6" y2="15.5" stroke="#38bdf8" strokeWidth="1" strokeOpacity="0.6" />
            <line x1="12" y1="12" x2="6" y2="8.5" stroke="#38bdf8" strokeWidth="1" strokeOpacity="0.6" />
          </svg>
        </div>

        <nav className="vscodeMenuNav" aria-label="Main menu">
          {Object.keys(menus).map(menuKey => {
            const isOpen = activeMenu === menuKey;
            return (
              <div key={menuKey} className="vscodeMenuContainer">
                <button
                  className={`vscodeMenuTrigger ${isOpen ? 'active' : ''}`}
                  onClick={() => setActiveMenu(isOpen ? null : menuKey)}
                  onMouseEnter={() => {
                    if (activeMenu !== null) setActiveMenu(menuKey);
                  }}
                  aria-haspopup="true"
                  aria-expanded={isOpen}
                >
                  {menuKey}
                </button>

                {isOpen && (
                  <div className="vscodeDropdownMenu" role="menu">
                    {menus[menuKey].map((item, idx) => (
                      <button
                        key={`${item.label}-${idx}`}
                        className="vscodeDropdownItem"
                        role="menuitem"
                        onClick={item.action}
                      >
                        <span className="dropdownLabel">{item.label}</span>
                        {item.shortcut && <span className="dropdownShortcut">{item.shortcut}</span>}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </nav>
      </div>

      {/* Center: Command Center Search */}
      <div className="vscodeTitleBarCenter">
        <button
          className="vscodeCommandCenter"
          onClick={onOpenCommandPalette}
          title="Search files, actions and symbols (Ctrl+K)"
          aria-label="Command center"
        >
          <svg className="commandCenterIcon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <span className="commandCenterText">
            {projectName} {activePath ? `— ${activePath.split('/').pop()}` : ''}
          </span>
          <kbd className="commandCenterKbd">Ctrl+K</kbd>
        </button>
      </div>

      {/* Right: Quick Run, Account, Panel Toggles & Window Controls */}
      <div className="vscodeTitleBarRight">
        {/* Quick Run Workflow Button */}
        <button
          className="vscodeQuickRunBtn"
          onClick={onRunWorkflow}
          title="Start Autonomous Workflow (Ctrl+Enter)"
        >
          ▶ Run
        </button>

        {/* User Account Avatar */}
        <button
          className="vscodeUserBtn"
          onClick={onOpenAccount}
          title={`Signed in as ${userDisplayName} (${userEmail})`}
        >
          <span className="userAvatarGlyph">{initial}</span>
        </button>

        <div className="vscodeLayoutToggles">
          <button
            className="vscodeIconButton"
            onClick={onToggleSidebar}
            title="Toggle Primary Sidebar"
            aria-label="Toggle primary sidebar"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="18" height="18" rx="2" />
              <line x1="9" y1="3" x2="9" y2="21" />
            </svg>
          </button>
          <button
            className="vscodeIconButton"
            onClick={onToggleTerminal}
            title="Toggle Terminal Panel"
            aria-label="Toggle terminal panel"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="18" height="18" rx="2" />
              <line x1="3" y1="15" x2="21" y2="15" />
            </svg>
          </button>
          <button
            className="vscodeIconButton"
            onClick={onToggleAgentPanel}
            title="Toggle Agent Panel"
            aria-label="Toggle agent panel"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="18" height="18" rx="2" />
              <line x1="15" y1="3" x2="15" y2="21" />
            </svg>
          </button>
        </div>

        <div className="vscodeWindowControls" aria-hidden="true">
          <span className="windowCtrl minimize" title="Minimize">—</span>
          <span className="windowCtrl maximize" title="Maximize">□</span>
          <span className="windowCtrl close" title="Close">✕</span>
        </div>
      </div>
    </div>
  );
}
