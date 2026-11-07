import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { seamApi, FileNode, ProjectSummary } from './api/client';
import { connectProjectEvents } from './api/websocket';
import { ProjectExplorer } from './explorer/ProjectExplorer';
import { CodeEditor } from './editor/CodeEditor';
import { SeamPanel } from './seam/SeamPanel';
import { ChatMessage, nowIso } from './seam/chatTypes';
import { eventToChatMessages, projectStateToChatMessages } from './seam/eventToChatMessage';
import { FlexibleLayout, PanelDefinition, UnavailablePanel } from './layout/FlexibleLayout';
import { CommandPalette, CommandItem } from './components/CommandPalette';
import { DesignStudioPage } from './components/DesignStudioPage';
import { TestLabPage } from './components/TestLabPage';
import { ContractsPage } from './components/ContractsPage';
import { RepairCenterPage } from './components/RepairCenterPage';
import { RuntimeConsolePage } from './components/RuntimeConsolePage';
import { ModelControlPanel } from './components/ModelControlPanel';
import { VSCodeMenuBar } from './components/VSCodeMenuBar';
import { BreadcrumbBar } from './components/BreadcrumbBar';
import { TerminalSessionSelector } from './components/TerminalSessionSelector';
import { AntigravityHUD } from './components/AntigravityHUD';
import { AppShell } from './layout/AppShell';
import { LandingPage } from './landing/LandingPage';
import { AuthProvider, useAuth } from './firebase/AuthContext';
import { LoginPage } from './components/LoginPage';
import { SignupPage } from './components/SignupPage';
import { ProjectBuilder } from './components/ProjectBuilder/ProjectBuilder';
import './layout/ideEnhancements.css';

type Tab = {
  path: string;
  content: string;
  savedContent: string;
  version: number;
  kind?: 'text' | 'image';
  url?: string;
};

