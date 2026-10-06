import React, { useState } from 'react';

export type TerminalSession = {
  id: string;
  name: string;
  type: 'shell' | 'vite' | 'backend' | 'agent';
  badge?: string;
  active?: boolean;
};

export type TerminalSessionSelectorProps = {
  logs: string[];
  state?: any;
  onClearLogs?: () => void;
  activeTab?: string;
  onSelectTab?: (tab: string) => void;
};

export function TerminalSessionSelector({
  logs,
  state,
  onClearLogs,
  activeTab = 'TERMINAL',
  onSelectTab,
}: TerminalSessionSelectorProps) {
  const [sessions, setSessions] = useState<TerminalSession[]>([
    { id: 'session-1', name: '1: zsh (dev)', type: 'shell' },
    { id: 'session-2', name: '2: vite (port 4173)', type: 'vite', badge: 'RUNNING' },
    { id: 'session-3', name: '3: seam-backend (8000)', type: 'backend', badge: 'LIVE' },
  ]);
  const [activeSessionId, setActiveSessionId] = useState<string>('session-1');
  const [panelTab, setPanelTab] = useState<string>(activeTab);
  const [commandInput, setCommandInput] = useState<string>('');
  const [localHistory, setLocalHistory] = useState<string[]>([]);

  const handleTabClick = (tab: string) => {
    setPanelTab(tab);
    onSelectTab?.(tab);
  };

  const handleCommandSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!commandInput.trim()) return;
    const cmd = commandInput.trim();
    setLocalHistory(prev => [...prev, `➜ seam-workspace git:(feature/final-hardening) ${cmd}`]);
    if (cmd === 'clear') {
      setLocalHistory([]);
      onClearLogs?.();
    } else if (cmd === 'help') {
      setLocalHistory(prev => [...prev, 'Available commands: run, stop, status, clear, pytest, help']);
    } else {
      setLocalHistory(prev => [...prev, `[seam-terminal] Command executed: ${cmd}`]);
    }
    setCommandInput('');
  };

  const addSession = () => {
    const nextId = `session-${sessions.length + 1}`;
    const nextSession: TerminalSession = {
      id: nextId,
      name: `${sessions.length + 1}: zsh`,
      type: 'shell',
    };
    setSessions(prev => [...prev, nextSession]);
    setActiveSessionId(nextId);
  };

  const removeSession = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (sessions.length <= 1) return;
    setSessions(prev => prev.filter(s => s.id !== id));
    if (activeSessionId === id) {
      setActiveSessionId(sessions[0].id);
    }
  };

  const defectCount = state?.defect_locations?.length || 0;

  return (
    <div className="terminalContainer" role="region" aria-label="Integrated Terminal">
      {/* Panel Header */}
      <div className="terminalPanelHeader">
        <div className="terminalPanelTabs" role="tablist">
          {['PROBLEMS', 'OUTPUT', 'DEBUG CONSOLE', 'TERMINAL', 'PORTS'].map(tab => {
            const isActive = panelTab === tab;
            return (
              <button
                key={tab}
                role="tab"
                aria-selected={isActive}
                className={`terminalPanelTab ${isActive ? 'active' : ''}`}
                onClick={() => handleTabClick(tab)}
              >
                <span>{tab}</span>
                {tab === 'PROBLEMS' && defectCount > 0 && (
                  <span className="problemsBadge">{defectCount}</span>
                )}
                {isActive && <div className="activeTabIndicator" />}
              </button>
            );
          })}
        </div>

        {/* Header Actions */}
        <div className="terminalActions">
          <button className="terminalActionBtn" onClick={addSession} title="New Terminal Session (Ctrl+Shift+`)">
            +
          </button>
          <button className="terminalActionBtn" onClick={() => onClearLogs?.()} title="Clear Output">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
            </svg>
          </button>
        </div>
      </div>

      {/* Terminal Body with Sessions Sidebar and Shell Output */}
      <div className="terminalBody">
        {/* Terminal Sessions Column */}
        <div className="terminalSessionsColumn" aria-label="Terminal sessions">
          <div className="sessionsHeader">SESSIONS</div>
          {sessions.map(s => {
            const isSelected = s.id === activeSessionId;
            return (
              <div
                key={s.id}
                className={`terminalSessionItem ${isSelected ? 'active' : ''}`}
                onClick={() => setActiveSessionId(s.id)}
                role="button"
                tabIndex={0}
              >
                <span className="terminalSessionIcon">❯</span>
                <span className="terminalSessionName">{s.name}</span>
                {s.badge && <span className="sessionBadge">{s.badge}</span>}
                {sessions.length > 1 && (
                  <button
                    className="sessionCloseBtn"
                    onClick={(e) => removeSession(s.id, e)}
                    title="Kill session"
                  >
                    ×
                  </button>
                )}
              </div>
            );
          })}
        </div>

        {/* Terminal Output Area */}
        <div className="terminalContentArea">
          {panelTab === 'TERMINAL' && (
            <div className="terminalShellView scrollArea">
              {/* Default Mock / Live Vite Server startup banner from Figma */}
              <div className="terminalOutputLine prompt">
                ➜ seam-workspace git:(feature/final-hardening) npm run dev
              </div>
              <div className="terminalOutputLine muted">
                &gt; seam-ide@0.1.0 dev<br />
                &gt; vite --host 127.0.0.1 --port 4173<br />
                <span className="textSuccess">  VITE v5.4.0  ready in 186 ms</span><br />
                &nbsp;&nbsp;➜  Local:&nbsp;&nbsp;&nbsp;http://127.0.0.1:4173/<br />
                &nbsp;&nbsp;➜  Backend: http://127.0.0.1:8000/
              </div>

              {/* Real logs stream */}
              {logs.map((log, idx) => (
                <div key={idx} className="terminalOutputLine">
                  {log}
                </div>
              ))}

              {/* Local session history */}
              {localHistory.map((item, idx) => (
                <div key={`hist-${idx}`} className="terminalOutputLine history">
                  {item}
                </div>
              ))}

              {/* Interactive prompt input */}
              <form onSubmit={handleCommandSubmit} className="terminalPromptRow">
                <span className="terminalPromptLabel">➜ seam-workspace git:(final-hardening)</span>
                <input
                  type="text"
                  className="terminalInput"
                  value={commandInput}
                  onChange={(e) => setCommandInput(e.target.value)}
                  placeholder="type 'help' or command..."
                  aria-label="Terminal command input"
                />
              </form>
            </div>
          )}

          {panelTab === 'PROBLEMS' && (
            <div className="terminalProblemsView scrollArea">
              {defectCount > 0 ? (
                state.defect_locations.map((defect: any, idx: number) => (
                  <div key={idx} className="problemRow">
                    <span className="problemSeverity">⚠</span>
                    <span className="problemFile">{defect.file_path || 'unknown'}</span>
                    <span className="problemDesc">{defect.description || defect.defect_type}</span>
                  </div>
                ))
              ) : (
                <div className="emptyProblems">✓ No problems detected in the current workspace.</div>
              )}
            </div>
          )}

          {panelTab === 'OUTPUT' && (
            <div className="terminalShellView scrollArea">
              <div className="terminalOutputLine muted">[SEAM Output Channel] Connected to EventBus daemon.</div>
              {logs.slice(-50).map((l, i) => (
                <div key={i} className="terminalOutputLine">{l}</div>
              ))}
            </div>
          )}

          {panelTab === 'DEBUG CONSOLE' && (
            <div className="terminalShellView scrollArea">
              <div className="terminalOutputLine muted">[Debug Console] Attached to Python 3.14 debugger on 127.0.0.1:8000.</div>
            </div>
          )}

          {panelTab === 'PORTS' && (
            <div className="terminalPortsView">
              <div className="portRow"><span>8000</span><span>FastAPI Backend (Uvicorn)</span><span className="textSuccess">ONLINE</span></div>
              <div className="portRow"><span>4173</span><span>Vite Preview IDE</span><span className="textSuccess">ONLINE</span></div>
              <div className="portRow"><span>12434</span><span>Docker Model Runner (DMR)</span><span className="textSuccess">RUNNING</span></div>
              <div className="portRow"><span>11434</span><span>Ollama Runtime</span><span className="textSuccess">LISTENING</span></div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
