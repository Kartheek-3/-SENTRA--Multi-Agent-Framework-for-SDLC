import React from 'react';

export type StatusBarProps = {
  gitBranch?: string;
  isSyncing?: boolean;
  onSync?: () => void;
  errorCount?: number;
  warningCount?: number;
  onOpenProblems?: () => void;
  cursorLine?: number;
  cursorCol?: number;
  tabSize?: number;
  encoding?: string;
  lineEnding?: string;
  language?: string;
  formatter?: string;
  notificationCount?: number;
  onOpenNotifications?: () => void;
  remoteName?: string;
  onRemoteClick?: () => void;
};

export function StatusBar({
  gitBranch = 'release-v1.0.1',
  isSyncing = false,
  onSync,
  errorCount = 0,
  warningCount = 0,
  onOpenProblems,
  cursorLine = 1,
  cursorCol = 1,
  tabSize = 2,
  encoding = 'UTF-8',
  lineEnding = 'LF',
  language = 'TypeScript React',
  formatter = 'Prettier',
  notificationCount = 0,
  onOpenNotifications,
  remoteName = 'SEAM Local',
  onRemoteClick,
}: StatusBarProps) {
  return (
    <footer className="statusBar" role="status" aria-label="Editor Status Bar">
      {/* Left: Repository & Diagnostics Status */}
      <div className="statusBarLeft">
        {/* Remote Connection Pill */}
        <button
          className="statusRemotePill"
          onClick={onRemoteClick}
          title={`Connected to ${remoteName} (127.0.0.1:8000)`}
          aria-label={`Remote connection: ${remoteName}`}
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <polyline points="7 13 3 9 7 5" />
            <polyline points="17 11 21 15 17 19" />
          </svg>
          <span className="remoteLabel">{remoteName}</span>
        </button>

        {/* Git Branch */}
        <button
          className="statusBarBtn branchBtn"
          onClick={onSync}
          title={`Git Branch: ${gitBranch} (Click to synchronize)`}
          aria-label={`Git branch: ${gitBranch}`}
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="6" y1="3" x2="6" y2="15" />
            <circle cx="18" cy="6" r="3" />
            <circle cx="6" cy="18" r="3" />
            <path d="M18 9a9 9 0 0 1-9 9" />
          </svg>
          <span className="branchName">{gitBranch}</span>
          <svg
            className={`syncIcon ${isSyncing ? 'spinning' : ''}`}
            width="11"
            height="11"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <polyline points="23 4 23 10 17 10" />
            <polyline points="1 20 1 14 7 14" />
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
          </svg>
        </button>

        {/* Problems Summary */}
        <button
          className="statusBarBtn problemsBtn"
          onClick={onOpenProblems}
          title={`${errorCount} Errors, ${warningCount} Warnings`}
          aria-label={`Problems: ${errorCount} errors, ${warningCount} warnings`}
        >
          <span className="errorIcon" aria-hidden="true">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <circle cx="12" cy="12" r="10" />
              <line x1="15" y1="9" x2="9" y2="15" />
              <line x1="9" y1="9" x2="15" y2="15" />
            </svg>
          </span>
          <span className="errorCount">{errorCount}</span>

          <span className="warningIcon" aria-hidden="true">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
              <line x1="12" y1="9" x2="12" y2="13" />
              <line x1="12" y1="17" x2="12.01" y2="17" />
            </svg>
          </span>
          <span className="warningCount">{warningCount}</span>
        </button>
      </div>

      {/* Right: Editor Status & Utilities */}
      <div className="statusBarRight">
        {/* Line & Column */}
        <span className="statusBarItem" title="Current Cursor Position">
          Ln {cursorLine}, Col {cursorCol}
        </span>

        {/* Spaces / Indentation */}
        <span className="statusBarItem" title="Indentation Size">
          Spaces: {tabSize}
        </span>

        {/* Encoding */}
        <span className="statusBarItem" title="File Encoding">
          {encoding}
        </span>

        {/* Line Ending */}
        <span className="statusBarItem" title="Line Sequence Separator">
          {lineEnding}
        </span>

        {/* Language Mode */}
        <span className="statusBarItem language" title="Language Mode">
          {language}
        </span>

        {/* Formatter */}
        <span className="statusBarItem formatter" title={`Code Formatter: ${formatter}`}>
          <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <polyline points="20 6 9 17 4 12" />
          </svg>
          <span>{formatter}</span>
        </span>

        {/* Notifications */}
        <button
          className="statusBarBtn notificationsBtn"
          onClick={onOpenNotifications}
          title={`${notificationCount} Notifications`}
          aria-label="Notifications"
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
            <path d="M13.73 21a2 2 0 0 1-3.46 0" />
          </svg>
        </button>
      </div>
    </footer>
  );
}
