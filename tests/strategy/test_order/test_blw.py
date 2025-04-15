"""Unit tests for the BLW test order generation algorithm."""

import pytest
import networkx as nx
from uuid import uuid4

from src.models.component import Component
from src.models.relationship import Relationship
from src.models.dependency_graph import DependencyGraph
from src.strategy.test_order.blw import BLWOrderGenerator


@pytest.fixture
def complex_components():
    """Create a set of components with varying complexity for testing."""
    components = []
    for i in range(6):
        comp = Component(
            name=f"Component{i}",
            component_type="class",
            location=f"file{i}.py",
            complexity_score=0.5 * i  # Varying complexity
        )
        # Add method count metadata for some components
        if i > 2:
            comp.add_metadata("method_count", str(i))
        components.append(comp)
    return components


@pytest.fixture
def mixed_dependency_graph(complex_components):
    """Create a dependency graph with mixed relationship types."""
    graph = DependencyGraph()

    # Add components
    for component in complex_components:
        graph.add_component(component)

    # Create relationships with different types
    relationships = [
        # Cycle 1 with mixed relationships
        Relationship(complex_components[0], complex_components[1], "inheritance"),
        Relationship(complex_components[1], complex_components[2], "association"),
        Relationship(complex_components[2], complex_components[0], "aggregation"),
        # Cycle 2 with only associations
        Relationship(complex_components[3], complex_components[4], "association"),
        Relationship(complex_components[4], complex_components[5], "association"),
        Relationship(complex_components[5], complex_components[3], "association"),
        # Cross-cycle relationship
        Relationship(complex_components[2], complex_components[4], "association")
    ]

    for rel in relationships:
        graph.add_relationship(rel)

    return graph


def test_association_edge_priority(mixed_dependency_graph):
    """Test that BLW algorithm prioritizes breaking association edges."""
    generator = BLWOrderGenerator(mixed_dependency_graph)
    result = generator.generate_order()

    # Get the broken edges (those requiring stubs)
    broken_edges = set()
    for component, stub_set in result.stubs.items():
        for stub in stub_set:
            broken_edges.add((component.name, stub.name))

    # Verify that association edges were broken before inheritance/aggregation
    # In cycle 1, the association edge should be broken
    assert ("Component1", "Component2") in broken_edges
    # The inheritance edge should be preserved if possible
    assert ("Component0", "Component1") not in broken_edges


def test_specific_stub_minimization(mixed_dependency_graph):
    """Test that BLW algorithm minimizes specific stubs based on method count."""
    generator = BLWOrderGenerator(mixed_dependency_graph)
    result = generator.generate_order()

    # Calculate specific stub count
    specific_stubs = generator._calculate_specific_stub_count(result.stubs)

    # Create a reversed order (which should require more stubs)
    reversed_order = list(reversed(result.order))
    reversed_stubs = generator.calculate_required_stubs(reversed_order)
    reversed_specific_stubs = generator._calculate_specific_stub_count(reversed_stubs)

    # BLW should produce fewer specific stubs
    assert specific_stubs < reversed_specific_stubs


def test_stub_complexity_consideration(mixed_dependency_graph):
    """Test that BLW algorithm considers stub complexity in its decisions."""
    generator = BLWOrderGenerator(mixed_dependency_graph)
    result = generator.generate_order()

    # Components with higher complexity scores and method counts should be
    # less likely to be stubbed
    high_complexity_components = {comp for comp in mixed_dependency_graph.get_components()
                                if comp.complexity_score > 1.0 or
                                int(comp.metadata.get("method_count", "1")) > 2}

    # Count how many high-complexity components are stubbed
    high_complexity_stubs = 0
    for stub_set in result.stubs.values():
        high_complexity_stubs += len(stub_set.intersection(high_complexity_components))

    # There should be relatively few high-complexity stubs
    assert high_complexity_stubs <= len(high_complexity_components) // 2


