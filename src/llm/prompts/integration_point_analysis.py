"""Integration point analysis prompt template."""
from typing import Any, Dict

from .base import PromptTemplate

class IntegrationPointAnalysisPrompt(PromptTemplate):
    """Prompt template for analyzing integration points."""

    def __init__(self):
        """Initialize the integration point analysis prompt template."""
        template = """
Analyze the following integration point and provide a detailed assessment.

Integration Point Information:
{integration_point_info}

Connected Components:
{connected_components}

Interface Details:
{interface_details}

Communication Pattern:
{communication_pattern}

Please analyze this integration point and provide:
1. Interface stability assessment
2. Data flow analysis
3. Error handling evaluation
4. Testing requirements
5. Risk factors

Respond in JSON format matching the provided schema.
"""
        super().__init__(template)

    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for integration point analysis response.

        Returns:
            A JSON schema for the expected response
        """
        return {
            "type": "object",
            "properties": {
                "interface_assessment": {
                    "type": "object",
                    "properties": {
                        "stability_level": {
                            "type": "string",
                            "enum": ["stable", "evolving", "unstable"]
                        },
                        "breaking_change_risk": {
                            "type": "string",
                            "enum": ["high", "medium", "low"]
                        },
                        "backwards_compatibility": {
                            "type": "object",
                            "properties": {
                                "is_compatible": {"type": "boolean"},
                                "concerns": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                }
                            },
                            "required": ["is_compatible", "concerns"]
                        }
                    },
                    "required": ["stability_level", "breaking_change_risk", "backwards_compatibility"]
                },
                "data_flow": {
                    "type": "object",
                    "properties": {
                        "input_validation": {
                            "type": "object",
                            "properties": {
                                "validation_level": {"type": "string"},
                                "critical_fields": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "validation_rules": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                }
                            },
                            "required": ["validation_level", "critical_fields", "validation_rules"]
                        },
                        "data_transformations": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "description": {"type": "string"},
                                    "complexity": {"type": "string"},
                                    "testing_focus": {"type": "string"}
                                },
                                "required": ["description", "complexity", "testing_focus"]
                            }
                        },
                        "output_consistency": {
                            "type": "object",
                            "properties": {
                                "consistency_level": {"type": "string"},
                                "verification_points": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                }
                            },
                            "required": ["consistency_level", "verification_points"]
                        }
                    },
                    "required": ["input_validation", "data_transformations", "output_consistency"]
                },
                "error_handling": {
                    "type": "object",
                    "properties": {
                        "error_scenarios": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "scenario": {"type": "string"},
                                    "handling_mechanism": {"type": "string"},
                                    "recovery_process": {"type": "string"},
                                    "test_approach": {"type": "string"}
                                },
                                "required": ["scenario", "handling_mechanism", "recovery_process", "test_approach"]
                            }
                        },
                        "resilience_measures": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["error_scenarios", "resilience_measures"]
                },
                "testing_requirements": {
                    "type": "object",
                    "properties": {
                        "test_scenarios": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "description": {"type": "string"},
                                    "priority": {"type": "string"},
                                    "prerequisites": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    },
                                    "validation_criteria": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    }
                                },
                                "required": ["description", "priority", "prerequisites", "validation_criteria"]
                            }
                        },
                        "mocking_requirements": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "component": {"type": "string"},
                                    "complexity": {"type": "string"},
                                    "behavior_specs": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    }
                                },
                                "required": ["component", "complexity", "behavior_specs"]
                            }
                        }
                    },
                    "required": ["test_scenarios", "mocking_requirements"]
                },
                "risk_factors": {
                    "type": "object",
                    "properties": {
                        "technical_risks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "description": {"type": "string"},
                                    "severity": {"type": "string"},
                                    "mitigation": {"type": "string"}
                                },
                                "required": ["description", "severity", "mitigation"]
                            }
                        },
                        "operational_risks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "description": {"type": "string"},
                                    "impact": {"type": "string"},
                                    "contingency": {"type": "string"}
                                },
                                "required": ["description", "impact", "contingency"]
                            }
                        }
                    },
                    "required": ["technical_risks", "operational_risks"]
                }
            },
            "required": [
                "interface_assessment",
                "data_flow",
                "error_handling",
                "testing_requirements",
                "risk_factors"
            ]
        }

    def get_default_system_prompt(self) -> str:
        """Get the default system prompt for integration point analysis.

        Returns:
            A string containing the system prompt
        """
        return (
            "You are an expert in software integration and testing. "
            "Analyze the provided integration point thoroughly, considering "
            "interface stability, data flow, error handling, and potential risks. "
            "Focus on identifying critical test scenarios and providing "
            "actionable testing requirements."
        )
