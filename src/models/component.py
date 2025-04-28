"""Component class for representing system components in the dependency analysis."""

from dataclasses import dataclass, field
from typing import Dict, Optional, List
from uuid import UUID, uuid4


@dataclass
class Component:
    """Represents a system component (module, class, function) in the codebase."""

    name: str
    component_type: str  # module, class, function, etc.
    location: str  # file path or module path
    metadata: Dict[str, str] = field(default_factory=dict)
    complexity_score: float = 0.0
    importance_score: float = 0.0
    id: UUID = field(default_factory=uuid4)
    description: Optional[str] = None
    integration_points: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert the component to a dictionary representation."""
        return {
            "id": str(self.id),
            "name": self.name,
            "component_type": self.component_type,
            "location": self.location,
            "metadata": self.metadata,
            "complexity_score": self.complexity_score,
            "importance_score": self.importance_score,
            "description": self.description,
            "integration_points": self.integration_points
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Component":
        """Create a Component instance from a dictionary."""
        data["id"] = UUID(data["id"]) if isinstance(data["id"], str) else data["id"]
        return cls(**data)

    def update_scores(self, complexity: float, importance: float) -> None:
        """Update the complexity and importance scores of the component."""
        self.complexity_score = complexity
        self.importance_score = importance

    def add_integration_point(self, integration_point: str) -> None:
        """Add an integration point to the component."""
        if integration_point not in self.integration_points:
            self.integration_points.append(integration_point)

    def add_metadata(self, key: str, value: str) -> None:
        """Add metadata information to the component."""
        self.metadata[key] = value

    def get_metadata(self, key: str) -> Optional[str]:
        """Get metadata value for the given key."""
        return self.metadata.get(key)

    def __hash__(self) -> int:
        """Make Component hashable using its ID."""
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        """Compare components using their IDs."""
        if not isinstance(other, Component):
            return NotImplemented
        return self.id == other.id
