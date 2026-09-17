import { ReactNode, useEffect, useMemo, useRef, useState } from 'react';

export type DockArea = 'left' | 'center' | 'right' | 'bottom';
export type PanelId =
  | 'explorer'
  | 'search'
  | 'git'
  | 'agents'
  | 'tasks'
  | 'artifacts'
  | 'knowledge'
  | 'skills'
  | 'mcp'
  | 'browser'
  | 'editor'
  | 'chat'
  | 'terminal'
  | 'problems'
  | 'output'
  | 'qa'
  | 'logs';

export type PanelDefinition = {
  id: PanelId;
  title: string;
  render: () => ReactNode;
  available?: boolean;
};

type FloatingPanel = {
  id: PanelId;
  x: number;
  y: number;
  width: number;
  height: number;
  minimized?: boolean;
};

export type LayoutState = {
  leftWidth: number;
  rightWidth: number;
  bottomHeight: number;
  bottomVisible: boolean;
  collapsed: Record<'left' | 'right' | 'bottom', boolean>;
  activeTabs: Record<DockArea, PanelId>;
  areas: Record<DockArea, PanelId[]>;
  floating: FloatingPanel[];
  fullscreen: PanelId | null;
  preset: string;
};

const storageKey = 'seam.ui.layout';

const presets: Record<string, Partial<LayoutState>> = {
  DEFAULT: { leftWidth: 280, rightWidth: 420, bottomHeight: 180, bottomVisible: true, collapsed: { left: false, right: false, bottom: false } },
  CODING: { leftWidth: 260, rightWidth: 320, bottomHeight: 120, bottomVisible: false, collapsed: { left: false, right: false, bottom: true } },
  AGENT: { leftWidth: 300, rightWidth: 520, bottomHeight: 220, bottomVisible: true, collapsed: { left: false, right: false, bottom: false }, activeTabs: { left: 'agents', center: 'editor', right: 'chat', bottom: 'tasks' } },
  DEBUG: { leftWidth: 240, rightWidth: 320, bottomHeight: 260, bottomVisible: true, activeTabs: { left: 'explorer', center: 'editor', right: 'chat', bottom: 'terminal' } },
  QA: { leftWidth: 240, rightWidth: 420, bottomHeight: 240, bottomVisible: true, activeTabs: { left: 'explorer', center: 'editor', right: 'chat', bottom: 'qa' } },
  FOCUS: { leftWidth: 0, rightWidth: 0, bottomHeight: 0, bottomVisible: false, collapsed: { left: true, right: true, bottom: true } },
};

const defaultLayout: LayoutState = {
  leftWidth: 280,
  rightWidth: 420,
  bottomHeight: 180,
  bottomVisible: true,
  collapsed: { left: false, right: false, bottom: false },
  activeTabs: { left: 'explorer', center: 'editor', right: 'chat', bottom: 'logs' },
  areas: {
    left: ['explorer', 'search', 'git', 'agents', 'tasks', 'artifacts', 'knowledge', 'skills', 'mcp'],
    center: ['editor'],
    right: ['chat'],
    bottom: ['logs', 'terminal', 'problems', 'output', 'qa', 'browser'],
  },
  floating: [],
  fullscreen: null,
  preset: 'DEFAULT',
};

function loadLayout(): LayoutState {
  try {
    const saved = window.localStorage.getItem(storageKey);
    if (!saved) return defaultLayout;
    return { ...defaultLayout, ...JSON.parse(saved) };
  } catch {
    return defaultLayout;
  }
}

