import { useEffect, useMemo, useRef, useState } from 'react';
import { ChatMessage } from './chatTypes';

type Props = {
  projectId: string | null;
  state: any;
  health: any;
  wsStatus: string;
  messages: ChatMessage[];
  onCreateProject: (input: any) => Promise<void>;
  onRun: () => Promise<void>;
  onStop: () => Promise<void>;
  onRefresh: () => Promise<void>;
  onOpenFile: (path: string) => Promise<void>;
  onChatCommand: (text: string) => Promise<void>;
  onClearConversation: () => void;
};

const workflowSteps = [
  ['AnalysisAgent', 'Analysis'],
  ['PlanningAgent', 'Planning'],
  ['SupervisorAgent', 'Supervisor'],
  ['CodingAgent', 'Coding'],
  ['QAAgent', 'QA'],
  ['DeliveryAgent', 'Delivery'],
];

export function SeamPanel(props: Props) {
  const [showProjectForm, setShowProjectForm] = useState(!props.projectId);
  const [command, setCommand] = useState('');
  const [mode, setMode] = useState(localStorage.getItem('seam.composer.mode') || 'Default');
  const [security, setSecurity] = useState(localStorage.getItem('seam.composer.security') || 'REVIEW');
  const [contextChips, setContextChips] = useState<string[]>([]);
  const [history, setHistory] = useState<string[]>(() => JSON.parse(localStorage.getItem('seam.prompt.history') || '[]'));
  const [historyIndex, setHistoryIndex] = useState<number | null>(null);
  const [newActivity, setNewActivity] = useState(false);
  const listRef = useRef<HTMLDivElement | null>(null);
  const stickToBottom = useRef(true);
  const inputRef = useRef<HTMLTextAreaElement | null>(null);
  const visibleMessages = useMemo(() => props.messages.slice(-150), [props.messages]);
  const draftKey = `seam.prompt.draft.${props.projectId || 'global'}`;
  const showSlash = /(^|\s)\/[\w-]*$/.test(command);
  const showContext = /(^|\s)@[\w-]*$/.test(command);

  useEffect(() => {
    const list = listRef.current;
    if (!list) return;
    if (stickToBottom.current) {
      list.scrollTo({ top: list.scrollHeight });
      setNewActivity(false);
    } else {
      setNewActivity(true);
    }
  }, [visibleMessages.length]);

  useEffect(() => {
    setCommand(localStorage.getItem(draftKey) || '');
    setHistoryIndex(null);
  }, [draftKey]);

  useEffect(() => {
    localStorage.setItem(draftKey, command);
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      inputRef.current.style.height = `${Math.min(300, Math.max(56, inputRef.current.scrollHeight))}px`;
    }
  }, [command, draftKey]);

  useEffect(() => {
    localStorage.setItem('seam.composer.mode', mode);
  }, [mode]);

  useEffect(() => {
    localStorage.setItem('seam.composer.security', security);
  }, [security]);

  const submitCommand = async () => {
    const text = command.trim();
    if (!text) return;
    const enriched = [
      contextChips.length ? `Context: ${contextChips.join(', ')}` : '',
      `Mode: ${mode}`,
      `Security: ${security}`,
      text,
    ].filter(Boolean).join('\n\n');
    const nextHistory = [text, ...history.filter(item => item !== text)].slice(0, 50);
    setHistory(nextHistory);
    localStorage.setItem('seam.prompt.history', JSON.stringify(nextHistory));
    setCommand('');
    setContextChips([]);
    await props.onChatCommand(enriched);
  };

  const applyToken = (token: string) => {
    setCommand(current => current.replace(/(^|\s)([/@][\w-]*)?$/, match => `${match.startsWith(' ') ? ' ' : ''}${token} `));
    inputRef.current?.focus();
  };

  const addContext = (chip: string) => {
    setContextChips(current => current.includes(chip) ? current : [...current, chip]);
  };

  return (
    <aside className="seamPanel chatPanel">
      <div className="chatHeader">
        <div>
          <strong>SEAM AI</strong>
          <span>{props.health?.backend || 'NOT_AVAILABLE'} / WS {props.wsStatus}</span>
        </div>
        <div className="buttonRow">
          <button onClick={() => setShowProjectForm(value => !value)}>New</button>
          <button onClick={props.onRefresh}>Refresh</button>
          <button onClick={props.onClearConversation}>Clear</button>
        </div>
      </div>

      <Timeline state={props.state} />

      {showProjectForm && (
        <NewProject
          onCreateProject={async input => {
            await props.onCreateProject(input);
            setShowProjectForm(false);
          }}
        />
      )}

      <div
        className="chatList scrollArea"
        ref={listRef}
        aria-label="SEAM conversation"
        tabIndex={0}
        onScroll={() => {
          const list = listRef.current;
          if (!list) return;
          const distanceFromBottom = list.scrollHeight - list.scrollTop - list.clientHeight;
          stickToBottom.current = distanceFromBottom < 72;
          if (stickToBottom.current) setNewActivity(false);
        }}
      >
        {visibleMessages.length ? visibleMessages.map(message => (
          <ChatBubble key={message.id} message={message} onOpenFile={props.onOpenFile} />
        )) : (
          <div className="emptyChat">
            <strong>Start a SEAM conversation</strong>
            <span>Create a project or ask SEAM to show generated files, explain architecture, or run the workflow.</span>
          </div>
        )}
      </div>
      {newActivity && (
        <button className="newActivityButton" onClick={() => {
          listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' });
          stickToBottom.current = true;
          setNewActivity(false);
        }}>
          Down New activity
        </button>
      )}

      <Composer
        inputRef={inputRef}
        command={command}
        setCommand={setCommand}
        mode={mode}
        setMode={setMode}
        security={security}
        setSecurity={setSecurity}
        contextChips={contextChips}
        removeChip={chip => setContextChips(current => current.filter(item => item !== chip))}
        addContext={addContext}
        showSlash={showSlash}
        showContext={showContext}
        applyToken={applyToken}
        canRun={Boolean(props.projectId) && props.state.workflow_status !== 'running'}
        canStop={Boolean(props.projectId)}
        isRunning={props.state.workflow_status === 'running'}
        onRun={props.onRun}
        onStop={props.onStop}
        onSubmit={submitCommand}
        history={history}
        historyIndex={historyIndex}
        setHistoryIndex={setHistoryIndex}
      />
    </aside>
  );
}

