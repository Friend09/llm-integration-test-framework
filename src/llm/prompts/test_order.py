"""Test order prompt template."""
from typing import Any, Dict

from .base import PromptTemplate

class TestOrderPrompt(PromptTemplate):
    """Prompt template for determining test execution order."""

    def __init__(self):
        """Initialize the test order prompt template."""
        template = """
Analyze the following component dependencies and determine the optimal test execution order.

Component Dependencies:
{dependencies}

Test Strategy:
{test_strategy}

Algorithm Results:
{algorithm_results}

Resource Constraints:
{resource_constraints}

Please evaluate the test order options and provide:
1. Optimal test sequence
2. Stub requirements
3. Justification for the order
4. Implementation considerations
5. Risk assessment

Respond in JSON format matching the provided schema.
"""
        super().__init__(template)

    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for test order response.

        Returns:
            A JSON schema for the expected response
        """
        return {
            "type": "object",
            "properties": {
                "test_sequence": {
                    "type": "object",
                    "properties": {
                        "ordered_components": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "component": {"type": "string"},
                                    "phase": {"type": "integer"},
                                    "dependencies_ready": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    },
                                    "dependencies_stubbed": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    }
                                },
                                "required": ["component", "phase", "dependencies_ready", "dependencies_stubbed"]
                            }
                        },
                        "parallel_testing_groups": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "group_id": {"type": "integer"},
                                    "components": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    },
                                    "prerequisites": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    }
                                },
                                "required": ["group_id", "components", "prerequisites"]
                            }
                        }
                    },
                    "required": ["ordered_components", "parallel_testing_groups"]
                },
                "stub_requirements": {
                    "type": "object",
                    "properties": {
                        "total_stub_count": {"type": "integer"},
                        "stub_complexity_assessment": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "component": {"type": "string"},
                                    "complexity": {"type": "string"},
                                    "implementation_effort": {"type": "string"},
                                    "reuse_potential": {"type": "boolean"}
                                },
                                "required": ["component", "complexity", "implementation_effort", "reuse_potential"]
                            }
                        },
                        "stub_dependencies": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "stub": {"type": "string"},
                                    "used_by": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    },
                                    "lifetime": {"type": "string"}
                                },
                                "required": ["stub", "used_by", "lifetime"]
                            }
                        }
                    },
                    "required": ["total_stub_count", "stub_complexity_assessment", "stub_dependencies"]
                },
                "order_justification": {
                    "type": "object",
                    "properties": {
                        "algorithm_comparison": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "algorithm": {"type": "string"},
                                    "advantages": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    },
                                    "disadvantages": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    },
                                    "suitability_score": {"type": "number"}
                                },
                                "required": ["algorithm", "advantages", "disadvantages", "suitability_score"]
                            }
                        },
                        "selected_approach": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "rationale": {"type": "string"},
                                "key_benefits": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                }
                            },
                            "required": ["name", "rationale", "key_benefits"]
                        }
                    },
                    "required": ["algorithm_comparison", "selected_approach"]
                },
                "implementation_considerations": {
                    "type": "object",
                    "properties": {
                        "prerequisites": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "requirement": {"type": "string"},
                                    "type": {"type": "string"},
                                    "effort": {"type": "string"}
                                },
                                "required": ["requirement", "type", "effort"]
                            }
                        },
                        "environment_setup": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "component": {"type": "string"},
                                    "setup_steps": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    },
                                    "dependencies": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    }
                                },
                                "required": ["component", "setup_steps", "dependencies"]
                            }
                        },
                        "resource_requirements": {
                            "type": "object",
                            "properties": {
                                "team_size": {"type": "integer"},
                                "estimated_duration": {"type": "string"},
                                "special_skills": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                }
                            },
                            "required": ["team_size", "estimated_duration", "special_skills"]
                        }
                    },
                    "required": ["prerequisites", "environment_setup", "resource_requirements"]
                },
                "risk_assessment": {
                    "type": "object",
                    "properties": {
                        "sequence_risks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "risk_type": {"type": "string"},
                                    "description": {"type": "string"},
                                    "impact": {"type": "string"},
                                    "mitigation": {"type": "string"}
                                },
                                "required": ["risk_type", "description", "impact", "mitigation"]
                            }
                        },
                        "dependency_risks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "components": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    },
                                    "risk_description": {"type": "string"},
                                    "mitigation_strategy": {"type": "string"}
                                },
                                "required": ["components", "risk_description", "mitigation_strategy"]
                            }
                        },
                        "overall_risk_level": {
                            "type": "string",
                            "enum": ["high", "medium", "low"]
                        }
                    },
                    "required": ["sequence_risks", "dependency_risks", "overall_risk_level"]
                }
            },
            "required": [
                "test_sequence",
                "stub_requirements",
                "order_justification",
                "implementation_considerations",
                "risk_assessment"
            ]
        }

    def get_default_system_prompt(self) -> str:
        """Get the default system prompt for test order determination.

        Returns:
            A string containing the system prompt
        """
        return (
            "You are an expert in integration testing and dependency analysis. "
            "Evaluate the provided component dependencies and algorithm results "
            "to determine the optimal test execution order. Consider stub "
            "requirements, implementation complexity, and resource constraints "
            "to provide a practical and efficient testing sequence."
        )
