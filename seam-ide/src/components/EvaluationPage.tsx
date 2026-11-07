import React, { useState } from 'react';
import { EngineeringConsole } from '../consoles/shared/EngineeringConsole';
import { StatusBadge, EvidenceDrawer } from '../consoles/shared/ConsoleComponents';
import '../consoles/shared/engineering-consoles.css';

export function EvaluationPage() {
  const [selectedMetric, setSelectedMetric] = useState<any>(null);

  const metrics = [
    { id: 'req', area: 'Requirement Coverage', status: 'UNKNOWN', detail: 'Requirements-to-test trace' },
    { id: 'agent', area: 'Agent Metrics', status: 'PASS', detail: 'Agent execution duration & token usage' },
    { id: 'tool', area: 'Tool Metrics', status: 'PASS', detail: 'Tool call success rate' },
    { id: 'qa', area: 'QA', status: 'UNKNOWN', detail: 'QA suite pass percentage' },
    { id: 'contract', area: 'Contracts', status: 'PASS', detail: 'Schema drift tracking' },
    { id: 'e2e', area: 'E2E', status: 'NOT_CONFIGURED', detail: 'Browser journey success' },
    { id: 'repair', area: 'Repair', status: 'PASS', detail: 'Autonomous defect repair success rate' },
    { id: 'delivery', area: 'Delivery', status: 'NOT_CONFIGURED', detail: 'Release readiness gating' },
    { id: 'rag', area: 'RAG', status: 'UNKNOWN', detail: 'Vector retrieval precision' },
    { id: 'domain', area: 'Domain Intelligence', status: 'UNKNOWN', detail: 'Domain model entity coverage' },
    { id: 'runtime', area: 'Runtime', status: 'PASS', detail: 'Uptime and resource bounds' },
    { id: 'autonomy', area: 'Autonomy', status: 'PASS', detail: 'Human intervention requests per workflow' },
  ];

  return (
    <EngineeringConsole
      title="Evaluation Center"
      description="Research & Agentic System Evaluation Metrics"
      toolbarNode={
        <>
          <button className="consoleBtn">↻ Recalculate Metrics</button>
        </>
      }
      evidenceDrawerNode={
        selectedMetric ? (
          <EvidenceDrawer title={`Evaluation Data: ${selectedMetric.area}`} defaultExpanded={true}>
            <pre style={{ fontSize: 12, color: '#ccc', margin: 0 }}>
              {`Artifact links and experiment traces for ${selectedMetric.area} not yet synthesized in this session.`}
            </pre>
          </EvidenceDrawer>
        ) : null
      }
    >
      <main style={{ padding: 0, height: '100%', overflowY: 'auto' }}>
        <table className="consoleTable">
          <thead>
            <tr>
              <th>Evaluation Area</th>
              <th>Status</th>
              <th>Detail</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {metrics.map(metric => (
              <tr 
                key={metric.id}
                onClick={() => setSelectedMetric(metric)}
                style={{ cursor: 'pointer', background: selectedMetric?.id === metric.id ? 'rgba(255,255,255,0.05)' : '' }}
              >
                <td style={{ fontWeight: 500, color: '#fff' }}>{metric.area}</td>
                <td><StatusBadge status={metric.status} /></td>
                <td style={{ color: '#888' }}>{metric.detail}</td>
                <td><span className="tableActionLink">View Experiment</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </main>
    </EngineeringConsole>
  );
}
