"""Dependency analyzer module.

This module analyzes code dependencies and identifies integration points
in a repository based on the scanned structure.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any

import networkx as nx

from src.scanner.repository_scanner import RepositoryStructure, CodeFile


@dataclass
class IntegrationPoint:
    """Represents an integration point between components."""
    source_component: str
    target_component: str
    integration_type: str  # "API", "Database", "UI", "External", "Internal"
    importance: float = 1.0  # 0.0 to 1.0
    complexity: float = 0.5  # 0.0 to 1.0
    description: str = ""


@dataclass
class AnalysisResult:
    """Results of the dependency analysis."""
    dependency_graph: nx.DiGraph
    integration_points: List[IntegrationPoint] = field(default_factory=list)
    critical_paths: List[List[str]] = field(default_factory=list)
    test_coverage_gaps: Dict[str, float] = field(default_factory=dict)

    # Additional metrics
    component_count: int = 0
    integration_point_count: int = 0
    test_coverage_percentage: float = 0.0
    high_risk_components: List[str] = field(default_factory=list)


class DependencyAnalyzer:
    """Analyzes dependencies between components in a repository."""

    # Keywords that suggest integration points by type
    INTEGRATION_KEYWORDS = {
        "API": [
            "api", "rest", "http", "endpoint", "controller", "route",
            "request", "response", "client", "server", "service", "fetch",
            "axios", "requests"
        ],
        "Database": [
            "database", "db", "repository", "dao", "entity", "model",
            "schema", "query", "sql", "mongo", "orm", "jdbc", "jpa",
            "sequelize", "typeorm", "prisma", "sqlalchemy"
        ],
        "UI": [
            "ui", "view", "component", "render", "template", "page",
            "screen", "display", "interface", "react", "vue", "angular",
            "dom", "html", "css", "style"
        ],
        "External": [
            "external", "third", "party", "integration", "webhook",
            "callback", "oauth", "auth", "authentication", "provider",
            "cloud", "aws", "azure", "gcp", "google", "s3", "lambda"
        ]
    }

    def __init__(self):
        """Initialize the dependency analyzer."""
        self.logger = logging.getLogger(__name__)

    def analyze(self, repo_structure: RepositoryStructure) -> AnalysisResult:
        """
        Analyze the repository structure and identify dependencies.

        Args:
            repo_structure: The scanned repository structure

        Returns:
            AnalysisResult: Analysis result containing dependency graph and integration points
        """
        self.logger.info("Starting dependency analysis")

        # Create a directed graph for dependencies
        graph = nx.DiGraph()

        # Add nodes for each file
        for file_path in repo_structure.files:
            graph.add_node(file_path)

        # Add edges based on dependencies
        for source, targets in repo_structure.dependencies.items():
            for target in targets:
                graph.add_edge(source, target)

        # Find integration points
        integration_points = self._identify_integration_points(graph, repo_structure)

        # Find critical paths
        critical_paths = self._identify_critical_paths(graph)

        # Identify potential test coverage gaps
        test_coverage_gaps = self._identify_test_coverage_gaps(
            graph, repo_structure, integration_points
        )

        # Calculate additional metrics
        component_count = len(graph.nodes)
        integration_point_count = len(integration_points)
        test_coverage_percentage = self._calculate_test_coverage_percentage(repo_structure)
        high_risk_components = self._identify_high_risk_components(
            graph, repo_structure, test_coverage_gaps
        )

        return AnalysisResult(
            dependency_graph=graph,
            integration_points=integration_points,
            critical_paths=critical_paths,
            test_coverage_gaps=test_coverage_gaps,
            component_count=component_count,
            integration_point_count=integration_point_count,
            test_coverage_percentage=test_coverage_percentage,
            high_risk_components=high_risk_components
        )

    def _identify_integration_points(
        self, graph: nx.DiGraph, repo_structure: RepositoryStructure
    ) -> List[IntegrationPoint]:
        """
        Identify potential integration points in the codebase.

        Args:
            graph: Dependency graph
            repo_structure: Repository structure

        Returns:
            List[IntegrationPoint]: List of identified integration points
        """
        integration_points = []

        # Identify files related to different integration types
        api_files = self._identify_files_by_keywords(repo_structure, "API")
        db_files = self._identify_files_by_keywords(repo_structure, "Database")
        ui_files = self._identify_files_by_keywords(repo_structure, "UI")
        external_files = self._identify_files_by_keywords(repo_structure, "External")

        # Collect all integration points
        all_integration_points = []

        # API integration points (components calling API endpoints)
        for source, target in graph.edges():
            if target in api_files:
                all_integration_points.append((source, target, "API"))

        # Database integration points (components interacting with database)
        for source, target in graph.edges():
            if target in db_files:
                all_integration_points.append((source, target, "Database"))

        # UI integration points (components rendering UI)
        for source, target in graph.edges():
            if target in ui_files:
                all_integration_points.append((source, target, "UI"))

        # External integration points (components using external services)
        for source, target in graph.edges():
            if target in external_files:
                all_integration_points.append((source, target, "External"))

        # Internal integration points (other significant dependencies)
        for source, target in graph.edges():
            # Skip if already identified as another type
            if any(s == source and t == target for s, t, _ in all_integration_points):
                continue

            # Use centrality as a proxy for importance
            source_centrality = nx.degree_centrality(graph)[source]
            target_centrality = nx.degree_centrality(graph)[target]

            # If either node is important based on centrality
            if source_centrality > 0.1 or target_centrality > 0.1:
                all_integration_points.append((source, target, "Internal"))

        # Convert to IntegrationPoint objects with importance and complexity scores
        for source, target, integration_type in all_integration_points:
            # Calculate importance based on centrality and type
            source_centrality = nx.degree_centrality(graph)[source]
            target_centrality = nx.degree_centrality(graph)[target]

            base_importance = (source_centrality + target_centrality) / 2

            # Adjust importance by type
            type_importance_factor = {
                "API": 1.2,
                "Database": 1.3,
                "External": 1.4,
                "UI": 1.0,
                "Internal": 0.8
            }

            importance = min(1.0, base_importance * 10 * type_importance_factor.get(integration_type, 1.0))

            # Calculate complexity based on file size, in-degree, and out-degree
            source_file = repo_structure.files.get(source)
            target_file = repo_structure.files.get(target)

            complexity_factors = []

            # File size factor
            if source_file and target_file:
                avg_lines = (len(source_file.content.split('\n')) + len(target_file.content.split('\n'))) / 2
                size_factor = min(1.0, avg_lines / 1000)
                complexity_factors.append(size_factor)

            # Connectivity factor
            source_degree = graph.in_degree(source) + graph.out_degree(source)
            target_degree = graph.in_degree(target) + graph.out_degree(target)
            connectivity_factor = min(1.0, (source_degree + target_degree) / 20)
            complexity_factors.append(connectivity_factor)

            # Integration type factor
            type_complexity_factor = {
                "API": 0.7,
                "Database": 0.8,
                "External": 0.9,
                "UI": 0.6,
                "Internal": 0.5
            }
            complexity_factors.append(type_complexity_factor.get(integration_type, 0.5))

            # Average complexity
            complexity = sum(complexity_factors) / len(complexity_factors)

            # Generate a description
            description = self._generate_integration_description(
                source, target, integration_type, repo_structure
            )

            integration_points.append(
                IntegrationPoint(
                    source_component=source,
                    target_component=target,
                    integration_type=integration_type,
                    importance=importance,
                    complexity=complexity,
                    description=description
                )
            )

        # Sort by importance (descending)
        integration_points.sort(key=lambda x: x.importance, reverse=True)

        return integration_points

    def _identify_files_by_keywords(
        self, repo_structure: RepositoryStructure, integration_type: str
    ) -> Set[str]:
        """
        Identify files that likely belong to a specific integration type.

        Args:
            repo_structure: Repository structure
            integration_type: Type of integration to look for

        Returns:
            Set[str]: Set of file paths matching the integration type
        """
        matching_files = set()

        if integration_type not in self.INTEGRATION_KEYWORDS:
            return matching_files

        keywords = self.INTEGRATION_KEYWORDS[integration_type]

        for file_path, file_info in repo_structure.files.items():
            # Check file path for indicators
            if any(keyword in file_path.lower() for keyword in keywords):
                matching_files.add(file_path)
                continue

            # Check content for indicators
            lower_content = file_info.content.lower()
            if any(keyword in lower_content for keyword in keywords):
                matching_files.add(file_path)

        return matching_files

    def _generate_integration_description(
        self, source: str, target: str, integration_type: str, repo_structure: RepositoryStructure
    ) -> str:
        """
        Generate a description for an integration point.

        Args:
            source: Source component file path
            target: Target component file path
            integration_type: Type of integration
            repo_structure: Repository structure

        Returns:
            str: Description of the integration point
        """
        source_file = repo_structure.files.get(source)
        target_file = repo_structure.files.get(target)

        if not source_file or not target_file:
            return f"{integration_type} integration from {source} to {target}"

        source_language = source_file.language
        target_language = target_file.language

        if integration_type == "API":
            return f"API integration from {source} ({source_language}) to {target} ({target_language})"
        elif integration_type == "Database":
            return f"Database access from {source} ({source_language}) to {target} ({target_language})"
        elif integration_type == "UI":
            return f"UI component integration from {source} ({source_language}) to {target} ({target_language})"
        elif integration_type == "External":
            return f"External service integration from {source} ({source_language}) to {target} ({target_language})"
        else:
            return f"Internal component dependency from {source} ({source_language}) to {target} ({target_language})"

    def _identify_critical_paths(self, graph: nx.DiGraph) -> List[List[str]]:
        """
        Identify critical paths in the dependency graph.

        Args:
            graph: Dependency graph

        Returns:
            List[List[str]]: List of critical paths
        """
        critical_paths = []

        # Find nodes with high in-degree (many components depend on them)
        important_nodes = sorted(
            graph.nodes(),
            key=lambda n: graph.in_degree(n),
            reverse=True
        )[:min(10, len(graph.nodes()))]  # Top 10 most depended-upon nodes

        # Find nodes with high out-degree (depend on many components)
        dependent_nodes = sorted(
            graph.nodes(),
            key=lambda n: graph.out_degree(n),
            reverse=True
        )[:min(10, len(graph.nodes()))]  # Top 10 nodes with most dependencies

        # Find paths between highly dependent nodes and important nodes
        for source in dependent_nodes:
            for target in important_nodes:
                try:
                    if source != target and nx.has_path(graph, source, target):
                        path = nx.shortest_path(graph, source, target)
                        if len(path) > 1:  # Only include non-trivial paths
                            critical_paths.append(path)
                except nx.NetworkXNoPath:
                    continue

        # Sort paths by length (descending)
        critical_paths.sort(key=len, reverse=True)

        # Return top 20 paths or fewer if there aren't that many
        return critical_paths[:min(20, len(critical_paths))]

    def _identify_test_coverage_gaps(
        self,
        graph: nx.DiGraph,
        repo_structure: RepositoryStructure,
        integration_points: List[IntegrationPoint]
    ) -> Dict[str, float]:
        """
        Identify potential gaps in test coverage.

        Args:
            graph: Dependency graph
            repo_structure: Repository structure
            integration_points: List of integration points

        Returns:
            Dict[str, float]: Dictionary mapping components to a gap score (higher = more important to test)
        """
        test_coverage_gaps = {}

        # Find files that appear to be tested (have corresponding test files)
        tested_files = set()
        for file_path, file_info in repo_structure.files.items():
            if file_info.is_test_file:
                continue  # Skip test files themselves

            # Check if there might be a test for this file
            file_base = Path(file_path).stem
            for test_file in repo_structure.test_files:
                test_base = Path(test_file).stem
                if (
                    file_base in test_base or
                    test_base.replace('test_', '') == file_base or
                    test_base.replace('Test', '') == file_base
                ):
                    tested_files.add(file_path)
                    break

        # Calculate scores based on several factors
        for node in graph.nodes():
            if node in repo_structure.test_files:
                continue  # Skip test files themselves

            # Base score uses centrality in the graph
            centrality = nx.degree_centrality(graph)[node]
            score = centrality * 5  # Scale up for readability

            # Higher score if it's part of important integration points
            involvement_in_integrations = sum(
                point.importance
                for point in integration_points
                if point.source_component == node or point.target_component == node
            )
            score += involvement_in_integrations * 2

            # Higher score if part of critical paths
            critical_path_count = sum(
                1 for path in self._identify_critical_paths(graph) if node in path
            )
            score += critical_path_count * 0.5

            # If the file doesn't appear to be tested, boost the score
            if node not in tested_files:
                score += 2

            # Cap at 10 for readability
            test_coverage_gaps[node] = min(10, score)

        return test_coverage_gaps

    def _calculate_test_coverage_percentage(self, repo_structure: RepositoryStructure) -> float:
        """
        Calculate an estimate of test coverage percentage.

        Args:
            repo_structure: Repository structure

        Returns:
            float: Estimated test coverage percentage
        """
        total_files = len([f for f in repo_structure.files.values() if not f.is_test_file])

        if total_files == 0:
            return 0.0

        # Count files that appear to be tested
        tested_files = 0
        for file_path, file_info in repo_structure.files.items():
            if file_info.is_test_file:
                continue  # Skip test files themselves

            # Check if there might be a test for this file
            file_base = Path(file_path).stem
            for test_file in repo_structure.test_files:
                test_base = Path(test_file).stem
                if (
                    file_base in test_base or
                    test_base.replace('test_', '') == file_base or
                    test_base.replace('Test', '') == file_base
                ):
                    tested_files += 1
                    break

        return (tested_files / total_files) * 100

    def _identify_high_risk_components(
        self,
        graph: nx.DiGraph,
        repo_structure: RepositoryStructure,
        test_coverage_gaps: Dict[str, float]
    ) -> List[str]:
        """
        Identify high-risk components that should be prioritized for testing.

        Args:
            graph: Dependency graph
            repo_structure: Repository structure
            test_coverage_gaps: Test coverage gap scores

        Returns:
            List[str]: List of high-risk component file paths
        """
        risk_scores = {}

        for node in graph.nodes():
            if node in repo_structure.test_files:
                continue  # Skip test files

            # Calculate risk based on:
            # 1. Centrality (how many components are affected by this)
            # 2. Test coverage gap score
            # 3. Number of incoming edges (how many components depend on this)
            # 4. Number of outgoing edges (how many dependencies it has)

            centrality = nx.degree_centrality(graph)[node]
            gap_score = test_coverage_gaps.get(node, 0)
            in_degree = graph.in_degree(node)
            out_degree = graph.out_degree(node)

            risk_score = (
                centrality * 3 +
                gap_score / 10 * 4 +
                in_degree / 10 +
                out_degree / 20
            )

            risk_scores[node] = risk_score

        # Sort by risk score (descending)
        high_risk = sorted(risk_scores.items(), key=lambda x: x[1], reverse=True)

        # Return top 10 or fewer if there aren't that many
        return [node for node, _ in high_risk[:min(10, len(high_risk))]]
