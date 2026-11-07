import os
import re
import json
from typing import Any, Dict, List, Optional, Tuple, Type
from pydantic import BaseModel, Field

from backend.models.diagram import DiagramEdge, DiagramJSON, DiagramNode
from backend.models.analysis import AnalysisResult
from backend.models.planning import ProjectPlan


# =====================================================================
# 1. CANONICAL DIAGRAM DEFINITIONS AND ALIAS MAPPER
# =====================================================================

CANONICAL_DIAGRAM_TYPES = [
    {
        "id": "architecture_diagram",
        "canonical_name": "architecture",
        "label": "Architecture",
        "category": "High-Level Design",
        "aliases": ["architecture", "architecture_diagram", "architecture-diagram", "arch"],
        "filename": "architecture.json",
        "png_filename": "architecture.png",
    },
    {
        "id": "use_case_diagram",
        "canonical_name": "use_case",
        "label": "Use Case",
        "category": "Behavioral",
        "aliases": ["use_case", "use_case_diagram", "use-case", "use-case-diagram", "usecase", "use_cases"],
        "filename": "use_case.json",
        "png_filename": "use_case.png",
    },
    {
        "id": "class_diagram",
        "canonical_name": "class_diagram",
        "label": "Class Diagram",
        "category": "Structural",
        "aliases": ["class", "class_diagram", "class-diagram", "classes"],
        "filename": "class_diagram.json",
        "png_filename": "class_diagram.png",
    },
    {
        "id": "object_diagram",
        "canonical_name": "object_diagram",
        "label": "Object Diagram",
        "category": "Structural",
        "aliases": ["object", "object_diagram", "object-diagram", "objects"],
        "filename": "object_diagram.json",
        "png_filename": "object_diagram.png",
    },
    {
        "id": "sequence_diagram",
        "canonical_name": "sequence_diagram",
        "label": "Sequence",
        "category": "Behavioral",
        "aliases": ["sequence", "sequence_diagram", "sequence-diagram", "seq"],
        "filename": "sequence_diagram.json",
        "png_filename": "sequence_diagram.png",
    },
    {
        "id": "activity_diagram",
        "canonical_name": "activity_diagram",
        "label": "Activity",
        "category": "Behavioral",
        "aliases": ["activity", "activity_diagram", "activity-diagram", "activities"],
        "filename": "activity_diagram.json",
        "png_filename": "activity_diagram.png",
    },
    {
        "id": "dfd_level_0",
        "canonical_name": "dfd_level_0",
        "label": "DFD Level 0",
        "category": "Data Flow",
        "aliases": ["dfd_level_0", "dfd-level-0", "dfd_0", "dfd0", "dfd level 0", "data_flow_0"],
        "filename": "dfd_level_0.json",
        "png_filename": "dfd_level_0.png",
    },
    {
        "id": "dfd_level_1",
        "canonical_name": "dfd_level_1",
        "label": "DFD Level 1",
        "category": "Data Flow",
        "aliases": ["dfd_level_1", "dfd-level-1", "dfd_1", "dfd1", "dfd level 1", "data_flow_1"],
        "filename": "dfd_level_1.json",
        "png_filename": "dfd_level_1.png",
    },
    {
        "id": "erd_diagram",
        "canonical_name": "erd_diagram",
        "label": "ERD (Database)",
        "category": "Data Architecture",
        "aliases": ["erd", "erd_diagram", "erd-diagram", "entity_relationship", "erd_database", "erd database", "database_erd"],
        "filename": "erd_diagram.json",
        "png_filename": "erd_diagram.png",
    },
    {
        "id": "deployment_diagram",
        "canonical_name": "deployment_diagram",
        "label": "Deployment",
        "category": "Infrastructure",
        "aliases": ["deployment", "deployment_diagram", "deployment-diagram", "infra", "infrastructure"],
        "filename": "deployment_diagram.json",
        "png_filename": "deployment_diagram.png",
    },
]

