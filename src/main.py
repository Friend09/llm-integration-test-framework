"""Main module for LLM Integration Test Framework.

This module provides the entry point for the application and orchestrates
the entire analysis process.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from config.settings import load_config
from src.analyzer.dependency_analyzer import DependencyAnalyzer
from src.llm.analyzer import LLMAnalyzer
from src.report.report_generator import ReportGenerator
from src.scanner.repository_scanner import RepositoryScanner

# Set up console for rich output
console = Console()

# Create a Typer app
app = typer.Typer(help="LLM Integration Test Framework")


async def analyze_repository(
    repo_url: str,
    output_dir: Optional[Path] = None,
    verbose: bool = False,
    skip_llm: bool = False
) -> Path:
    """
    Analyze a repository and generate an integration test report.

    Args:
        repo_url: URL to the GitHub repository
        output_dir: Directory to save the results to
        verbose: Whether to show verbose output
        skip_llm: Whether to skip LLM analysis (useful for testing)

    Returns:
        Path: Path to the generated report
    """
    # Set up logging with rich output
    logging_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=logging_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, markup=True)]
    )
    logger = logging.getLogger("rich")

    try:
        # Load configuration
        config = load_config()

        # Override output directory if provided
        if output_dir:
            config.output_dir = output_dir

        # Extract repository name from URL
        repo_name = repo_url.split("/")[-1]
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            # Step 1: Scan the repository
            scan_task = progress.add_task("Scanning repository...", total=None)
            logger.info(f"Step 1: Scanning repository: {repo_url}")

            repo_scanner = RepositoryScanner(repo_url, config.scanner)
            repo_structure = await repo_scanner.scan()

            progress.update(scan_task, completed=True, description="Repository scan complete")

            # Step 2: Analyze dependencies
            analyze_task = progress.add_task("Analyzing dependencies...", total=None)
            logger.info("Step 2: Analyzing dependencies")

            dependency_analyzer = DependencyAnalyzer()
            analysis_result = dependency_analyzer.analyze(repo_structure)

            progress.update(analyze_task, completed=True, description="Dependency analysis complete")

            # Step 3: LLM analysis (optional)
            if not skip_llm:
                llm_task = progress.add_task("Performing LLM analysis...", total=None)
                logger.info("Step 3: Performing LLM analysis")

                llm_analyzer = LLMAnalyzer(config.llm)
                llm_report = await llm_analyzer.analyze_dependencies(
                    analysis_result, repo_structure, repo_name
                )

                progress.update(llm_task, completed=True, description="LLM analysis complete")
            else:
                # Create a dummy LLM report for testing
                from src.llm.analyzer import LLMAnalysisReport, TestCoverageRecommendation

                logger.info("Skipping LLM analysis (test mode)")

                # Create a simple test recommendation
                test_recommendation = TestCoverageRecommendation(
                    component="example_component",
                    integration_points=["point1", "point2"],
                    recommended_test_types=["integration", "api"],
                    priority=4,
                    complexity=3,
                    rationale="This is a test recommendation",
                    suggested_test_approach="Use mock objects and verify integration points",
                    test_data_requirements=["sample data 1", "sample data 2"],
                    potential_mocking_targets=["target1", "target2"]
                )

                # Create a test LLM report
                llm_report = LLMAnalysisReport(
                    project_overview="Test project overview",
                    architecture_summary="Test architecture summary",
                    identified_integration_points=[
                        {
                            "source": "source1",
                            "target": "target1",
                            "type": "API",
                            "importance": 0.8,
                            "explanation": "Test explanation"
                        }
                    ],
                    test_coverage_recommendations=[test_recommendation],
                    critical_paths_analysis="Test critical paths analysis",
                    suggested_testing_approach="Test suggested approach",
                    estimated_effort={
                        "high_priority_components": 3,
                        "estimated_person_days": 10,
                        "complexity_factors": ["factor1", "factor2"]
                    },
                    test_strategy_recommendations="Test strategy recommendations",
                    next_steps=["step1", "step2", "step3"]
                )

            # Step 4: Generate report
            report_task = progress.add_task("Generating report...", total=None)
            logger.info("Step 4: Generating report")

            report_generator = ReportGenerator(config.output_dir)
            report_path = report_generator.generate_report(
                llm_report, analysis_result, repo_name
            )

            progress.update(report_task, completed=True, description="Report generation complete")

        # Print final success message
        console.print(f"\n[bold green]Analysis complete![/bold green]")
        console.print(f"Report available at: [link file://{report_path}]{report_path}[/link]")

        return report_path

    except Exception as e:
        logger.error(f"Error analyzing repository: {str(e)}")
        if verbose:
            import traceback
            logger.debug(traceback.format_exc())
        raise


@app.command()
def analyze(
    repo_url: str = typer.Argument(..., help="URL of the GitHub repository to analyze"),
    output_dir: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Directory to save output reports"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging"
    ),
    test_mode: bool = typer.Option(
        False, "--test", "-t", help="Run in test mode (skip LLM analysis)"
    ),
):
    """Analyze a repository and generate an integration test report."""
    try:
        report_path = asyncio.run(analyze_repository(
            repo_url=repo_url,
            output_dir=output_dir,
            verbose=verbose,
            skip_llm=test_mode
        ))

        # Open report if on macOS
        if sys.platform == 'darwin':
            import subprocess
            subprocess.run(['open', report_path])

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)


@app.command()
def version():
    """Show the version of the framework."""
    console.print("[bold]LLM Integration Test Framework[/bold] v0.1.0")


if __name__ == "__main__":
    app()