const slashCommands = ['/plan', '/analyze', '/code', '/qa', '/test', '/review', '/security', '/browser', '/git', '/diff', '/artifacts', '/knowledge', '/agents', '/tasks', '/diagram', '/delivery', '/stop', '/pause', '/resume', '/retry', '/rollback'];
const contextCommands = ['@file', '@folder', '@selection', '@project', '@task', '@agent', '@artifact', '@diagram', '@qa', '@knowledge', '@git', '@terminal'];

function Composer(props: {
  inputRef: React.MutableRefObject<HTMLTextAreaElement | null>;
  command: string;
  setCommand: (value: string) => void;
  mode: string;
  setMode: (value: string) => void;
  security: string;
  setSecurity: (value: string) => void;
  contextChips: string[];
  removeChip: (chip: string) => void;
  addContext: (chip: string) => void;
  showSlash: boolean;
  showContext: boolean;
  applyToken: (token: string) => void;
  canRun: boolean;
  canStop: boolean;
  isRunning: boolean;
  onRun: () => Promise<void>;
  onStop: () => Promise<void>;
  onSubmit: () => Promise<void>;
  history: string[];
  historyIndex: number | null;
  setHistoryIndex: (index: number | null) => void;
}) {
  const selectHistory = (direction: 'up' | 'down') => {
    if (!props.history.length) return;
    const next = direction === 'up'
      ? Math.min(props.history.length - 1, props.historyIndex === null ? 0 : props.historyIndex + 1)
      : Math.max(0, (props.historyIndex || 0) - 1);
    props.setHistoryIndex(next);
    props.setCommand(props.history[next] || '');
  };

  return (
    <div className="composer">
      <div className="chatActions">
        {!props.isRunning && <button onClick={props.onRun} disabled={!props.canRun}>Run Workflow</button>}
        {props.isRunning && <button onClick={props.onStop} disabled={!props.canStop}>Stop</button>}
        <button disabled title="Pause is unavailable until backend cancellation is implemented.">Pause</button>
      </div>

      {props.contextChips.length > 0 && (
        <div className="contextChips">
          {props.contextChips.map(chip => <button key={chip} onClick={() => props.removeChip(chip)}>{chip} x</button>)}
        </div>
      )}

      <div className="composerBox" onDragOver={event => event.preventDefault()} onDrop={event => {
        event.preventDefault();
        const text = event.dataTransfer.getData('text/plain');
        if (text) props.addContext(text);
      }}>
        <textarea
          ref={props.inputRef}
          rows={1}
          value={props.command}
          onChange={event => props.setCommand(event.target.value)}
          placeholder="Ask SEAM anything... Use / for commands or @ for context."
          onKeyDown={event => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault();
              void props.onSubmit();
            }
            if (event.key === 'Enter' && event.ctrlKey) {
              event.preventDefault();
              void props.onSubmit();
            }
            if (event.key === 'ArrowUp' && !props.command.includes('\n')) {
              event.preventDefault();
              selectHistory('up');
            }
            if (event.key === 'ArrowDown' && props.historyIndex !== null) {
              event.preventDefault();
              selectHistory('down');
            }
            if (event.key === 'Escape') {
              props.setCommand(props.command.replace(/(^|\s)([/@][\w-]*)$/, ''));
            }
          }}
        />
        {(props.showSlash || props.showContext) && (
          <div className="autocompleteMenu">
            {(props.showSlash ? slashCommands : contextCommands).map(item => (
              <button key={item} onClick={() => props.applyToken(item)}>{item}</button>
            ))}
          </div>
        )}
        <div className="composerToolbar">
          <button onClick={() => props.addContext('@file')}>+</button>
          <button onClick={() => props.applyToken('@')}>@</button>
          <button onClick={() => props.applyToken('/')}>/</button>
          <button disabled title="File attachments need backend upload support.">Attach</button>
          <button disabled title="Voice provider is unavailable.">Voice</button>
          <select value={props.mode} onChange={event => props.setMode(event.target.value)}>
            {['Plan', 'Default', 'Fast'].map(item => <option key={item}>{item}</option>)}
          </select>
          <select value="Qwen / Ollama" disabled>
            <option>Qwen / Ollama</option>
          </select>
          <select value={props.security} onChange={event => props.setSecurity(event.target.value)}>
            {['SAFE', 'DEFAULT', 'REVIEW', 'SANDBOX'].map(item => <option key={item}>{item}</option>)}
          </select>
          <button className="sendButton" onClick={props.onSubmit}>Send</button>
        </div>
      </div>
    </div>
  );
}

