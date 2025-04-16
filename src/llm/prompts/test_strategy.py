"""Test strategy prompt generator."""
from typing import Any, Dict, List

class TestStrategyPrompt:
    """Generates prompts for test strategy analysis."""

    def render(
        self,
        system_overview: Dict[str, Any],
        component_analysis: List[Any],
        integration_points: List[Any],
        dependencies: List[tuple],
        resource_constraints: Dict[str, Any]
    ) -> str:
        """Render the test strategy prompt."""
        return f"""
        Analyze the following system and generate a test strategy:

        System Overview:
        - Repository: {system_overview['repository_url']}
        - Components: {system_overview['total_components']}
        - Integration Points: {system_overview['total_integration_points']}
        - Technologies: {', '.join(system_overview['main_technologies'])}
        - Complexity Score: {system_overview['complexity_score']}
        - Estimated Effort: {system_overview['estimated_test_effort']} days

        Components:
        {self._format_components(component_analysis)}

        Integration Points:
        {self._format_integration_points(integration_points)}

        Dependencies:
        {self._format_dependencies(dependencies)}

        Resource Constraints:
        - Team Size: {resource_constraints['team_size']}
        - Timeline: {resource_constraints['timeline_weeks']} weeks
        """

    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for responses."""
        return {
            "type": "object",
            "properties": {
                "overall_approach": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "justification": {"type": "string"},
                        "key_considerations": {"type": "array", "items": {"type": "string"}}
                    }
                },
                "component_prioritization": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "component": {"type": "string"},
                            "priority": {"type": "string"},
                            "rationale": {"type": "string"}
                        }
                    }
                },
                "test_sequence": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "phase_name": {"type": "string"},
                            "components": {"type": "array", "items": {"type": "string"}},
                            "expected_duration": {"type": "string"}
                        }
                    }
                }
            }
        }

    def _format_components(self, components: List[Any]) -> str:
        """Format component information."""
        return "\n".join(
            f"- {c.name} ({c.component_type}): {c.description}"
            for c in components
        )

    def _format_integration_points(self, points: List[Any]) -> str:
        """Format integration point information."""
        return "\n".join(
            f"- {p.name}: {p.source_component} → {p.target_component}"
            for p in points
        )

    def _format_dependencies(self, dependencies: List[tuple]) -> str:
        """Format dependency information."""
        return "\n".join(
            f"- {source} → {target}"
            for source, target in dependencies
        )
