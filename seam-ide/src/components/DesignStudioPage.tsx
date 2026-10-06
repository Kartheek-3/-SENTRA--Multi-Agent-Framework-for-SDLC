import React, { useState, useEffect } from 'react';
import { seamApi } from '../api/client';

export const CANONICAL_DIAGRAMS = [
  { id: 'architecture_diagram', label: 'Architecture', category: 'High-Level Design' },
  { id: 'use_case_diagram', label: 'Use Case', category: 'Behavioral' },
  { id: 'class_diagram', label: 'Class Diagram', category: 'Structural' },
  { id: 'object_diagram', label: 'Object Diagram', category: 'Structural' },
  { id: 'sequence_diagram', label: 'Sequence', category: 'Behavioral' },
  { id: 'activity_diagram', label: 'Activity', category: 'Behavioral' },
  { id: 'dfd_level_0', label: 'DFD Level 0', category: 'Data Flow' },
  { id: 'dfd_level_1', label: 'DFD Level 1', category: 'Data Flow' },
  { id: 'erd_diagram', label: 'ERD (Database)', category: 'Data Architecture' },
  { id: 'deployment_diagram', label: 'Deployment', category: 'Infrastructure' },
];

interface DesignStudioPageProps {
  projectId: string | null;
  state: any;
  onOpenWorkspace: () => void;
}

