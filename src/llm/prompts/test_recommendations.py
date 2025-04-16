from typing import Dict, List, Optional, Any
from .base import PromptTemplate
import json

class TestRecommendationsPrompt(PromptTemplate):
    """Prompt template for generating test recommendations."""

    def __init__(self) -> None:
        """Initialize the test recommendations prompt template."""
        super().__init__("""
As an expert test strategist, analyze the following test requirements, risk assessment, and complexity analysis to provide comprehensive test recommendations.

Test Requirements:
{test_requirements}

Risk Assessment:
{risk_assessment}

Complexity Analysis:
{complexity_analysis}

{resource_constraints}

Based on the provided information, generate detailed test recommendations that:
1. Address identified risks and complexity factors
2. Consider resource constraints and technical requirements
3. Provide specific testing approaches and methodologies
4. Include tool and framework recommendations
5. Suggest test automation strategies
6. Outline test environment requirements
7. Define test data management approaches
8. Recommend test execution and reporting strategies

Provide your response in the specified JSON schema format, ensuring:
- Recommendations are practical and actionable
- Testing approaches are well-justified
- Tool recommendations are appropriate
- Automation strategies are feasible
- Environment requirements are complete
- Data management approaches are robust
- Execution strategies are efficient
- Reporting approaches are comprehensive

Consider factors such as:
- Risk mitigation strategies
- Complexity management approaches
- Resource optimization techniques
- Tool integration requirements
- Automation feasibility
- Environment setup needs
- Data management challenges
- Execution efficiency
- Reporting effectiveness
""")
        self.response_schema = {
            "type": "object",
            "properties": {
                "testing_approaches": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "approach_name": {"type": "string"},
                            "description": {"type": "string"},
                            "applicable_components": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "justification": {"type": "string"},
                            "implementation_steps": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["approach_name", "description",
                                   "applicable_components", "justification",
                                   "implementation_steps"]
                    }
                },
                "tool_recommendations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "tool_name": {"type": "string"},
                            "category": {"type": "string"},
                            "description": {"type": "string"},
                            "use_cases": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "integration_requirements": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["tool_name", "category", "description",
                                   "use_cases", "integration_requirements"]
                    }
                },
                "automation_strategy": {
                    "type": "object",
                    "properties": {
                        "overall_approach": {"type": "string"},
                        "automation_levels": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "level": {"type": "string"},
                                    "description": {"type": "string"},
                                    "applicable_tests": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    }
                                },
                                "required": ["level", "description", "applicable_tests"]
                            }
                        },
                        "framework_recommendations": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["overall_approach", "automation_levels",
                               "framework_recommendations"]
                },
                "environment_requirements": {
                    "type": "object",
                    "properties": {
                        "test_environments": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "environment_name": {"type": "string"},
                                    "description": {"type": "string"},
                                    "setup_requirements": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    },
                                    "configuration_needs": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    }
                                },
                                "required": ["environment_name", "description",
                                           "setup_requirements", "configuration_needs"]
                            }
                        },
                        "data_management": {
                            "type": "object",
                            "properties": {
                                "data_generation": {"type": "string"},
                                "data_validation": {"type": "string"},
                                "data_cleanup": {"type": "string"}
                            },
                            "required": ["data_generation", "data_validation",
                                       "data_cleanup"]
                        }
                    },
                    "required": ["test_environments", "data_management"]
                },
                "execution_strategy": {
                    "type": "object",
                    "properties": {
                        "test_sequence": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "parallel_execution": {"type": "boolean"},
                        "resource_allocation": {
                            "type": "object",
                            "properties": {
                                "team_structure": {"type": "string"},
                                "role_assignments": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                }
                            },
                            "required": ["team_structure", "role_assignments"]
                        }
                    },
                    "required": ["test_sequence", "parallel_execution",
                               "resource_allocation"]
                },
                "reporting_approach": {
                    "type": "object",
                    "properties": {
                        "report_types": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "metrics_tracked": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "notification_strategy": {"type": "string"}
                    },
                    "required": ["report_types", "metrics_tracked",
                               "notification_strategy"]
                }
            },
            "required": ["testing_approaches", "tool_recommendations",
                       "automation_strategy", "environment_requirements",
                       "execution_strategy", "reporting_approach"]
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
        kwargs["risk_assessment"] = self._format_dict(kwargs["risk_assessment"])
        kwargs["complexity_analysis"] = self._format_dict(kwargs["complexity_analysis"])

        return super().format(**kwargs)

    def _format_dict(self, data: Dict) -> str:
        """Format a dictionary for display in the prompt."""
        return json.dumps(data, indent=2)

    def _format_list(self, data: List) -> str:
        """Format a list for display in the prompt."""
        return json.dumps(data, indent=2)
