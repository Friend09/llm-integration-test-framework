from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from .base import PromptTemplate
import json

@dataclass
class RiskFactor:
    """Data class representing a risk factor in testing."""
    name: str
    description: str
    impact: str
    probability: str
    mitigation_strategy: str
    affected_components: List[str]

class TestRiskAssessmentPrompt(PromptTemplate):
    """Prompt template for assessing risks in test scenarios."""

    def __init__(self) -> None:
        """Initialize the test risk assessment prompt template."""
        super().__init__("""
As an expert test risk analyst, evaluate the following system components and test requirements to assess potential risks.

Test Requirements:
{test_requirements}

System Components:
{component_analysis}

Integration Points:
{integration_points}

Dependencies:
{dependencies}

{resource_constraints}

Based on the provided information, perform a comprehensive risk assessment that:
1. Identifies potential failure points and vulnerabilities
2. Evaluates the impact and probability of each risk
3. Suggests mitigation strategies
4. Considers resource constraints and technical limitations
5. Prioritizes risks based on their potential impact
6. Provides actionable recommendations

Provide your response in the specified JSON schema format, ensuring:
- Each risk factor is clearly named and described
- Impact and probability levels are justified
- Mitigation strategies are practical and specific
- Affected components are accurately identified
- Overall risk assessment provides a clear picture
- Recommendations are actionable and prioritized

Focus on risks that are:
- Technical (e.g., integration failures, performance issues)
- Operational (e.g., resource constraints, environment issues)
- Business-critical (e.g., data integrity, security concerns)
- Project-related (e.g., dependencies, timeline impacts)
""")
        self.response_schema = {
            "type": "object",
            "properties": {
                "risk_factors": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "impact": {
                                "type": "string",
                                "enum": ["high", "medium", "low"]
                            },
                            "probability": {
                                "type": "string",
                                "enum": ["high", "medium", "low"]
                            },
                            "mitigation_strategy": {"type": "string"},
                            "affected_components": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["name", "description", "impact",
                                   "probability", "mitigation_strategy",
                                   "affected_components"]
                    }
                },
                "overall_risk_assessment": {
                    "type": "object",
                    "properties": {
                        "risk_level": {
                            "type": "string",
                            "enum": ["high", "medium", "low"]
                        },
                        "key_concerns": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "recommendations": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["risk_level", "key_concerns", "recommendations"]
                }
            },
            "required": ["risk_factors", "overall_risk_assessment"]
        }

    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for the expected response."""
        return self.response_schema

    def format(self, **kwargs: Any) -> str:
        """Format the template with the provided values."""
        if "resource_constraints" in kwargs and kwargs["resource_constraints"]:
            kwargs["resource_constraints"] = f"\nResource Constraints:\n{self._format_dict(kwargs['resource_constraints'])}\n"
        else:
            kwargs["resource_constraints"] = ""

        kwargs["test_requirements"] = self._format_dict(kwargs["test_requirements"])
        kwargs["component_analysis"] = self._format_dict(kwargs["component_analysis"])
        kwargs["integration_points"] = self._format_list(kwargs["integration_points"])
        kwargs["dependencies"] = self._format_dict(kwargs["dependencies"])

        return super().format(**kwargs)

    def _format_dict(self, data: Dict) -> str:
        """Format a dictionary for display in the prompt."""
        return json.dumps(data, indent=2)

    def _format_list(self, data: List) -> str:
        """Format a list for display in the prompt."""
        return json.dumps(data, indent=2)
