"""Component model."""
from dataclasses import dataclass
from typing import Optional

@dataclass
class Component:
    """Represents a component in the system."""
    name: str
    component_type: str
    location: str
    complexity_score: float
    importance_score: float
    description: Optional[str] = None