export function FlexibleLayout({ panels, topbar }: { panels: PanelDefinition[]; topbar: ReactNode }) {
  const [layout, setLayout] = useState<LayoutState>(() => loadLayout());
  const panelMap = useMemo(() => new Map(panels.map(panel => [panel.id, panel])), [panels]);
  const dragPanel = useRef<PanelId | null>(null);

  useEffect(() => {
    window.localStorage.setItem(storageKey, JSON.stringify(layout));
  }, [layout]);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setLayout(current => ({ ...current, fullscreen: null }));
      if (event.ctrlKey && event.shiftKey && event.key.toLowerCase() === 'e') toggleDock('left');
      if (event.ctrlKey && event.shiftKey && event.key.toLowerCase() === 'j') setActive('right', 'chat');
      if (event.ctrlKey && event.shiftKey && event.key.toLowerCase() === 't') setActive('bottom', 'terminal');
      if (event.ctrlKey && event.shiftKey && event.key.toLowerCase() === 'g') setActive('left', 'git');
      if (event.ctrlKey && event.shiftKey && event.key.toLowerCase() === 'a') setActive('left', 'agents');
      if (event.ctrlKey && event.shiftKey && event.key.toLowerCase() === 'b') setActive('bottom', 'browser');
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  const updateLayout = (patch: Partial<LayoutState>) => setLayout(current => ({ ...current, ...patch }));
  const setActive = (area: DockArea, id: PanelId) => setLayout(current => ({ ...current, activeTabs: { ...current.activeTabs, [area]: id } }));
  const toggleDock = (dock: 'left' | 'right' | 'bottom') => setLayout(current => ({ ...current, collapsed: { ...current.collapsed, [dock]: !current.collapsed[dock] } }));

  const applyPreset = (name: string) => {
    setLayout(current => ({ ...current, ...presets[name], preset: name }));
  };

  const resize = (kind: 'left' | 'right' | 'bottom', startEvent: React.PointerEvent) => {
    startEvent.preventDefault();
    const startX = startEvent.clientX;
    const startY = startEvent.clientY;
    const start = { ...layout };
    const onMove = (event: PointerEvent) => {
      requestAnimationFrame(() => {
        if (kind === 'left') updateLayout({ leftWidth: Math.max(190, Math.min(520, start.leftWidth + event.clientX - startX)) });
        if (kind === 'right') updateLayout({ rightWidth: Math.max(300, Math.min(680, start.rightWidth - (event.clientX - startX))) });
        if (kind === 'bottom') updateLayout({ bottomHeight: Math.max(110, Math.min(420, start.bottomHeight - (event.clientY - startY))) });
      });
    };
    const onUp = () => {
      window.removeEventListener('pointermove', onMove);
      window.removeEventListener('pointerup', onUp);
    };
    window.addEventListener('pointermove', onMove);
    window.addEventListener('pointerup', onUp);
  };

  const floatPanel = (id: PanelId) => {
    setLayout(current => ({
      ...current,
      floating: current.floating.some(panel => panel.id === id)
        ? current.floating
        : [...current.floating, { id, x: 160, y: 120, width: 460, height: 420 }],
    }));
  };

  const dockFloating = (id: PanelId, area: DockArea = 'right') => {
    setLayout(current => ({
      ...current,
      floating: current.floating.filter(panel => panel.id !== id),
      areas: { ...current.areas, [area]: Array.from(new Set([...current.areas[area], id])) },
      activeTabs: { ...current.activeTabs, [area]: id },
    }));
  };

  const dropToArea = (area: DockArea) => {
    const id = dragPanel.current;
    dragPanel.current = null;
    if (!id) return;
    setLayout(current => ({
      ...current,
      floating: current.floating.filter(panel => panel.id !== id),
      areas: Object.fromEntries(Object.entries(current.areas).map(([key, ids]) => [key, key === area ? Array.from(new Set([...ids, id])) : ids.filter(item => item !== id)])) as LayoutState['areas'],
      activeTabs: { ...current.activeTabs, [area]: id },
    }));
  };

  const renderPanel = (id: PanelId) => {
    const panel = panelMap.get(id);
    if (!panel) return <UnavailablePanel title={id} detail="Panel is not registered." />;
    if (panel.available === false) return <UnavailablePanel title={panel.title} detail="Backend support is not implemented yet." />;
    return panel.render();
  };

  const fullscreen = layout.fullscreen ? panelMap.get(layout.fullscreen) : null;

  return (
    <div className="ideShell">
      <header className="globalBar">
        {topbar}
        <select aria-label="Layout preset" value={layout.preset} onChange={event => applyPreset(event.target.value)}>
          {Object.keys(presets).map(name => <option key={name}>{name}</option>)}
        </select>
        <button onClick={() => setLayout(defaultLayout)}>Reset Layout</button>
        <button onClick={() => toggleDock('left')}>Explorer</button>
        <button onClick={() => toggleDock('right')}>Chat</button>
        <button onClick={() => toggleDock('bottom')}>Bottom</button>
      </header>

      <div className="layoutGrid" style={{
        gridTemplateColumns: `${layout.collapsed.left ? 0 : layout.leftWidth}px 6px minmax(360px, 1fr) 6px ${layout.collapsed.right ? 0 : layout.rightWidth}px`,
        gridTemplateRows: `minmax(0, 1fr) 6px ${layout.collapsed.bottom || !layout.bottomVisible ? 0 : layout.bottomHeight}px`,
      }}>
        <DockPane area="left" layout={layout} panels={panelMap} onActive={setActive} onFloat={floatPanel} onFullscreen={id => updateLayout({ fullscreen: id })} onDragStart={id => { dragPanel.current = id; }} onDropArea={dropToArea}>
          {renderPanel(layout.activeTabs.left)}
        </DockPane>
        <ResizeHandle hidden={layout.collapsed.left} onPointerDown={event => resize('left', event)} onDoubleClick={() => updateLayout({ leftWidth: defaultLayout.leftWidth })} />
        <DockPane area="center" layout={layout} panels={panelMap} onActive={setActive} onFloat={floatPanel} onFullscreen={id => updateLayout({ fullscreen: id })} onDragStart={id => { dragPanel.current = id; }} onDropArea={dropToArea}>
          {renderPanel(layout.activeTabs.center)}
        </DockPane>
        <ResizeHandle hidden={layout.collapsed.right} onPointerDown={event => resize('right', event)} onDoubleClick={() => updateLayout({ rightWidth: defaultLayout.rightWidth })} />
        <DockPane area="right" layout={layout} panels={panelMap} onActive={setActive} onFloat={floatPanel} onFullscreen={id => updateLayout({ fullscreen: id })} onDragStart={id => { dragPanel.current = id; }} onDropArea={dropToArea}>
          {renderPanel(layout.activeTabs.right)}
        </DockPane>
        <div />
        <div />
        <ResizeHandle horizontal hidden={layout.collapsed.bottom || !layout.bottomVisible} onPointerDown={event => resize('bottom', event)} onDoubleClick={() => updateLayout({ bottomHeight: defaultLayout.bottomHeight })} />
        <div />
        <div />
        <DockPane area="bottom" layout={layout} panels={panelMap} onActive={setActive} onFloat={floatPanel} onFullscreen={id => updateLayout({ fullscreen: id })} onDragStart={id => { dragPanel.current = id; }} onDropArea={dropToArea}>
          {renderPanel(layout.activeTabs.bottom)}
        </DockPane>
        <div />
      </div>

      {layout.floating.map(float => (
        <FloatingWindow
          key={float.id}
          floating={float}
          title={panelMap.get(float.id)?.title || float.id}
          onDock={() => dockFloating(float.id)}
          onClose={() => setLayout(current => ({ ...current, floating: current.floating.filter(panel => panel.id !== float.id) }))}
          onFullscreen={() => updateLayout({ fullscreen: float.id })}
          onChange={next => setLayout(current => ({ ...current, floating: current.floating.map(panel => panel.id === float.id ? next : panel) }))}
        >
          {renderPanel(float.id)}
        </FloatingWindow>
      ))}

      {fullscreen && layout.fullscreen && (
        <div className="fullscreenPanel">
          <PanelTitle title={fullscreen.title} onFloat={() => floatPanel(layout.fullscreen!)} onFullscreen={() => updateLayout({ fullscreen: null })} />
          <div className="fullscreenBody">{renderPanel(layout.fullscreen)}</div>
        </div>
      )}
    </div>
  );
}