def _clean_key(s: str) -> str:
    """Normalizes string by stripping non-alphanumeric punctuation and standardizing separators."""
    if not s:
        return ""
    val = s.lower().strip()
    val = re.sub(r'[\(\)\[\]\{\}\'"\.]', '', val)
    val = re.sub(r'[\s\-]+', '_', val)
    return val.strip('_')

_ALIAS_MAP: Dict[str, Dict[str, Any]] = {}
for _def in CANONICAL_DIAGRAM_TYPES:
    # Register ID, canonical_name, label, filename stem
    keys_to_register = [
        _def["id"],
        _def["canonical_name"],
        _def["label"],
        _def["filename"].replace(".json", ""),
        _def["png_filename"].replace(".png", ""),
    ] + _def["aliases"]

    for k in keys_to_register:
        cleaned = _clean_key(k)
        if cleaned:
            _ALIAS_MAP[cleaned] = _def
        _ALIAS_MAP[k.lower().strip()] = _def

def normalize_diagram_identifier(diagram_type: str) -> Optional[Dict[str, Any]]:
    """Normalizes any diagram identifier or legacy alias to the canonical definition."""
    if not diagram_type:
        return None
    raw_clean = diagram_type.lower().strip()
    if raw_clean in _ALIAS_MAP:
        return _ALIAS_MAP[raw_clean]
    cleaned = _clean_key(diagram_type)
    return _ALIAS_MAP.get(cleaned)


# =====================================================================
# 2. TYPE-SPECIFIC PYDANTIC SCHEMAS (10 CANONICAL SCHEMAS)
# =====================================================================

# 1. Architecture
class ArchitectureNode(BaseModel):
    id: str
    label: str
    type: str = "component"
    technology: Optional[str] = None
    responsibility: Optional[str] = None
    source_refs: List[str] = Field(default_factory=list)

class ArchitectureLayer(BaseModel):
    id: str
    name: str
    nodes: List[ArchitectureNode] = Field(default_factory=list)

class ArchitectureConnection(BaseModel):
    id: str
    source: str
    target: str
    label: Optional[str] = "depends on"
    protocol: Optional[str] = None

class ArchitectureDiagramJSON(BaseModel):
    diagram_type: str = "architecture"
    title: str = "Architecture"
    layers: List[ArchitectureLayer] = Field(default_factory=list)
    connections: List[ArchitectureConnection] = Field(default_factory=list)
    nodes: List[DiagramNode] = Field(default_factory=list)
    edges: List[DiagramEdge] = Field(default_factory=list)
    mermaid: Optional[str] = None


# 2. Use Case
class Actor(BaseModel):
    id: str
    name: str
    type: str = "actor"

