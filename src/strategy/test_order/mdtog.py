"""Implementation of the Minimum Dependency Test Order Generation algorithm."""

from typing import Dict, List, Set, Tuple
from collections import defaultdict
import networkx as nx

from ...models.component import Component
from ...models.relationship import Relationship
from .base import TestOrderGenerator, TestOrderResult


class MDTOGOrderGenerator(TestOrderGenerator):
    """Implements the Minimum Dependency Test Order Generation algorithm.

    The algorithm works by:
    1. Creating a weighted dependency graph
    2. Finding strongly connected components (SCCs)
    3. Breaking cycles by identifying minimum feedback arc set
    4. Generating a test order that minimizes stub requirements
    """

    def __init__(self, *args, **kwargs):
        """Initialize the MDTOG order generator."""
        super().__init__(*args, **kwargs)
        self.relationship_weights = {
            "inheritance": 3,
            "aggregation": 2,
            "association": 1
        }

    def generate_order(self) -> TestOrderResult:
        """Generate a test order using the MDTOG algorithm."""
        # Step 1: Create weighted dependency graph
        weighted_graph = self._create_weighted_graph()

        # Step 2: Find strongly connected components
        sccs = list(nx.strongly_connected_components(weighted_graph))

        # Step 3: Break cycles using minimum feedback arc set
        ordered_components = self._break_cycles_and_order(weighted_graph, sccs)

        # Step 4: Calculate required stubs
        stubs = self.calculate_required_stubs(ordered_components)

        # Step 5: Assign levels based on dependencies
        level_assignments = self._assign_levels(ordered_components)

        # Generate justification
        justification = self._generate_justification(ordered_components, sccs, stubs)

        return self.create_result(
            order=ordered_components,
            stubs=stubs,
            justification=justification,
            level_assignments=level_assignments
        )

    def _create_weighted_graph(self) -> nx.DiGraph:
        """Create a weighted dependency graph."""
        graph = nx.DiGraph()

        # Add all components as nodes
        for component in self.components:
            graph.add_node(component)

        # Add weighted edges based on relationships
        for rel in self.relationships:
            weight = self.relationship_weights.get(rel.relationship_type, 1.0) * rel.strength
            graph.add_edge(rel.source, rel.target, weight=weight)

        return graph

    def _break_cycles_and_order(
        self,
        graph: nx.DiGraph,
        sccs: List[Set[Component]]
    ) -> List[Component]:
        """Break cycles and create a test order."""
        ordered_components = []
        processed = set()

        # Process SCCs in topological order
        condensed = nx.condensation(graph, scc=sccs)
        for scc_id in nx.topological_sort(condensed):
            scc = sccs[scc_id]

            if len(scc) == 1:
                # Single component, just add it
                component = list(scc)[0]
                if component not in processed:
                    ordered_components.append(component)
                    processed.add(component)
            else:
                # Multiple components, find minimum feedback arc set
                subgraph = graph.subgraph(scc)
                feedback_edges = self._find_minimum_feedback_arc_set(subgraph)

                # Remove feedback edges temporarily
                for u, v in feedback_edges:
                    if graph.has_edge(u, v):
                        graph.remove_edge(u, v)

                # Add components in topological order
                for component in nx.topological_sort(subgraph):
                    if component not in processed:
                        ordered_components.append(component)
                        processed.add(component)

                # Restore feedback edges
                for u, v in feedback_edges:
                    graph.add_edge(u, v)

        return ordered_components

    def _find_minimum_feedback_arc_set(self, graph: nx.DiGraph) -> List[Tuple[Component, Component]]:
        """Find minimum feedback arc set using a greedy algorithm."""
        feedback_edges = []
        while not nx.is_directed_acyclic_graph(graph):
            # Find edge that participates in most cycles
            max_cycles = 0
            worst_edge = None

            for edge in graph.edges():
                graph.remove_edge(*edge)
                num_cycles = len(list(nx.simple_cycles(graph)))
                graph.add_edge(*edge)

                if num_cycles > max_cycles:
                    max_cycles = num_cycles
                    worst_edge = edge

            if worst_edge:
                feedback_edges.append(worst_edge)
                graph.remove_edge(*worst_edge)

        return feedback_edges

    def _assign_levels(self, ordered_components: List[Component]) -> Dict[Component, int]:
        """Assign levels to components based on dependencies."""
        levels = {}
        graph = self._create_weighted_graph()

        for component in ordered_components:
            # Find maximum level of dependencies
            max_dep_level = -1
            for pred in graph.predecessors(component):
                if pred in levels:
                    max_dep_level = max(max_dep_level, levels[pred])

            # Assign level one higher than maximum dependency
            levels[component] = max_dep_level + 1

        return levels

    def _generate_justification(
        self,
        order: List[Component],
        sccs: List[Set[Component]],
        stubs: Dict[Component, Set[Component]]
    ) -> List[str]:
        """Generate justification for the test order."""
        justification = [
            f"Test order generated using MDTOG algorithm",
            f"Found {len(sccs)} strongly connected components"
        ]

        # Add SCC information
        for i, scc in enumerate(sccs):
            if len(scc) > 1:
                justification.append(
                    f"SCC {i+1}: {len(scc)} components - "
                    f"{', '.join(c.name for c in scc)}"
                )

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
