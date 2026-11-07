import React, { useState, useRef, useEffect } from 'react';

export type SlashCommandDef = {
  command: string;
  description: string;
  agent: string;
};

export const AVAILABLE_COMMANDS: SlashCommandDef[] = [
  { command: '/analyze', description: 'Analyze requirements & formulate scope boundaries', agent: 'Analysis Agent' },
  { command: '/plan', description: 'Synthesize architecture blueprints & 10 diagrams', agent: 'Planning & Design Agent' },
  { command: '/code', description: 'Implement code logic & context providers', agent: 'Coding Agent' },
  { command: '/qa', description: 'Run comprehensive test suites & contracts verification', agent: 'QA Agent' },
  { command: '/repair', description: 'Execute autonomous defect repair & regression closure', agent: 'Coding Agent' },
  { command: '/review', description: 'Audit full-stack contracts, ASTs & schemas', agent: 'Supervisor' },
  { command: '/deliver', description: 'Package release artifacts & verify delivery gates', agent: 'Delivery Agent' },
  { command: '/status', description: 'Inspect agent states, telemetry & process status', agent: 'Supervisor' },
];

export type AgentCommandBarProps = {
  isRunning: boolean;
  onSubmitCommand: (cmd: string) => Promise<void> | void;
  onClearConversation?: () => void;
};

export function AgentCommandBar({
  isRunning,
  onSubmitCommand,
  onClearConversation,
}: AgentCommandBarProps) {
  const [inputVal, setInputVal] = useState('');
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [selectedIdx, setSelectedIdx] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  // Filter commands if user typed "/..."
  const filteredCommands = React.useMemo(() => {
    if (!inputVal.startsWith('/')) return AVAILABLE_COMMANDS;
    const query = inputVal.toLowerCase();
    return AVAILABLE_COMMANDS.filter(c => c.command.toLowerCase().startsWith(query));
  }, [inputVal]);

  useEffect(() => {
    if (inputVal.startsWith('/')) {
      setPaletteOpen(true);
      setSelectedIdx(0);
    } else {
      setPaletteOpen(false);
    }
  }, [inputVal]);

  const handleSelectCommand = (cmd: string) => {
    setInputVal(cmd + ' ');
    setPaletteOpen(false);
    inputRef.current?.focus();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputVal.trim()) return;
    const text = inputVal.trim();
    setInputVal('');
    setPaletteOpen(false);
    await onSubmitCommand(text);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (paletteOpen && filteredCommands.length > 0) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIdx(prev => (prev + 1) % filteredCommands.length);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIdx(prev => (prev - 1 + filteredCommands.length) % filteredCommands.length);
      } else if (e.key === 'Enter' || e.key === 'Tab') {
        if (inputVal.startsWith('/') && !inputVal.includes(' ')) {
          e.preventDefault();
          handleSelectCommand(filteredCommands[selectedIdx]?.command || inputVal);
        }
      } else if (e.key === 'Escape') {
        setPaletteOpen(false);
      }
    }
  };

  return (
    <div className="agentCommandConsoleWrapper">
      {/* Autocomplete Palette Modal/Popup */}
      {paletteOpen && filteredCommands.length > 0 && (
        <div className="commandPaletteDropdown" role="listbox" aria-label="Slash commands autocomplete">
          <div className="paletteDropdownHeader">
            <span>ENGINEERING COMMAND PALETTE</span>
            <span>Use ↑↓ to navigate • ↵ / Tab to select</span>
          </div>
          <div className="paletteList">
            {filteredCommands.map((item, idx) => (
              <div
                key={item.command}
                className={`paletteItem ${idx === selectedIdx ? 'selected' : ''}`}
                onClick={() => handleSelectCommand(item.command)}
                role="option"
                aria-selected={idx === selectedIdx}
              >
                <div className="paletteItemCommand monospace">
                  <strong>{item.command}</strong>
                  <span className="paletteItemAgent">[{item.agent}]</span>
                </div>
                <div className="paletteItemDesc">{item.description}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Engineering Console Input Bar */}
      <form className="agentConsoleForm" onSubmit={handleSubmit}>
        <div className="consoleInputPrefix monospace">/seam &gt;</div>
        <input
          ref={inputRef}
          type="text"
          className="consoleInput monospace"
          placeholder="Execute engineering command (type / for command palette)..."
          value={inputVal}
          onChange={e => setInputVal(e.target.value)}
          onKeyDown={handleKeyDown}
          aria-label="Engineering command console"
        />
        <button
          type="submit"
          className="consoleSubmitBtn"
          disabled={!inputVal.trim()}
          title="Dispatch command to SEAM orchestrator"
        >
          EXECUTE
        </button>
      </form>
    </div>
  );
}
