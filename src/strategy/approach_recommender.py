"""Test approach recommendation module."""

from dataclasses import dataclass
from typing import Dict, List, Set, Tuple
import networkx as nx

from ..models.dependency_graph import DependencyGraph
from ..models.component import Component
from ..models.integration_points.base import IntegrationPoint


@dataclass
class TestingApproach:
    """Represents a recommended testing approach."""

    name: str  # top-down, bottom-up, hybrid, big-bang
    score: float  # Suitability score (0.0 to 1.0)
    justification: List[str]  # Reasons for recommending this approach
    estimated_effort: Dict[str, float]  # Estimated effort for different aspects
    prerequisites: List[str]  # Required setup and infrastructure
    risks: List[str]  # Potential risks and challenges
    advantages: List[str]  # Benefits of this approach
    disadvantages: List[str]  # Drawbacks of this approach


class TestApproachRecommender:
    """Analyzes codebase and recommends testing approaches."""

    def __init__(self, dependency_graph: DependencyGraph, integration_points: List[IntegrationPoint]):
        """Initialize the test approach recommender."""
        self.dependency_graph = dependency_graph
        self.integration_points = integration_points
        self.critical_components = self.dependency_graph.get_critical_components()

    def recommend_approach(self) -> TestingApproach:
        """Analyze the codebase and recommend the best testing approach."""
        # Calculate scores for each approach
        top_down_score = self._evaluate_top_down()
        bottom_up_score = self._evaluate_bottom_up()
        hybrid_score = self._evaluate_hybrid()
        big_bang_score = self._evaluate_big_bang()

        # Select the approach with the highest score
        approaches = [
            ("top-down", top_down_score),
            ("bottom-up", bottom_up_score),
            ("hybrid", hybrid_score),
            ("big-bang", big_bang_score)
        ]
        best_approach, best_score = max(approaches, key=lambda x: x[1])

        return self._create_approach_recommendation(best_approach, best_score)

    def _evaluate_top_down(self) -> float:
        """Evaluate suitability of top-down testing approach."""
        score = 0.0

        # Check if there's a clear hierarchical structure
        if self._has_clear_hierarchy():
            score += 0.3

        # Check if high-level components are well-defined
        if self._has_well_defined_interfaces():
            score += 0.2

        # Check if there are more interface-level integration points
        if self._has_more_interface_integrations():
            score += 0.2

        # Check if stubs can be easily created
        if self._can_create_stubs_easily():
            score += 0.2

        # Check for minimal circular dependencies
        if not self._has_significant_cycles():
            score += 0.1

        return score

    def _evaluate_bottom_up(self) -> float:
        """Evaluate suitability of bottom-up testing approach."""
        score = 0.0

        # Check if there are complex low-level components
        if self._has_complex_low_level_components():
            score += 0.3

        # Check if there are many database/external service dependencies
        if self._has_many_external_dependencies():
            score += 0.2

        # Check if components can be tested in isolation
        if self._can_test_in_isolation():
            score += 0.2

        # Check if there are clear component boundaries
        if self._has_clear_boundaries():
            score += 0.2

        # Check for minimal upward dependencies
        if not self._has_significant_upward_dependencies():
            score += 0.1

        return score

    def _evaluate_hybrid(self) -> float:
        """Evaluate suitability of hybrid testing approach."""
        score = 0.0

        # Check if there's a mix of hierarchical and non-hierarchical structures
        if self._has_mixed_architecture():
            score += 0.3

        # Check if there are independent subsystems
        if self._has_independent_subsystems():
            score += 0.2

        # Check if there's a balance of integration types
        if self._has_balanced_integration_types():
            score += 0.2

        # Check if critical components are spread across levels
        if self._has_distributed_critical_components():
            score += 0.2

        # Check for moderate complexity
        if self._has_moderate_complexity():
            score += 0.1

        return score

    def _evaluate_big_bang(self) -> float:
        """Evaluate suitability of big bang testing approach."""
        score = 0.0

        # Check if it's a small system
        if self._is_small_system():
            score += 0.3

        # Check if there are few integration points
        if self._has_few_integration_points():
            score += 0.2

        # Check if components are tightly coupled
        if self._is_tightly_coupled():
            score += 0.2

        # Check if quick feedback is needed
        if self._needs_quick_feedback():
            score += 0.2

        # Check if there are few external dependencies
        if not self._has_many_external_dependencies():
            score += 0.1

        return score

    def _create_approach_recommendation(self, approach: str, score: float) -> TestingApproach:
        """Create a detailed recommendation for the selected approach."""
        if approach == "top-down":
            return self._create_top_down_recommendation(score)
        elif approach == "bottom-up":
            return self._create_bottom_up_recommendation(score)
        elif approach == "hybrid":
            return self._create_hybrid_recommendation(score)
        else:
            return self._create_big_bang_recommendation(score)

    def _create_top_down_recommendation(self, score: float) -> TestingApproach:
        """Create a recommendation for top-down testing approach."""
        return TestingApproach(
            name="top-down",
            score=score,
            justification=[
                "Clear hierarchical structure in the codebase",
                "Well-defined interfaces between components",
                "More interface-level integration points",
                "Stubs can be easily created for lower-level components"
            ],
            estimated_effort={
                "stub_creation": 0.3,
                "interface_testing": 0.4,
                "integration_testing": 0.3
            },
            prerequisites=[
                "Interface specifications for all components",
                "Mocking framework for creating stubs",
                "Test environment for high-level components"
            ],
            risks=[
                "Late detection of low-level problems",
                "Stub maintenance overhead",
                "Potential mismatch between stubs and actual components"
            ],
            advantages=[
                "Early testing of high-level functionality",
                "Early feedback on architecture",
                "Parallel development of lower-level components",
                "Good for user-oriented testing"
            ],
            disadvantages=[
                "Requires significant stub creation",
                "May miss low-level integration issues",
                "Stub maintenance can be complex"
            ]
        )

    def _create_bottom_up_recommendation(self, score: float) -> TestingApproach:
        """Create a recommendation for bottom-up testing approach."""
        return TestingApproach(
            name="bottom-up",
            score=score,
            justification=[
                "Complex low-level components present",
                "Many database and external service dependencies",
                "Components can be tested in isolation",
                "Clear component boundaries"
            ],
            estimated_effort={
                "unit_testing": 0.4,
                "component_testing": 0.3,
                "integration_testing": 0.3
            },
            prerequisites=[
                "Unit testing framework",
                "Test data for low-level components",
                "Mock objects for external dependencies"
            ],
            risks=[
                "Late detection of interface problems",
                "Integration issues may be found late",
                "May need significant rework if high-level changes occur"
            ],
            advantages=[
                "Early detection of low-level problems",
                "Reduced need for stubs",
                "More thorough testing of core components",
                "Good for data-intensive applications"
            ],
            disadvantages=[
                "Late feedback on system behavior",
                "May miss interface issues until late",
                "Can be slower to show progress"
            ]
        )

    def _create_hybrid_recommendation(self, score: float) -> TestingApproach:
        """Create a recommendation for hybrid testing approach."""
        return TestingApproach(
            name="hybrid",
            score=score,
            justification=[
                "Mixed architectural patterns present",
                "Independent subsystems identified",
                "Balanced mix of integration types",
                "Critical components distributed across levels"
            ],
            estimated_effort={
                "critical_path_testing": 0.3,
                "subsystem_testing": 0.4,
                "integration_testing": 0.3
            },
            prerequisites=[
                "Both unit and integration test frameworks",
                "Test environments for different levels",
                "Good understanding of component dependencies"
            ],
            risks=[
                "Complexity in managing different approaches",
                "Potential gaps between approaches",
                "Resource allocation challenges"
            ],
            advantages=[
                "Flexible and adaptable approach",
                "Balanced coverage of system",
                "Can prioritize critical components",
                "Good for complex systems"
            ],
            disadvantages=[
                "More complex to manage",
                "Requires more planning",
                "May need more resources"
            ]
        )

    def _create_big_bang_recommendation(self, score: float) -> TestingApproach:
        """Create a recommendation for big bang testing approach."""
        return TestingApproach(
            name="big-bang",
            score=score,
            justification=[
                "Small system with few components",
                "Limited number of integration points",
                "Tightly coupled components",
                "Quick feedback needed"
            ],
            estimated_effort={
                "system_testing": 0.6,
                "defect_fixing": 0.4
            },
            prerequisites=[
                "Complete system implementation",
                "Test environment for whole system",
                "Comprehensive test data"
            ],
            risks=[
                "Difficult to locate problems",
                "All components must be ready",
                "May be overwhelming to fix issues"
            ],
            advantages=[
                "Simple to implement",
                "Quick to execute",
                "No need for stubs/drivers",
                "Good for small systems"
            ],
            disadvantages=[
                "Hard to locate problems",
                "No incremental feedback",
                "All components must be ready"
            ]
        )

    def _has_clear_hierarchy(self) -> bool:
        """Check if the dependency graph has a clear hierarchical structure."""
        # Calculate the number of levels in the graph
        try:
            levels = nx.topological_generations(self.dependency_graph.graph)
            num_levels = sum(1 for _ in levels)
            total_nodes = len(self.dependency_graph.graph)

            # If there are several distinct levels relative to total nodes,
            # consider it hierarchical
            return num_levels >= 3 and num_levels <= total_nodes / 2
        except nx.NetworkXUnfeasible:
            return False

    def _has_well_defined_interfaces(self) -> bool:
        """Check if components have well-defined interfaces."""
        api_points = [p for p in self.integration_points if p.integration_type == "api"]
        return len(api_points) >= len(self.dependency_graph.get_components()) * 0.3

    def _has_more_interface_integrations(self) -> bool:
        """Check if interface-level integrations dominate."""
        interface_count = len([p for p in self.integration_points if p.integration_type == "api"])
        other_count = len([p for p in self.integration_points if p.integration_type != "api"])
        return interface_count > other_count

    def _can_create_stubs_easily(self) -> bool:
        """Check if stubs can be created easily."""
        # Look for well-defined interfaces and limited circular dependencies
        return (self._has_well_defined_interfaces() and
                not self._has_significant_cycles())

    def _has_significant_cycles(self) -> bool:
        """Check if there are significant circular dependencies."""
        cycles = self.dependency_graph.find_cycles()
        return len(cycles) > len(self.dependency_graph.get_components()) * 0.1

    def _has_complex_low_level_components(self) -> bool:
        """Check if there are complex low-level components."""
        # Consider components with high complexity but few dependencies as low-level
        return any(c.complexity_score > 0.7 for c in self.dependency_graph.get_components())

    def _has_many_external_dependencies(self) -> bool:
        """Check if there are many external dependencies."""
        external_points = [p for p in self.integration_points
                         if p.integration_type in ["database", "service"]]
        return len(external_points) >= len(self.dependency_graph.get_components()) * 0.3

    def _can_test_in_isolation(self) -> bool:
        """Check if components can be tested in isolation."""
        # Look for components with minimal dependencies
        return any(len(self.dependency_graph.get_dependencies(c)) <= 2
                  for c in self.dependency_graph.get_components())

    def _has_clear_boundaries(self) -> bool:
        """Check if components have clear boundaries."""
        # Look for limited cross-component dependencies
        for component in self.dependency_graph.get_components():
            deps = self.dependency_graph.get_dependencies(component)
            if len(deps) > 5:  # Arbitrary threshold
                return False
        return True

    def _has_significant_upward_dependencies(self) -> bool:
        """Check if there are significant upward dependencies."""
        try:
            levels = list(nx.topological_generations(self.dependency_graph.graph))
            for i, level in enumerate(levels[:-1]):
                for node in level:
                    successors = set(self.dependency_graph.graph.successors(node))
                    # Check if node has dependencies on higher levels
                    for higher_level in levels[i+1:]:
                        if successors & set(higher_level):
                            return True
            return False
        except nx.NetworkXUnfeasible:
            return True

    def _has_mixed_architecture(self) -> bool:
        """Check if the system has a mix of architectural patterns."""
        has_hierarchy = self._has_clear_hierarchy()
        has_cycles = self._has_significant_cycles()
        return has_hierarchy and has_cycles

    def _has_independent_subsystems(self) -> bool:
        """Check if there are independent subsystems."""
        # Look for strongly connected components
        sccs = self.dependency_graph.get_strongly_connected_components()
        return len(sccs) > 1

    def _has_balanced_integration_types(self) -> bool:
        """Check if there's a balance of integration types."""
        types = [p.integration_type for p in self.integration_points]
        unique_types = set(types)
        if len(unique_types) < 2:
            return False

        # Check if no single type dominates (>60%)
        for type_name in unique_types:
            count = sum(1 for t in types if t == type_name)
            if count / len(types) > 0.6:
                return False
        return True

    def _has_distributed_critical_components(self) -> bool:
        """Check if critical components are distributed across levels."""
        if not self.critical_components:
            return False

        try:
            levels = list(nx.topological_generations(self.dependency_graph.graph))
            critical_levels = set()
            for component in self.critical_components:
                for i, level in enumerate(levels):
                    if component.id in level:
                        critical_levels.add(i)
                        break
            return len(critical_levels) > 1
        except nx.NetworkXUnfeasible:
            return False

    def _has_moderate_complexity(self) -> bool:
        """Check if the system has moderate complexity."""
        num_components = len(self.dependency_graph.get_components())
        num_relationships = len(self.dependency_graph.get_relationships())
        return 5 <= num_components <= 20 and num_relationships <= num_components * 3

    def _is_small_system(self) -> bool:
        """Check if it's a small system."""
        return len(self.dependency_graph.get_components()) <= 5

    def _has_few_integration_points(self) -> bool:
        """Check if there are few integration points."""
        return len(self.integration_points) <= 5

    def _is_tightly_coupled(self) -> bool:
        """Check if components are tightly coupled."""
        num_components = len(self.dependency_graph.get_components())
        num_relationships = len(self.dependency_graph.get_relationships())
        return num_relationships >= (num_components * (num_components - 1)) / 4

    def _needs_quick_feedback(self) -> bool:
        """Check if quick feedback is needed."""
        # This is a heuristic based on system size and complexity
        return self._is_small_system() and not self._has_many_external_dependencies()
