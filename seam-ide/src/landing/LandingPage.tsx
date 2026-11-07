import React, { useState, useEffect, useRef, useCallback } from 'react';
import './landing.css';

/* ───────────────────── Types ───────────────────── */

type LandingPageProps = {
  onLaunch: () => void;
  onWorkspace: () => void;
  onArchitecture?: () => void;
  onLogin?: () => void;
};

/* ───────────────────── Constants ───────────────────── */

const WORKFLOW_STEPS = [
  { num: '01', label: 'REQUIREMENTS', icon: '◈' },
  { num: '02', label: 'ANALYSIS', icon: '◇' },
  { num: '03', label: 'PLANNING', icon: '△' },
  { num: '04', label: 'DESIGN', icon: '▢' },
  { num: '05', label: 'CODING', icon: '⟨⟩' },
  { num: '06', label: 'QA', icon: '✓' },
  { num: '07', label: 'REPAIR', icon: '⟳' },
  { num: '08', label: 'DELIVERY', icon: '◉' },
] as const;

const AGENTS = [
  {
    name: 'Analysis Agent',
    role: 'Requirements Engineering',
    desc: 'Transforms raw requirements into structured engineering knowledge — constraints, dependencies, domain context, and traceability matrices.',
    input: 'Natural-language requirements, domain context',
    output: 'Structured scope, dependency graph, traceability',
    color: '#58A6FF',
  },
  {
    name: 'Planning Agent',
    role: 'Architecture & Design',
    desc: 'Produces system architecture, implementation strategy, task decomposition, and 10 canonical engineering diagrams.',
    input: 'Analyzed requirements, technology preferences',
    output: 'Architecture, diagrams, ordered task plan',
    color: '#BC8CFF',
  },
  {
    name: 'Supervisor Agent',
    role: 'Workflow Orchestration',
    desc: 'Coordinates the entire lifecycle — maintains workflow state, dependencies, priorities, previous outputs, QA feedback, and rework routing.',
    input: 'Execution plan, agent outputs, QA signals',
    output: 'Agent routing, rework decisions, state sync',
    color: '#CCA700',
  },
  {
    name: 'Coding Agent',
    role: 'Code Generation & Modification',
    desc: 'Creates and modifies real application code, project structure, configuration files, and Git commits through sandboxed tool execution.',
    input: 'Task assignments, architecture specs',
    output: 'Generated code, file structure, commits',
    color: '#73C991',
  },
  {
    name: 'QA Agent',
    role: 'Verification & Validation',
    desc: 'Validates through unit tests, API contracts, runtime checks, E2E workflows, security scans, accessibility audits, and type checking.',
    input: 'Generated code, contracts, test specifications',
    output: 'Findings, evidence, defect locations, repair requests',
    color: '#F85149',
  },
  {
    name: 'Delivery Agent',
    role: 'Release Readiness & Packaging',
    desc: 'Checks release readiness gates, validates deployment artifacts, Docker configurations, and prepares software for delivery.',
    input: 'Verified code, QA results, deployment specs',
    output: 'Delivery report, Docker validation, release gate',
    color: '#569CD6',
  },
] as const;

const REPAIR_STEPS = [
  { label: 'DEFECT DETECTED', detail: 'QA Agent identifies failing verification', status: 'error' },
  { label: 'LOCALIZE', detail: 'Isolate affected file, function, line', status: 'active' },
  { label: 'ROOT CAUSE', detail: 'Analyze evidence chain and dependencies', status: 'active' },
  { label: 'REPAIR PLAN', detail: 'Generate targeted fix strategy', status: 'active' },
  { label: 'PATCH', detail: 'Apply code modifications via sandboxed tools', status: 'active' },
  { label: 'TARGETED VERIFICATION', detail: 'Re-run affected tests only', status: 'success' },
  { label: 'REGRESSION CHECK', detail: 'Full suite to confirm no side effects', status: 'success' },
  { label: 'RESOLVED', detail: 'Defect closed, evidence archived', status: 'resolved' },
] as const;

const TESTING_LAYERS = [
  'Unit', 'Integration', 'API', 'Contract', 'E2E',
  'Runtime', 'Security', 'Accessibility', 'Performance',
  'Build', 'Typecheck', 'Lint',
] as const;

const INTELLIGENCE_CAPABILITIES = [
  { name: 'Design Intelligence', desc: '10 canonical engineering diagrams generated from architecture', icon: '◇' },
  { name: 'Contract Intelligence', desc: 'Frontend ↔ API ↔ Database schema synchronization & drift detection', icon: '⇌' },
  { name: 'Test Intelligence', desc: '17 testing categories across unit, integration, contract, E2E, and security', icon: '✓' },
  { name: 'Runtime Intelligence', desc: 'Process lifecycle management, health monitoring, and resource tracking', icon: '⚡' },
  { name: 'Delivery Intelligence', desc: 'Release readiness gates, Docker validation, and deployment artifacts', icon: '◉' },
  { name: 'Evaluation Intelligence', desc: 'Ablation studies, controlled comparisons, and reproducible measurement', icon: '≡' },
  { name: 'GitHub Intelligence', desc: 'Repository operations, branch management, commit tracking, and PR workflows', icon: '⎇' },
  { name: 'Diagram Intelligence', desc: 'System, sequence, class, ERD, component, deployment, and data flow diagrams', icon: '▤' },
] as const;