function DockPane(props: {
  area: DockArea;
  layout: LayoutState;
  panels: Map<PanelId, PanelDefinition>;
  children: ReactNode;
  onActive: (area: DockArea, id: PanelId) => void;
  onFloat: (id: PanelId) => void;
  onFullscreen: (id: PanelId) => void;
  onDragStart: (id: PanelId) => void;
  onDropArea: (area: DockArea) => void;
}) {
  const ids = props.layout.areas[props.area];
  const active = props.layout.activeTabs[props.area];
  return (
    <section className={`dockPane dock-${props.area}`} onDragOver={event => event.preventDefault()} onDrop={() => props.onDropArea(props.area)}>
      <div className="panelTabs">
        {ids.map(id => {
          const panel = props.panels.get(id);
          return (
            <button key={id} draggable onDragStart={() => props.onDragStart(id)} className={id === active ? 'active' : ''} onClick={() => props.onActive(props.area, id)}>
              {panel?.title || id}
            </button>
          );
        })}
        <button className="tabIcon" onClick={() => props.onFloat(active)}>Float</button>
        <button className="tabIcon" onClick={() => props.onFullscreen(active)}>Fullscreen</button>
      </div>
      <div className="dockBody" aria-label={`${props.area} panel content`}>{props.children}</div>
    </section>
  );
}