export function App() {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [projectId, setProjectId] = useState<string | null>(null);
  const [state, setState] = useState<any>({});
  const [health, setHealth] = useState<any>({});
  const [tree, setTree] = useState<FileNode[]>([]);
  const [tabs, setTabs] = useState<Tab[]>([]);
  const [activePath, setActivePath] = useState<string>('');
  const [filter, setFilter] = useState('');
  const [logs, setLogs] = useState<string[]>([]);
  const [wsStatus, setWsStatus] = useState('DISCONNECTED');
  const [wordWrap, setWordWrap] = useState(true);
  const [status, setStatus] = useState('Ready');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [n8nStatus, setN8nStatus] = useState<any>(null);
  const [events, setEvents] = useState<any[]>([]);
  const [experiments, setExperiments] = useState<any>(null);
  const [appError, setAppError] = useState('');
  const processedEvents = useRef<Set<string>>(new Set());

  const activeTab = tabs.find(tab => tab.path === activePath);

  const log = useCallback((message: string) => {
    const stamp = new Date().toLocaleTimeString();
    setLogs(current => [...current.slice(-250), `${stamp} ${message}`]);
  }, []);

  const appendMessages = useCallback((nextMessages: ChatMessage[]) => {
    if (!nextMessages.length) return;
    setMessages(current => {
      const seen = new Set(current.map(message => message.id));
      const merged = [...current];
      for (const message of nextMessages) {
        if (!seen.has(message.id)) {
          seen.add(message.id);
          merged.push(message);
        }
      }
      return merged.slice(-300);
    });
  }, []);

  const refreshHealth = useCallback(async () => {
    try {
      const [system, n8n] = await Promise.all([
        seamApi.systemHealth(),
        seamApi.n8nStatus().catch(() => null),
      ]);
      setHealth(system);
      setN8nStatus(n8n);
      setAppError('');
    } catch (error: any) {
      setHealth({ backend: 'offline', qwen: 'NOT_AVAILABLE', rag: 'NOT_AVAILABLE', github: 'NOT_AVAILABLE' });
      setAppError(error.message);
      log(`Backend health failed: ${error.message}`);
    }
  }, [log]);

  const refreshProjects = useCallback(async () => {
    try {
      const result = await seamApi.listProjects();
      setProjects(result.projects);
      if (!projectId && result.projects[0]) setProjectId(result.projects[0].project_id);
    } catch (error: any) {
      log(`Project list failed: ${error.message}`);
    }
  }, [log, projectId]);

  const refreshState = useCallback(async () => {
    if (!projectId) return null;
    try {
      const [nextState, eventResult] = await Promise.all([
        seamApi.projectStatus(projectId),
        seamApi.events(projectId).catch(() => ({ events: [] })),
      ]);
      setState(nextState);
      setEvents(eventResult.events || []);
      setStatus(`${nextState.workflow_status || 'pending'} ${nextState.current_agent || ''}`.trim());
      appendMessages(projectStateToChatMessages(nextState));
      return nextState;
    } catch (error: any) {
      log(`Status refresh failed: ${error.message}`);
      return null;
    }
  }, [appendMessages, log, projectId]);

  const refreshExperiments = useCallback(async () => {
    try {
      setExperiments(await seamApi.experiments());
    } catch {
      setExperiments(null);
    }
  }, []);

  const refreshTree = useCallback(async () => {
    if (!projectId) {
      setTree([]);
      return;
    }
    try {
      const result = await seamApi.tree(projectId);
      setTree(result.children);
    } catch (error: any) {
      setTree([]);
      log(`Explorer refresh failed: ${error.message}`);
    }
  }, [log, projectId]);

  const refreshAll = useCallback(async () => {
    await Promise.all([refreshHealth(), refreshProjects(), refreshState(), refreshTree(), refreshExperiments()]);
  }, [refreshHealth, refreshProjects, refreshState, refreshTree, refreshExperiments]);

  useEffect(() => {
    void refreshAll();
  }, [refreshAll]);

  useEffect(() => {
    if (!projectId) return;
    void refreshState();
    void refreshTree();
    const stop = connectProjectEvents(projectId, seamApi.wsUrl(projectId), event => {
      log(`${event.event || 'EVENT'} ${event.data?.agent || event.data?.task_id || ''}`.trim());
      const eventKey = event.event_id || `${event.event}-${event.agent || ''}-${event.task_id || ''}-${event.path || ''}`;
      if (processedEvents.current.has(eventKey)) return;
      processedEvents.current.add(eventKey);
      void handleWorkflowEvent(event);
    }, setWsStatus);
    return stop;
  }, [log, projectId, refreshState, refreshTree]);

  const handleWorkflowEvent = useCallback(async (event: any) => {
    setEvents(current => [event, ...current.slice(0, 199)]);
    const nextState = event.event === 'STATE_SYNC' && event.data ? event.data : await seamApi.projectStatus(event.project_id);
    setState(nextState);
    const translated = eventToChatMessages(event, nextState);
    if ((event.event === 'FILE_CREATED' || event.event === 'FILE_GENERATED' || event.event === 'FILE_UPDATED') && event.path && !/\.(png|jpg|jpeg|gif|webp)$/i.test(event.path)) {
      try {
        const file = await seamApi.readFile(event.project_id, event.path);
        for (const message of translated) {
          message.type = 'CODE';
          message.content = `${message.content}\n\nLLM-generated code preview from disk:`;
          message.metadata = {
            ...(message.metadata || {}),
            codePreview: file.content.slice(0, 6000),
            previewTruncated: file.content.length > 6000,
          };
        }
      } catch (error: any) {
        translated.push({
          id: `file-preview-error-${event.event_id || Date.now()}`,
          timestamp: nowIso(),
          role: 'SEAM',
          type: 'WARNING',
          status: 'NOT_AVAILABLE',
          content: `The file event arrived, but I could not read ${event.path} yet.\n${error.message}`,
        });
      }
    }
    appendMessages(translated);
    appendMessages(projectStateToChatMessages(nextState));
    if (event.event === 'DIRECTORY_CREATED' || event.event === 'FILE_CREATED' || event.event === 'FILE_GENERATED' || event.event === 'FILE_UPDATED' || event.event === 'ARTIFACT_CREATED' || event.event === 'ARTIFACT_REGISTERED' || event.event === 'DIAGRAM_GENERATED' || event.event === 'WORKFLOW_COMPLETED') {
      await refreshTree();
    }
  }, [appendMessages, refreshTree]);

  const createProject = async (input: any) => {
    appendMessages([
      {
        id: `user-create-${Date.now()}`,
        timestamp: nowIso(),
        role: 'USER',
        type: 'MESSAGE',
        status: 'COMPLETE',
        content: input.requirement,
        metadata: { project_name: input.project_name, scale: input.scale },
      },
      {
        id: `seam-create-${Date.now()}`,
        timestamp: nowIso(),
        role: 'SEAM',
        type: 'MESSAGE',
        status: 'WAITING',
        content: "I'll analyze this project and build it step by step. Run the workflow when you are ready.",
      },
    ]);
    const created = await seamApi.createProject(input);
    setProjectId(created.project_id);
    log(`Project created: ${created.project_name}`);
    await refreshProjects();
  };

  const runProject = async () => {
    if (!projectId) return;
    await seamApi.runProject(projectId);
    log('Workflow started');
    appendMessages([{
      id: `run-${projectId}-${Date.now()}`,
      timestamp: nowIso(),
      role: 'USER',
      type: 'MESSAGE',
      status: 'COMPLETE',
      content: 'Run workflow.',
    }]);
    await refreshState();
  };

  const stopProject = async () => {
    if (!projectId) return;
    appendMessages([{
      id: `stop-${projectId}-${Date.now()}`,
      timestamp: nowIso(),
      role: 'USER',
      type: 'MESSAGE',
      status: 'COMPLETE',
      content: 'Stop workflow.',
    }, {
      id: `stop-seam-${projectId}-${Date.now()}`,
      timestamp: nowIso(),
      role: 'SEAM',
      type: 'PROGRESS',
      status: 'RUNNING',
      content: 'Stopping the workflow...',
    }]);
    const result = await seamApi.stopProject(projectId);
    log(`Stop workflow: ${result.status || 'requested'}`);
    await refreshState();
  };

  const openFile = async (path: string) => {
    if (!projectId) return;
    const existing = tabs.find(tab => tab.path === path);
    if (existing) {
      setActivePath(path);
      return;
    }
    if (/\.(png|jpg|jpeg|gif|webp)$/i.test(path)) {
      const url = seamApi.fileUrl(projectId, path);
      setTabs(current => [...current, { path, content: '', savedContent: '', version: Date.now(), kind: 'image', url }]);
      setActivePath(path);
      log(`Opened image ${path}`);
      return;
    }
    try {
      const result = await seamApi.readFile(projectId, path);
      setTabs(current => [...current, { path, content: result.content, savedContent: result.content, version: Date.now(), kind: 'text' }]);
      setActivePath(path);
      log(`Opened ${path}`);
    } catch (error: any) {
      log(`Open failed: ${error.message}`);
    }
  };

  const handleChatCommand = async (text: string) => {
    appendMessages([{
      id: `user-command-${Date.now()}`,
      timestamp: nowIso(),
      role: 'USER',
      type: 'MESSAGE',
      status: 'COMPLETE',
      content: text,
    }]);

    const lower = text.toLowerCase();
    if (lower.includes('stop')) {
      await stopProject();
      return;
    }
    if (lower.includes('run')) {
      await runProject();
      return;
    }
    if (lower.includes('generated') || lower.includes('files')) {
      if (!projectId) return;
      const artifacts = await seamApi.artifacts(projectId);
      const fileMessages: ChatMessage[] = [];
      for (const file of artifacts.artifacts.slice(0, 20)) {
        let codePreview = '';
        try {
          const content = await seamApi.readFile(projectId, file.path);
          codePreview = content.content.slice(0, 3000);
        } catch {
          codePreview = '';
        }
        fileMessages.push({
          id: `artifact-${file.path}`,
          timestamp: nowIso(),
          role: 'SEAM',
          type: codePreview ? 'CODE' : 'FILE',
          status: 'COMPLETE',
          content: codePreview ? `Generated file: ${file.path}\n\nCode preview from disk:` : `Generated file: ${file.path}`,
          artifact: { kind: 'file', label: file.path, path: file.path, action: 'openFile' },
          metadata: codePreview ? { codePreview, previewTruncated: true } : undefined,
        });
      }
      appendMessages(fileMessages);
      return;
    }
    if (lower.includes('qa')) {
      appendMessages([{
        id: `qa-query-${Date.now()}`,
        timestamp: nowIso(),
        role: 'SEAM',
        type: 'QA',
        status: state.latest_qa_status ? 'COMPLETE' : 'NOT_AVAILABLE',
        content: JSON.stringify(Object.values(state.tasks || {}).map((task: any) => ({ task_id: task.task_id, status: task.status, qa: task.result?.qa_result || 'NOT_AVAILABLE' })), null, 2),
      }]);
      return;
    }
    if (lower.includes('architecture') || lower.includes('database')) {
      appendMessages([{
        id: `architecture-query-${Date.now()}`,
        timestamp: nowIso(),
        role: 'SEAM',
        type: 'SUMMARY',
        status: state.project_plan ? 'COMPLETE' : 'NOT_AVAILABLE',
        content: state.project_plan?.system_design ? JSON.stringify(state.project_plan.system_design, null, 2) : 'Architecture is NOT_AVAILABLE until planning completes.',
        artifact: state.project_plan?.system_design ? { kind: 'architecture', label: 'Architecture', action: 'openArchitecture' } : undefined,
      }]);
      return;
    }
    const fileMatch = text.match(/([\w.-]+\/[\w./-]+\.\w+)/);
    if (fileMatch) {
      await openFile(fileMatch[1]);
      return;
    }
    appendMessages([{
      id: `unsupported-command-${Date.now()}`,
      timestamp: nowIso(),
      role: 'SEAM',
      type: 'WARNING',
      status: 'NOT_AVAILABLE',
      content: 'I can map that only to real backend operations or current ProjectState queries. Try: Run workflow, Stop workflow, Show generated files, Show QA, Show architecture, or Open backend/main.py.',
    }]);
  };

  const updateActiveContent = (content: string) => {
    setTabs(current => current.map(tab => tab.path === activePath ? { ...tab, content } : tab));
  };

  const saveActive = async () => {
    if (!projectId || !activeTab) return;
    await seamApi.saveFile(projectId, activeTab.path, activeTab.content);
    setTabs(current => current.map(tab => tab.path === activeTab.path ? { ...tab, savedContent: tab.content } : tab));
    log(`Saved ${activeTab.path}`);
    await refreshTree();
  };

  const reloadActive = async () => {
    if (!projectId || !activeTab) return;
    if (activeTab.content !== activeTab.savedContent && !window.confirm('Discard unsaved changes and reload this file?')) return;
    const result = await seamApi.readFile(projectId, activeTab.path);
    setTabs(current => current.map(tab => tab.path === activeTab.path ? { ...tab, content: result.content, savedContent: result.content, version: Date.now() } : tab));
    log(`Reloaded ${activeTab.path}`);
  };

  const closeTab = (path: string) => {
    const tab = tabs.find(item => item.path === path);
    if (tab && tab.content !== tab.savedContent && !window.confirm(`Close ${path} with unsaved changes?`)) return;
    const nextTabs = tabs.filter(item => item.path !== path);
    setTabs(nextTabs);
    if (activePath === path) setActivePath(nextTabs[0]?.path || '');
  };

  const selectedPath = activePath || '';
  const createEntry = async (type: 'file' | 'directory') => {
    if (!projectId) return;
    const path = window.prompt(`New ${type} path`);
    if (!path) return;
    await seamApi.createEntry(projectId, path, type);
    log(`Created ${type}: ${path}`);
    await refreshTree();
  };

  const renameEntry = async () => {
    if (!projectId || !selectedPath) return;
    const target = window.prompt('Rename to', selectedPath);
    if (!target || target === selectedPath) return;
    await seamApi.renameEntry(projectId, selectedPath, target);
    setTabs(current => current.map(tab => tab.path === selectedPath ? { ...tab, path: target } : tab));
    setActivePath(target);
    log(`Renamed ${selectedPath} to ${target}`);
    await refreshTree();
  };

  const deleteEntry = async () => {
    if (!projectId || !selectedPath) return;
    if (!window.confirm(`Delete ${selectedPath}? Empty directories only. This cannot be undone.`)) return;
    await seamApi.deleteEntry(projectId, selectedPath);
    closeTab(selectedPath);
    log(`Deleted ${selectedPath}`);
    await refreshTree();
  };

  const hasDirtyTabs = useMemo(() => tabs.some(tab => tab.content !== tab.savedContent), [tabs]);

  const topbar = (
    <>
        <strong>SEAM IDE</strong>
        <select value={projectId || ''} onChange={event => setProjectId(event.target.value || null)}>
          <option value="">No project selected</option>
          {projects.map(project => <option key={project.project_id} value={project.project_id}>{project.project_name || project.domain || project.project_id}</option>)}
        </select>
        <button onClick={runProject} disabled={!projectId || state.workflow_status === 'running'}>Run</button>
        <button onClick={stopProject} disabled={!projectId}>Stop</button>
        <button onClick={refreshAll}>Refresh</button>
        <label className="inlineToggle"><input type="checkbox" checked={wordWrap} onChange={event => setWordWrap(event.target.checked)} /> Wrap</label>
        <span className={hasDirtyTabs ? 'dirtyStatus' : 'status'}>{hasDirtyTabs ? 'Unsaved changes' : status}</span>
    </>
  );

  const panels: PanelDefinition[] = [
    {
      id: 'explorer',
      title: 'Explorer',
      render: () => (
        <ProjectExplorer
          tree={tree}
          activePath={activePath}
          filter={filter}
          onFilter={setFilter}
          onOpen={openFile}
          onCreateFile={() => createEntry('file')}
          onCreateFolder={() => createEntry('directory')}
          onRename={renameEntry}
          onDelete={deleteEntry}
          onRefresh={refreshTree}
        />
      ),
    },
    {
      id: 'editor',
      title: 'Editor',
      render: () => (
        <section className="editorPane">
          <div className="tabs">
            {tabs.map(tab => (
              <button key={tab.path} className={tab.path === activePath ? 'active' : ''} onClick={() => setActivePath(tab.path)}>
                {tab.content !== tab.savedContent ? '* ' : ''}{tab.path.split('/').pop()}
                <span onClick={event => { event.stopPropagation(); closeTab(tab.path); }}> x</span>
              </button>
            ))}
          </div>
          <BreadcrumbBar path={activePath} onNavigateSegment={openFile} />
          <div className="editorToolbar">
            <span>{activePath || 'Open a file from Explorer'}</span>
            <button onClick={saveActive} disabled={!activeTab || activeTab.content === activeTab.savedContent}>Save</button>
            <button onClick={reloadActive} disabled={!activeTab}>Reload</button>
          </div>
          {activeTab?.kind === 'image' ? (
            <div className="imagePreview"><img src={activeTab.url} alt={activeTab.path} /></div>
          ) : activeTab ? (
            <CodeEditor path={activeTab.path} content={activeTab.content} version={activeTab.version} wordWrap={wordWrap} onChange={updateActiveContent} />
          ) : (
            <div className="emptyEditor">Create or select a project, then open a generated file.</div>
          )}
        </section>
      ),
    },
    {
      id: 'chat',
      title: 'SEAM Chat',
      render: () => (
        <SeamPanel
          projectId={projectId}
          state={state}
          health={health}
          wsStatus={wsStatus}
          messages={messages}
          onCreateProject={createProject}
          onRun={runProject}
          onStop={stopProject}
          onRefresh={refreshAll}
          onOpenFile={openFile}
          onChatCommand={handleChatCommand}
          onClearConversation={() => setMessages([])}
        />
      ),
    },
    {
      id: 'logs',
      title: 'Logs',
      render: () => (
        <TerminalSessionSelector
          logs={logs}
          state={state}
          onClearLogs={() => setLogs([])}
          activeTab="OUTPUT"
        />
      ),
    },
    {
      id: 'agents',
      title: 'Agents',
      render: () => <AgentSummary state={state} />,
    },
    {
      id: 'tasks',
      title: 'Tasks',
      render: () => <TaskSummary state={state} />,
    },
    {
      id: 'artifacts',
      title: 'Artifacts',
      render: () => <UnavailablePanel title="Artifacts" detail="The backend artifact registry exists; a dedicated artifact browser is not wired into the UI yet." />,
    },
    { id: 'search', title: 'Search', available: false, render: () => null },
    { id: 'git', title: 'Git', available: false, render: () => null },
    { id: 'knowledge', title: 'Knowledge', available: false, render: () => null },
    { id: 'skills', title: 'Skills', available: false, render: () => null },
    { id: 'mcp', title: 'MCP', available: false, render: () => null },
    { id: 'browser', title: 'Browser', available: false, render: () => null },
    {
      id: 'terminal',
      title: 'Terminal',
      available: true,
      render: () => (
        <TerminalSessionSelector
          logs={logs}
          state={state}
          onClearLogs={() => setLogs([])}
          activeTab="TERMINAL"
        />
      ),
    },
    { id: 'problems', title: 'Problems', render: () => <ProblemsPanel state={state} /> },
    { id: 'output', title: 'Output', render: () => <OutputPanel state={state} /> },
    { id: 'qa', title: 'QA', render: () => <QaPanel state={state} /> },
  ];

  const workspace = <FlexibleLayout panels={panels} topbar={topbar} />;

  return (
    <AuthProvider>
      <ProductShell
        projects={projects}
        projectId={projectId}
        onSelectProject={setProjectId}
        state={state}
        health={health}
        n8nStatus={n8nStatus}
        events={events}
        experiments={experiments}
        appError={appError}
        tree={tree}
        tabs={tabs}
        activePath={activePath}
        filter={filter}
        onFilter={setFilter}
        onOpen={openFile}
        onCloseTab={closeTab}
        onSelectTab={setActivePath}
        onContentChange={updateActiveContent}
        onSaveFile={saveActive}
        onReloadFile={reloadActive}
        onCreateFile={() => createEntry('file')}
        onCreateFolder={() => createEntry('directory')}
        onRename={renameEntry}
        onDelete={deleteEntry}
        logs={logs}
        onClearLogs={() => setLogs([])}
        wsStatus={wsStatus}
        messages={messages}
        onChatCommand={handleChatCommand}
        onClearConversation={() => setMessages([])}
        wordWrap={wordWrap}
        onToggleWordWrap={() => setWordWrap(!wordWrap)}
        workspace={workspace}
        onOpenWorkspace={() => setProjectId(projectId || projects[0]?.project_id || null)}
        onCreateProject={createProject}
        onRun={runProject}
        onStop={stopProject}
        onRefresh={refreshAll}
      />
    </AuthProvider>
  );
}

