from typing import Any, Dict, List, Optional, Set, Tuple
from backend.models.diagram import DiagramEdge, DiagramJSON, DiagramNode


class DiagramValidationError:
    def __init__(self, code: str, message: str, severity: str = "ERROR"):
        self.code = code
        self.message = message
        self.severity = severity

    def to_dict(self) -> Dict[str, str]:
        return {"code": self.code, "message": self.message, "severity": self.severity}


class DiagramValidator:
    """Rigorous structural and semantic validator for software engineering diagrams."""

    @staticmethod
    def validate(diagram: Any) -> Tuple[bool, List[Dict[str, str]]]:
        """Structural validation: nodes, edges, unique IDs, referential integrity."""
        errors: List[DiagramValidationError] = []

        if isinstance(diagram, dict):
            nodes = diagram.get("nodes", [])
            edges = diagram.get("edges", [])
            dtype = diagram.get("diagram_type", "unknown")
        elif hasattr(diagram, "nodes") and hasattr(diagram, "edges"):
            nodes = [n.model_dump() if hasattr(n, "model_dump") else n for n in getattr(diagram, "nodes", [])]
            edges = [e.model_dump() if hasattr(e, "model_dump") else e for e in getattr(diagram, "edges", [])]
            dtype = getattr(diagram, "diagram_type", "unknown")
        else:
            errors.append(DiagramValidationError("INVALID_DATA", "Diagram object must contain nodes and edges collections."))
            return False, [e.to_dict() for e in errors]

        if not nodes:
            errors.append(DiagramValidationError("EMPTY_NODES", f"Diagram '{dtype}' contains 0 nodes."))
            return False, [e.to_dict() for e in errors]

        # 1. Check duplicate node IDs and missing identifiers
        seen_ids: Set[str] = set()
        for idx, node in enumerate(nodes):
            nid = str(node.get("id") if isinstance(node, dict) else getattr(node, "id", "")).strip()
            if not nid:
                errors.append(DiagramValidationError("MISSING_NODE_ID", f"Node at index {idx} has an empty identifier."))
                continue
            if nid in seen_ids:
                errors.append(DiagramValidationError("DUPLICATE_NODE_ID", f"Duplicate node ID detected: '{nid}'."))
            seen_ids.add(nid)

        # 2. Check edge endpoint referential integrity
        for idx, edge in enumerate(edges):
            src = str(edge.get("source") if isinstance(edge, dict) else getattr(edge, "source", "")).strip()
            tgt = str(edge.get("target") if isinstance(edge, dict) else getattr(edge, "target", "")).strip()
            eid = str(edge.get("id") if isinstance(edge, dict) else getattr(edge, "id", f"edge_{idx}")).strip()

            if not src:
                errors.append(DiagramValidationError("MISSING_EDGE_SOURCE", f"Edge '{eid}' has no source specified."))
            elif src not in seen_ids:
                errors.append(DiagramValidationError("DANGLING_EDGE_SOURCE", f"Edge '{eid}' references non-existent source node: '{src}'."))

            if not tgt:
                errors.append(DiagramValidationError("MISSING_EDGE_TARGET", f"Edge '{eid}' has no target specified."))
            elif tgt not in seen_ids:
                errors.append(DiagramValidationError("DANGLING_EDGE_TARGET", f"Edge '{eid}' references non-existent target node: '{tgt}'."))

        has_errors = any(e.severity == "ERROR" for e in errors)
        return (not has_errors), [e.to_dict() for e in errors]

    @staticmethod
    def validate_semantic(diagram: Any, canonical_id: str) -> Tuple[bool, List[Dict[str, str]]]:
        """Type-specific semantic rule validation."""
        errors: List[DiagramValidationError] = []

        if isinstance(diagram, dict):
            nodes = diagram.get("nodes", [])
            edges = diagram.get("edges", [])
        elif hasattr(diagram, "nodes") and hasattr(diagram, "edges"):
            nodes = [n.model_dump() if hasattr(n, "model_dump") else n for n in getattr(diagram, "nodes", [])]
            edges = [e.model_dump() if hasattr(e, "model_dump") else e for e in getattr(diagram, "edges", [])]
        else:
            return True, []

        clean_type = canonical_id.lower().replace("-", "_")

        # Sequence semantic check: must have at least 2 participants or at least 1 message/edge
        if "sequence" in clean_type:
            if len(nodes) < 2 and not edges:
                errors.append(DiagramValidationError("SEMANTIC_SEQUENCE_TOO_FEW_PARTICIPANTS", "Sequence diagram requires at least 2 participants."))

        # ERD semantic check: entities should have attributes or field definitions
        elif "erd" in clean_type:
            for n in nodes:
                data = n.get("data", {}) if isinstance(n, dict) else getattr(n, "data", {})
                attrs = data.get("attributes", []) if isinstance(data, dict) else []
                fields = data.get("fields", []) if isinstance(data, dict) else []
                if not attrs and not fields and not data.get("columns"):
                    errors.append(DiagramValidationError("SEMANTIC_ERD_MISSING_ATTRIBUTES", f"ERD entity '{n.get('id')}' has no attributes defined.", severity="WARNING"))

        # DFD semantic check: Level 0 should contain at least 1 Process
        elif "dfd_level_0" in clean_type:
            has_process = any(
                (n.get("data", {}).get("type") == "Process" or "process" in str(n.get("id", "")).lower())
                for n in nodes
            )
            if not has_process:
                errors.append(DiagramValidationError("SEMANTIC_DFD_MISSING_PROCESS", "DFD Level 0 must contain at least one Process boundary node."))

        # Deployment semantic check: must declare target nodes with environments or technologies
        elif "deployment" in clean_type:
            if len(nodes) < 2:
                errors.append(DiagramValidationError("SEMANTIC_DEPLOYMENT_TOO_FEW_NODES", "Deployment diagram must define at least 2 infrastructure nodes."))

        has_errors = any(e.severity == "ERROR" for e in errors)
        return (not has_errors), [e.to_dict() for e in errors]

    @staticmethod
    def validate_cross_artifact(diagram: Any, analysis: Optional[Any], plan: Optional[Any]) -> Tuple[bool, List[Dict[str, str]]]:
        """Verifies evidence consistency between diagram elements and structured analysis/plan."""
        errors: List[DiagramValidationError] = []
        if not analysis and not plan:
            return True, []

        if isinstance(diagram, dict):
            nodes = diagram.get("nodes", [])
            dtype = diagram.get("diagram_type", "")
        else:
            nodes = getattr(diagram, "nodes", [])
            dtype = getattr(diagram, "diagram_type", "")

        clean_type = str(dtype).lower().replace("-", "_")

        # Class/ERD entities should align with plan database_schema or analysis entities
        if ("class" in clean_type or "erd" in clean_type) and plan and plan.system_design:
            schema_names = {e.name.lower() for e in plan.system_design.database_schema}
            node_labels = {
                (n.get("data", {}).get("label", "") if isinstance(n, dict) else getattr(n, "data", {}).get("label", "")).split("\n")[0].lower()
                for n in nodes
            }
            if schema_names and not (schema_names & node_labels):
                errors.append(DiagramValidationError("CROSS_ARTIFACT_ENTITY_MISMATCH", "Diagram entities do not match planned database schema.", severity="WARNING"))

        has_errors = any(e.severity == "ERROR" for e in errors)
        return (not has_errors), [e.to_dict() for e in errors]
