"""Implementation of the Briand-Labiche-Wang (BLW) test order generation algorithm."""

from typing import Dict, List, Set, Tuple
import networkx as nx
from uuid import UUID

from .base import TestOrderGenerator, TestOrderResult
from ...models.component import Component
from ...models.relationship import Relationship


class BLWOrderGenerator(TestOrderGenerator):
    """Implements the BLW algorithm for test order generation.

    The BLW algorithm focuses on:
    1. Identifying strongly connected components
    2. Breaking cycles by selecting edges based on stub complexity
    3. Prioritizing association edges over inheritance/aggregation
    4. Generating a test order that minimizes specific stub complexity
    """

    def generate_order(self) -> TestOrderResult:
        """Generate a test order using the BLW algorithm."""
        justification = []

        # Step 1: Find strongly connected components
        sccs = self.dependency_graph.get_strongly_connected_components()
        justification.append(f"Found {len(sccs)} strongly connected components")

        # If no cycles, use topological sort directly
        if all(len(scc) == 1 for scc in sccs):
            order = list(reversed(self._generate_order_from_dag()))
            stubs = self.calculate_required_stubs(order)
            justification.append("No cycles found, using topological sort")
            return self.create_result(
                order=order,
                stubs=stubs,
                justification=justification,
                level_assignments=self._assign_levels(order)
            )

        # Step 2: Create a copy of the graph for modification
        modified_graph = nx.DiGraph(self.dependency_graph.graph)

        # Step 3: Process each SCC with more than one component
        edges_to_remove = []
        for scc in sccs:
            if len(scc) > 1:
                scc_edges = self._find_edges_to_break_cycle(scc)
                edges_to_remove.extend(scc_edges)
                justification.append(
                    f"Breaking cycle in SCC of size {len(scc)} by removing {len(scc_edges)} edges"
                )

        # Step 4: Remove selected edges
        for edge in edges_to_remove:
            modified_graph.remove_edge(edge[0], edge[1])

        # Step 5: Generate order from the modified (acyclic) graph
        order = self._generate_order_from_modified_graph(modified_graph)

        # Step 6: Calculate required stubs based on removed edges
        stubs = {}
        total_complexity = 0
        for component in order:
            stubs[component] = set()
            for edge in edges_to_remove:
                if edge[0] == component.id:
                    target_comp = self.dependency_graph.get_component(edge[1])
                    stubs[component].add(target_comp)
                    total_complexity += self._calculate_stub_complexity(component, target_comp)

        # Step 7: Assign levels based on the final order
        level_assignments = self._assign_levels(order)

        # Add stub complexity information to justification
        justification.append(f"Final order requires {len(edges_to_remove)} stubs with total complexity score: {total_complexity:.2f}")

        return self.create_result(
            order=order,
            stubs=stubs,
            justification=justification,
            level_assignments=level_assignments
        )

    def _find_edges_to_break_cycle(self, scc: Set[Component]) -> List[Tuple[UUID, UUID]]:
        """Find optimal edges to remove to break cycles in a strongly connected component.

        BLW prioritizes:
        1. Association edges over inheritance/aggregation
        2. Edges with lower stub complexity
        3. Edges that break multiple cycles
        """
        scc_subgraph = nx.DiGraph(self.dependency_graph.graph.subgraph([c.id for c in scc]))
        edges_to_remove = []

        while not self._is_acyclic(scc_subgraph):
            edge = self._select_edge_to_break(scc_subgraph)
            if edge:
                edges_to_remove.append(edge)
                scc_subgraph.remove_edge(*edge)
            else:
                break

        return edges_to_remove

    def _select_edge_to_break(self, graph: nx.DiGraph) -> Tuple[UUID, UUID]:
        """Select an edge to break based on BLW criteria."""
        cycles = list(nx.simple_cycles(graph))
        if not cycles:
            return None

        # Get all edges in cycles with their relationship types
        edge_info = {}
        for cycle in cycles:
            for i in range(len(cycle)):
                edge = (cycle[i], cycle[(i + 1) % len(cycle)])
                if edge in graph.edges():
                    if edge not in edge_info:
                        source = self.dependency_graph.get_component(edge[0])
                        target = self.dependency_graph.get_component(edge[1])
                        rel_type = self.dependency_graph.get_relationship(source, target).relationship_type
                        complexity = self._calculate_stub_complexity(source, target)
                        cycle_count = 1
                        edge_info[edge] = {
                            'type': rel_type,
                            'complexity': complexity,
                            'cycle_count': cycle_count
                        }
                    else:
                        edge_info[edge]['cycle_count'] += 1

        # First, try to find association edges
        association_edges = {e: info for e, info in edge_info.items()
                           if info['type'] == 'association'}

        if association_edges:
            candidates = association_edges
        else:
            candidates = edge_info

        # Select edge with best score (highest cycles broken per complexity)
        best_edge = None
        best_score = -1

        for edge, info in candidates.items():
            score = info['cycle_count'] / (info['complexity'] + 1)  # Add 1 to avoid division by zero
            if score > best_score:
                best_score = score
                best_edge = edge

        return best_edge

    def _calculate_stub_complexity(self, source: Component, target: Component) -> float:
        """Calculate the complexity of creating a stub for the target component.

        BLW considers:
        1. Component complexity score
        2. Number of methods that need to be stubbed
        3. Parameter and return type complexity
        """
        # Base complexity from the target component's complexity score
        base_complexity = target.complexity_score if target.complexity_score is not None else 0.5

        # Add complexity based on the relationship type
        rel = self.dependency_graph.get_relationship(source, target)
        type_multiplier = {
            'inheritance': 2.0,  # Inheritance stubs are most complex
            'aggregation': 1.5,  # Aggregation stubs are moderately complex
            'association': 1.0   # Association stubs are least complex
        }.get(rel.relationship_type, 1.0)

        return base_complexity * type_multiplier

    def _is_acyclic(self, graph: nx.DiGraph) -> bool:
        """Check if a graph is acyclic."""
        try:
            nx.find_cycle(graph)
            return False
        except nx.NetworkXNoCycle:
            return True

    def _generate_order_from_dag(self) -> List[Component]:
        """Generate a test order from a directed acyclic graph using topological sort."""
        try:
            node_order = list(nx.topological_sort(self.dependency_graph.graph))
            return [self.dependency_graph.get_component(node_id) for node_id in node_order]
        except nx.NetworkXUnfeasible:
            raise ValueError("Graph contains cycles, cannot perform topological sort")

    def _generate_order_from_modified_graph(self, modified_graph: nx.DiGraph) -> List[Component]:
        """Generate a test order from the modified graph."""
        try:
            node_order = list(reversed(list(nx.topological_sort(modified_graph))))
            return [self.dependency_graph.get_component(node_id) for node_id in node_order]
        except nx.NetworkXUnfeasible:
            raise ValueError("Modified graph still contains cycles")

    def _assign_levels(self, order: List[Component]) -> Dict[Component, int]:
        """Assign levels to components based on their position in the test order."""
        return {component: level for level, component in enumerate(order)}