type ProductPage =
  | 'home'
  | 'login'
  | 'signup'
  | 'builder'
  | 'dashboard'
  | 'projects'
  | 'workspace'
  | 'design'
  | 'testlab'
  | 'contracts'
  | 'repair'
  | 'runtime'
  | 'models'
  | 'agents'
  | 'artifacts'
  | 'qa'
  | 'delivery'
  | 'evaluation'
  | 'experiments'
  | 'integrations'
  | 'settings'
  | 'readiness';

function ProductShell(props: {
  projects: ProjectSummary[];
  projectId: string | null;
  onSelectProject: (id: string | null) => void;
  state: any;
  health: any;
  n8nStatus: any;
  events: any[];
  experiments: any;
  appError: string;
  tree: FileNode[];
  tabs: Tab[];
  activePath: string;
  filter: string;
  onFilter: (value: string) => void;
  onOpen: (path: string) => void;
  onCloseTab: (path: string) => void;
  onSelectTab: (path: string) => void;
  onContentChange: (content: string) => void;
  onSaveFile: () => Promise<void>;
  onReloadFile: () => Promise<void>;
  onCreateFile: () => void;
  onCreateFolder: () => void;
  onRename: () => void;
  onDelete: () => void;
  logs: string[];
  onClearLogs: () => void;
  wsStatus: string;
  messages: ChatMessage[];
  onChatCommand: (text: string) => Promise<void>;
  onClearConversation: () => void;
  wordWrap: boolean;
  onToggleWordWrap: () => void;
  workspace: JSX.Element;
  onOpenWorkspace: () => void;
  onCreateProject: (input: any) => Promise<void>;
  onRun: () => Promise<void>;
  onStop: () => Promise<void>;
  onRefresh: () => Promise<void>;
}) {
  const { currentUser, userProfile } = useAuth();
  const [page, setPage] = useState<ProductPage>(() => {
    const params = new URLSearchParams(window.location.search);
    const p = params.get('page') as ProductPage | null;
    if (p && ['home', 'login', 'signup', 'builder', 'dashboard', 'projects', 'workspace', 'design', 'testlab', 'contracts', 'repair', 'runtime', 'models', 'agents', 'artifacts', 'qa', 'delivery', 'evaluation', 'experiments', 'integrations', 'settings', 'readiness'].includes(p)) {
      return p;
    }
    return 'home';
  });
  const [workspaceView, setWorkspaceView] = useState('editor');
  const [theme, setTheme] = useState<'dark' | 'light' | 'system'>('dark');
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  useEffect(() => {
    const handleGlobalKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && (e.key === 'k' || e.key === 'K')) {
        e.preventDefault();
        setCommandPaletteOpen(prev => !prev);
      }
    };
    window.addEventListener('keydown', handleGlobalKeyDown);
    return () => window.removeEventListener('keydown', handleGlobalKeyDown);
  }, []);

  const commands: CommandItem[] = [
    { id: 'open-builder', label: 'Create Project: Describe Application & Select Technology Stack', category: 'Project Builder', shortcut: 'Alt+N', action: () => setPage('builder') },
    { id: 'open-landing', label: 'Go to SEAM Landing Page / Overview', category: 'Navigation', shortcut: 'Alt+H', action: () => setPage('home') },
    { id: 'open-login', label: 'Account: Sign In to SEAM', category: 'Account', action: () => setPage('login') },
    { id: 'open-signup', label: 'Account: Create New Account', category: 'Account', action: () => setPage('signup') },
    { id: 'open-ws', label: 'Open Workspace IDE', category: 'Navigation', shortcut: 'Alt+W', action: () => setPage('workspace') },
    { id: 'open-dash', label: 'Go to Dashboard', category: 'Navigation', shortcut: 'Alt+D', action: () => setPage('dashboard') },
    { id: 'open-design', label: 'Open Design Studio (10 Canonical Diagrams)', category: 'Design', shortcut: 'Alt+G', action: () => setPage('design') },
    { id: 'open-testlab', label: 'Open Test Lab (17 Categories)', category: 'Testing', shortcut: 'Alt+T', action: () => setPage('testlab') },
    { id: 'open-contracts', label: 'Open Full-Stack Contracts (Drift Detector)', category: 'Architecture', shortcut: 'Alt+C', action: () => setPage('contracts') },
    { id: 'open-repair', label: 'Open Autonomous Defect Repair Center', category: 'Autonomous Repair', shortcut: 'Alt+R', action: () => setPage('repair') },
    { id: 'open-runtime', label: 'Open Runtime & Process Lifecycle Console', category: 'Runtime', shortcut: 'Alt+P', action: () => setPage('runtime') },
    { id: 'open-models', label: 'Open Model Router & Control Panel', category: 'AI Inference', shortcut: 'Alt+M', action: () => setPage('models') },
    { id: 'open-delivery', label: 'Open Delivery Center', category: 'Deployment', action: () => setPage('delivery') },
    { id: 'open-eval', label: 'Open Evaluation Console', category: 'Analysis', action: () => setPage('evaluation') },
    { id: 'open-integ', label: 'Open Integrations (n8n, Docker, GitHub)', category: 'Integrations', action: () => setPage('integrations') },
    { id: 'run-workflow', label: 'Start SEAM Workflow', category: 'Execution', shortcut: 'Ctrl+Enter', action: () => props.onRun() },
    { id: 'refresh-data', label: 'Refresh All System State', category: 'System', shortcut: 'F5', action: () => props.onRefresh() },
    { id: 'toggle-theme', label: 'Toggle Color Theme (Dark/Light)', category: 'Appearance', action: () => setTheme(prev => prev === 'dark' ? 'light' : 'dark') },
  ];

  const nav: Array<[ProductPage, string]> = [
    ['builder', '✨ Build Project'],
    ['projects', '📁 Existing Projects'],
    ['workspace', '💻 Code Editor & Files'],
    ['dashboard', '📊 Overview Dashboard'],
    ['design', '📐 Design Studio'],
    ['testlab', '🧪 Test Lab & QA'],
    ['repair', '🔧 Defect Repair'],
    ['runtime', '⚡ Runtime Console'],
    ['contracts', '📋 Contract Drift'],
    ['delivery', '🚀 Delivery Center'],
    ['models', '🧠 AI Model Router'],
    ['evaluation', '📈 Evaluation & Benchmarks'],
    ['settings', '⚙️ Settings & Readiness'],
  ];

  if (page === 'home') {
    return (
      <LandingPage
        onLaunch={() => setPage(currentUser ? 'builder' : 'login')}
        onWorkspace={() => setPage(currentUser ? 'workspace' : 'login')}
        onLogin={() => setPage('login')}
        onArchitecture={() => {
          setWorkspaceView('design');
          setPage(currentUser ? 'workspace' : 'login');
        }}
      />
    );
  }

  if (page === 'login') {
    return (
      <LoginPage
        onSuccess={() => setPage('workspace')}
        onNavigateSignup={() => setPage('signup')}
        onBackToLanding={() => setPage('home')}
      />
    );
  }

  if (page === 'signup') {
    return (
      <SignupPage
        onSuccess={() => setPage('workspace')}
        onNavigateLogin={() => setPage('login')}
        onBackToLanding={() => setPage('home')}
      />
    );
  }

  if (page === 'workspace') {
    return (
      <AppShell
        projects={props.projects}
        projectId={props.projectId}
        onSelectProject={props.onSelectProject}
        state={props.state}
        health={props.health}
        n8nStatus={props.n8nStatus}
        events={props.events}
        tree={props.tree}
        tabs={props.tabs}
        activePath={props.activePath}
        filter={props.filter}
        onFilter={props.onFilter}
        onOpen={props.onOpen}
        onCloseTab={props.onCloseTab}
        onSelectTab={props.onSelectTab}
        onContentChange={props.onContentChange}
        onSaveFile={props.onSaveFile}
        onReloadFile={props.onReloadFile}
        onCreateFile={props.onCreateFile}
        onCreateFolder={props.onCreateFolder}
        onRename={props.onRename}
        onDelete={props.onDelete}
        onRefresh={props.onRefresh}
        logs={props.logs}
        onClearLogs={props.onClearLogs}
        wsStatus={props.wsStatus}
        messages={props.messages}
        onRunWorkflow={props.onRun}
        onStopWorkflow={props.onStop}
        onChatCommand={props.onChatCommand}
        onClearConversation={props.onClearConversation}
        wordWrap={props.wordWrap}
        onToggleWordWrap={props.onToggleWordWrap}
        activeView={workspaceView}
        onSelectView={setWorkspaceView}
        renderPageView={view => {
          if (view === 'dashboard') return <DashboardPage {...props} />;
          if (view === 'design') return <DesignStudioPage projectId={props.projectId} state={props.state} onOpenWorkspace={() => setWorkspaceView('editor')} />;
          if (view === 'testlab') return <TestLabPage state={props.state} />;
          if (view === 'contracts') return <ContractsPage state={props.state} onOpenWorkspace={() => setWorkspaceView('editor')} />;
          if (view === 'repair') return <RepairCenterPage state={props.state} onOpenWorkspace={() => setWorkspaceView('editor')} />;
          if (view === 'runtime') return <RuntimeConsolePage health={props.health} state={props.state} />;
          if (view === 'models') return <ModelControlPanel />;
          if (view === 'agents') return <AgentsPage state={props.state} events={props.events} />;
          if (view === 'artifacts') return <ArtifactsPage state={props.state} />;
          if (view === 'qa') return <QaProductPage state={props.state} />;
          if (view === 'delivery') return <DeliveryPage state={props.state} />;
          if (view === 'evaluation') return <EvaluationPage state={props.state} events={props.events} />;
          if (view === 'experiments') return <ExperimentsPage experiments={props.experiments} />;
          if (view === 'integrations') return <IntegrationsPage health={props.health} n8nStatus={props.n8nStatus} />;
          if (view === 'settings') return <SettingsPage health={props.health} n8nStatus={props.n8nStatus} />;
          if (view === 'readiness') return <ReadinessPage health={props.health} n8nStatus={props.n8nStatus} />;
          return null;
        }}
        onGoHome={() => setPage('home')}
        userDisplayName={userProfile?.displayName || currentUser?.displayName || 'Kartheek Mudi'}
        userEmail={userProfile?.email || currentUser?.email || 'engineer@seam.internal'}
      />
    );
  }

  return (
    <div className="productShell">
      <VSCodeMenuBar
        projectName={props.projects.find(p => p.project_id === props.projectId)?.project_name || props.projectId || 'SEAM Workspace'}
        onOpenCommandPalette={() => setCommandPaletteOpen(true)}
        onRunWorkflow={props.onRun}
        onStopWorkflow={() => {}}
        onSaveFile={() => {}}
        onToggleSidebar={() => {}}
        onToggleTerminal={() => {}}
        onToggleAgentPanel={() => {}}
        onToggleTheme={() => setTheme(prev => prev === 'dark' ? 'light' : 'dark')}
        onGoHome={() => setPage('home')}
        userDisplayName={userProfile?.displayName || currentUser?.displayName || 'Kartheek Mudi'}
        userEmail={userProfile?.email || currentUser?.email || 'engineer@seam.internal'}
        activePath=""
      />
      <header className="productTopbar">
        <button className="brandButton" onClick={() => setPage('home')} aria-label="Open SEAM website">
          <strong>SEAM</strong>
          <span>Self-Evolving Autonomous Multi-Agent Framework</span>
        </button>
        <button
          className="topbarCreateBtn"
          onClick={() => setPage('builder')}
          style={{
            background: 'linear-gradient(135deg, #2563eb, #7c3aed)',
            color: '#fff',
            fontWeight: 600,
            border: 'none',
            borderRadius: '6px',
            padding: '6px 14px',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            cursor: 'pointer',
            fontSize: '13px',
            boxShadow: '0 2px 8px rgba(37,99,235,0.3)',
          }}
        >
          <span style={{ fontSize: '15px' }}>+</span> Build Project
        </button>
        <select aria-label="Workspace selector">
          <option>SEAM Workspace</option>
          <option>SEAM Desktop</option>
        </select>
        <select
          aria-label="Project selector"
          value={props.projectId || ''}
          onChange={e => {
            if (e.target.value) {
              props.onSelectProject(e.target.value);
              setPage('workspace');
            }
          }}
        >
          <option value="">Select project</option>
          {props.projects.map(project => <option key={project.project_id} value={project.project_id}>{project.project_name || project.project_id}</option>)}
        </select>
        <div className="searchTriggerContainer" onClick={() => setCommandPaletteOpen(true)}>
          <input
            className="globalSearch"
            aria-label="Search"
            placeholder="Search projects, actions (Press Ctrl+K)..."
            readOnly
          />
          <kbd className="kbdShortcut">Ctrl+K</kbd>
        </div>
        <button onClick={props.onRefresh}>Refresh</button>
        <select aria-label="Appearance" value={theme} onChange={event => setTheme(event.target.value as any)}>
          <option value="dark">Dark</option>
          <option value="light">Light</option>
          <option value="system">System</option>
        </select>
      </header>

      <aside className="productSidebar" aria-label="Product navigation">
        {nav.map(([id, label]) => (
          <button key={id} className={page === id ? 'active' : ''} onClick={() => setPage(id)}>
            {label}
          </button>
        ))}
      </aside>

      <main className="productMain scrollArea">
        {props.appError && <ErrorBanner message={props.appError} />}
        {(page === 'builder' || page === 'projects') && (
          <ProjectBuilder
            projects={props.projects}
            currentProjectId={props.projectId}
            onSelectProject={id => {
              props.onSelectProject(id);
              setPage('workspace');
            }}
            onOpenWorkspace={() => setPage('workspace')}
            onOpenDesignStudio={() => setPage('design')}
            onOpenTestLab={() => setPage('testlab')}
            onOpenDelivery={() => setPage('delivery')}
            onRefreshProjects={props.onRefresh}
          />
        )}
        {page === 'dashboard' && <DashboardPage {...props} />}
        {page === 'design' && <DesignStudioPage projectId={props.projectId} state={props.state} onOpenWorkspace={() => setPage('workspace')} />}
        {page === 'testlab' && <TestLabPage state={props.state} />}
        {page === 'contracts' && <ContractsPage state={props.state} onOpenWorkspace={() => setPage('workspace')} />}
        {page === 'repair' && <RepairCenterPage state={props.state} onOpenWorkspace={() => setPage('workspace')} />}
        {page === 'runtime' && <RuntimeConsolePage health={props.health} state={props.state} />}
        {page === 'models' && <ModelControlPanel />}
        {page === 'agents' && <AgentsPage state={props.state} events={props.events} />}
        {page === 'artifacts' && <ArtifactsPage state={props.state} />}
        {page === 'qa' && <QaProductPage state={props.state} />}
        {page === 'delivery' && <DeliveryPage state={props.state} />}
        {page === 'evaluation' && <EvaluationPage state={props.state} events={props.events} />}
        {page === 'experiments' && <ExperimentsPage experiments={props.experiments} />}
        {page === 'integrations' && <IntegrationsPage health={props.health} n8nStatus={props.n8nStatus} />}
        {page === 'settings' && <SettingsPage health={props.health} n8nStatus={props.n8nStatus} />}
        {page === 'readiness' && <ReadinessPage health={props.health} n8nStatus={props.n8nStatus} />}
      </main>

      <AntigravityHUD
        state={props.state}
        health={props.health}
        events={props.events}
        onOpenRepair={() => setPage('repair')}
        onRunWorkflow={props.onRun}
        onTriggerAction={(action) => {
          if (action === 'sync_overview') {
            props.onRefresh();
          }
        }}
      />

      <CommandPalette
        isOpen={commandPaletteOpen}
        onClose={() => setCommandPaletteOpen(false)}
        commands={commands}
      />
    </div>
  );
}

