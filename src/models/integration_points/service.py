"""Service integration point model."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from .base import IntegrationPoint


@dataclass
class ServiceIntegrationPoint(IntegrationPoint):
    """Represents a service integration point."""
    protocol: str = field(default="http")
    service_name: str = field(default="unknown")
    is_synchronous: bool = field(default=True)
    has_timeout: bool = field(default=False)
    required_services: Set[str] = field(default_factory=set)
    error_handling_level: float = field(default=0.0)

    def to_dict(self) -> Dict:
        """Convert the service integration point to a dictionary representation."""
        base_dict = super().to_dict()
        service_dict = {
            "protocol": self.protocol,
            "service_name": self.service_name,
            "is_synchronous": self.is_synchronous,
            "has_timeout": self.has_timeout
        }
        return {**base_dict, **service_dict}

    @classmethod
    def from_dict(cls, data: Dict) -> "ServiceIntegrationPoint":
        """Create a ServiceIntegrationPoint instance from a dictionary."""
        return cls(**data)

    def calculate_complexity_score(self) -> float:
        """Calculate complexity score based on service integration characteristics."""
        score = 0.0

        # Base complexity from protocol
        if self.protocol == "grpc":
            score += 0.2
        elif self.protocol == "custom":
            score += 0.3

        # Complexity from synchronization type
        if not self.is_synchronous:
            score += 0.2

        # Additional complexity factors
        if self.has_timeout:
            score += 0.1

        # Normalize score to 0-1 range
        return min(1.0, score)

    def calculate_risk_score(self) -> float:
        """Calculate risk score based on service integration characteristics."""
        score = 0.0

        # Base risk from error handling completeness
        score += 0.3

        # Additional risk factors
        if not self.has_timeout:
            score += 0.15  # No timeout handling

        # Normalize score to 0-1 range
        return min(1.0, score)

    def generate_test_requirements(self) -> List[str]:
        """Generate a list of test requirements for this service integration."""
        requirements = [
            f"Test {self.service_name} service communication"
        ]

        # Basic communication tests
        requirements.extend([
            "Test successful service communication",
            "Test service unavailable scenario",
            f"Test {self.protocol} protocol handling"
        ])

        # Timing and synchronization tests
        if self.has_timeout:
            requirements.append("Test timeout handling")
        if not self.is_synchronous:
            requirements.extend([
                "Test asynchronous response handling",
                "Test callback processing",
                "Test message ordering"
            ])

        # Error handling tests
        requirements.extend([
            "Test error response handling",
            "Test network error scenarios",
            "Test invalid response handling"
        ])

        return requirements

    def add_required_service(self, service_name: str) -> None:
        """Add a required service dependency."""
        self.required_services.add(service_name)

    def update_error_handling_level(self, level: float) -> None:
        """Update the error handling completeness level."""
        if not 0.0 <= level <= 1.0:
            raise ValueError("Error handling level must be between 0.0 and 1.0")
        self.error_handling_level = level