const INTEGRATIONS = [
  { name: 'GitHub', status: 'AVAILABLE', category: 'Platform' },
  { name: 'Figma', status: 'AVAILABLE', category: 'Design' },
  { name: 'Docker', status: 'CONNECTED', category: 'Infrastructure' },
  { name: 'Docker Model Runner', status: 'CONNECTED', category: 'AI Inference' },
  { name: 'Ollama', status: 'AVAILABLE', category: 'AI Inference' },
  { name: 'n8n', status: 'AVAILABLE', category: 'Automation' },
  { name: 'ChromaDB', status: 'CONNECTED', category: 'RAG' },
  { name: 'FastAPI', status: 'CONNECTED', category: 'Backend' },
  { name: 'React', status: 'CONNECTED', category: 'Frontend' },
  { name: 'PostgreSQL', status: 'AVAILABLE', category: 'Database' },
  { name: 'Redis', status: 'AVAILABLE', category: 'Cache' },
] as const;

const SECURITY_ITEMS = [
  'Permission Engine',
  'Tool Registry (39 Registered)',
  'Approval Gates',
  'Secret Scanning',
  'Path Safety & Confinement',
  'Git Safety',
  'Sandboxed Execution',
  'Traceability & Audit Log',
  'AST Validation',
] as const;

const CREDIBILITY = [
  { label: '6', detail: 'Cognitive Agents' },
  { label: '39', detail: 'Registered Native Tools' },
  { label: '17', detail: 'Testing Categories' },
  { label: '10', detail: 'Canonical Diagrams' },
] as const;

/* ───────────────────── Intersection Observer Hook ───────────────────── */

function useReveal() {
  const ref = useRef<HTMLElement>(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setVisible(true); obs.disconnect(); } },
      { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, []);
  return { ref, visible };
}

function Reveal({ children, className = '', delay = 0 }: { children: React.ReactNode; className?: string; delay?: number }) {
  const { ref, visible } = useReveal();
  return (
    <div
      ref={ref as React.RefObject<HTMLDivElement>}
      className={`lp-reveal ${visible ? 'lp-revealed' : ''} ${className}`}
      style={{ transitionDelay: `${delay}ms` }}
    >
      {children}
    </div>
  );
}

/* ───────────────────── Navigation ───────────────────── */

function Navbar({ onLaunch, onWorkspace, onLogin }: { onLaunch: () => void; onWorkspace: () => void; onLogin?: () => void }) {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const scrollEl = document.querySelector('.lp-root');
    if (!scrollEl) return;
    const handler = () => setScrolled(scrollEl.scrollTop > 48);
    scrollEl.addEventListener('scroll', handler, { passive: true });
    return () => scrollEl.removeEventListener('scroll', handler);
  }, []);

  const scrollTo = useCallback((id: string) => {
    setMobileOpen(false);
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, []);

  return (
    <nav className={`lp-nav ${scrolled ? 'lp-nav--scrolled' : ''}`} aria-label="Main navigation">
      <div className="lp-nav-inner">
        <button className="lp-nav-brand" onClick={() => scrollTo('lp-hero')} aria-label="SEAM Home">
          <span className="lp-logo-icon" aria-hidden="true">⚡</span>
          <span className="lp-logo-text">SEAM</span>
        </button>

        <div className={`lp-nav-links ${mobileOpen ? 'lp-nav-links--open' : ''}`}>
          <button onClick={() => scrollTo('lp-workflow')}>Product</button>
          <button onClick={() => scrollTo('lp-agents')}>Architecture</button>
          <button onClick={() => scrollTo('lp-intelligence')}>Capabilities</button>
          <button onClick={() => scrollTo('lp-research')}>Research</button>
          <button onClick={() => scrollTo('lp-integrations')}>Integrations</button>
        </div>

        <div className="lp-nav-actions">
          <button className="lp-nav-link-btn" onClick={onLogin || onLaunch}>Sign In</button>
          <button className="lp-nav-link-btn" onClick={onWorkspace}>Open Workspace</button>
          <button className="lp-btn lp-btn--primary lp-btn--sm" onClick={onLaunch}>Launch SEAM</button>
        </div>

        <button
          className="lp-nav-hamburger"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label="Toggle navigation menu"
          aria-expanded={mobileOpen}
        >
          <span /><span /><span />
        </button>
      </div>
    </nav>
  );
}

/* ───────────────────── Hero ───────────────────── */