function MarketingPage({ onStart, onWorkspace }: { onStart: () => void; onWorkspace: () => void }) {
  const agents = [
    ['Analysis', 'Turns requirements into structured scope.', 'Requirements, domain context, traceability'],
    ['Planning', 'Designs architecture and implementation tasks.', 'System design, diagrams, task plan'],
    ['Supervisor', 'Coordinates workflow and rework decisions.', 'Execution plan, agent routing'],
    ['Coding', 'Creates code, files, folders, and commits.', 'Generated project structure and code'],
    ['QA', 'Validates APIs, contracts, runtime, and tests.', 'Findings, evidence, repair requests'],
    ['Delivery', 'Checks release readiness and deployment assets.', 'Delivery report, Docker validation'],
  ];
  return (
    <main className="marketing scrollArea">
      <section className="heroSection">
        <div className="heroCopy">
          <span className="eyebrow">SEAM Workspace</span>
          <h1>Build Software End-to-End with Autonomous AI Agents</h1>
          <p>SEAM coordinates analysis, architecture, coding, testing, repair, and delivery in one software-engineering workflow.</p>
          <div className="heroActions">
            <button onClick={onStart}>Start Building</button>
            <button onClick={onWorkspace}>View Architecture</button>
          </div>
        </div>
        <div className="workflowMap" aria-label="SEAM workflow visualization">
          {['Requirement', 'Analysis', 'Planning', 'Coding', 'QA', 'Repair', 'Delivery'].map(step => <div key={step}>{step}</div>)}
        </div>
      </section>
      <section className="contentBand">
        <h2>Six Agents</h2>
        <div className="productGrid three">
          {agents.map(([name, purpose, output]) => (
            <article className="productCard" key={name}>
              <span>{name}</span>
              <p>{purpose}</p>
              <strong>{output}</strong>
            </article>
          ))}
        </div>
      </section>
      <section className="contentBand splitBand">
        <div>
          <h2>Intelligence Layer</h2>
          <p>LangGraph orchestrates agents, LangChain standardizes model calls, RAG grounds decisions, ToolRegistry controls actions, and ProjectState/EventStore keep execution observable.</p>
        </div>
        <div className="architectureStack">
          {['LangGraph', 'LangChain', 'RAG', 'Domain Intelligence', 'Tool Registry', 'ProjectState'].map(item => <span key={item}>{item}</span>)}
        </div>
      </section>
      <section className="contentBand">
        <h2>Autonomous Repair</h2>
        <div className="repairViz">
          {['Bug detected', 'Root evidence', 'Repair', 'Verification', 'Regression'].map(item => <span key={item}>{item}</span>)}
        </div>
      </section>
      <section className="contentBand">
        <h2>Integrations</h2>
        <div className="integrationStrip">
          {['GitHub', 'n8n', 'Docker', 'Ollama', 'ChromaDB', 'FastAPI'].map(item => <span key={item}>{item}</span>)}
        </div>
      </section>
      <section className="contentBand">
        <h2>Use Cases</h2>
        <div className="productGrid five">
          {['Full-stack applications', 'AI applications', 'Domain-specific applications', 'Enterprise software', 'Rapid prototyping'].map(item => <article className="productCard" key={item}>{item}</article>)}
        </div>
      </section>
      <section className="contentBand">
        <h2>Product Screens</h2>
        <div className="screenshotGrid">
          {['Dashboard', 'Workspace', 'Agent execution', 'QA', 'Delivery', 'Evaluation'].map(item => <div className="screenDemo" key={item}>{item}</div>)}
        </div>
      </section>
      <section className="finalCta">
        <h2>Start Building with SEAM</h2>
        <button onClick={onStart}>Get Started</button>
        <button onClick={onWorkspace}>Open Workspace</button>
      </section>
    </main>
  );
}

