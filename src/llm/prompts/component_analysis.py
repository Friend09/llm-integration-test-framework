"""Component analysis prompt template."""
from typing import Any, Dict

from .base import PromptTemplate

class ComponentAnalysisPrompt(PromptTemplate):
    """Prompt template for analyzing software components."""

    def __init__(self):
        """Initialize the component analysis prompt template."""
        template = """
Analyze the following software component and provide a detailed assessment.

Component Information:
{component_info}

Dependencies:
{dependencies}

Code Metrics:
{metrics}

Please analyze this component and provide:
1. Its role in the system
2. Critical dependencies and integration points
3. Potential testing challenges
4. Recommended testing approach
5. Risk assessment

Respond in JSON format matching the provided schema.
"""
        super().__init__(template)

    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for component analysis response.

        Returns:
            A JSON schema for the expected response
        """
        return {
            "type": "object",
            "properties": {
                "role": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string"},
                        "responsibilities": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "importance_level": {
                            "type": "string",
                            "enum": ["critical", "high", "medium", "low"]
                        }
                    },
                    "required": ["description", "responsibilities", "importance_level"]
                },
                "dependencies": {
                    "type": "object",
                    "properties": {
                        "critical_dependencies": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "type": {"type": "string"},
                                    "impact": {"type": "string"}
                                },
                                "required": ["name", "type", "impact"]
                            }
                        },
                        "integration_points": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "type": {"type": "string"},
                                    "complexity": {"type": "string"},
                                    "testing_considerations": {"type": "string"}
                                },
                                "required": ["name", "type", "complexity", "testing_considerations"]
                            }
                        }
                    },
                    "required": ["critical_dependencies", "integration_points"]
                },
                "testing": {
                    "type": "object",
                    "properties": {
                        "challenges": {
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
                        "recommended_approach": {
                            "type": "object",
                            "properties": {
                                "strategy": {"type": "string"},
                                "justification": {"type": "string"},
                                "key_test_cases": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                }
                            },
                            "required": ["strategy", "justification", "key_test_cases"]
                        }
                    },
                    "required": ["challenges", "recommended_approach"]
                },
                "risk_assessment": {
                    "type": "object",
                    "properties": {
                        "overall_risk_level": {
                            "type": "string",
                            "enum": ["critical", "high", "medium", "low"]
                        },
                        "specific_risks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "description": {"type": "string"},
                                    "likelihood": {"type": "string"},
                                    "impact": {"type": "string"},
                                    "mitigation_strategy": {"type": "string"}
                                },
                                "required": ["description", "likelihood", "impact", "mitigation_strategy"]
                            }
                        }
                    },
                    "required": ["overall_risk_level", "specific_risks"]
                }
            },
            "required": ["role", "dependencies", "testing", "risk_assessment"]
        }

    def get_default_system_prompt(self) -> str:
        """Get the default system prompt for component analysis.

        Returns:
            A string containing the system prompt
        """
        return (
            "You are an expert software architect and testing specialist. "
            "Analyze the provided component thoroughly, considering its role, "
            "dependencies, integration points, and potential risks. "
            "Provide detailed, actionable insights for integration testing."
        )
