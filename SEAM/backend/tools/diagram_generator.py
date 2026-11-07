import os
import json
import struct
import zlib
import logging
from concurrent.futures import as_completed
from typing import Any, Dict, List, Optional, Tuple

from backend.models.analysis import AnalysisResult
from backend.models.planning import ProjectPlan
from backend.models.diagram import DiagramEdge, DiagramJSON, DiagramNode
from backend.llm.model_router import ModelRouter
from backend.utils import slugify
from backend.tools.artifact_pipeline import write_bytes_artifact, write_text_artifact
from backend.concurrency import diagram_executor
from backend.config import DIAGRAM_TIMEOUT_SECONDS
from backend.performance import estimate_tokens, timed_call, timed_llm_call

from backend.tools.diagram_templates import (
    CANONICAL_DIAGRAM_TYPES,
    DiagramSelectionService,
    normalize_diagram_identifier,
    registry as template_registry,
)
from backend.tools.diagram_adapter import adapt_to_react_flow
from backend.tools.diagram_validator import DiagramValidator
from backend.tools.diagram_exporter import export_diagram_to_mermaid

logger = logging.getLogger(__name__)


# =====================================================================
# PNG RENDERING ENGINE (Pure Python, zero external binary dependency)
# =====================================================================

def _chunk(tag: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

def _png(width: int, height: int, pixels: bytearray) -> bytes:
    rows = bytearray()
    stride = width * 3
    for y in range(height):
        rows.append(0)
        rows.extend(pixels[y * stride:(y + 1) * stride])
    return b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) + _chunk(b"IDAT", zlib.compress(bytes(rows), 9)) + _chunk(b"IEND", b"")

def _draw_rect(pixels: bytearray, width: int, height: int, x: int, y: int, w: int, h: int, color: tuple, fill: Optional[tuple] = None):
    if fill:
        for yy in range(max(0, y), min(height, y + h)):
            for xx in range(max(0, x), min(width, x + w)):
                i = (yy * width + xx) * 3
                pixels[i:i + 3] = bytes(fill)
    for xx in range(max(0, x), min(width, x + w)):
        for yy in (y, y + h - 1):
            if 0 <= yy < height:
                i = (yy * width + xx) * 3
                pixels[i:i + 3] = bytes(color)
    for yy in range(max(0, y), min(height, y + h)):
        for xx in (x, x + w - 1):
            if 0 <= xx < width:
                i = (yy * width + xx) * 3
                pixels[i:i + 3] = bytes(color)

FONT = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"], "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01111", "10000", "10000", "10000", "10000", "10000", "01111"], "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"], "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01111", "10000", "10000", "10111", "10001", "10001", "01110"], "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"], "J": ["11111", "00010", "00010", "00010", "10010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"], "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"], "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"], "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"], "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"], "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"], "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "10101", "01010"], "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"], "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"], "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"], "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"], "5": ["11111", "10000", "10000", "11110", "00001", "00001", "11110"],
    "6": ["01110", "10000", "10000", "11110", "10001", "10001", "01110"], "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"], "9": ["01110", "10001", "10001", "01111", "00001", "00001", "01110"],
    " ": ["00000"] * 7, "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"], "_": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    "/": ["00001", "00010", "00010", "00100", "01000", "01000", "10000"], ":": ["00000", "00100", "00000", "00000", "00100", "00000", "00000"],
}

def _draw_text(pixels: bytearray, width: int, height: int, x: int, y: int, text: str, color=(29, 37, 51), scale=2):
    cursor = x
    for char in text.upper()[:34]:
        glyph = FONT.get(char, FONT[" "])
        for gy, row in enumerate(glyph):
            for gx, val in enumerate(row):
                if val == "1":
                    for sy in range(scale):
                        for sx in range(scale):
                            xx = cursor + gx * scale + sx
                            yy = y + gy * scale + sy
                            if 0 <= xx < width and 0 <= yy < height:
                                i = (yy * width + xx) * 3
                                pixels[i:i + 3] = bytes(color)
        cursor += 6 * scale

