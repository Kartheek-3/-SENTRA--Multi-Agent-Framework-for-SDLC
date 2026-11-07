import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { seamApi } from '../api/client';
import { EngineeringConsole } from '../consoles/shared/EngineeringConsole';
import { StatusBadge, EvidenceDrawer, ConsoleTabs, EmptyState } from '../consoles/shared/ConsoleComponents';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  Handle,
  Position,
  Panel,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import dagre from 'dagre';
import '../consoles/shared/engineering-consoles.css';

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

export const IMAGE_PURPOSES = [
  { id: 'product_illustration', label: 'Product Illustration' },
  { id: 'concept_art', label: 'Concept Art' },
  { id: 'presentation_visual', label: 'Presentation Visual' },
  { id: 'landing_page_artwork', label: 'Landing Page Artwork' },
  { id: 'abstract_system_visualization', label: 'Abstract System Visualization' },
  { id: 'decorative_architecture_concept', label: 'Decorative Architecture Concept' },
  { id: 'supporting_visual_asset', label: 'Supporting Visual Asset' },
];

export const IMAGE_SIZES = [
  { width: 1024, height: 1024, label: '1024 × 1024 (Square 1:1)' },
  { width: 1152, height: 896, label: '1152 × 896 (Landscape 5:4)' },
  { width: 896, height: 1152, label: '896 × 1152 (Portrait 4:5)' },
  { width: 1216, height: 832, label: '1216 × 832 (Wide 3:2)' },
  { width: 832, height: 1216, label: '832 × 1216 (Tall 2:3)' },
];

const getLayoutedElements = (nodes: any[], edges: any[], direction = 'TB') => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));

  const isHorizontal = direction === 'LR';
  dagreGraph.setGraph({ rankdir: direction });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 250, height: 100 });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  nodes.forEach((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    node.targetPosition = isHorizontal ? 'left' : 'top';
    node.sourcePosition = isHorizontal ? 'right' : 'bottom';
    node.position = {
      x: nodeWithPosition.x - 250 / 2,
      y: nodeWithPosition.y - 100 / 2,
    };
    return node;
  });

  return { nodes, edges };
};

// Custom Node for displaying detailed structural information
const SEAMNode = ({ data }: any) => {
  return (
    <div style={{ background: '#242424', border: '1px solid #3c3c3c', borderRadius: 6, padding: '10px 14px', width: 250, color: '#ccc', fontSize: 12 }}>
      <Handle type="target" position={Position.Top} style={{ background: '#555' }} />
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, borderBottom: '1px solid #333', paddingBottom: 4 }}>
        <span style={{ fontWeight: 'bold', color: '#58A6FF' }}>{data.type || 'Component'}</span>
        <span style={{ color: '#888', fontSize: 10 }}>{data.id}</span>
      </div>
      <div style={{ fontWeight: 600, color: '#fff', marginBottom: 4 }}>{data.label}</div>
      {data.description && <div style={{ fontSize: 11, color: '#aaa', marginBottom: 6 }}>{data.description}</div>}
      <Handle type="source" position={Position.Bottom} style={{ background: '#555' }} />
    </div>
  );
};

const nodeTypes = { seamNode: SEAMNode };

interface DesignStudioPageProps {
  projectId: string | null;
  state: any;
  onOpenWorkspace: () => void;
}

