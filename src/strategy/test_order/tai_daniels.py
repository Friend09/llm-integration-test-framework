"""Implementation of the Tai-Daniels algorithm for test order generation."""

from typing import Dict, List, Set, Tuple
from collections import defaultdict

from ...models.component import Component
from ...models.relationship import Relationship
from .base import TestOrderGenerator, TestOrderResult


class TaiDanielsOrderGenerator(TestOrderGenerator):
    """Implements the Tai-Daniels algorithm for test order generation.

    The algorithm works by:
    1. Assigning weights to relationships based on type
    2. Calculating component levels based on weighted dependencies
    3. Ordering components within each level based on coupling metrics
    4. Minimizing stubs by considering relationship types
    """

    def __init__(self, *args, **kwargs):
        """Initialize the Tai-Daniels order generator."""
        super().__init__(*args, **kwargs)
        self.relationship_weights = {
            "inheritance": 3,
            "aggregation": 2,
            "association": 1
        }

    def generate_order(self) -> TestOrderResult:
        """Generate a test order using the Tai-Daniels algorithm."""
        # Step 1: Calculate weighted dependencies
        weighted_deps = self._calculate_weighted_dependencies()

        # Step 2: Assign levels to components
        levels = self._assign_levels(weighted_deps)
        level_assignments = {comp: level for level, comps in levels.items() for comp in comps}

        # Step 3: Order components within levels
        ordered_components = self._order_within_levels(levels, weighted_deps)

        # Step 4: Calculate required stubs
        stubs = self.calculate_required_stubs(ordered_components)

        # Generate justification
        justification = self._generate_justification(ordered_components, levels, stubs)

        return self.create_result(
            order=ordered_components,
            stubs=stubs,
            justification=justification,
            level_assignments=level_assignments
        )

    def _calculate_weighted_dependencies(self) -> Dict[Component, Dict[Component, float]]:
        """Calculate weighted dependencies between components."""
        weighted_deps = defaultdict(lambda: defaultdict(float))

        for rel in self.relationships:
            weight = self.relationship_weights.get(rel.relationship_type, 1.0)
            weighted_deps[rel.source][rel.target] += weight * rel.strength

        return weighted_deps

    def _assign_levels(self, weighted_deps: Dict[Component, Dict[Component, float]]) -> Dict[int, List[Component]]:
        """Assign components to levels based on weighted dependencies."""
        levels: Dict[int, List[Component]] = defaultdict(list)
        assigned = set()
        level = 0

        while len(assigned) < len(self.components):
            # Find components with no unassigned dependencies
            level_components = []
            for component in self.components:
                if component in assigned:
                    continue

                has_unassigned_deps = False
                for dep, weight in weighted_deps[component].items():
                    if dep not in assigned and weight > 0:
                        has_unassigned_deps = True
                        break

                if not has_unassigned_deps:
                    level_components.append(component)

            # Handle cycles by choosing component with minimum dependencies
            if not level_components:
                min_deps = float('inf')
                cycle_component = None

                for component in self.components:
                    if component in assigned:
                        continue

                    unassigned_deps = sum(
                        1 for dep, weight in weighted_deps[component].items()
                        if dep not in assigned and weight > 0
                    )

                    if unassigned_deps < min_deps:
                        min_deps = unassigned_deps
                        cycle_component = component

                if cycle_component:
                    level_components.append(cycle_component)

            # Add components to current level
            levels[level].extend(level_components)
            assigned.update(level_components)
            level += 1

        return levels

    def _order_within_levels(
        self,
        levels: Dict[int, List[Component]],
        weighted_deps: Dict[Component, Dict[Component, float]]
    ) -> List[Component]:
        """Order components within each level based on coupling metrics."""
        ordered_components = []

        for level in sorted(levels.keys()):
            level_components = levels[level]

            # Sort components by coupling metrics
            sorted_components = sorted(
                level_components,
                key=lambda c: (
                    -sum(weighted_deps[c].values()),  # Higher weighted dependencies first
                    -self.get_dependent_count(c),     # More dependents first
                    -c.complexity_score,              # Higher complexity first
                    -c.importance_score              # Higher importance first
                )
            )

            ordered_components.extend(sorted_components)

        return ordered_components

    def _generate_justification(
        self,
        order: List[Component],
        levels: Dict[int, List[Component]],
        stubs: Dict[Component, Set[Component]]
    ) -> List[str]:
        """Generate justification for the test order."""
        justification = [
            f"Test order generated using Tai-Daniels algorithm with {len(levels)} levels",
            f"Components ordered based on relationship types (inheritance: {self.relationship_weights['inheritance']}, "
            f"aggregation: {self.relationship_weights['aggregation']}, "
            f"association: {self.relationship_weights['association']})"
        ]

        # Add level information
        for level, components in levels.items():
            justification.append(f"Level {level}: {len(components)} components")

        # Add stub information
        total_stubs = sum(len(stub_set) for stub_set in stubs.values())
        components_with_stubs = sum(1 for stub_set in stubs.values() if stub_set)
        justification.extend([
            f"Total stubs required: {total_stubs}",
            f"Components requiring stubs: {components_with_stubs}"
        ])

        # Add specific component ordering justification
        for i, component in enumerate(order):
            deps = self.get_component_dependencies(component)
            deps_str = ", ".join(d.name for d in deps) if deps else "none"
            stub_str = ", ".join(s.name for s in stubs[component]) if stubs[component] else "none"
            justification.append(
                f"{i+1}. Testing {component.name} - Dependencies: {deps_str} - "
                f"Required stubs: {stub_str}"
            )

        return justification