function HeroSection({ onLaunch, onArchitecture }: { onLaunch: () => void; onArchitecture?: () => void }) {
  return (
    <section className="lp-hero" id="lp-hero">
      <div className="lp-hero-bg" aria-hidden="true">
        <div className="lp-hero-grid" />
        <div className="lp-hero-glow" />
      </div>
      <div className="lp-hero-content">
        <Reveal>
          <span className="lp-eyebrow">AUTONOMOUS SOFTWARE ENGINEERING</span>
        </Reveal>
        <Reveal delay={80}>
          <h1 className="lp-hero-title">
            TURN REQUIREMENTS<br />
            INTO ENGINEERED SOFTWARE.
          </h1>
        </Reveal>
        <Reveal delay={160}>
          <p className="lp-hero-sub">
            An autonomous multi-agent engineering framework that analyzes requirements,
            plans architecture, writes code, validates systems, repairs defects, and
            prepares software for delivery.
          </p>
        </Reveal>
        <Reveal delay={240}>
          <div className="lp-hero-actions">
            <button className="lp-btn lp-btn--primary lp-btn--lg" onClick={onLaunch}>
              Launch SEAM
              <span className="lp-btn-arrow" aria-hidden="true">→</span>
            </button>
            <button className="lp-btn lp-btn--ghost lp-btn--lg" onClick={() => onArchitecture?.() || document.getElementById('lp-agents')?.scrollIntoView({ behavior: 'smooth' })}>
              Explore Architecture
            </button>
          </div>
        </Reveal>
        <Reveal delay={320}>
          <div className="lp-hero-trust">
            <span>Multi-Agent</span>
            <span className="lp-dot" aria-hidden="true" />
            <span>Domain-Aware</span>
            <span className="lp-dot" aria-hidden="true" />
            <span>Testable</span>
            <span className="lp-dot" aria-hidden="true" />
            <span>Traceable</span>
          </div>
        </Reveal>
      </div>
    </section>
  );
}

/* ───────────────────── Product Preview ───────────────────── */

function ProductPreview() {
  return (
    <section className="lp-section lp-preview-section">
      <Reveal>
        <div className="lp-preview-window">
          <div className="lp-preview-chrome">
            <div className="lp-preview-dots" aria-hidden="true"><span /><span /><span /></div>
            <span className="lp-preview-title">SEAM — Autonomous Engineering Workspace</span>
          </div>
          <div className="lp-preview-body">
            {/* Activity Bar */}
            <div className="lp-preview-activity" aria-hidden="true">
              <div className="lp-pa-icon active" /><div className="lp-pa-icon" /><div className="lp-pa-icon" /><div className="lp-pa-icon" /><div className="lp-pa-icon" />
            </div>
            {/* Explorer */}
            <div className="lp-preview-explorer">
              <div className="lp-pe-header">EXPLORER</div>
              <div className="lp-pe-section">▾ PROJECT FILES</div>
              <div className="lp-pe-item">📁 src</div>
              <div className="lp-pe-item lp-pe-active">⚛ App.tsx</div>
              <div className="lp-pe-item">&nbsp;&nbsp;📁 agents</div>
              <div className="lp-pe-item">&nbsp;&nbsp;📁 api</div>
              <div className="lp-pe-item">&nbsp;&nbsp;📁 components</div>
              <div className="lp-pe-section">▸ OUTLINE</div>
              <div className="lp-pe-section">▸ TIMELINE</div>
            </div>
            {/* Editor */}
            <div className="lp-preview-editor">
              <div className="lp-pe-tabs">
                <span className="lp-pe-tab active">App.tsx</span>
                <span className="lp-pe-tab">index.css</span>
              </div>
              <div className="lp-pe-code">
                <div className="lp-code-line"><span className="lp-ln">1</span><span className="lp-kw">import</span> {'{'} <span className="lp-fn">useEffect</span> {'}'} <span className="lp-kw">from</span> <span className="lp-str">'react'</span>;</div>
                <div className="lp-code-line"><span className="lp-ln">2</span><span className="lp-kw">import</span> {'{'} <span className="lp-fn">SEAMEngine</span> {'}'} <span className="lp-kw">from</span> <span className="lp-str">'./engine'</span>;</div>
                <div className="lp-code-line"><span className="lp-ln">3</span></div>
                <div className="lp-code-line"><span className="lp-ln">4</span><span className="lp-kw">export function</span> <span className="lp-fn">App</span>() {'{'}</div>
                <div className="lp-code-line"><span className="lp-ln">5</span>  <span className="lp-kw">const</span> engine = <span className="lp-fn">useEngine</span>();</div>
                <div className="lp-code-line"><span className="lp-ln">6</span>  <span className="lp-cmt">// Autonomous workflow</span></div>
                <div className="lp-code-line"><span className="lp-ln">7</span>  <span className="lp-kw">return</span> {'<'}<span className="lp-fn">Workspace</span> /{'>'}</div>
                <div className="lp-code-line"><span className="lp-ln">8</span>{'}'}</div>
              </div>
            </div>
            {/* Agent Panel */}
            <div className="lp-preview-agent">
              <div className="lp-pa-header">
                <span>SEAM AGENT</span>
                <span className="lp-pa-live">LIVE</span>
              </div>
              <div className="lp-pa-card">
                <div className="lp-pa-row"><span className="lp-pa-label">Agent</span><span>Supervisor</span></div>
                <div className="lp-pa-row"><span className="lp-pa-label">State</span><span className="lp-pa-status">ACTIVE</span></div>
                <div className="lp-pa-row"><span className="lp-pa-label">Tasks</span><span>3 / 6</span></div>
                <div className="lp-pa-row"><span className="lp-pa-label">QA</span><span className="lp-status-pass">PASS</span></div>
              </div>
              <div className="lp-pa-card">
                <div className="lp-pa-row"><span className="lp-pa-label">RAG</span><span>loaded</span></div>
                <div className="lp-pa-row"><span className="lp-pa-label">Tools</span><span>39 registered</span></div>
              </div>
            </div>
          </div>
          {/* Terminal strip */}
          <div className="lp-preview-terminal">
            <div className="lp-pt-tabs">
              <span>PROBLEMS</span><span>OUTPUT</span><span className="active">TERMINAL</span><span>PORTS</span>
            </div>
            <div className="lp-pt-content">
              <span className="lp-pt-prompt">→</span> seam-workspace git:(main) <span className="lp-pt-cmd">seam run --autonomous</span>
            </div>
          </div>
          {/* Status Bar */}
          <div className="lp-preview-statusbar">
            <span className="lp-ps-remote">{'><'} SEAM Local</span>
            <span>⎇ main</span>
            <span>⊘ 0 ⚠ 0</span>
            <span className="lp-ps-right">Ln 5, Col 24 · Spaces: 2 · UTF-8 · TypeScript React</span>
          </div>
        </div>
      </Reveal>
    </section>
  );
}

