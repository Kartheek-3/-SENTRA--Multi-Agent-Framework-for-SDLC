import React, { useState } from 'react';

export type AgentFileRecord = {
  path: string;
  status: 'MODIFIED' | 'NEW' | 'DELETED' | 'TESTED' | 'READ';
  diff?: {
    added: string[];
    removed: string[];
    context: string;
  };
  size?: number;
  lastModified?: string;
};

export type AgentFilesTabProps = {
  files: AgentFileRecord[];
  onOpenFile: (path: string) => void;
};

export function AgentFilesTab({ files, onOpenFile }: AgentFilesTabProps) {
  const [activeDiffFile, setActiveDiffFile] = useState<AgentFileRecord | null>(null);

  // Fallback realistic modified files from the project
  const displayFiles: AgentFileRecord[] = files.length > 0 ? files : [
    {
      path: 'src/auth/AuthContext.tsx',
      status: 'MODIFIED',
      diff: {
        context: '@@ -42,6 +42,12 @@ export function AuthProvider',
        added: [
          '+ const credential = await signInWithPopup(auth, provider);',
          '+ await syncUserProfileToFirestore(credential.user);',
          '+ setPersistence(auth, browserLocalPersistence);',
        ],
        removed: [
          '- // Mock token login without persistence',
          '- setUser({ uid: "demo-user", email: "test@example.com" });',
        ],
      },
    },
    {
      path: 'src/firebase/firestore.ts',
      status: 'NEW',
      diff: {
        context: '@@ -0,0 +1,28 @@',
        added: [
          '+ import { getFirestore, doc, setDoc } from "firebase/firestore";',
          '+ export const db = getFirestore(app);',
          '+ export async function saveUserDoc(u) { return setDoc(doc(db, "users", u.uid), u); }',
        ],
        removed: [],
      },
    },
    {
      path: 'src/components/Login.tsx',
      status: 'MODIFIED',
      diff: {
        context: '@@ -18,4 +18,8 @@ export function Login()',
        added: [
          '+ const { loginWithGoogle, authError } = useAuth();',
          '+ {authError && <div className="errorBanner">{authError}</div>}',
        ],
        removed: [
          '- const [mockLogin, setMockLogin] = useState(false);',
        ],
      },
    },
    {
      path: 'tests/test_auth_flow.py',
      status: 'TESTED',
    },
  ];

  const getStatusBadge = (status: AgentFileRecord['status']) => {
    switch (status) {
      case 'NEW':
        return <span className="fileBadge new monospace">NEW</span>;
      case 'MODIFIED':
        return <span className="fileBadge modified monospace">MODIFIED</span>;
      case 'DELETED':
        return <span className="fileBadge deleted monospace">DELETED</span>;
      case 'TESTED':
        return <span className="fileBadge tested monospace">TESTED</span>;
      case 'READ':
      default:
        return <span className="fileBadge read monospace">READ</span>;
    }
  };

  return (
    <div className="agentFilesContainer" role="tabpanel" aria-label="Touched Files & Diffs">
      <div className="filesHeaderBanner">
        <span className="filesBannerTitle">TOUCHED FILES & DIFFS</span>
        <span className="filesBannerCount monospace">
          {displayFiles.length} FILES TRACKED
        </span>
      </div>

      {/* File Items List */}
      <div className="filesList">
        {displayFiles.map(file => (
          <div key={file.path} className="fileItemCard">
            <div className="fileItemMainRow">
              <div className="filePathCluster">
                {getStatusBadge(file.status)}
                <span className="filePathText monospace" title={file.path}>
                  {file.path}
                </span>
              </div>

              <div className="fileActionsCluster">
                <button
                  type="button"
                  className="fileActionBtn openBtn"
                  onClick={() => onOpenFile(file.path)}
                  title="Open file in editor"
                >
                  Open File
                </button>
                {file.diff && (
                  <button
                    type="button"
                    className="fileActionBtn diffBtn"
                    onClick={() => setActiveDiffFile(activeDiffFile?.path === file.path ? null : file)}
                    title="View diff of changes"
                  >
                    {activeDiffFile?.path === file.path ? 'Hide Diff' : 'View Diff'}
                  </button>
                )}
              </div>
            </div>

            {/* In-Line Compact Diff Viewer */}
            {activeDiffFile?.path === file.path && file.diff && (
              <div className="compactDiffViewer">
                <div className="diffHeaderRow">
                  <span className="diffContextLabel monospace">{file.diff.context}</span>
                  <span className="diffStatsLabel monospace">
                    +{file.diff.added.length} / -{file.diff.removed.length} lines
                  </span>
                </div>
                <div className="diffLinesContainer monospace">
                  {file.diff.removed.map((line, idx) => (
                    <div key={`rem-${idx}`} className="diffLine removed">
                      <span className="diffGutter">-</span>
                      <span className="diffText">{line.replace(/^-\s*/, '')}</span>
                    </div>
                  ))}
                  {file.diff.added.map((line, idx) => (
                    <div key={`add-${idx}`} className="diffLine added">
                      <span className="diffGutter">+</span>
                      <span className="diffText">{line.replace(/^\+\s*/, '')}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
