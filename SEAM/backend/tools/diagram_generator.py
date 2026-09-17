import os
import json
import struct
import zlib
from concurrent.futures import as_completed
from langchain_core.prompts import PromptTemplate
from backend.models.analysis import AnalysisResult
from backend.models.planning import ProjectPlan
from backend.models.diagram import DiagramEdge, DiagramJSON, DiagramNode
from backend.llm.model_router import ModelRouter
from langchain_core.output_parsers import PydanticOutputParser
from backend.utils import slugify
from backend.tools.artifact_pipeline import write_bytes_artifact, write_text_artifact
from backend.concurrency import diagram_executor
from backend.config import DIAGRAM_TIMEOUT_SECONDS
from backend.performance import estimate_tokens, timed_call, timed_llm_call

DIAGRAM_PROMPT = """
You are an expert software architect.
Generate a structured JSON visual diagram representation for a {diagram_type} diagram.
Do NOT use PlantUML. Produce React Flow compatible JSON with 'nodes' and 'edges' according to the schema.

Context:
System Overview: {overview}
Components: {components}
Actors: {actors}
API Endpoints: {apis}

Provide logical coordinates (x, y) for nodes so they are laid out readably.

{format_instructions}
"""

def generate_diagram_with_llm(diagram_type: str, analysis: AnalysisResult, plan: ProjectPlan) -> DiagramJSON:
    deterministic = _generate_rule_based_diagram(diagram_type, analysis, plan)
    if deterministic:
        return deterministic

    router = ModelRouter()
    llm = router.get_model("planning")
    parser = PydanticOutputParser(pydantic_object=DiagramJSON)
    
    prompt = PromptTemplate(
        template=DIAGRAM_PROMPT,
        input_variables=["diagram_type", "overview", "components", "actors", "apis"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    
    chain = prompt | llm | parser
    
    components = ", ".join([c.name for c in plan.system_design.components]) if plan and plan.system_design else ""
    apis = ", ".join([a.path for a in plan.system_design.api_endpoints]) if plan and plan.system_design else ""
    
    inputs = {
        "diagram_type": diagram_type,
        "overview": plan.project_overview if plan else "",
        "components": components,
        "actors": ", ".join(analysis.actors) if analysis else "",
        "apis": apis
    }
    res = timed_llm_call(
        lambda: chain.invoke(inputs),
        agent="PlanningAgent",
        operation="diagram_generation",
        diagram_type=diagram_type,
        model=router.active_models.get("planning", {}).get("actual"),
        input_token_estimate=estimate_tokens(inputs),
        timeout_seconds=DIAGRAM_TIMEOUT_SECONDS,
        retry_count=0,
    )
    
    # Ensure all nodes and edges have required fields
    return res


def _node(node_id: str, label: str, x: int, y: int, node_type: str = "default", **data) -> DiagramNode:
    return DiagramNode(
        id=node_id,
        type=node_type,
        data={"label": label, **data},
        position={"x": x, "y": y},
    )


def _edge(edge_id: str, source: str, target: str, label: str = "") -> DiagramEdge:
    return DiagramEdge(id=edge_id, source=source, target=target, label=label or None, type="smoothstep")


def _entity_nodes(plan: ProjectPlan) -> list[DiagramNode]:
    entities = plan.system_design.database_schema if plan and plan.system_design else []
    if not entities:
        entities = []
    nodes = []
    for index, entity in enumerate(entities):
        fields = "\\n".join(entity.fields[:8]) or "id"
        label = f"{entity.name}\\n----------------\\n{fields}"
        nodes.append(_node(f"class_{slugify(entity.name)}", label, 90 + (index % 3) * 470, 150 + (index // 3) * 210, "default", kind="class", fields=entity.fields, relationships=entity.relationships))
    return nodes


def _generate_rule_based_diagram(diagram_type: str, analysis: AnalysisResult, plan: ProjectPlan) -> DiagramJSON | None:
    kind = diagram_type.lower()
    entities = plan.system_design.database_schema if plan and plan.system_design else []
    actors = analysis.actors if analysis else []
    components = plan.system_design.components if plan and plan.system_design else []
    apis = plan.system_design.api_endpoints if plan and plan.system_design else []

    if kind == "architecture":
        nodes = []
        for index, component in enumerate(components):
            nodes.append(_node(
                f"component_{slugify(component.component_id or component.name)}",
                f"{component.name}\\n{component.responsibility[:44]}",
                110 + (index % 3) * 520,
                150 + (index // 3) * 210,
                "default",
                kind="component",
                technologies=component.technologies,
            ))
        if not nodes:
            nodes = [_node("component_app", plan.project_overview[:40] if plan else "Application", 650, 260, "default", kind="component")]
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

    if kind == "use case":
        actor_names = actors[:3] or ["User"]
        nodes = [_node(f"actor_{index}", actor, 90, 160 + index * 170, "input", kind="actor") for index, actor in enumerate(actor_names)]
        requirements = analysis.functional_requirements if analysis else []
        for index, req in enumerate(requirements[:8]):
            nodes.append(_node(f"usecase_{index}", f"{req.id}\\n{req.description[:46]}", 540 + (index % 2) * 460, 130 + (index // 2) * 145, "default", kind="use_case"))
        edges = []
        usecases = [node for node in nodes if node.data.get("kind") == "use_case"]
        for index, usecase in enumerate(usecases):
            edges.append(_edge(f"usecase_actor_{index}", f"actor_{index % len(actor_names)}", usecase.id, "performs"))
        return DiagramJSON(diagram_type="Use Case", nodes=nodes, edges=edges)

    if kind == "class":
        nodes = _entity_nodes(plan)
        if not nodes:
            nodes = [_node(f"class_{slugify(entity)}", f"{entity}\\n----------------\\nid\\nname", 90 + index * 470, 150, "default", kind="class") for index, entity in enumerate((analysis.entities if analysis else [])[:3])]
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

    if kind == "object":
        base_entities = entities or []
        if not base_entities and analysis:
            base_entities = [type("Entity", (), {"name": name, "fields": ["id", "name"], "relationships": []}) for name in analysis.entities[:4]]
        nodes = []
        for index, entity in enumerate(base_entities[:6]):
            fields = getattr(entity, "fields", []) or ["id", "name"]
            values = "\\n".join(f"{field}: sample_{slugify(field)}" for field in fields[:5])
            nodes.append(_node(f"object_{slugify(entity.name)}_{index}", f"{entity.name} instance\\n----------------\\n{values}", 90 + (index % 3) * 470, 150 + (index // 3) * 220, "default", kind="object"))
        edges = [_edge(f"object_link_{index}", nodes[index].id, nodes[index + 1].id, "references") for index in range(len(nodes) - 1)]
        return DiagramJSON(diagram_type="Object", nodes=nodes, edges=edges)

    if kind == "sequence":
        actor = actors[0] if actors else "User"
        participants = [_node("seq_actor", actor, 80, 160, "input", kind="participant")]
        for index, component in enumerate(components[:4]):
            participants.append(_node(f"seq_{slugify(component.name)}", component.name, 380 + index * 330, 160, "default", kind="participant"))
        if len(participants) == 1:
            participants.extend([
                _node("seq_frontend", "Frontend", 380, 160, "default", kind="participant"),
                _node("seq_api", "API", 710, 160, "default", kind="participant"),
                _node("seq_db", "Database", 1040, 160, "output", kind="participant"),
            ])
        edges = []
        for index in range(len(participants) - 1):
            edges.append(_edge(f"seq_call_{index}", participants[index].id, participants[index + 1].id, apis[index].path if index < len(apis) else "request"))
        for index in range(len(participants) - 1, 0, -1):
            edges.append(_edge(f"seq_return_{index}", participants[index].id, participants[index - 1].id, "response"))
        return DiagramJSON(diagram_type="Sequence", nodes=participants, edges=edges)

    if kind == "activity":
        activity_steps = ["Start"]
        activity_steps.extend([task.title for task in (plan.tasks[:6] if plan else [])])
        activity_steps.append("QA and Delivery")
        nodes = [_node(f"activity_{index}", step[:48], 140 + (index % 3) * 500, 150 + (index // 3) * 190, "default", kind="activity") for index, step in enumerate(activity_steps)]
        edges = [_edge(f"activity_flow_{index}", nodes[index].id, nodes[index + 1].id, "next") for index in range(len(nodes) - 1)]
        return DiagramJSON(diagram_type="Activity", nodes=nodes, edges=edges)

    if kind == "dfd level 0":
        actor_names = actors[:3] or ["User"]
        nodes = [_node(f"actor_{index}", actor, 90, 180 + index * 190, "input", kind="external_entity") for index, actor in enumerate(actor_names)]
        nodes.append(_node("process_system", plan.project_overview[:34] if plan else "Application System", 700, 270, "default", kind="process"))
        stores = entities[:3]
        for index, entity in enumerate(stores):
            nodes.append(_node(f"store_{slugify(entity.name)}", f"{entity.name} Store", 1280, 180 + index * 190, "output", kind="data_store"))
        edges = []
        for index, actor in enumerate(actor_names):
            edges.append(_edge(f"dfd0_in_{index}", f"actor_{index}", "process_system", "request/input"))
            edges.append(_edge(f"dfd0_out_{index}", "process_system", f"actor_{index}", "response/output"))
        for index, entity in enumerate(stores):
            edges.append(_edge(f"dfd0_store_{index}", "process_system", f"store_{slugify(entity.name)}", "read/write data"))
        return DiagramJSON(diagram_type="DFD Level 0", nodes=nodes, edges=edges)

    if kind == "dfd level 1":
        nodes = []
        for index, api in enumerate(apis[:6]):
            nodes.append(_node(f"process_{index}", f"{api.method} {api.path}\\n{api.purpose[:40]}", 430 + (index % 2) * 430, 140 + (index // 2) * 190, "default", kind="process"))
        if not nodes:
            for index, task in enumerate(plan.tasks[:6] if plan else []):
                nodes.append(_node(f"process_{index}", task.title[:42], 430 + (index % 2) * 430, 140 + (index // 2) * 190, "default", kind="process"))
        nodes.insert(0, _node("external_user", actors[0] if actors else "User", 90, 280, "input", kind="external_entity"))
        for index, entity in enumerate(entities[:3]):
            nodes.append(_node(f"store_{slugify(entity.name)}", f"{entity.name} Store", 1320, 180 + index * 190, "output", kind="data_store"))
        edges = []
        process_nodes = [node for node in nodes if node.data.get("kind") == "process"]
        for index, node in enumerate(process_nodes):
            edges.append(_edge(f"dfd1_user_{index}", "external_user", node.id, "request"))
            if entities:
                store = f"store_{slugify(entities[index % len(entities)].name)}"
                edges.append(_edge(f"dfd1_store_{index}", node.id, store, "read/write"))
            edges.append(_edge(f"dfd1_response_{index}", node.id, "external_user", "response"))
        return DiagramJSON(diagram_type="DFD Level 1", nodes=nodes, edges=edges)

    return None

def write_diagram_json(path: str, data: DiagramJSON) -> str:
    with open(path, "w", encoding="utf-8") as f:
        f.write(data.model_dump_json(indent=2))
    return path

def _chunk(tag: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def _png(width: int, height: int, pixels: bytearray) -> bytes:
    rows = bytearray()
    stride = width * 3
    for y in range(height):
        rows.append(0)
        rows.extend(pixels[y * stride:(y + 1) * stride])
    return b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) + _chunk(b"IDAT", zlib.compress(bytes(rows), 9)) + _chunk(b"IEND", b"")


def _draw_rect(pixels: bytearray, width: int, height: int, x: int, y: int, w: int, h: int, color: tuple[int, int, int], fill: tuple[int, int, int] | None = None):
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
    " ": ["00000"] * 7, "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"], "_": ["00000", "00000", "00000", "00000", "00000", "00000", "11111"], "/": ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
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


def generate_all_diagrams_for_state(state) -> list:
    if not state.structured_requirements or not state.project_plan:
        raise ValueError("Diagram generation requires analysis and planning output")
    diagram_types = [
        ("Architecture", "architecture"),
        ("Use Case", "use_case"),
        ("Class", "class_diagram"),
        ("Object", "object_diagram"),
        ("Sequence", "sequence_diagram"),
        ("Activity", "activity_diagram"),
        ("DFD Level 0", "dfd_level_0"),
        ("DFD Level 1", "dfd_level_1"),
    ]
    def build_one(label: str, name: str) -> list[str]:
        res = generate_diagram_with_llm(label, state.structured_requirements, state.project_plan)
        json_content = res.model_dump_json(indent=2)
        source_path = f"design/diagram_source/{name}.json"
        image_path = f"design/diagrams/{name}.png"
        write_text_artifact(state, source_path, json_content, "DIAGRAM", "PlanningAgent", diagram_type=label)
        png = timed_call(
            "diagram_rendering",
            lambda: render_diagram_png(res, f"{state.project_name} {label}"),
            project_id=state.project_id,
            agent="PlanningAgent",
            diagram_type=label,
            diagram_json_token_estimate=estimate_tokens(json_content),
        )
        write_bytes_artifact(state, image_path, png, "DIAGRAM", "PlanningAgent", diagram_type=label)
        return [source_path, image_path]

    paths = []
    futures = [diagram_executor.submit(build_one, label, name) for label, name in diagram_types]
    for future in as_completed(futures, timeout=DIAGRAM_TIMEOUT_SECONDS):
        paths.extend(future.result())
    return paths


def generate_all_diagrams(project_id: str, domain: str, analysis: AnalysisResult, plan: ProjectPlan) -> list:
    project_name = slugify(domain) or slugify(project_id)
    base_dir = f"generated_projects/{project_name}/design"
    diagrams_dir = f"{base_dir}/diagram_source"
    os.makedirs(diagrams_dir, exist_ok=True)
    paths = []
    for dt in ["Architecture", "Use Case", "Class", "Object", "Sequence", "Activity", "DFD Level 0", "DFD Level 1"]:
        res = generate_diagram_with_llm(dt, analysis, plan)
        fname = slugify(dt) + ".json"
        paths.append(write_diagram_json(f"{diagrams_dir}/{fname}", res))
    return paths
