"""Unit tests for the TJJM test order generation algorithm."""

import pytest
import networkx as nx
from uuid import uuid4

from src.models.component import Component
from src.models.relationship import Relationship
from src.models.dependency_graph import DependencyGraph
from src.strategy.test_order.tjjm import TJJMOrderGenerator


@pytest.fixture
def simple_components():
    """Create a set of simple components for testing."""
    return [
        Component(name=f"Component{i}", component_type="class", location=f"file{i}.py")
        for i in range(4)
    ]


@pytest.fixture
def cyclic_components():
    """Create a set of components with cyclic dependencies."""
    components = []
    for i in range(5):
        comp = Component(
            name=f"Component{i}",
            component_type="class",
            location=f"file{i}.py",
            complexity_score=0.5 * i
        )
        components.append(comp)
    return components


@pytest.fixture
def cyclic_dependency_graph(cyclic_components):
    """Create a dependency graph with multiple cycles."""
    graph = DependencyGraph()

    # Add components
    for component in cyclic_components:
        graph.add_component(component)

    # Create relationships with cycles
    relationships = [
        # Cycle 1: 0 -> 1 -> 2 -> 0
        Relationship(cyclic_components[0], cyclic_components[1], "association"),
        Relationship(cyclic_components[1], cyclic_components[2], "association"),
        Relationship(cyclic_components[2], cyclic_components[0], "association"),
        # Cycle 2: 2 -> 3 -> 4 -> 2
        Relationship(cyclic_components[2], cyclic_components[3], "association"),
        Relationship(cyclic_components[3], cyclic_components[4], "association"),
        Relationship(cyclic_components[4], cyclic_components[2], "association"),
    ]

    for rel in relationships:
        graph.add_relationship(rel)

    return graph


@pytest.fixture
def complex_dependency_graph():
    """Create a more complex dependency graph with multiple cycles."""
    graph = DependencyGraph()

    # Create components
    components = [
        Component(name=f"Component{i}", component_type="class", location=f"file{i}.py")
        for i in range(6)
    ]

    for component in components:
        graph.add_component(component)

    # Create two interconnected cycles:
    # Cycle 1: C0 -> C1 -> C2 -> C0
    # Cycle 2: C2 -> C3 -> C4 -> C2
    # C5 depends on C1 and C3
    relationships = [
        # Cycle 1
        Relationship(components[0], components[1], "association"),
        Relationship(components[1], components[2], "association"),
        Relationship(components[2], components[0], "association"),
        # Cycle 2
        Relationship(components[2], components[3], "association"),
        Relationship(components[3], components[4], "association"),
        Relationship(components[4], components[2], "association"),
        # Additional dependencies
        Relationship(components[1], components[5], "association"),
        Relationship(components[3], components[5], "association")
    ]

    for rel in relationships:
        graph.add_relationship(rel)

    return graph


def test_acyclic_graph():
    """Test TJJM algorithm with an acyclic graph."""
    graph = DependencyGraph()

    # Create a simple chain: A -> B -> C
    components = [
        Component(name=f"Component{i}", component_type="class", location=f"file{i}.py")
        for i in range(3)
    ]

    for component in components:
        graph.add_component(component)

    relationships = [
        Relationship(components[0], components[1], "association"),
        Relationship(components[1], components[2], "association")
    ]

    for rel in relationships:
        graph.add_relationship(rel)

    generator = TJJMOrderGenerator(graph)
    result = generator.generate_order()

    # Verify the order is correct
    assert len(result.order) == 3
    assert result.order == [components[2], components[1], components[0]]

    # Verify no stubs are required
    assert all(len(stubs) == 0 for stubs in result.stubs.values())


def test_cycle_detection(cyclic_dependency_graph):
    """Test that TJJM algorithm correctly detects cycles."""
    generator = TJJMOrderGenerator(cyclic_dependency_graph)
    sccs = generator.dependency_graph.get_strongly_connected_components()

    # Should find one strongly connected component containing all cyclically connected nodes
    cycles = [scc for scc in sccs if len(scc) > 1]
    assert len(cycles) == 1

    # The cycle should contain 5 components (Component0 through Component4)
    assert len(cycles[0]) == 5

    # Verify that all components in the cycles are present
    component_names = {comp.name for comp in cycles[0]}
    expected_names = {f"Component{i}" for i in range(5)}
    assert component_names == expected_names


