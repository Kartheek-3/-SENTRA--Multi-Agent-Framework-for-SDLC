from typing import Any, Dict, List, Optional, Tuple
from backend.models.diagram import DiagramEdge, DiagramJSON, DiagramNode


def _ensure_unique_node(
    nodes: List[DiagramNode],
    node_id: str,
    label: str,
    node_type: str = "default",
    **data
) -> DiagramNode:
    for n in nodes:
        if n.id == node_id:
            # Merge extra data
            if isinstance(n.data, dict):
                n.data.update({k: v for k, v in data.items() if v is not None})
            return n
    node_data = {"id": node_id, "label": label, **data}
    node = DiagramNode(
        id=node_id,
        type=node_type,
        data=node_data,
        position={"x": 0.0, "y": 0.0},
    )
    nodes.append(node)
    return node


def _ensure_edge(
    edges: List[DiagramEdge],
    edge_id: str,
    source: str,
    target: str,
    label: Optional[str] = None
) -> None:
    if not source or not target:
        return
    for e in edges:
        if e.source == source and e.target == target and e.label == label:
            return
    edges.append(DiagramEdge(
        id=edge_id,
        source=source,
        target=target,
        label=label or None,
        type="smoothstep",
    ))


def adapt_to_react_flow(data: Any, diagram_type: str) -> Tuple[List[DiagramNode], List[DiagramEdge]]:
    """Converts any of the 10 canonical diagram structured representations into validated React Flow nodes and edges."""
    if isinstance(data, dict):
        d_dict = data
    elif hasattr(data, "model_dump"):
        d_dict = data.model_dump()
    else:
        d_dict = {}

    nodes: List[DiagramNode] = []
    edges: List[DiagramEdge] = []

    # 1. Existing pre-computed nodes/edges if present and structured
    existing_nodes = d_dict.get("nodes", [])
    existing_edges = d_dict.get("edges", [])
    if existing_nodes and isinstance(existing_nodes, list):
        for raw in existing_nodes:
            if isinstance(raw, dict) and "id" in raw:
                raw_data = raw.get("data", {})
                if not isinstance(raw_data, dict):
                    raw_data = {"label": str(raw_data)}
                raw_data.setdefault("id", raw["id"])
                raw_data.setdefault("label", raw.get("name") or raw.get("label") or raw["id"])
                nodes.append(DiagramNode(
                    id=str(raw["id"]),
                    type=raw.get("type", "default"),
                    data=raw_data,
                    position=raw.get("position", {"x": 0.0, "y": 0.0}),
                ))
            elif hasattr(raw, "id"):
                raw_data = getattr(raw, "data", {})
                if not isinstance(raw_data, dict):
                    raw_data = {"label": str(raw_data)}
                raw_data.setdefault("id", getattr(raw, "id"))
                raw_data.setdefault("label", raw_data.get("label") or getattr(raw, "id"))
                nodes.append(DiagramNode(
                    id=str(getattr(raw, "id")),
                    type=getattr(raw, "type", "default"),
                    data=raw_data,
                    position=getattr(raw, "position", {"x": 0.0, "y": 0.0}),
                ))

        for raw_e in existing_edges:
            if isinstance(raw_e, dict) and "source" in raw_e and "target" in raw_e:
                edges.append(DiagramEdge(
                    id=str(raw_e.get("id", f"e_{raw_e['source']}_{raw_e['target']}")),
                    source=str(raw_e["source"]),
                    target=str(raw_e["target"]),
                    label=raw_e.get("label"),
                    type=raw_e.get("type", "smoothstep"),
                ))
            elif hasattr(raw_e, "source") and hasattr(raw_e, "target"):
                edges.append(DiagramEdge(
                    id=str(getattr(raw_e, "id", f"e_{getattr(raw_e, 'source')}_{getattr(raw_e, 'target')}一部")),
                    source=str(getattr(raw_e, "source")),
                    target=str(getattr(raw_e, "target")),
                    label=getattr(raw_e, "label", None),
                    type=getattr(raw_e, "type", "smoothstep"),
                ))

        if nodes:
            return nodes, edges

    dtype = str(diagram_type).lower().replace("-", "_")

    # 2. Architecture: layers & connections
    if "architecture" in dtype or "layers" in d_dict:
        layers = d_dict.get("layers", [])
        for layer in layers:
            layer_name = layer.get("name", "Layer")
            for node in layer.get("nodes", []):
                nid = str(node.get("id"))
                _ensure_unique_node(
                    nodes,
                    nid,
                    node.get("label", nid),
                    "default",
                    type="Component",
                    layer=layer_name,
                    technology=node.get("technology"),
                    responsibility=node.get("responsibility"),
                )
        for conn in d_dict.get("connections", []):
            _ensure_edge(
                edges,
                conn.get("id", f"conn_{conn.get('source')}_{conn.get('target')}"),
                str(conn.get("source")),
                str(conn.get("target")),
                conn.get("label") or conn.get("protocol") or "depends on",
            )

    # 3. Use Case: actors, use_cases, relationships
    elif "use_case" in dtype or "use_cases" in d_dict:
        for actor in d_dict.get("actors", []):
            aid = str(actor.get("id"))
            _ensure_unique_node(nodes, aid, actor.get("name", aid), "input", type="Actor")
        for uc in d_dict.get("use_cases", []):
            uid = str(uc.get("id"))
            _ensure_unique_node(nodes, uid, uc.get("name", uid), "default", type="UseCase", description=uc.get("description"))
        for rel in d_dict.get("relationships", []):
            _ensure_edge(
                edges,
                f"rel_{rel.get('actor')}_{rel.get('use_case')}",
                str(rel.get("actor")),
                str(rel.get("use_case")),
                rel.get("relationship", "performs"),
            )

    # 4. Class: classes & relationships
    elif "class" in dtype and "objects" not in d_dict:
        for cls in d_dict.get("classes", []):
            cid = str(cls.get("id"))
            attrs = [f"{a.get('name')}: {a.get('type')}" for a in cls.get("attributes", []) if isinstance(a, dict)]
            methods = [f"{m.get('name')}(): {m.get('return_type')}" for m in cls.get("methods", []) if isinstance(m, dict)]
            _ensure_unique_node(
                nodes,
                cid,
                cls.get("name", cid),
                "default",
                type="Class",
                attributes=attrs,
                methods=methods,
            )
        for rel in d_dict.get("relationships", []):
            _ensure_edge(
                edges,
                f"rel_{rel.get('source')}_{rel.get('target')}",
                str(rel.get("source")),
                str(rel.get("target")),
                rel.get("type", "relates to"),
            )

    # 5. Object: objects & links
    elif "object" in dtype:
        for obj in d_dict.get("objects", []):
            oid = str(obj.get("id"))
            _ensure_unique_node(
                nodes,
                oid,
                obj.get("label") or f"{obj.get('class_name')} instance",
                "default",
                type="Object",
                className=obj.get("class_name"),
                attributes=obj.get("attributes", {}),
            )
        for link in d_dict.get("links", []):
            _ensure_edge(
                edges,
                f"link_{link.get('source')}_{link.get('target')}",
                str(link.get("source")),
                str(link.get("target")),
                link.get("label", "references"),
            )

    # 6. Sequence: participants & messages
    elif "sequence" in dtype:
        for p in d_dict.get("participants", []):
            pid = str(p.get("id"))
            _ensure_unique_node(nodes, pid, p.get("name", pid), "default", type="Participant")
        for msg in d_dict.get("messages", []):
            _ensure_edge(
                edges,
                msg.get("id", f"msg_{msg.get('from_node')}_{msg.get('to_node')}"),
                str(msg.get("from_node")),
                str(msg.get("to_node")),
                msg.get("message", "call"),
            )

    # 7. Activity: activity_nodes & flows
    elif "activity" in dtype:
        for act in d_dict.get("activity_nodes", []):
            aid = str(act.get("id"))
            _ensure_unique_node(nodes, aid, act.get("label", aid), "default", type="ActivityStep")
        for flow in d_dict.get("flows", []):
            _ensure_edge(
                edges,
                f"flow_{flow.get('source')}_{flow.get('target')}",
                str(flow.get("source")),
                str(flow.get("target")),
                flow.get("condition") or "next",
            )

    # 8. DFD Level 0: external_entities, processes, data_flows
    elif "dfd_level_0" in dtype or ("external_entities" in d_dict and "data_stores" not in d_dict):
        for ent in d_dict.get("external_entities", []):
            eid = str(ent.get("id"))
            _ensure_unique_node(nodes, eid, ent.get("name", eid), "input", type="ExternalEntity")
        for proc in d_dict.get("processes", []):
            pid = str(proc.get("id"))
            _ensure_unique_node(nodes, pid, proc.get("name", pid), "default", type="Process")
        for df in d_dict.get("data_flows", []):
            _ensure_edge(
                edges,
                f"df_{df.get('source')}_{df.get('target')}",
                str(df.get("source")),
                str(df.get("target")),
                df.get("label", "data flow"),
            )

    # 9. DFD Level 1: external_entities, processes, data_stores, data_flows
    elif "dfd_level_1" in dtype or "data_stores" in d_dict:
        for ent in d_dict.get("external_entities", []):
            eid = str(ent.get("id"))
            _ensure_unique_node(nodes, eid, ent.get("name", eid), "input", type="ExternalEntity")
        for proc in d_dict.get("processes", []):
            pid = str(proc.get("id"))
            _ensure_unique_node(nodes, pid, proc.get("name", pid), "default", type="Process")
        for ds in d_dict.get("data_stores", []):
            did = str(ds.get("id"))
            _ensure_unique_node(nodes, did, ds.get("name", did), "output", type="DataStore")
        for df in d_dict.get("data_flows", []):
            _ensure_edge(
                edges,
                f"df1_{df.get('source')}_{df.get('target')}",
                str(df.get("source")),
                str(df.get("target")),
                df.get("label", "data flow"),
            )

    # 10. ERD: entities & relationships
    elif "erd" in dtype:
        for ent in d_dict.get("entities", []):
            eid = str(ent.get("id"))
            columns = [f"{c.get('name')} ({c.get('type')})" for c in ent.get("columns", []) if isinstance(c, dict)]
            _ensure_unique_node(
                nodes,
                eid,
                ent.get("name", eid),
                "default",
                type="DatabaseEntity",
                attributes=columns,
            )
        for rel in d_dict.get("relationships", []):
            _ensure_edge(
                edges,
                f"rel_{rel.get('source')}_{rel.get('target')}",
                str(rel.get("source")),
                str(rel.get("target")),
                rel.get("foreign_key") or rel.get("type", "relates to"),
            )

    # 11. Deployment: deployment_nodes & connections
    elif "deployment" in dtype:
        for node in d_dict.get("deployment_nodes", []):
            nid = str(node.get("id"))
            _ensure_unique_node(
                nodes,
                nid,
                node.get("name", nid),
                "default",
                type="DeploymentNode",
                technology=node.get("technology"),
                environment=node.get("environment"),
                status=node.get("status"),
            )
        for conn in d_dict.get("connections", []):
            _ensure_edge(
                edges,
                f"conn_{conn.get('source')}_{conn.get('target')}",
                str(conn.get("source")),
                str(conn.get("target")),
                f"{conn.get('protocol', 'TCP')}:{conn.get('port', '')}".rstrip(":"),
            )

    return nodes, edges
