import React, { useState, useEffect } from 'react';
import { seamApi, ProjectSummary, CreateProjectInput } from '../../api/client';
import './ProjectBuilder.css';

/* ───────────────────── Types & Constants ───────────────────── */

export type StackConfig = {
  language: string;
  frontend: string;
  backend: string;
  database: string;
  styling: string;
  auth: string;
  build_tool: string;
};

export type StackPreset = {
  id: string;
  name: string;
  description: string;
  tags: string[];
  config: StackConfig;
};

const STACK_PRESETS: StackPreset[] = [
  {
    id: 'modern_fullstack',
    name: 'Modern Full-Stack',
    description: 'React 18 + Vite SPA paired with high-performance FastAPI and SQLite WAL storage.',
    tags: ['React 18', 'Vite', 'FastAPI', 'SQLite', 'TailwindCSS'],
    config: {
      language: 'TypeScript',
      frontend: 'React',
      backend: 'FastAPI',
      database: 'SQLite',
      styling: 'TailwindCSS',
      auth: 'JWT',
      build_tool: 'Vite',
    },
  },
  {
    id: 'python_api',
    name: 'Python Cloud API',
    description: 'Pure microservice REST API with Pydantic validation, SQLite/PostgreSQL, and Pytest.',
    tags: ['Python', 'FastAPI', 'SQLite', 'Pydantic', 'Pytest'],
    config: {
      language: 'Python',
      frontend: 'None',
      backend: 'FastAPI',
      database: 'SQLite',
      styling: 'None',
      auth: 'JWT',
      build_tool: 'None',
    },
  },
  {
    id: 'ts_fullstack',
    name: 'TypeScript Full-Stack',
    description: 'Unified TypeScript end-to-end with React frontend, Express.js API, and SQLite.',
    tags: ['TypeScript', 'React', 'Express', 'SQLite', 'Vanilla CSS'],
    config: {
      language: 'TypeScript',
      frontend: 'React',
      backend: 'Express',
      database: 'SQLite',
      styling: 'Vanilla CSS',
      auth: 'Session Cookies',
      build_tool: 'Vite',
    },
  },
  {
    id: 'lightweight_web',
    name: 'Lightweight Web App',
    description: 'Minimal zero-build HTML5/CSS3 frontend served by a streamlined Python FastAPI backend.',
    tags: ['HTML5', 'Vanilla CSS', 'FastAPI', 'SQLite'],
    config: {
      language: 'JavaScript',
      frontend: 'Vanilla HTML/JS',
      backend: 'FastAPI',
      database: 'SQLite',
      styling: 'Vanilla CSS',
      auth: 'None',
      build_tool: 'None',
    },
  },
];

const EXAMPLE_PROMPTS = [
  {
    label: 'Student Association Hub',
    title: 'Student Association Platform',
    prompt:
      'Build a student association management platform with member registration, role-based access, event scheduling, attendance tracking, financial contributions, notifications, and analytics.',
    preset: 'modern_fullstack',
  },
  {
    label: 'E-Commerce Inventory API',
    title: 'Inventory REST API',
    prompt:
      'Create a resilient inventory management REST API with product catalog, stock replenishment thresholds, SKU tracking, category taxonomy, and supplier fulfillment integration.',
    preset: 'python_api',
  },
  {
    label: 'Financial Ledger (ACID)',
    title: 'Banking Ledger Service',
    prompt:
      'Build a double-entry financial ledger service with ACID transactional integrity, multi-currency accounts, transfer audits, idempotency keys, and reconciliation reporting.',
    preset: 'python_api',
  },
  {
    label: 'IoT Telemetry Streamer',
    title: 'IoT Sensor Monitor',
    prompt:
      'Develop an IoT device telemetry aggregator with time-series ingestion, anomalous sensor readings detection, threshold triggers, and real-time dashboard data feeds.',
    preset: 'ts_fullstack',
  },
];

