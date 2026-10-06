import React, { useState, useEffect, useRef } from 'react';

export type MenuAction = {
  label: string;
  shortcut?: string;
  action: () => void;
  separator?: boolean;
};

export type MenuSection = {
  title: string;
  items: MenuAction[];
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

  const menus: Record<string, MenuAction[]> = {
    File: [
      { label: 'Save', shortcut: 'Ctrl+S', action: () => { onSaveFile?.(); setActiveMenu(null); } },
      { label: 'Close Active Editor', shortcut: 'Ctrl+W', action: () => { setActiveMenu(null); } },
      { label: 'Quick Open...', shortcut: 'Ctrl+P', action: () => { onOpenCommandPalette(); setActiveMenu(null); } },
    ],
    Edit: [
      { label: 'Undo', shortcut: 'Ctrl+Z', action: () => { setActiveMenu(null); } },
      { label: 'Redo', shortcut: 'Ctrl+Y', action: () => { setActiveMenu(null); } },
      { label: 'Find in Files', shortcut: 'Ctrl+Shift+F', action: () => { onOpenCommandPalette(); setActiveMenu(null); } },
    ],
    Selection: [
      { label: 'Select All', shortcut: 'Ctrl+A', action: () => { setActiveMenu(null); } },
      { label: 'Expand Selection', shortcut: 'Shift+Alt+Right', action: () => { setActiveMenu(null); } },
    ],
    View: [
      { label: 'Command Palette...', shortcut: 'Ctrl+K', action: () => { onOpenCommandPalette(); setActiveMenu(null); } },
      { label: 'Toggle Primary Sidebar', shortcut: 'Ctrl+B', action: () => { onToggleSidebar?.(); setActiveMenu(null); } },
      { label: 'Toggle Terminal Panel', shortcut: 'Ctrl+`', action: () => { onToggleTerminal?.(); setActiveMenu(null); } },
      { label: 'Toggle SEAM Agent Panel', shortcut: 'Ctrl+J', action: () => { onToggleAgentPanel?.(); setActiveMenu(null); } },
      { label: 'Toggle Theme (Dark/Light)', action: () => { onToggleTheme?.(); setActiveMenu(null); } },
    ],
    Go: [
      { label: 'Go to File...', shortcut: 'Ctrl+P', action: () => { onOpenCommandPalette(); setActiveMenu(null); } },
      { label: 'Go to Symbol...', shortcut: 'Ctrl+Shift+O', action: () => { onOpenCommandPalette(); setActiveMenu(null); } },
    ],
    Run: [
      { label: 'Start SEAM Workflow', shortcut: 'Ctrl+Enter', action: () => { onRunWorkflow?.(); setActiveMenu(null); } },
      { label: 'Stop Workflow', action: () => { onStopWorkflow?.(); setActiveMenu(null); } },
    ],
    Terminal: [
      { label: 'New Terminal Session', shortcut: 'Ctrl+Shift+`', action: () => { onToggleTerminal?.(); setActiveMenu(null); } },
      { label: 'Clear Terminal Output', action: () => { setActiveMenu(null); } },
    ],
    Help: [
      { label: 'SEAM Documentation', action: () => { setActiveMenu(null); } },
      { label: 'About SEAM Framework v1.0.1', action: () => { alert('SEAM v1.0.1 — Autonomous Multi-Agent Framework for SDLC'); setActiveMenu(null); } },
    ],
  };

  return (
    <div className="vscodeTitleBar" ref={menuBarRef} role="menubar" aria-label="Application menu bar">
      {/* Left: App Logo & Menus */}
      <div className="vscodeTitleBarLeft">
        <div className="vscodeLogo" title="SEAM IDE">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M17.5 2.5L7 11.5L17.5 20.5V2.5Z" fill="#007acc" />
            <path d="M7 11.5L1.5 7L7 2.5V11.5Z" fill="#007acc" opacity="0.6" />
            <path d="M17.5 2.5L22.5 5.5V18.5L17.5 20.5V2.5Z" fill="#007acc" opacity="0.85" />
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

      {/* Right: Panel Toggles & Window Controls */}
      <div className="vscodeTitleBarRight">
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
