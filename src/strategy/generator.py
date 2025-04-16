"""Test strategy generator for the LLM Integration Testing Framework."""
import asyncio
import logging
from typing import Any, Dict

from src.llm.openai import OpenAIClient
from src.strategy.approach_recommender import TestApproachRecommender
from src.strategy.test_order_selector import TestOrderSelector

logger = logging.getLogger(__name__)

class TestStrategyGenerator:
    """Generates test strategies based on codebase analysis."""

    def __init__(self, llm_client: OpenAIClient):
        """Initialize the test strategy generator.

        Args:
            llm_client: LLM client for generating recommendations
        """
        self.llm_client = llm_client
        self.approach_recommender = TestApproachRecommender(llm_client)
        self.test_order_selector = TestOrderSelector()

    async def generate(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a test strategy based on the analysis results.

        Args:
            analysis_results: Dictionary containing analysis results

        Returns:
            Dictionary containing the test strategy including:
            - approach: Recommended testing approach
            - test_order: Ordered list of components to test
            - stub_requirements: Stub requirements for each component
            - risk_assessment: Risk assessment for integration points
            - recommendations: List of testing recommendations
        """
        try:
            # Generate testing approach
            approach = await self.approach_recommender.recommend(
                components=analysis_results["components"],
                dependencies=analysis_results["dependencies"],
                integration_points=analysis_results["integration_points"]
            )

            # Generate test order
            test_order = await self.test_order_selector.select(
                components=analysis_results["components"],
                dependencies=analysis_results["dependencies"]
            )

            # Generate stub requirements
            stub_requirements = self._generate_stub_requirements(
                components=analysis_results["components"],
                test_order=test_order
            )

            # Generate risk assessment
            risk_assessment = await self._assess_risks(
                integration_points=analysis_results["integration_points"]
            )

            # Generate recommendations
            recommendations = await self._generate_recommendations(
                components=analysis_results["components"],
                integration_points=analysis_results["integration_points"],
                risk_assessment=risk_assessment
            )

            return {
                "approach": approach,
                "test_order": test_order,
                "stub_requirements": stub_requirements,
                "risk_assessment": risk_assessment,
                "recommendations": recommendations
            }

        except Exception as e:
            logger.error(f"Error generating test strategy: {str(e)}")
            raise

    def _generate_stub_requirements(self,
                                  components: list,
                                  test_order: list) -> Dict[str, Any]:
        """Generate stub requirements for each component.

        Args:
            components: List of components
            test_order: Ordered list of components to test

        Returns:
            Dictionary mapping component names to their stub requirements
        """
        requirements = {}
        for component in components:
            component_name = component["name"]
            dependencies = component.get("dependencies", [])

            # Components that need to be stubbed are those that appear later in the test order
            stub_components = [
                dep for dep in dependencies
                if dep in test_order and test_order.index(dep) > test_order.index(component_name)
            ]

            requirements[component_name] = {
                "required_stubs": stub_components,
                "stub_count": len(stub_components)
            }

        return requirements

    async def _assess_risks(self, integration_points: list) -> Dict[str, Any]:
        """Assess risks for integration points.

        Args:
            integration_points: List of integration points

        Returns:
            Dictionary containing risk assessment for each integration point
        """
        risk_assessment = {}
        for point in integration_points:
            point_id = f"{point['source']}_{point['target']}"

            # Use LLM to assess risk
            risk_prompt = f"""
            Assess the risk level for the following integration point:
            Source: {point['source']}
            Target: {point['target']}
            Type: {point['type']}

            Consider factors such as:
            - Complexity of the integration
            - Criticality of the components
            - Potential impact of failures
            - Historical reliability

            Provide a risk level (LOW, MEDIUM, HIGH) and a brief justification.
            """

            response = await self.llm_client.complete(risk_prompt)
            risk_assessment[point_id] = {
                "risk_level": response.split("\n")[0].strip(),
                "justification": "\n".join(response.split("\n")[1:]).strip()
            }

        return risk_assessment

    async def _generate_recommendations(self,
                                      components: list,
                                      integration_points: list,
                                      risk_assessment: Dict[str, Any]) -> list:
        """Generate testing recommendations.

        Args:
            components: List of components
            integration_points: List of integration points
            risk_assessment: Risk assessment for integration points

        Returns:
            List of testing recommendations
        """
        recommendations = []

        # Generate component-specific recommendations
        for component in components:
            component_name = component["name"]

            prompt = f"""
            Generate testing recommendations for the following component:
            Name: {component_name}
            Type: {component.get('type', 'Unknown')}
            Dependencies: {', '.join(component.get('dependencies', []))}

            Consider:
            - Appropriate test types (unit, integration, etc.)
            - Test coverage goals
            - Specific test cases to implement
            - Mocking/stubbing strategy
            """

            response = await self.llm_client.complete(prompt)
            recommendations.append({
                "component": component_name,
                "type": "component",
                "recommendation": response.strip()
            })

        # Generate integration-specific recommendations
        for point in integration_points:
            point_id = f"{point['source']}_{point['target']}"
            risk_info = risk_assessment[point_id]

            prompt = f"""
            Generate testing recommendations for the following integration point:
            Source: {point['source']}
            Target: {point['target']}
            Type: {point['type']}
            Risk Level: {risk_info['risk_level']}

            Consider:
            - Integration testing approach
            - Error handling and edge cases
            - Performance considerations
            - Monitoring and logging
            """

            response = await self.llm_client.complete(prompt)
            recommendations.append({
                "integration_point": point_id,
                "type": "integration",
                "recommendation": response.strip()
            })

        return recommendations
