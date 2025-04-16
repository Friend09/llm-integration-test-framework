import pytest
from pathlib import Path
from src.reporting.comprehensive_report import ComprehensiveReport

@pytest.fixture
def sample_analysis_results():
    """Sample analysis results for testing."""
    return {
        "project_overview": {
            "project_name": "Test Project",
            "description": "A test project for the LLM Integration Testing Framework",
            "repository_url": "https://github.com/example/test-project",
            "analysis_date": "2024-04-16",
            "total_components": 10,
            "total_dependencies": 15
        },
        "dependency_analysis": {
            "dependency_graph": {
                "nodes": ["A", "B", "C"],
                "edges": [("A", "B"), ("B", "C")]
            },
            "metrics": {
                "total_components": 3,
                "total_dependencies": 2,
                "average_dependencies": 0.67,
                "max_dependencies": 1,
                "min_dependencies": 0
            },
            "component_details": [
                {"name": "A", "dependencies": ["B"], "dependents": []},
                {"name": "B", "dependencies": ["C"], "dependents": ["A"]},
                {"name": "C", "dependencies": [], "dependents": ["B"]}
            ]
        },
        "test_strategy": {
            "overall_approach": "Comprehensive testing approach",
            "component_prioritization": ["A", "B", "C"],
            "test_sequences": [
                {"name": "Sequence 1", "components": ["A", "B"]},
                {"name": "Sequence 2", "components": ["C"]}
            ],
            "resource_allocation": {
                "team_size": 3,
                "roles": ["Tester", "Developer", "QA Lead"]
            },
            "risk_mitigation": ["Strategy 1", "Strategy 2"]
        },
        "test_order": {
            "test_sequence": ["A", "B", "C"],
            "stub_requirements": {
                "A": ["B"],
                "B": ["C"]
            },
            "justifications": {
                "A": "Test A first",
                "B": "Test B second",
                "C": "Test C last"
            },
            "parallel_execution": False
        },
        "risk_assessment": {
            "risk_factors": [
                {
                    "name": "Risk 1",
                    "description": "Description 1",
                    "impact": "high",
                    "probability": "medium"
                }
            ],
            "overall_risk_level": "medium",
            "key_concerns": ["Concern 1", "Concern 2"],
            "mitigation_strategies": ["Strategy 1", "Strategy 2"]
        },
        "complexity_assessment": {
            "component_complexity": [
                {
                    "name": "A",
                    "cyclomatic_complexity": 5,
                    "integration_complexity": 3,
                    "test_effort": "medium"
                }
            ],
            "overall_complexity_score": 8,
            "estimated_testing_time": "2 weeks",
            "resource_requirements": {
                "team_size": 3,
                "skills": ["Python", "Testing"]
            },
            "recommendations": ["Recommendation 1", "Recommendation 2"]
        },
        "recommendations": {
            "testing_approaches": [
                {
                    "name": "Approach 1",
                    "description": "Description 1",
                    "components": ["A", "B"]
                }
            ],
            "tool_recommendations": [
                {
                    "name": "Tool 1",
                    "category": "Testing",
                    "description": "Description 1"
                }
            ],
            "automation_strategy": {
                "approach": "Comprehensive",
                "tools": ["Tool 1", "Tool 2"]
            },
            "environment_requirements": {
                "setup": ["Requirement 1", "Requirement 2"],
                "configuration": ["Config 1", "Config 2"]
            },
            "execution_strategy": {
                "sequence": ["Step 1", "Step 2"],
                "parallel": False
            },
            "reporting_approach": {
                "metrics": ["Metric 1", "Metric 2"],
                "format": "HTML"
            }
        }
    }

@pytest.fixture
def report_generator(tmp_path):
    """Create a report generator with temporary output directory."""
    return ComprehensiveReport(output_dir=str(tmp_path))

async def test_generate_report(report_generator, sample_analysis_results):
    """Test report generation with sample data."""
    # Generate report
    report_path = report_generator.generate(sample_analysis_results)

    # Verify report was created
    assert report_path.exists()
    assert report_path.suffix == ".html"

    # Verify report content
    content = report_path.read_text()
    assert "Test Project" in content
    assert "Comprehensive Test Analysis Report" in content
    assert "Dependency Analysis" in content
    assert "Test Strategy" in content
    assert "Risk Assessment" in content
    assert "Complexity Assessment" in content
    assert "Test Recommendations" in content

async def test_export_pdf(report_generator, sample_analysis_results):
    """Test PDF export functionality."""
    # Generate HTML report first
    html_path = report_generator.generate(sample_analysis_results)

    # Attempt PDF export
    pdf_path = report_generator.export_pdf(html_path)

    # Verify PDF path
    assert pdf_path.suffix == ".pdf"
    assert pdf_path.parent == html_path.parent
    assert pdf_path.stem == html_path.stem

async def test_missing_data(report_generator):
    """Test report generation with missing data."""
    # Generate report with empty data
    report_path = report_generator.generate({})

    # Verify report was created
    assert report_path.exists()
    assert report_path.suffix == ".html"

    # Verify default values are used
    content = report_path.read_text()
    assert "Unknown Project" in content
    assert "No description available" in content
