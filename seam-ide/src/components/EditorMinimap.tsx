import React, { useMemo, useRef, useState, useEffect } from 'react';

export type EditorMinimapProps = {
  content: string;
  scrollTop?: number;
  scrollHeight?: number;
  clientHeight?: number;
  onScrollTo?: (scrollTop: number) => void;
};

export function EditorMinimap({
  content,
  scrollTop = 0,
  scrollHeight = 1,
  clientHeight = 1,
  onScrollTo,
}: EditorMinimapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  // Parse lines and compute miniature line widths and syntax colors
  const miniLines = useMemo(() => {
    const rawLines = content.split('\n').slice(0, 300); // capped for extreme performance
    return rawLines.map((line) => {
      const trimmed = line.trim();
      const length = Math.min(line.length, 60);
      const indent = (line.length - line.trimStart().length) * 2;
      const widthPercent = Math.max(8, Math.min(100, length * 1.8));

      // Simple heuristic syntax token tinting
      let color = 'rgba(255, 255, 255, 0.2)';
      if (trimmed.startsWith('import ') || trimmed.startsWith('export ') || trimmed.startsWith('return ') || trimmed.startsWith('const ') || trimmed.startsWith('function ')) {
        color = 'rgba(86, 156, 214, 0.65)'; // Blue keyword
      } else if (trimmed.includes('type ') || trimmed.includes('interface ')) {
        color = 'rgba(78, 201, 176, 0.65)'; // Teal type
      } else if (trimmed.includes('//') || trimmed.startsWith('/*')) {
        color = 'rgba(106, 153, 85, 0.5)'; // Green comment
      } else if (trimmed.includes('<') && trimmed.includes('>')) {
        color = 'rgba(197, 134, 192, 0.6)'; // Purple JSX
      } else if (trimmed.includes('(') || trimmed.includes('{')) {
        color = 'rgba(220, 220, 170, 0.55)'; // Yellow function/block
      }

      return { indent, widthPercent, color };
    });
  }, [content]);

  // Compute proportional viewport indicator
  const viewportRatio = scrollHeight > 0 ? Math.min(1, clientHeight / scrollHeight) : 1;
  const scrollRatio = scrollHeight > clientHeight ? Math.min(1, Math.max(0, scrollTop / (scrollHeight - clientHeight))) : 0;

  const viewportHeightPercent = Math.max(12, Math.min(100, viewportRatio * 100));
  const viewportTopPercent = scrollRatio * (100 - viewportHeightPercent);

  const handlePointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!containerRef.current || !onScrollTo) return;
    const rect = containerRef.current.getBoundingClientRect();
    const clickY = e.clientY - rect.top;
    const clickRatio = Math.max(0, Math.min(1, clickY / rect.height));
    const targetScroll = clickRatio * (scrollHeight - clientHeight);
    onScrollTo(targetScroll);
    setIsDragging(true);
  };

  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!isDragging || !containerRef.current || !onScrollTo) return;
    const rect = containerRef.current.getBoundingClientRect();
    const clickY = e.clientY - rect.top;
    const clickRatio = Math.max(0, Math.min(1, clickY / rect.height));
    const targetScroll = clickRatio * (scrollHeight - clientHeight);
    onScrollTo(targetScroll);
  };

  const handlePointerUp = () => {
    setIsDragging(false);
  };

  useEffect(() => {
    const handleGlobalUp = () => setIsDragging(false);
    window.addEventListener('pointerup', handleGlobalUp);
    return () => window.removeEventListener('pointerup', handleGlobalUp);
  }, []);

  return (
    <div
      className="editorMinimap"
      ref={containerRef}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      role="scrollbar"
      aria-label="Code minimap"
      aria-valuenow={Math.round(scrollRatio * 100)}
    >
      {/* Visual range overlay */}
      <div
        className="minimapVisibleRange"
        style={{
          top: `${viewportTopPercent}%`,
          height: `${viewportHeightPercent}%`,
        }}
      />

      {/* Render mini line representations */}
      <div className="minimapLines">
        {miniLines.map((line, idx) => (
          <div
            key={idx}
            className="minimapLine"
            style={{
              paddingLeft: `${line.indent}px`,
            }}
          >
            <span
              className="minimapLineBar"
              style={{
                width: `${line.widthPercent}%`,
                backgroundColor: line.color,
              }}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