/* ───────────────────── Workflow Strip ───────────────────── */

function WorkflowSection() {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => setActiveStep(prev => (prev + 1) % WORKFLOW_STEPS.length), 2400);
    return () => clearInterval(timer);
  }, []);

  return (
    <section className="lp-section lp-workflow" id="lp-workflow">
      <Reveal>
        <div className="lp-section-header">
          <span className="lp-eyebrow">ENGINEERING LIFECYCLE</span>
          <h2 className="lp-h2">From intent to validated software.</h2>
          <p className="lp-section-sub">Eight stages of autonomous engineering, executed as one coordinated system.</p>
        </div>
      </Reveal>
      <Reveal delay={120}>
        <div className="lp-workflow-strip" role="list" aria-label="SEAM engineering workflow stages">
          {WORKFLOW_STEPS.map((step, i) => (
            <React.Fragment key={step.label}>
              {i > 0 && <div className={`lp-wf-connector ${i <= activeStep ? 'lp-wf-active' : ''}`} aria-hidden="true" />}
              <div
                className={`lp-wf-step ${i === activeStep ? 'lp-wf-current' : ''} ${i < activeStep ? 'lp-wf-done' : ''}`}
                role="listitem"
                aria-current={i === activeStep ? 'step' : undefined}
              >
                <span className="lp-wf-num">{step.num}</span>
                <span className="lp-wf-icon" aria-hidden="true">{step.icon}</span>
                <span className="lp-wf-label">{step.label}</span>
              </div>
            </React.Fragment>
          ))}
        </div>
      </Reveal>
    </section>
  );
}

/* ───────────────────── How SEAM Works ───────────────────── */

function HowItWorksSection() {
  const stages = [
    { num: '01', title: 'ANALYZE', desc: 'Understand requirements, constraints, dependencies and domain context.' },
    { num: '02', title: 'PLAN', desc: 'Produce architecture, implementation strategy and execution plan.' },
    { num: '03', title: 'BUILD', desc: 'Generate and modify real application code through sandboxed tool execution.' },
    { num: '04', title: 'TEST', desc: 'Validate through tests, contracts, runtime checks and E2E workflows.' },
    { num: '05', title: 'REPAIR', desc: 'Detect defects, localize causes, apply targeted repairs, and re-run verification.' },
    { num: '06', title: 'DELIVER', desc: 'Package validated artifacts and evaluate release readiness.' },
  ];

  return (
    <section className="lp-section" id="lp-how">
      <Reveal>
        <div className="lp-section-header">
          <span className="lp-eyebrow">HOW SEAM WORKS</span>
          <h2 className="lp-h2">Six stages of autonomous engineering.</h2>
        </div>
      </Reveal>
      <div className="lp-stages-grid">
        {stages.map((stage, i) => (
          <Reveal key={stage.num} delay={i * 80}>
            <div className="lp-stage-card">
              <div className="lp-stage-num">{stage.num}</div>
              <h3 className="lp-stage-title">{stage.title}</h3>
              <p className="lp-stage-desc">{stage.desc}</p>
              {i < stages.length - 1 && <div className="lp-stage-connector" aria-hidden="true" />}
            </div>
          </Reveal>
        ))}
      </div>
    </section>
  );
}

/* ───────────────────── Six Agents ───────────────────── */

