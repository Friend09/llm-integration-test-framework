"""LLM analyzer module.

This module uses Large Language Models (LLMs) to analyze the repository structure
and dependency analysis results to generate insights and test recommendations.
"""

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

import httpx

from config.settings import LLMConfig
from src.analyzer.dependency_analyzer import (AnalysisResult, IntegrationPoint,
                                             RepositoryStructure)


@dataclass
class TestCoverageRecommendation:
    """LLM-generated test coverage recommendation."""
    component: str
    integration_points: List[str]
    recommended_test_types: List[str]
    priority: int  # 1-5, with 5 being highest priority
    complexity: int  # 1-5, with 5 being most complex
    rationale: str
    suggested_test_approach: str
    test_data_requirements: Optional[List[str]] = None
    potential_mocking_targets: Optional[List[str]] = None


@dataclass
class LLMAnalysisReport:
    """Full analysis report generated by the LLM."""
    project_overview: str
    architecture_summary: str
    identified_integration_points: List[Dict[str, Any]]
    test_coverage_recommendations: List[TestCoverageRecommendation]
    critical_paths_analysis: str
    suggested_testing_approach: str
    estimated_effort: Dict[str, Any]
    test_strategy_recommendations: str
    next_steps: List[str]


class LLMAnalyzer:
    """Uses LLM to analyze code dependencies and recommend integration tests."""

    def __init__(self, llm_config: LLMConfig):
        """
        Initialize LLM analyzer.

        Args:
            llm_config: Configuration for the LLM
        """
        self.config = llm_config
        self.logger = logging.getLogger(__name__)

    async def analyze_dependencies(
        self,
        analysis_result: AnalysisResult,
        repo_structure: RepositoryStructure,
        repo_name: str
    ) -> LLMAnalysisReport:
        """
        Generate integration test recommendations using LLM.

        Args:
            analysis_result: Result of dependency analysis
            repo_structure: Repository structure
            repo_name: Name of the repository

        Returns:
            LLMAnalysisReport: Report with test recommendations

        Raises:
            Exception: If there is an error calling the LLM API
        """
        self.logger.info("Starting LLM analysis of dependencies")

        # Prepare information for the LLM
        repo_summary = self._create_repo_summary(repo_structure, repo_name)

        # Prepare the prompt for the LLM
        prompt = await self._create_analysis_prompt(analysis_result, repo_summary)

        # Call the LLM API
        response = await self._call_llm_api(prompt)

        # Parse the response
        analysis_report = self._parse_llm_response(response)

        return analysis_report

    def _create_repo_summary(
        self, repo_structure: RepositoryStructure, repo_name: str
    ) -> Dict[str, Any]:
        """
        Create a summary of the repository structure for the LLM.

        Args:
            repo_structure: Repository structure
            repo_name: Name of the repository

        Returns:
            Dict[str, Any]: Summary of the repository
        """
        # Count files by language
        language_counts = {}
        for file in repo_structure.files.values():
            language = file.language
            language_counts[language] = language_counts.get(language, 0) + 1

        # Identify main entry points
        entry_points = repo_structure.entry_points

        # Count test files
        test_file_count = len(repo_structure.test_files)

        # Extract directory structure (top-level directories)
        directories = set()
        for file_path in repo_structure.files:
            parts = file_path.split('/')
            if len(parts) > 1:
                directories.add(parts[0])

        # Create summary
        return {
            "repo_name": repo_name,
            "file_count": len(repo_structure.files),
            "language_statistics": language_counts,
            "entry_points": entry_points,
            "test_file_count": test_file_count,
            "top_level_directories": list(directories)
        }

    async def _create_analysis_prompt(
        self,
        analysis_result: AnalysisResult,
        repo_summary: Dict[str, Any]
    ) -> str:
        """
        Create a detailed prompt for the LLM.

        Args:
            analysis_result: Result of dependency analysis
            repo_summary: Summary of the repository

        Returns:
            str: Prompt for the LLM
        """
        # Convert integration points to a serializable format
        integration_points = [
            {
                "source": point.source_component,
                "target": point.target_component,
                "type": point.integration_type,
                "importance": point.importance,
                "complexity": point.complexity,
                "description": point.description
            }
            for point in analysis_result.integration_points
        ]

        # Convert dependency graph to a summary format
        # (full graph would be too large for LLM context)
        graph_summary = {
            "node_count": len(analysis_result.dependency_graph.nodes()),
            "edge_count": len(analysis_result.dependency_graph.edges()),
            "most_central_nodes": [
                {"node": node, "centrality": centrality}
                for node, centrality in sorted(
                    nx.degree_centrality(analysis_result.dependency_graph).items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10]  # Top 10 most central nodes
            ]
        }

        # Format critical paths
        critical_paths = [
            {"path": path, "length": len(path)}
            for path in analysis_result.critical_paths[:5]  # Just show top 5 to save context
        ]

        # Format test coverage gaps
        top_gaps = sorted(
            analysis_result.test_coverage_gaps.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]  # Top 10 gaps

        test_coverage_gaps = {file_path: score for file_path, score in top_gaps}

        # Combine all information into a context object for the LLM
        context = {
            "repository_summary": repo_summary,
            "graph_summary": graph_summary,
            "integration_points": integration_points[:20],  # Limit to top 20 by importance
            "critical_paths": critical_paths,
            "test_coverage_gaps": test_coverage_gaps,
            "metrics": {
                "component_count": analysis_result.component_count,
                "integration_point_count": analysis_result.integration_point_count,
                "test_coverage_percentage": analysis_result.test_coverage_percentage,
                "high_risk_components": analysis_result.high_risk_components[:5]  # Top 5 high risk
            }
        }

        # Create the prompt
        prompt = f"""
        I need you to analyze a codebase and provide detailed recommendations for integration testing.

        # REPOSITORY INFORMATION
        {json.dumps(context["repository_summary"], indent=2)}

        # DEPENDENCY ANALYSIS
        {json.dumps(context["graph_summary"], indent=2)}

        # INTEGRATION POINTS
        I've identified the following integration points (showing top by importance):
        {json.dumps(context["integration_points"], indent=2)}

        # CRITICAL PATHS
        These are the critical paths through the codebase:
        {json.dumps(context["critical_paths"], indent=2)}

        # TEST COVERAGE GAPS
        These are the components with the largest test coverage gaps:
        {json.dumps(context["test_coverage_gaps"], indent=2)}

        # METRICS
        {json.dumps(context["metrics"], indent=2)}

        Based on this information, please provide a comprehensive analysis including:

        1. A brief overview of the project architecture
        2. Analysis of the integration points and their importance
        3. Detailed recommendations for integration test coverage with specific examples
        4. Suggested testing approach (e.g., bottom-up, top-down, hybrid)
        5. Critical paths that should be prioritized for testing
        6. Estimated effort for implementing the recommended tests
        7. Specific test strategy recommendations
        8. Next steps for the team

        Format your response as a JSON object with the following structure:
        {{
            "project_overview": "Brief overview of the project",
            "architecture_summary": "Summary of the architecture based on dependency analysis",
            "identified_integration_points": [
                {{
                    "source": "source_component",
                    "target": "target_component",
                    "type": "integration_type",
                    "importance": importance_score,
                    "explanation": "Why this is important to test"
                }}
            ],
            "test_coverage_recommendations": [
                {{
                    "component": "component_name",
                    "integration_points": ["list", "of", "integration_points"],
                    "recommended_test_types": ["unit", "integration", "api", "etc"],
                    "priority": priority_score,
                    "complexity": complexity_score,
                    "rationale": "Why this component needs testing",
                    "suggested_test_approach": "How to test this component",
                    "test_data_requirements": ["list", "of", "test", "data", "requirements"],
                    "potential_mocking_targets": ["list", "of", "components", "to", "mock"]
                }}
            ],
            "critical_paths_analysis": "Analysis of critical paths",
            "suggested_testing_approach": "Overall testing approach",
            "estimated_effort": {{
                "high_priority_components": number_of_components,
                "estimated_person_days": estimated_days,
                "complexity_factors": ["list", "of", "complexity", "factors"]
            }},
            "test_strategy_recommendations": "Overall test strategy recommendations",
            "next_steps": ["step1", "step2", "step3"]
        }}

        Focus on providing practical, actionable recommendations that will help the team implement effective integration tests.
        """

        return prompt

    async def _call_llm_api(self, prompt: str) -> Dict[str, Any]:
        """
        Call the LLM API with the generated prompt.

        Args:
            prompt: The prompt to send to the LLM

        Returns:
            Dict[str, Any]: Raw response from the LLM API

        Raises:
            Exception: If there is an error calling the LLM API
        """
        self.logger.info(f"Calling LLM API using provider: {self.config.provider}")

        if self.config.provider == "openai":
            return await self._call_openai_api(prompt)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.config.provider}")

    async def _call_openai_api(self, prompt: str) -> Dict[str, Any]:
        """
        Call the OpenAI API with the generated prompt.

        Args:
            prompt: The prompt to send to the LLM

        Returns:
            Dict[str, Any]: Raw response from the OpenAI API

        Raises:
            Exception: If there is an error calling the API
        """
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.config.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.config.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are an expert software architect and testing specialist. "
                                          "Your task is to analyze code dependencies and provide "
                                          "recommendations for integration testing."
                            },
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": self.config.temperature,
                        "max_tokens": self.config.max_tokens
                    }
                )

                if response.status_code != 200:
                    self.logger.error(f"Error calling OpenAI API: {response.text}")
                    raise Exception(f"Error calling OpenAI API: {response.status_code}")

                return response.json()
        except Exception as e:
            self.logger.error(f"Exception calling OpenAI API: {str(e)}")
            raise

    def _parse_llm_response(self, response: Dict[str, Any]) -> LLMAnalysisReport:
        """
        Parse the LLM response into a structured report.

        Args:
            response: Raw response from the LLM API

        Returns:
            LLMAnalysisReport: Structured analysis report

        Raises:
            Exception: If there is an error parsing the response
        """
        self.logger.info("Parsing LLM response")

        try:
            # Extract the content from the response
            content = response["choices"][0]["message"]["content"]

            # Find the JSON part of the response
            json_start = content.find("{")
            json_end = content.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_content = content[json_start:json_end]
                parsed_content = json.loads(json_content)
            else:
                self.logger.warning("No JSON found in LLM response, trying to parse the entire content")
                parsed_content = json.loads(content)

            # Convert to TestCoverageRecommendation objects
            test_recommendations = []
            for rec in parsed_content.get("test_coverage_recommendations", []):
                test_recommendations.append(
                    TestCoverageRecommendation(
                        component=rec["component"],
                        integration_points=rec["integration_points"],
                        recommended_test_types=rec["recommended_test_types"],
                        priority=rec["priority"],
                        complexity=rec["complexity"],
                        rationale=rec["rationale"],
                        suggested_test_approach=rec["suggested_test_approach"],
                        test_data_requirements=rec.get("test_data_requirements"),
                        potential_mocking_targets=rec.get("potential_mocking_targets")
                    )
                )

            # Create the report
            return LLMAnalysisReport(
                project_overview=parsed_content.get("project_overview", ""),
                architecture_summary=parsed_content.get("architecture_summary", ""),
                identified_integration_points=parsed_content.get("identified_integration_points", []),
                test_coverage_recommendations=test_recommendations,
                critical_paths_analysis=parsed_content.get("critical_paths_analysis", ""),
                suggested_testing_approach=parsed_content.get("suggested_testing_approach", ""),
                estimated_effort=parsed_content.get("estimated_effort", {}),
                test_strategy_recommendations=parsed_content.get("test_strategy_recommendations", ""),
                next_steps=parsed_content.get("next_steps", [])
            )

        except (KeyError, json.JSONDecodeError) as e:
            self.logger.error(f"Error parsing LLM response: {str(e)}")
            raise Exception(f"Error parsing LLM response: {str(e)}")