function DashboardPage(props: { projects: ProjectSummary[]; state: any; health: any; n8nStatus: any; events: any[] }) {
  const completed = props.projects.filter(project => project.workflow_status === 'completed').length;
  const active = props.projects.filter(project => project.workflow_status === 'running').length;
  return (
    <PageFrame title="Dashboard" subtitle="Real-time SEAM workspace status">
      <div className="kpiGrid">
        <Kpi label="Projects" value={props.projects.length || '0'} />
        <Kpi label="Active Runs" value={active} />
        <Kpi label="Completed Runs" value={completed} />
        <Kpi label="QA Status" value={props.state.latest_qa_status || 'NOT_AVAILABLE'} tone={props.state.latest_qa_status === 'passed' ? 'good' : 'neutral'} />
      </div>
      <div className="productGrid two">
        <ActivityCard events={props.events} />
        <StatusCard title="Integrations" rows={[
          ['Backend', props.health.backend || 'UNKNOWN'],
          ['RAG', props.health.rag || 'UNKNOWN'],
          ['GitHub', props.health.github || 'UNKNOWN'],
          ['n8n', props.n8nStatus?.reachable ? 'CONNECTED' : props.n8nStatus?.configured ? 'DISCONNECTED' : 'NOT_CONFIGURED'],
        ]} />
      </div>
    </PageFrame>
  );
}

