import React, { useState, useEffect } from 'react';
import { ProjectSummary, FileNode } from '../api/client';
import { ChatMessage } from '../seam/chatTypes';
import { VSCodeMenuBar } from '../components/VSCodeMenuBar';
import { ActivityBar } from './ActivityBar';
import { StatusBar } from './StatusBar';
import { ProjectExplorer } from '../explorer/ProjectExplorer';
import { WorkspaceSearchPanel } from '../components/WorkspaceSearchPanel';
import { GitControlPanel } from '../components/GitControlPanel';
import { RunDebugPanel } from '../components/RunDebugPanel';
import { AccountProfileModal } from '../components/AccountProfileModal';
import { EditorTabs } from '../editor/EditorTabs';
import { BreadcrumbBar } from '../components/BreadcrumbBar';
import { CodeEditor } from '../editor/CodeEditor';
import { TerminalSessionSelector } from '../components/TerminalSessionSelector';
import { SEAMAgentPanel } from '../seam/SEAMAgentPanel';
import { AgentCollapsedWidget } from '../seam/components/AgentCollapsedWidget';
import { AntigravityHUD } from '../components/AntigravityHUD';
import { CommandPalette, CommandItem } from '../components/CommandPalette';

// Consoles
import { DesignStudioPage } from '../components/DesignStudioPage';
import { TestLabPage } from '../components/TestLabPage';
import { ContractsPage } from '../components/ContractsPage';
import { RepairCenterPage } from '../components/RepairCenterPage';
import { RuntimeConsolePage } from '../components/RuntimeConsolePage';
import { ModelControlPanel } from '../components/ModelControlPanel';
import { DeliveryCenterPage } from '../components/DeliveryCenterPage';
import { EvaluationPage } from '../components/EvaluationPage';
import { ExperimentsPage } from '../components/ExperimentsPage';
import { IntegrationsPage } from '../components/IntegrationsPage';
import { ReadinessPage } from '../components/ReadinessPage';
import { SettingsPage } from '../components/SettingsPage';
import { ProjectBuilder } from '../components/ProjectBuilder/ProjectBuilder';

export type Tab = {
  path: string;
  content: string;
  savedContent: string;
  version: number;
  kind?: 'text' | 'image';
  url?: string;
};

export type AppShellProps = {
  projects: ProjectSummary[];
  projectId: string | null;
  onSelectProject: (id: string | null) => void;
  state: any;
  health: any;
  n8nStatus: any;
  events: any[];
  tree: FileNode[];
  tabs: Tab[];
  activePath: string;
  filter: string;
  onFilter: (value: string) => void;
  onOpen: (path: string) => void | Promise<void>;
  onCloseTab: (path: string) => void;
  onSelectTab: (path: string) => void;
  onContentChange: (content: string) => void;
  onSaveFile: () => Promise<void>;
  onReloadFile: () => Promise<void>;
  onCreateFile: () => void;
  onCreateFolder: () => void;
  onRename: () => void;
  onDelete: () => void;
  onRefresh: () => Promise<void>;
  logs: string[];
  onClearLogs: () => void;
  wsStatus: string;
  messages: ChatMessage[];
  onRunWorkflow: () => Promise<void>;
  onStopWorkflow: () => Promise<void>;
  onChatCommand: (text: string) => Promise<void>;
  onClearConversation: () => void;
  wordWrap: boolean;
  onToggleWordWrap: () => void;
  // External Page renderers
  activeView: string;
  onSelectView: (view: string) => void;
  renderPageView?: (view: string) => React.ReactNode;
  onGoHome?: () => void;
  userDisplayName?: string;
  userEmail?: string;
};