function AgentsSection() {
  const [hovered, setHovered] = useState<number | null>(null);

  return (
    <section className="lp-section lp-agents-section" id="lp-agents">
      <Reveal>
        <div className="lp-section-header">
          <span className="lp-eyebrow">MULTI-AGENT ARCHITECTURE</span>
          <h2 className="lp-h2">Six agents. One engineering system.</h2>
          <p className="lp-section-sub">Each agent is a specialized cognitive worker. Together they form a coordinated autonomous engineering pipeline.</p>
        </div>
      </Reveal>
      <div className="lp-agents-grid">
        {AGENTS.map((agent, i) => (
          <Reveal key={agent.name} delay={i * 60}>
            <article
              className={`lp-agent-card ${hovered === i ? 'lp-agent-hovered' : ''}`}
              onMouseEnter={() => setHovered(i)}
              onMouseLeave={() => setHovered(null)}
              style={{ '--agent-color': agent.color } as React.CSSProperties}
            >
              <div className="lp-agent-indicator" aria-hidden="true" />
              <div className="lp-agent-header">
                <h3 className="lp-agent-name">{agent.name}</h3>
                <span className="lp-agent-role">{agent.role}</span>
              </div>
              <p className="lp-agent-desc">{agent.desc}</p>
              <div className="lp-agent-io">
                <div className="lp-agent-io-row">
                  <span className="lp-agent-io-label">INPUT</span>
                  <span>{agent.input}</span>
                </div>
                <div className="lp-agent-io-row">
                  <span className="lp-agent-io-label">OUTPUT</span>
                  <span>{agent.output}</span>
                </div>
              </div>
            </article>
          </Reveal>
        ))}
      </div>
    </section>
  );
}

/* ───────────────────── Supervisor ───────────────────── */

function SupervisorSection() {
  return (
    <section className="lp-section lp-supervisor-section">
      <Reveal>
        <div className="lp-section-header">
          <span className="lp-eyebrow">ORCHESTRATION LAYER</span>
          <h2 className="lp-h2">One system coordinating the entire lifecycle.</h2>
          <p className="lp-section-sub">
            The Supervisor maintains workflow state, dependencies, priorities, previous outputs, QA feedback and rework routing.
          </p>
        </div>
      </Reveal>
      <Reveal delay={120}>
        <div className="lp-supervisor-diagram" role="img" aria-label="Supervisor orchestration diagram">
          <div className="lp-sv-top-row">
            <div className="lp-sv-node">Requirement</div>
            <div className="lp-sv-arrow" aria-hidden="true" />
            <div className="lp-sv-node">Analysis</div>
            <div className="lp-sv-arrow" aria-hidden="true" />
            <div className="lp-sv-node">Planning</div>
          </div>
          <div className="lp-sv-center-arrow" aria-hidden="true" />
          <div className="lp-sv-core">
            <div className="lp-sv-supervisor-node">
              <span className="lp-sv-label">SUPERVISOR</span>
              <span className="lp-sv-sublabel">Workflow State · Dependencies · Rework</span>
            </div>
          </div>
          <div className="lp-sv-fan" aria-hidden="true">
            <div className="lp-sv-fan-line" /><div className="lp-sv-fan-line" /><div className="lp-sv-fan-line" />
          </div>
          <div className="lp-sv-bottom-row">
            <div className="lp-sv-node lp-sv-coding">Coding</div>
            <div className="lp-sv-node lp-sv-qa">QA</div>
            <div className="lp-sv-node lp-sv-repair">Repair</div>
          </div>
          <div className="lp-sv-center-arrow" aria-hidden="true" />
          <div className="lp-sv-final-row">
            <div className="lp-sv-node">Verification</div>
            <div className="lp-sv-arrow" aria-hidden="true" />
            <div className="lp-sv-node lp-sv-delivery">Delivery</div>
          </div>
        </div>
      </Reveal>
    </section>
  );
}

/* ───────────────────── Domain-Aware Intelligence ───────────────────── */

function DomainIntelligenceSection() {
  const sources = [
    'Official documentation',
    'Engineering knowledge',
    'Validated project context',
    'Academic literature',
    'Domain-specific patterns',
  ];

  return (
    <section className="lp-section" id="lp-rag">
      <Reveal>
        <div className="lp-section-header">
          <span className="lp-eyebrow">DOMAIN-AWARE RAG</span>
          <h2 className="lp-h2">Engineering context, not generic generation.</h2>
          <p className="lp-section-sub">
            Domain adaptation is achieved through validated retrieval and in-context orchestration — not model retraining.
          </p>
        </div>
      </Reveal>
      <Reveal delay={100}>
        <div className="lp-rag-pipeline">
          <div className="lp-rag-column">
            <h4 className="lp-rag-heading">Knowledge Sources</h4>
            {sources.map(s => (
              <div className="lp-rag-source" key={s}>{s}</div>
            ))}
          </div>
          <div className="lp-rag-flow" aria-hidden="true">
            <div className="lp-rag-flow-line" />
            <span>Validation</span>
            <div className="lp-rag-flow-line" />
            <span className="lp-rag-tech">ChromaDB + FastEmbed</span>
            <div className="lp-rag-flow-line" />
            <span>Domain Retrieval</span>
            <div className="lp-rag-flow-line" />
          </div>
          <div className="lp-rag-column">
            <h4 className="lp-rag-heading">Agent Context</h4>
            <div className="lp-rag-output">Grounded engineering decisions</div>
            <div className="lp-rag-output">Domain-specific code generation</div>
            <div className="lp-rag-output">Contextual test strategies</div>
            <div className="lp-rag-output">Architecture recommendations</div>
          </div>
        </div>
      </Reveal>
    </section>
  );
}

