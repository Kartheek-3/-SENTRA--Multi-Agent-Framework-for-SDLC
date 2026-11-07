import React, { useState } from 'react';
import './engineering-consoles.css';

export function StatusBadge({ status, label }: { status: string; label?: string }) {
  const norm = status.toLowerCase();
  let colorClass = 'idle';
  
  if (['pass', 'success', 'resolved', 'valid', 'match'].includes(norm)) colorClass = 'pass';
  else if (['fail', 'failed', 'error', 'invalid', 'drift', 'missing'].includes(norm)) colorClass = 'fail';
  else if (['running', 'active', 'generating'].includes(norm)) colorClass = 'active';
  else if (['warning', 'stale', 'blocked'].includes(norm)) colorClass = 'warning';
  
  return (
    <span className={`statusBadge ${colorClass}`}>
      {label || status.toUpperCase()}
    </span>
  );
}

export function EvidenceDrawer({
  title = 'Evidence available',
  defaultExpanded = false,
  children
}: {
  title?: string;
  defaultExpanded?: boolean;
  children: React.ReactNode;
}) {
  const [expanded, setExpanded] = useState(defaultExpanded);
  
  return (
    <div className="evidenceDrawerContainer">
      <div className="evidenceDrawerHeader" onClick={() => setExpanded(!expanded)}>
        <span className="evidenceDrawerTitle">
          {expanded ? '▼' : '▶'} {title}
        </span>
        <span className="tableActionLink">
          {expanded ? 'Hide evidence' : 'View evidence'}
        </span>
      </div>
      {expanded && (
        <div className="evidenceDrawerContent">
          {children}
        </div>
      )}
    </div>
  );
}

export function ConsoleTabs({
  tabs,
  activeId,
  onChange
}: {
  tabs: { id: string; label: string }[];
  activeId: string;
  onChange: (id: string) => void;
}) {
  return (
    <div className="consoleTabs">
      {tabs.map(t => (
        <div
          key={t.id}
          className={`consoleTab ${t.id === activeId ? 'active' : ''}`}
          onClick={() => onChange(t.id)}
        >
          {t.label}
        </div>
      ))}
    </div>
  );
}

export function EmptyState({ title, description, actionNode }: { title: string; description: string; actionNode?: React.ReactNode }) {
  return (
    <div className="consoleEmptyState">
      <h3>{title}</h3>
      <p>{description}</p>
      {actionNode && <div style={{ marginTop: 24 }}>{actionNode}</div>}
    </div>
  );
}
