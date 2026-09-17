import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { seamApi, FileNode, ProjectSummary } from './api/client';
import { connectProjectEvents } from './api/websocket';
import { ProjectExplorer } from './explorer/ProjectExplorer';
import { CodeEditor } from './editor/CodeEditor';
import { SeamPanel } from './seam/SeamPanel';
import { ChatMessage, nowIso } from './seam/chatTypes';
import { eventToChatMessages, projectStateToChatMessages } from './seam/eventToChatMessage';
import { FlexibleLayout, PanelDefinition, UnavailablePanel } from './layout/FlexibleLayout';

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
      setHealth(await seamApi.systemHealth());
    } catch (error: any) {
      setHealth({ backend: 'offline', qwen: 'NOT_AVAILABLE', rag: 'NOT_AVAILABLE', github: 'NOT_AVAILABLE' });
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
      const nextState = await seamApi.projectStatus(projectId);
      setState(nextState);
      setStatus(`${nextState.workflow_status || 'pending'} ${nextState.current_agent || ''}`.trim());
      appendMessages(projectStateToChatMessages(nextState));
      return nextState;
    } catch (error: any) {
      log(`Status refresh failed: ${error.message}`);
      return null;
    }
  }, [appendMessages, log, projectId]);

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
    await Promise.all([refreshHealth(), refreshProjects(), refreshState(), refreshTree()]);
  }, [refreshHealth, refreshProjects, refreshState, refreshTree]);

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
        <div className="logPanel scrollArea" aria-label="SEAM logs">
          {logs.length ? logs.slice(-120).map((line, index) => <pre key={`${line}-${index}`}>{line}</pre>) : <span className="muted">Ready</span>}
        </div>
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
    { id: 'terminal', title: 'Terminal', available: false, render: () => null },
    { id: 'problems', title: 'Problems', render: () => <ProblemsPanel state={state} /> },
    { id: 'output', title: 'Output', render: () => <OutputPanel state={state} /> },
    { id: 'qa', title: 'QA', render: () => <QaPanel state={state} /> },
  ];

  return <FlexibleLayout panels={panels} topbar={topbar} />;
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
