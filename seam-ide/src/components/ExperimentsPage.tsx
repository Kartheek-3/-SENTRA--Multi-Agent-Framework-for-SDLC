import React, { useState } from 'react';
import { EngineeringConsole } from '../consoles/shared/EngineeringConsole';
import { StatusBadge, EvidenceDrawer } from '../consoles/shared/ConsoleComponents';
import '../consoles/shared/engineering-consoles.css';

export function ExperimentsPage() {
  const [selectedExperiment, setSelectedExperiment] = useState<any>(null);

  const experiments = [
    { id: '1', scenario: 'EXP_DOMAIN_RAG', config: 'SEAM_FULL', run: 42, duration: '24m 12s', metrics: 'UNKNOWN', status: 'PASS', reproducible: true },
    { id: '2', scenario: 'EXP_DOMAIN_RAG', config: 'ABLATION_NO_DOMAIN_RAG', run: 43, duration: '18m 05s', metrics: 'UNKNOWN', status: 'PASS', reproducible: true },
    { id: '3', scenario: 'EXP_AUTONOMOUS_REPAIR', config: 'SEAM_FULL', run: 12, duration: '41m 33s', metrics: 'UNKNOWN', status: 'PASS', reproducible: true },
    { id: '4', scenario: 'EXP_AUTONOMOUS_REPAIR', config: 'ABLATION_NO_AUTONOMOUS_REPAIR', run: 13, duration: '12m 10s', metrics: 'UNKNOWN', status: 'FAIL', reproducible: true },
    { id: '5', scenario: 'EXP_CONTRACT_INTELLIGENCE', config: 'BASELINE', run: 1, duration: '05m 20s', metrics: 'UNKNOWN', status: 'UNKNOWN', reproducible: false },
  ];

  return (
    <EngineeringConsole
      title="Experiments Matrix"
      description="Ablation studies and configuration benchmarking"
      toolbarNode={
        <>
          <button className="consoleBtn">↻ Refresh Matrix</button>
          <div style={{ flex: 1 }} />
          <button className="consoleBtn primary">Queue New Run</button>
        </>
      }
    >
      <div style={{ display: 'flex', height: '100%' }}>
        <main style={{ flex: 1, padding: 0, overflowY: 'auto' }}>
          <table className="consoleTable">
            <thead>
              <tr>
                <th>Scenario</th>
                <th>Configuration</th>
                <th>Run ID</th>
                <th>Duration</th>
                <th>Metrics</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {experiments.map(exp => (
                <tr 
                  key={exp.id}
                  onClick={() => setSelectedExperiment(exp)}
                  style={{ cursor: 'pointer', background: selectedExperiment?.id === exp.id ? 'rgba(255,255,255,0.05)' : '' }}
                >
                  <td style={{ fontWeight: 500, color: '#fff' }}>{exp.scenario}</td>
                  <td style={{ fontFamily: 'monospace', color: '#58A6FF' }}>{exp.config}</td>
                  <td>{exp.run}</td>
                  <td style={{ fontFamily: 'monospace' }}>{exp.duration}</td>
                  <td>{exp.metrics}</td>
                  <td><StatusBadge status={exp.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </main>

        {selectedExperiment && (
          <aside style={{ width: 380, borderLeft: '1px solid #2b2b2b', background: '#1a1a1a', padding: 20, overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
              <h3 style={{ margin: 0, fontSize: 16, color: '#fff', wordBreak: 'break-all' }}>{selectedExperiment.scenario}</h3>
              <button className="consoleBtn" style={{ padding: '2px 8px' }} onClick={() => setSelectedExperiment(null)}>✕</button>
            </div>
            
            <StatusBadge status={selectedExperiment.status} />

            <div style={{ marginTop: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <div style={{ fontSize: 11, color: '#888' }}>Configuration</div>
                <div style={{ fontSize: 13, color: '#58A6FF', fontFamily: 'monospace' }}>{selectedExperiment.config}</div>
              </div>
              <div>
                <div style={{ fontSize: 11, color: '#888' }}>Model / Environment</div>
                <div style={{ fontSize: 13, color: '#ccc' }}>ai/qwen3:4b-instruct-2507-q4_K_M (Local)</div>
              </div>
              <div>
                <div style={{ fontSize: 11, color: '#888' }}>Reproducibility</div>
                <div style={{ fontSize: 13, color: selectedExperiment.reproducible ? '#73C991' : '#CCA700' }}>
                  {selectedExperiment.reproducible ? '✓ Deterministic Seed' : '⚠ Non-deterministic'}
                </div>
              </div>
            </div>

            <div style={{ marginTop: 24, padding: 12, background: '#242424', borderRadius: 4, border: '1px solid #3c3c3c' }}>
              <div style={{ fontSize: 11, color: '#888', marginBottom: 4 }}>Machine-Readable Result Artifact</div>
              <pre style={{ margin: 0, fontSize: 11, color: '#aaa', whiteSpace: 'pre-wrap' }}>
                {`{\n  "scenario": "${selectedExperiment.scenario}",\n  "config": "${selectedExperiment.config}",\n  "status": "${selectedExperiment.status}",\n  "metrics": {}\n}`}
              </pre>
            </div>

            <div style={{ marginTop: 16 }}>
              <button className="consoleBtn primary" style={{ width: '100%', justifyContent: 'center' }}>Open Result Artifact</button>
            </div>
          </aside>
        )}
      </div>
    </EngineeringConsole>
  );
}
