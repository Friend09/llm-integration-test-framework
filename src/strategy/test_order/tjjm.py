"""Implementation of the Traon-Jéron-Jézéquel-Morel (TJJM) test order generation algorithm."""

from typing import Dict, List, Set, Tuple
import networkx as nx
from uuid import UUID

from .base import TestOrderGenerator, TestOrderResult
from ...models.component import Component
from ...models.relationship import Relationship


class TJJMOrderGenerator(TestOrderGenerator):
    """Implements the TJJM algorithm for test order generation.

    The TJJM algorithm focuses on:
    1. Identifying strongly connected components
    2. Breaking cycles by selecting optimal edges
    3. Generating a test order that minimizes stubs
    """

    def generate_order(self) -> TestOrderResult:
        """Generate a test order using the TJJM algorithm."""
        justification = []

        # Step 1: Find strongly connected components
        sccs = self.dependency_graph.get_strongly_connected_components()
        justification.append(f"Found {len(sccs)} strongly connected components")

        # If no cycles, use topological sort directly
        if all(len(scc) == 1 for scc in sccs):
            order = list(reversed(self._generate_order_from_dag()))  # Reverse for correct dependencies
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
        for component in order:
            stubs[component] = set()
            for edge in edges_to_remove:
                if edge[0] == component.id:
                    target_comp = self.dependency_graph.get_component(edge[1])
                    stubs[component].add(target_comp)

        # Step 7: Assign levels based on the final order
        level_assignments = self._assign_levels(order)

        # Add stub information to justification
        total_stubs = sum(len(stub_set) for stub_set in stubs.values())
        justification.append(f"Final order requires {total_stubs} stubs")

        return self.create_result(
            order=order,
            stubs=stubs,
            justification=justification,
            level_assignments=level_assignments
        )

    def _find_edges_to_break_cycle(self, scc: Set[Component]) -> List[Tuple[UUID, UUID]]:
        """Find optimal edges to remove to break cycles in a strongly connected component."""
        # Create a mutable copy of the subgraph
        scc_subgraph = nx.DiGraph(self.dependency_graph.graph.subgraph([c.id for c in scc]))
        edges_to_remove = []

        while not self._is_acyclic(scc_subgraph):
            edge = self._select_edge_to_break(scc_subgraph)
            if edge:
                edges_to_remove.append(edge)
                scc_subgraph.remove_edge(*edge)
            else:
                break  # Shouldn't happen, but prevent infinite loop

        return edges_to_remove

    def _select_edge_to_break(self, graph: nx.DiGraph) -> Tuple[UUID, UUID]:
        """Select an edge to break based on TJJM criteria."""
        cycles = list(nx.simple_cycles(graph))
        if not cycles:
            return None

        # Find edges that appear in the most cycles
        edge_cycle_count = {}
        for cycle in cycles:
            for i in range(len(cycle)):
                edge = (cycle[i], cycle[(i + 1) % len(cycle)])
                if edge in graph.edges():
                    edge_cycle_count[edge] = edge_cycle_count.get(edge, 0) + 1

        if not edge_cycle_count:
            return None

        # Select edge that appears in the most cycles and has minimal impact
        best_edge = None
        max_cycles = 0
        min_impact = float('inf')

        for edge, cycle_count in edge_cycle_count.items():
            # Calculate impact (number of paths that would require stubs)
            impact = len(list(nx.descendants(graph, edge[1])))

            if cycle_count > max_cycles or (cycle_count == max_cycles and impact < min_impact):
                max_cycles = cycle_count
                min_impact = impact
                best_edge = edge

        return best_edge

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
            node_order = list(reversed(list(nx.topological_sort(modified_graph))))  # Reverse for correct dependencies
            return [self.dependency_graph.get_component(node_id) for node_id in node_order]
        except nx.NetworkXUnfeasible:
            raise ValueError("Modified graph still contains cycles")

    def _assign_levels(self, order: List[Component]) -> Dict[Component, int]:
        """Assign levels to components based on their position in the test order."""
        return {component: level for level, component in enumerate(order)}
