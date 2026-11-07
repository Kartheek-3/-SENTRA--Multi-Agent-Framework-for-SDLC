import React from 'react';

export type FileChange = {
  path: string;
  name: string;
  status: 'M' | 'A' | 'D' | 'T'; // Modified, Added, Deleted, Tested
  diffSummary?: string;
};

export type FileChangeListProps = {
  files?: FileChange[];
  onOpenFile: (path: string) => void;
  onOpenDiff?: (file: FileChange) => void;
};

export function FileChangeList({ files, onOpenFile, onOpenDiff }: FileChangeListProps) {
  if (!files || files.length === 0) {
    return (
      <div className="fileChangeListMinimal">
        <div className="emptyStateSubtle monospace" style={{ padding: '8px 12px', color: 'var(--text-muted, #71717a)', fontSize: '11px' }}>
          No files modified in current session (IDLE)
        </div>
      </div>
    );
  }

  const displayFiles = files;

  const getStatusBadge = (status: FileChange['status']) => {
    switch (status) {
      case 'A': return <span className="fileStatusTag tag-added monospace">A</span>;
      case 'D': return <span className="fileStatusTag tag-deleted monospace">D</span>;
      case 'T': return <span className="fileStatusTag tag-tested monospace">T</span>;
      case 'M':
      default: return <span className="fileStatusTag tag-modified monospace">M</span>;
    }
  };

  return (
    <div className="fileChangeListMinimal">
      {displayFiles.map(file => (
        <div key={file.path} className="fileChangeRowMinimal">
          <div className="fileLeftCluster">
            {getStatusBadge(file.status)}
            <span
              className="fileNameText monospace"
              title={file.path}
              onClick={() => onOpenFile(file.path)}
            >
              {file.name}
            </span>
          </div>

          <div className="fileRightActions">
            <button
              type="button"
              className="fileMiniBtn"
              onClick={() => onOpenFile(file.path)}
              title={`Open ${file.path}`}
            >
              Open
            </button>
            {onOpenDiff && (
              <button
                type="button"
                className="fileMiniBtn diff"
                onClick={() => onOpenDiff(file)}
                title={`View diff for ${file.name}`}
              >
                Diff
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
