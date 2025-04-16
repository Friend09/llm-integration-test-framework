from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from .base import PromptTemplate
import json

@dataclass
class TestRequirement:
    """Data class representing a specific test requirement."""
    name: str
    description: str
    prerequisites: List[str]
    validation_criteria: List[str]
    dependencies: List[str]
    priority: str

class TestRequirementsPrompt(PromptTemplate):
    """Prompt template for generating specific test requirements based on component analysis."""

    def __init__(self) -> None:
        """Initialize the test requirements prompt template."""
        super().__init__("""
As an expert test engineer, analyze the following system components and generate detailed test requirements.

System Overview:
{component_analysis}

Integration Points:
{integration_points}

Dependencies:
{dependencies}

{resource_constraints}

Based on the above information, generate comprehensive test requirements that:
1. Cover all critical functionality and edge cases
2. Address integration points and dependencies
3. Include clear validation criteria
4. Specify prerequisites and setup requirements
5. Consider resource constraints (if provided)
6. Prioritize tests based on component criticality

Provide your response in the specified JSON schema format, ensuring:
- Each test requirement has a clear name and description
- Prerequisites are clearly listed
- Validation criteria are specific and measurable
- Dependencies are explicitly stated
- Priority levels are assigned appropriately
- Coverage requirements are realistic and justified

Focus on creating requirements that are:
- Specific and unambiguous
- Testable and measurable
- Aligned with system architecture
- Feasible within resource constraints
""")
        self.response_schema = {
            "type": "object",
            "properties": {
                "test_requirements": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "prerequisites": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "validation_criteria": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "dependencies": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "priority": {
                                "type": "string",
                                "enum": ["high", "medium", "low"]
                            }
                        },
                        "required": ["name", "description", "prerequisites",
                                   "validation_criteria", "dependencies", "priority"]
                    }
                },
                "coverage_requirements": {
                    "type": "object",
                    "properties": {
                        "unit_test_coverage": {"type": "number"},
                        "integration_test_coverage": {"type": "number"},
                        "e2e_test_coverage": {"type": "number"}
                    },
                    "required": ["unit_test_coverage", "integration_test_coverage", "e2e_test_coverage"]
                }
            },
            "required": ["test_requirements", "coverage_requirements"]
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