/* ───────────────────── Autonomous Repair ───────────────────── */

function AutonomousRepairSection() {
  return (
    <section className="lp-section lp-repair-section" id="lp-repair">
      <Reveal>
        <div className="lp-section-header">
          <span className="lp-eyebrow">AUTONOMOUS REPAIR ENGINE</span>
          <h2 className="lp-h2">When software fails, SEAM keeps engineering.</h2>
          <p className="lp-section-sub">
            Defects are detected, localized, repaired, and re-verified autonomously — without human intervention.
          </p>
        </div>
      </Reveal>
      <Reveal delay={100}>
        <div className="lp-repair-timeline" role="list" aria-label="Repair pipeline">
          {REPAIR_STEPS.map((step, i) => (
            <div className={`lp-repair-step lp-repair-${step.status}`} key={step.label} role="listitem">
              <div className="lp-repair-marker" aria-hidden="true">
                <div className="lp-repair-dot" />
                {i < REPAIR_STEPS.length - 1 && <div className="lp-repair-line" />}
              </div>
              <div className="lp-repair-content">
                <h4 className="lp-repair-label">{step.label}</h4>
                <p className="lp-repair-detail">{step.detail}</p>
              </div>
            </div>
          ))}
        </div>
      </Reveal>
    </section>
  );
}

/* ───────────────────── Engineering Intelligence ───────────────────── */

function EngineeringIntelligenceSection() {
  return (
    <section className="lp-section" id="lp-intelligence">
      <Reveal>
        <div className="lp-section-header">
          <span className="lp-eyebrow">ENGINEERING INTELLIGENCE</span>
          <h2 className="lp-h2">Connected engineering subsystems.</h2>
        </div>
      </Reveal>
      <div className="lp-intel-grid">
        {INTELLIGENCE_CAPABILITIES.map((cap, i) => (
          <Reveal key={cap.name} delay={i * 50}>
            <div className="lp-intel-card">
              <span className="lp-intel-icon" aria-hidden="true">{cap.icon}</span>
              <h4 className="lp-intel-name">{cap.name}</h4>
              <p className="lp-intel-desc">{cap.desc}</p>
            </div>
          </Reveal>
        ))}
      </div>
    </section>
  );
}

/* ───────────────────── Contract Intelligence ───────────────────── */

function ContractIntelligenceSection() {
  const statuses = [
    { layer: 'FRONTEND', field: 'User.email', status: 'MATCH' },
    { layer: 'API CONTRACT', field: 'POST /users', status: 'MATCH' },
    { layer: 'DATABASE', field: 'users.email', status: 'MATCH' },
    { layer: 'FRONTEND', field: 'User.role', status: 'DRIFT' },
    { layer: 'API CONTRACT', field: 'GET /users/:id', status: 'MISSING' },
  ];

  return (
    <section className="lp-section">
      <Reveal>
        <div className="lp-section-header">
          <span className="lp-eyebrow">CONTRACT INTELLIGENCE</span>
          <h2 className="lp-h2">Catch integration failures before runtime.</h2>
          <p className="lp-section-sub">
            Contract intelligence identifies schema mismatches between frontend, API, and database layers before they become runtime failures.
          </p>
        </div>
      </Reveal>
      <Reveal delay={100}>
        <div className="lp-contract-table" role="table" aria-label="Contract validation status">
          <div className="lp-ct-header" role="row">
            <span role="columnheader">Layer</span>
            <span role="columnheader">Field / Endpoint</span>
            <span role="columnheader">Status</span>
          </div>
          {statuses.map((s, i) => (
            <div className="lp-ct-row" role="row" key={i}>
              <span className="lp-ct-layer">{s.layer}</span>
              <span className="lp-ct-field"><code>{s.field}</code></span>
              <span className={`lp-ct-status lp-ct-${s.status.toLowerCase()}`}>{s.status}</span>
            </div>
          ))}
        </div>
      </Reveal>
    </section>
  );
}

/* ───────────────────── Testing / Quality Pipeline ───────────────────── */

function TestingSection() {
  return (
    <section className="lp-section" id="lp-testing">
      <Reveal>
        <div className="lp-section-header">
          <span className="lp-eyebrow">VERIFICATION PIPELINE</span>
          <h2 className="lp-h2">Verification is part of generation.</h2>
        </div>
      </Reveal>
      <Reveal delay={100}>
        <div className="lp-testing-pipeline">
          <div className="lp-tp-source">
            <span className="lp-tp-label">Generated Code</span>
          </div>
          <div className="lp-tp-arrow" aria-hidden="true" />
          <div className="lp-tp-layers">
            {TESTING_LAYERS.map((layer, i) => (
              <div className="lp-tp-layer" key={layer} style={{ animationDelay: `${i * 60}ms` }}>
                {layer}
              </div>
            ))}
          </div>
          <div className="lp-tp-arrow" aria-hidden="true" />
          <div className="lp-tp-gate">
            <span className="lp-tp-label">Release Gate</span>
          </div>
        </div>
      </Reveal>
    </section>
  );
}