function PanelTitle({ title, onFloat, onFullscreen }: { title: string; onFloat: () => void; onFullscreen: () => void }) {
  return (
    <div className="floatingTitle">
      <strong>{title}</strong>
      <div className="buttonRow">
        <button onClick={onFloat}>Float</button>
        <button onClick={onFullscreen}>Restore</button>
      </div>
    </div>
  );
}

function FloatingWindow(props: { floating: FloatingPanel; title: string; children: ReactNode; onDock: () => void; onClose: () => void; onFullscreen: () => void; onChange: (next: FloatingPanel) => void }) {
  const start = useRef<{ x: number; y: number; panel: FloatingPanel } | null>(null);
  const move = (event: React.PointerEvent) => {
    start.current = { x: event.clientX, y: event.clientY, panel: props.floating };
    const onMove = (nextEvent: PointerEvent) => {
      if (!start.current) return;
      props.onChange({ ...start.current.panel, x: start.current.panel.x + nextEvent.clientX - start.current.x, y: start.current.panel.y + nextEvent.clientY - start.current.y });
    };
    const onUp = () => {
      start.current = null;
      window.removeEventListener('pointermove', onMove);
      window.removeEventListener('pointerup', onUp);
    };
    window.addEventListener('pointermove', onMove);
    window.addEventListener('pointerup', onUp);
  };
  return (
    <aside className="floatingWindow" style={{ left: props.floating.x, top: props.floating.y, width: props.floating.width, height: props.floating.height }}>
      <div className="floatingTitle" onPointerDown={move}>
        <strong>{props.title}</strong>
        <div className="buttonRow">
          <button onClick={props.onDock}>Dock</button>
          <button onClick={props.onFullscreen}>Fullscreen</button>
          <button onClick={props.onClose}>Close</button>
        </div>
      </div>
      <div className="floatingBody" aria-label={`${props.title} floating panel content`}>{props.children}</div>
    </aside>
  );
}

function ResizeHandle(props: { horizontal?: boolean; hidden?: boolean; onPointerDown: (event: React.PointerEvent) => void; onDoubleClick: () => void }) {
  return <div className={`resizeHandle ${props.horizontal ? 'horizontal' : ''} ${props.hidden ? 'hidden' : ''}`} onPointerDown={props.onPointerDown} onDoubleClick={props.onDoubleClick} />;
}

export function UnavailablePanel({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="unavailablePanel">
      <strong>{title}</strong>
      <span>{detail}</span>
    </div>
  );
}