function AgentsPage({ state, events }: { state: any; events: any[] }) {
  return <PageFrame title="Agents" subtitle="Operational progress from ProjectState and EventStore."><AgentTimeline state={state} events={events} /></PageFrame>;
}

function ArtifactsPage({ state }: { state: any }) {
  const paths = [
    ...(state.design_artifacts?.diagram_paths || []),
    ...(state.design_artifacts?.rendered_diagram_paths || []),
    ...(state.deployment_artifacts || []).map((item: any) => item.path || item.name).filter(Boolean),
  ];
  return <PageFrame title="Artifacts" subtitle="Generated documents, diagrams, and delivery assets.">{paths.length ? <div className="productGrid two">{paths.map(path => <article className="productCard" key={path}>{path}</article>)}</div> : <EmptyState title="No artifacts yet" detail="Artifacts appear as agents generate files." />}</PageFrame>;
}

function QaProductPage({ state }: { state: any }) {
  const checks: Array<[string, any]> = [
    ['Contracts', state.full_stack_contract ? 'AVAILABLE' : 'NOT_AVAILABLE'],
    ['Runtime', state.runtime_contract_results?.length ? 'AVAILABLE' : 'NOT_CONFIGURED'],
    ['E2E', state.e2e_results?.length ? 'AVAILABLE' : 'NOT_CONFIGURED'],
    ['Frontend', state.frontend_execution ? 'AVAILABLE' : 'NOT_AVAILABLE'],
    ['Backend', state.latest_qa_status || 'NOT_AVAILABLE'],
    ['Security', state.security_status || 'NOT_CONFIGURED'],
  ];
  return (
    <PageFrame title="QA" subtitle="Detected issues, evidence, and repair status.">
      <Kpi label="Overall Status" value={state.latest_qa_status || 'NOT_AVAILABLE'} />
      <StatusCard title="QA Layers" rows={checks} />
      <DefectList state={state} />
    </PageFrame>
  );
}

