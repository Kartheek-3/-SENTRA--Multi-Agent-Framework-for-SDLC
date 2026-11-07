import React, { useState } from 'react';

export type ProcessItem = {
  name: string;
  status: 'RUNNING' | 'STOPPED' | 'STARTING';
  port?: number;
  pid?: number;
  type: string;
};

export type RunDebugPanelProps = {
  projectName?: string;
  onRunWorkflow: () => Promise<void>;
  onStopWorkflow: () => Promise<void>;
  onOpenRuntimeConsole: () => void;
};

export function RunDebugPanel({
  projectName = 'SEAM Workspace',
  onRunWorkflow,
  onStopWorkflow,
  onOpenRuntimeConsole,
}: RunDebugPanelProps) {
  const [selectedConfig, setSelectedConfig] = useState('Full Autonomous Pipeline');
  const [isRunning, setIsRunning] = useState(false);
  const [processes, setProcesses] = useState<ProcessItem[]>([
    { name: 'Vite Frontend Dev', status: 'RUNNING', port: 5173, pid: 16392, type: 'web' },
    { name: 'SEAM FastAPI Backend', status: 'RUNNING', port: 8000, pid: 21044, type: 'api' },
    { name: 'Docker Model Runner', status: 'RUNNING', port: 12434, pid: 8940, type: 'inference' },
    { name: 'ChromaDB Knowledge Store', status: 'RUNNING', port: 8000, type: 'vector' },
    { name: 'n8n Automation Engine', status: 'STOPPED', port: 5678, type: 'automation' },
  ]);

  const configs = [
    'Full Autonomous Pipeline',
    'Analysis & Architecture Planning',
    'Code Generation with Hot Reload',
    'Full QA & Contract Validation',
    'Targeted Defect Repair Loop',
  ];

  const handleStart = async () => {
    setIsRunning(true);
    await onRunWorkflow();
  };

  const handleStop = async () => {
    setIsRunning(false);
    await onStopWorkflow();
  };

  return (
    <div className="runDebugPanel" role="region" aria-label="Run & Debug">
      <div className="sidebarHeader">
        <span className="sidebarTitle">RUN & DEBUG</span>
        <button
          className="sidebarActionBtn"
          onClick={onOpenRuntimeConsole}
          title="Open Full Runtime Console"
        >
          ⚡
        </button>
      </div>

      {/* Target config selector */}
      <div className="runConfigSelector">
        <select
          value={selectedConfig}
          onChange={e => setSelectedConfig(e.target.value)}
          aria-label="Debug Configuration"
        >
          {configs.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
        <button
          className={`runActionBtn ${isRunning ? 'running' : ''}`}
          onClick={isRunning ? handleStop : handleStart}
          title={isRunning ? 'Stop Pipeline' : 'Start Pipeline'}
        >
          {isRunning ? '■' : '▶'}
        </button>
      </div>

      <div className="runSectionsList scrollArea">
        {/* Active Processes */}
        <div className="runSectionHeader">
          <span>ACTIVE PROCESSES ({processes.filter(p => p.status === 'RUNNING').length})</span>
        </div>
        <div className="runProcessList">
          {processes.map(proc => (
            <div className="processRow" key={proc.name}>
              <span className={`processDot ${proc.status.toLowerCase()}`} />
              <div className="processInfo">
                <span className="processName">{proc.name}</span>
                <span className="processDetail">
                  {proc.port ? `Port :${proc.port}` : ''} {proc.pid ? `(PID: ${proc.pid})` : ''}
                </span>
              </div>
              <span className={`processStatusBadge ${proc.status.toLowerCase()}`}>
                {proc.status}
              </span>
            </div>
          ))}
        </div>

        {/* Ports Mapping */}
        <div className="runSectionHeader">
          <span>PORTS MAPPING</span>
        </div>
        <div className="runPortsList">
          <div className="portRow">
            <span className="portNum">5173</span>
            <span className="portLabel">Vite IDE Frontend</span>
            <span className="portState">Active</span>
          </div>
          <div className="portRow">
            <span className="portNum">8000</span>
            <span className="portLabel">FastAPI & SSE WebSocket</span>
            <span className="portState">Active</span>
          </div>
          <div className="portRow">
            <span className="portNum">12434</span>
            <span className="portLabel">Docker Model Runner</span>
            <span className="portState">Active</span>
          </div>
        </div>

        {/* Breakpoints & Watch */}
        <div className="runSectionHeader">
          <span>AGENT EXECUTION GATES</span>
        </div>
        <div className="agentGatesList">
          <label className="gateCheckbox">
            <input type="checkbox" defaultChecked />
            <span>Break on Contract Drift Detection</span>
          </label>
          <label className="gateCheckbox">
            <input type="checkbox" defaultChecked />
            <span>Break on Security Gate Violation</span>
          </label>
          <label className="gateCheckbox">
            <input type="checkbox" />
            <span>Pause for Manual Patch Approval</span>
          </label>
        </div>
      </div>
    </div>
  );
}
