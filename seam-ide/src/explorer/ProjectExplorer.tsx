import { FileNode } from '../api/client';
import { useState } from 'react';

type Props = {
  tree: FileNode[];
  activePath?: string;
  filter: string;
  onFilter: (value: string) => void;
  onOpen: (path: string) => void;
  onCreateFile: () => void;
  onCreateFolder: () => void;
  onRename: () => void;
  onDelete: () => void;
  onRefresh: () => void;
};

export function ProjectExplorer(props: Props) {
  const [openFolders, setOpenFolders] = useState<Set<string>>(() => new Set());
  const filtered = props.filter.trim().toLowerCase();
  const toggleFolder = (path: string) => {
    setOpenFolders(current => {
      const next = new Set(current);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
  };

  const renderNode = (node: FileNode, level = 0) => {
    const visible = !filtered || node.path.toLowerCase().includes(filtered);
    const isOpen = filtered || openFolders.has(node.path);
    const children = node.children?.map(child => renderNode(child, level + 1));
    if (!visible && !children?.some(Boolean)) return null;
    return (
      <div key={node.path || node.name}>
        <button
          className={`treeNode ${props.activePath === node.path ? 'active' : ''}`}
          style={{ paddingLeft: 8 + level * 14 }}
          onClick={() => node.type === 'directory' ? toggleFolder(node.path) : props.onOpen(node.path)}
          title={node.path}
        >
          <span>{node.type === 'directory' ? (isOpen ? '-' : '+') : '-'}</span>
          <span>{node.name}</span>
        </button>
        {node.type === 'directory' && isOpen && children}
      </div>
    );
  };

  return (
    <aside className="explorer">
      <div className="paneHeader">
        <strong>Explorer</strong>
        <button onClick={props.onRefresh}>Refresh</button>
      </div>
      <input className="compactInput" value={props.filter} onChange={event => props.onFilter(event.target.value)} placeholder="Search files" />
      <div className="buttonRow">
        <button onClick={props.onCreateFile}>File</button>
        <button onClick={props.onCreateFolder}>Folder</button>
        <button onClick={props.onRename}>Rename</button>
        <button onClick={props.onDelete}>Delete</button>
      </div>
      <div className="tree">{props.tree.length ? props.tree.map(node => renderNode(node)) : <p className="muted">No files yet.</p>}</div>
    </aside>
  );
}
