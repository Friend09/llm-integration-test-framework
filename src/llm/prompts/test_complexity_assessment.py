from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from .base import PromptTemplate
import json

@dataclass
class ComplexityMetrics:
    """Data class representing complexity metrics for a component."""
    cyclomatic_complexity: int
    integration_complexity: int
    data_complexity: int
    test_effort_estimate: str
    required_expertise_level: str

class TestComplexityAssessmentPrompt(PromptTemplate):
    """Prompt template for assessing test complexity and resource requirements."""

    def __init__(self) -> None:
        """Initialize the test complexity assessment prompt template."""
        super().__init__("""
As an expert test complexity analyst, evaluate the following system components and requirements to assess testing complexity.

Test Requirements:
{test_requirements}

System Components:
{component_analysis}

Integration Points:
{integration_points}

Dependencies:
{dependencies}

{resource_constraints}

Based on the provided information, perform a comprehensive complexity assessment that:
1. Evaluates cyclomatic complexity of components
2. Assesses integration complexity between components
3. Analyzes data complexity and state management
4. Estimates required testing effort and expertise
5. Considers resource constraints and technical requirements
6. Provides actionable recommendations for test planning

Provide your response in the specified JSON schema format, ensuring:
- Each component's complexity metrics are justified
- Test effort estimates are realistic
- Required expertise levels are appropriate
- Complexity factors are clearly identified
- Resource requirements are well-defined
- Recommendations are practical and specific

Consider complexity factors such as:
- Code structure and flow complexity
- Integration dependencies and interfaces
- Data flow and state management
- Environmental setup requirements
- Technical skill requirements
- Testing tool requirements
""")
        self.response_schema = {
            "type": "object",
            "properties": {
                "component_complexity": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "component_name": {"type": "string"},
                            "cyclomatic_complexity": {"type": "integer"},
                            "integration_complexity": {"type": "integer"},
                            "data_complexity": {"type": "integer"},
                            "test_effort_estimate": {
                                "type": "string",
                                "enum": ["high", "medium", "low"]
                            },
                            "required_expertise_level": {
                                "type": "string",
                                "enum": ["expert", "intermediate", "beginner"]
                            },
                            "complexity_factors": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["component_name", "cyclomatic_complexity",
                                   "integration_complexity", "data_complexity",
                                   "test_effort_estimate", "required_expertise_level",
                                   "complexity_factors"]
                    }
                },
                "overall_assessment": {
                    "type": "object",
                    "properties": {
                        "total_complexity_score": {"type": "integer"},
                        "estimated_testing_time": {"type": "string"},
                        "resource_requirements": {
                            "type": "object",
                            "properties": {
                                "team_size": {"type": "integer"},
                                "required_skills": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "tools_needed": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                }
                            },
                            "required": ["team_size", "required_skills", "tools_needed"]
                        },
                        "recommendations": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["total_complexity_score", "estimated_testing_time",
                               "resource_requirements", "recommendations"]
                }
            },
            "required": ["component_complexity", "overall_assessment"]
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
