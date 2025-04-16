"""Codebase analyzer for the LLM Integration Testing Framework."""
import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List

from src.analysis.integration_detector import IntegrationPointDetector
from src.scanner.base import BaseScanner
from src.scanner.python_scanner import PythonScanner
from src.scanner.dotnet_scanner import DotNetScanner

logger = logging.getLogger(__name__)

class CodebaseAnalyzer:
    """Analyzes codebases to identify components, dependencies, and integration points."""

    def __init__(self):
        """Initialize the codebase analyzer."""
        self.scanners: List[BaseScanner] = [
            PythonScanner(),
            DotNetScanner()
        ]
        self.integration_detector = IntegrationPointDetector()

    async def analyze(self, repo_path: Path) -> Dict[str, Any]:
        """Analyze the codebase at the given path.

        Args:
            repo_path: Path to the repository to analyze

        Returns:
            Dictionary containing analysis results including:
            - components: List of identified components
            - dependencies: Dependency graph
            - integration_points: List of integration points
            - metrics: Analysis metrics
        """
        try:
            # Scan the codebase
            components = []
            for scanner in self.scanners:
                scanner_components = await scanner.scan(repo_path)
                components.extend(scanner_components)

            # Detect integration points
            integration_points = await self.integration_detector.detect(components)

            # Build dependency graph
            dependencies = self._build_dependency_graph(components)

            # Calculate metrics
            metrics = self._calculate_metrics(components, dependencies, integration_points)

            return {
                "components": components,
                "dependencies": dependencies,
                "integration_points": integration_points,
                "metrics": metrics
            }

        except Exception as e:
            logger.error(f"Error analyzing codebase: {str(e)}")
            raise

    def _build_dependency_graph(self, components: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Build a dependency graph from the components.

        Args:
            components: List of component dictionaries

        Returns:
            Dictionary mapping component names to their dependencies
        """
        graph = {}
        for component in components:
            graph[component["name"]] = component.get("dependencies", [])
        return graph

    def _calculate_metrics(self,
                         components: List[Dict[str, Any]],
                         dependencies: Dict[str, List[str]],
                         integration_points: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate analysis metrics.

        Args:
            components: List of component dictionaries
            dependencies: Dependency graph
            integration_points: List of integration points

        Returns:
            Dictionary containing calculated metrics
        """
        total_components = len(components)
        total_dependencies = sum(len(deps) for deps in dependencies.values())
        total_integration_points = len(integration_points)

        return {
            "total_components": total_components,
            "total_dependencies": total_dependencies,
            "avg_dependencies_per_component": total_dependencies / total_components if total_components > 0 else 0,
            "total_integration_points": total_integration_points,
            "components_with_integration_points": len({ip["source"] for ip in integration_points} | {ip["target"] for ip in integration_points})
        }
