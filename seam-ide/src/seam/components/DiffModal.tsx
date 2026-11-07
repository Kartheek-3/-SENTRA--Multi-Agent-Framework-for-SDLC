import React from 'react';
import { FileChange } from './FileChangeList';

export type DiffModalProps = {
  isOpen: boolean;
  onClose: () => void;
  file: FileChange | null;
  onOpenFile?: (path: string) => void;
};

export function DiffModal({ isOpen, onClose, file, onOpenFile }: DiffModalProps) {
  if (!isOpen || !file) return null;

  const previewDiffLines = file.diffSummary
    ? [
        { type: 'ctx', text: `@@ ${file.path} (${file.status === 'A' ? 'Added' : file.status === 'D' ? 'Deleted' : 'Modified'}) @@` },
        { type: 'ctx', text: file.diffSummary },
      ]
    : [
        { type: 'ctx', text: `@@ ${file.path} (${file.status === 'A' ? 'Added' : file.status === 'D' ? 'Deleted' : 'Modified'}) @@` },
        { type: file.status === 'A' ? 'add' : 'rem', text: `${file.status === 'A' ? '+' : '-'} [File touched in execution context: ${file.path}]` },
      ];

  return (
    <div className="diffModalOverlay" role="dialog" aria-modal="true" aria-label="File Diff Viewer">
      <div className="diffModalBackdrop" onClick={onClose} />
      <div className="diffModalContent">
        <div className="diffModalHeader">
          <div className="diffHeaderLeft">
            <span className="diffFileBadge monospace">{file.status}</span>
            <span className="diffFilePath monospace">{file.path}</span>
          </div>
          <button type="button" className="diffModalCloseBtn" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="diffModalBody monospace">
          {previewDiffLines.map((line, idx) => (
            <div key={idx} className={`diffLineItem ${line.type}`}>
              <span className="diffGutter">
                {line.type === 'add' ? '+' : line.type === 'rem' ? '-' : ' '}
              </span>
              <span className="diffCodeText">{line.text}</span>
            </div>
          ))}
        </div>

        <div className="diffModalFooter">
          {onOpenFile && (
            <button
              type="button"
              className="openEditorBtn"
              onClick={() => {
                onClose();
                onOpenFile(file.path);
              }}
            >
              Open File in Editor
            </button>
          )}
          <button type="button" className="closeDiffBtn" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
