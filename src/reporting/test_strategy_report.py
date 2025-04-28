"""Test strategy report generation module."""

from pathlib import Path
from typing import Dict, List, Optional
import json
from datetime import datetime

from ..models.dependency_graph import DependencyGraph
from ..models.integration_points.base import IntegrationPoint
from ..strategy.approach_recommender import TestingApproach
from ..strategy.test_order.base import TestOrderResult
from ..visualization.test_order_visualizer import TestOrderVisualizer


class TestStrategyReportGenerator:
    """Generates comprehensive test strategy reports."""

    def __init__(
        self,
        dependency_graph: DependencyGraph,
        integration_points: List[IntegrationPoint]
    ):
        """Initialize the report generator."""
        self.dependency_graph = dependency_graph
        self.integration_points = integration_points
        self.visualizer = TestOrderVisualizer()

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
        html_content = f"""
        <html>
        <head>
            <title>{title}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 20px;
                    color: #333;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                }}
                h1, h2, h3 {{
                    color: #2c3e50;
                    margin-top: 30px;
                }}
                .section {{
                    background: #fff;
                    padding: 20px;
                    margin: 20px 0;
                    border-radius: 5px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }}
                .metrics {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin: 20px 0;
                }}
                .metric-card {{
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 5px;
                    text-align: center;
                }}
                .metric-value {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #2c3e50;
                }}
                .metric-label {{
                    color: #666;
                    font-size: 14px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                th, td {{
                    padding: 12px;
                    border: 1px solid #ddd;
                    text-align: left;
                }}
                th {{
                    background: #f5f5f5;
                }}
                .score {{
                    font-size: 18px;
                    font-weight: bold;
                    color: #2c3e50;
                }}
                .list-section {{
                    margin: 15px 0;
                }}
                .list-section h3 {{
                    color: #2c3e50;
                    margin-bottom: 10px;
                }}
                .list-section ul {{
                    list-style-type: none;
                    padding-left: 0;
                }}
                .list-section li {{
                    padding: 8px 0;
                    border-bottom: 1px solid #eee;
                }}
                .visualization {{
                    text-align: center;
                    margin: 30px 0;
                }}
                .visualization img {{
                    max-width: 100%;
                    height: auto;
                }}
                .footer {{
                    margin-top: 50px;
                    padding-top: 20px;
                    border-top: 1px solid #eee;
                    text-align: center;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>{title}</h1>
                <div class="section">
                    <h2>Executive Summary</h2>
                    <p>
                        Based on the analysis of {len(self.dependency_graph.get_components())} components and
                        {len(self.integration_points)} integration points, the recommended testing approach is
                        <strong>{approach.name}</strong> with a suitability score of {approach.score:.2f}.
                    </p>
                </div>

                <div class="section">
                    <h2>System Overview</h2>
                    <div class="metrics">
                        <div class="metric-card">
                            <div class="metric-value">{len(self.dependency_graph.get_components())}</div>
                            <div class="metric-label">Total Components</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{len(self.integration_points)}</div>
                            <div class="metric-label">Integration Points</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{test_order.metrics['total_stub_count']}</div>
                            <div class="metric-label">Required Stubs</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">{len(self.dependency_graph.find_cycles())}</div>
                            <div class="metric-label">Cyclic Dependencies</div>
                        </div>
                    </div>
                </div>

                <div class="section">
                    <h2>Recommended Testing Approach</h2>
                    <div class="score">Suitability Score: {approach.score:.2f}</div>

                    <div class="list-section">
                        <h3>Advantages</h3>
                        <ul>
                            {"".join(f"<li>{adv}</li>" for adv in approach.advantages)}
                        </ul>
                    </div>

                    <div class="list-section">
                        <h3>Disadvantages</h3>
                        <ul>
                            {"".join(f"<li>{dis}</li>" for dis in approach.disadvantages)}
                        </ul>
                    </div>

                    <div class="list-section">
                        <h3>Prerequisites</h3>
                        <ul>
                            {"".join(f"<li>{pre}</li>" for pre in approach.prerequisites)}
                        </ul>
                    </div>

                    <div class="list-section">
                        <h3>Risks</h3>
                        <ul>
                            {"".join(f"<li>{risk}</li>" for risk in approach.risks)}
                        </ul>
                    </div>

                    <h3>Estimated Effort Distribution</h3>
                    <table>
                        <tr>
                            <th>Activity</th>
                            <th>Effort (%)</th>
                        </tr>
                        {"".join(
                            f"<tr><td>{activity}</td><td>{effort*100:.1f}%</td></tr>"
                            for activity, effort in approach.estimated_effort.items()
                        )}
                    </table>
                </div>

                <div class="section">
                    <h2>Test Order Analysis</h2>
                    <div class="visualization">
                        <img src="test_order/test_order_graph.png" alt="Test Order Graph">
                    </div>
                    <p>For detailed test order information, please see the <a href="test_order/test_order_table.html">Test Order Details</a>.</p>
                </div>

                <div class="section">
                    <h2>Integration Points Analysis</h2>
                    <table>
                        <tr>
                            <th>Type</th>
                            <th>Count</th>
                            <th>Average Complexity</th>
                            <th>Average Risk</th>
                        </tr>
                        {self._generate_integration_point_stats()}
                    </table>
                </div>

                <div class="footer">
                    <p>Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                </div>
            </div>
        </body>
        </html>
        """

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
