"""API integration point class for representing API endpoints and integrations."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .base import IntegrationPoint


@dataclass
class APIIntegrationPoint(IntegrationPoint):
    """Represents an API endpoint or integration point in the system."""

    http_method: str = field(default="GET")
    route_pattern: str = field(default="/")
    auth_required: bool = field(default=False)
    request_params: Dict[str, str] = field(default_factory=dict)  # Expected request parameters
    response_type: str = "json"  # Expected response type
    rate_limited: bool = False  # Whether the endpoint is rate limited
    api_version: Optional[str] = None  # API version if applicable

    def to_dict(self) -> Dict:
        """Convert the API integration point to a dictionary representation."""
        base_dict = super().to_dict()
        api_dict = {
            "http_method": self.http_method,
            "route_pattern": self.route_pattern,
            "request_params": self.request_params,
            "response_type": self.response_type,
            "auth_required": self.auth_required,
            "rate_limited": self.rate_limited,
            "api_version": self.api_version
        }
        return {**base_dict, **api_dict}

    @classmethod
    def from_dict(cls, data: Dict) -> "APIIntegrationPoint":
        """Create an APIIntegrationPoint instance from a dictionary."""
        return cls(**data)

    def calculate_complexity_score(self) -> float:
        """Calculate complexity score based on API characteristics."""
        score = 0.0

        # Add complexity for authentication
        if self.auth_required:
            score += 0.2

        # Add complexity for rate limiting
        if self.rate_limited:
            score += 0.1

        # Add complexity based on HTTP method
        if self.http_method in ["POST", "PUT", "PATCH"]:
            score += 0.2
        elif self.http_method == "DELETE":
            score += 0.1

        # Add complexity based on parameters
        param_count = len(self.request_params)
        score += min(0.3, param_count * 0.05)  # Cap at 0.3

        # Normalize score to 0-1 range
        return min(1.0, score)

    def calculate_risk_score(self) -> float:
        """Calculate risk score based on API characteristics."""
        score = 0.0

        # Higher risk for write operations
        if self.http_method in ["POST", "PUT", "PATCH", "DELETE"]:
            score += 0.3

        # Higher risk for authenticated endpoints
        if self.auth_required:
            score += 0.3

        # Risk based on parameter count (more params = more risk)
        param_count = len(self.request_params)
        score += min(0.2, param_count * 0.04)  # Cap at 0.2

        # Risk for rate-limited endpoints
        if self.rate_limited:
            score += 0.2

        # Normalize score to 0-1 range
        return min(1.0, score)

    def generate_test_requirements(self) -> List[str]:
        """Generate a list of test requirements for this API endpoint."""
        requirements = [
            f"Test {self.http_method} request to {self.route_pattern}",
        ]

        if self.auth_required:
            requirements.extend([
                "Test with valid authentication",
                "Test with invalid authentication",
                "Test with missing authentication"
            ])

        if self.request_params:
            requirements.extend([
                "Test with valid request parameters",
                "Test with missing required parameters",
                "Test with invalid parameter values"
            ])

        if self.rate_limited:
            requirements.append("Test rate limiting behavior")

        requirements.extend([
            "Test successful response format",
            "Test error response handling"
        ])

        return requirements
