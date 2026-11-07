import React, { useState, useEffect } from 'react';
import { seamApi } from '../api/client';
import { EngineeringConsole } from '../consoles/shared/EngineeringConsole';
import { StatusBadge, EvidenceDrawer } from '../consoles/shared/ConsoleComponents';
import '../consoles/shared/engineering-consoles.css';

export function ModelControlPanel() {
  const [modelInfo, setModelInfo] = useState<any>(null);

  useEffect(() => {
    seamApi.models()
      .then(res => setModelInfo(res))
      .catch(() => setModelInfo(null));
  }, []);

  const fallbackTelemetry = [
    { ts: new Date().toISOString(), req: 'ai/qwen3.8-flash-next', sel: 'ai/qwen3:4b-instruct-2507-q4_K_M', reason: 'Insufficient Hardware (CPU-Only)' },
    { ts: new Date().toISOString(), req: 'qwen3-coder:30b', sel: 'ai/qwen3:4b-instruct-2507-q4_K_M', reason: 'Insufficient RAM (15.6GB)' },
  ];

  const models = [
    { id: 'ai/qwen3:4b-instruct-2507-q4_K_M', provider: 'Docker Model Runner', tier: 'Local Fallback', ctx: '32K', lat: '~3.2s', status: 'AVAILABLE' },
    { id: 'ai/qwen3.8-flash-next', provider: 'Docker Model Runner', tier: 'High-Tier Candidate', ctx: '128K', lat: '~2.8s (GPU)', status: 'NOT_AVAILABLE' },
    { id: 'ai/devstral-small-2', provider: 'Docker Model Runner', tier: 'Agentic Workstation', ctx: '32K', lat: '~4.2s', status: 'NOT_CONFIGURED' },
    { id: 'qwen3-coder:30b', provider: 'Ollama / Remote', tier: 'Production Workstation', ctx: '131K', lat: 'N/A', status: 'BLOCKED' },
    { id: 'qwen3-coder:480b-cloud', provider: 'Cloud Gateway', tier: 'Enterprise Cloud', ctx: '262K', lat: '~3.2s', status: 'NOT_CONFIGURED' },
  ];

  return (
    <EngineeringConsole
      title="Model Routing & Inference Configuration"
      statusNode={<StatusBadge status="active" label="TRANSPARENT FALLBACK ACTIVE" />}
      description="REQUEST ⟶ MODEL ROUTER ⟶ HARDWARE CHECK ⟶ PRIMARY / FALLBACK ⟶ EXECUTION"
      toolbarNode={
        <>
          <div style={{ fontSize: 13, color: '#ccc' }}>
            Provider: <b style={{ color: '#fff' }}>{modelInfo?.llm_provider || 'docker'}</b> | 
            Hardware: <b style={{ color: '#F85149' }}>LOW_RESOURCE_CPU</b>
          </div>
          <div style={{ flex: 1 }} />
          <button className="consoleBtn">↻ Refresh Engine</button>
        </>
      }
      evidenceDrawerNode={
        <EvidenceDrawer title="Telemetry: MODEL_FALLBACK_TRIGGERED" defaultExpanded={true}>
          <table className="consoleTable" style={{ background: '#111' }}>
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Requested Model</th>
                <th>Selected Model</th>
                <th>Reason</th>
              </tr>
            </thead>
            <tbody>
              {fallbackTelemetry.map((t, i) => (
                <tr key={i}>
                  <td style={{ color: '#888' }}>{new Date(t.ts).toLocaleTimeString()}</td>
                  <td style={{ color: '#CCA700' }}>{t.req}</td>
                  <td style={{ color: '#73C991' }}>{t.sel}</td>
                  <td style={{ color: '#F85149' }}>{t.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </EvidenceDrawer>
      }
    >
      <div style={{ padding: 20, height: '100%', overflowY: 'auto' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 20 }}>
          {models.map(m => (
            <div key={m.id} style={{ background: '#1a1a1a', border: '1px solid #2b2b2b', borderRadius: 8, padding: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                <div>
                  <div style={{ fontSize: 11, color: '#888', marginBottom: 4 }}>{m.tier}</div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: '#fff' }}>{m.id}</div>
                </div>
                <StatusBadge status={m.status} />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#888' }}>Provider:</span>
                  <span style={{ color: '#ccc' }}>{m.provider}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#888' }}>Context:</span>
                  <span style={{ color: '#ccc' }}>{m.ctx}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#888' }}>Latency:</span>
                  <span style={{ color: '#ccc' }}>{m.lat}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </EngineeringConsole>
  );
}
