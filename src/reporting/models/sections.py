"""Report section models for the LLM Integration Testing Framework."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .base import ReportSection, ReportSectionInterface

class ProjectOverviewSection(ReportSection):
    """Section for project overview information."""

    def __init__(self, data: Dict[str, Any]):
        """Initialize project overview section."""
        self.title = "Project Overview"
        self.template_name = "project_overview.html"
        super().__init__(data)

    def _process_data(self) -> None:
        """Process project overview data."""
        self.data.setdefault("project_name", "Unknown Project")
        self.data.setdefault("description", "No description available")
        self.data.setdefault("repository_url", "")
        self.data.setdefault("analysis_date", "")
        self.data.setdefault("total_components", 0)
        self.data.setdefault("total_dependencies", 0)

class DependencyAnalysisSection(ReportSection):
    """Section for dependency analysis results."""

    def __init__(self, data: Dict[str, Any]):
        """Initialize dependency analysis section."""
        self.title = "Dependency Analysis"
        self.template_name = "dependency_analysis.html"
        super().__init__(data)

    def _process_data(self) -> None:
        """Process dependency analysis data."""
        self.data.setdefault("dependency_graph", {})
        self.data.setdefault("metrics", {
            "total_components": 0,
            "total_dependencies": 0,
            "average_dependencies": 0.0,
            "max_dependencies": 0,
            "min_dependencies": 0
        })
        self.data.setdefault("component_details", [])

class TestStrategySection(ReportSection):
    """Section for test strategy information."""

    def __init__(self, data: Dict[str, Any]):
        """Initialize test strategy section."""
        self.title = "Test Strategy"
        self.template_name = "test_strategy.html"
        super().__init__(data)

    def _process_data(self) -> None:
        """Process test strategy data."""
        self.data.setdefault("overall_approach", "")
        self.data.setdefault("component_prioritization", [])
        self.data.setdefault("test_sequences", [])
        self.data.setdefault("resource_allocation", {})
        self.data.setdefault("risk_mitigation", [])

class TestOrderSection(ReportSection):
    """Section for test execution order."""

    def __init__(self, data: Dict[str, Any]):
        """Initialize test order section."""
        self.title = "Test Execution Order"
        self.template_name = "test_order_table.html"
        super().__init__(data)

    def _process_data(self) -> None:
        """Process test order data."""
        self.data.setdefault("test_sequence", [])
        self.data.setdefault("stub_requirements", {})
        self.data.setdefault("justifications", {})
        self.data.setdefault("parallel_execution", False)

class RiskAssessmentSection(ReportSection):
    """Section for risk assessment results."""

    def __init__(self, data: Dict[str, Any]):
        """Initialize risk assessment section."""
        self.title = "Risk Assessment"
        self.template_name = "risk_assessment.html"
        super().__init__(data)

    def _process_data(self) -> None:
        """Process risk assessment data."""
        self.data.setdefault("risk_factors", [])
        self.data.setdefault("overall_risk_level", "Unknown")
        self.data.setdefault("key_concerns", [])
        self.data.setdefault("mitigation_strategies", [])

class ComplexityAssessmentSection(ReportSection):
    """Section for complexity assessment results."""

    def __init__(self, data: Dict[str, Any]):
        """Initialize complexity assessment section."""
        self.title = "Complexity Assessment"
        self.template_name = "complexity_assessment.html"
        super().__init__(data)

    def _process_data(self) -> None:
        """Process complexity assessment data."""
        self.data.setdefault("component_complexity", [])
        self.data.setdefault("overall_complexity_score", 0)
        self.data.setdefault("estimated_testing_time", "")
        self.data.setdefault("resource_requirements", {})
        self.data.setdefault("recommendations", [])

class RecommendationsSection(ReportSection):
    """Section for test recommendations."""

    def __init__(self, data: Dict[str, Any]):
        """Initialize recommendations section."""
        self.title = "Test Recommendations"
        self.template_name = "recommendations.html"
        super().__init__(data)

    def _process_data(self) -> None:
        """Process recommendations data."""
        self.data.setdefault("testing_approaches", [])
        self.data.setdefault("tool_recommendations", [])
        self.data.setdefault("automation_strategy", {})
        self.data.setdefault("environment_requirements", {})
        self.data.setdefault("execution_strategy", {})
        self.data.setdefault("reporting_approach", {})
