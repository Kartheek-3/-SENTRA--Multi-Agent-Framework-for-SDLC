# SEAM v1.0.0 — Figma Workflow & Design Integration Guide

**Project:** SEAM (Self-Evolving Autonomous Multi-Agent Framework)  
**Roles:** Principal UI/UX Designer, Senior Frontend Architect, Design Reviewer  
**Figma Integration Status:** **`NOT_CONFIGURED` (Local Code-Based System Active)**

---

## 1. Executive Summary & Board Position

In strict adherence to SEAM's primary engineering principles:
> *"Never claim Figma was updated unless an actual Figma operation succeeded. If Figma MCP is unavailable, continue with local code-based design work, but clearly mark Figma integration as NOT_CONFIGURED."*

In the current execution environment, no active Figma MCP server or remote token is mounted. Therefore, SEAM operates under the **Local Code-Based Design System Mode**, while maintaining a formal specification for bidirectional Figma synchronization when credentials are provided.

---

## 2. Figma-First Design Workflow Architecture

When a Figma workspace is connected via the official Figma MCP or REST API, SEAM follows this 6-stage lifecycle:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   STAGE 1: DESIGN TOKENS DEFINITION                   │
│  Figma Variables (Colors, Spacing, Radii) ──► SEAM Design Tokens       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 STAGE 2: COMPONENT INVENTORY & VARIANTS                │
│  Auto Layout Frames: Badges, Buttons, Cards, Modals, Topbar, Sidebar  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 STAGE 3: HIGH-FIDELITY SCREEN LAYOUTS                  │
│  Landing, Dashboard, Workspace, Design Studio, Test Lab, Repair Center │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 STAGE 4: REACT / TYPESCRIPT SYNCHRONIZATION            │
│  Figma AST / Node Export ──► React Components in seam-ide/src/         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 STAGE 5: VISUAL QA & DRIFT COMPARISON                  │
│  Playwright Visual Regression ⟷ Figma Frame Pixels (Threshold < 1%)    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 STAGE 6: BIDIRECTIONAL HANDOFF                         │
│  Design adjustments pushed back to Figma via Figma MCP write tools     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Figma Design System File Structure

When creating the official Figma project file (`SEAM_Design_System.fig`), frames must be organized into 5 designated pages:

### Page 1: Design Tokens & Primitives
- **Color Palettes:** Neutrals (Canvas `#0d1117`, Surface `#161b22`, Border `#30363d`), Accents (`#388bfd`), and Semantic Badges (`#3fb950`, `#d29922`, `#f85149`).
- **Typography Styles:** Inter font tokens (Display 24/700, Title 20/600, Section 14/600, Body 13/400) and JetBrains Mono code styles.
- **Spacing Components:** Visual spacers representing 4px, 8px, 12px, 16px, 24px, 32px.

### Page 2: Atomic Components & Variants
- **Buttons:** Primary (`#388bfd`), Secondary (`#21262d`), Danger (`#da3633`), Ghost.
- **Status Badges:** Variants for `PASS`, `FAIL`, `RUNNING`, `NOT_CONFIGURED`, `BLOCKED`, `STALE`, `UNKNOWN`.
- **Search Trigger & Command Palette:** Search bar with embedded `<kbd>Ctrl+K</kbd>` badge.

### Page 3: Canonical Diagram Components
- Visual nodes for the **10 Canonical Diagrams** (Components, Packages, Classes, Actors, Use Cases, DB Entities).
- Relationship connectors (Directed dependency, association, inheritance, data flow).

### Page 4: Full Application Screens
1. **LandingPage:** Hero banner, 6-agent overview, autonomous repair flow, architecture stack.
2. **DashboardPage:** KPI stat tiles, recent activity feed, real-time subsystem integration matrix.
3. **Workspace:** Flexible multi-dock layout (Explorer, CodeMirror Editor, Agent Cockpit, Bottom Dock).
4. **DesignStudioPage:** 10-diagram switcher, Sugiyama visual canvas, JSON/Mermaid export drawer.
5. **TestLabPage:** 17-category testing cards, category filter tabs, execution details drawer.
6. **ContractsPage:** Three-way parity columns (Frontend Plan, API Endpoints, DB Schema).
7. **RepairCenterPage:** Closed-loop healing timeline, defect inspector, root cause & patch view.
8. **RuntimePage:** Process lifecycle manager, port allocation grid, stdout log box.
9. **ModelControlPanel:** Inference provider cards, fallback policy banner, task routing table.

### Page 5: Interactive Prototypes & Transitions
- Command Palette overlay modal transitions.
- Drawer slide-ins and tab switching states.

---

## 4. Figma MCP Configuration Guide

To enable live bidirectional synchronization with Figma:

1. **Obtain Personal Access Token:** Generate a token in Figma under *Settings $\to$ Account $\to$ Personal access tokens*.
2. **Set Host Environment Variable:**
   Configure `FIGMA_ACCESS_TOKEN` in your system environment variables. Never write or commit token values to files.
   ```bash
   # Set in host environment (do not commit to files)
   export FIGMA_ACCESS_TOKEN="<YOUR_TOKEN_HERE>"
   # On Windows PowerShell:
   $env:FIGMA_ACCESS_TOKEN="<YOUR_TOKEN_HERE>"
   ```
3. **Enable Figma MCP Server in Antigravity IDE:**
   Configure `mcp_config.json` using the official remote endpoint or environment reference:
   ```json
   {
     "mcpServers": {
       "figma": {
         "serverUrl": "https://mcp.figma.com/sse"
       }
     }
   }
   ```
4. **Automated Handoff:** Once mounted, SEAM can extract variables directly into `src/styles.css` and validate UI layout parity.
