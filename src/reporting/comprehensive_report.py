from typing import Dict, Any, Optional, List
from pathlib import Path
import logging
from jinja2 import Environment, FileSystemLoader
import json
from datetime import datetime

from .models.base import ReportSection
from .models.sections import (
    ProjectOverviewSection,
    DependencyAnalysisSection,
    TestStrategySection,
    TestOrderSection,
    RiskAssessmentSection,
    ComplexityAssessmentSection,
    RecommendationsSection
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ComprehensiveReport:
    """Class to generate comprehensive test analysis reports."""

    def __init__(self, output_dir: str = "output/reports"):
        """
        Initialize the comprehensive report generator.

        Args:
            output_dir: Directory to store generated reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Jinja2 environment
        template_dir = Path(__file__).parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True
        )

    def generate(self, analysis_results: Dict[str, Any]) -> Path:
        """
        Generate a comprehensive report from analysis results.

        Args:
            analysis_results: Dictionary containing all analysis results

        Returns:
            Path to the generated report file
        """
        try:
            logger.debug(f"Generating report from analysis results: {json.dumps(analysis_results, indent=2)}")

            # Create report sections based on what's available in the results
            sections = []

            # Add project overview if available
            if "project_overview" in analysis_results:
                sections.append(ProjectOverviewSection(analysis_results["project_overview"]))

            # Add dependency analysis if available
            if "dependency_analysis" in analysis_results:
                sections.append(DependencyAnalysisSection(analysis_results["dependency_analysis"]))

            # Add test strategy if available
            if "test_strategy" in analysis_results:
                sections.append(TestStrategySection(analysis_results["test_strategy"]))

            # Add test order if available
            if "test_order" in analysis_results:
                sections.append(TestOrderSection(analysis_results["test_order"]))

            # Add test requirements if available (direct key from our mock data)
            if "test_requirements" in analysis_results:
                # Create test strategy from test requirements since format is similar
                test_requirements = analysis_results["test_requirements"]
                strategy_data = {
                    "approach": "Generated from test requirements",
                    "components": test_requirements.get("components", []),
                    "integration_points": test_requirements.get("integration_points", [])
                }
                sections.append(TestStrategySection(strategy_data))

            # Add risk assessment if available
            if "risk_assessment" in analysis_results:
                sections.append(RiskAssessmentSection(analysis_results["risk_assessment"]))

            # Add complexity assessment if available
            if "complexity_assessment" in analysis_results:
                sections.append(ComplexityAssessmentSection(analysis_results["complexity_assessment"]))

            # Add recommendations if available
            if "recommendations" in analysis_results:
                sections.append(RecommendationsSection(analysis_results["recommendations"]))

            # Add some dummy data if no sections are created
            if not sections:
                logger.warning("No valid sections found in analysis results, adding dummy data")
                sections.append(ProjectOverviewSection({"name": "Demo Project", "description": "Generated from mock data"}))

            # Generate report content
            report_content = self._generate_report_content(sections)

            # Save report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = self.output_dir / f"comprehensive_report_{timestamp}.html"

            with open(report_path, "w") as f:
                f.write(report_content)

            logger.info(f"Generated comprehensive report: {report_path}")
            return report_path

        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise

    def _generate_report_content(self, sections: List[ReportSection]) -> str:
        """
        Generate the complete report content.

        Args:
            sections: List of report sections

        Returns:
            str: Complete report content
        """
        # Load report template instead of base
        template = self.env.get_template("report.html")

        # Prepare section data
        section_data = {
            "sections": [section.to_dict() for section in sections],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "title": "Comprehensive Test Analysis Report"
        }

        logger.debug(f"Rendering template with sections: {len(sections)}")
        logger.debug(f"Section data: {json.dumps(section_data, indent=2)}")

        # Render template
        return template.render(**section_data)

    def export_pdf(self, html_path: Path) -> Path:
        """
        Export the HTML report to PDF format.

        Args:
            html_path: Path to the HTML report

        Returns:
            Path to the generated PDF file
        """
        try:
            # TODO: Implement PDF export using WeasyPrint or similar
            pdf_path = html_path.with_suffix(".pdf")
            logger.info(f"PDF export not yet implemented. Would save to: {pdf_path}")
            return pdf_path

        except Exception as e:
            logger.error(f"Error exporting to PDF: {str(e)}")
            raise
