import React, { useState } from 'react';
import { EngineeringConsole } from '../consoles/shared/EngineeringConsole';
import { StatusBadge, EvidenceDrawer } from '../consoles/shared/ConsoleComponents';
import '../consoles/shared/engineering-consoles.css';

interface ContractsPageProps {
  state: any;
  onOpenWorkspace: () => void;
}

export function ContractsPage({ state, onOpenWorkspace }: ContractsPageProps) {
  const [filter, setFilter] = useState<'All' | 'Healthy' | 'Drift' | 'Missing' | 'Invalid'>('All');
  const [selectedContract, setSelectedContract] = useState<any>(null);

  const plan = state?.project_plan;
  const systemDesign = plan?.system_design;
  const contractIssues = state?.contract_issues || [];

  // Fallback data for demonstration if backend data is sparse
  const endpoints = systemDesign?.api_endpoints || [
    { path: '/api/v1/health', method: 'GET', frontend: 'HealthClient', database: 'None', status: 'MATCH' },
    { path: '/api/v1/auth/login', method: 'POST', frontend: 'AuthClient.login', database: 'users table', status: 'MATCH' },
    { path: '/api/v1/items', method: 'GET', frontend: 'ItemsClient.list', database: 'items view', status: 'DRIFT' },
    { path: '/api/v1/items', method: 'POST', frontend: 'Missing', database: 'items table', status: 'MISSING' },
  ];

  const filteredEndpoints = endpoints.filter((ep: any) => {
    if (filter === 'All') return true;
    if (filter === 'Healthy') return ep.status === 'MATCH';
    if (filter === 'Drift') return ep.status === 'DRIFT';
    if (filter === 'Missing') return ep.status === 'MISSING';
    if (filter === 'Invalid') return ep.status === 'INVALID';
    return true;
  });

  const hasContracts = Boolean(plan || state?.frontend_architecture_plan || state?.full_stack_contract);
  const driftCount = endpoints.filter((ep: any) => ep.status === 'DRIFT' || ep.status === 'MISSING').length;
  
  const consoleStatus = !hasContracts ? 'NOT_CONFIGURED' : driftCount === 0 ? 'PASS' : 'WARNING';

  return (
    <EngineeringConsole
      title="Contract Intelligence"
      statusNode={<StatusBadge status={consoleStatus} label={driftCount === 0 ? 'ZERO DRIFT' : `${driftCount} ISSUES`} />}
      description="Three-Way Schema Parity: Frontend Architecture ⟷ SystemDesign API ⟷ Database Relational Schema"
      toolbarNode={
        <>
          <div className="consoleTabs" style={{ borderBottom: 'none' }}>
            {['All', 'Healthy', 'Drift', 'Missing', 'Invalid'].map(f => (
              <div 
                key={f} 
                className={`consoleTab ${filter === f ? 'active' : ''}`}
                onClick={() => setFilter(f as any)}
                style={{ padding: '4px 12px' }}
              >
                {f}
              </div>
            ))}
          </div>
          <div style={{ flex: 1 }} />
          <button className="consoleBtn">↻ Rescan Contracts</button>
        </>
      }
      evidenceDrawerNode={
        contractIssues.length > 0 ? (
          <EvidenceDrawer title="Drift Evidence">
            <pre style={{ fontSize: 12, color: '#F85149', margin: 0, padding: 12 }}>
              {JSON.stringify(contractIssues, null, 2)}
            </pre>
          </EvidenceDrawer>
        ) : null
      }
    >
      <div style={{ display: 'flex', height: '100%' }}>
        <main style={{ flex: 1, overflowY: 'auto' }}>
          <table className="consoleTable">
            <thead>
              <tr>
                <th>Method</th>
                <th>Endpoint</th>
                <th>Frontend</th>
                <th>API</th>
                <th>Database</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {filteredEndpoints.map((ep: any, idx: number) => (
                <tr 
                  key={idx} 
                  onClick={() => setSelectedContract(ep)}
                  style={{ cursor: 'pointer', background: selectedContract?.path === ep.path ? 'rgba(255,255,255,0.05)' : '' }}
                >
                  <td><span style={{ color: ep.method === 'GET' ? '#58A6FF' : ep.method === 'POST' ? '#73C991' : '#CCA700', fontWeight: 600 }}>{ep.method}</span></td>
                  <td style={{ fontFamily: 'monospace' }}>{ep.path}</td>
                  <td style={{ color: ep.frontend === 'Missing' ? '#888' : '#ccc' }}>{ep.frontend}</td>
                  <td>OpenAPI 3.1</td>
                  <td>{ep.database}</td>
                  <td><StatusBadge status={ep.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </main>

        {selectedContract && (
          <aside style={{ width: 350, borderLeft: '1px solid #2b2b2b', background: '#1a1a1a', padding: 20, overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h3 style={{ margin: 0, fontSize: 16, color: '#fff' }}>Contract Inspector</h3>
              <button className="consoleBtn" style={{ padding: '2px 8px' }} onClick={() => setSelectedContract(null)}>✕</button>
            </div>
            
            <div style={{ marginBottom: 16 }}>
              <StatusBadge status={selectedContract.status} />
            </div>

            <div style={{ marginBottom: 12 }}>
              <div style={{ fontSize: 11, color: '#888' }}>Endpoint</div>
              <div style={{ fontSize: 13, color: '#ccc', fontFamily: 'monospace' }}>{selectedContract.method} {selectedContract.path}</div>
            </div>

            <div style={{ marginBottom: 12 }}>
              <div style={{ fontSize: 11, color: '#888' }}>Frontend Usage</div>
              <div style={{ fontSize: 13, color: '#58A6FF', cursor: 'pointer' }} onClick={onOpenWorkspace}>
                {selectedContract.frontend} ↗
              </div>
            </div>

            <div style={{ marginBottom: 12 }}>
              <div style={{ fontSize: 11, color: '#888' }}>Database Mapping</div>
              <div style={{ fontSize: 13, color: '#ccc' }}>{selectedContract.database}</div>
            </div>

            <div style={{ marginTop: 24, padding: 12, background: '#242424', borderRadius: 4, border: '1px solid #3c3c3c' }}>
              <div style={{ fontSize: 11, color: '#888', marginBottom: 4 }}>Request Schema</div>
              <pre style={{ margin: 0, fontSize: 11, color: '#aaa' }}>
                {`{\n  "type": "object",\n  "properties": {}\n}`}
              </pre>
            </div>

            <div style={{ marginTop: 12, padding: 12, background: '#242424', borderRadius: 4, border: '1px solid #3c3c3c' }}>
              <div style={{ fontSize: 11, color: '#888', marginBottom: 4 }}>Response Schema</div>
              <pre style={{ margin: 0, fontSize: 11, color: '#aaa' }}>
                {`{\n  "status": 200,\n  "type": "object"\n}`}
              </pre>
            </div>

            {selectedContract.status !== 'MATCH' && (
              <div style={{ marginTop: 24 }}>
                <button className="consoleBtn primary" style={{ width: '100%', justifyContent: 'center' }}>Start Repair Workflow</button>
              </div>
            )}
          </aside>
        )}
      </div>
    </EngineeringConsole>
  );
}