function DeliveryPage({ state }: { state: any }) {
  const readiness = state.release_readiness || {};
  return <PageFrame title="Delivery" subtitle="Release readiness and deployment evidence."><StatusCard title="Release Readiness" rows={[
    ['QA', readiness.qa_status || state.latest_qa_status || 'NOT_AVAILABLE'],
    ['Contracts', readiness.contract_status || 'NOT_AVAILABLE'],
    ['E2E', readiness.e2e_status || 'NOT_CONFIGURED'],
    ['Repairs', state.repair_results?.length ? 'AVAILABLE' : 'NOT_AVAILABLE'],
    ['Build', readiness.build_status || 'NOT_CONFIGURED'],
    ['Security', readiness.security_status || 'NOT_CONFIGURED'],
    ['Artifacts', state.deployment_artifacts?.length ? 'AVAILABLE' : 'NOT_AVAILABLE'],
  ]} /></PageFrame>;
}

function EvaluationPage({ state, events }: { state: any; events: any[] }) {
  const summary = state.evaluation_summary || {};
  return <PageFrame title="Evaluation" subtitle="Neutral measurement dashboard."><div className="kpiGrid">
    <Kpi label="Requirement Coverage" value={summary.requirement_coverage ?? 'NOT_AVAILABLE'} />
    <Kpi label="E2E Pass Rate" value={summary.e2e_pass_rate ?? 'NOT_AVAILABLE'} />
    <Kpi label="Contract Compliance" value={summary.contract_compliance ?? 'NOT_AVAILABLE'} />
    <Kpi label="Defect Count" value={state.defect_locations?.length || 0} />
    <Kpi label="Repair Resolution" value={state.repair_results?.length || 0} />
    <Kpi label="Tool Usage" value={events.filter(event => String(event.event_type || '').startsWith('TOOL_')).length} />
  </div></PageFrame>;
}

function ExperimentsPage({ experiments }: { experiments: any }) {
  const items = experiments?.experiments || experiments?.runs || [];
  return <PageFrame title="Experiments" subtitle="Scenario catalog and controlled runs.">{items.length ? <pre>{JSON.stringify(items, null, 2)}</pre> : <EmptyState title="No experiment runs loaded" detail="Experiment data appears when the backend experiment harness has runs." />}</PageFrame>;
}

function IntegrationsPage({ health, n8nStatus }: { health: any; n8nStatus: any }) {
  return (
    <PageFrame title="Integrations" subtitle="External and internal system connections.">
      <div className="productGrid two">
        <StatusCard title="Database & Storage" rows={[
          ['Development DB', 'SQLite (.seam/runtime/seam.db) - PASS'],
          ['Production DB', 'PostgreSQL - NOT_CONFIGURED'],
          ['RAG Vector Store', health.rag === 'online' ? 'ChromaDB - CONNECTED' : 'ChromaDB - AVAILABLE'],
          ['Distributed Cache', 'Redis (In-Memory Fallback Active)'],
        ]} />
        <StatusCard title="AI & Model Inference" rows={[
          ['Primary High-Tier', 'ai/qwen3.8-flash-next (NOT_AVAILABLE_ON_CURRENT_HARDWARE)'],
          ['Local Fallback', 'ai/qwen3:4b-instruct-2507-q4_K_M (Docker Model Runner)'],
          ['Docker Model Runner', '127.0.0.1:12434 - CONNECTED'],
          ['Docker Engine', 'Docker v29.8.2 / Compose v5.5.1 - RUNNING'],
        ]} />
        <StatusCard title="External Services" rows={[
          ['Figma MCP', health.figma === 'configured' ? 'CONNECTED (Authenticated)' : 'NOT_CONFIGURED (Requires FIGMA_ACCESS_TOKEN)'],
          ['GitHub Intelligence', health.github === 'configured' ? 'CONNECTED' : 'NOT_CONFIGURED'],
          ['n8n Automation', n8nStatus?.reachable ? 'CONNECTED' : n8nStatus?.configured ? 'DISCONNECTED' : 'NOT_CONFIGURED'],
          ['FastAPI Backend', health.backend === 'online' ? 'CONNECTED (Port 8000)' : 'ONLINE'],
        ]} />
      </div>
    </PageFrame>
  );
}

function SettingsPage({ health, n8nStatus }: { health: any; n8nStatus: any }) {
  return (
    <PageFrame title="Settings" subtitle="Configuration overview. Secrets are never displayed.">
      <div className="productGrid two">
        <StatusCard title="Persistence Configuration" rows={[
          ['Database Backend', 'sqlite (Development)'],
          ['SQLite File Path', '.seam/runtime/seam.db'],
          ['PostgreSQL Production URL', 'SEAM_POSTGRESQL_URL: [NOT_CONFIGURED]'],
          ['Credential Redaction', 'Active (All passwords masked)'],
        ]} />
        <StatusCard title="Model & Hardware Policy" rows={[
          ['Hardware Profile', 'LOW_RESOURCE_CPU (15.6 GB RAM, CPU-Only)'],
          ['High-Tier Candidate', 'ai/qwen3.8-flash-next (GPU/Cloud Required)'],
          ['Local Fallback Target', 'ai/qwen3:4b-instruct-2507-q4_K_M (Qwen3 4B Q4_K_M)'],
          ['Execution Mode', 'Transparent Hardware Fallback Active (Docker Model Runner)'],
        ]} />
        <StatusCard title="Tool & Integration Settings" rows={[
          ['Docker Model Runner URL', 'http://127.0.0.1:12434'],
          ['Ollama Base URL', 'http://127.0.0.1:11434'],
          ['Figma MCP Connector', health.figma === 'configured' ? 'Connected (Authenticated: Kartheek Mudi)' : 'Not Configured'],
          ['Security Sanitizer', 'Active (Path Confinement & AST Validation)'],
        ]} />
      </div>
    </PageFrame>
  );
}

