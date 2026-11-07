import React, { useState, useMemo } from 'react';

export type LogLevel = 'ALL' | 'INFO' | 'WARNING' | 'ERROR' | 'DEBUG';

export type LogItem = {
  id: string;
  timestamp: string;
  level: 'INFO' | 'WARNING' | 'ERROR' | 'DEBUG';
  agent?: string;
  message: string;
};

export type AgentLogDrawerProps = {
  isOpen: boolean;
  onClose: () => void;
  rawLogs: string[];
  onClearLogs?: () => void;
};

export function AgentLogDrawer({
  isOpen,
  onClose,
  rawLogs,
  onClearLogs,
}: AgentLogDrawerProps) {
  const [filterLevel, setFilterLevel] = useState<LogLevel>('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  const parsedLogs: LogItem[] = useMemo(() => {
    if (rawLogs.length > 0) {
      return rawLogs.map((logStr, idx) => {
        let level: LogItem['level'] = 'INFO';
        const lower = logStr.toLowerCase();
        if (lower.includes('error') || lower.includes('fail')) level = 'ERROR';
        else if (lower.includes('warn')) level = 'WARNING';
        else if (lower.includes('debug')) level = 'DEBUG';

        const timeMatch = logStr.match(/^\[(.*?)\]/);
        const timestamp = timeMatch ? timeMatch[1] : new Date().toLocaleTimeString();
        const cleanMsg = logStr.replace(/^\[.*?\]\s*/, '');

        return {
          id: `log-${idx}`,
          timestamp,
          level,
          message: cleanMsg,
        };
      });
    }

    return [
      { id: '1', timestamp: '10:42:15', level: 'INFO', agent: 'Supervisor', message: 'Autonomous session initialized.' },
      { id: '2', timestamp: '10:42:18', level: 'INFO', agent: 'Analysis Agent', message: 'Domain knowledge retrieved from ChromaDB / FastEmbed.' },
      { id: '3', timestamp: '10:42:24', level: 'DEBUG', agent: 'Planning Agent', message: 'Synthesized architectural diagrams.' },
      { id: '4', timestamp: '10:42:30', level: 'INFO', agent: 'Coding Agent', message: 'Modifying src/auth/AuthContext.tsx' },
      { id: '5', timestamp: '10:42:40', level: 'WARNING', agent: 'QA Agent', message: 'Contract schema parity verified with minor warning.' },
      { id: '6', timestamp: '10:42:55', level: 'INFO', agent: 'Delivery Agent', message: 'Ready for packaging.' },
    ];
  }, [rawLogs]);

  const filteredLogs = useMemo(() => {
    return parsedLogs.filter(l => {
      const matchLvl = filterLevel === 'ALL' || l.level === filterLevel;
      const matchSearch = !searchQuery.trim() || l.message.toLowerCase().includes(searchQuery.toLowerCase());
      return matchLvl && matchSearch;
    });
  }, [parsedLogs, filterLevel, searchQuery]);

  if (!isOpen) return null;

  return (
    <div className="agentLogDrawerOverlay" role="dialog" aria-modal="true" aria-label="System Log Drawer">
      <div className="agentLogDrawerBackdrop" onClick={onClose} />
      <div className="agentLogDrawerContent">
        {/* Drawer Header */}
        <div className="drawerHeader">
          <div className="drawerTitleCluster">
            <span className="drawerIcon">📋</span>
            <div>
              <h3 className="drawerTitle">ENGINEERING LOGS & TRACEABILITY</h3>
              <span className="drawerSub monospace">{filteredLogs.length} events matching filter</span>
            </div>
          </div>
          <button type="button" className="drawerCloseBtn" onClick={onClose} title="Close drawer">
            ✕
          </button>
        </div>

        {/* Toolbar: Filters, Search, Clear */}
        <div className="drawerToolbar">
          <div className="drawerFilterButtons">
            {(['ALL', 'INFO', 'WARNING', 'ERROR', 'DEBUG'] as LogLevel[]).map(lvl => (
              <button
                key={lvl}
                type="button"
                className={`drawerFilterBtn ${filterLevel === lvl ? 'active' : ''} ${lvl.toLowerCase()}`}
                onClick={() => setFilterLevel(lvl)}
              >
                {lvl}
              </button>
            ))}
          </div>

          <div className="drawerSearchBar">
            <input
              type="text"
              placeholder="Search logs..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="drawerSearchInput monospace"
            />
            {searchQuery && (
              <button type="button" className="clearSearchBtn" onClick={() => setSearchQuery('')}>
                ✕
              </button>
            )}
          </div>

          {onClearLogs && (
            <button type="button" className="drawerClearBtn" onClick={onClearLogs}>
              Clear
            </button>
          )}
        </div>

        {/* Log Stream */}
        <div className="drawerLogList monospace scrollArea">
          {filteredLogs.length === 0 ? (
            <div className="emptyLogsText">No matching log records.</div>
          ) : (
            filteredLogs.map(item => (
              <div key={item.id} className={`drawerLogRow ${item.level.toLowerCase()}`}>
                <span className="dTimestamp">{item.timestamp}</span>
                <span className={`dLevel ${item.level.toLowerCase()}`}>[{item.level}]</span>
                {item.agent && <span className="dAgent">&lt;{item.agent}&gt;</span>}
                <span className="dMessage">{item.message}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