def test_cycle_breaking(cyclic_dependency_graph):
    """Test that TJJM algorithm effectively breaks cycles."""
    generator = TJJMOrderGenerator(cyclic_dependency_graph)
    result = generator.generate_order()

    # Create a graph from the resulting order
    test_graph = nx.DiGraph()
    for component in result.order:
        test_graph.add_node(component.id)

    # Add edges that don't require stubs
    for component in result.order:
        deps = cyclic_dependency_graph.get_dependencies(component)
        for dep in deps:
            if dep.target not in result.stubs[component]:
                test_graph.add_edge(component.id, dep.target.id)

    # Verify the resulting graph is acyclic
    assert nx.is_directed_acyclic_graph(test_graph)


def test_stub_minimization(cyclic_dependency_graph):
    """Test that TJJM algorithm minimizes the number of stubs."""
    generator = TJJMOrderGenerator(cyclic_dependency_graph)
    result = generator.generate_order()

    # Count total stubs
    total_stubs = sum(len(stubs) for stubs in result.stubs.values())

    # Create a reversed order (which should require more stubs)
    reversed_order = list(reversed(result.order))
    reversed_stubs = generator.calculate_required_stubs(reversed_order)
    total_reversed_stubs = sum(len(stubs) for stubs in reversed_stubs.values())

    # TJJM should produce fewer stubs
    assert total_stubs <= total_reversed_stubs


def test_overlapping_cycles(cyclic_dependency_graph):
    """Test that TJJM algorithm handles overlapping cycles correctly."""
    generator = TJJMOrderGenerator(cyclic_dependency_graph)
    result = generator.generate_order()

    # Component2 is part of both cycles, should be handled efficiently
    component2 = next(c for c in result.order if c.name == "Component2")

    # Count how many stubs are required for Component2
    stubs_for_component2 = len(result.stubs[component2])

    # Should require minimal stubs despite being in two cycles
    assert stubs_for_component2 <= 2


def test_acyclic_subgraph():
    """Test TJJM algorithm with a mixed graph containing both cyclic and acyclic parts."""
    graph = DependencyGraph()

    # Create components
    components = [
        Component(name=f"Component{i}", component_type="class", location=f"file{i}.py")
        for i in range(4)
    ]

    for component in components:
        graph.add_component(component)

    # Create a cycle (0 -> 1 -> 0) and an acyclic part (2 -> 3)
    relationships = [
        Relationship(components[0], components[1], "association"),
        Relationship(components[1], components[0], "association"),
        Relationship(components[2], components[3], "association"),
    ]

    for rel in relationships:
        graph.add_relationship(rel)

    generator = TJJMOrderGenerator(graph)
    result = generator.generate_order()

    # Components 2 and 3 should not require stubs
    assert len(result.stubs[components[2]]) == 0
    assert len(result.stubs[components[3]]) == 0


def test_empty_graph():
    """Test TJJM algorithm with an empty graph."""
    graph = DependencyGraph()
    generator = TJJMOrderGenerator(graph)
    result = generator.generate_order()

    assert len(result.order) == 0
    assert len(result.stubs) == 0
    assert len(result.level_assignments) == 0


def test_single_component():
    """Test TJJM algorithm with a single component."""
    graph = DependencyGraph()
    component = Component(
        name="SingleComponent",
        component_type="class",
        location="file.py"
    )
    graph.add_component(component)

    generator = TJJMOrderGenerator(graph)
    result = generator.generate_order()

    assert len(result.order) == 1
    assert result.order[0] == component
    assert len(result.stubs[component]) == 0
    assert result.level_assignments[component] == 0


def test_justification_content(cyclic_dependency_graph):
    """Test that TJJM algorithm provides meaningful justification."""
    generator = TJJMOrderGenerator(cyclic_dependency_graph)
    result = generator.generate_order()

    # Verify justification includes key information
    assert any("strongly connected components" in j.lower() for j in result.justification)
    assert any("cycle" in j.lower() for j in result.justification)

    # Should mention the number of stubs
    assert any("stub" in j.lower() for j in result.justification)


def test_level_assignment_validity(cyclic_dependency_graph):
    """Test that level assignments are valid for non-stubbed dependencies."""
    generator = TJJMOrderGenerator(cyclic_dependency_graph)
    result = generator.generate_order()

    # For each component, verify its level is higher than its non-stubbed dependencies
    for component in result.order:
        level = result.level_assignments[component]
        for dep in cyclic_dependency_graph.get_dependencies(component):
            if dep.target not in result.stubs[component]:
                assert result.level_assignments[dep.target] < level


