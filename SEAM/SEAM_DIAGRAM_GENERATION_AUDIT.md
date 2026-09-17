# SEAM Diagram Generation Audit

## Current Pipeline

The active diagram pipeline is:

```text
AnalysisResult + ProjectPlan + SystemDesign
  -> LLM diagram generator
  -> Structured DiagramJSON
  -> Pydantic validation
  -> persisted JSON files
  -> VS Code webview rendering with React Flow
```

## Active Files

- `backend/models/diagram.py`
- `backend/tools/diagram_generator.py`
- `backend/api/projects.py` diagram endpoints
- `../seam-vscode/src/webview/DiagramsView.tsx`
- `tests/test_diagram_generation.py`

## Supported Diagram Types

- Architecture
- Use Case
- Class
- Object
- Sequence
- Activity
- DFD Level 0
- DFD Level 1

## Retired Pipeline

Text-based generated `.puml` artifacts are not part of the final active pipeline. Existing generated `.puml` files were removed during repository cleanup.