class UseCase(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    source_refs: List[str] = Field(default_factory=list)

class UseCaseRelationship(BaseModel):
    actor: str
    use_case: str
    relationship: str = "performs"

class UseCaseDiagramJSON(BaseModel):
    diagram_type: str = "use_case"
    actors: List[Actor] = Field(default_factory=list)
    use_cases: List[UseCase] = Field(default_factory=list)
    relationships: List[UseCaseRelationship] = Field(default_factory=list)
    nodes: List[DiagramNode] = Field(default_factory=list)
    edges: List[DiagramEdge] = Field(default_factory=list)
    mermaid: Optional[str] = None


# 3. Class
class ClassAttribute(BaseModel):
    name: str
    type: str = "string"

class ClassMethod(BaseModel):
    name: str
    return_type: str = "void"

class ClassEntity(BaseModel):
    id: str
    name: str
    attributes: List[ClassAttribute] = Field(default_factory=list)
    methods: List[ClassMethod] = Field(default_factory=list)
    source_refs: List[str] = Field(default_factory=list)

class ClassRelationship(BaseModel):
    source: str
    target: str
    type: str = "relates to"

class ClassDiagramJSON(BaseModel):
    diagram_type: str = "class_diagram"
    classes: List[ClassEntity] = Field(default_factory=list)
    relationships: List[ClassRelationship] = Field(default_factory=list)
    nodes: List[DiagramNode] = Field(default_factory=list)
    edges: List[DiagramEdge] = Field(default_factory=list)
    mermaid: Optional[str] = None


# 4. Object
class ObjectEntity(BaseModel):
    id: str
    class_name: str
    label: str
    attributes: Dict[str, Any] = Field(default_factory=dict)

class ObjectLink(BaseModel):
    source: str
    target: str
    label: Optional[str] = "references"

class ObjectDiagramJSON(BaseModel):
    diagram_type: str = "object_diagram"
    objects: List[ObjectEntity] = Field(default_factory=list)
    links: List[ObjectLink] = Field(default_factory=list)
    nodes: List[DiagramNode] = Field(default_factory=list)
    edges: List[DiagramEdge] = Field(default_factory=list)
    mermaid: Optional[str] = None


# 5. Sequence
class Participant(BaseModel):
    id: str
    name: str
    type: str = "participant"

class SequenceMessage(BaseModel):
    id: str
    from_node: str
    to_node: str
    message: str
    kind: str = "call"

class SequenceDiagramJSON(BaseModel):
    diagram_type: str = "sequence_diagram"
    participants: List[Participant] = Field(default_factory=list)
    messages: List[SequenceMessage] = Field(default_factory=list)
    nodes: List[DiagramNode] = Field(default_factory=list)
    edges: List[DiagramEdge] = Field(default_factory=list)
    mermaid: Optional[str] = None


# 6. Activity
class ActivityNode(BaseModel):
    id: str
    type: str = "activity"
    label: str

class ActivityFlow(BaseModel):
    source: str
    target: str
    condition: Optional[str] = None

class ActivityDiagramJSON(BaseModel):
    diagram_type: str = "activity_diagram"
    activity_nodes: List[ActivityNode] = Field(default_factory=list)
    flows: List[ActivityFlow] = Field(default_factory=list)
    nodes: List[DiagramNode] = Field(default_factory=list)
    edges: List[DiagramEdge] = Field(default_factory=list)
    mermaid: Optional[str] = None


# 7. DFD Level 0
class DFDEntity(BaseModel):
    id: str
    name: str

class DFDProcess(BaseModel):
    id: str
    name: str

class DFDDataFlow(BaseModel):
    source: str
    target: str
    label: str

class DFDLevel0DiagramJSON(BaseModel):
    diagram_type: str = "dfd_level_0"
    external_entities: List[DFDEntity] = Field(default_factory=list)
    processes: List[DFDProcess] = Field(default_factory=list)
    data_flows: List[DFDDataFlow] = Field(default_factory=list)
    nodes: List[DiagramNode] = Field(default_factory=list)
    edges: List[DiagramEdge] = Field(default_factory=list)
    mermaid: Optional[str] = None


# 8. DFD Level 1
class DFDDataStore(BaseModel):
    id: str
    name: str

class DFDLevel1DiagramJSON(BaseModel):
    diagram_type: str = "dfd_level_1"
    external_entities: List[DFDEntity] = Field(default_factory=list)
    processes: List[DFDProcess] = Field(default_factory=list)
    data_stores: List[DFDDataStore] = Field(default_factory=list)
    data_flows: List[DFDDataFlow] = Field(default_factory=list)
    nodes: List[DiagramNode] = Field(default_factory=list)
    edges: List[DiagramEdge] = Field(default_factory=list)
    mermaid: Optional[str] = None


# 9. ERD
class ERDColumn(BaseModel):
    name: str
    type: str = "VARCHAR"
    primary_key: bool = False
    nullable: bool = True

class ERDEntity(BaseModel):
    id: str
    name: str
    columns: List[ERDColumn] = Field(default_factory=list)
    source_refs: List[str] = Field(default_factory=list)

class ERDRelationship(BaseModel):
    source: str
    target: str
    type: str = "one_to_many"
    foreign_key: Optional[str] = None

class ERDDiagramJSON(BaseModel):
    diagram_type: str = "erd_diagram"
    entities: List[ERDEntity] = Field(default_factory=list)
    relationships: List[ERDRelationship] = Field(default_factory=list)
    nodes: List[DiagramNode] = Field(default_factory=list)
    edges: List[DiagramEdge] = Field(default_factory=list)
    mermaid: Optional[str] = None


# 10. Deployment
class DeploymentNode(BaseModel):
    id: str
    name: str
    type: str = "container"
    technology: str = "Docker"
    environment: Optional[str] = "Production"
    status: Optional[str] = "configured"

class DeploymentConnection(BaseModel):
    source: str
    target: str
    protocol: str = "HTTP/REST"
    port: Optional[str] = "8000"

class DeploymentDiagramJSON(BaseModel):
    diagram_type: str = "deployment_diagram"
    deployment_nodes: List[DeploymentNode] = Field(default_factory=list)
    connections: List[DeploymentConnection] = Field(default_factory=list)
    nodes: List[DiagramNode] = Field(default_factory=list)
    edges: List[DiagramEdge] = Field(default_factory=list)
    mermaid: Optional[str] = None


# =====================================================================
# 3. DIAGRAM TEMPLATE REGISTRY
# =====================================================================

class DiagramTemplateEntry:
    def __init__(
        self,
        canonical_id: str,
        canonical_name: str,
        label: str,
        category: str,
        schema_class: Type[BaseModel],
        required_fields: List[str],
        prompt_instruction: str,
        frontend_renderer: str = "react_flow",
    ):
        self.canonical_id = canonical_id
        self.canonical_name = canonical_name
        self.label = label
        self.category = category
        self.schema_class = schema_class
        self.required_fields = required_fields
        self.prompt_instruction = prompt_instruction
        self.frontend_renderer = frontend_renderer

    def validate_schema(self, data: Dict[str, Any]) -> BaseModel:
        for f in self.required_fields:
            if f not in data and "nodes" not in data:
                raise ValueError(f"Missing required field '{f}' for diagram '{self.canonical_id}'")
        return self.schema_class.model_validate(data)

    def validate_structural(self, data: Any) -> Tuple[bool, List[Dict[str, str]]]:
        from backend.tools.diagram_validator import DiagramValidator
        return DiagramValidator.validate(data)

    def validate_semantic(self, data: Any) -> Tuple[bool, List[Dict[str, str]]]:
        from backend.tools.diagram_validator import DiagramValidator
        return DiagramValidator.validate_semantic(data, self.canonical_id)

    def export_mermaid(self, data: Any) -> str:
        from backend.tools.diagram_exporter import export_diagram_to_mermaid
        return export_diagram_to_mermaid(data)

    def adapt_for_rendering(self, data: Any) -> Tuple[List[DiagramNode], List[DiagramEdge]]:
        from backend.tools.diagram_adapter import adapt_to_react_flow
        return adapt_to_react_flow(data, self.canonical_id)


class DiagramTemplateRegistry:
    def __init__(self):
        self._templates: Dict[str, DiagramTemplateEntry] = {}
        self._register_all()

    def _register_all(self):
        self._register(
            "architecture_diagram",
            "architecture",
            "Architecture",
            "High-Level Design",
            ArchitectureDiagramJSON,
            ["layers", "connections"],
            "Generate Architecture diagram depicting system components, layers, and service dependencies.",
        )
        self._register(
            "use_case_diagram",
            "use_case",
            "Use Case",
            "Behavioral",
            UseCaseDiagramJSON,
            ["actors", "use_cases"],
            "Generate Use Case diagram showing primary actors, core functional requirements, and actions.",
        )
        self._register(
            "class_diagram",
            "class_diagram",
            "Class Diagram",
            "Structural",
            ClassDiagramJSON,
            ["classes", "relationships"],
            "Generate Class diagram representing domain entities, key attributes, and data relationships.",
        )
        self._register(
            "object_diagram",
            "object_diagram",
            "Object Diagram",
            "Structural",
            ObjectDiagramJSON,
            ["objects", "links"],
            "Generate Object diagram depicting concrete runtime instances and sample attribute values.",
        )
        self._register(
            "sequence_diagram",
            "sequence_diagram",
            "Sequence",
            "Behavioral",
            SequenceDiagramJSON,
            ["participants", "messages"],
            "Generate Sequence diagram showing actor-component interactions, API calls, and responses.",
        )
        self._register(
            "activity_diagram",
            "activity_diagram",
            "Activity",
            "Behavioral",
            ActivityDiagramJSON,
            ["activity_nodes", "flows"],
            "Generate Activity diagram demonstrating the sequential workflow execution across task stages.",
        )
        self._register(
            "dfd_level_0",
            "dfd_level_0",
            "DFD Level 0",
            "Data Flow",
            DFDLevel0DiagramJSON,
            ["external_entities", "processes", "data_flows"],
            "Generate Context DFD (Level 0) showing external entities, core process boundary, and data stores.",
        )
        self._register(
            "dfd_level_1",
            "dfd_level_1",
            "DFD Level 1",
            "Data Flow",
            DFDLevel1DiagramJSON,
            ["external_entities", "processes", "data_stores", "data_flows"],
            "Generate Detailed DFD (Level 1) decomposing system APIs and flows into respective data stores.",
        )
        self._register(
            "erd_diagram",
            "erd_diagram",
            "ERD (Database)",
            "Data Architecture",
            ERDDiagramJSON,
            ["entities", "relationships"],
            "Generate Entity Relationship Diagram (ERD) capturing database tables, primary/foreign keys, and cardinalities.",
        )
        self._register(
            "deployment_diagram",
            "deployment_diagram",
            "Deployment",
            "Infrastructure",
            DeploymentDiagramJSON,
            ["deployment_nodes", "connections"],
            "Generate Deployment diagram detailing execution nodes, containers, exposed ports, and network protocols.",
        )

    def _register(
        self,
        canonical_id: str,
        canonical_name: str,
        label: str,
        category: str,
        schema_class: Type[BaseModel],
        required_fields: List[str],
        prompt_instruction: str,
    ):
        entry = DiagramTemplateEntry(
            canonical_id=canonical_id,
            canonical_name=canonical_name,
            label=label,
            category=category,
            schema_class=schema_class,
            required_fields=required_fields,
            prompt_instruction=prompt_instruction,
        )
        self._templates[canonical_id] = entry

    def get_template(self, diagram_type: str) -> Optional[DiagramTemplateEntry]:
        norm = normalize_diagram_identifier(diagram_type)
        if not norm:
            return None
        return self._templates.get(norm["id"])

    def list_templates(self) -> List[DiagramTemplateEntry]:
        return list(self._templates.values())


registry = DiagramTemplateRegistry()


# =====================================================================
# 4. DIAGRAM SELECTION SERVICE
# =====================================================================

class DiagramSelectionService:
    """Authoritative service for resolving and selecting canonical diagram types from requirements or aliases."""

    @staticmethod
    def select_diagram(diagram_type: str) -> Optional[DiagramTemplateEntry]:
        return registry.get_template(diagram_type)

    @staticmethod
    def list_canonical_diagrams() -> List[Dict[str, Any]]:
        return list(CANONICAL_DIAGRAM_TYPES)

    @staticmethod
    def resolve_canonical_id(diagram_type: str) -> Optional[str]:
        norm = normalize_diagram_identifier(diagram_type)
        return norm["id"] if norm else None

    @staticmethod
    def is_valid_diagram_type(diagram_type: str) -> bool:
        return normalize_diagram_identifier(diagram_type) is not None
