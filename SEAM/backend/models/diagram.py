from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class DiagramNode(BaseModel):
    id: str
    type: str = "default"  # React Flow node types: 'default', 'input', 'output', 'group'
    data: Dict[str, Any] = Field(default_factory=dict) # e.g., {"label": "Node Label"}
    position: Dict[str, float] = Field(default_factory=lambda: {"x": 0, "y": 0})
    style: Optional[Dict[str, Any]] = None

class DiagramEdge(BaseModel):
    id: str
    source: str
    target: str
    label: Optional[str] = None
    animated: bool = False
    style: Optional[Dict[str, Any]] = None
    type: str = "default" # 'default', 'straight', 'step', 'smoothstep'

class DiagramJSON(BaseModel):
    diagram_type: str
    nodes: List[DiagramNode]
    edges: List[DiagramEdge]
    generation_method: Optional[str] = "deterministic_extraction"
    model_name: Optional[str] = None
    provider: Optional[str] = None
