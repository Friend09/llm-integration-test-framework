"""Test order visualization module."""

from typing import Dict, List, Set, Optional
import graphviz
from pathlib import Path

from ..models.component import Component
from ..strategy.test_order.base import TestOrderResult


class TestOrderVisualizer:
    """Generates visual representations of test orders."""

    def __init__(self):
        """Initialize the test order visualizer."""
        self.node_colors = {
            0: "#e6f3ff",  # Light blue for level 0
            1: "#e6ffe6",  # Light green for level 1
            2: "#fff5e6",  # Light orange for level 2
            3: "#ffe6e6",  # Light red for level 3
            4: "#f0e6ff",  # Light purple for level 4
            5: "#fff0f0"   # Light pink for level 5+
        }
        self.edge_colors = {
            "inheritance": "#0000FF",  # Blue
            "aggregation": "#00AA00",  # Green
            "association": "#AA0000"   # Red
        }

    def generate_test_order_graph(
        self,
        result: TestOrderResult,
        output_path: str,
        title: str = "Test Order Visualization"
    ) -> None:
        """Generate a visual representation of the test order."""
        dot = graphviz.Digraph(comment=title)
        dot.attr(rankdir="TB")

        # Set graph title
        dot.attr(label=title)
        dot.attr(labelloc="t")

        # Create subgraphs for each level
        self._create_level_subgraphs(dot, result)

        # Add edges for dependencies and stubs
        self._add_dependency_edges(dot, result)

        # Save the graph
        dot.render(output_path, format="png", cleanup=True)

    def _create_level_subgraphs(self, dot: graphviz.Digraph, result: TestOrderResult) -> None:
        """Create subgraphs for each level in the test order."""
        # Group components by level
        level_components: Dict[int, List[Component]] = {}
        for component, level in result.level_assignments.items():
            if level not in level_components:
                level_components[level] = []
            level_components[level].append(component)

        # Create subgraph for each level
        for level in sorted(level_components.keys()):
            with dot.subgraph(name=f"cluster_level_{level}") as subg:
                subg.attr(label=f"Level {level}")
                subg.attr(style="filled")
                subg.attr(color=self.node_colors.get(level, self.node_colors[5]))

                # Add nodes for components in this level
                for component in level_components[level]:
                    self._add_component_node(subg, component, result)

    def _add_component_node(
        self,
        graph: graphviz.Digraph,
        component: Component,
        result: TestOrderResult
    ) -> None:
        """Add a node for a component with appropriate styling."""
        # Calculate test order index
        test_order_index = result.order.index(component) + 1

        # Create node label with component details
        label = f"{component.name}\\n({test_order_index})"

        # Add complexity and importance scores if available
        if hasattr(component, "complexity_score"):
            label += f"\\nC: {component.complexity_score:.2f}"
        if hasattr(component, "importance_score"):
            label += f"\\nI: {component.importance_score:.2f}"

        # Add node with styling
        graph.node(
            component.name,
            label=label,
            shape="box",
            style="filled",
            fillcolor="white"
        )

    def _add_dependency_edges(self, dot: graphviz.Digraph, result: TestOrderResult) -> None:
        """Add edges for dependencies and stubs."""
        # Track added edges to avoid duplicates
        added_edges = set()

        # Add edges for stubs
        for component, stub_set in result.stubs.items():
            for stub in stub_set:
                edge_key = (component.name, stub.name)
                if edge_key not in added_edges:
                    dot.edge(
                        component.name,
                        stub.name,
                        style="dashed",
                        color="red",
                        label="stub"
                    )
                    added_edges.add(edge_key)

        # Add regular dependency edges
        for i, component in enumerate(result.order):
            # Get dependencies that are not stubs
            deps = set()
            for j in range(i):
                prev_component = result.order[j]
                if prev_component in result.stubs.get(component, set()):
                    continue
                deps.add(prev_component)

            # Add edges for actual dependencies
            for dep in deps:
                edge_key = (component.name, dep.name)
                if edge_key not in added_edges:
                    dot.edge(
                        component.name,
                        dep.name,
                        style="solid",
                        color="black"
                    )
                    added_edges.add(edge_key)

    def generate_test_order_table(
        self,
        result: TestOrderResult,
        output_path: str,
        title: str = "Test Order Summary"
    ) -> None:
        """Generate an HTML table representation of the test order."""
        html_content = f"""
        <html>
        <head>
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #f5f5f5; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                tr:hover {{ background-color: #f0f0f0; }}
                .metrics {{ margin: 20px 0; padding: 15px; background-color: #f8f9fa; border-radius: 5px; }}
                .justification {{ margin: 20px 0; }}
                .justification li {{ margin: 5px 0; }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>

            <div class="metrics">
                <h2>Test Order Metrics</h2>
                <ul>
                    <li>Total Components: {len(result.order)}</li>
                    <li>Total Stubs Required: {result.metrics['total_stub_count']}</li>
                    <li>Components with Stubs: {result.metrics['components_with_stubs']}</li>
                    <li>Average Stubs per Component: {result.metrics['average_stubs_per_component']:.2f}</li>
                </ul>
            </div>

            <div class="justification">
                <h2>Justification</h2>
                <ul>
                    {"".join(f"<li>{reason}</li>" for reason in result.justification)}
                </ul>
            </div>

            <h2>Test Order Details</h2>
            <table>
                <tr>
                    <th>Order</th>
                    <th>Component</th>
                    <th>Level</th>
                    <th>Dependencies</th>
                    <th>Required Stubs</th>
                </tr>
        """

        # Add rows for each component
        for i, component in enumerate(result.order):
            deps = ", ".join(d.name for d in result.stubs[component]) if result.stubs[component] else "None"
            stubs = ", ".join(s.name for s in result.stubs[component]) if result.stubs[component] else "None"

            html_content += f"""
                <tr>
                    <td>{i + 1}</td>
                    <td>{component.name}</td>
                    <td>{result.level_assignments[component]}</td>
                    <td>{deps}</td>
                    <td>{stubs}</td>
                </tr>
            """

        html_content += """
            </table>
        </body>
        </html>
        """

        # Write the HTML file
        output_path = Path(output_path)
        output_path.write_text(html_content)

    def generate_test_order_report(
        self,
        result: TestOrderResult,
        output_dir: str,
        title: str = "Test Order Report"
    ) -> None:
        """Generate a complete test order report with graph and table."""
        # Create output directory if it doesn't exist
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate graph visualization
        graph_path = output_dir / "test_order_graph"
        self.generate_test_order_graph(result, str(graph_path), title)

        # Generate HTML table
        table_path = output_dir / "test_order_table.html"
        self.generate_test_order_table(result, str(table_path), title)