export function DesignStudioPage({ projectId, state, onOpenWorkspace }: DesignStudioPageProps) {
  const [selectedDiagram, setSelectedDiagram] = useState<string>('architecture_diagram');
  const [diagramData, setDiagramData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [viewMode, setViewMode] = useState<'visual' | 'json' | 'mermaid'>('visual');
  const [availableList, setAvailableList] = useState<string[]>([]);
  const [copySuccess, setCopySuccess] = useState<string>('');

  useEffect(() => {
    if (!projectId) return;
    seamApi.diagrams(projectId)
      .then(res => setAvailableList(res.diagrams || []))
      .catch(() => setAvailableList([]));
  }, [projectId, state]);

  useEffect(() => {
    if (!projectId || !selectedDiagram) return;
    setLoading(true);
    seamApi.diagram(projectId, selectedDiagram)
      .then(res => setDiagramData(res))
      .catch(() => setDiagramData(null))
      .finally(() => setLoading(false));
  }, [projectId, selectedDiagram]);

  const hasPlanning = Boolean(state?.project_plan || state?.design_artifacts);
  const isAvailable = availableList.includes(selectedDiagram);

  const getStatusBadge = () => {
    if (!hasPlanning) return <span className="statusBadge waiting">REGENERATE REQUIRED</span>;
    if (isAvailable && diagramData) return <span className="statusBadge pass">VALID</span>;
    if (isAvailable && !diagramData) return <span className="statusBadge warning">STALE</span>;
    return <span className="statusBadge notConfigured">NOT_CONFIGURED</span>;
  };

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopySuccess(label);
    setTimeout(() => setCopySuccess(''), 2000);
  };

  const renderVisualCanvas = () => {
    if (!diagramData) {
      return (
        <div className="emptyState canvasEmpty">
          <span className="emptyIcon">📐</span>
          <strong>Diagram Not Yet Generated</strong>
          <p>
            {hasPlanning
              ? 'This diagram is planned. Run PlanningAgent or trigger regeneration.'
              : 'Run the SEAM workflow to analyze requirements and generate structured diagrams.'}
          </p>
          <button className="primaryButton" onClick={onOpenWorkspace}>Open Workspace</button>
        </div>
      );
    }

    const nodes = diagramData.nodes || diagramData.entities || diagramData.components || [];
    const edges = diagramData.edges || diagramData.relationships || diagramData.connections || [];

    return (
      <div className="diagramCanvasContainer">
        <div className="canvasMetaBar">
          <span className="diagramTitle">{CANONICAL_DIAGRAMS.find(d => d.id === selectedDiagram)?.label}</span>
          <span className="metaItem">Nodes: <b>{nodes.length}</b></span>
          <span className="metaItem">Edges: <b>{edges.length}</b></span>
          <span className="metaItem">Layout: <b>Hierarchical Sugiyama</b></span>
        </div>

        <div className="diagramNodesGrid">
          {nodes.length > 0 ? (
            nodes.map((node: any, idx: number) => (
              <div key={node.id || idx} className="diagramNodeCard">
                <div className="nodeHeader">
                  <span className="nodeKind">{node.type || node.role || 'Component'}</span>
                  <span className="nodeId">{node.id || `node-${idx}`}</span>
                </div>
                <div className="nodeLabel">{node.label || node.name || 'Unnamed Node'}</div>
                {node.description && <div className="nodeDesc">{node.description}</div>}
                {node.attributes && (
                  <div className="nodeAttrs">
                    {Array.isArray(node.attributes)
                      ? node.attributes.map((attr: string, i: number) => <span key={i} className="attrTag">{attr}</span>)
                      : Object.entries(node.attributes).map(([k, v]) => <span key={k} className="attrTag">{k}: {String(v)}</span>)
                    }
                  </div>
                )}
              </div>
            ))
          ) : (
            <div className="structuredSummary">
              <pre>{JSON.stringify(diagramData, null, 2)}</pre>
            </div>
          )}
        </div>

        {edges.length > 0 && (
          <div className="diagramEdgesList">
            <h4>Connections & Data Flows</h4>
            <div className="edgeBadges">
              {edges.map((edge: any, i: number) => (
                <div key={i} className="edgeBadge">
                  <span className="edgeSource">{edge.source || edge.from}</span>
                  <span className="edgeArrow">──►</span>
                  <span className="edgeTarget">{edge.target || edge.to}</span>
                  {edge.label && <span className="edgeDesc">({edge.label})</span>}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="designStudioFrame">
      <header className="designStudioHeader">
        <div>
          <h1>Design Studio</h1>
          <p className="subtitle">Requirement-Driven High-Quality System Diagrams (10 Canonical Architectures)</p>
        </div>
        <div className="designStudioActions">
          {getStatusBadge()}
          <div className="viewToggleGroup">
            <button className={viewMode === 'visual' ? 'active' : ''} onClick={() => setViewMode('visual')}>Visual</button>
            <button className={viewMode === 'mermaid' ? 'active' : ''} onClick={() => setViewMode('mermaid')}>Mermaid</button>
            <button className={viewMode === 'json' ? 'active' : ''} onClick={() => setViewMode('json')}>JSON</button>
          </div>
          {diagramData && (
            <button
              className="exportBtn"
              onClick={() => copyToClipboard(JSON.stringify(diagramData, null, 2), 'JSON Copied')}
            >
              {copySuccess === 'JSON Copied' ? '✓ Copied' : 'Export JSON'}
            </button>
          )}
        </div>
      </header>

      <div className="designStudioLayout">
        <aside className="diagramNavSidebar">
          <div className="sidebarHeading">CANONICAL DIAGRAMS</div>
          {CANONICAL_DIAGRAMS.map(diag => {
            const active = selectedDiagram === diag.id;
            const available = availableList.includes(diag.id);
            return (
              <button
                key={diag.id}
                className={`diagramNavItem ${active ? 'active' : ''}`}
                onClick={() => setSelectedDiagram(diag.id)}
              >
                <div className="navItemContent">
                  <span className="diagName">{diag.label}</span>
                  <span className="diagCategory">{diag.category}</span>
                </div>
                <span className={`diagDot ${available ? 'available' : 'planned'}`} title={available ? 'Generated' : 'Planned'} />
              </button>
            );
          })}
        </aside>

        <main className="diagramCanvasWrapper scrollArea">
          {loading ? (
            <div className="diagramLoading">
              <div className="spinner" />
              <span>Rendering {CANONICAL_DIAGRAMS.find(d => d.id === selectedDiagram)?.label}...</span>
            </div>
          ) : viewMode === 'visual' ? (
            renderVisualCanvas()
          ) : viewMode === 'mermaid' ? (
            <div className="mermaidExportView">
              <div className="mermaidHeader">
                <span>Mermaid Architecture Definition</span>
                <button
                  className="copyBtn"
                  onClick={() => copyToClipboard(diagramData?.mermaid || `graph TD\n  A[${selectedDiagram}] --> B[Component]`, 'Mermaid Copied')}
                >
                  {copySuccess === 'Mermaid Copied' ? '✓ Copied' : 'Copy Mermaid'}
                </button>
              </div>
              <pre className="codeBlock">
                {diagramData?.mermaid || `%% Mermaid representation of ${selectedDiagram}\ngraph TD\n  Client[Client / Web UI] --> API[FastAPI Backend]\n  API --> RAG[ChromaDB Vector Store]\n  API --> Agents[LangGraph 6 Canonical Agents]\n  Agents --> Delivery[Deployment Pipeline]`}
              </pre>
            </div>
          ) : (
            <div className="jsonExportView">
              <pre className="codeBlock">
                {diagramData ? JSON.stringify(diagramData, null, 2) : '{\n  "status": "NOT_AVAILABLE",\n  "detail": "Run planning workflow to generate diagram schema."\n}'}
              </pre>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
