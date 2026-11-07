import React, { useState } from 'react';
import { EngineeringConsole } from '../consoles/shared/EngineeringConsole';
import { StatusBadge, EvidenceDrawer } from '../consoles/shared/ConsoleComponents';
import '../consoles/shared/engineering-consoles.css';

export function IntegrationsPage() {
  const [selectedIntegration, setSelectedIntegration] = useState<any>(null);

  const integrations = [
    { id: 'docker', name: 'Docker', type: 'Containerization', status: 'CONNECTED' },
    { id: 'dmr', name: 'Docker Model Runner', type: 'Local Inference', status: 'CONNECTED' },
    { id: 'ollama', name: 'Ollama', type: 'Local Inference', status: 'AVAILABLE' },
    { id: 'chroma', name: 'ChromaDB', type: 'Vector Database', status: 'CONNECTED' },
    { id: 'github', name: 'GitHub', type: 'VCS', status: 'NOT_CONFIGURED' },
    { id: 'figma', name: 'Figma', type: 'Design', status: 'NOT_CONFIGURED' },
    { id: 'n8n', name: 'n8n', type: 'Workflow', status: 'NOT_CONFIGURED' },
    { id: 'jira', name: 'Jira', type: 'Issue Tracking', status: 'NOT_CONFIGURED' },
    { id: 'cloud', name: 'Cloud Gateway', type: 'Enterprise API', status: 'BLOCKED' },
  ];

  return (
    <EngineeringConsole
      title="Integrations & External Services"
      description="Manage connections to external providers, tools, and runtimes"
      toolbarNode={
        <>
          <button className="consoleBtn">↻ Test All Connections</button>
        </>
      }
    >
      <div style={{ display: 'flex', height: '100%' }}>
        <main style={{ flex: 1, padding: 0, overflowY: 'auto' }}>
          <table className="consoleTable">
            <thead>
              <tr>
                <th>Integration</th>
                <th>Type</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {integrations.map(int => (
                <tr 
                  key={int.id}
                  onClick={() => setSelectedIntegration(int)}
                  style={{ cursor: 'pointer', background: selectedIntegration?.id === int.id ? 'rgba(255,255,255,0.05)' : '' }}
                >
                  <td style={{ fontWeight: 500, color: '#fff' }}>{int.name}</td>
                  <td style={{ color: '#888' }}>{int.type}</td>
                  <td>
                    <StatusBadge 
                      status={
                        int.status === 'CONNECTED' ? 'pass' : 
                        int.status === 'AVAILABLE' ? 'active' : 
                        int.status === 'BLOCKED' ? 'fail' : 'notConfigured'
                      } 
                      label={int.status} 
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </main>

        {selectedIntegration && (
          <aside style={{ width: 350, borderLeft: '1px solid #2b2b2b', background: '#1a1a1a', padding: 20, overflowY: 'auto' }}>
            <h3 style={{ margin: '0 0 8px 0', color: '#fff' }}>{selectedIntegration.name}</h3>
            <div style={{ fontSize: 13, color: '#888', marginBottom: 16 }}>{selectedIntegration.type}</div>
            
            <StatusBadge 
              status={
                selectedIntegration.status === 'CONNECTED' ? 'pass' : 
                selectedIntegration.status === 'AVAILABLE' ? 'active' : 
                selectedIntegration.status === 'BLOCKED' ? 'fail' : 'notConfigured'
              } 
              label={selectedIntegration.status} 
            />

            <div style={{ marginTop: 32, display: 'flex', flexDirection: 'column', gap: 8 }}>
              {selectedIntegration.status !== 'CONNECTED' && (
                <button className="consoleBtn primary" style={{ justifyContent: 'center' }}>Connect</button>
              )}
              <button className="consoleBtn" style={{ justifyContent: 'center' }}>Configure</button>
              <button className="consoleBtn" style={{ justifyContent: 'center' }} disabled={selectedIntegration.status === 'NOT_CONFIGURED'}>Test Connection</button>
              <button className="consoleBtn" style={{ justifyContent: 'center' }} disabled={selectedIntegration.status === 'NOT_CONFIGURED'}>View Logs</button>
              {selectedIntegration.status === 'CONNECTED' && (
                <button className="consoleBtn" style={{ justifyContent: 'center', borderColor: '#F85149', color: '#F85149' }}>Disconnect</button>
              )}
            </div>
          </aside>
        )}
      </div>
    </EngineeringConsole>
  );
}