/* ───────────────────── Model Routing ───────────────────── */

function ModelRoutingSection() {
  return (
    <section className="lp-section">
      <Reveal>
        <div className="lp-section-header">
          <span className="lp-eyebrow">MODEL ROUTING</span>
          <h2 className="lp-h2">Transparent hardware-aware model selection.</h2>
        </div>
      </Reveal>
      <Reveal delay={100}>
        <div className="lp-model-routing">
          <div className="lp-mr-node lp-mr-primary">
            <span className="lp-mr-label">Primary Model</span>
            <code>ai/qwen3.8-flash-next</code>
            <span className="lp-mr-status lp-mr-unavailable">NOT AVAILABLE ON CURRENT HARDWARE</span>
          </div>
          <div className="lp-mr-arrow" aria-hidden="true">
            <span>Hardware capability check</span>
          </div>
          <div className="lp-mr-node lp-mr-fallback">
            <span className="lp-mr-label">Transparent Fallback</span>
            <code>ai/qwen3:4b-instruct-2507-q4_K_M</code>
            <span className="lp-mr-status lp-mr-connected">CONNECTED · Docker Model Runner</span>
          </div>
          <div className="lp-mr-arrow" aria-hidden="true">
            <span>Execution</span>
          </div>
          <div className="lp-mr-node lp-mr-execution">
            <span className="lp-mr-label">Agent Inference</span>
            <span className="lp-mr-detail">All 6 agents receive model access through unified routing</span>
          </div>
        </div>
      </Reveal>
    </section>
  );
}

/* ───────────────────── Real Software Engineering ───────────────────── */

function RealEngineeringSection() {
  const items = ['Code', 'Git', 'Tests', 'Runtime', 'Docker', 'APIs', 'Databases', 'RAG', 'Deployment', 'Artifacts'];
  return (
    <section className="lp-section">
      <Reveal>
        <div className="lp-section-header">
          <span className="lp-eyebrow">REAL ENGINEERING</span>
          <h2 className="lp-h2">Built for engineering workflows, not demos.</h2>
          <p className="lp-section-sub">SEAM operates on actual engineering workflows — real files, real processes, real verification.</p>
        </div>
      </Reveal>
      <Reveal delay={100}>
        <div className="lp-real-grid">
          {items.map(item => (
            <div className="lp-real-item" key={item}>
              <span className="lp-real-dot" aria-hidden="true" />
              {item}
            </div>
          ))}
        </div>
      </Reveal>
    </section>
  );
}

/* ───────────────────── Integrations ───────────────────── */

function IntegrationsSection() {
  return (
    <section className="lp-section" id="lp-integrations">
      <Reveal>
        <div className="lp-section-header">
          <span className="lp-eyebrow">ECOSYSTEM</span>
          <h2 className="lp-h2">Verified integrations.</h2>
        </div>
      </Reveal>
      <Reveal delay={100}>
        <div className="lp-integrations-grid">
          {INTEGRATIONS.map(int => (
            <div className="lp-integration-card" key={int.name}>
              <span className="lp-int-name">{int.name}</span>
              <span className="lp-int-category">{int.category}</span>
              <span className={`lp-int-status lp-int-${int.status.toLowerCase().replace(/_/g, '-')}`}>
                {int.status.replace(/_/g, ' ')}
              </span>
            </div>
          ))}
        </div>
      </Reveal>
    </section>
  );
}

/* ───────────────────── Security / Governance ───────────────────── */

function SecuritySection() {
  return (
    <section className="lp-section" id="lp-security">
      <Reveal>
        <div className="lp-section-header">
          <span className="lp-eyebrow">SECURITY & GOVERNANCE</span>
          <h2 className="lp-h2">Autonomy with guardrails.</h2>
          <p className="lp-section-sub">
            Every autonomous action is controlled through permission boundaries, tool registries, and audit trails.
          </p>
        </div>
      </Reveal>
      <Reveal delay={100}>
        <div className="lp-security-grid">
          {SECURITY_ITEMS.map(item => (
            <div className="lp-security-item" key={item}>
              <span className="lp-security-check" aria-hidden="true">✓</span>
              <span>{item}</span>
            </div>
          ))}
        </div>
      </Reveal>
    </section>
  );
}

/* ───────────────────── Research / Evaluation ───────────────────── */

