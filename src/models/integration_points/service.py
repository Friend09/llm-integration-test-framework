"""Service integration point class for representing service-to-service communications."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from .base import IntegrationPoint


@dataclass
class ServiceIntegrationPoint(IntegrationPoint):
    """Represents a service-to-service integration point in the system."""

    protocol: str = "http"  # Communication protocol (http, grpc, etc.)
    service_name: str = "unknown"  # Name of the target service
    operation_name: str = "unknown"  # Name of the operation/method being called
    is_synchronous: bool = True  # Whether the call is synchronous
    has_retry_logic: bool = False  # Whether retry logic is implemented
    has_circuit_breaker: bool = False  # Whether circuit breaker is implemented
    has_timeout: bool = False  # Whether timeout is configured
    required_services: Set[str] = field(default_factory=set)  # Additional services required
    error_handling_level: float = 0.0  # Score for error handling completeness (0.0 to 1.0)

    def to_dict(self) -> Dict:
        """Convert the service integration point to a dictionary representation."""
        base_dict = super().to_dict()
        service_dict = {
            "protocol": self.protocol,
            "service_name": self.service_name,
            "operation_name": self.operation_name,
            "is_synchronous": self.is_synchronous,
            "has_retry_logic": self.has_retry_logic,
            "has_circuit_breaker": self.has_circuit_breaker,
            "has_timeout": self.has_timeout,
            "required_services": list(self.required_services),
            "error_handling_level": self.error_handling_level
        }
        return {**base_dict, **service_dict}

    @classmethod
    def from_dict(cls, data: Dict) -> "ServiceIntegrationPoint":
        """Create a ServiceIntegrationPoint instance from a dictionary."""
        if "required_services" in data:
            data["required_services"] = set(data["required_services"])
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

        # Complexity from required services
        service_count = len(self.required_services)
        score += min(0.2, service_count * 0.05)  # Cap at 0.2

        # Additional complexity factors
        if self.has_retry_logic:
            score += 0.1
        if self.has_circuit_breaker:
            score += 0.1
        if self.has_timeout:
            score += 0.1

        # Normalize score to 0-1 range
        return min(1.0, score)

    def calculate_risk_score(self) -> float:
        """Calculate risk score based on service integration characteristics."""
        score = 0.0

        # Base risk from error handling completeness
        score += (1.0 - self.error_handling_level) * 0.3

        # Risk from required services
        service_count = len(self.required_services)
        score += min(0.2, service_count * 0.05)  # Cap at 0.2

        # Additional risk factors
        if not self.has_timeout:
            score += 0.15  # No timeout handling
        if not self.has_retry_logic:
            score += 0.15  # No retry mechanism
        if not self.has_circuit_breaker:
            score += 0.1  # No circuit breaker
        if not self.is_synchronous:
            score += 0.1  # Asynchronous complexity

        # Normalize score to 0-1 range
        return min(1.0, score)

    def generate_test_requirements(self) -> List[str]:
        """Generate a list of test requirements for this service integration."""
        requirements = [
            f"Test {self.operation_name} call to {self.service_name} service"
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

        # Resilience tests
        if self.has_retry_logic:
            requirements.extend([
                "Test retry mechanism on failure",
                "Test retry backoff strategy",
                "Test maximum retry limit"
            ])

        if self.has_circuit_breaker:
            requirements.extend([
                "Test circuit breaker triggering",
                "Test circuit breaker recovery",
                "Test partial outage handling"
            ])

        # Dependency tests
        if self.required_services:
            requirements.extend([
                "Test dependency service failures",
                "Test cascading failure scenarios",
                "Test partial system availability"
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
