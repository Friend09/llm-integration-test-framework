"""Relationship class for representing dependencies between components."""

from dataclasses import dataclass, field
from typing import Dict, Optional
from uuid import UUID, uuid4

from .component import Component


@dataclass
class Relationship:
    """Represents a relationship/dependency between two components."""

    source: Component
    target: Component
    relationship_type: str  # inheritance, association, aggregation, etc.
    strength: float = 1.0  # relationship strength/importance (0.0 to 1.0)
    metadata: Dict[str, str] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    description: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert the relationship to a dictionary representation."""
        return {
            "id": str(self.id),
            "source_id": str(self.source.id),
            "target_id": str(self.target.id),
            "relationship_type": self.relationship_type,
            "strength": self.strength,
            "metadata": self.metadata,
            "description": self.description
        }

    @classmethod
    def from_dict(cls, data: Dict, components: Dict[str, Component]) -> "Relationship":
        """Create a Relationship instance from a dictionary and component map."""
        source = components[data["source_id"]]
        target = components[data["target_id"]]
        relationship_data = {
            "source": source,
            "target": target,
            "relationship_type": data["relationship_type"],
            "strength": data["strength"],
            "metadata": data.get("metadata", {}),
            "description": data.get("description"),
            "id": UUID(data["id"]) if isinstance(data["id"], str) else data["id"]
        }
        return cls(**relationship_data)

    def update_strength(self, strength: float) -> None:
        """Update the relationship strength."""
        if not 0.0 <= strength <= 1.0:
            raise ValueError("Strength must be between 0.0 and 1.0")
        self.strength = strength

    def add_metadata(self, key: str, value: str) -> None:
        """Add metadata information to the relationship."""
        self.metadata[key] = value

    def get_metadata(self, key: str) -> Optional[str]:
        """Get metadata value for the given key."""
        return self.metadata.get(key)

    def __hash__(self) -> int:
        """Make Relationship hashable using its ID."""
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        """Compare relationships using their IDs."""
        if not isinstance(other, Relationship):
            return NotImplemented
        return self.id == other.id