function Timeline({ state }: { state: any }) {
  return (
    <div className="workflowTimeline">
      {workflowSteps.map(([agent, label]) => {
        const status = state.current_agent === agent ? 'RUNNING' : state.agent_status?.[agent]?.status || 'WAITING';
        const mark = status === 'running' || status === 'RUNNING' ? 'RUNNING' : status === 'complete' ? 'COMPLETE' : status.toUpperCase();
        return <span key={agent} className={`timelineStep ${mark.toLowerCase()}`}>{label}: {mark}</span>;
      })}
    </div>
  );
}

function NewProject({ onCreateProject }: { onCreateProject: (input: any) => Promise<void> }) {
  const [form, setForm] = useState({ project_name: '', requirement: '', scale: 'AUTO', technology_preferences: '', workspace_location: '', github_repository: '', additional_constraints: '' });
  const update = (key: string, value: string) => setForm(current => ({ ...current, [key]: value }));
  return (
    <div className="newProjectCard">
      <label>Project Name<input value={form.project_name} onChange={event => update('project_name', event.target.value)} /></label>
      <label>Requirements<textarea rows={5} value={form.requirement} onChange={event => update('requirement', event.target.value)} /></label>
      <div className="twoCol">
        <label>Scale<select value={form.scale} onChange={event => update('scale', event.target.value)}>{['AUTO', 'SMALL', 'MEDIUM', 'LARGE', 'ENTERPRISE'].map(item => <option key={item}>{item}</option>)}</select></label>
        <label>Technology<input value={form.technology_preferences} onChange={event => update('technology_preferences', event.target.value)} placeholder="FastAPI, React" /></label>
      </div>
      <label>GitHub Repository<input value={form.github_repository} onChange={event => update('github_repository', event.target.value)} placeholder="optional" /></label>
      <button disabled={!form.project_name.trim() || !form.requirement.trim()} onClick={() => onCreateProject({ ...form, technology_preferences: form.technology_preferences.split(',').map(item => item.trim()).filter(Boolean) })}>Start Conversation</button>
    </div>
  );
}

function ChatBubble({ message, onOpenFile }: { message: ChatMessage; onOpenFile: (path: string) => Promise<void> }) {
  const [expanded, setExpanded] = useState(false);
  const isUser = message.role === 'USER';
  const lines = message.content.split('\n');
  const long = lines.length > 8 || message.content.length > 700;
  const content = long && !expanded ? lines.slice(0, 8).join('\n') : message.content;

  return (
    <article className={`chatBubble ${isUser ? 'user' : 'assistant'} ${message.status.toLowerCase()}`}>
      <header>
        <strong>{isUser ? 'You' : message.agent || message.role}</strong>
        <span>{new Date(message.timestamp).toLocaleTimeString()}</span>
      </header>
      <pre>{content}</pre>
      {typeof message.metadata?.codePreview === 'string' && (
        <div className="codePreviewCard">
          <div className="codePreviewHeader">
            <strong>Generated code</strong>
            {message.metadata.previewTruncated ? <span>Preview truncated</span> : <span>Full preview</span>}
          </div>
          <pre>{message.metadata.codePreview}</pre>
        </div>
      )}
      {long && <button className="linkButton" onClick={() => setExpanded(value => !value)}>{expanded ? 'Show less' : 'Show details'}</button>}
      {message.artifact && <ArtifactCard artifact={message.artifact} taskId={message.taskId} onOpenFile={onOpenFile} />}
      <footer>{message.type} / {message.status}</footer>
    </article>
  );
}

function ArtifactCard({ artifact, taskId, onOpenFile }: { artifact: NonNullable<ChatMessage['artifact']>; taskId?: string; onOpenFile: (path: string) => Promise<void> }) {
  return (
    <div className="artifactCard">
      <strong>{artifact.label}</strong>
      <span>{artifact.kind}{taskId ? ` / ${taskId}` : ''}</span>
      {artifact.kind === 'file' && artifact.path && <button onClick={() => onOpenFile(artifact.path!)}>Open File</button>}
      {artifact.kind !== 'file' && <button disabled>Open {artifact.kind}</button>}
    </div>
  );
}
