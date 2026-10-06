# SEAM Product Frontend

Date: 2026-09-23

## Product Architecture

The frontend now presents two surfaces in the existing React/Vite/Tauri app:

- Public website: product narrative, workflow, agents, intelligence layer, integrations, use cases, and CTA.
- SEAM Workspace: dashboard, projects, IDE workspace, agents, artifacts, QA, delivery, evaluation, experiments, integrations, settings, and system readiness.

The existing CodeMirror/Tauri IDE remains intact and is mounted as the Workspace route.

## Data Flow

Product pages use existing backend state only:

- Projects: `/api/projects`
- Project status: `/api/projects/{project_id}/status`
- Files/artifacts: existing project filesystem and artifact endpoints
- EventStore: `/events`
- n8n: `/api/integrations/n8n/status`
- Experiments: `/api/experiments`
- Health: `/api/system/health`
- WebSocket: existing project event stream

Marketing content is static explanatory content. Product pages do not fabricate workflow completion.

## Navigation

Top navigation:

- SEAM brand
- Workspace selector
- Project selector
- Search
- Refresh
- Appearance

Left navigation:

- Dashboard
- Projects
- Workspace
- Agents
- Artifacts
- QA
- Delivery
- Evaluation
- Experiments
- Integrations
- Settings
- System Status

## Design System

The product layer adds theme tokens, restrained cards, clear status rows, accessible focusable controls, responsive grids, and first-class dark/light/system modes.

## Workspace

The Workspace route preserves:

- CodeMirror editor
- Project Explorer
- SEAM Assistant
- WebSocket-driven updates
- File open/save/reload
- Existing flexible dock/floating/fullscreen panels

## Responsive Strategy

Desktop and laptop use the full product shell. Tablet/mobile collapse navigation into horizontal scrolling and retain dashboard, projects, activity, QA, and assistant-friendly pages. The full IDE remains optimized for larger screens.

## Security

Secrets are never displayed. Credential settings show only `Configured` or `Not Configured`.

## Known Limitations

- Authentication is represented as a product shell, but the existing app does not yet include a full identity provider.
- Product screenshots are UI-style placeholders until captured screenshots are connected as assets.
- Optional integrations remain `NOT_CONFIGURED` unless backend status reports otherwise.
