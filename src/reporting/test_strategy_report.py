"""Test strategy report generator."""
import os
import json
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from ..models.dependency_graph import DependencyGraph
from ..models.integration_points.base import IntegrationPoint
from ..strategy.approach_recommender import TestingApproach
from ..strategy.test_order.base import TestOrderResult
from ..visualization.test_order_visualizer import TestOrderVisualizer


class TestStrategyReportGenerator:
    """Generates test strategy reports with LLM insights."""

    def __init__(
        self,
        dependency_graph: DependencyGraph,
        integration_points: List[IntegrationPoint],
        llm_analysis: Optional[Dict[str, Any]] = None
    ):
        """Initialize the report generator.

        Args:
            dependency_graph: The dependency graph to generate reports for
            integration_points: List of integration points
            llm_analysis: Optional LLM analysis results
        """
        self.dependency_graph = dependency_graph
        self.integration_points = integration_points
        self.llm_analysis = llm_analysis
        self.visualizer = TestOrderVisualizer()
        self._setup_jinja()

    def _setup_jinja(self) -> None:
        """Set up Jinja2 environment."""
        template_dir = Path(__file__).parent / "templates"
        self.env = Environment(loader=FileSystemLoader(str(template_dir)))

    def generate_report(
        self,
        recommended_approach: TestingApproach,
        test_order: TestOrderResult,
        output_dir: str,
        title: str = "Test Strategy Report"
    ) -> None:
        """Generate a comprehensive test strategy report."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate test order visualization
        self.visualizer.generate_test_order_report(
            test_order,
            str(output_dir / "test_order"),
            "Test Order Analysis"
        )

        # Generate main HTML report
        self._generate_main_report(
            recommended_approach,
            test_order,
            output_dir,
            title
        )

        # Save raw data as JSON for potential future use
        self._save_raw_data(
            recommended_approach,
            test_order,
            output_dir
        )

    def _generate_main_report(
        self,
        approach: TestingApproach,
        test_order: TestOrderResult,
        output_dir: Path,
        title: str
    ) -> None:
        """Generate the main HTML report."""
        # Prepare report data
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "title": title,
            "approach": {
                "name": approach.name,
                "score": approach.score,
                "advantages": approach.advantages,
                "disadvantages": approach.disadvantages,
                "prerequisites": approach.prerequisites,
                "risks": approach.risks,
                "estimated_effort": approach.estimated_effort
            },
            "test_order": {
                "metrics": test_order.metrics,
                "components": [comp.name for comp in test_order.order],
                "levels": {comp.name: level for comp, level in test_order.level_assignments.items()},
                "stubs": {
                    comp.name: [stub.name for stub in stubs]
                    for comp, stubs in test_order.stubs.items()
                }
            },
            "system_stats": {
                "total_components": len(self.dependency_graph.get_components()),
                "total_integration_points": len(self.integration_points),
                "total_relationships": len(self.dependency_graph.get_relationships()),
                "total_cycles": len(self.dependency_graph.find_cycles())
            }
        }

        # Add LLM analysis if available
        if self.llm_analysis:
            report_data.update({
                "llm_analysis": {
                    "overall_approach": self.llm_analysis.get("overall_approach", {}),
                    "component_prioritization": self.llm_analysis.get("component_prioritization", {}),
                    "test_sequence": self.llm_analysis.get("test_sequence", {}),
                    "resource_allocation": self.llm_analysis.get("resource_allocation", {}),
                    "risk_mitigation": self.llm_analysis.get("risk_mitigation", {})
                }
            })

        # Generate HTML report
        template = self.env.get_template("report.html")
        html_content = template.render(**report_data)

        report_path = output_dir / "index.html"
        report_path.write_text(html_content)

    def _generate_integration_point_stats(self) -> str:
        """Generate statistics about integration points."""
        stats: Dict[str, Dict[str, float]] = {}

        for point in self.integration_points:
            if point.integration_type not in stats:
                stats[point.integration_type] = {
                    "count": 0,
                    "complexity": 0.0,
                    "risk": 0.0
                }

            stats[point.integration_type]["count"] += 1
            stats[point.integration_type]["complexity"] += point.complexity_score
            stats[point.integration_type]["risk"] += point.risk_score

        rows = []
        for type_name, type_stats in stats.items():
            count = type_stats["count"]
            avg_complexity = type_stats["complexity"] / count
            avg_risk = type_stats["risk"] / count

            rows.append(f"""
                <tr>
                    <td>{type_name}</td>
                    <td>{count}</td>
                    <td>{avg_complexity:.2f}</td>
                    <td>{avg_risk:.2f}</td>
                </tr>
            """)

        return "".join(rows)

    def _save_raw_data(
        self,
        approach: TestingApproach,
        test_order: TestOrderResult,
        output_dir: Path
    ) -> None:
        """Save raw data as JSON for future reference."""
        data = {
            "timestamp": datetime.now().isoformat(),
            "approach": {
                "name": approach.name,
                "score": approach.score,
                "advantages": approach.advantages,
                "disadvantages": approach.disadvantages,
                "prerequisites": approach.prerequisites,
                "risks": approach.risks,
                "estimated_effort": approach.estimated_effort
            },
            "test_order": {
                "metrics": test_order.metrics,
                "components": [comp.name for comp in test_order.order],
                "levels": {comp.name: level for comp, level in test_order.level_assignments.items()},
                "stubs": {
                    comp.name: [stub.name for stub in stubs]
                    for comp, stubs in test_order.stubs.items()
                }
            },
            "system_stats": {
                "total_components": len(self.dependency_graph.get_components()),
                "total_integration_points": len(self.integration_points),
                "total_relationships": len(self.dependency_graph.get_relationships()),
                "total_cycles": len(self.dependency_graph.find_cycles())
            }
        }

        json_path = output_dir / "raw_data.json"
        json_path.write_text(json.dumps(data, indent=2))
