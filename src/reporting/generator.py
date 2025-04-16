"""Report generator for the LLM Integration Testing Framework."""
import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader
from src.reporting.models.base import Report
from src.reporting.models.sections import (
    ProjectOverviewSection,
    DependencyAnalysisSection,
    IntegrationPointsSection,
    TestStrategySection
)

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Generates reports from analysis results and test strategies."""

    def __init__(self):
        """Initialize the report generator."""
        template_path = Path(__file__).parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(str(template_path)),
            autoescape=True
        )

    async def generate(self,
                      analysis_results: Dict[str, Any],
                      test_strategy: Dict[str, Any],
                      repo_url: str) -> Path:
        """Generate a report from the analysis results and test strategy.

        Args:
            analysis_results: Dictionary containing analysis results
            test_strategy: Dictionary containing test strategy
            repo_url: URL of the analyzed repository

        Returns:
            Path to the generated report file
        """
        try:
            # Create report sections
            sections = [
                ProjectOverviewSection(
                    repository_url=repo_url,
                    project_name=Path(repo_url).stem,
                    description="LLM Smoke Test Framework",
                    framework_type="Python",
                    language="Python"
                ),
                DependencyAnalysisSection(
                    components=analysis_results["components"],
                    dependencies=analysis_results["dependencies"],
                    metrics=analysis_results["metrics"]
                ),
                IntegrationPointsSection(
                    integration_points=analysis_results["integration_points"],
                    risk_assessment=test_strategy.get("risk_assessment", {}),
                    recommendations=test_strategy.get("recommendations", [])
                ),
                TestStrategySection(
                    approach=test_strategy["approach"],
                    test_order=test_strategy["test_order"],
                    stub_requirements=test_strategy["stub_requirements"],
                    resource_estimates=test_strategy.get("resource_estimates", {})
                )
            ]

            # Create report
            report = Report(
                title="LLM Integration Testing Framework Analysis Report",
                sections=sections,
                metadata={
                    "repository_url": repo_url,
                    "generated_at": datetime.now().isoformat()
                }
            )

            # Generate HTML report
            output_dir = Path(os.getenv("OUTPUT_DIR", "output"))
            output_dir.mkdir(exist_ok=True)

            report_path = output_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

            template = self.env.get_template("base.html")
            html_content = template.render(
                title=report.title,
                timestamp=report.timestamp,
                sections=report.sections
            )

            report_path.write_text(html_content)

            logger.info(f"Report generated at: {report_path}")
            return report_path

        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            raise
