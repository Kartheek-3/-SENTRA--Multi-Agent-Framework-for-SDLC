import React, { useState } from 'react';

export type GitFileChange = {
  path: string;
  status: 'M' | 'A' | 'D' | 'U';
  isStaged: boolean;
};

export type GitControlPanelProps = {
  branch?: string;
  onOpenFile: (path: string) => void;
  onRefresh?: () => void;
};

export function GitControlPanel({
  branch = 'final-validation',
  onOpenFile,
  onRefresh,
}: GitControlPanelProps) {
  const [commitMessage, setCommitMessage] = useState('');
  const [changes, setChanges] = useState<GitFileChange[]>([
    { path: 'src/App.tsx', status: 'M', isStaged: true },
    { path: 'src/landing/LandingPage.tsx', status: 'A', isStaged: true },
    { path: 'src/firebase/config.ts', status: 'A', isStaged: true },
    { path: 'src/firebase/AuthContext.tsx', status: 'A', isStaged: false },
    { path: 'src/components/LoginPage.tsx', status: 'A', isStaged: false },
    { path: 'src/components/SignupPage.tsx', status: 'A', isStaged: false },
    { path: 'src/styles.css', status: 'M', isStaged: false },
  ]);
  const [committedCount, setCommittedCount] = useState(14);
  const [committing, setCommitting] = useState(false);

  const staged = changes.filter(c => c.isStaged);
  const unstaged = changes.filter(c => !c.isStaged);

  const toggleStage = (path: string) => {
    setChanges(prev => prev.map(c => c.path === path ? { ...c, isStaged: !c.isStaged } : c));
  };

  const stageAll = () => {
    setChanges(prev => prev.map(c => ({ ...c, isStaged: true })));
  };

  const unstageAll = () => {
    setChanges(prev => prev.map(c => ({ ...c, isStaged: false })));
  };

  const handleCommit = () => {
    if (!commitMessage.trim() || staged.length === 0) return;
    setCommitting(true);
    setTimeout(() => {
      setChanges(prev => prev.filter(c => !c.isStaged));
      setCommittedCount(c => c + 1);
      setCommitMessage('');
      setCommitting(false);
    }, 400);
  };

  return (
    <div className="gitControlPanel" role="region" aria-label="Source Control">
      <div className="sidebarHeader">
        <span className="sidebarTitle">SOURCE CONTROL</span>
        <div className="sidebarHeaderActions">
          <button className="sidebarActionBtn" onClick={stageAll} title="Stage All Changes">+</button>
          <button className="sidebarActionBtn" onClick={onRefresh} title="Refresh Git Status">↻</button>
        </div>
      </div>

      {/* Branch strip */}
      <div className="gitBranchStrip">
        <span className="gitBranchIcon">⎇</span>
        <span className="gitBranchName">{branch}</span>
        <span className="gitSyncBadge">✓ UP TO DATE</span>
      </div>

      {/* Commit message box */}
      <div className="gitCommitSection">
        <textarea
          className="gitCommitInput"
          value={commitMessage}
          onChange={e => setCommitMessage(e.target.value)}
          placeholder="Message (Ctrl+Enter to commit to 'final-validation')..."
          rows={3}
        />
        <button
          className="gitCommitBtn"
          onClick={handleCommit}
          disabled={!commitMessage.trim() || staged.length === 0 || committing}
        >
          {committing ? 'Committing...' : `Commit (${staged.length} staged)`}
        </button>
      </div>

      <div className="gitChangesList scrollArea">
        {/* Staged Changes */}
        <div className="gitSectionHeader">
          <span>STAGED CHANGES ({staged.length})</span>
          {staged.length > 0 && (
            <button className="gitMiniAction" onClick={unstageAll} title="Unstage All">−</button>
          )}
        </div>
        <div className="gitFileItems">
          {staged.map(f => (
            <div className="gitFileRow" key={f.path}>
              <span className={`gitStatusBadge ${f.status}`}>{f.status}</span>
              <span className="gitFilePath" onClick={() => onOpenFile(f.path)}>{f.path}</span>
              <button className="gitStageBtn" onClick={() => toggleStage(f.path)} title="Unstage">−</button>
            </div>
          ))}
          {staged.length === 0 && <span className="gitEmptyHint">No staged changes</span>}
        </div>

        {/* Changes (Unstaged) */}
        <div className="gitSectionHeader">
          <span>CHANGES ({unstaged.length})</span>
          {unstaged.length > 0 && (
            <button className="gitMiniAction" onClick={stageAll} title="Stage All">+</button>
          )}
        </div>
        <div className="gitFileItems">
          {unstaged.map(f => (
            <div className="gitFileRow" key={f.path}>
              <span className={`gitStatusBadge ${f.status}`}>{f.status}</span>
              <span className="gitFilePath" onClick={() => onOpenFile(f.path)}>{f.path}</span>
              <button className="gitStageBtn" onClick={() => toggleStage(f.path)} title="Stage">+</button>
            </div>
          ))}
          {unstaged.length === 0 && <span className="gitEmptyHint">Working tree clean</span>}
        </div>

        {/* Commit History preview */}
        <div className="gitSectionHeader">
          <span>RECENT COMMITS ({committedCount})</span>
        </div>
        <div className="gitHistoryList">
          <div className="gitHistoryItem">
            <span className="commitHash">a47f91c</span>
            <span className="commitMsg">feat: SEAM professional landing page integration</span>
          </div>
          <div className="gitHistoryItem">
            <span className="commitHash">32b012e</span>
            <span className="commitMsg">feat: full-stack contracts and test lab consoles</span>
          </div>
          <div className="gitHistoryItem">
            <span className="commitHash">90fe45a</span>
            <span className="commitMsg">feat: autonomous defect repair loop and telemetry</span>
          </div>
        </div>
      </div>
    </div>
  );
}
