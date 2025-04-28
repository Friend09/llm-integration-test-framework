"""DependencyGraph class for managing and analyzing component relationships."""

from typing import Dict, List, Set, Optional, Tuple
import networkx as nx
from uuid import UUID

from .component import Component
from .relationship import Relationship


class DependencyGraph:
    """Manages and analyzes relationships between components using a directed graph."""

    def __init__(self):
        """Initialize an empty dependency graph."""
        self.graph = nx.DiGraph()
        self.components: Dict[UUID, Component] = {}
        self.relationships: Dict[UUID, Relationship] = {}

    def add_component(self, component: Component) -> None:
        """Add a component to the graph."""
        self.components[component.id] = component
        self.graph.add_node(component.id, component=component)

    def add_relationship(self, relationship: Relationship) -> None:
        """Add a relationship to the graph."""
        self.relationships[relationship.id] = relationship
        self.graph.add_edge(
            relationship.source.id,
            relationship.target.id,
            relationship=relationship
        )

    def get_component(self, component_id: UUID) -> Optional[Component]:
        """Get a component by its ID."""
        return self.components.get(component_id)

    def get_relationship(self, relationship_id: UUID) -> Optional[Relationship]:
        """Get a relationship by its ID."""
        return self.relationships.get(relationship_id)

    def get_components(self) -> List[Component]:
        """Get all components in the graph."""
        return list(self.components.values())

    def get_relationships(self) -> List[Relationship]:
        """Get all relationships in the graph."""
        return list(self.relationships.values())

    def get_dependencies(self, component: Component) -> List[Relationship]:
        """Get all outgoing dependencies for a component."""
        return [
            self.graph.edges[component.id, target_id]["relationship"]
            for target_id in self.graph.successors(component.id)
        ]

    def get_dependents(self, component: Component) -> List[Relationship]:
        """Get all incoming dependencies for a component."""
        return [
            self.graph.edges[source_id, component.id]["relationship"]
            for source_id in self.graph.predecessors(component.id)
        ]

    def find_cycles(self) -> List[List[Component]]:
        """Find all cycles in the dependency graph."""
        cycles = list(nx.simple_cycles(self.graph))
        return [
            [self.components[node_id] for node_id in cycle]
            for cycle in cycles
        ]

    def get_strongly_connected_components(self) -> List[Set[Component]]:
        """Find strongly connected components in the graph."""
        sccs = nx.strongly_connected_components(self.graph)
        return [
            {self.components[node_id] for node_id in scc}
            for scc in sccs
        ]

    def calculate_centrality_metrics(self) -> Dict[UUID, Dict[str, float]]:
        """Calculate various centrality metrics for components."""
        metrics = {}

        # Degree centrality
        in_degree = nx.in_degree_centrality(self.graph)
        out_degree = nx.out_degree_centrality(self.graph)

        # Betweenness centrality
        betweenness = nx.betweenness_centrality(self.graph)

        # Closeness centrality
        try:
            closeness = nx.closeness_centrality(self.graph)
        except nx.NetworkXError:  # Handle disconnected graphs
            closeness = {node: 0.0 for node in self.graph.nodes()}

        for node_id in self.graph.nodes():
            metrics[node_id] = {
                "in_degree": in_degree[node_id],
                "out_degree": out_degree[node_id],
                "betweenness": betweenness[node_id],
                "closeness": closeness[node_id]
            }

        return metrics

    def get_critical_components(self, threshold: float = 0.7) -> List[Component]:
        """Identify critical components based on centrality metrics."""
        metrics = self.calculate_centrality_metrics()
        critical_components = []

        for component_id, metric_values in metrics.items():
            # Calculate an overall importance score
            importance_score = (
                metric_values["in_degree"] +
                metric_values["out_degree"] +
                metric_values["betweenness"] +
                metric_values["closeness"]
            ) / 4.0

            component = self.components[component_id]
            if importance_score >= threshold:
                critical_components.append(component)

        return sorted(
            critical_components,
            key=lambda c: metrics[c.id]["betweenness"],
            reverse=True
        )

    def to_dict(self) -> Dict:
        """Convert the dependency graph to a dictionary representation."""
        return {
            "components": [comp.to_dict() for comp in self.components.values()],
            "relationships": [rel.to_dict() for rel in self.relationships.values()]
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "DependencyGraph":
        """Create a DependencyGraph instance from a dictionary."""
        graph = cls()

        # First, create all components
        components = {}
        for comp_data in data["components"]:
            component = Component.from_dict(comp_data)
            components[str(component.id)] = component
            graph.add_component(component)

        # Then create relationships
        for rel_data in data["relationships"]:
            relationship = Relationship.from_dict(rel_data, components)
            graph.add_relationship(relationship)

        return graph
