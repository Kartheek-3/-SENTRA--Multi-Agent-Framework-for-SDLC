import React from 'react';
import './engineering-consoles.css';

export interface EngineeringConsoleProps {
  title: string;
  statusNode?: React.ReactNode;
  description?: string;
  toolbarNode?: React.ReactNode;
  children: React.ReactNode;
  evidenceDrawerNode?: React.ReactNode;
}

export function EngineeringConsole({
  title,
  statusNode,
  description,
  toolbarNode,
  children,
  evidenceDrawerNode,
}: EngineeringConsoleProps) {
  return (
    <div className="engineeringConsoleContainer">
      {/* HEADER */}
      <header className="consoleHeader">
        <div className="consoleHeaderRow">
          <h1 className="consoleTitle">{title}</h1>
          <div className="consoleHeaderActions">{statusNode}</div>
        </div>
        {description && <p className="consoleDescription">{description}</p>}
      </header>

      {/* TOOLBAR */}
      {toolbarNode && (
        <div className="consoleToolbarSection">
          {toolbarNode}
        </div>
      )}

      {/* MAIN CONTENT */}
      <main className="consoleContentArea">
        {children}
      </main>

      {/* EVIDENCE / LOG DRAWER (BOTTOM OR SIDE) */}
      {evidenceDrawerNode && (
        <aside className="consoleEvidenceDrawer">
          {evidenceDrawerNode}
        </aside>
      )}
    </div>
  );
}