function ResearchSection() {
  return (
    <section className="lp-section" id="lp-research">
      <Reveal>
        <div className="lp-section-header">
          <span className="lp-eyebrow">RESEARCH & EVALUATION</span>
          <h2 className="lp-h2">Measured, not merely demonstrated.</h2>
          <p className="lp-section-sub">
            SEAM includes a controlled evaluation harness for reproducible measurement through ablation studies.
          </p>
        </div>
      </Reveal>
      <Reveal delay={100}>
        <div className="lp-research-grid">
          <div className="lp-research-card">
            <h4>Domain RAG</h4>
            <p>Controlled study comparing domain-aware retrieval against baseline generation.</p>
            <div className="lp-research-method">
              <span className="lp-rm-tag">Full System</span>
              <span className="lp-rm-vs">vs</span>
              <span className="lp-rm-tag lp-rm-ablation">Ablation</span>
            </div>
          </div>
          <div className="lp-research-card">
            <h4>Autonomous Repair</h4>
            <p>Evaluation of defect detection, localization accuracy, and repair success rate.</p>
            <div className="lp-research-method">
              <span className="lp-rm-tag">Reproducible</span>
              <span className="lp-rm-tag">Machine-Readable</span>
            </div>
          </div>
          <div className="lp-research-card">
            <h4>Contract Intelligence</h4>
            <p>Measurement of integration mismatch detection across frontend, API, and database layers.</p>
            <div className="lp-research-method">
              <span className="lp-rm-tag">Controlled</span>
              <span className="lp-rm-tag">Ablation</span>
            </div>
          </div>
        </div>
      </Reveal>
    </section>
  );
}

/* ───────────────────── Credibility ───────────────────── */

function CredibilitySection() {
  return (
    <section className="lp-section lp-credibility-section">
      <Reveal>
        <div className="lp-credibility-strip">
          {CREDIBILITY.map(c => (
            <div className="lp-cred-item" key={c.detail}>
              <span className="lp-cred-num">{c.label}</span>
              <span className="lp-cred-label">{c.detail}</span>
            </div>
          ))}
        </div>
      </Reveal>
    </section>
  );
}

/* ───────────────────── Final CTA ───────────────────── */

function FinalCTA({ onLaunch, onArchitecture }: { onLaunch: () => void; onArchitecture?: () => void }) {
  return (
    <section className="lp-section lp-final-cta" id="lp-cta">
      <Reveal>
        <div className="lp-cta-content">
          <h2 className="lp-h2 lp-cta-title">From requirements to validated delivery.</h2>
          <p className="lp-cta-sub">
            Build, verify, repair, and deliver software through one autonomous engineering workflow.
          </p>
          <div className="lp-hero-actions">
            <button className="lp-btn lp-btn--primary lp-btn--lg" onClick={onLaunch}>
              Launch SEAM
              <span className="lp-btn-arrow" aria-hidden="true">→</span>
            </button>
            <button className="lp-btn lp-btn--ghost lp-btn--lg" onClick={() => onArchitecture?.() || document.getElementById('lp-agents')?.scrollIntoView({ behavior: 'smooth' })}>
              Explore the Architecture
            </button>
          </div>
        </div>
      </Reveal>
    </section>
  );
}

/* ───────────────────── Footer ───────────────────── */

function Footer() {
  return (
    <footer className="lp-footer">
      <div className="lp-footer-grid">
        <div className="lp-footer-col">
          <h5>Product</h5>
          <span>Architecture</span>
          <span>Workspace</span>
          <span>Testing</span>
          <span>Repair</span>
          <span>Delivery</span>
        </div>
        <div className="lp-footer-col">
          <h5>Engineering</h5>
          <span>Agents</span>
          <span>RAG</span>
          <span>Contracts</span>
          <span>Runtime</span>
          <span>Evaluation</span>
        </div>
        <div className="lp-footer-col">
          <h5>Resources</h5>
          <span>Documentation</span>
          <span>GitHub</span>
          <span>Research</span>
        </div>
        <div className="lp-footer-col">
          <h5>Project</h5>
          <span>Final Year Project</span>
          <span>Architecture</span>
          <span>Experiments</span>
        </div>
      </div>
      <div className="lp-footer-bottom">
        <span className="lp-footer-brand">⚡ SEAM</span>
        <span className="lp-footer-tagline">Self-Evolving Autonomous Multi-Agent Framework</span>
      </div>
    </footer>
  );
}

/* ───────────────────── Main Landing Page ───────────────────── */

export function LandingPage({ onLaunch, onWorkspace, onArchitecture, onLogin }: LandingPageProps) {
  return (
    <div className="lp-root" role="main">
      <Navbar onLaunch={onLaunch} onWorkspace={onWorkspace} onLogin={onLogin} />
      <HeroSection onLaunch={onLaunch} onArchitecture={onArchitecture} />
      <ProductPreview />
      <WorkflowSection />
      <HowItWorksSection />
      <CredibilitySection />
      <AgentsSection />
      <SupervisorSection />
      <DomainIntelligenceSection />
      <AutonomousRepairSection />
      <EngineeringIntelligenceSection />
      <ContractIntelligenceSection />
      <TestingSection />
      <ModelRoutingSection />
      <RealEngineeringSection />
      <IntegrationsSection />
      <SecuritySection />
      <ResearchSection />
      <FinalCTA onLaunch={onLaunch} onArchitecture={onArchitecture} />
      <Footer />
    </div>
  );
}
