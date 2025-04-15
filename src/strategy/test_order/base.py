"""Base class for test order generation algorithms."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple
from uuid import UUID

from ...models.dependency_graph import DependencyGraph
from ...models.component import Component
from ...models.relationship import Relationship


@dataclass
class TestOrderResult:
    """Result of test order generation."""

    order: List[Component]  # Components in test order
    stubs: Dict[Component, Set[Component]]  # Required stubs for each component
    justification: List[str]  # Reasons for the chosen order
    metrics: Dict[str, float]  # Metrics about the order (e.g., stub count)
    level_assignments: Dict[Component, int]  # Level assigned to each component


class TestOrderGenerator(ABC):
    """Base class for test order generation algorithms."""

    def __init__(self, dependency_graph: DependencyGraph):
        """Initialize the test order generator."""
        self.dependency_graph = dependency_graph
        self.components = dependency_graph.get_components()
        self.relationships = dependency_graph.get_relationships()

    @abstractmethod
    def generate_order(self) -> TestOrderResult:
        """Generate a test order for the components."""
        pass

    def calculate_required_stubs(self, order: List[Component]) -> Dict[Component, Set[Component]]:
        """Calculate required stubs for a given test order."""
        stubs: Dict[Component, Set[Component]] = {comp: set() for comp in self.components}
        tested_components = set()

        for component in order:
            # Get all dependencies of the current component
            dependencies = {rel.target for rel in self.dependency_graph.get_dependencies(component)}

            # Any dependency not yet tested needs a stub
            for dep in dependencies:
                if dep not in tested_components:
                    stubs[component].add(dep)

            tested_components.add(component)

        return stubs

    def calculate_metrics(self, order: List[Component], stubs: Dict[Component, Set[Component]]) -> Dict[str, float]:
        """Calculate metrics for the test order."""
        total_stubs = sum(len(stub_set) for stub_set in stubs.values())
        components_with_stubs = sum(1 for stub_set in stubs.values() if stub_set)

        return {
            "total_stub_count": total_stubs,
            "components_with_stubs": components_with_stubs,
            "average_stubs_per_component": total_stubs / len(self.components) if self.components else 0.0,
            "stub_component_ratio": components_with_stubs / len(self.components) if self.components else 0.0
        }

    def validate_order(self, order: List[Component]) -> bool:
        """Validate that a test order includes all components exactly once."""
        order_set = set(order)
        component_set = set(self.components)

        # Check if all components are included
        if order_set != component_set:
            return False

        # Check for duplicates
        if len(order) != len(order_set):
            return False

        return True

    def get_inheritance_relationships(self) -> List[Relationship]:
        """Get all inheritance relationships in the graph."""
        return [
            rel for rel in self.relationships
            if rel.relationship_type == "inheritance"
        ]

    def get_aggregation_relationships(self) -> List[Relationship]:
        """Get all aggregation relationships in the graph."""
        return [
            rel for rel in self.relationships
            if rel.relationship_type == "aggregation"
        ]

    def get_association_relationships(self) -> List[Relationship]:
        """Get all association relationships in the graph."""
        return [
            rel for rel in self.relationships
            if rel.relationship_type == "association"
        ]

    def get_component_dependencies(self, component: Component) -> Set[Component]:
        """Get all components that a given component depends on."""
        return {
            rel.target for rel in self.dependency_graph.get_dependencies(component)
        }

    def get_component_dependents(self, component: Component) -> Set[Component]:
        """Get all components that depend on a given component."""
        return {
            rel.source for rel in self.dependency_graph.get_dependents(component)
        }

    def get_dependency_count(self, component: Component) -> int:
        """Get the number of dependencies for a component."""
        return len(self.get_component_dependencies(component))

    def get_dependent_count(self, component: Component) -> int:
        """Get the number of components that depend on this component."""
        return len(self.get_component_dependents(component))

    def create_result(
        self,
        order: List[Component],
        stubs: Dict[Component, Set[Component]],
        justification: List[str],
        level_assignments: Dict[Component, int]
    ) -> TestOrderResult:
        """Create a TestOrderResult with calculated metrics."""
        metrics = self.calculate_metrics(order, stubs)
        return TestOrderResult(
            order=order,
            stubs=stubs,
            justification=justification,
            metrics=metrics,
            level_assignments=level_assignments
        )
