import React, { useState, useMemo } from 'react';
import { FileNode } from '../api/client';

export type SearchResult = {
  path: string;
  line: number;
  content: string;
  matchStart: number;
  matchEnd: number;
};

export type WorkspaceSearchPanelProps = {
  tree: FileNode[];
  onOpenFile: (path: string) => void;
  cachedFileContents?: Record<string, string>;
};

export function WorkspaceSearchPanel({
  tree,
  onOpenFile,
  cachedFileContents = {},
}: WorkspaceSearchPanelProps) {
  const [query, setQuery] = useState('');
  const [replaceQuery, setReplaceQuery] = useState('');
  const [matchCase, setMatchCase] = useState(false);
  const [wholeWord, setWholeWord] = useState(false);
  const [useRegex, setUseRegex] = useState(false);
  const [showReplace, setShowReplace] = useState(false);

  // Flatten file list from tree
  const allFiles = useMemo(() => {
    const list: string[] = [];
    function traverse(nodes: FileNode[]) {
      for (const n of nodes) {
        if (n.type === 'file') list.push(n.path);
        if (n.children) traverse(n.children);
      }
    }
    traverse(tree);
    return list;
  }, [tree]);

  // Search across cached file contents and filenames
  const results = useMemo(() => {
    if (!query.trim()) return [];

    const matches: SearchResult[] = [];
    let regex: RegExp;
    try {
      const flags = matchCase ? 'g' : 'gi';
      let pattern = query;
      if (!useRegex) {
        pattern = pattern.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      }
      if (wholeWord) {
        pattern = `\\b${pattern}\\b`;
      }
      regex = new RegExp(pattern, flags);
    } catch {
      return [];
    }

    // Search in loaded file contents
    for (const [path, content] of Object.entries(cachedFileContents)) {
      const lines = content.split('\n');
      lines.forEach((lineText, idx) => {
        regex.lastIndex = 0;
        const match = regex.exec(lineText);
        if (match) {
          matches.push({
            path,
            line: idx + 1,
            content: lineText.trim(),
            matchStart: match.index,
            matchEnd: match.index + match[0].length,
          });
        }
      });
    }

    // If no contents loaded yet, match on file paths
    if (matches.length === 0) {
      allFiles.forEach(path => {
        regex.lastIndex = 0;
        if (regex.test(path)) {
          matches.push({
            path,
            line: 1,
            content: `Matching file: ${path}`,
            matchStart: 0,
            matchEnd: path.length,
          });
        }
      });
    }

    return matches;
  }, [query, matchCase, wholeWord, useRegex, cachedFileContents, allFiles]);

  // Group results by file path
  const grouped = useMemo(() => {
    const map = new Map<string, SearchResult[]>();
    results.forEach(res => {
      const current = map.get(res.path) || [];
      current.push(res);
      map.set(res.path, current);
    });
    return Array.from(map.entries());
  }, [results]);

  return (
    <div className="workspaceSearchPanel" role="region" aria-label="Search">
      <div className="sidebarHeader">
        <span className="sidebarTitle">SEARCH</span>
        <button
          className={`sidebarActionBtn ${showReplace ? 'active' : ''}`}
          onClick={() => setShowReplace(!showReplace)}
          title="Toggle Replace"
        >
          ⇌
        </button>
      </div>

      <div className="searchInputsArea">
        <div className="searchInputWrapper">
          <input
            type="text"
            className="searchTextInput"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Search in files (e.g. Agent, workflow)..."
            autoFocus
          />
          <div className="searchModifiers">
            <button
              className={`modBtn ${matchCase ? 'active' : ''}`}
              onClick={() => setMatchCase(!matchCase)}
              title="Match Case (Alt+C)"
            >
              Aa
            </button>
            <button
              className={`modBtn ${wholeWord ? 'active' : ''}`}
              onClick={() => setWholeWord(!wholeWord)}
              title="Match Whole Word (Alt+W)"
            >
              \b
            </button>
            <button
              className={`modBtn ${useRegex ? 'active' : ''}`}
              onClick={() => setUseRegex(!useRegex)}
              title="Use Regular Expression (Alt+R)"
            >
              .*
            </button>
          </div>
        </div>

        {showReplace && (
          <div className="replaceInputWrapper">
            <input
              type="text"
              className="searchTextInput"
              value={replaceQuery}
              onChange={e => setReplaceQuery(e.target.value)}
              placeholder="Replace with..."
            />
            <button
              className="replaceActionBtn"
              onClick={() => alert(`Replace '${query}' with '${replaceQuery}' across workspace`)}
              title="Replace All"
              disabled={!query}
            >
              Replace
            </button>
          </div>
        )}
      </div>

      <div className="searchResultsContainer scrollArea">
        {query && (
          <div className="resultsSummary">
            <span>{results.length} results in {grouped.length} files</span>
          </div>
        )}

        {grouped.map(([path, fileMatches]) => (
          <div className="searchFileGroup" key={path}>
            <div className="searchFileHeader" onClick={() => onOpenFile(path)}>
              <span className="fileChevron">▾</span>
              <span className="searchFileName">{path.split('/').pop() || path}</span>
              <span className="searchFileDir">{path.substring(0, path.lastIndexOf('/'))}</span>
              <span className="matchBadge">{fileMatches.length}</span>
            </div>
            <div className="searchFileMatches">
              {fileMatches.map((m, idx) => (
                <div
                  className="searchMatchRow"
                  key={idx}
                  onClick={() => onOpenFile(m.path)}
                >
                  <span className="lineNum">{m.line}</span>
                  <span className="matchSnippet">{m.content}</span>
                </div>
              ))}
            </div>
          </div>
        ))}

        {!query && (
          <div className="searchEmptyHint">
            <p>Type above to search across all project files and symbols.</p>
          </div>
        )}
      </div>
    </div>
  );
}