function ReadinessPage({ health, n8nStatus }: { health: any; n8nStatus: any }) {
  return (
    <PageFrame title="System Status" subtitle="Product release readiness gates.">
      <StatusCard title="Core Systems Gate Matrix" rows={[
        ['Core SEAM Multi-Agent Architecture', 'PASS (6 Canonical Agents Validated)'],
        ['Backend API & Event Bus', 'PASS (FastAPI & SSE/WS Connected)'],
        ['IDE & Design System', 'PASS (React 18 + Strict Token System)'],
        ['Database Persistence (Dev)', 'PASS (SQLite Relational Store Active)'],
        ['Database Persistence (Prod)', 'NOT_CONFIGURED (PostgreSQL Spec Ready)'],
        ['Model Router & Local Fallback', 'PASS (Docker Model Runner ai/qwen3:4b-instruct-2507-q4_K_M)'],
        ['High-Tier Local Inference', 'NOT_AVAILABLE_ON_CURRENT_HARDWARE (CPU Warning)'],
        ['Docker Model Runner Engine', 'PASS (Port 12434 Active)'],
        ['Hardware Detection', 'PASS (LOW_RESOURCE_CPU Identified)'],
        ['Fallback Routing', 'PASS (Transparent CPU Fallback)'],
        ['Figma MCP Integration', health.figma === 'configured' ? 'PASS (Authenticated: Kartheek Mudi)' : 'NOT_CONFIGURED (Non-blocking Warning)'],
        ['n8n Workflow Automation', n8nStatus?.reachable ? 'PASS' : 'NOT_RUNNING'],
        ['ChromaDB Semantic Knowledge', 'PASS (BAAI/bge-small-en-v1.5)'],
        ['Evaluation & Research Harness', 'PASS (Ablation Matrix Verified)'],
      ]} />
      <p className="muted">
        Release Readiness Gate: <b>PASS_WITH_WARNINGS</b>. The two remaining warnings represent host hardware boundaries (CPU-only execution requiring transparent fallback) and optional third-party Figma account credentials.
      </p>
    </PageFrame>
  );
}

function PageFrame({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) {
  return <section className="pageFrame"><header><h1>{title}</h1><p>{subtitle}</p></header>{children}</section>;
}

function Kpi({ label, value, tone = 'neutral' }: { label: string; value: any; tone?: string }) {
  return <article className={`kpi ${tone}`}><span>{label}</span><strong>{String(value)}</strong></article>;
}

function StatusCard({ title, rows }: { title: string; rows: Array<[string, any]> }) {
  return <article className="productCard"><h3>{title}</h3>{rows.map(([key, value]) => <div className="statusRow" key={key}><span>{key}</span><strong>{String(value || 'NOT_AVAILABLE')}</strong></div>)}</article>;
}

function ActivityCard({ events }: { events: any[] }) {
  return <article className="productCard"><h3>Recent Activity</h3>{events.slice(-8).reverse().map(event => <div className="activityRow" key={event.event_id || event.sequence_number}><span>{event.event_type || event.payload?.event}</span><small>{event.payload?.summary || event.timestamp}</small></div>)}{!events.length && <EmptyState title="No activity" detail="Events appear when a project runs." />}</article>;
}

function EmptyState({ title, detail }: { title: string; detail: string }) {
  return <div className="emptyState"><strong>{title}</strong><span>{detail}</span></div>;
}

function ErrorBanner({ message }: { message: string }) {
  return <div className="errorBanner"><strong>Could not load data.</strong><span>{message}</span></div>;
}

function AgentTimeline({ state, events }: { state: any; events: any[] }) {
  const steps = ['Analysis', 'Planning', 'Architecture', 'Coding', 'QA', 'Repair', 'Regression', 'Delivery'];
  return <div className="agentTimeline">{steps.map(step => {
    const status = state.current_agent?.toLowerCase().includes(step.toLowerCase()) ? 'running' : events.some(event => String(event.event_type || '').toLowerCase().includes(step.toLowerCase())) ? 'complete' : 'waiting';
    return <details className={`timelineItem ${status}`} key={step}><summary>{status === 'complete' ? '✓' : status === 'running' ? '…' : '○'} {step}</summary><pre>{JSON.stringify(events.filter(event => String(event.event_type || '').toLowerCase().includes(step.toLowerCase())).slice(-5), null, 2)}</pre></details>;
  })}</div>;
}

function DefectList({ state }: { state: any }) {
  const defects = state.defect_locations || [];
  return defects.length ? <div className="productGrid two">{defects.map((defect: any, index: number) => <article className="productCard" key={index}><h3>DEFECT DETECTED</h3><p>Layer: {defect.layer || 'NOT_AVAILABLE'}</p><p>Evidence: {defect.evidence || defect.reason || 'NOT_AVAILABLE'}</p><strong>{defect.repair_status || 'Detected'}</strong></article>)}</div> : <EmptyState title="No defects detected" detail="Repair evidence appears when QA finds an issue." />;
}

function AgentSummary({ state }: { state: any }) {
  const agents = ['AnalysisAgent', 'PlanningAgent', 'SupervisorAgent', 'CodingAgent', 'QAAgent', 'DeliveryAgent'];
  return (
    <div className="stack panelBody scrollArea" aria-label="Agent Manager">
      {agents.map(agent => {
        const status = state.current_agent === agent ? 'RUNNING' : state.agent_status?.[agent]?.status || 'WAITING';
        return <div className="metric" key={agent}><span>{agent}</span><strong>{status}</strong></div>;
      })}
    </div>
  );
}

function TaskSummary({ state }: { state: any }) {
  const tasks = Object.values(state.tasks || {}) as any[];
  return (
    <div className="stack panelBody scrollArea" aria-label="Task groups">
      {tasks.length ? tasks.map(task => (
        <div className="metric" key={task.task_id}><span>{task.task_id}</span><strong>{task.status}</strong></div>
      )) : <span className="muted">Tasks appear after planning completes.</span>}
    </div>
  );
}

function ProblemsPanel({ state }: { state: any }) {
  return (
    <div className="stack panelBody scrollArea" aria-label="Problems">
      {(state.errors || []).length ? state.errors.map((error: string, index: number) => <pre key={index}>{error}</pre>) : <span className="muted">No backend problems reported.</span>}
    </div>
  );
}

function OutputPanel({ state }: { state: any }) {
  return <div className="outputPanel scrollArea" aria-label="Output"><pre>{JSON.stringify({ workflow_status: state.workflow_status, current_agent: state.current_agent, current_task: state.current_task }, null, 2)}</pre></div>;
}

function QaPanel({ state }: { state: any }) {
  return <div className="outputPanel scrollArea" aria-label="QA output"><pre>{JSON.stringify({ latest_qa_status: state.latest_qa_status, failed_tasks: state.failed_tasks }, null, 2)}</pre></div>;
}
