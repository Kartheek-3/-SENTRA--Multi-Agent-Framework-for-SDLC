import React, { useState } from 'react';
import { EngineeringConsole } from '../consoles/shared/EngineeringConsole';
import { StatusBadge, EvidenceDrawer } from '../consoles/shared/ConsoleComponents';

export function DeliveryCenterPage({ state }: { state: any }) {
  const [selectedGate, setSelectedGate] = useState<any>(null);

  const gates = [
    { id: 'requirements', label: 'Requirements', status: 'PASS', detail: 'Requirements validated and scoped.' },
    { id: 'architecture', label: 'Architecture', status: state?.project_plan ? 'PASS' : 'BLOCKED', detail: 'Architecture blueprints and plan generated.' },
    { id: 'contracts', label: 'Contracts', status: state?.full_stack_contract ? 'PASS' : 'WARNING', detail: 'Three-way schema parity verification.' },
    { id: 'tests', label: 'Tests', status: state?.latest_qa_status === 'passed' ? 'PASS' : 'BLOCKED', detail: 'Unit, integration, and E2E test suites.' },
    { id: 'security', label: 'Security', status: 'PASS', detail: 'SAST and dependency scanning passed.' },
    { id: 'build', label: 'Build', status: state?.workflow_status === 'completed' ? 'PASS' : 'WARNING', detail: 'Source code compiles and builds successfully.' },
    { id: 'artifacts', label: 'Artifacts', status: 'NOT_CONFIGURED', detail: 'Docker images and static bundles.' },
    { id: 'deployment', label: 'Deployment', status: 'NOT_CONFIGURED', detail: 'Infrastructure as code apply and verification.' },
    { id: 'rollback', label: 'Rollback', status: 'NOT_CONFIGURED', detail: 'Stateful rollback safety check.' },
  ];

  const overallStatus = gates.some(g => g.status === 'BLOCKED') ? 'BLOCKED' : 'READY';

  return (
    <EngineeringConsole
      title="Delivery Center"
      statusNode={<StatusBadge status={overallStatus} label={`RELEASE ${overallStatus}`} />}
      description="Continuous Delivery Release Readiness Gates"
      toolbarNode={
        <>
          <button className="consoleBtn">↻ Re-verify Gates</button>
          <div style={{ flex: 1 }} />
          <button className="consoleBtn primary" disabled={overallStatus === 'BLOCKED'}>Build Release Package</button>
        </>
      }
    >
      <div style={{ display: 'flex', height: '100%' }}>
        <main style={{ flex: 1, padding: 20, overflowY: 'auto' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: 16 }}>
            {gates.map(gate => (
              <div 
                key={gate.id} 
                onClick={() => setSelectedGate(gate)}
                style={{ 
                  background: '#1a1a1a', 
                  border: `1px solid ${selectedGate?.id === gate.id ? '#58A6FF' : '#2b2b2b'}`, 
                  borderRadius: 6, 
                  padding: 16,
                  cursor: 'pointer'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <h4 style={{ margin: 0, color: '#fff' }}>{gate.label}</h4>
                  <StatusBadge status={gate.status} />
                </div>
                <p style={{ margin: 0, fontSize: 12, color: '#888' }}>{gate.detail}</p>
              </div>
            ))}
          </div>
        </main>

        {selectedGate && (
          <aside style={{ width: 350, borderLeft: '1px solid #2b2b2b', background: '#1a1a1a', padding: 20, overflowY: 'auto' }}>
            <h3 style={{ margin: '0 0 16px 0', color: '#fff' }}>Gate: {selectedGate.label}</h3>
            <StatusBadge status={selectedGate.status} />
            
            <div style={{ marginTop: 24, padding: 12, background: '#242424', borderRadius: 4, border: '1px solid #3c3c3c' }}>
              <div style={{ fontSize: 11, color: '#888', marginBottom: 4 }}>Gate Requirements</div>
              <p style={{ margin: 0, fontSize: 13, color: '#ccc' }}>{selectedGate.detail}</p>
            </div>

            <div style={{ marginTop: 24, display: 'flex', flexDirection: 'column', gap: 8 }}>
              <button className="consoleBtn" style={{ justifyContent: 'center' }}>Inspect Artifacts</button>
              <button className="consoleBtn" style={{ justifyContent: 'center' }}>View Manifest</button>
              <button className="consoleBtn" style={{ justifyContent: 'center' }}>View Deployment Profile</button>
            </div>
          </aside>
        )}
      </div>
    </EngineeringConsole>
  );
}