def _line(pixels: bytearray, width: int, height: int, x1: int, y1: int, x2: int, y2: int, color=(77, 94, 123)):
    steps = max(abs(x2 - x1), abs(y2 - y1), 1)
    for i in range(steps + 1):
        x = int(x1 + (x2 - x1) * i / steps)
        y = int(y1 + (y2 - y1) * i / steps)
        if 0 <= x < width and 0 <= y < height:
            idx = (y * width + x) * 3
            pixels[idx:idx + 3] = bytes(color)

def render_diagram_png(diagram: DiagramJSON, title: str) -> bytes:
    width, height = 1800, 1100
    pixels = bytearray([248, 250, 252] * width * height)
    _draw_text(pixels, width, height, 48, 36, title, (20, 30, 45), 3)
    nodes = diagram.nodes or []
    positions = {}
    for index, node in enumerate(nodes):
        x = int(getattr(node, "position", {}).get("x", 80 + (index % 4) * 410) if isinstance(getattr(node, "position", {}), dict) else 80 + (index % 4) * 410)
        y = int(getattr(node, "position", {}).get("y", 140 + (index // 4) * 180) if isinstance(getattr(node, "position", {}), dict) else 140 + (index // 4) * 180)
        x = max(60, min(width - 340, x))
        y = max(120, min(height - 140, y))
        positions[node.id] = (x + 150, y + 42)
    for edge in diagram.edges or []:
        source = positions.get(edge.source)
        target = positions.get(edge.target)
        if source and target:
            _line(pixels, width, height, source[0], source[1], target[0], target[1])
    for index, node in enumerate(nodes):
        cx, cy = positions.get(node.id, (120, 120))
        x, y = cx - 150, cy - 42
        _draw_rect(pixels, width, height, x, y, 300, 84, (67, 87, 121), (232, 238, 247))
        label = node.data.get("label") if isinstance(node.data, dict) else None
        _draw_text(pixels, width, height, x + 18, y + 22, str(label or node.id), (23, 35, 55), 2)
    return _png(width, height, pixels)


# =====================================================================
# DETERMINISTIC EXTRACTION ENGINE (ALL 10 CANONICAL TYPES)
# =====================================================================

def _node(node_id: str, label: str, x: int, y: int, node_type: str = "default", **data) -> DiagramNode:
    return DiagramNode(
        id=node_id,
        type=node_type,
        data={"id": node_id, "label": label, **data},
        position={"x": float(x), "y": float(y)},
    )

def _edge(edge_id: str, source: str, target: str, label: str = "") -> DiagramEdge:
    return DiagramEdge(id=edge_id, source=source, target=target, label=label or None, type="smoothstep")

def _generate_rule_based_diagram(diagram_type: str, analysis: Optional[AnalysisResult], plan: Optional[ProjectPlan]) -> Optional[DiagramJSON]:
    norm = normalize_diagram_identifier(diagram_type)
    if not norm:
        return None

    cid = norm["id"]
    entities = plan.system_design.database_schema if plan and plan.system_design else []
    actors = analysis.actors if analysis else []
    components = plan.system_design.components if plan and plan.system_design else []
    apis = plan.system_design.api_endpoints if plan and plan.system_design else []

    # 1. Architecture
    if cid == "architecture_diagram":
        nodes = []
        for index, component in enumerate(components):
            nodes.append(_node(
                f"component_{slugify(component.component_id or component.name)}",
                f"{component.name}\n{component.responsibility[:44]}",
                110 + (index % 3) * 520,
                150 + (index // 3) * 210,
                "default",
                type="Component",
                technologies=component.technologies,
            ))
        if not nodes:
            nodes = [_node("component_app", plan.project_overview[:40] if plan else "Application Core", 650, 260, "default", type="Component")]
        node_by_name = {component.name.lower(): f"component_{slugify(component.component_id or component.name)}" for component in components}
        edges = []
        for component in components:
            source = f"component_{slugify(component.component_id or component.name)}"
            for dep_index, dependency in enumerate(component.dependencies):
                target = node_by_name.get(dependency.lower()) or f"component_{slugify(dependency)}"
                if target != source and any(node.id == target for node in nodes):
                    edges.append(_edge(f"arch_{source}_{dep_index}", source, target, "depends on"))
        if not edges and len(nodes) > 1:
            edges = [_edge(f"arch_flow_{index}", nodes[index].id, nodes[index + 1].id, "uses") for index in range(len(nodes) - 1)]
        return DiagramJSON(diagram_type="Architecture", nodes=nodes, edges=edges)

    # 2. Use Case
    if cid == "use_case_diagram":
        actor_names = actors[:3] or ["User"]
        nodes = [_node(f"actor_{index}", actor, 90, 160 + index * 170, "input", type="Actor") for index, actor in enumerate(actor_names)]
        requirements = analysis.functional_requirements if analysis else []
        for index, req in enumerate(requirements[:8]):
            nodes.append(_node(f"usecase_{index}", f"{req.id}\n{req.description[:46]}", 540 + (index % 2) * 460, 130 + (index // 2) * 145, "default", type="UseCase"))
        edges = []
        usecases = [node for node in nodes if node.data.get("type") == "UseCase"]
        for index, usecase in enumerate(usecases):
            edges.append(_edge(f"usecase_actor_{index}", f"actor_{index % len(actor_names)}", usecase.id, "performs"))
        return DiagramJSON(diagram_type="Use Case", nodes=nodes, edges=edges)

    # 3. Class
    if cid == "class_diagram":
        nodes = []
        for index, entity in enumerate(entities):
            fields_str = "\n".join(entity.fields[:8]) or "id"
            label = f"{entity.name}\n----------------\n{fields_str}"
            nodes.append(_node(f"class_{slugify(entity.name)}", label, 90 + (index % 3) * 470, 150 + (index // 3) * 210, "default", type="Class", fields=entity.fields, relationships=entity.relationships))
        if not nodes:
            fallback_entities = (analysis.entities if analysis else [])[:3] or ["Entity"]
            nodes = [_node(f"class_{slugify(entity)}", f"{entity}\n----------------\nid\nname", 90 + index * 470, 150, "default", type="Class") for index, entity in enumerate(fallback_entities)]
        edges = []
        node_ids = {node.id for node in nodes}
        for entity in entities:
            source = f"class_{slugify(entity.name)}"
            for rel_index, rel in enumerate(entity.relationships):
                for target_entity in entities:
                    target = f"class_{slugify(target_entity.name)}"
                    if target in node_ids and target_entity.name.lower() in rel.lower() and target != source:
                        edges.append(_edge(f"class_rel_{source}_{target}_{rel_index}", source, target, rel[:32]))
        if not edges and len(nodes) > 1:
            edges = [_edge(f"class_dep_{index}", nodes[index].id, nodes[index + 1].id, "relates to") for index in range(len(nodes) - 1)]
        return DiagramJSON(diagram_type="Class", nodes=nodes, edges=edges)

    # 4. Object
    if cid == "object_diagram":
        base_entities = entities or []
        if not base_entities and analysis:
            base_entities = [type("Entity", (), {"name": name, "fields": ["id", "name"], "relationships": []}) for name in analysis.entities[:4]]
        if not base_entities:
            base_entities = [type("Entity", (), {"name": "SystemConfig", "fields": ["id", "status"], "relationships": []})]
        nodes = []
        for index, entity in enumerate(base_entities[:6]):
            fields = getattr(entity, "fields", []) or ["id", "name"]
            values = "\n".join(f"{field}: sample_{slugify(field)}" for field in fields[:5])
            nodes.append(_node(f"object_{slugify(entity.name)}_{index}", f"{entity.name} instance\n----------------\n{values}", 90 + (index % 3) * 470, 150 + (index // 3) * 220, "default", type="Object"))
        edges = [_edge(f"object_link_{index}", nodes[index].id, nodes[index + 1].id, "references") for index in range(len(nodes) - 1)]
        return DiagramJSON(diagram_type="Object", nodes=nodes, edges=edges)

    # 5. Sequence
    if cid == "sequence_diagram":
        actor = actors[0] if actors else "User"
        participants = [_node("seq_actor", actor, 80, 160, "input", type="Participant")]
        for index, component in enumerate(components[:4]):
            participants.append(_node(f"seq_{slugify(component.name)}", component.name, 380 + index * 330, 160, "default", type="Participant"))
        if len(participants) == 1:
            participants.extend([
                _node("seq_frontend", "Frontend UI", 380, 160, "default", type="Participant"),
                _node("seq_api", "API Gateway", 710, 160, "default", type="Participant"),
                _node("seq_db", "Database", 1040, 160, "output", type="Participant"),
            ])
        edges = []
        for index in range(len(participants) - 1):
            lbl = apis[index].path if index < len(apis) else "request"
            edges.append(_edge(f"seq_call_{index}", participants[index].id, participants[index + 1].id, lbl))
        for index in range(len(participants) - 1, 0, -1):
            edges.append(_edge(f"seq_return_{index}", participants[index].id, participants[index - 1].id, "response"))
        return DiagramJSON(diagram_type="Sequence", nodes=participants, edges=edges)

    # 6. Activity
    if cid == "activity_diagram":
        activity_steps = ["Start"]
        activity_steps.extend([task.title for task in (plan.tasks[:6] if plan else [])])
        activity_steps.append("QA & Delivery")
        nodes = [_node(f"activity_{index}", step[:48], 140 + (index % 3) * 500, 150 + (index // 3) * 190, "default", type="ActivityStep") for index, step in enumerate(activity_steps)]
        edges = [_edge(f"activity_flow_{index}", nodes[index].id, nodes[index + 1].id, "next") for index in range(len(nodes) - 1)]
        return DiagramJSON(diagram_type="Activity", nodes=nodes, edges=edges)

    # 7. DFD Level 0
    if cid == "dfd_level_0":
        actor_names = actors[:3] or ["User"]
        nodes = [_node(f"actor_{index}", actor, 90, 180 + index * 190, "input", type="ExternalEntity") for index, actor in enumerate(actor_names)]
        nodes.append(_node("process_system", plan.project_overview[:34] if plan else "Application System", 700, 270, "default", type="Process"))
        stores = entities[:3]
        for index, entity in enumerate(stores):
            nodes.append(_node(f"store_{slugify(entity.name)}", f"{entity.name} Store", 1280, 180 + index * 190, "output", type="DataStore"))
        edges = []
        for index, actor in enumerate(actor_names):
            edges.append(_edge(f"dfd0_in_{index}", f"actor_{index}", "process_system", "request/input"))
            edges.append(_edge(f"dfd0_out_{index}", "process_system", f"actor_{index}", "response/output"))
        for index, entity in enumerate(stores):
            edges.append(_edge(f"dfd0_store_{index}", "process_system", f"store_{slugify(entity.name)}", "read/write data"))
        return DiagramJSON(diagram_type="DFD Level 0", nodes=nodes, edges=edges)

    # 8. DFD Level 1
    if cid == "dfd_level_1":
        nodes = []
        for index, api in enumerate(apis[:6]):
            nodes.append(_node(f"process_{index}", f"{api.method} {api.path}\n{api.purpose[:40]}", 430 + (index % 2) * 430, 140 + (index // 2) * 190, "default", type="Process"))
        if not nodes:
            for index, task in enumerate(plan.tasks[:6] if plan else []):
                nodes.append(_node(f"process_{index}", task.title[:42], 430 + (index % 2) * 430, 140 + (index // 2) * 190, "default", type="Process"))
        nodes.insert(0, _node("external_user", actors[0] if actors else "User", 90, 280, "input", type="ExternalEntity"))
        for index, entity in enumerate(entities[:3]):
            nodes.append(_node(f"store_{slugify(entity.name)}", f"{entity.name} Store", 1320, 180 + index * 190, "output", type="DataStore"))
        edges = []
        process_nodes = [node for node in nodes if node.data.get("type") == "Process"]
        for index, node in enumerate(process_nodes):
            edges.append(_edge(f"dfd1_user_{index}", "external_user", node.id, "request"))
            if entities:
                store = f"store_{slugify(entities[index % len(entities)].name)}"
                edges.append(_edge(f"dfd1_store_{index}", node.id, store, "read/write"))
            edges.append(_edge(f"dfd1_response_{index}", node.id, "external_user", "response"))
        return DiagramJSON(diagram_type="DFD Level 1", nodes=nodes, edges=edges)

    # 9. ERD (Database)
    if cid == "erd_diagram":
        nodes = []
        for index, entity in enumerate(entities):
            cols = [f"{f} (VARCHAR)" for f in (entity.fields[:8] or ["id"])]
            label = f"{entity.name}\n================\n" + "\n".join(cols)
            nodes.append(_node(
                f"erd_{slugify(entity.name)}",
                label,
                100 + (index % 3) * 480,
                150 + (index // 3) * 230,
                "default",
                type="DatabaseEntity",
                attributes=cols,
            ))
        if not nodes:
            fallback_entities = (analysis.entities if analysis else [])[:3] or ["User", "Record"]
            nodes = [
                _node(f"erd_{slugify(ent)}", f"{ent}\n================\nid (UUID)\nname (VARCHAR)", 100 + idx * 480, 150, "default", type="DatabaseEntity", attributes=["id (UUID)", "name (VARCHAR)"])
                for idx, ent in enumerate(fallback_entities)
            ]
        edges = []
        node_ids = {node.id for node in nodes}
        for entity in entities:
            source = f"erd_{slugify(entity.name)}"
            for r_idx, rel in enumerate(entity.relationships):
                for target_entity in entities:
                    target = f"erd_{slugify(target_entity.name)}"
                    if target in node_ids and target_entity.name.lower() in rel.lower() and target != source:
                        edges.append(_edge(f"erd_rel_{source}_{target}_{r_idx}", source, target, "1:N (Foreign Key)"))
        if not edges and len(nodes) > 1:
            edges = [_edge(f"erd_link_{i}", nodes[i].id, nodes[i + 1].id, "1:N Relationship") for i in range(len(nodes) - 1)]
        return DiagramJSON(diagram_type="ERD (Database)", nodes=nodes, edges=edges)

    # 10. Deployment
    if cid == "deployment_diagram":
        nodes = [
            _node("dep_client", "Client Browser\n(React SPA / HTTPS)", 100, 200, "input", type="DeploymentNode", technology="React 18", environment="Client Host"),
            _node("dep_gateway", "Reverse Proxy / Gateway\n(Port 80/443)", 500, 200, "default", type="DeploymentNode", technology="Nginx / Traefik", environment="Edge Network"),
            _node("dep_backend", "SEAM Backend Core\n(FastAPI / Port 8000)", 900, 200, "default", type="DeploymentNode", technology="Python / FastAPI", environment="Docker Container"),
            _node("dep_database", "Database Service\n(SQLite / Postgres)", 1300, 200, "output", type="DeploymentNode", technology="SQLite 3 / PostgreSQL 15", environment="Persistent Volume"),
        ]
        edges = [
            _edge("dep_e1", "dep_client", "dep_gateway", "HTTPS / WSS"),
            _edge("dep_e2", "dep_gateway", "dep_backend", "HTTP REST / Port 8000"),
            _edge("dep_e3", "dep_backend", "dep_database", "TCP / SQL Connection"),
        ]
        return DiagramJSON(diagram_type="Deployment", nodes=nodes, edges=edges)

    return None


# =====================================================================
# BOUNDED CORRECTION & PIPELINE EXECUTION
# =====================================================================

def generate_diagram_with_llm(
    diagram_type: str,
    analysis: Optional[AnalysisResult],
    plan: Optional[ProjectPlan],
    force_llm: bool = False,
) -> DiagramJSON:
    """Generates structured diagram with template registry integration, schema validation, bounded correction, and Mermaid export."""
    template = DiagramSelectionService.select_diagram(diagram_type)
    norm = normalize_diagram_identifier(diagram_type)
    canonical_id = norm["id"] if norm else "architecture_diagram"
    canonical_label = norm["label"] if norm else "Architecture"

    generation_method = "deterministic_extraction"
    model_name = "local-deterministic"

    res: Optional[DiagramJSON] = None

    # Check local ModelRouter if force_llm is requested
    router = ModelRouter()
    planning_chat = None
    actual_model = None
    model_avail = False

    if router.available_models:
        planning_chat = router.get_model("planning")
        actual_model = (
            router.active_models.get("planning", {}).get("actual")
            or getattr(planning_chat, "model_name", None)
            or getattr(planning_chat, "model", None)
            or (router.available_models[0] if router.available_models else "local-model")
        )
        model_avail = router.model_available(actual_model or "")

    if force_llm and planning_chat and model_avail:
        instruction = template.prompt_instruction if template else f"Generate {canonical_label} diagram."
        evidence_summary = ""
        if plan and plan.system_design:
            comps = [c.name for c in plan.system_design.components]
            entities = [e.name for e in plan.system_design.database_schema]
            apis = [f"{a.method} {a.path}" for a in plan.system_design.api_endpoints]
            evidence_summary = f"Components: {comps}. Database Entities: {entities}. APIs: {apis}."
        if analysis:
            evidence_summary += f" Actors: {analysis.actors}."

        prompt_text = f"""You are a software modeling architect.
{instruction}
Evidence context from project: {evidence_summary}

Respond ONLY with valid JSON matching this schema:
{{
  "diagram_type": "{canonical_label}",
  "nodes": [{{"id": "node_1", "data": {{"label": "Node 1"}}}}, {{"id": "node_2", "data": {{"label": "Node 2"}}}}],
  "edges": [{{"id": "e1", "source": "node_1", "target": "node_2", "label": "connection"}}]
}}
Do NOT output markdown backticks, explanations, or prologue. Output ONLY valid JSON.
"""
        last_error = ""
        # Bounded correction attempt with max 2 retries
        for attempt in range(2):
            try:
                curr_prompt = prompt_text if attempt == 0 else f"{prompt_text}\nCorrection requirement: Previous attempt had validation error: {last_error}. Provide valid JSON adhering strictly to schema."
                import time
                t0 = time.time()
                llm_res = planning_chat.invoke(curr_prompt)
                latency_ms = int((time.time() - t0) * 1000)
                content = llm_res.content if hasattr(llm_res, "content") else str(llm_res)

                cleaned = content.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                if cleaned.startswith("```"):
                    cleaned = cleaned[3:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                cleaned = cleaned.strip()

                parsed = json.loads(cleaned)
                is_valid, validation_errors = DiagramValidator.validate(parsed)
                if not is_valid:
                    last_error = str(validation_errors)
                    continue

                res = DiagramJSON.model_validate(parsed)
                generation_method = "llm_inference"
                model_name = actual_model
                logger.info(f"Generated {canonical_id} via real LLM inference ({actual_model}) in {latency_ms}ms")
                break
            except Exception as exc:
                last_error = str(exc)
                logger.warning(f"Diagram LLM generation attempt {attempt + 1} failed: {exc}")
    else:
        if not model_avail:
            logger.info(f"Local model '{actual_model}' unavailable or not requested; relying on grounded evidence extraction.")

    # Grounded evidence extraction from real analysis and plan if LLM was not used or failed
    if not res:
        res = _generate_rule_based_diagram(diagram_type, analysis, plan)
        generation_method = "deterministic_extraction"
        model_name = "grounded_evidence"

    # Fallback safety: ensure non-null DiagramJSON
    if not res:
        res = DiagramJSON(diagram_type=canonical_label, nodes=[_node("node_main", "Core Component", 100, 100)], edges=[])
        generation_method = "deterministic_extraction"
        model_name = "grounded_evidence"

    res.generation_method = generation_method
    res.model_name = model_name
    res.provider = router.provider

    # Adapt nodes and edges to standard React Flow contract
    nodes, edges = adapt_to_react_flow(res, canonical_id)
    res.nodes = nodes
    res.edges = edges
    res.diagram_type = canonical_label

    # Structural and Semantic Validation
    is_valid, validation_errors = DiagramValidator.validate(res)
    if not is_valid:
        logger.warning(f"Diagram '{canonical_id}' failed structural validation: {validation_errors}")

    sem_valid, sem_errors = DiagramValidator.validate_semantic(res, canonical_id)
    if not sem_valid:
        logger.warning(f"Diagram '{canonical_id}' failed semantic validation: {sem_errors}")

    return res


def write_diagram_json(path: str, data: DiagramJSON) -> str:
    norm = normalize_diagram_identifier(data.diagram_type)
    payload = data.model_dump()
    payload["mermaid"] = export_diagram_to_mermaid(data)
    payload["canonical_id"] = norm["id"] if norm else "architecture_diagram"
    payload["diagram_type"] = norm["label"] if norm else data.diagram_type
    payload["generation_method"] = getattr(data, "generation_method", "deterministic_extraction")
    payload["model_name"] = getattr(data, "model_name", None)
    payload["provider"] = getattr(data, "provider", "ollama")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return path


def generate_all_diagrams_for_state(state) -> List[str]:
    """Generates all 10 canonical diagrams for a state and registers both JSON and PNG artifacts."""
    if not state.structured_requirements or not state.project_plan:
        raise ValueError("Diagram generation requires analysis and planning output")

    paths: List[str] = []

    def build_one(diagram_def: Dict[str, Any]) -> List[str]:
        label = diagram_def["label"]
        cid = diagram_def["id"]
        res = generate_diagram_with_llm(cid, state.structured_requirements, state.project_plan)

        # Primary canonical JSON payload with embedded Mermaid
        payload = res.model_dump()
        payload["mermaid"] = export_diagram_to_mermaid(res)
        payload["canonical_id"] = cid
        payload["diagram_type"] = label
        json_content = json.dumps(payload, indent=2)

        # Write canonical file (e.g., architecture.json)
        source_path = f"design/diagram_source/{diagram_def['filename']}"
        write_text_artifact(state, source_path, json_content, "DIAGRAM", "PlanningAgent", diagram_type=label, canonical_id=cid)

        # Write alias file for backward compatibility (e.g., architecture_diagram.json)
        alias_source_path = f"design/diagram_source/{cid}.json"
        if alias_source_path != source_path:
            write_text_artifact(state, alias_source_path, json_content, "DIAGRAM", "PlanningAgent", diagram_type=label, canonical_id=cid)

        # Render PNG visual artifact
        png = timed_call(
            "diagram_rendering",
            lambda: render_diagram_png(res, f"{state.project_name} {label}"),
            project_id=state.project_id,
            agent="PlanningAgent",
            diagram_type=label,
            diagram_json_token_estimate=estimate_tokens(json_content),
        )
        image_path = f"design/diagrams/{diagram_def['png_filename']}"
        write_bytes_artifact(state, image_path, png, "DIAGRAM", "PlanningAgent", diagram_type=label, canonical_id=cid)

        alias_image_path = f"design/diagrams/{cid}.png"
        if alias_image_path != image_path:
            write_bytes_artifact(state, alias_image_path, png, "DIAGRAM", "PlanningAgent", diagram_type=label, canonical_id=cid)

        return [source_path, image_path]

    futures = [diagram_executor.submit(build_one, d_def) for d_def in CANONICAL_DIAGRAM_TYPES]
    for future in as_completed(futures, timeout=DIAGRAM_TIMEOUT_SECONDS):
        paths.extend(future.result())

    return paths


def generate_all_diagrams(project_id: str, domain: str, analysis: AnalysisResult, plan: ProjectPlan) -> List[str]:
    """Test and standalone entrypoint generating all 10 canonical software diagrams."""
    project_name = slugify(domain) or slugify(project_id)
    base_dir = f"generated_projects/{project_name}/design"
    diagrams_dir = f"{base_dir}/diagram_source"
    os.makedirs(diagrams_dir, exist_ok=True)

    paths = []
    for d_def in CANONICAL_DIAGRAM_TYPES:
        res = generate_diagram_with_llm(d_def["id"], analysis, plan)
        canonical_path = os.path.join(diagrams_dir, d_def["filename"])
        write_diagram_json(canonical_path, res)
        paths.append(canonical_path)

        # Write alias file if filename differs from ID
        alias_path = os.path.join(diagrams_dir, f"{d_def['id']}.json")
        if alias_path != canonical_path:
            write_diagram_json(alias_path, res)
            paths.append(alias_path)

    return paths