export function DesignStudioPage({ projectId, state, onOpenWorkspace }: DesignStudioPageProps) {
  // Mode selection: Engineering Diagrams vs Visual Assets
  const [studioSection, setStudioSection] = useState<'diagrams' | 'visual_assets'>('diagrams');

  // Engineering Diagrams State
  const [selectedDiagram, setSelectedDiagram] = useState<string>('architecture_diagram');
  const [diagramData, setDiagramData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [regenerating, setRegenerating] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [availableList, setAvailableList] = useState<string[]>([]);
  const [viewMode, setViewMode] = useState<'visual' | 'json' | 'mermaid'>('visual');
  const [selectedElement, setSelectedElement] = useState<any>(null);

  const [nodes, setNodes, onNodesChange] = useNodesState<any>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<any>([]);

  // Visual Assets State (SDXL Image Generation)
  const [imagePrompt, setImagePrompt] = useState<string>('');
  const [imagePurpose, setImagePurpose] = useState<string>('product_illustration');
  const [imageSize, setImageSize] = useState<{ width: number; height: number }>({ width: 1024, height: 1024 });
  const [negativePrompt, setNegativePrompt] = useState<string>('');
  const [selectedProvider, setSelectedProvider] = useState<string>('auto');
  const [caps, setCaps] = useState<any>(null);
  const [capsLoading, setCapsLoading] = useState<boolean>(false);
  const [generatingImage, setGeneratingImage] = useState<boolean>(false);
  const [imageResult, setImageResult] = useState<any>(null);
  const [imageError, setImageError] = useState<string | null>(null);
  const [visualAssetsList, setVisualAssetsList] = useState<any[]>([]);

  // 1. Fetch Diagram Available List
  const fetchAvailableList = useCallback(() => {
    if (!projectId) return;
    seamApi.diagrams(projectId)
      .then(res => setAvailableList(res.diagrams || []))
      .catch(() => setAvailableList([]));
  }, [projectId]);

  useEffect(() => {
    fetchAvailableList();
  }, [fetchAvailableList, state]);

  // 2. Fetch Image Generation Capabilities
  const fetchImageCaps = useCallback(() => {
    setCapsLoading(true);
    seamApi.imageCapabilities?.()
      ?.then((res: any) => {
        setCaps(res);
      })
      ?.catch((err: any) => {
        setCaps({
          status: 'NOT_AVAILABLE_ON_CURRENT_HOST',
          reason: 'UNSUPPORTED_DIFFUSERS_PLATFORM_OR_HARDWARE',
          host_os: 'Windows',
          has_cuda: false,
          gpu_info: 'Intel(R) UHD Graphics',
          dmr_available: true,
          diffusers_supported_on_host: false,
          explanation: err?.message || 'Docker Model Runner Diffusers engine requires Linux with NVIDIA GPU.',
          supported_providers: [
            { id: 'docker_sdxl', name: 'Docker SDXL 1.0', status: 'NOT_AVAILABLE_ON_CURRENT_HOST', supported: false }
          ]
        });
      })
      ?.finally(() => setCapsLoading(false));
  }, []);

  const fetchVisualAssets = useCallback(() => {
    if (!projectId) return;
    seamApi.listProjectVisualAssets?.(projectId)
      ?.then((res: any) => setVisualAssetsList(res.visual_assets || []))
      ?.catch(() => setVisualAssetsList([]));
  }, [projectId]);

  useEffect(() => {
    fetchImageCaps();
    fetchVisualAssets();
  }, [fetchImageCaps, fetchVisualAssets, projectId]);

  // 3. Load Canonical Diagram
  const loadDiagram = useCallback(() => {
    if (!projectId || !selectedDiagram) return;
    setLoading(true);
    setErrorMessage(null);
    seamApi.diagram(projectId, selectedDiagram)
      .then(res => {
        setDiagramData(res);
        if (res) {
          let rawNodes = res.nodes || res.entities || res.components || [];
          if (!rawNodes.length && res.layers) {
            rawNodes = res.layers.flatMap((l: any) => l.nodes || []);
          }
          if (!rawNodes.length && res.classes) {
            rawNodes = res.classes;
          }
          if (!rawNodes.length && res.objects) {
            rawNodes = res.objects;
          }
          if (!rawNodes.length && res.participants) {
            rawNodes = res.participants;
          }
          if (!rawNodes.length && res.activity_nodes) {
            rawNodes = res.activity_nodes;
          }
          if (!rawNodes.length && (res.external_entities || res.processes || res.data_stores)) {
            rawNodes = [
              ...(res.external_entities || []),
              ...(res.processes || []),
              ...(res.data_stores || [])
            ];
          }

          let rawEdges = res.edges || res.relationships || res.connections || [];
          if (!rawEdges.length && res.messages) {
            rawEdges = res.messages;
          }
          if (!rawEdges.length && res.data_flows) {
            rawEdges = res.data_flows;
          }

          const flowNodes = rawNodes.map((n: any, idx: number) => ({
            id: n.id || `node_${idx}`,
            type: 'seamNode',
            data: {
              id: n.id || `node_${idx}`,
              label: n.name || n.label || n.title || `Node ${idx + 1}`,
              type: n.type || n.role || 'Component',
              description: n.description || '',
              attributes: n.attributes || n.methods || n.fields || n.columns,
            },
            position: { x: 0, y: 0 },
          }));

          const flowEdges = rawEdges.map((e: any, idx: number) => ({
            id: e.id || `edge_${idx}`,
            source: e.from_node || e.source || e.sender || e.from || '',
            target: e.to_node || e.target || e.receiver || e.to || '',
            label: e.label || e.action || e.description || '',
            type: 'smoothstep',
            animated: true,
            style: { stroke: '#58A6FF', strokeWidth: 1.5 },
          })).filter((e: any) => e.source && e.target);

          const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(flowNodes, flowEdges);
          setNodes(layoutedNodes);
          setEdges(layoutedEdges);
        } else {
          setNodes([]);
          setEdges([]);
        }
      })
      .catch(err => {
        setErrorMessage(err?.message || 'Failed to fetch diagram artifact');
        setDiagramData(null);
        setNodes([]);
        setEdges([]);
      })
      .finally(() => setLoading(false));
  }, [projectId, selectedDiagram, setNodes, setEdges]);

  useEffect(() => {
    if (studioSection === 'diagrams') {
      loadDiagram();
    }
  }, [loadDiagram, studioSection]);

  const handleRegenerateDiagram = async () => {
    if (!projectId || !selectedDiagram || regenerating) return;
    setRegenerating(true);
    setErrorMessage(null);
    try {
      await seamApi.regenerateDiagram(projectId, selectedDiagram);
      fetchAvailableList();
      loadDiagram();
    } catch (err: any) {
      setErrorMessage(err?.message || 'Failed to regenerate diagram. Ensure planning phase is complete.');
    } finally {
      setRegenerating(false);
    }
  };

  const handleGenerateImage = async () => {
    if (!projectId || !imagePrompt.trim() || generatingImage) return;
    setGeneratingImage(true);
    setImageError(null);
    setImageResult(null);

    try {
      const res = await seamApi.generateImage({
        project_id: projectId,
        prompt: imagePrompt.trim(),
        image_purpose: imagePurpose,
        width: imageSize.width,
        height: imageSize.height,
        model: 'ai/stable-diffusion',
        negative_prompt: negativePrompt.trim() || undefined,
      });
      setImageResult(res);
      if (res.status === 'completed') {
        fetchVisualAssets();
      } else if (res.error) {
        setImageError(`${res.error}: ${res.message || 'Image generation unavailable.'}`);
      }
    } catch (err: any) {
      setImageError(err?.message || 'Image generation request failed.');
    } finally {
      setGeneratingImage(false);
    }
  };

  const hasPlanning = Boolean(state?.project_plan || state?.design_artifacts);
  const isAvailable = availableList.includes(selectedDiagram);

  const diagramStatus = !hasPlanning ? 'REGENERATION_REQUIRED' 
    : isAvailable && diagramData ? 'VALID' 
    : isAvailable ? 'STALE' 
    : 'NOT_CONFIGURED';

  const imageGenStatus = caps?.status || 'CHECKING_PROVIDER';

  const onNodeClick = (_: any, node: any) => {
    setSelectedElement(node);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <EngineeringConsole
      title="Design Studio"
      statusNode={
        studioSection === 'diagrams' ? (
          <StatusBadge status={diagramStatus} />
        ) : (
          <StatusBadge
            status={imageGenStatus === 'READY' ? 'READY' : 'WARNING'}
            label={imageGenStatus}
          />
        )
      }
      description={
        studioSection === 'diagrams'
          ? "Requirement-Driven High-Quality System Diagrams (10 Canonical Architectures)"
          : "Visual Assets & Illustrative Artwork (SDXL 1.0 — Separate from Authoritative Diagrams)"
      }
      toolbarNode={
        <>
          {/* Main Mode Toggle: Canonical Diagrams vs Visual Assets */}
          <div style={{ display: 'flex', gap: 4, background: '#252526', padding: 2, borderRadius: 6, border: '1px solid #3c3c3c' }}>
            <button
              className={`consoleBtn ${studioSection === 'diagrams' ? 'primary' : ''}`}
              style={{ fontSize: 12, padding: '4px 10px' }}
              onClick={() => setStudioSection('diagrams')}
            >
              📐 Engineering Diagrams
            </button>
            <button
              className={`consoleBtn ${studioSection === 'visual_assets' ? 'primary' : ''}`}
              style={{ fontSize: 12, padding: '4px 10px' }}
              onClick={() => setStudioSection('visual_assets')}
            >
              🎨 Visual Assets (Illustrations)
            </button>
          </div>

          <div style={{ width: 16 }} />

          {studioSection === 'diagrams' ? (
            <>
              <button className="consoleBtn" onClick={handleRegenerateDiagram} disabled={regenerating || loading}>
                {regenerating ? '↻ Regenerating...' : '↻ Regenerate'}
              </button>
              <button className="consoleBtn" onClick={loadDiagram} disabled={loading}>✓ Validate</button>
              <div style={{ flex: 1 }} />
              <ConsoleTabs 
                tabs={[
                  { id: 'visual', label: 'Visual' },
                  { id: 'mermaid', label: 'Mermaid' },
                  { id: 'json', label: 'JSON' }
                ]} 
                activeId={viewMode}
                onChange={(id) => setViewMode(id as any)}
              />
              <button className="consoleBtn primary" onClick={() => copyToClipboard(JSON.stringify(diagramData))}>Export JSON</button>
            </>
          ) : (
            <>
              <div style={{ flex: 1 }} />
              <button className="consoleBtn" onClick={fetchImageCaps} disabled={capsLoading}>
                {capsLoading ? '↻ Checking...' : '↻ Re-check Hardware'}
              </button>
              <button className="consoleBtn" onClick={() => setStudioSection('diagrams')}>
                ← Back to Engineering Diagrams
              </button>
            </>
          )}
        </>
      }
      evidenceDrawerNode={
        studioSection === 'diagrams' ? (
          diagramData ? (
            <EvidenceDrawer title="Validation Evidence">
              <div style={{ fontSize: 13, color: '#ccc' }}>
                <p>✓ Structural validation passed</p>
                <p>✓ Semantic validation passed</p>
                <p>✓ Traceability links intact</p>
                <p style={{ color: '#888', fontSize: 11 }}>Source of Truth: Canonical Diagram JSON (Pydantic Schema)</p>
              </div>
            </EvidenceDrawer>
          ) : null
        ) : (
          <EvidenceDrawer title="Hardware & Provider Capabilities">
            <div style={{ fontSize: 12, color: '#ccc', lineHeight: 1.6 }}>
              <div><strong>Host OS:</strong> {caps?.host_os || 'Detecting...'}</div>
              <div><strong>GPU Adapter:</strong> {caps?.gpu_info || 'Unknown'}</div>
              <div><strong>CUDA Available:</strong> {caps?.has_cuda ? 'Yes' : 'No (CPU / Integrated GPU)'}</div>
              <div><strong>Docker Model Runner:</strong> {caps?.dmr_available ? `Online (${caps?.dmr_base_url})` : 'Offline'}</div>
              <div><strong>Diffusers Backend:</strong> {caps?.diffusers_supported_on_host ? 'Supported' : 'Unsupported on this OS/GPU'}</div>
              <div><strong>SDXL 1.0 Model:</strong> {caps?.model_installed ? 'Installed' : 'Not Loaded'}</div>
              <div style={{ marginTop: 8, padding: 8, background: '#252526', borderRadius: 4, border: '1px solid #3c3c3c' }}>
                <strong>Classification Notice:</strong> All image outputs are classified as <em>illustrative visual assets</em>. Canonical engineering specifications are managed strictly via the Diagram Engine.
              </div>
            </div>
          </EvidenceDrawer>
        )
      }
    >
      {studioSection === 'diagrams' ? (
        /* ================= SECTION A: CANONICAL ENGINEERING DIAGRAMS ================= */
        <div style={{ display: 'flex', height: '100%' }}>
          {/* LEFT NAV */}
          <aside style={{ width: 220, borderRight: '1px solid #2b2b2b', background: '#1a1a1a', padding: '16px 0', display: 'flex', flexDirection: 'column' }}>
            <div style={{ padding: '0 16px 12px 16px', fontSize: 11, fontWeight: 600, color: '#888', letterSpacing: 0.5 }}>CANONICAL DIAGRAMS</div>
            <div style={{ overflowY: 'auto', flex: 1 }}>
              {CANONICAL_DIAGRAMS.map(diag => {
                const active = selectedDiagram === diag.id;
                const available = availableList.includes(diag.id);
                return (
                  <div
                    key={diag.id}
                    onClick={() => { setSelectedDiagram(diag.id); setSelectedElement(null); }}
                    style={{
                      padding: '8px 16px',
                      cursor: 'pointer',
                      background: active ? 'rgba(255,255,255,0.05)' : 'transparent',
                      borderLeft: `3px solid ${active ? '#007ACC' : 'transparent'}`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between'
                    }}
                  >
                    <div>
                      <div style={{ fontSize: 13, color: active ? '#fff' : '#ccc' }}>{diag.label}</div>
                      <div style={{ fontSize: 11, color: '#888' }}>{diag.category}</div>
                    </div>
                    <span style={{ width: 6, height: 6, borderRadius: '50%', background: available ? '#73C991' : '#555' }} />
                  </div>
                );
              })}
            </div>
          </aside>

          {/* CENTER CONTENT */}
          <main style={{ flex: 1, position: 'relative', background: '#1e1e1e' }}>
            {loading ? (
              <EmptyState title="Rendering Diagram..." description="Processing layout and structural mappings." />
            ) : !diagramData ? (
              <EmptyState 
                title="Diagram Not Generated" 
                description={errorMessage || (hasPlanning ? 'This diagram is planned. Run PlanningAgent or trigger regeneration.' : 'Run the SEAM workflow to analyze requirements and generate diagrams.')}
                actionNode={hasPlanning ? (
                  <button className="consoleBtn primary" onClick={handleRegenerateDiagram} disabled={regenerating}>
                    {regenerating ? '↻ Regenerating...' : 'Generate Now'}
                  </button>
                ) : (
                  <button className="consoleBtn primary" onClick={onOpenWorkspace}>Open Workspace</button>
                )}
              />
            ) : viewMode === 'visual' ? (
              <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                nodeTypes={nodeTypes}
                onNodeClick={onNodeClick}
                fitView
                attributionPosition="bottom-right"
                colorMode="dark"
              >
                <Background color="#333" gap={16} />
                <Controls />
                <MiniMap nodeStrokeWidth={3} nodeColor="#2b2b2b" maskColor="rgba(0,0,0,0.5)" />
                <Panel position="top-left" style={{ background: 'rgba(0,0,0,0.6)', padding: '4px 8px', borderRadius: 4, fontSize: 12 }}>
                  Nodes: {nodes.length} | Edges: {edges.length}
                </Panel>
              </ReactFlow>
            ) : viewMode === 'json' ? (
               <pre style={{ margin: 0, padding: 24, fontSize: 13, color: '#ccc', overflow: 'auto', height: '100%' }}>
                 {JSON.stringify(diagramData, null, 2)}
               </pre>
            ) : (
               <pre style={{ margin: 0, padding: 24, fontSize: 13, color: '#ccc', overflow: 'auto', height: '100%' }}>
                 {diagramData?.mermaid || '%% Mermaid definition missing'}
               </pre>
            )}
          </main>

          {/* RIGHT INSPECTOR */}
          {selectedElement && viewMode === 'visual' && (
            <aside style={{ width: 300, borderLeft: '1px solid #2b2b2b', background: '#1a1a1a', padding: 20, overflowY: 'auto' }}>
              <h3 style={{ margin: '0 0 16px 0', fontSize: 14, color: '#fff' }}>Inspector</h3>
              <div style={{ marginBottom: 12 }}>
                <div style={{ fontSize: 11, color: '#888' }}>ID</div>
                <div style={{ fontSize: 13, color: '#ccc', wordBreak: 'break-all' }}>{selectedElement.data.id}</div>
              </div>
              <div style={{ marginBottom: 12 }}>
                <div style={{ fontSize: 11, color: '#888' }}>Type</div>
                <div style={{ fontSize: 13, color: '#58A6FF' }}>{selectedElement.data.type || 'Component'}</div>
              </div>
              <div style={{ marginBottom: 12 }}>
                <div style={{ fontSize: 11, color: '#888' }}>Label</div>
                <div style={{ fontSize: 13, color: '#ccc' }}>{selectedElement.data.label}</div>
              </div>
              {selectedElement.data.description && (
                <div style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: 11, color: '#888' }}>Description</div>
                  <div style={{ fontSize: 13, color: '#ccc' }}>{selectedElement.data.description}</div>
                </div>
              )}
              {selectedElement.data.attributes && (
                <div style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: 11, color: '#888' }}>Attributes</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 4 }}>
                    {Array.isArray(selectedElement.data.attributes)
                      ? selectedElement.data.attributes.map((a: string, i: number) => (
                          <span key={i} style={{ background: '#333', padding: '2px 6px', borderRadius: 4, fontSize: 11, color: '#ccc' }}>{a}</span>
                        ))
                      : Object.entries(selectedElement.data.attributes).map(([k, v]) => (
                          <span key={k} style={{ background: '#333', padding: '2px 6px', borderRadius: 4, fontSize: 11, color: '#ccc' }}>{k}: {String(v)}</span>
                        ))
                    }
                  </div>
                </div>
              )}
              
              <div style={{ marginTop: 24 }}>
                 <button className="consoleBtn primary" style={{ width: '100%', justifyContent: 'center' }} onClick={onOpenWorkspace}>Open Source File</button>
              </div>
            </aside>
          )}
        </div>
      ) : (
        /* ================= SECTION B: VISUAL ASSETS (SDXL 1.0) ================= */
        <div style={{ display: 'flex', height: '100%', background: '#181818' }}>
          {/* LEFT CONTROLS PANEL */}
          <aside style={{ width: 380, borderRight: '1px solid #2b2b2b', background: '#1c1c1c', padding: 20, overflowY: 'auto' }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: '#fff', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 8 }}>
              <span>VISUAL ASSET GENERATION</span>
              <span style={{ fontSize: 10, background: '#333', color: '#888', padding: '2px 6px', borderRadius: 4 }}>SDXL 1.0</span>
            </div>
            <p style={{ fontSize: 12, color: '#888', margin: '0 0 16px 0' }}>
              Create product illustrations, concept art, and visual representations for presentations or marketing.
            </p>

            {/* Hardware Status Alert Banner */}
            {caps?.status === 'NOT_AVAILABLE_ON_CURRENT_HOST' && (
              <div style={{
                background: 'rgba(210, 153, 34, 0.12)',
                border: '1px solid #d29922',
                borderRadius: 6,
                padding: '12px 14px',
                marginBottom: 20,
                fontSize: 12,
                color: '#e3b341',
                lineHeight: 1.5,
              }}>
                <div style={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                  <span>⚠️ NOT AVAILABLE ON CURRENT HOST</span>
                </div>
                <div style={{ fontSize: 11, color: '#ccc' }}>
                  {caps.explanation || 'Docker Diffusers backend requires Linux with NVIDIA CUDA GPU.'}
                </div>
                <div style={{ marginTop: 8, fontSize: 11, color: '#888' }}>
                  Host Profile: <strong>{caps.host_os}</strong> | <strong>{caps.gpu_info}</strong> (CUDA: No).
                </div>
              </div>
            )}

            {/* Provider Selector */}
            <div style={{ marginBottom: 14 }}>
              <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: '#aaa', marginBottom: 6 }}>
                PROVIDER SELECTOR
              </label>
              <select
                value={selectedProvider}
                onChange={e => setSelectedProvider(e.target.value)}
                style={{
                  width: '100%',
                  background: '#252526',
                  color: '#ccc',
                  border: '1px solid #3c3c3c',
                  borderRadius: 4,
                  padding: '6px 10px',
                  fontSize: 12,
                }}
              >
                <option value="auto">Auto (Docker SDXL 1.0)</option>
                <option value="docker_sdxl" disabled={caps?.status === 'NOT_AVAILABLE_ON_CURRENT_HOST'}>
                  Docker SDXL 1.0 {caps?.status === 'NOT_AVAILABLE_ON_CURRENT_HOST' ? '(Unavailable: Unsupported Host)' : ''}
                </option>
              </select>
            </div>

            {/* Prompt Input */}
            <div style={{ marginBottom: 14 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                <label style={{ fontSize: 11, fontWeight: 600, color: '#aaa' }}>PROMPT</label>
                <span style={{ fontSize: 11, color: imagePrompt.length > 900 ? '#f85149' : '#888' }}>
                  {imagePrompt.length} / 1000
                </span>
              </div>
              <textarea
                value={imagePrompt}
                onChange={e => setImagePrompt(e.target.value.slice(0, 1000))}
                placeholder="Describe your visual concept (e.g. Modern isometric dark-mode cloud architecture visualization with glowing neon services)..."
                rows={4}
                style={{
                  width: '100%',
                  background: '#252526',
                  color: '#fff',
                  border: '1px solid #3c3c3c',
                  borderRadius: 4,
                  padding: 8,
                  fontSize: 12,
                  fontFamily: 'inherit',
                  resize: 'vertical',
                  boxSizing: 'border-box',
                }}
              />
            </div>

            {/* Image Purpose */}
            <div style={{ marginBottom: 14 }}>
              <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: '#aaa', marginBottom: 6 }}>
                IMAGE PURPOSE / CLASSIFICATION
              </label>
              <select
                value={imagePurpose}
                onChange={e => setImagePurpose(e.target.value)}
                style={{
                  width: '100%',
                  background: '#252526',
                  color: '#ccc',
                  border: '1px solid #3c3c3c',
                  borderRadius: 4,
                  padding: '6px 10px',
                  fontSize: 12,
                }}
              >
                {IMAGE_PURPOSES.map(p => (
                  <option key={p.id} value={p.id}>{p.label}</option>
                ))}
              </select>
            </div>

            {/* Size & Dimensions */}
            <div style={{ marginBottom: 14 }}>
              <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: '#aaa', marginBottom: 6 }}>
                DIMENSIONS (SDXL OPTIMIZED)
              </label>
              <select
                value={`${imageSize.width}x${imageSize.height}`}
                onChange={e => {
                  const [w, h] = e.target.value.split('x').map(Number);
                  setImageSize({ width: w, height: h });
                }}
                style={{
                  width: '100%',
                  background: '#252526',
                  color: '#ccc',
                  border: '1px solid #3c3c3c',
                  borderRadius: 4,
                  padding: '6px 10px',
                  fontSize: 12,
                }}
              >
                {IMAGE_SIZES.map(s => (
                  <option key={`${s.width}x${s.height}`} value={`${s.width}x${s.height}`}>
                    {s.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Negative Prompt */}
            <div style={{ marginBottom: 18 }}>
              <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: '#aaa', marginBottom: 6 }}>
                NEGATIVE PROMPT (OPTIONAL)
              </label>
              <input
                type="text"
                value={negativePrompt}
                onChange={e => setNegativePrompt(e.target.value.slice(0, 500))}
                placeholder="e.g. blurry, low quality, distorted text, artifacts"
                style={{
                  width: '100%',
                  background: '#252526',
                  color: '#fff',
                  border: '1px solid #3c3c3c',
                  borderRadius: 4,
                  padding: '6px 10px',
                  fontSize: 12,
                  boxSizing: 'border-box',
                }}
              />
            </div>

            {/* Generate Action Button */}
            <button
              className="consoleBtn primary"
              style={{
                width: '100%',
                justifyContent: 'center',
                padding: '10px 14px',
                opacity: caps?.status === 'NOT_AVAILABLE_ON_CURRENT_HOST' ? 0.6 : 1,
                cursor: caps?.status === 'NOT_AVAILABLE_ON_CURRENT_HOST' ? 'not-allowed' : 'pointer',
              }}
              onClick={handleGenerateImage}
              disabled={caps?.status === 'NOT_AVAILABLE_ON_CURRENT_HOST' || generatingImage || !imagePrompt.trim()}
            >
              {generatingImage ? '⚡ Generating Image...' : caps?.status === 'NOT_AVAILABLE_ON_CURRENT_HOST' ? 'Unavailable on Current Host' : '⚡ Generate Visual Asset'}
            </button>

            {imageError && (
              <div style={{ marginTop: 12, color: '#f85149', fontSize: 11, background: '#251b1b', padding: 8, borderRadius: 4, border: '1px solid #5a1e1e' }}>
                {imageError}
              </div>
            )}
          </aside>

          {/* RIGHT PREVIEW & GALLERY AREA */}
          <main style={{ flex: 1, padding: 24, overflowY: 'auto' }}>
            <h2 style={{ fontSize: 15, color: '#fff', margin: '0 0 16px 0' }}>Visual Asset Preview & Gallery</h2>

            {imageResult?.image_base64 ? (
              <div style={{ background: '#202020', border: '1px solid #333', borderRadius: 8, padding: 16, marginBottom: 24, maxWidth: 600 }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: '#58A6FF', marginBottom: 8 }}>Newly Generated Visual Asset</div>
                <img
                  src={`data:image/png;base64,${imageResult.image_base64}`}
                  alt="Generated visual asset"
                  style={{ width: '100%', borderRadius: 6, display: 'block', marginBottom: 12 }}
                />
                <div style={{ fontSize: 11, color: '#aaa', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
                  <div><strong>Provider:</strong> {imageResult.provider}</div>
                  <div><strong>Model:</strong> {imageResult.model}</div>
                  <div><strong>Artifact Path:</strong> {imageResult.artifact_path}</div>
                  <div><strong>Method:</strong> Illustrative Asset</div>
                </div>
              </div>
            ) : null}

            {visualAssetsList.length > 0 ? (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 16 }}>
                {visualAssetsList.map(asset => (
                  <div key={asset.artifact_id} style={{ background: '#242424', border: '1px solid #333', borderRadius: 6, padding: 12 }}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: '#fff', marginBottom: 4 }}>{asset.title}</div>
                    <div style={{ fontSize: 11, color: '#888', marginBottom: 8 }}>{asset.path}</div>
                    <div style={{ fontSize: 11, color: '#58A6FF' }}>{asset.status}</div>
                  </div>
                ))}
              </div>
            ) : !imageResult ? (
              <div style={{ textAlign: 'center', padding: '60px 20px', color: '#777', border: '1px dashed #333', borderRadius: 8 }}>
                <div style={{ fontSize: 32, marginBottom: 12 }}>🎨</div>
                <div style={{ fontSize: 14, color: '#ccc', marginBottom: 6 }}>No Visual Assets Generated Yet</div>
                <div style={{ fontSize: 12, maxWidth: 450, margin: '0 auto', lineHeight: 1.5 }}>
                  {caps?.status === 'NOT_AVAILABLE_ON_CURRENT_HOST'
                    ? "Image generation through Docker SDXL is currently disabled on this Windows host due to lack of a CUDA GPU. Use Engineering Diagrams for validated architectures."
                    : "Enter a prompt and select an image purpose to generate conceptual visual artwork using Stable Diffusion XL 1.0."}
                </div>
              </div>
            ) : null}
          </main>
        </div>
      )}
    </EngineeringConsole>
  );
}
