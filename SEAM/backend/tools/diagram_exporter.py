from typing import Any, Dict, List
import re
from backend.models.diagram import DiagramEdge, DiagramJSON, DiagramNode


def _sanitize_id(val: str) -> str:
    s = re.sub(r'[^a-zA-Z0-9_]', '_', str(val))
    return s.strip('_') or "node"


def _sanitize_label(val: str) -> str:
    s = str(val).replace('"', "'").replace("\n", " ").replace(";", " ")
    return s.strip()


def export_diagram_to_mermaid(diagram: Any) -> str:
    """Exports any validated diagram structure into strict, parseable Mermaid syntax."""
    if isinstance(diagram, dict):
        nodes = diagram.get("nodes", [])
        edges = diagram.get("edges", [])
        dtype = str(diagram.get("diagram_type", "Diagram")).replace("_", " ").title()
        raw_dict = diagram
    elif hasattr(diagram, "nodes") and hasattr(diagram, "edges"):
        nodes = getattr(diagram, "nodes", [])
        edges = getattr(diagram, "edges", [])
        dtype = str(getattr(diagram, "diagram_type", "Diagram")).replace("_", " ").title()
        raw_dict = diagram.model_dump() if hasattr(diagram, "model_dump") else {}
    else:
        return "%% Empty diagram data"

    clean_dtype = dtype.lower().replace("-", "_")

    # 1. Specialized Sequence Diagram Export
    if "sequence" in clean_dtype and ("participants" in raw_dict or len(nodes) >= 2):
        lines = ["sequenceDiagram", f"  %% {dtype}"]
        participants = raw_dict.get("participants", [])
        if participants:
            for p in participants:
                pid = _sanitize_id(p.get("id", "p"))
                name = _sanitize_label(p.get("name", pid))
                lines.append(f'  participant {pid} as {name}')
            for msg in raw_dict.get("messages", []):
                src = _sanitize_id(msg.get("from_node", "src"))
                tgt = _sanitize_id(msg.get("to_node", "tgt"))
                txt = _sanitize_label(msg.get("message", "call"))
                lines.append(f"  {src}->>{tgt}: {txt}")
            return "\n".join(lines)
        else:
            for n in nodes:
                nid = _sanitize_id(n.get("id") if isinstance(n, dict) else getattr(n, "id"))
                label = _sanitize_label(
                    (n.get("data", {}).get("label") if isinstance(n, dict) else getattr(n, "data", {}).get("label")) or nid
                )
                lines.append(f'  participant {nid} as {label}')
            for e in edges:
                src = _sanitize_id(e.get("source") if isinstance(e, dict) else getattr(e, "source"))
                tgt = _sanitize_id(e.get("target") if isinstance(e, dict) else getattr(e, "target"))
                lbl = _sanitize_label(e.get("label") if isinstance(e, dict) else getattr(e, "label", "call"))
                lines.append(f"  {src}->>{tgt}: {lbl or 'call'}")
            return "\n".join(lines)

    # 2. Specialized Class Diagram Export
    if "class" in clean_dtype and "classes" in raw_dict:
        lines = ["classDiagram", f"  %% {dtype}"]
        for cls in raw_dict.get("classes", []):
            cname = _sanitize_id(cls.get("name", cls.get("id", "Class")))
            lines.append(f"  class {cname} {{")
            for a in cls.get("attributes", []):
                lines.append(f"    +{a.get('name')}: {a.get('type')}")
            for m in cls.get("methods", []):
                lines.append(f"    +{m.get('name')}()")
            lines.append("  }")
        for rel in raw_dict.get("relationships", []):
            src = _sanitize_id(rel.get("source", ""))
            tgt = _sanitize_id(rel.get("target", ""))
            if src and tgt:
                lines.append(f"  {src} --> {tgt}")
        if len(lines) > 2:
            return "\n".join(lines)

    # 3. Standard Flowchart TD for Architecture, DFD, Activity, ERD, Deployment
    lines = ["flowchart TD", f"  %% {dtype}"]

    for n in nodes:
        if isinstance(n, dict):
            nid = _sanitize_id(n.get("id", "node"))
            data = n.get("data", {})
            label = _sanitize_label(data.get("label") or n.get("label") or nid)
        else:
            nid = _sanitize_id(getattr(n, "id", "node"))
            data = getattr(n, "data", {})
            label = _sanitize_label(data.get("label") if isinstance(data, dict) else nid)
        lines.append(f'  {nid}["{label}"]')

    for e in edges:
        if isinstance(e, dict):
            src = _sanitize_id(e.get("source", ""))
            tgt = _sanitize_id(e.get("target", ""))
            lbl = e.get("label")
        else:
            src = _sanitize_id(getattr(e, "source", ""))
            tgt = _sanitize_id(getattr(e, "target", ""))
            lbl = getattr(e, "label", None)

        if src and tgt:
            if lbl:
                clean_lbl = _sanitize_label(lbl)
                lines.append(f'  {src} -->|"{clean_lbl}"| {tgt}')
            else:
                lines.append(f"  {src} --> {tgt}")

    return "\n".join(lines)
