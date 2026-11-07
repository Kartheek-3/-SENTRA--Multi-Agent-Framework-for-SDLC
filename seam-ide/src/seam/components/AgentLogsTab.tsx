import React, { useState, useMemo } from 'react';

export type LogLevel = 'ALL' | 'INFO' | 'WARNING' | 'ERROR' | 'DEBUG';

export type LogEntry = {
  id: string;
  timestamp: string;
  level: 'INFO' | 'WARNING' | 'ERROR' | 'DEBUG';
  agent?: string;
  source?: string;
  message: string;
};

export type AgentLogsTabProps = {
  rawLogs?: string[];
  onClearLogs?: () => void;
};

export function AgentLogsTab({ rawLogs = [], onClearLogs }: AgentLogsTabProps) {
  const [filterLevel, setFilterLevel] = useState<LogLevel>('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Parse raw log strings or provide canonical defaults
  const parsedLogs: LogEntry[] = useMemo(() => {
    if (rawLogs.length > 0) {
      return rawLogs.map((logStr, idx) => {
        let level: LogEntry['level'] = 'INFO';
        if (logStr.toLowerCase().includes('error') || logStr.toLowerCase().includes('fail')) {
          level = 'ERROR';
        } else if (logStr.toLowerCase().includes('warn')) {
          level = 'WARNING';
        } else if (logStr.toLowerCase().includes('debug')) {
          level = 'DEBUG';
        }

        const timeMatch = logStr.match(/^\[(.*?)\]/);
        const timestamp = timeMatch ? timeMatch[1] : new Date().toLocaleTimeString();
        const cleanMsg = logStr.replace(/^\[.*?\]\s*/, '');

        return {
          id: `log-${idx}`,
          timestamp,
          level,
          agent: 'Supervisor',
          source: 'runtime',
          message: cleanMsg,
        };
      });
    }

    return [
      {
        id: 'log-1',
        timestamp: '10:42:15',
        level: 'INFO',
        agent: 'Supervisor',
        source: 'orchestrator',
        message: 'Initialized autonomous engineering session for project.',
      },
      {
        id: 'log-2',
        timestamp: '10:42:18',
        level: 'INFO',
        agent: 'Analysis Agent',
        source: 'rag_retrieval',
        message: 'Knowledge repository queried (ChromaDB + FastEmbed vectors).',
      },
      {
        id: 'log-3',
        timestamp: '10:42:24',
        level: 'INFO',
        agent: 'Planning Agent',
        source: 'design_studio',
        message: 'Synthesized 10 canonical system diagrams.',
      },
      {
        id: 'log-4',
        timestamp: '10:42:30',
        level: 'DEBUG',
        agent: 'Coding Agent',
        source: 'ast_engine',
        message: 'Resolved React context imports: src/auth/AuthContext.tsx',
      },
      {
        id: 'log-5',
        timestamp: '10:42:40',
        level: 'WARNING',
        agent: 'QA Agent',
        source: 'contract_validator',
        message: 'Minor schema discrepancy checked; automatically aligned with OpenAPI spec.',
      },
      {
        id: 'log-6',
        timestamp: '10:42:55',
        level: 'INFO',
        agent: 'Delivery Agent',
        source: 'release_gate',
        message: 'Targeted verification checks passing. Regression clean.',
      },
    ];
  }, [rawLogs]);

  // Filter logs by level and search
  const filteredLogs = useMemo(() => {
    return parsedLogs.filter(item => {
      const matchesLevel = filterLevel === 'ALL' || item.level === filterLevel;
      const matchesSearch =
        !searchQuery.trim() ||
        item.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (item.agent && item.agent.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (item.source && item.source.toLowerCase().includes(searchQuery.toLowerCase()));
      return matchesLevel && matchesSearch;
    });
  }, [parsedLogs, filterLevel, searchQuery]);

  return (
    <div className="agentLogsContainer" role="tabpanel" aria-label="Structured Agent Logs">
      {/* Controls & Filter Bar */}
      <div className="logsFilterBar">
        <div className="logsLevelButtons" role="group" aria-label="Log level filter">
          {(['ALL', 'INFO', 'WARNING', 'ERROR', 'DEBUG'] as LogLevel[]).map(lvl => (
            <button
              key={lvl}
              type="button"
              className={`logFilterBtn ${filterLevel === lvl ? 'active' : ''} ${lvl.toLowerCase()}`}
              onClick={() => setFilterLevel(lvl)}
            >
              {lvl}
            </button>
          ))}
        </div>

        {onClearLogs && (
          <button
            type="button"
            className="clearLogsBtn"
            onClick={onClearLogs}
            title="Clear all logs"
          >
            Clear
          </button>
        )}
      </div>

      {/* Search Input */}
      <div className="logsSearchBar">
        <span className="searchIcon">🔍</span>
        <input
          type="text"
          className="logsSearchInput monospace"
          placeholder="Filter logs by message, agent, or source..."
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
        />
        {searchQuery && (
          <button
            type="button"
            className="clearSearchBtn"
            onClick={() => setSearchQuery('')}
          >
            ✕
          </button>
        )}
      </div>

      {/* Structured Log List */}
      <div className="logsStreamList scrollArea monospace">
        {filteredLogs.length === 0 ? (
          <div className="emptyLogsNotice">
            <span>No log entries match the current filter.</span>
          </div>
        ) : (
          filteredLogs.map(item => (
            <div key={item.id} className={`logEntryRow ${item.level.toLowerCase()}`}>
              <span className="logTimestamp">{item.timestamp}</span>
              <span className={`logLevelBadge ${item.level.toLowerCase()}`}>
                {item.level}
              </span>
              {item.agent && (
                <span className="logAgentBadge">[{item.agent}]</span>
              )}
              {item.source && (
                <span className="logSourceBadge">({item.source})</span>
              )}
              <span className="logMessage">{item.message}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
