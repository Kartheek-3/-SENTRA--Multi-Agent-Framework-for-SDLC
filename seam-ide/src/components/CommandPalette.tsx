import React, { useEffect, useState, useMemo } from 'react';

export interface CommandItem {
  id: string;
  label: string;
  category: string;
  shortcut?: string;
  action: () => void;
}

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  commands: CommandItem[];
}

export function CommandPalette({ isOpen, onClose, commands }: CommandPaletteProps) {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);

  const filteredCommands = useMemo(() => {
    if (!query.trim()) return commands;
    const lower = query.toLowerCase();
    return commands.filter(
      cmd =>
        cmd.label.toLowerCase().includes(lower) ||
        cmd.category.toLowerCase().includes(lower)
    );
  }, [commands, query]);

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        if (isOpen) {
          onClose();
        } else {
          // Parent triggers open
        }
      }
      if (!isOpen) return;

      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex(prev => (prev + 1) % (filteredCommands.length || 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex(prev => (prev - 1 + filteredCommands.length) % (filteredCommands.length || 1));
      } else if (e.key === 'Enter') {
        e.preventDefault();
        if (filteredCommands[selectedIndex]) {
          filteredCommands[selectedIndex].action();
          onClose();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose, filteredCommands, selectedIndex]);

  if (!isOpen) return null;

  return (
    <div className="commandPaletteOverlay" onClick={onClose} role="dialog" aria-modal="true" aria-label="Command Palette">
      <div className="commandPaletteModal" onClick={e => e.stopPropagation()}>
        <div className="commandPaletteHeader">
          <span className="searchIcon">🔍</span>
          <input
            autoFocus
            type="text"
            className="commandPaletteInput"
            placeholder="Type a command or search actions (e.g., 'Run', 'Diagram', 'Test', 'Repair')..."
            value={query}
            onChange={e => setQuery(e.target.value)}
          />
          <kbd className="escBadge" onClick={onClose}>ESC</kbd>
        </div>

        <div className="commandPaletteList scrollArea">
          {filteredCommands.length === 0 ? (
            <div className="commandEmpty">No commands found matching "{query}"</div>
          ) : (
            filteredCommands.map((cmd, index) => (
              <div
                key={cmd.id}
                className={`commandItem ${index === selectedIndex ? 'selected' : ''}`}
                onClick={() => {
                  cmd.action();
                  onClose();
                }}
                onMouseEnter={() => setSelectedIndex(index)}
              >
                <div className="commandItemLeft">
                  <span className="commandCategory">{cmd.category}</span>
                  <span className="commandLabel">{cmd.label}</span>
                </div>
                {cmd.shortcut && <kbd className="commandShortcut">{cmd.shortcut}</kbd>}
              </div>
            ))
          )}
        </div>

        <div className="commandPaletteFooter">
          <span>Use <b>↑</b> <b>↓</b> to navigate</span>
          <span><b>ENTER</b> to select</span>
          <span><b>ESC</b> to dismiss</span>
        </div>
      </div>
    </div>
  );
}
