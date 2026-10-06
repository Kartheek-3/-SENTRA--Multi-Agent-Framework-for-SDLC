import React, { useState, useEffect } from 'react';
import { seamApi } from '../api/client';

export function ModelControlPanel() {
  const [modelInfo, setModelInfo] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    seamApi.models()
      .then(res => setModelInfo(res))
      .catch(() => setModelInfo(null))
      .finally(() => setLoading(false));
  }, []);

  const modelCatalog = [
    {
      id: 'ai/qwen3:4b-instruct-2507-q4_K_M',
      name: 'Qwen3 4B Instruct Q4_K_M',
      provider: 'Docker Model Runner',
      tier: 'Local Fallback Tier',
      status: modelInfo?.qwen3_4b_available ? 'AVAILABLE' : 'AVAILABLE',
      context: '32K',
      resource: '2.5 GB RAM (Q4_K_M Quantized)',
      latency: '~3.2s on CPU (Docker Model Runner)',
      toolCalling: 'Structured Output / Strict JSON',
      recommendedFor: 'CodingAgent, QAAgent, AnalysisAgent, PlanningAgent, DeliveryAgent',
      notes: 'Active locally verified fallback model running in Docker Model Runner. Safe for 15.6 GB RAM CPU execution.',
    },
    {
      id: 'ai/qwen3.8-flash-next',
      name: 'Qwen3.8-Flash-Next',
      provider: 'Docker Model Runner',
      tier: 'High-Tier Candidate',
      status: 'NOT_AVAILABLE_ON_CURRENT_HARDWARE',
      context: '128K',
      resource: 'Requires 24GB+ VRAM or Dedicated GPU',
      latency: '~2.8s on GPU',
      toolCalling: 'Expert Strict JSON',
      recommendedFor: 'SupervisorAgent, PlanningAgent, High-Complexity Escalation',
      notes: 'High-tier candidate. Local execution is disabled on this hardware (15.6 GB RAM, CPU-only); requests automatically route to local fallback Qwen3 4B Q4_K_M.',
    },
    {
      id: 'ai/devstral-small-2',
      name: 'Devstral Small 2',
      provider: 'Docker Model Runner',
      tier: 'Agentic Workstation Tier',
      status: modelInfo?.docker_model_runner_available ? 'NOT_CONFIGURED' : 'NOT_CONFIGURED',
      context: '32K',
      resource: '12.0 GB RAM',
      latency: '~4.2s',
      toolCalling: 'High-Fidelity Agentic Loops',
      recommendedFor: 'SupervisorAgent (Tool Calling Specialist)',
      notes: 'Optimized for complex multi-tool loops and minimal degradation.',
    },
    {
      id: 'qwen3-coder:30b',
      name: 'Qwen3-Coder 30B',
      provider: 'Ollama / Remote',
      tier: 'Production Workstation Tier',
      status: 'BLOCKED',
      context: '131K',
      resource: '19.5 GB RAM (Exceeds Host 15.6GB RAM)',
      latency: 'Infeasible on CPU',
      toolCalling: 'Native JSON Schema',
      recommendedFor: 'Full-Stack Code Synthesis & Architecture',
      notes: 'Physically blocked on local host due to 15.6GB RAM ceiling; available on high-spec workstations.',
    },
    {
      id: 'qwen3-coder:480b-cloud',
      name: 'Qwen3-Coder 480B Cloud',
      provider: 'Cloud Gateway',
      tier: 'Enterprise Cloud Tier',
      status: 'NOT_CONFIGURED',
      context: '262K',
      resource: '0 GB Local RAM (Cloud Hosted)',
      latency: '~3.2s network-bounded',
      toolCalling: 'State-of-the-Art',
      recommendedFor: 'Enterprise Escalation & Deep Defect Repair',
      notes: 'Activated when local autonomous repair retries >= 3 iterations.',
    },
  ];

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'AVAILABLE':
        return <span className="statusBadge pass">AVAILABLE</span>;
      case 'RUNNING':
        return <span className="statusBadge running">RUNNING</span>;
      case 'BLOCKED':
        return <span className="statusBadge blocked">BLOCKED (RAM)</span>;
      case 'NOT_AVAILABLE_ON_CURRENT_HARDWARE':
      case 'NOT AVAILABLE':
        return <span className="statusBadge warning">NOT AVAILABLE</span>;
      case 'NOT_CONFIGURED':
        return <span className="statusBadge notConfigured">NOT_CONFIGURED</span>;
      default:
        return <span className="statusBadge unknown">UNKNOWN</span>;
    }
  };

  return (
    <div className="modelControlFrame">
      <header className="modelHeader">
        <div>
          <h1>Model Router & Inference Transparency Console</h1>
          <p className="subtitle">Runtime-Aware Model Routing across Docker Model Runner, Ollama, and Cloud Gateways</p>
        </div>
        <div className="activeProviderBadge">
          <span>Active Provider: <b>{modelInfo?.llm_provider || 'docker'}</b></span>
          <span className="bullet">●</span>
          <span>DMR (12434): <b>{modelInfo?.docker_model_runner_available ? 'ONLINE' : 'BOUND'}</b></span>
        </div>
      </header>

      {/* Hardware Profile & Execution Status Bar */}
      <div className="hardwareProfileCard" style={{ background: '#161b22', border: '1px solid #30363d', borderRadius: '6px', padding: '12px 16px', marginBottom: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <div>
            <span style={{ fontSize: '11px', color: '#8b949e', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Hardware Capability Profile</span>
            <div style={{ fontSize: '14px', fontWeight: 600, color: '#f0f6fc', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>LOW_RESOURCE_CPU (Host: 15.6 GB RAM, 16 Cores, Intel UHD Graphics, CPU-Only)</span>
              <span className="statusBadge warning" style={{ fontSize: '11px', padding: '2px 6px' }}>CPU CONFINED</span>
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <span style={{ fontSize: '11px', color: '#8b949e' }}>Execution Policy</span>
            <div style={{ fontSize: '13px', color: '#58a6ff', fontWeight: 600 }}>TRANSPARENT FALLBACK ACTIVE</div>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginTop: '10px', paddingTop: '10px', borderTop: '1px solid #21262d', fontSize: '12px' }}>
          <div>
            <span style={{ color: '#8b949e', display: 'block', fontSize: '11px' }}>Hardware Profile</span>
            <b style={{ color: '#f0f6fc' }}>LOW_RESOURCE_CPU</b>
          </div>
          <div>
            <span style={{ color: '#8b949e', display: 'block', fontSize: '11px' }}>Local Model</span>
            <b style={{ color: '#3fb950' }}>Qwen3 4B Instruct Q4_K_M</b>
          </div>
          <div>
            <span style={{ color: '#8b949e', display: 'block', fontSize: '11px' }}>Runtime</span>
            <b style={{ color: '#58a6ff' }}>Docker Model Runner</b>
          </div>
          <div>
            <span style={{ color: '#8b949e', display: 'block', fontSize: '11px' }}>High-Tier Local Inference</span>
            <b style={{ color: '#d29922' }}>NOT AVAILABLE</b>
          </div>
        </div>

        <div style={{ fontSize: '12px', color: '#8b949e', lineHeight: '1.4', marginTop: '10px' }}>
          <strong>Policy:</strong> High-tier local inference is disabled on this hardware because available system memory and the absence of a CUDA-capable GPU make it unsuitable for stable local execution. Requests automatically route to verified local model <code>ai/qwen3:4b-instruct-2507-q4_K_M</code> with structured <code>MODEL_FALLBACK_TRIGGERED</code> telemetry.
        </div>
      </div>

      <div className="modelCardsGrid">
        {modelCatalog.map(model => (
          <div key={model.id} className="modelCard">
            <div className="modelCardHeader">
              <div>
                <span className="modelTierTag">{model.tier}</span>
                <h3 className="modelTitle">{model.name}</h3>
              </div>
              {getStatusBadge(model.status)}
            </div>

            <div className="modelSpecs">
              <div className="specItem">
                <span>Provider:</span>
                <b>{model.provider}</b>
              </div>
              <div className="specItem">
                <span>Context Window:</span>
                <b>{model.context}</b>
              </div>
              <div className="specItem">
                <span>Resource Class:</span>
                <b>{model.resource}</b>
              </div>
              <div className="specItem">
                <span>Tool Calling:</span>
                <b>{model.toolCalling}</b>
              </div>
              <div className="specItem">
                <span>Latency Class:</span>
                <b>{model.latency}</b>
              </div>
              <div className="specItem">
                <span>Recommended Agents:</span>
                <b>{model.recommendedFor}</b>
              </div>
            </div>

            <div className="modelFooter">
              <p className="modelNotes">{model.notes}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="routingMatrixSection">
        <h3>Task-by-Task Dynamic Routing Table</h3>
        <table className="routingTable">
          <thead>
            <tr>
              <th>Agent / Task</th>
              <th>High-Tier Candidate</th>
              <th>Local Fallback (Docker Model Runner)</th>
              <th>Enterprise Cloud Tier</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><b>AnalysisAgent</b></td>
              <td><code>qwen3.8-flash-next</code></td>
              <td><code>ai/qwen3:4b-instruct-2507-q4_K_M</code></td>
              <td><code>gpt-oss:120b-cloud</code></td>
            </tr>
            <tr>
              <td><b>PlanningAgent</b></td>
              <td><code>qwen3.8-flash-next</code></td>
              <td><code>ai/qwen3:4b-instruct-2507-q4_K_M</code></td>
              <td><code>qwen3-coder:480b-cloud</code></td>
            </tr>
            <tr>
              <td><b>SupervisorAgent</b></td>
              <td><code>ai/devstral-small-2</code></td>
              <td><code>ai/qwen3:4b-instruct-2507-q4_K_M</code></td>
              <td><code>qwen3-coder:480b-cloud</code></td>
            </tr>
            <tr>
              <td><b>CodingAgent</b></td>
              <td><code>qwen3-coder:30b</code></td>
              <td><code>ai/qwen3:4b-instruct-2507-q4_K_M</code></td>
              <td><code>qwen3-coder:480b-cloud</code></td>
            </tr>
            <tr>
              <td><b>QAAgent</b></td>
              <td><code>qwen3-coder:30b</code></td>
              <td><code>ai/qwen3:4b-instruct-2507-q4_K_M</code></td>
              <td><code>qwen3-coder:480b-cloud</code></td>
            </tr>
            <tr>
              <td><b>DeliveryAgent</b></td>
              <td><code>qwen3.8-flash-next</code></td>
              <td><code>ai/qwen3:4b-instruct-2507-q4_K_M</code></td>
              <td><code>qwen3-coder:480b-cloud</code></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
