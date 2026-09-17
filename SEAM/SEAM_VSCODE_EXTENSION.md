# SEAM VS Code Extension Guide

## Overview
The SEAM IDE Extension transforms VS Code into a powerful, multi-agent AI Autonomous Engineering platform. It seamlessly connects to the SEAM FastAPI backend via REST and WebSockets to orchestrate, monitor, and visualize software engineering tasks dynamically.

## Installation
1. Locate the generated VSIX file: `seam-vscode/seam-1.0.0.vsix`
2. Open VS Code.
3. Go to the Extensions view (`Ctrl+Shift+X`).
4. Click the `...` menu and select **Install from VSIX**.
5. Restart VS Code.

## Configuration
- `seam.apiUrl`: The URL to the SEAM backend. Default is `http://127.0.0.1:8000`.
- `seam.websocketEnabled`: Set to `true` to receive live streaming agent events.

## Features
### Requirements & Scale Awareness
The built-in Dashboard lets you submit natural language requirements. It will automatically trigger the Analysis Agent to classify the domain and establish a **Project Scale** bounds constraint (from Small to Enterprise).

### Agent Monitoring & Supervisor Workflows
A WebSocket connection streams events from the 6 SEAM Agents directly into the VS Code UI. The Dashboard provides a real-time view into the Supervisor's orchestration logic (including error/rework loops).

### LLM Visual Diagrams
A key feature of the extension is the interactive Webview for **Architecture, Class, Sequence, and DFD Diagrams**.
SEAM completely bypasses text-based renderers like PlantUML. Instead, Qwen streams structured Pydantic JSON directly into the VS Code Webview, which then renders the coordinates dynamically via **React Flow**.

### Security & Path Traversal Protection
The extension provides a secure file-opener mechanism that restricts access strictly to files inside the `generated_projects/{project_name}/` workspace folder. Any attempt to traverse out (e.g., `../`) will trigger a security boundary exception.