const COGNITIVE_AGENTS = [
  { step: '01', name: 'Analysis Agent', desc: 'Requirements & Domain Modeling' },
  { step: '02', name: 'Planning Agent', desc: 'Architecture & 10 Canonical Diagrams' },
  { step: '03', name: 'Supervisor Agent', desc: 'Task Graph & Human Approval Gates' },
  { step: '04', name: 'Coding Agent', desc: 'Source Code & Sandboxed Tool Writes' },
  { step: '05', name: 'QA Agent', desc: 'Automated Tests & Defect Repair Loops' },
  { step: '06', name: 'Delivery Agent', desc: 'Packaging & Release Readiness' },
];

/* ───────────────────── Component Props ───────────────────── */

export type ProjectBuilderProps = {
  projects: ProjectSummary[];
  onSelectProject: (projectId: string) => void;
  onOpenWorkspace: () => void;
  onOpenDesignStudio?: () => void;
  onOpenTestLab?: () => void;
  onOpenDelivery?: () => void;
  onRefreshProjects?: () => Promise<void>;
  currentProjectId?: string | null;
  currentState?: any;
};

export function ProjectBuilder({
  projects,
  onSelectProject,
  onOpenWorkspace,
  onOpenDesignStudio,
  onOpenTestLab,
  onOpenDelivery,
  onRefreshProjects,
  currentProjectId,
  currentState,
}: ProjectBuilderProps) {
  // Workflow mode: new_project (Workflow A) vs enhance_existing (Workflow B)
  const [workflowMode, setWorkflowMode] = useState<'new_project' | 'enhance_existing'>('new_project');

  // Form inputs
  const [projectName, setProjectName] = useState('');
  const [promptText, setPromptText] = useState('');
  const [selectedPresetId, setSelectedPresetId] = useState<string>('modern_fullstack');
  const [customStackOpen, setCustomStackOpen] = useState(false);
  const [stackConfig, setStackConfig] = useState<StackConfig>(STACK_PRESETS[0].config);

  // Advanced options
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const [scale, setScale] = useState('AUTO');
  const [constraints, setConstraints] = useState('');

  // Workflow B (GitHub Enhancement)
  const [githubRepo, setGithubRepo] = useState('');
  const [githubBranch, setGithubBranch] = useState('main');
  const [githubStatus, setGithubStatus] = useState<any>(null);
  const [inspectingRepo, setInspectingRepo] = useState(false);

  // Generation status
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationProgress, setGenerationProgress] = useState(0);
  const [currentAgentIndex, setCurrentAgentIndex] = useState(0);
  const [generationError, setGenerationError] = useState<string | null>(null);
  const [completedProject, setCompletedProject] = useState<{
    id: string;
    name: string;
    stack: StackConfig;
    outputDir: string;
  } | null>(null);

  // Select Preset Handler
  const handleSelectPreset = (preset: StackPreset) => {
    setSelectedPresetId(preset.id);
    setStackConfig(preset.config);
  };

  // Example Prompt Picker
  const handleSelectExample = (item: typeof EXAMPLE_PROMPTS[0]) => {
    setPromptText(item.prompt);
    if (!projectName) {
      setProjectName(item.title.toLowerCase().replace(/[^a-z0-9]+/g, '-'));
    }
    const foundPreset = STACK_PRESETS.find(p => p.id === item.preset);
    if (foundPreset) {
      handleSelectPreset(foundPreset);
    }
  };

  // GitHub Repo Inspection Handler
  const handleInspectGithub = async () => {
    if (!githubRepo.trim()) return;
    setInspectingRepo(true);
    setGenerationError(null);
    try {
      const res = await seamApi.connectGithub(githubRepo.trim(), githubBranch.trim());
      setGithubStatus(res);
      if (res.name && !projectName) {
        setProjectName(res.name);
      }
    } catch (err: any) {
      setGithubStatus({ status: 'ERROR', detail: err.message });
    } finally {
      setInspectingRepo(false);
    }
  };

  // Generate Project Handler
  const handleGenerateProject = async () => {
    const prompt = promptText.trim();
    if (!prompt) return;

    const finalProjectName = projectName.trim() || prompt.slice(0, 24).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'seam-app';

    setIsGenerating(true);
    setGenerationError(null);
    setCompletedProject(null);
    setGenerationProgress(10);
    setCurrentAgentIndex(0);

    try {
      const techPreferences = [
        stackConfig.language,
        stackConfig.frontend !== 'None' ? stackConfig.frontend : null,
        stackConfig.backend !== 'None' ? stackConfig.backend : null,
        stackConfig.database !== 'None' ? stackConfig.database : null,
        stackConfig.styling !== 'None' ? stackConfig.styling : null,
      ].filter(Boolean) as string[];

      const input: CreateProjectInput = {
        project_name: finalProjectName,
        requirement: prompt,
        scale,
        technology_preferences: techPreferences,
        technology_stack: stackConfig as any,
        workflow_type: workflowMode,
        additional_constraints: constraints.trim() || undefined,
        ...(workflowMode === 'enhance_existing'
          ? { github_repository: githubRepo.trim(), github_branch: githubBranch.trim() }
          : {}),
      };

      // 1. Submit project creation to FastAPI backend
      const created = await seamApi.createProject(input);
      const projectId = created.project_id;
      onSelectProject(projectId);
      await onRefreshProjects?.();

      setGenerationProgress(25);
      setCurrentAgentIndex(1); // Planning

      // 2. Start the autonomous multi-agent workflow
      await seamApi.runProject(projectId);

      // Poll real backend project status and agent telemetry
      const pollInterval = window.setInterval(async () => {
        try {
          const status = await seamApi.projectStatus(projectId);

          // Map real cognitive agent to progress indicator
          const agentMap: Record<string, { index: number; progress: number }> = {
            AnalysisAgent: { index: 0, progress: 20 },
            PlanningAgent: { index: 1, progress: 40 },
            SupervisorAgent: { index: 2, progress: 55 },
            CodingAgent: { index: 3, progress: 75 },
            QAAgent: { index: 4, progress: 90 },
            DeliveryAgent: { index: 5, progress: 98 },
          };

          if (status.current_agent && agentMap[status.current_agent]) {
            setCurrentAgentIndex(agentMap[status.current_agent].index);
            setGenerationProgress(agentMap[status.current_agent].progress);
          }

          if (status.workflow_status === 'completed' || status.delivery_result) {
            window.clearInterval(pollInterval);
            setCurrentAgentIndex(5);
            setGenerationProgress(100);
            setIsGenerating(false);
            setCompletedProject({
              id: projectId,
              name: finalProjectName,
              stack: stackConfig,
              outputDir: `generated_projects/${finalProjectName.replace(/[^a-zA-Z0-9_-]/g, '_')}`,
            });
            await onRefreshProjects?.();
          } else if (status.workflow_status === 'failed') {
            window.clearInterval(pollInterval);
            setIsGenerating(false);
            setGenerationError(status.errors?.join('\n') || 'Workflow failed during agent execution.');
          }
        } catch {
          // Keep polling if transient network issue occurs
        }
      }, 1500);
    } catch (err: any) {
      setIsGenerating(false);
      setGenerationError(err.message || 'Project generation failed.');
    }
  };

  return (
    <div className="projectBuilderContainer" role="main" aria-label="Project Builder">
      {/* 1. Header Banner */}
      <header className="builderHero">
        <div className="builderBadge">
          <span>AI Architecture & Code Engine</span>
        </div>
        <h1>Build your next project</h1>
        <p>
          What do you want to build? Describe your application, choose a supported technology stack, and let SEAM’s six cognitive agents architect, code, test, and deliver your project.
        </p>

        {/* Workflow Switcher: Greenfield vs Brownfield */}
        <div className="workflowTabs" role="tablist">
          <button
            role="tab"
            aria-selected={workflowMode === 'new_project'}
            className={`workflowTab ${workflowMode === 'new_project' ? 'active' : ''}`}
            onClick={() => setWorkflowMode('new_project')}
          >
            <span>🚀</span> Create New Project (Greenfield)
          </button>
          <button
            role="tab"
            aria-selected={workflowMode === 'enhance_existing'}
            className={`workflowTab ${workflowMode === 'enhance_existing' ? 'active' : ''}`}
            onClick={() => setWorkflowMode('enhance_existing')}
          >
            <span>⎇</span> Enhance Existing Repo (GitHub)
          </button>
        </div>
      </header>

      {/* 2. Main Builder Grid */}
      <div className="builderGrid">
        <div className="builderMainColumn">
          {/* Workflow A: Create New Project */}
          {workflowMode === 'new_project' ? (
            <>
              {/* Step 1: Prompt Input Card */}
              <section className="builderCard" aria-labelledby="step1-heading">
                <div className="cardHeader">
                  <h2 id="step1-heading">
                    <span className="stepNumber">1</span> Describe Your Application
                  </h2>
                  <span style={{ fontSize: '12px', color: '#8b949e' }}>Required</span>
                </div>

                <div className="promptTextareaContainer">
                  <textarea
                    className="promptTextarea"
                    value={promptText}
                    onChange={e => setPromptText(e.target.value)}
                    placeholder="Describe the application you want to build. Explain its purpose, key features, users, and any important requirements..."
                    rows={5}
                    maxLength={4000}
                    aria-label="Application Description"
                  />
                  <div className="promptFooter">
                    <span>Be specific about features, data models, and business logic.</span>
                    <span className={`promptCharCount ${promptText.length > 3800 ? 'limit' : ''}`}>
                      {promptText.length} / 4000
                    </span>
                  </div>
                </div>

                {/* Example Prompts */}
                <div className="examplesSection">
                  <label>Or start from an example prompt:</label>
                  <div className="exampleChips">
                    {EXAMPLE_PROMPTS.map((item, idx) => (
                      <button
                        key={idx}
                        type="button"
                        className="exampleChip"
                        onClick={() => handleSelectExample(item)}
                        title={item.prompt}
                      >
                        <span>💡</span> {item.label}
                      </button>
                    ))}
                  </div>
                </div>
              </section>

              {/* Step 2: Tech Stack Selector Card */}
              <section className="builderCard" aria-labelledby="step2-heading">
                <div className="cardHeader">
                  <h2 id="step2-heading">
                    <span className="stepNumber">2</span> Choose Technology Stack
                  </h2>
                  <span style={{ fontSize: '12px', color: '#58a6ff' }}>Grounded in Real Generator</span>
                </div>

                {/* Curated Stack Presets */}
                <div className="presetsGrid">
                  {STACK_PRESETS.map(preset => {
                    const isSelected = selectedPresetId === preset.id;
                    return (
                      <button
                        key={preset.id}
                        type="button"
                        className={`presetCard ${isSelected ? 'selected' : ''}`}
                        onClick={() => handleSelectPreset(preset)}
                      >
                        <div className="presetTitle">
                          <span>{preset.name}</span>
                          {isSelected && <span className="presetCheck">✓</span>}
                        </div>
                        <p className="presetDesc">{preset.description}</p>
                        <div className="presetTags">
                          {preset.tags.map((t, i) => (
                            <span key={i} className="presetTag">{t}</span>
                          ))}
                        </div>
                      </button>
                    );
                  })}
                </div>

                {/* Custom Stack Details Toggle */}
                <button
                  type="button"
                  className="customStackToggle"
                  onClick={() => setCustomStackOpen(!customStackOpen)}
                >
                  {customStackOpen ? '▲ Hide Custom Stack Options' : '▼ Customize Stack Details (Language, Database, Styling)'}
                </button>

                {customStackOpen && (
                  <div className="customStackCategories">
                    <div className="stackCategoryGroup">
                      <label>Language</label>
                      <select
                        className="stackSelect"
                        value={stackConfig.language}
                        onChange={e => {
                          setSelectedPresetId('custom');
                          setStackConfig({ ...stackConfig, language: e.target.value });
                        }}
                      >
                        <option value="TypeScript">TypeScript</option>
                        <option value="Python">Python</option>
                        <option value="JavaScript">JavaScript</option>
                      </select>
                    </div>

                    <div className="stackCategoryGroup">
                      <label>Frontend Framework</label>
                      <select
                        className="stackSelect"
                        value={stackConfig.frontend}
                        onChange={e => {
                          setSelectedPresetId('custom');
                          setStackConfig({ ...stackConfig, frontend: e.target.value });
                        }}
                      >
                        <option value="React">React (Vite)</option>
                        <option value="Next.js">Next.js</option>
                        <option value="Vanilla HTML/JS">Vanilla HTML/JS</option>
                        <option value="None">None (API Only)</option>
                      </select>
                    </div>

                    <div className="stackCategoryGroup">
                      <label>Backend Framework</label>
                      <select
                        className="stackSelect"
                        value={stackConfig.backend}
                        onChange={e => {
                          setSelectedPresetId('custom');
                          setStackConfig({ ...stackConfig, backend: e.target.value });
                        }}
                      >
                        <option value="FastAPI">FastAPI (Python)</option>
                        <option value="Express">Express.js (Node)</option>
                        <option value="Flask">Flask (Python)</option>
                        <option value="None">None (Static UI)</option>
                      </select>
                    </div>

                    <div className="stackCategoryGroup">
                      <label>Database</label>
                      <select
                        className="stackSelect"
                        value={stackConfig.database}
                        onChange={e => {
                          setSelectedPresetId('custom');
                          setStackConfig({ ...stackConfig, database: e.target.value });
                        }}
                      >
                        <option value="SQLite">SQLite (Embedded WAL)</option>
                        <option value="PostgreSQL">PostgreSQL</option>
                        <option value="In-Memory">In-Memory Store</option>
                        <option value="None">None</option>
                      </select>
                    </div>

                    <div className="stackCategoryGroup">
                      <label>Styling System</label>
                      <select
                        className="stackSelect"
                        value={stackConfig.styling}
                        onChange={e => {
                          setSelectedPresetId('custom');
                          setStackConfig({ ...stackConfig, styling: e.target.value });
                        }}
                      >
                        <option value="TailwindCSS">TailwindCSS</option>
                        <option value="Vanilla CSS">Vanilla CSS</option>
                        <option value="None">None</option>
                      </select>
                    </div>

                    <div className="stackCategoryGroup">
                      <label>Authentication</label>
                      <select
                        className="stackSelect"
                        value={stackConfig.auth}
                        onChange={e => {
                          setSelectedPresetId('custom');
                          setStackConfig({ ...stackConfig, auth: e.target.value });
                        }}
                      >
                        <option value="JWT">JWT Bearer Tokens</option>
                        <option value="Session Cookies">Session Cookies</option>
                        <option value="None">None</option>
                      </select>
                    </div>
                  </div>
                )}

                {/* Selected Stack Summary Chips */}
                <div className="activeStackBar">
                  <div className="activeStackHeader">
                    <span>⚡ Configured Generation Stack:</span>
                  </div>
                  <div className="activeChipsList">
                    <span className="stackChip"><strong>Lang:</strong> {stackConfig.language}</span>
                    <span className="stackChip"><strong>Frontend:</strong> {stackConfig.frontend}</span>
                    <span className="stackChip"><strong>Backend:</strong> {stackConfig.backend}</span>
                    <span className="stackChip"><strong>DB:</strong> {stackConfig.database}</span>
                    {stackConfig.styling !== 'None' && <span className="stackChip"><strong>UI:</strong> {stackConfig.styling}</span>}
                    {stackConfig.auth !== 'None' && <span className="stackChip"><strong>Auth:</strong> {stackConfig.auth}</span>}
                  </div>
                </div>

                {/* Advanced Options Accordion */}
                <div className="advancedSection">
                  <button
                    type="button"
                    className="advancedToggle"
                    onClick={() => setAdvancedOpen(!advancedOpen)}
                  >
                    {advancedOpen ? '▲ Hide Advanced Configuration' : '▼ Advanced Configuration (Project Name, Scale, Constraints)'}
                  </button>

                  {advancedOpen && (
                    <div className="advancedFields">
                      <div className="fieldGroup">
                        <label>Project Name (Optional)</label>
                        <input
                          type="text"
                          className="fieldInput"
                          placeholder="e.g. inventory-service (auto-derived if empty)"
                          value={projectName}
                          onChange={e => setProjectName(e.target.value)}
                        />
                      </div>

                      <div className="fieldGroup">
                        <label>Estimated Project Scale</label>
                        <select
                          className="fieldInput"
                          value={scale}
                          onChange={e => setScale(e.target.value)}
                        >
                          <option value="AUTO">AUTO (Evaluated by Analysis Agent)</option>
                          <option value="SMALL">SMALL (Single Service / Prototype)</option>
                          <option value="MEDIUM">MEDIUM (Modular Service with DB)</option>
                          <option value="LARGE">LARGE (Distributed Architecture)</option>
                          <option value="ENTERPRISE">ENTERPRISE (High Compliance / ACID)</option>
                        </select>
                      </div>

                      <div className="fieldGroup" style={{ gridColumn: '1 / -1' }}>
                        <label>Additional Constraints / Non-Functional Requirements</label>
                        <input
                          type="text"
                          className="fieldInput"
                          placeholder="e.g. Include Dockerfile, zero external cloud dependencies, strict unit test coverage"
                          value={constraints}
                          onChange={e => setConstraints(e.target.value)}
                        />
                      </div>
                    </div>
                  )}
                </div>

                {/* Primary Action Button */}
                <div className="actionRow">
                  {generationError && (
                    <div className="validationAlert">
                      <span>⚠️ {generationError}</span>
                    </div>
                  )}
                  <button
                    type="button"
                    className="generateButton"
                    disabled={!promptText.trim() || promptText.trim().length < 10 || isGenerating}
                    onClick={handleGenerateProject}
                  >
                    {isGenerating ? (
                      <>
                        <span className="spinner">⏳</span> Generating Application...
                      </>
                    ) : (
                      <>
                        <span>🚀</span> Generate Project
                      </>
                    )}
                  </button>
                </div>
              </section>
            </>
          ) : (
            /* Workflow B: Enhance Existing GitHub Repository */
            <section className="builderCard" aria-labelledby="wf-b-heading">
              <div className="cardHeader">
                <h2 id="wf-b-heading">
                  <span className="stepNumber">⎇</span> Enhance Existing GitHub Repository
                </h2>
                <span style={{ fontSize: '12px', color: '#3fb950' }}>Brownfield Safe Mode</span>
              </div>

              {/* Approval Gate Notice */}
              <div className="githubBanner">
                <span>🛡️</span>
                <div>
                  <strong>SEAM Approval Gate Enforced:</strong> SEAM will clone and analyze the repository in an isolated workspace. No files will be modified or committed without your explicit approval of the Enhancement Plan.
                </div>
              </div>

              <div className="fieldGroup">
                <label>GitHub Repository URL or Slug</label>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <input
                    type="text"
                    className="fieldInput"
                    style={{ flex: 1 }}
                    placeholder="https://github.com/owner/repository or owner/repo"
                    value={githubRepo}
                    onChange={e => setGithubRepo(e.target.value)}
                  />
                  <input
                    type="text"
                    className="fieldInput"
                    style={{ width: '120px' }}
                    placeholder="Branch (main)"
                    value={githubBranch}
                    onChange={e => setGithubBranch(e.target.value)}
                  />
                  <button
                    type="button"
                    className="secondaryActionButton"
                    disabled={!githubRepo.trim() || inspectingRepo}
                    onClick={handleInspectGithub}
                  >
                    {inspectingRepo ? 'Checking...' : 'Inspect Repo'}
                  </button>
                </div>
              </div>

              {githubStatus && (
                <div className="repoInspectorResults">
                  {githubStatus.status === 'ERROR' ? (
                    <span style={{ color: '#f85149' }}>❌ {githubStatus.detail}</span>
                  ) : (
                    <>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <strong style={{ color: '#58a6ff' }}>📦 {githubStatus.owner}/{githubStatus.name}</strong>
                        <span className="statusPill completed">Connected</span>
                      </div>
                      <div className="repoMetaGrid">
                        <span><strong>Branch:</strong> {githubStatus.selected_branch || 'main'}</span>
                        <span><strong>Language:</strong> {githubStatus.language || 'Detected from repo'}</span>
                        <span><strong>Commit:</strong> {githubStatus.commit_sha ? githubStatus.commit_sha.slice(0, 7) : 'HEAD'}</span>
                      </div>
                    </>
                  )}
                </div>
              )}

              <div className="fieldGroup">
                <label>Enhancement Goal / Problem Statement</label>
                <textarea
                  className="promptTextarea"
                  rows={4}
                  placeholder="Describe the feature to implement, bug to fix, or architectural enhancement required..."
                  value={promptText}
                  onChange={e => setPromptText(e.target.value)}
                />
              </div>

              <div className="actionRow">
                <button
                  type="button"
                  className="generateButton"
                  style={{ background: '#1f6feb' }}
                  disabled={!githubRepo.trim() || !promptText.trim() || isGenerating}
                  onClick={handleGenerateProject}
                >
                  {isGenerating ? 'Analyzing Repository...' : '🔍 Analyze & Build Enhancement Plan'}
                </button>
              </div>
            </section>
          )}

          {/* 3. Live Generation Progress Display */}
          {isGenerating && (
            <section className="generationProgressCard" aria-live="polite">
              <div className="progressHeader">
                <div className="progressTitle">Autonomous Multi-Agent Pipeline Running</div>
                <span style={{ color: '#58a6ff', fontWeight: 600 }}>{generationProgress}% Complete</span>
              </div>

              <div className="progressBarTrack">
                <div className="progressBarFill" style={{ width: `${generationProgress}%` }} />
              </div>

              <div className="agentTimelineGrid">
                {COGNITIVE_AGENTS.map((agent, i) => {
                  const isCurrent = i === currentAgentIndex;
                  const isDone = i < currentAgentIndex;
                  return (
                    <div
                      key={agent.step}
                      className={`timelineAgentBox ${isCurrent ? 'active' : ''} ${isDone ? 'done' : ''}`}
                    >
                      <span>{isDone ? '✓' : agent.step}</span>
                      <strong>{agent.name.split(' ')[0]}</strong>
                    </div>
                  );
                })}
              </div>
            </section>
          )}

          {/* 4. Post-Generation Completion Workspace */}
          {completedProject && (
            <section className="completionWorkspace">
              <div className="completionBanner">
                <div className="completionSuccess">
                  <div className="successIcon">✓</div>
                  <div>
                    <h3 style={{ margin: 0, fontSize: '18px', color: '#f0f6fc' }}>
                      Application Generated Successfully!
                    </h3>
                    <p style={{ margin: '4px 0 0', color: '#8b949e', fontSize: '13px' }}>
                      Project <strong>{completedProject.name}</strong> created in <code>{completedProject.outputDir}</code>
                    </p>
                  </div>
                </div>

                <div className="completionActions">
                  <button
                    type="button"
                    className="primaryActionButton"
                    onClick={onOpenWorkspace}
                  >
                    <span>💻</span> Open in Code Editor
                  </button>
                  {onOpenDesignStudio && (
                    <button
                      type="button"
                      className="secondaryActionButton"
                      onClick={onOpenDesignStudio}
                    >
                      <span>📐</span> View 10 Diagrams
                    </button>
                  )}
                  {onOpenTestLab && (
                    <button
                      type="button"
                      className="secondaryActionButton"
                      onClick={onOpenTestLab}
                    >
                      <span>🧪</span> Run Test Lab
                    </button>
                  )}
                  {onOpenDelivery && (
                    <button
                      type="button"
                      className="secondaryActionButton"
                      onClick={onOpenDelivery}
                    >
                      <span>📦</span> Delivery Center
                    </button>
                  )}
                </div>
              </div>
            </section>
          )}
        </div>

        {/* Supporting Right Sidebar */}
        <aside className="builderSidebar">
          {/* Agent Chain Info */}
          <div className="sidebarCard">
            <h3><span>🤖</span> 6 Cognitive Agents</h3>
            <div className="agentChainList">
              {COGNITIVE_AGENTS.map((agent, idx) => (
                <div key={idx} className="agentChainItem">
                  <div className="agentStepDot">{agent.step}</div>
                  <div className="agentChainInfo">
                    <span className="agentChainName">{agent.name}</span>
                    <span className="agentChainDesc">{agent.desc}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Recent Projects */}
          <div className="sidebarCard">
            <h3><span>📁</span> Recent Projects</h3>
            {projects && projects.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {projects.slice(0, 5).map(p => (
                  <div
                    key={p.project_id}
                    className="recentProjectItem"
                    onClick={() => {
                      onSelectProject(p.project_id);
                      onOpenWorkspace();
                    }}
                  >
                    <span className="recentProjectName">{p.project_name || p.project_id.slice(0, 8)}</span>
                    <span className={`statusPill ${p.workflow_status || 'pending'}`}>
                      {p.workflow_status || 'pending'}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ margin: 0, fontSize: '12px', color: '#8b949e' }}>No previous projects yet.</p>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
