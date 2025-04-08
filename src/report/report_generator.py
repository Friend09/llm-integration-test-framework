"""Report generator module.

This module generates detailed HTML reports from LLM analysis results,
including visualizations of dependencies and integration points.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from jinja2 import Environment, FileSystemLoader

from src.analyzer.dependency_analyzer import AnalysisResult
from src.llm.analyzer import LLMAnalysisReport

# Use non-interactive backend for matplotlib in non-GUI environments
matplotlib.use('Agg')


class ReportGenerator:
    """Generates detailed reports from LLM analysis results."""

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize report generator.

        Args:
            output_dir: Directory to save reports (defaults to ./reports)
        """
        self.output_dir = output_dir or Path("./reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)

        # Set up Jinja2 environment
        templates_dir = Path(__file__).parent.parent / "templates"
        templates_dir.mkdir(exist_ok=True)
        self.env = Environment(loader=FileSystemLoader(templates_dir))

    def generate_report(
        self,
        llm_report: LLMAnalysisReport,
        analysis_result: AnalysisResult,
        repository_name: str
    ) -> Path:
        """
        Generate a comprehensive HTML report.

        Args:
            llm_report: LLM analysis report
            analysis_result: Dependency analysis result
            repository_name: Name of the repository

        Returns:
            Path to the generated report
        """
        self.logger.info(f"Generating report for {repository_name}")

        # Create visualizations directory
        vis_dir = self.output_dir / "visualizations"
        vis_dir.mkdir(exist_ok=True)

        try:
            # Generate visualizations
            dependency_graph_path = self._generate_dependency_graph(
                analysis_result.dependency_graph,
                vis_dir,
                repository_name
            )

            integration_heatmap_path = self._generate_integration_heatmap(
                analysis_result.integration_points,
                vis_dir,
                repository_name
            )

            test_coverage_gap_path = self._generate_test_coverage_chart(
                analysis_result.test_coverage_gaps,
                vis_dir,
                repository_name
            )

            # Format the report data
            report_data = {
                "repository_name": repository_name,
                "report_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "llm_report": llm_report,
                "dependency_graph_path": str(dependency_graph_path.relative_to(self.output_dir)),
                "integration_heatmap_path": str(integration_heatmap_path.relative_to(self.output_dir)),
                "test_coverage_gap_path": str(test_coverage_gap_path.relative_to(self.output_dir)),
                "test_priorities": self._sort_recommendations_by_priority(llm_report.test_coverage_recommendations),
                "test_coverage_percentage": analysis_result.test_coverage_percentage,
                "component_count": analysis_result.component_count,
                "integration_point_count": analysis_result.integration_point_count,
                "high_risk_components": analysis_result.high_risk_components,
                "estimated_effort": self._format_estimation_summary(llm_report.estimated_effort)
            }

            # Check if HTML template exists, and create a default one if not
            template_path = Path(__file__).parent.parent / "templates" / "integration_test_report.html"
            if not template_path.exists():
                self._create_default_template(template_path)

            # Render the report template
            template = self.env.get_template("integration_test_report.html")
            report_html = template.render(**report_data)

            # Save the report
            report_path = self.output_dir / f"{repository_name}_integration_test_report.html"
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report_html)

            # Also save the raw JSON data for programmatic access
            json_path = self.output_dir / f"{repository_name}_integration_test_data.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "project_overview": llm_report.project_overview,
                        "architecture_summary": llm_report.architecture_summary,
                        "identified_integration_points": llm_report.identified_integration_points,
                        "test_coverage_recommendations": [
                            {
                                "component": r.component,
                                "integration_points": r.integration_points,
                                "recommended_test_types": r.recommended_test_types,
                                "priority": r.priority,
                                "complexity": r.complexity,
                                "rationale": r.rationale,
                                "suggested_test_approach": r.suggested_test_approach,
                                "test_data_requirements": r.test_data_requirements,
                                "potential_mocking_targets": r.potential_mocking_targets
                            }
                            for r in llm_report.test_coverage_recommendations
                        ],
                        "critical_paths_analysis": llm_report.critical_paths_analysis,
                        "suggested_testing_approach": llm_report.suggested_testing_approach,
                        "estimated_effort": llm_report.estimated_effort,
                        "test_strategy_recommendations": llm_report.test_strategy_recommendations,
                        "next_steps": llm_report.next_steps,
                        "metrics": {
                            "component_count": analysis_result.component_count,
                            "integration_point_count": analysis_result.integration_point_count,
                            "test_coverage_percentage": analysis_result.test_coverage_percentage
                        }
                    },
                    f,
                    indent=2
                )

            self.logger.info(f"Report generated at {report_path}")
            return report_path

        except Exception as e:
            self.logger.error(f"Error generating report: {str(e)}")
            raise

    def _generate_dependency_graph(
        self, graph: nx.DiGraph, vis_dir: Path, repository_name: str
    ) -> Path:
        """
        Generate a visualization of the dependency graph.

        Args:
            graph: NetworkX directed graph of dependencies
            vis_dir: Directory to save visualizations
            repository_name: Name of the repository

        Returns:
            Path to the saved visualization
        """
        self.logger.info("Generating dependency graph visualization")

        plt.figure(figsize=(14, 10))

        # For large graphs, use a different layout and smaller nodes
        if len(graph) > 100:
            pos = nx.spring_layout(graph, k=0.3, iterations=50, seed=42)
            node_size = 30
            with_labels = False
        else:
            pos = nx.spring_layout(graph, k=0.15, iterations=100, seed=42)
            node_size = 80
            with_labels = True

        # Calculate node colors based on in-degree (importance)
        # More connections = more important = darker color
        in_degree = dict(graph.in_degree())
        node_colors = [plt.cm.viridis(min(in_degree[n] / 10, 1.0)) for n in graph.nodes()]

        # Draw nodes and edges
        nx.draw_networkx_nodes(graph, pos, node_size=node_size, node_color=node_colors, alpha=0.7)
        nx.draw_networkx_edges(graph, pos, alpha=0.3, arrows=True, arrowsize=10)

        if with_labels:
            # Determine node labels (use shortened paths for readability)
            labels = {}
            for node in graph.nodes():
                # Shorten path by showing only filename and parent directory
                parts = node.split('/')
                if len(parts) > 1:
                    labels[node] = f"{parts[-2]}/{parts[-1]}" if len(parts) > 1 else parts[-1]
                else:
                    labels[node] = node

            # Draw labels with small font
            nx.draw_networkx_labels(graph, pos, labels=labels, font_size=8, font_family="sans-serif")

        plt.title(f"Dependency Graph for {repository_name}")
        plt.axis("off")
        plt.tight_layout()

        # Save the visualization
        output_path = vis_dir / f"{repository_name}_dependency_graph.png"
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()

        return output_path

    def _generate_integration_heatmap(
        self, integration_points: List, vis_dir: Path, repository_name: str
    ) -> Path:
        """
        Generate a heatmap of integration point importance.

        Args:
            integration_points: List of integration points
            vis_dir: Directory to save visualizations
            repository_name: Name of the repository

        Returns:
            Path to the saved visualization
        """
        self.logger.info("Generating integration heatmap")

        if not integration_points:
            # Generate empty placeholder if no integration points
            plt.figure(figsize=(10, 8))
            plt.text(0.5, 0.5, "No integration points detected",
                    ha='center', va='center', fontsize=14)
            plt.axis('off')
            output_path = vis_dir / f"{repository_name}_integration_heatmap.png"
            plt.savefig(output_path, dpi=300)
            plt.close()
            return output_path

        # Extract unique components from integration points
        components = set()
        for point in integration_points:
            components.add(point.source_component)
            components.add(point.target_component)

        # If there are too many components, limit to the most important ones
        if len(components) > 30:
            # Count occurrences of each component in integration points
            component_count = {}
            for point in integration_points:
                component_count[point.source_component] = component_count.get(point.source_component, 0) + 1
                component_count[point.target_component] = component_count.get(point.target_component, 0) + 1

            # Get the top 30 components
            components = sorted(
                component_count.keys(),
                key=lambda c: component_count[c],
                reverse=True
            )[:30]

        # Sort components for consistent display
        components = sorted(list(components))
        n = len(components)

        # Create component index mapping
        comp_to_idx = {comp: i for i, comp in enumerate(components)}

        # Initialize matrix
        matrix = np.zeros((n, n))

        # Fill matrix with importance values
        for point in integration_points:
            if point.source_component in comp_to_idx and point.target_component in comp_to_idx:
                i = comp_to_idx[point.source_component]
                j = comp_to_idx[point.target_component]
                matrix[i][j] = point.importance

        # Generate clean, shortened labels
        labels = []
        for comp in components:
            parts = comp.split('/')
            # Use only the last two parts of the path
            if len(parts) > 1:
                labels.append(f"{parts[-2]}/{parts[-1]}")
            else:
                labels.append(parts[-1])

        # Create heatmap
        plt.figure(figsize=(14, 12))
        plt.imshow(matrix, cmap="YlOrRd")

        # Add labels
        if n <= 30:  # Only show labels for smaller matrices
            plt.xticks(range(n), labels, rotation=90, fontsize=8)
            plt.yticks(range(n), labels, fontsize=8)
        else:
            plt.xticks([])
            plt.yticks([])

        plt.title(f"Integration Point Importance Heatmap for {repository_name}")
        plt.colorbar(label="Importance")
        plt.tight_layout()

        # Save the visualization
        output_path = vis_dir / f"{repository_name}_integration_heatmap.png"
        plt.savefig(output_path, dpi=300)
        plt.close()

        return output_path

    def _generate_test_coverage_chart(
        self, test_coverage_gaps: Dict[str, float], vis_dir: Path, repository_name: str
    ) -> Path:
        """
        Generate a chart showing test coverage gaps.

        Args:
            test_coverage_gaps: Dictionary of components with gap scores
            vis_dir: Directory to save visualizations
            repository_name: Name of the repository

        Returns:
            Path to the saved visualization
        """
        self.logger.info("Generating test coverage gap chart")

        if not test_coverage_gaps:
            # Generate empty placeholder if no coverage gaps
            plt.figure(figsize=(10, 8))
            plt.text(0.5, 0.5, "No test coverage gaps detected",
                    ha='center', va='center', fontsize=14)
            plt.axis('off')
            output_path = vis_dir / f"{repository_name}_test_coverage_gaps.png"
            plt.savefig(output_path, dpi=300)
            plt.close()
            return output_path

        # Sort gaps by score (descending)
        sorted_gaps = sorted(test_coverage_gaps.items(), key=lambda x: x[1], reverse=True)

        # Limit to top 15 for readability
        top_gaps = sorted_gaps[:15]

        # Extract components and scores
        components = []
        scores = []

        for component, score in top_gaps:
            # Shorten component name for readability
            parts = component.split('/')
            if len(parts) > 1:
                components.append(f"{parts[-2]}/{parts[-1]}")
            else:
                components.append(parts[-1])
            scores.append(score)

        # Create bar chart
        plt.figure(figsize=(14, 8))
        bars = plt.barh(components, scores, color=plt.cm.viridis(np.array(scores) / 10))

        plt.xlabel('Gap Score (higher = higher priority for testing)')
        plt.ylabel('Components')
        plt.title(f'Test Coverage Gaps for {repository_name}')

        # Add value labels to bars
        for i, v in enumerate(scores):
            plt.text(v + 0.1, i, f"{v:.1f}", va='center')

        # Add a legend explaining the score
        plt.figtext(0.5, 0.01,
                   "Gap Score: Higher scores indicate components that should be prioritized for testing.\n"
                   "Scores are based on centrality, integration point importance, and critical path analysis.",
                   ha="center", fontsize=10, bbox={"facecolor":"lightgray", "alpha":0.5, "pad":5})

        plt.tight_layout(rect=[0, 0.03, 1, 0.97])

        # Save the visualization
        output_path = vis_dir / f"{repository_name}_test_coverage_gaps.png"
        plt.savefig(output_path, dpi=300)
        plt.close()

        return output_path

    def _sort_recommendations_by_priority(self, recommendations):
        """Sort test recommendations by priority (descending)."""
        return sorted(recommendations, key=lambda r: r.priority, reverse=True)

    def _format_estimation_summary(self, effort: Dict[str, Any]) -> Dict[str, Any]:
        """Format the effort estimation for display in the report."""
        return {
            "total_components": effort.get("high_priority_components", 0),
            "person_days": effort.get("estimated_person_days", 0),
            "weeks_estimate": round(effort.get("estimated_person_days", 0) / 5, 1),
            "complexity_factors": effort.get("complexity_factors", [])
        }

    def _create_default_template(self, template_path: Path) -> None:
        """
        Create a default HTML template for the integration test report.

        Args:
            template_path: Path to save the template
        """
        self.logger.info(f"Creating default HTML template at {template_path}")

        # Create parent directory if it doesn't exist
        template_path.parent.mkdir(parents=True, exist_ok=True)

        html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Integration Test Coverage Report - {{ repository_name }}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f7f9fc;
        }
        h1, h2, h3, h4 {
            color: #2c3e50;
            margin-top: 30px;
        }
        h1 {
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        .report-header {
            background-color: #3498db;
            color: white;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .report-section {
            background-color: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stats-container {
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            margin-bottom: 20px;
        }
        .stat-box {
            background-color: white;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 15px;
            flex-basis: calc(25% - 20px);
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #3498db;
        }
        .stat-label {
            font-size: 14px;
            color: #7f8c8d;
        }
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }
        .visualization {
            width: 100%;
            max-width: 800px;
            margin: 20px auto;
            display: block;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        table, th, td {
            border: 1px solid #ddd;
        }
        th, td {
            text-align: left;
            padding: 12px;
        }
        th {
            background-color: #f2f2f2;
        }
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        .priority-high {
            background-color: #ff7675;
            color: white;
            padding: 5px 10px;
            border-radius: 3px;
        }
        .priority-medium {
            background-color: #fdcb6e;
            padding: 5px 10px;
            border-radius: 3px;
        }
        .priority-low {
            background-color: #55efc4;
            padding: 5px 10px;
            border-radius: 3px;
        }
        .tag {
            background-color: #e0e0e0;
            color: #333;
            padding: 3px 8px;
            border-radius: 3px;
            margin-right: 5px;
            font-size: 12px;
            display: inline-block;
            margin-bottom: 5px;
        }
        .next-steps {
            list-style-type: none;
            padding-left: 0;
        }
        .next-steps li {
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }
        .next-steps li:last-child {
            border-bottom: none;
        }
    </style>
</head>
<body>
    <div class="report-header">
        <h1>Integration Test Coverage Report</h1>
        <p>Repository: <strong>{{ repository_name }}</strong></p>
        <p>Generated on: {{ report_date }}</p>
    </div>

    <div class="stats-container">
        <div class="stat-box">
            <div class="stat-label">Components</div>
            <div class="stat-value">{{ component_count }}</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">Integration Points</div>
            <div class="stat-value">{{ integration_point_count }}</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">Test Coverage</div>
            <div class="stat-value">{{ test_coverage_percentage|round(1) }}%</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">Est. Effort</div>
            <div class="stat-value">{{ estimated_effort.person_days }} days</div>
        </div>
    </div>

    <div class="report-section">
        <h2>Project Overview</h2>
        <p>{{ llm_report.project_overview }}</p>
    </div>

    <div class="report-section">
        <h2>Architecture Summary</h2>
        <p>{{ llm_report.architecture_summary }}</p>
        <h3>Dependency Graph</h3>
        <img src="{{ dependency_graph_path }}" alt="Dependency Graph" class="visualization">
    </div>

    <div class="report-section">
        <h2>Integration Points Analysis</h2>
        <p>The following integration points were identified in the codebase:</p>
        <img src="{{ integration_heatmap_path }}" alt="Integration Points Heatmap" class="visualization">

        <h3>Top Integration Points</h3>
        <table>
            <thead>
                <tr>
                    <th>Source Component</th>
                    <th>Target Component</th>
                    <th>Type</th>
                    <th>Importance</th>
                    <th>Explanation</th>
                </tr>
            </thead>
            <tbody>
                {% for point in llm_report.identified_integration_points[:10] %}
                <tr>
                    <td>{{ point.source }}</td>
                    <td>{{ point.target }}</td>
                    <td>{{ point.type }}</td>
                    <td>{{ point.importance|round(2) }}</td>
                    <td>{{ point.explanation }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <div class="report-section">
        <h2>Test Coverage Gaps</h2>
        <p>The following components have the largest test coverage gaps and should be prioritized for testing:</p>
        <img src="{{ test_coverage_gap_path }}" alt="Test Coverage Gaps" class="visualization">
    </div>

    <div class="report-section">
        <h2>Test Coverage Recommendations</h2>
        <p>{{ llm_report.suggested_testing_approach }}</p>

        <h3>Critical Paths Analysis</h3>
        <p>{{ llm_report.critical_paths_analysis }}</p>

        <h3>High Priority Components</h3>
        <table>
            <thead>
                <tr>
                    <th>Component</th>
                    <th>Priority</th>
                    <th>Complexity</th>
                    <th>Test Types</th>
                    <th>Approach</th>
                </tr>
            </thead>
            <tbody>
                {% for rec in test_priorities %}
                <tr>
                    <td>{{ rec.component }}</td>
                    <td>
                        {% if rec.priority >= 4 %}
                        <span class="priority-high">High ({{ rec.priority }})</span>
                        {% elif rec.priority >= 2 %}
                        <span class="priority-medium">Medium ({{ rec.priority }})</span>
                        {% else %}
                        <span class="priority-low">Low ({{ rec.priority }})</span>
                        {% endif %}
                    </td>
                    <td>{{ rec.complexity }}</td>
                    <td>
                        {% for test_type in rec.recommended_test_types %}
                        <span class="tag">{{ test_type }}</span>
                        {% endfor %}
                    </td>
                    <td>{{ rec.suggested_test_approach }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <div class="report-section">
        <h2>Estimated Effort</h2>
        <p>Total estimated effort: <strong>{{ estimated_effort.person_days }} person-days</strong> (approximately {{ estimated_effort.weeks_estimate }} weeks).</p>

        <h3>Complexity Factors</h3>
        <ul>
            {% for factor in estimated_effort.complexity_factors %}
            <li>{{ factor }}</li>
            {% endfor %}
        </ul>
    </div>

    <div class="report-section">
        <h2>Next Steps</h2>
        <ol class="next-steps">
            {% for step in llm_report.next_steps %}
            <li>{{ step }}</li>
            {% endfor %}
        </ol>
    </div>

    <footer>
        <p style="text-align: center; margin-top: 40px; color: #7f8c8d; font-size: 12px;">
            Generated by LLM Integration Test Framework
        </p>
    </footer>
</body>
</html>
"""

        with open(template_path, "w") as f:
            f.write(html_template)