export function AppShell({
  projects,
  projectId,
  onSelectProject,
  state,
  health,
  n8nStatus,
  events,
  tree,
  tabs,
  activePath,
  filter,
  onFilter,
  onOpen,
  onCloseTab,
  onSelectTab,
  onContentChange,
  onSaveFile,
  onReloadFile,
  onCreateFile,
  onCreateFolder,
  onRename,
  onDelete,
  onRefresh,
  logs,
  onClearLogs,
  wsStatus,
  messages,
  onRunWorkflow,
  onStopWorkflow,
  onChatCommand,
  onClearConversation,
  wordWrap,
  onToggleWordWrap,
  activeView,
  onSelectView,
  renderPageView,
  onGoHome,
  userDisplayName = 'Kartheek Mudi',
  userEmail = 'engineer@seam.internal',
}: AppShellProps) {
  // Panel visibility states
  const [sidebarVisible, setSidebarVisible] = useState(true);
  const [terminalVisible, setTerminalVisible] = useState(true);
  const [agentPanelVisible, setAgentPanelVisible] = useState(true);
  const [activeActivityTool, setActiveActivityTool] = useState('explorer');
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [accountModalOpen, setAccountModalOpen] = useState(false);
  const [isSplit, setIsSplit] = useState(false);
  const [cursorPos, setCursorPos] = useState({ line: 1, col: 1 });

  // Sizing
  const [terminalHeight, setTerminalHeight] = useState(240);
  const [sidebarWidth, setSidebarWidth] = useState(256);
  const [agentPanelWidth, setAgentPanelWidth] = useState(320);

  const activeTab = tabs.find(t => t.path === activePath);
  const secondaryTab = tabs.find(t => t.path !== activePath) || activeTab;
  const defectCount = state?.defect_locations?.length || 0;
  const projectName = projects.find(p => p.project_id === projectId)?.project_name || projectId || 'SEAM-WORKSPACE';

  // Map file contents cache for search
  const cachedContents: Record<string, string> = {};
  tabs.forEach(t => {
    cachedContents[t.path] = t.content;
  });

  // Global keyboard shortcuts (Ctrl+K, Ctrl+Shift+P, Ctrl+B, Ctrl+J, Ctrl+`, Ctrl+S)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && (e.key === 'p' || e.key === 'P')) {
        e.preventDefault();
        setCommandPaletteOpen(prev => !prev);
      } else if ((e.ctrlKey || e.metaKey) && (e.key === 'k' || e.key === 'K')) {
        e.preventDefault();
        setCommandPaletteOpen(prev => !prev);
      } else if ((e.ctrlKey || e.metaKey) && (e.key === 'b' || e.key === 'B')) {
        e.preventDefault();
        setSidebarVisible(prev => !prev);
      } else if ((e.ctrlKey || e.metaKey) && e.shiftKey && (e.key === 'a' || e.key === 'A')) {
        e.preventDefault();
        setAgentPanelVisible(prev => !prev);
      } else if ((e.ctrlKey || e.metaKey) && (e.key === 'j' || e.key === 'J')) {
        e.preventDefault();
        setAgentPanelVisible(prev => !prev);
      } else if ((e.ctrlKey || e.metaKey) && e.key === '`') {
        e.preventDefault();
        setTerminalVisible(prev => !prev);
      } else if ((e.ctrlKey || e.metaKey) && (e.key === 's' || e.key === 'S')) {
        e.preventDefault();
        onSaveFile();
      } else if ((e.ctrlKey || e.metaKey) && e.key === '\\') {
        e.preventDefault();
        setIsSplit(prev => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onSaveFile]);

  // Command palette item catalog across all categories
  const commands: CommandItem[] = [
    // SEAM Autonomous Actions
    { id: 'seam-builder', label: 'SEAM: Create Project & Configure Technology Stack', category: 'SEAM', shortcut: 'Ctrl+N', action: () => onSelectView('builder') },
    { id: 'seam-analyze', label: 'SEAM: Analyze Requirements & Formulate Scope', category: 'SEAM', action: () => onSelectView('dashboard') },
    { id: 'seam-plan', label: 'SEAM: Generate Architecture Plan & Diagrams', category: 'SEAM', action: () => onSelectView('design') },
    { id: 'seam-run', label: 'SEAM: Start Autonomous Multi-Agent Workflow', category: 'SEAM', shortcut: 'Ctrl+Enter', action: onRunWorkflow },
    { id: 'seam-qa', label: 'SEAM: Run Comprehensive QA & Contract Verification', category: 'SEAM', action: () => onSelectView('testlab') },
    { id: 'seam-repair', label: 'SEAM: Execute Autonomous Defect Repair Loop', category: 'SEAM', shortcut: 'Alt+R', action: () => onSelectView('repair') },
    { id: 'seam-delivery', label: 'SEAM: Verify Release Gates & Package Delivery', category: 'SEAM', action: () => onSelectView('delivery') },
    { id: 'seam-stop', label: 'SEAM: Stop Current Workflow Execution', category: 'SEAM', action: onStopWorkflow },

    // Navigation & Views
    { id: 'view-editor', label: 'View: Show Code Editor', category: 'Navigation', shortcut: 'Alt+E', action: () => onSelectView('editor') },
    { id: 'view-design', label: 'View: Open Design Studio (10 Canonical Diagrams)', category: 'Architecture', shortcut: 'Alt+G', action: () => onSelectView('design') },
    { id: 'view-contracts', label: 'View: Open Full-Stack Contracts Drift Detector', category: 'Architecture', shortcut: 'Alt+C', action: () => onSelectView('contracts') },
    { id: 'view-testlab', label: 'View: Open Test Lab (17 Categories)', category: 'Testing', shortcut: 'Alt+T', action: () => onSelectView('testlab') },
    { id: 'view-repair', label: 'View: Open Autonomous Defect Repair Center', category: 'Repair', action: () => onSelectView('repair') },
    { id: 'view-runtime', label: 'View: Open Runtime & Process Lifecycle Console', category: 'Runtime', shortcut: 'Alt+P', action: () => onSelectView('runtime') },
    { id: 'view-models', label: 'View: Open Model Router & Hardware Control', category: 'AI Inference', shortcut: 'Alt+M', action: () => onSelectView('models') },
    { id: 'view-eval', label: 'View: Open Evaluation Console (Ablations)', category: 'Research', action: () => onSelectView('evaluation') },
    { id: 'view-experiments', label: 'View: Open Experiments Matrix Console', category: 'Research', action: () => onSelectView('experiments') },
    { id: 'view-integrations', label: 'View: Open Integrations Management', category: 'Integrations', action: () => onSelectView('integrations') },
    { id: 'view-readiness', label: 'View: Open System Readiness & Health Gates', category: 'System', action: () => onSelectView('readiness') },
    { id: 'view-settings', label: 'View: Open Workspace & Engine Settings', category: 'Settings', shortcut: 'Ctrl+,', action: () => onSelectView('settings') },
    { id: 'view-landing', label: 'View: Open Public SEAM Landing Page', category: 'Navigation', shortcut: 'Alt+H', action: () => onGoHome?.() },

    // Layout & Editor Actions
    { id: 'toggle-sidebar', label: 'View: Toggle Primary Side Bar', category: 'Editor', shortcut: 'Ctrl+B', action: () => setSidebarVisible(!sidebarVisible) },
    { id: 'toggle-terminal', label: 'View: Toggle Integrated Terminal Panel', category: 'Editor', shortcut: 'Ctrl+`', action: () => setTerminalVisible(!terminalVisible) },
    { id: 'toggle-agent', label: 'View: Toggle SEAM Agent Control Panel', category: 'Editor', shortcut: 'Ctrl+J', action: () => setAgentPanelVisible(!agentPanelVisible) },
    { id: 'toggle-split', label: 'View: Split Editor Right (Side-by-Side)', category: 'Editor', shortcut: 'Ctrl+\\', action: () => setIsSplit(!isSplit) },
    { id: 'save-file', label: 'File: Save Active File', category: 'Files', shortcut: 'Ctrl+S', action: onSaveFile },
    { id: 'refresh-state', label: 'System: Refresh All State & Backend Health', category: 'System', shortcut: 'F5', action: onRefresh },
    { id: 'user-profile', label: 'Account: Open Firebase User Profile & Persistence', category: 'Account', action: () => setAccountModalOpen(true) },
  ];

  const handleToolSelect = (tool: string) => {
    setActiveActivityTool(tool);
    if (tool === 'explorer' || tool === 'search' || tool === 'git' || tool === 'debug') {
      setSidebarVisible(true);
      if (activeView !== 'editor') onSelectView('editor');
    } else if (tool === 'settings') {
      onSelectView('settings');
    } else if (tool === 'account') {
      setAccountModalOpen(true);
    }
  };

  return (
    <div className="vscodeAppShell" role="application" aria-label="SEAM IDE Workspace">
      {/* 1. TOP MENU & TITLE BAR */}
      <VSCodeMenuBar
        projectName={projectName}
        activePath={activePath}
        onOpenCommandPalette={() => setCommandPaletteOpen(true)}
        onRunWorkflow={onRunWorkflow}
        onStopWorkflow={onStopWorkflow}
        onSaveFile={onSaveFile}
        onToggleSidebar={() => setSidebarVisible(!sidebarVisible)}
        onToggleTerminal={() => setTerminalVisible(!terminalVisible)}
        onToggleAgentPanel={() => setAgentPanelVisible(!agentPanelVisible)}
        onGoHome={onGoHome}
        onSelectConsole={page => onSelectView(page)}
        onOpenAccount={() => setAccountModalOpen(true)}
        userDisplayName={userDisplayName}
        userEmail={userEmail}
      />

      {/* 2. MAIN HORIZONTAL WORKSPACE ROW */}
      <div className="vscodeMainWorkspace">
        {/* 2.1 Activity Bar */}
        <ActivityBar
          activeTool={activeActivityTool}
          onSelectTool={handleToolSelect}
          gitBranch="final-validation"
          defectCount={defectCount}
          onOpenCommandPalette={() => setCommandPaletteOpen(true)}
          onSelectConsole={page => onSelectView(page)}
          onOpenSettings={() => onSelectView('settings')}
          onOpenAccount={() => setAccountModalOpen(true)}
          userInitial={userDisplayName.charAt(0).toUpperCase()}
        />

        {/* 2.2 Primary Sidebar (Explorer, Search, Git, Debug) */}
        {sidebarVisible && (
          <div className="vscodeSidebarWrapper" style={{ width: `${sidebarWidth}px` }}>
            {activeActivityTool === 'explorer' && (
              <ProjectExplorer
                projectName={projectName}
                tree={tree}
                activePath={activePath}
                openEditors={tabs.map(t => ({ path: t.path, isDirty: t.content !== t.savedContent }))}
                filter={filter}
                onFilter={onFilter}
                onOpen={path => {
                  onOpen(path);
                  onSelectView('editor');
                }}
                onCloseEditor={onCloseTab}
                onCreateFile={onCreateFile}
                onCreateFolder={onCreateFolder}
                onRename={onRename}
                onDelete={onDelete}
                onRefresh={onRefresh}
              />
            )}

            {activeActivityTool === 'search' && (
              <WorkspaceSearchPanel
                tree={tree}
                onOpenFile={path => {
                  onOpen(path);
                  onSelectView('editor');
                }}
                cachedFileContents={cachedContents}
              />
            )}

            {activeActivityTool === 'git' && (
              <GitControlPanel
                branch="final-validation"
                onOpenFile={path => {
                  onOpen(path);
                  onSelectView('editor');
                }}
                onRefresh={onRefresh}
              />
            )}

            {activeActivityTool === 'debug' && (
              <RunDebugPanel
                projectName={projectName}
                onRunWorkflow={onRunWorkflow}
                onStopWorkflow={onStopWorkflow}
                onOpenRuntimeConsole={() => onSelectView('runtime')}
              />
            )}
          </div>
        )}

        {/* 2.3 Workspace Center (Tabs + Breadcrumbs + Editor + Terminal) */}
        <div className="vscodeCenterPane">
          {activeView === 'editor' ? (
            <div className="editorWorkspaceView">
              {/* Editor Tabs */}
              <EditorTabs
                tabs={tabs.map(t => ({ path: t.path, isDirty: t.content !== t.savedContent }))}
                activePath={activePath}
                onSelectTab={onSelectTab}
                onCloseTab={onCloseTab}
                onSplitEditor={() => setIsSplit(!isSplit)}
              />

              {/* Breadcrumb Navigation */}
              <BreadcrumbBar path={activePath} onNavigateSegment={onOpen} />

              {/* Code Canvas Area (Single or Split) */}
              <div className={`editorCanvasContainer ${isSplit ? 'splitLayout' : ''}`}>
                {/* Column 1: Primary Editor */}
                <div className="editorColumnPane">
                  {activeTab?.kind === 'image' ? (
                    <div className="imagePreviewPane">
                      <img src={activeTab.url} alt={activeTab.path} />
                    </div>
                  ) : activeTab ? (
                    <CodeEditor
                      path={activeTab.path}
                      content={activeTab.content}
                      version={activeTab.version}
                      wordWrap={wordWrap}
                      onChange={onContentChange}
                    />
                  ) : (
                    <div className="emptyWorkspaceNotice">
                      <div className="emptyLogoGlyph">⚡</div>
                      <h3>SEAM Autonomous Engineering Workspace</h3>
                      <p>Select a file from the Explorer or initiate an autonomous workflow via the Agent panel.</p>
                      <div className="quickTipsRow">
                        <span><kbd>Ctrl+P</kbd> Quick Open</span>
                        <span><kbd>Ctrl+K</kbd> Command Palette</span>
                        <span><kbd>Ctrl+`</kbd> Terminal</span>
                        <span><kbd>Ctrl+\</kbd> Split Editor</span>
                      </div>
                    </div>
                  )}
                </div>

                {/* Column 2: Split Editor (if enabled) */}
                {isSplit && (
                  <div className="editorColumnPane splitSecond">
                    {secondaryTab ? (
                      <CodeEditor
                        path={secondaryTab.path}
                        content={secondaryTab.content}
                        version={secondaryTab.version}
                        wordWrap={wordWrap}
                        onChange={() => {}}
                      />
                    ) : (
                      <div className="emptyWorkspaceNotice">
                        <p>No secondary tab to split.</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ) : (
            /* Dedicated Console View inside Center Pane */
            <div className="embeddedConsoleView scrollArea">
              <div className="consoleViewNavBar">
                <button className="backToEditorBtn" onClick={() => onSelectView('editor')}>
                  ← Return to Code Editor
                </button>
                <span className="consoleTitleBadge">{activeView.toUpperCase()} CONSOLE</span>
              </div>
              <div className="consoleViewContent">
                {activeView === 'builder' && (
                  <ProjectBuilder
                    projects={projects}
                    currentProjectId={projectId}
                    onSelectProject={id => {
                      onSelectProject(id);
                      onSelectView('editor');
                    }}
                    onOpenWorkspace={() => onSelectView('editor')}
                    onOpenDesignStudio={() => onSelectView('design')}
                    onOpenTestLab={() => onSelectView('testlab')}
                    onOpenDelivery={() => onSelectView('delivery')}
                    onRefreshProjects={onRefresh}
                  />
                )}
                {activeView === 'design' && <DesignStudioPage projectId={projectId} state={state} onOpenWorkspace={() => onSelectView('editor')} />}
                {activeView === 'testlab' && <TestLabPage state={state} />}
                {activeView === 'contracts' && <ContractsPage state={state} onOpenWorkspace={() => onSelectView('editor')} />}
                {activeView === 'repair' && <RepairCenterPage state={state} onOpenWorkspace={() => onSelectView('editor')} />}
                {activeView === 'runtime' && <RuntimeConsolePage health={health} state={state} />}
                {activeView === 'models' && <ModelControlPanel />}
                {activeView === 'delivery' && <DeliveryCenterPage state={state} />}
                {activeView === 'evaluation' && <EvaluationPage />}
                {activeView === 'experiments' && <ExperimentsPage />}
                {activeView === 'integrations' && <IntegrationsPage />}
                {activeView === 'readiness' && <ReadinessPage />}
                {activeView === 'settings' && <SettingsPage />}
                {renderPageView && renderPageView(activeView)}
              </div>
            </div>
          )}

          {/* Integrated Terminal (Bottom Panel) */}
          {terminalVisible && (
            <div className="vscodeBottomPanelWrapper" style={{ height: `${terminalHeight}px` }}>
              <TerminalSessionSelector
                logs={logs}
                state={state}
                onClearLogs={onClearLogs}
                activeTab="TERMINAL"
              />
            </div>
          )}
        </div>

        {/* 2.4 SEAM Agent Panel */}
        {agentPanelVisible ? (
          <div className="vscodeAgentPanelWrapper" style={{ width: `${agentPanelWidth}px` }}>
            <SEAMAgentPanel
              projectId={projectId}
              state={state}
              health={health}
              wsStatus={wsStatus}
              messages={messages}
              events={events}
              tabs={tabs}
              tree={tree}
              onRunWorkflow={onRunWorkflow}
              onStopWorkflow={onStopWorkflow}
              onRefresh={onRefresh}
              onOpenFile={onOpen}
              onChatCommand={onChatCommand}
              onClearConversation={onClearConversation}
              onClose={() => setAgentPanelVisible(false)}
              onSelectView={onSelectView}
              onWidthChange={setAgentPanelWidth}
            />
          </div>
        ) : (
          <AgentCollapsedWidget
            currentAgent={state?.current_agent || (state?.workflow_status === 'running' ? 'Coding' : 'Supervisor')}
            workflowStatus={state?.workflow_status === 'running' ? 'EXECUTING' : (state?.workflow_status ? state.workflow_status.toUpperCase() : 'READY')}
            onExpand={() => setAgentPanelVisible(true)}
          />
        )}
      </div>

      {/* 3. BOTTOM STATUS BAR */}
      <StatusBar
        gitBranch="final-validation"
        isSyncing={false}
        errorCount={defectCount}
        warningCount={0}
        cursorLine={cursorPos.line}
        cursorCol={cursorPos.col}
        tabSize={2}
        encoding="UTF-8"
        lineEnding="LF"
        language={activePath?.endsWith('.py') ? 'Python' : (activePath?.endsWith('.json') ? 'JSON' : 'TypeScript React')}
        formatter="Prettier"
        onOpenProblems={() => {
          setTerminalVisible(true);
        }}
      />

      {/* 4. ANTIGRAVITY FLOATING HUD OVERLAY */}
      <AntigravityHUD
        state={state}
        health={health}
        events={events}
        onOpenRepair={() => onSelectView('repair')}
        onRunWorkflow={onRunWorkflow}
        onOpenAgent={() => setAgentPanelVisible(true)}
      />

      {/* 5. COMMAND PALETTE MODAL (Ctrl+K / Ctrl+Shift+P) */}
      <CommandPalette
        isOpen={commandPaletteOpen}
        onClose={() => setCommandPaletteOpen(false)}
        commands={commands}
      />

      {/* 6. ACCOUNT PROFILE MODAL */}
      <AccountProfileModal
        isOpen={accountModalOpen}
        onClose={() => setAccountModalOpen(false)}
        onOpenSettings={() => onSelectView('settings')}
        projectCount={projects.length}
      />
    </div>
  );
}