def test_cycle_breaking_efficiency(mixed_dependency_graph):
    """Test that BLW algorithm efficiently breaks cycles."""
    generator = BLWOrderGenerator(mixed_dependency_graph)
    result = generator.generate_order()

    # Create a graph from the resulting order
    test_graph = nx.DiGraph()
    for component in result.order:
        test_graph.add_node(component.id)

    # Add edges that don't require stubs
    for component in result.order:
        deps = mixed_dependency_graph.get_dependencies(component)
        for dep in deps:
            if dep.target not in result.stubs[component]:
                test_graph.add_edge(component.id, dep.target.id)

    # Verify the resulting graph is acyclic
    assert nx.is_directed_acyclic_graph(test_graph)

    # Verify minimal number of edges were removed
    original_edge_count = mixed_dependency_graph.graph.number_of_edges()
    final_edge_count = test_graph.number_of_edges()
    edges_removed = original_edge_count - final_edge_count

    # The number of removed edges should be close to the minimum needed
    # to break cycles (at least one edge per cycle)
    cycles = list(nx.simple_cycles(mixed_dependency_graph.graph))
    assert edges_removed <= len(cycles) + 1  # Allow for one extra edge


def test_acyclic_graph():
    """Test BLW algorithm with an acyclic graph."""
    graph = DependencyGraph()

    # Create a simple chain: A -> B -> C
    components = [
        Component(name=f"Component{i}", component_type="class", location=f"file{i}.py")
        for i in range(3)
    ]

    for component in components:
        graph.add_component(component)

    # Add only association relationships
    relationships = [
        Relationship(components[0], components[1], "association"),
        Relationship(components[1], components[2], "association")
    ]

    for rel in relationships:
        graph.add_relationship(rel)

    generator = BLWOrderGenerator(graph)
    result = generator.generate_order()

    # Verify the order is correct
    assert len(result.order) == 3
    assert result.order == [components[2], components[1], components[0]]

    # Verify no stubs are required
    assert all(len(stubs) == 0 for stubs in result.stubs.values())


def test_empty_graph():
    """Test BLW algorithm with an empty graph."""
    graph = DependencyGraph()
    generator = BLWOrderGenerator(graph)
    result = generator.generate_order()

    assert len(result.order) == 0
    assert len(result.stubs) == 0
    assert len(result.level_assignments) == 0


def test_single_component():
    """Test BLW algorithm with a single component."""
    graph = DependencyGraph()
    component = Component(
        name="SingleComponent",
        component_type="class",
        location="file.py",
        complexity_score=1.0
    )
    component.add_metadata("method_count", "5")
    graph.add_component(component)

    generator = BLWOrderGenerator(graph)
    result = generator.generate_order()

    assert len(result.order) == 1
    assert result.order[0] == component
    assert len(result.stubs[component]) == 0
    assert result.level_assignments[component] == 0


def test_justification_content(mixed_dependency_graph):
    """Test that BLW algorithm provides meaningful justification."""
    generator = BLWOrderGenerator(mixed_dependency_graph)
    result = generator.generate_order()

    # Verify justification includes key information
    assert any("strongly connected components" in j.lower() for j in result.justification)
    assert any("specific stubs" in j.lower() for j in result.justification)

    # If cycles were found, verify cycle breaking is mentioned
    cycles = list(nx.simple_cycles(mixed_dependency_graph.graph))
    if cycles:
        assert any("breaking cycle" in j.lower() for j in result.justification)


def test_level_assignment_validity(mixed_dependency_graph):
    """Test that level assignments are valid for non-stubbed dependencies."""
    generator = BLWOrderGenerator(mixed_dependency_graph)
    result = generator.generate_order()

    # For each component, verify its level is higher than its non-stubbed dependencies
    for component in result.order:
        level = result.level_assignments[component]
        for dep in mixed_dependency_graph.get_dependencies(component):
            if dep.target not in result.stubs[component]:
                assert result.level_assignments[dep.target] < level
