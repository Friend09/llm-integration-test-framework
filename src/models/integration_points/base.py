"""Base class for integration points in the system."""

from dataclasses import dataclass, field
from typing import Dict, Optional, List
from uuid import UUID, uuid4


@dataclass
class IntegrationPoint:
    """Base class for representing integration points in the system."""

    name: str
    location: str  # file path or module path
    integration_type: str  # API, Database, Service, etc.
    source_component: str  # Component that contains this integration point
    target_component: str  # Component being integrated with
    complexity_score: float = 0.0
    risk_score: float = 0.0
    metadata: Dict[str, str] = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    description: Optional[str] = None
    test_requirements: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert the integration point to a dictionary representation."""
        return {
            "id": str(self.id),
            "name": self.name,
            "location": self.location,
            "integration_type": self.integration_type,
            "source_component": self.source_component,
            "target_component": self.target_component,
            "complexity_score": self.complexity_score,
            "risk_score": self.risk_score,
            "metadata": self.metadata,
            "description": self.description,
            "test_requirements": self.test_requirements
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "IntegrationPoint":
        """Create an IntegrationPoint instance from a dictionary."""
        data["id"] = UUID(data["id"]) if isinstance(data["id"], str) else data["id"]
        return cls(**data)

    def update_scores(self, complexity: float, risk: float) -> None:
        """Update the complexity and risk scores of the integration point."""
        if not 0.0 <= complexity <= 1.0 or not 0.0 <= risk <= 1.0:
            raise ValueError("Scores must be between 0.0 and 1.0")
        self.complexity_score = complexity
        self.risk_score = risk

    def add_test_requirement(self, requirement: str) -> None:
        """Add a test requirement for this integration point."""
        if requirement not in self.test_requirements:
            self.test_requirements.append(requirement)

    def add_metadata(self, key: str, value: str) -> None:
        """Add metadata information to the integration point."""
        self.metadata[key] = value

    def get_metadata(self, key: str) -> Optional[str]:
        """Get metadata value for the given key."""
        return self.metadata.get(key)

    def calculate_priority_score(self) -> float:
        """Calculate the overall priority score for testing this integration point."""
        return (self.complexity_score + self.risk_score) / 2.0

    def __hash__(self) -> int:
        """Make IntegrationPoint hashable using its ID."""
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        """Compare integration points using their IDs."""
        if not isinstance(other, IntegrationPoint):
            return NotImplemented
        return self.id == other.id
