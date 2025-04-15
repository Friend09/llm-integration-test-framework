"""Test order algorithm selector and comparison module."""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import networkx as nx

from .test_order.base import TestOrderGenerator, TestOrderResult
from .test_order.tai_daniels import TaiDanielsOrderGenerator
from .test_order.tjjm import TJJMOrderGenerator
from .test_order.blw import BLWOrderGenerator
from ..models.component import Component
from ..models.dependency_graph import DependencyGraph


@dataclass
class AlgorithmComparison:
    """Comparison results between different test order algorithms."""
    algorithm_name: str
    total_stubs: int
    stub_complexity: float
    test_sequence_quality: float
    suitability_score: float
    justification: List[str]


class TestOrderSelector:
    """Selects the most appropriate test order algorithm based on project characteristics."""

    def __init__(self, dependency_graph: DependencyGraph):
        """Initialize the selector with a dependency graph."""
        self.dependency_graph = dependency_graph
        self.algorithms = {
            'Tai-Daniels': TaiDanielsOrderGenerator(dependency_graph),
            'TJJM': TJJMOrderGenerator(dependency_graph),
            'BLW': BLWOrderGenerator(dependency_graph)
        }

    def compare_algorithms(self) -> Dict[str, AlgorithmComparison]:
        """Compare all available algorithms and return their metrics."""
        comparisons = {}

        for name, algorithm in self.algorithms.items():
            result = algorithm.generate_order()
            comparison = self._evaluate_algorithm(name, result)
            comparisons[name] = comparison

        return comparisons

    def select_best_algorithm(self) -> Tuple[str, TestOrderResult, List[str]]:
        """Select the best algorithm based on project characteristics and results."""
        comparisons = self.compare_algorithms()

        # Calculate weighted scores
        weights = self._calculate_weights()
        best_algorithm = None
        best_score = float('-inf')
        justification = []

        for name, comparison in comparisons.items():
            score = (
                weights['stubs'] * (1.0 / (comparison.total_stubs + 1)) +
                weights['complexity'] * (1.0 / (comparison.stub_complexity + 1)) +
                weights['quality'] * comparison.test_sequence_quality +
                weights['suitability'] * comparison.suitability_score
            )

            if score > best_score:
                best_score = score
                best_algorithm = name

        # Generate justification
        justification.append(f"Selected {best_algorithm} as the best algorithm based on:")
        justification.extend(comparisons[best_algorithm].justification)

        # Generate final result
        result = self.algorithms[best_algorithm].generate_order()

        return best_algorithm, result, justification

    def _evaluate_algorithm(self, name: str, result: TestOrderResult) -> AlgorithmComparison:
        """Evaluate an algorithm's performance based on multiple criteria."""
        total_stubs = sum(len(stubs) for stubs in result.stubs.values())
        stub_complexity = self._calculate_stub_complexity(result)
        test_sequence_quality = self._evaluate_test_sequence(result)
        suitability_score = self._calculate_suitability(name, result)

        justification = [
            f"Total stubs required: {total_stubs}",
            f"Overall stub complexity: {stub_complexity:.2f}",
            f"Test sequence quality score: {test_sequence_quality:.2f}",
            f"Project suitability score: {suitability_score:.2f}"
        ]

        return AlgorithmComparison(
            algorithm_name=name,
            total_stubs=total_stubs,
            stub_complexity=stub_complexity,
            test_sequence_quality=test_sequence_quality,
            suitability_score=suitability_score,
            justification=justification
        )

    def _calculate_stub_complexity(self, result: TestOrderResult) -> float:
        """Calculate the overall complexity of required stubs."""
        total_complexity = 0.0

        for component, stubs in result.stubs.items():
            for stub in stubs:
                # Base complexity from stub's complexity score
                base_complexity = stub.complexity_score if stub.complexity_score is not None else 0.5

                # Add relationship type multiplier
                rel = self.dependency_graph.get_relationship(component, stub)
                type_multiplier = {
                    'inheritance': 2.0,
                    'aggregation': 1.5,
                    'association': 1.0
                }.get(rel.relationship_type, 1.0)

                total_complexity += base_complexity * type_multiplier

        return total_complexity

    def _evaluate_test_sequence(self, result: TestOrderResult) -> float:
        """Evaluate the quality of the test sequence."""
        if not result.order:
            return 0.0

        score = 0.0
        max_level = max(result.level_assignments.values())

        # Evaluate level distribution (prefer balanced levels)
        level_counts = [0] * (max_level + 1)
        for level in result.level_assignments.values():
            level_counts[level] += 1

        avg_components_per_level = len(result.order) / (max_level + 1)
        level_balance = 1.0 - sum(abs(count - avg_components_per_level)
                                 for count in level_counts) / len(result.order)

        # Evaluate dependency preservation
        preserved_deps = 0
        total_deps = 0

        for component in result.order:
            deps = self.dependency_graph.get_dependencies(component)
            total_deps += len(deps)
            for dep in deps:
                if dep.target not in result.stubs[component]:
                    preserved_deps += 1

        dependency_score = preserved_deps / total_deps if total_deps > 0 else 1.0

        # Combine scores (equal weights)
        score = (level_balance + dependency_score) / 2
        return score

    def _calculate_suitability(self, algorithm_name: str, result: TestOrderResult) -> float:
        """Calculate how suitable the algorithm is for the project structure."""
        # Analyze graph characteristics
        graph = self.dependency_graph.graph
        n_components = len(self.dependency_graph.get_components())
        n_edges = graph.number_of_edges()

        # Calculate graph metrics
        density = nx.density(graph)
        try:
            avg_clustering = nx.average_clustering(graph)
        except:
            avg_clustering = 0

        # Calculate suitability scores based on algorithm strengths
        if algorithm_name == 'Tai-Daniels':
            # Better for hierarchical structures with clear levels
            score = (1 - density) * 0.6 + (1 - avg_clustering) * 0.4

        elif algorithm_name == 'TJJM':
            # Better for moderately connected graphs with some cycles
            score = (density * 0.4 + avg_clustering * 0.6)

        elif algorithm_name == 'BLW':
            # Better for complex graphs with many specific dependencies
            score = (density * 0.5 + avg_clustering * 0.5)

        else:
            score = 0.5  # Default score for unknown algorithms

        return score

    def _calculate_weights(self) -> Dict[str, float]:
        """Calculate weights for different metrics based on project characteristics."""
        graph = self.dependency_graph.graph
        density = nx.density(graph)

        # Adjust weights based on graph characteristics
        if density < 0.3:  # Sparse graph
            return {
                'stubs': 0.4,
                'complexity': 0.2,
                'quality': 0.3,
                'suitability': 0.1
            }
        elif density > 0.7:  # Dense graph
            return {
                'stubs': 0.2,
                'complexity': 0.4,
                'quality': 0.2,
                'suitability': 0.2
            }
        else:  # Moderate density
            return {
                'stubs': 0.3,
                'complexity': 0.3,
                'quality': 0.2,
                'suitability': 0.2
            }
