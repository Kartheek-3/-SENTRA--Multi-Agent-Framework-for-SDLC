import React, { useState, useMemo } from 'react';
import { FileNode } from '../api/client';

export type OpenEditorItem = {
  path: string;
  isDirty?: boolean;
};

export type ProjectExplorerProps = {
  projectName?: string;
  tree: FileNode[];
  activePath?: string;
  openEditors?: OpenEditorItem[];
  filter: string;
  onFilter: (value: string) => void;
  onOpen: (path: string) => void;
  onCloseEditor?: (path: string) => void;
  onCreateFile: () => void;
  onCreateFolder: () => void;
  onRename: () => void;
  onDelete: () => void;
  onRefresh: () => void;
  onCollapseAll?: () => void;
};

export function ProjectExplorer({
  projectName = 'SEAM-WORKSPACE',
  tree,
  activePath,
  openEditors = [],
  filter,
  onFilter,
  onOpen,
  onCloseEditor,
  onCreateFile,
  onCreateFolder,
  onRename,
  onDelete,
  onRefresh,
}: ProjectExplorerProps) {
  // Collapsible section states
  const [openEditorsCollapsed, setOpenEditorsCollapsed] = useState(false);
  const [projectFilesCollapsed, setProjectFilesCollapsed] = useState(false);
  const [outlineCollapsed, setOutlineCollapsed] = useState(true);
  const [timelineCollapsed, setTimelineCollapsed] = useState(true);

  // Expanded folders set
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(() => {
    const initial = new Set<string>();
    // Auto-expand first level folders
    tree.forEach(node => {
      if (node.type === 'directory') initial.add(node.path);
    });
    return initial;
  });

  const toggleFolder = (folderPath: string) => {
    setExpandedFolders(prev => {
      const next = new Set(prev);
      if (next.has(folderPath)) next.delete(folderPath);
      else next.add(folderPath);
      return next;
    });
  };

  const collapseAllFolders = () => {
    setExpandedFolders(new Set());
  };

  const filtered = filter.trim().toLowerCase();

  // Helper for file type icons
  const getFileIcon = (name: string) => {
    if (name.endsWith('.tsx') || name.endsWith('.jsx')) {
      return <span className="fileIcon tsx" title="React TypeScript">⚛</span>;
    }
    if (name.endsWith('.ts') || name.endsWith('.js')) {
      return <span className="fileIcon ts" title="TypeScript/JavaScript">TS</span>;
    }
    if (name.endsWith('.json')) {
      return <span className="fileIcon json" title="JSON">{`{}`}</span>;
    }
    if (name.endsWith('.css') || name.endsWith('.scss')) {
      return <span className="fileIcon css" title="Stylesheet">#</span>;
    }
    if (name.endsWith('.py')) {
      return <span className="fileIcon python" title="Python">🐍</span>;
    }
    if (name.endsWith('.md')) {
      return <span className="fileIcon markdown" title="Markdown">📄</span>;
    }
    if (name.endsWith('.png') || name.endsWith('.svg') || name.endsWith('.jpg')) {
      return <span className="fileIcon image" title="Asset">🖼️</span>;
    }
    return <span className="fileIcon generic" title="File">📄</span>;
  };

  // Render tree recursively
  const renderNode = (node: FileNode, level = 0): React.ReactNode => {
    const isDir = node.type === 'directory';
    const isExpanded = filtered ? true : expandedFolders.has(node.path);
    const isSelected = activePath === node.path;
    const matchesFilter = !filtered || node.path.toLowerCase().includes(filtered);

    const children = node.children?.map(child => renderNode(child, level + 1));
    const hasVisibleChildren = children?.some(Boolean);

    if (!matchesFilter && !hasVisibleChildren) return null;

    return (
      <div key={node.path || node.name} className="explorerTreeNodeContainer">
        <button
          className={`explorerTreeNode ${isSelected ? 'selected' : ''}`}
          style={{ paddingLeft: `${12 + level * 14}px` }}
          onClick={() => {
            if (isDir) toggleFolder(node.path);
            else onOpen(node.path);
          }}
          title={node.path}
          aria-expanded={isDir ? isExpanded : undefined}
        >
          {isDir ? (
            <span className={`folderChevron ${isExpanded ? 'open' : ''}`} aria-hidden="true">
              ▶
            </span>
          ) : (
            <span className="fileIndentSpacer" aria-hidden="true" />
          )}

          {isDir ? (
            <span className="folderIcon" aria-hidden="true">
              {isExpanded ? '📂' : '📁'}
            </span>
          ) : (
            getFileIcon(node.name)
          )}

          <span className="treeNodeLabel">{node.name}</span>

          {/* Quick actions on hover */}
          <div className="nodeHoverActions" onClick={e => e.stopPropagation()}>
            {isSelected && (
              <>
                <button className="nodeHoverBtn" onClick={onRename} title="Rename">
                  ✎
                </button>
                <button className="nodeHoverBtn danger" onClick={onDelete} title="Delete">
                  ✕
                </button>
              </>
            )}
          </div>
        </button>

        {isDir && isExpanded && <div className="treeSubGroup">{children}</div>}
      </div>
    );
  };

  // Extract simple outline symbols from activePath
  const outlineSymbols = useMemo(() => {
    if (!activePath) return [];
    const base = activePath.split('/').pop() || '';
    if (base.endsWith('.tsx') || base.endsWith('.ts')) {
      const name = base.replace(/\.[^/.]+$/, '');
      return [
        { name: `export function ${name}`, type: 'function', icon: 'ƒ' },
        { name: `type Props`, type: 'type', icon: 'T' },
        { name: `return JSX`, type: 'render', icon: '⚛' },
      ];
    }
    return [
      { name: base, type: 'file', icon: '📄' },
    ];
  }, [activePath]);

  return (
    <aside className="explorerPanel" aria-label="Project Explorer">
      {/* 1. Explorer Header */}
      <div className="explorerHeader">
        <span className="explorerHeadingText">EXPLORER</span>
        <div className="explorerHeaderActions">
          <button className="explorerActionBtn" onClick={onCreateFile} title="New File" aria-label="New file">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="12" y1="18" x2="12" y2="12" />
              <line x1="9" y1="15" x2="15" y2="15" />
            </svg>
          </button>
          <button className="explorerActionBtn" onClick={onCreateFolder} title="New Folder" aria-label="New folder">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
              <line x1="12" y1="11" x2="12" y2="17" />
              <line x1="9" y1="14" x2="15" y2="14" />
            </svg>
          </button>
          <button className="explorerActionBtn" onClick={onRefresh} title="Refresh Explorer" aria-label="Refresh">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="23 4 23 10 17 10" />
              <polyline points="1 20 1 14 7 14" />
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
            </svg>
          </button>
          <button className="explorerActionBtn" onClick={collapseAllFolders} title="Collapse All Folders" aria-label="Collapse all">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="4 14 10 14 10 20" />
              <polyline points="20 10 14 10 14 4" />
              <line x1="14" y1="10" x2="21" y2="3" />
              <line x1="3" y1="21" x2="10" y2="14" />
            </svg>
          </button>
        </div>
      </div>

      <div className="explorerScrollArea scrollArea">
        {/* 2. Open Editors Section */}
        <div className="explorerSection">
          <div
            className="explorerSectionHeader"
            onClick={() => setOpenEditorsCollapsed(!openEditorsCollapsed)}
            role="button"
            tabIndex={0}
          >
            <span className={`sectionChevron ${openEditorsCollapsed ? '' : 'open'}`}>▶</span>
            <span className="sectionTitle">OPEN EDITORS</span>
            {openEditors.length > 0 && <span className="sectionCount">{openEditors.length}</span>}
          </div>

          {!openEditorsCollapsed && (
            <div className="openEditorsList">
              {openEditors.length === 0 ? (
                <div className="emptySectionNote">No open editors</div>
              ) : (
                openEditors.map(editor => {
                  const fileName = editor.path.split('/').pop() || editor.path;
                  const isActive = activePath === editor.path;
                  return (
                    <div
                      key={editor.path}
                      className={`openEditorRow ${isActive ? 'active' : ''}`}
                      onClick={() => onOpen(editor.path)}
                      title={editor.path}
                    >
                      <span className="editorIconSpan">{getFileIcon(fileName)}</span>
                      <span className="openEditorName">{fileName}</span>
                      {editor.isDirty && <span className="dirtyDot" title="Unsaved changes">●</span>}
                      <button
                        className="openEditorCloseBtn"
                        onClick={e => {
                          e.stopPropagation();
                          onCloseEditor?.(editor.path);
                        }}
                        title="Close Editor"
                      >
                        ✕
                      </button>
                    </div>
                  );
                })
              )}
            </div>
          )}
        </div>

        {/* 3. Project Files Tree Section */}
        <div className="explorerSection projectTreeSection">
          <div
            className="explorerSectionHeader"
            onClick={() => setProjectFilesCollapsed(!projectFilesCollapsed)}
            role="button"
            tabIndex={0}
          >
            <span className={`sectionChevron ${projectFilesCollapsed ? '' : 'open'}`}>▶</span>
            <span className="sectionTitle projectTitle">{projectName.toUpperCase()}</span>
          </div>

          {!projectFilesCollapsed && (
            <div className="projectTreeBody">
              {/* Subtle Search Filter Input */}
              <div className="explorerFilterRow">
                <input
                  className="explorerFilterInput"
                  value={filter}
                  onChange={e => onFilter(e.target.value)}
                  placeholder="Filter by name..."
                  aria-label="Filter files"
                />
                {filter && (
                  <button className="clearFilterBtn" onClick={() => onFilter('')}>
                    ✕
                  </button>
                )}
              </div>

              {/* Tree Content */}
              <div className="treeContent">
                {tree.length ? (
                  tree.map(node => renderNode(node))
                ) : (
                  <div className="emptyTreeNotice">
                    <p>No project files loaded.</p>
                    <button className="treeRefreshBtn" onClick={onRefresh}>
                      Load Workspace
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* 4. Outline Section */}
        <div className="explorerSection">
          <div
            className="explorerSectionHeader"
            onClick={() => setOutlineCollapsed(!outlineCollapsed)}
            role="button"
            tabIndex={0}
          >
            <span className={`sectionChevron ${outlineCollapsed ? '' : 'open'}`}>▶</span>
            <span className="sectionTitle">OUTLINE</span>
          </div>

          {!outlineCollapsed && (
            <div className="outlineBody">
              {outlineSymbols.map((sym, idx) => (
                <div key={idx} className="outlineSymbolRow">
                  <span className={`symbolGlyph ${sym.type}`}>{sym.icon}</span>
                  <span className="symbolName">{sym.name}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 5. Timeline Section */}
        <div className="explorerSection">
          <div
            className="explorerSectionHeader"
            onClick={() => setTimelineCollapsed(!timelineCollapsed)}
            role="button"
            tabIndex={0}
          >
            <span className={`sectionChevron ${timelineCollapsed ? '' : 'open'}`}>▶</span>
            <span className="sectionTitle">TIMELINE</span>
          </div>

          {!timelineCollapsed && (
            <div className="timelineBody">
              <div className="timelineEventRow">
                <span className="timelineDot" />
                <span className="timelineText">File saved ({activePath ? activePath.split('/').pop() : 'buffer'})</span>
                <span className="timelineTime">Just now</span>
              </div>
              <div className="timelineEventRow">
                <span className="timelineDot past" />
                <span className="timelineText">Git Commit: SEAM v1.0.1 final hardening</span>
                <span className="timelineTime">Latest</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}
