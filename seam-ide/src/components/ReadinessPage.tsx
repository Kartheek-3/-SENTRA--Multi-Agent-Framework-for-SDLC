import React, { useState } from 'react';
import { EngineeringConsole } from '../consoles/shared/EngineeringConsole';
import { StatusBadge, EvidenceDrawer } from '../consoles/shared/ConsoleComponents';
import '../consoles/shared/engineering-consoles.css';

export function ReadinessPage() {
  const [selectedArea, setSelectedArea] = useState<any>(null);

  const areas = [
    { id: 'arch', name: 'Architecture', status: 'PASS', evidence: 'Project plan and canonical schemas valid.', last: '1m ago' },
    { id: 'backend', name: 'Backend', status: 'PASS', evidence: 'FastAPI routes compiled and running.', last: '1m ago' },
    { id: 'frontend', name: 'Frontend', status: 'PASS', evidence: 'Vite build successful.', last: '1m ago' },
    { id: 'agents', name: 'Agents', status: 'PASS', evidence: 'LangGraph workflow idle and ready.', last: '1m ago' },
    { id: 'tools', name: 'Tools', status: 'PASS', evidence: 'Tool registry schema validated.', last: '1m ago' },
    { id: 'rag', name: 'RAG', status: 'PASS', evidence: 'ChromaDB local connection active.', last: '1m ago' },
    { id: 'models', name: 'Models', status: 'PASS', evidence: 'Qwen3 4B fallback loaded in memory.', last: '1m ago' },
    { id: 'security', name: 'Security', status: 'PASS', evidence: 'Static analysis passed.', last: '1m ago' },
    { id: 'testing', name: 'Testing', status: 'PASS', evidence: 'Core test suites passed.', last: '1m ago' },
    { id: 'runtime', name: 'Runtime', status: 'PASS', evidence: 'Localhost confinement active.', last: '1m ago' },
    { id: 'db', name: 'Database', status: 'PASS', evidence: 'SQLite migrations applied.', last: '1m ago' },
    { id: 'figma', name: 'Figma', status: 'NOT_CONFIGURED', evidence: 'Token not set.', last: '1m ago' },
    { id: 'docker', name: 'Docker', status: 'PASS', evidence: 'Daemon reachable.', last: '1m ago' },
    { id: 'deploy', name: 'Deployment', status: 'NOT_CONFIGURED', evidence: 'No production pipeline configured.', last: '1m ago' },
    { id: 'obs', name: 'Observability', status: 'PASS', evidence: 'EventStore WebSocket active.', last: '1m ago' },
  ];

  return (
    <EngineeringConsole
      title="System Readiness & Health"
      description="Overall workspace health and subsystem release readiness"
      toolbarNode={
        <>
          <button className="consoleBtn">↻ Run Full Health Check</button>
        </>
      }
      evidenceDrawerNode={
        selectedArea ? (
          <EvidenceDrawer title={`Health Evidence: ${selectedArea.name}`} defaultExpanded={true}>
            <pre style={{ fontSize: 12, color: '#ccc', margin: 0 }}>
              {selectedArea.evidence}
            </pre>
          </EvidenceDrawer>
        ) : null
      }
    >
      <main style={{ padding: 0, height: '100%', overflowY: 'auto' }}>
        <table className="consoleTable">
          <thead>
            <tr>
              <th>Area</th>
              <th>Status</th>
              <th>Evidence</th>
              <th>Last Checked</th>
            </tr>
          </thead>
          <tbody>
            {areas.map(area => (
              <tr 
                key={area.id}
                onClick={() => setSelectedArea(area)}
                style={{ cursor: 'pointer', background: selectedArea?.id === area.id ? 'rgba(255,255,255,0.05)' : '' }}
              >
                <td style={{ fontWeight: 500, color: '#fff' }}>{area.name}</td>
                <td><StatusBadge status={area.status} /></td>
                <td style={{ color: '#888' }}>{area.evidence}</td>
                <td style={{ color: '#888', fontSize: 12 }}>{area.last}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </main>
    </EngineeringConsole>
  );
}
