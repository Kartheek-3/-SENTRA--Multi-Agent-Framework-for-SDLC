import React from 'react';

export type TabItem = {
  path: string;
  isDirty?: boolean;
};

export type EditorTabsProps = {
  tabs: TabItem[];
  activePath: string;
  onSelectTab: (path: string) => void;
  onCloseTab: (path: string) => void;
  onSplitEditor?: () => void;
  onMoreActions?: () => void;
};

export function EditorTabs({
  tabs,
  activePath,
  onSelectTab,
  onCloseTab,
  onSplitEditor,
  onMoreActions,
}: EditorTabsProps) {
  const getFileIcon = (name: string) => {
    if (name.endsWith('.tsx') || name.endsWith('.jsx')) {
      return <span className="tabIconSpan react">⚛</span>;
    }
    if (name.endsWith('.ts') || name.endsWith('.js')) {
      return <span className="tabIconSpan ts">TS</span>;
    }
    if (name.endsWith('.json')) {
      return <span className="tabIconSpan json">{`{}`}</span>;
    }
    if (name.endsWith('.css') || name.endsWith('.scss')) {
      return <span className="tabIconSpan css">#</span>;
    }
    if (name.endsWith('.py')) {
      return <span className="tabIconSpan python">🐍</span>;
    }
    if (name.endsWith('.md')) {
      return <span className="tabIconSpan md">📄</span>;
    }
    return <span className="tabIconSpan generic">📄</span>;
  };

  return (
    <div className="editorTabsBar" role="tablist" aria-label="Editor Tabs">
      <div className="editorTabsScrollArea">
        {tabs.map(tab => {
          const fileName = tab.path.split('/').pop() || tab.path;
          const isActive = tab.path === activePath;
          return (
            <div
              key={tab.path}
              role="tab"
              aria-selected={isActive}
              className={`editorTabItem ${isActive ? 'active' : ''}`}
              onClick={() => onSelectTab(tab.path)}
              title={tab.path}
            >
              <div className="tabFileDetails">
                {getFileIcon(fileName)}
                <span className="tabFileName">{fileName}</span>
              </div>

              {tab.isDirty && (
                <span className="tabDirtyDot" title="Unsaved changes">
                  ●
                </span>
              )}

              <button
                className="tabCloseBtn"
                onClick={e => {
                  e.stopPropagation();
                  onCloseTab(tab.path);
                }}
                title="Close Tab (Ctrl+W)"
                aria-label={`Close ${fileName}`}
              >
                ✕
              </button>

              {isActive && <div className="activeTabBorderAccent" />}
            </div>
          );
        })}
      </div>

      {/* Tab bar right actions */}
      <div className="editorTabsActions">
        <button
          className="tabActionBtn"
          onClick={onSplitEditor}
          title="Split Editor Right (Ctrl+\)"
          aria-label="Split editor right"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="3" width="18" height="18" rx="2" />
            <line x1="12" y1="3" x2="12" y2="21" />
          </svg>
        </button>
        <button
          className="tabActionBtn"
          onClick={onMoreActions}
          title="More Actions..."
          aria-label="More actions"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="1.5" />
            <circle cx="19" cy="12" r="1.5" />
            <circle cx="5" cy="12" r="1.5" />
          </svg>
        </button>
      </div>
    </div>
  );
}