def test_cycle_breaking_efficiency():
    """Test that TJJM algorithm breaks cycles efficiently."""
    graph = DependencyGraph()

    # Create a complex cyclic structure with multiple possible break points
    components = [
        Component(name=f"Component{i}", component_type="class", location=f"file{i}.py",
                 complexity_score=0.5 * i) for i in range(6)
    ]

    for component in components:
        graph.add_component(component)

    # Create multiple cycles with shared edges
    relationships = [
        # Cycle 1: 0 -> 1 -> 2 -> 0
        Relationship(components[0], components[1], "association"),
        Relationship(components[1], components[2], "association"),
        Relationship(components[2], components[0], "association"),
        # Cycle 2: 2 -> 3 -> 4 -> 2
        Relationship(components[2], components[3], "association"),
        Relationship(components[3], components[4], "association"),
        Relationship(components[4], components[2], "association"),
        # Additional edge to test break point selection
        Relationship(components[4], components[5], "association")
    ]

    for rel in relationships:
        graph.add_relationship(rel)

    generator = TJJMOrderGenerator(graph)
    result = generator.generate_order()

    # Count the number of edges broken (stubs created)
    total_stubs = sum(len(stubs) for stubs in result.stubs.values())

    # Should break minimum number of edges (2 for this case)
    assert total_stubs <= 2, f"Expected at most 2 stubs, but got {total_stubs}"


def test_stub_complexity_consideration():
    """Test that TJJM algorithm considers component complexity when breaking cycles."""
    graph = DependencyGraph()

    # Create components with varying complexity scores
    components = [
        Component(name="HighComplexity", component_type="class", location="high.py",
                 complexity_score=0.9),
        Component(name="MediumComplexity", component_type="class", location="med.py",
                 complexity_score=0.5),
        Component(name="LowComplexity", component_type="class", location="low.py",
                 complexity_score=0.1)
    ]

    for component in components:
        graph.add_component(component)

    # Create a cycle where breaking different edges would require different complexity stubs
    relationships = [
        Relationship(components[0], components[1], "association"),
        Relationship(components[1], components[2], "association"),
        Relationship(components[2], components[0], "association")
    ]

    for rel in relationships:
        graph.add_relationship(rel)

    generator = TJJMOrderGenerator(graph)
    result = generator.generate_order()

    # The algorithm should prefer breaking edges that require simpler stubs
    for component, stubs in result.stubs.items():
        for stub in stubs:
            # Verify that high complexity components are not chosen for stubbing when possible
            assert stub.complexity_score < 0.9, "High complexity component should not be stubbed"


def test_multiple_cycles_shared_components():
    """Test TJJM algorithm with multiple cycles sharing components."""
    graph = DependencyGraph()

    # Create components for multiple interconnected cycles
    components = [
        Component(name=f"Component{i}", component_type="class", location=f"file{i}.py")
        for i in range(5)
    ]

    for component in components:
        graph.add_component(component)

    # Create two cycles sharing Component2
    relationships = [
        # Cycle 1: 0 -> 1 -> 2 -> 0
        Relationship(components[0], components[1], "association"),
        Relationship(components[1], components[2], "association"),
        Relationship(components[2], components[0], "association"),
        # Cycle 2: 2 -> 3 -> 4 -> 2
        Relationship(components[2], components[3], "association"),
        Relationship(components[3], components[4], "association"),
        Relationship(components[4], components[2], "association")
    ]

    for rel in relationships:
        graph.add_relationship(rel)

    generator = TJJMOrderGenerator(graph)
    result = generator.generate_order()

    # Verify that the shared component (Component2) is handled efficiently
    component2 = next(c for c in components if c.name == "Component2")
    component2_stubs = len(result.stubs[component2])

    # The shared component should not require more stubs than necessary
    assert component2_stubs <= 2, f"Component2 requires {component2_stubs} stubs, expected at most 2"


def test_graph_structure_preservation():
    """Test that TJJM algorithm preserves essential graph structure."""
    graph = DependencyGraph()

    # Create a graph with both cyclic and important acyclic relationships
    components = [
        Component(name=f"Component{i}", component_type="class", location=f"file{i}.py")
        for i in range(4)
    ]

    for component in components:
        graph.add_component(component)

    # Create a cycle (0 -> 1 -> 0) and important acyclic edges (2 -> 3, 1 -> 3)
    relationships = [
        Relationship(components[0], components[1], "association"),
        Relationship(components[1], components[0], "association"),
        Relationship(components[2], components[3], "association"),  # Important acyclic edge
        Relationship(components[1], components[3], "association")   # Important acyclic edge
    ]

    for rel in relationships:
        graph.add_relationship(rel)

    generator = TJJMOrderGenerator(graph)
    result = generator.generate_order()

    # Verify that acyclic relationships are preserved
    comp2_idx = result.order.index(components[2])
    comp3_idx = result.order.index(components[3])
    assert comp3_idx < comp2_idx, "Acyclic relationship 2->3 should be preserved in order"

    # Verify that components 2 and 3 don't require stubs
    assert len(result.stubs[components[2]]) == 0, "Component2 should not require stubs"
    assert len(result.stubs[components[3]]) == 0, "Component3 should not require stubs"
