"""LLM Integration Testing Framework CLI entry point.

This CLI allows users to analyze a GitHub repository and generate an integration testing strategy report.
Each step of the framework can be run independently or as a complete pipeline.

Usage examples:
    # Run the full pipeline
    python -m src.cli.main analyze --repo-url https://github.com/psf/requests.git --output-dir ./output

    # Run just the repository scanner
    python -m src.cli.main scan --repo-url https://github.com/psf/requests.git --output-dir ./output

    # Generate a test strategy from existing scan results
    python -m src.cli.main strategy --scan-dir ./output/scan --output-dir ./output
"""
import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.logging import RichHandler

from ..models.component import Component
from ..models.relationship import Relationship
from ..models.dependency_graph import DependencyGraph
from ..models.test_order import TestOrderResult
from ..models.test_approach import TestApproach
from ..strategy.test_algorithms.tai_daniels import TaiDanielsAlgorithm
from ..strategy.test_algorithms.tjjm import TJJMAlgorithm
from ..strategy.test_algorithms.blw import BLWAlgorithm
from ..scanner.repository import RepositoryScanner
from ..utils.repo_manager import RepoManager
from ..reporting.report_generator import ReportGenerator

# Import the quick test functionality
# from .. import test_end_to_end

console = Console()
app = typer.Typer(help="LLM Integration Testing Framework CLI")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.command()
def analyze(
    repo_url: str = typer.Option(..., help="GitHub repository URL to analyze."),
    output_dir: str = typer.Option("./output", help="Directory to store the generated report."),
    report_format: str = typer.Option("html", help="Report format: html, json, or both."),
    language: List[str] = typer.Option(["python"], help="Languages to analyze: python, dotnet, or both."),
    llm_enabled: bool = typer.Option(True, help="Enable LLM analysis."),
    test_order_algorithm: str = typer.Option(
        "tai_daniels",
        help="Test order algorithm: tai_daniels, tjjm, blw, or auto."
    ),
):
    """Analyze a GitHub repository and generate a complete integration testing strategy report.

    This command runs the entire pipeline from repository scanning to report generation.
    """
    console.print(Panel.fit("LLM Integration Testing Framework", title="Starting Analysis"))
    console.print(f"[bold]Repository:[/bold] {repo_url}")
    console.print(f"[bold]Output Directory:[/bold] {output_dir}")

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_id = f"run-{timestamp}"
    output_path = Path(output_dir) / run_id
    output_path.mkdir(parents=True, exist_ok=True)

    try:
        # Step 1: Repository Scanning
        scan_result_path = scan_repository(repo_url, output_path, language)

        # Step 2: Dependency Analysis
        dependency_result_path = analyze_dependencies(scan_result_path, output_path)

        # Step 3: Strategy Generation
        strategy_result_path = generate_strategy(dependency_result_path, output_path, test_order_algorithm)

        # Step 4: LLM Analysis (optional)
        if llm_enabled:
            llm_result_path = perform_llm_analysis(strategy_result_path, output_path)
            report_input_path = llm_result_path
        else:
            report_input_path = strategy_result_path

        # Step 5: Report Generation
        report_path = generate_report(report_input_path, output_path, report_format)

        console.print(Panel.fit(f"Analysis complete! Reports available at:\n{report_path}",
                               title="Success", border_style="green"))
    except Exception as exc:
        console.print(Panel.fit(f"Error: {exc}", title="Error", border_style="red"))
        raise typer.Exit(code=1)


@app.command()
def scan(
    repo_url: str = typer.Option(..., help="GitHub repository URL to scan."),
    output_dir: str = typer.Option("./output/scan", help="Directory to store scan results."),
    language: List[str] = typer.Option(["python"], help="Languages to analyze: python, dotnet, or both."),
):
    """Scan a repository to extract components and structure.

    This command clones the repository and runs the appropriate scanners based on the languages specified.
    """
    console.print(Panel.fit("Repository Scanner", title="Step 1 of 5"))
    console.print(f"[bold]Repository:[/bold] {repo_url}")
    console.print(f"[bold]Output Directory:[/bold] {output_dir}")

    try:
        scan_result_path = scan_repository(repo_url, Path(output_dir), language)
        console.print(Panel.fit(f"Scan complete! Results available at:\n{scan_result_path}",
                              title="Success", border_style="green"))
        return scan_result_path
    except Exception as exc:
        console.print(Panel.fit(f"Error: {exc}", title="Error", border_style="red"))
        raise typer.Exit(code=1)


@app.command()
def analyze_deps(
    scan_dir: str = typer.Option(..., help="Directory containing scan results."),
    output_dir: str = typer.Option("./output/dependencies", help="Directory to store dependency analysis results."),
):
    """Analyze dependencies between components from scan results.

    This command analyzes the component relationships and builds a dependency graph.
    """
    console.print(Panel.fit("Dependency Analyzer", title="Step 2 of 5"))
    console.print(f"[bold]Input Directory:[/bold] {scan_dir}")
    console.print(f"[bold]Output Directory:[/bold] {output_dir}")

    try:
        dependency_result_path = analyze_dependencies(Path(scan_dir), Path(output_dir))
        console.print(Panel.fit(f"Dependency analysis complete! Results available at:\n{dependency_result_path}",
                                title="Success", border_style="green"))
        return dependency_result_path
    except Exception as exc:
        console.print(Panel.fit(f"Error: {exc}", title="Error", border_style="red"))
        raise typer.Exit(code=1)


@app.command()
def strategy(
    dependency_dir: str = typer.Option(..., help="Directory containing dependency analysis results."),
    output_dir: str = typer.Option("./output/strategy", help="Directory to store strategy generation results."),
    algorithm: str = typer.Option(
        "tai_daniels",
        help="Test order algorithm: tai_daniels, tjjm, blw, or auto."
    ),
):
    """Generate testing strategy based on dependency analysis.

    This command recommends a testing approach and determines an optimal testing order.
    """
    console.print(Panel.fit("Strategy Generator", title="Step 3 of 5"))
    console.print(f"[bold]Input Directory:[/bold] {dependency_dir}")
    console.print(f"[bold]Output Directory:[/bold] {output_dir}")
    console.print(f"[bold]Algorithm:[/bold] {algorithm}")

    try:
        strategy_result_path = generate_strategy(Path(dependency_dir), Path(output_dir), algorithm)
        console.print(Panel.fit(f"Strategy generation complete! Results available at:\n{strategy_result_path}",
                               title="Success", border_style="green"))
        return strategy_result_path
    except Exception as exc:
        console.print(Panel.fit(f"Error: {exc}", title="Error", border_style="red"))
        raise typer.Exit(code=1)


@app.command()
def llm_analyze(
    strategy_dir: str = typer.Option(..., help="Directory containing strategy results."),
    output_dir: str = typer.Option("./output/llm", help="Directory to store LLM analysis results."),
):
    """Enhance strategy with LLM-powered analysis.

    This command uses LLMs to provide additional insights and recommendations.
    """
    console.print(Panel.fit("LLM Analyzer", title="Step 4 of 5"))
    console.print(f"[bold]Input Directory:[/bold] {strategy_dir}")
    console.print(f"[bold]Output Directory:[/bold] {output_dir}")

    try:
        llm_result_path = perform_llm_analysis(Path(strategy_dir), Path(output_dir))
        console.print(Panel.fit(f"LLM analysis complete! Results available at:\n{llm_result_path}",
                               title="Success", border_style="green"))
        return llm_result_path
    except Exception as exc:
        console.print(Panel.fit(f"Error: {exc}", title="Error", border_style="red"))
        raise typer.Exit(code=1)


@app.command()
def report(
    input_dir: str = typer.Option(..., help="Directory containing analysis results (LLM or strategy)."),
    output_dir: str = typer.Option("./output/report", help="Directory to store the generated report."),
    report_format: str = typer.Option("html", help="Report format: html, json, or both."),
):
    """Generate detailed reports from analysis results.

    This command creates HTML and/or JSON reports with visualizations.
    """
    console.print(Panel.fit("Report Generator", title="Step 5 of 5"))
    console.print(f"[bold]Input Directory:[/bold] {input_dir}")
    console.print(f"[bold]Output Directory:[/bold] {output_dir}")
    console.print(f"[bold]Format:[/bold] {report_format}")

    try:
        report_path = generate_report(Path(input_dir), Path(output_dir), report_format)
        console.print(Panel.fit(f"Report generation complete! Reports available at:\n{report_path}",
                               title="Success", border_style="green"))
        return report_path
    except Exception as exc:
        console.print(Panel.fit(f"Error: {exc}", title="Error", border_style="red"))
        raise typer.Exit(code=1)


@app.command()
def test_order(
    dependency_dir: str = typer.Option(..., help="Directory containing dependency analysis results."),
    output_dir: str = typer.Option("./output/test_order", help="Directory to store test order results."),
    algorithm: str = typer.Option(
        "tai_daniels",
        help="Test order algorithm: tai_daniels, tjjm, blw, or compare."
    ),
):
    """Generate test order using a specific algorithm.

    This command runs a single test order algorithm and outputs the results.
    If 'compare' is specified, all algorithms are run and compared.
    """
    console.print(Panel.fit("Test Order Algorithm", title="Test Sequencing"))
    console.print(f"[bold]Input Directory:[/bold] {dependency_dir}")
    console.print(f"[bold]Output Directory:[/bold] {output_dir}")
    console.print(f"[bold]Algorithm:[/bold] {algorithm}")

    try:
        # Load dependency graph
        dependency_path = Path(dependency_dir) / "dependency_graph.json"
        if not dependency_path.exists():
            raise FileNotFoundError(f"Dependency graph not found at {dependency_path}")

        from src.models.dependency_graph import DependencyGraph
        from src.strategy.test_order.tai_daniels import TaiDanielsOrderGenerator
        from src.strategy.test_order.tjjm import TJJMOrderGenerator
        from src.strategy.test_order.blw import BLWOrderGenerator

        # Load dependency graph from file
        with open(dependency_path, 'r') as f:
            graph_data = json.load(f)

        dependency_graph = DependencyGraph.from_dict(graph_data)

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        results = {}

        if algorithm.lower() == "compare":
            # Run all algorithms and compare
            algorithms = {
                "tai_daniels": TaiDanielsOrderGenerator,
                "tjjm": TJJMOrderGenerator,
                "blw": BLWOrderGenerator
            }

            for algo_name, algo_class in algorithms.items():
                console.print(f"Running {algo_name} algorithm...")
                generator = algo_class(dependency_graph)
                test_order = generator.generate_order()
                results[algo_name] = {
                    "order": [comp.name for comp in test_order.order],
                    "metrics": test_order.metrics,
                    "stubs": {comp.name: [stub.name for stub in stubs]
                             for comp, stubs in test_order.stubs.items()}
                }

            # Save comparison results
            comparison_path = output_path / "algorithm_comparison.json"
            with open(comparison_path, 'w') as f:
                json.dump(results, f, indent=2)

            console.print(Panel.fit(f"Algorithm comparison complete! Results available at:\n{comparison_path}",
                                   title="Success", border_style="green"))
            return comparison_path
        else:
            # Run a single algorithm
            if algorithm.lower() == "tai_daniels":
                generator = TaiDanielsOrderGenerator(dependency_graph)
            elif algorithm.lower() == "tjjm":
                generator = TJJMOrderGenerator(dependency_graph)
            elif algorithm.lower() == "blw":
                generator = BLWOrderGenerator(dependency_graph)
            else:
                raise ValueError(f"Unknown algorithm: {algorithm}")

            test_order = generator.generate_order()
            result = {
                "order": [comp.name for comp in test_order.order],
                "metrics": test_order.metrics,
                "stubs": {comp.name: [stub.name for stub in stubs]
                         for comp, stubs in test_order.stubs.items()}
            }

            # Save results
            result_path = output_path / f"{algorithm.lower()}_results.json"
            with open(result_path, 'w') as f:
                json.dump(result, f, indent=2)

            console.print(Panel.fit(f"Test order generation complete! Results available at:\n{result_path}",
                                   title="Success", border_style="green"))
            return result_path

    except Exception as exc:
        console.print(Panel.fit(f"Error: {exc}", title="Error", border_style="red"))
        raise typer.Exit(code=1)


@app.command()
def quick_test(
    repo_url: str = typer.Option(..., help="GitHub repository URL to analyze."),
    output_dir: str = typer.Option("./reports", help="Directory to store the generated report."),
    cleanup: bool = typer.Option(True, help="Clean up temporary files after analysis.")
):
    """
    Perform a quick analysis of a repository without requiring OpenAI API access.

    This command uses a simplified analysis approach that examines the repository structure
    and generates a basic test strategy report. It's useful for getting a quick overview
    or when you don't have an OpenAI API key configured.
    """
    logger.info(f"Starting quick analysis of {repo_url}")

    try:
        # Run the analysis
        from ..test_end_to_end import run_analysis
        report_path = run_analysis(repo_url, output_dir, cleanup)

        if report_path:
            logger.info(f"✅ Analysis complete. Report available at: {report_path}")
            return 0
        else:
            logger.error("❌ Analysis failed.")
            return 1
    except Exception as e:
        logger.error(f"❌ Error during quick analysis: {str(e)}")
        return 1


# Helper functions for command implementation
def scan_repository(repo_url: str, output_path: Path, languages: List[str]) -> Path:
    """Run repository scanner on the given repository."""
    from src.scanner.repository import RepositoryManager
    from src.scanner.python_scanner import PythonScanner
    from src.scanner.dotnet_scanner import DotNetScanner

    # Create output directory
    scan_output = output_path / "scan"
    scan_output.mkdir(parents=True, exist_ok=True)

    # Clone repository
    logger.info(f"Cloning repository: {repo_url}")
    with RepositoryManager(repo_url) as repo_path:
        logger.info(f"Repository cloned to: {repo_path}")

        scanners = []
        scanner_results = {}

        # Initialize scanners based on languages
        if "python" in languages or "all" in languages:
            logger.info("Initializing Python scanner")
            python_scanner = PythonScanner(repo_path)
            scanners.append(("python", python_scanner))

        if "dotnet" in languages or "all" in languages:
            logger.info("Initializing .NET scanner")
            dotnet_scanner = DotNetScanner(repo_path)
            scanners.append(("dotnet", dotnet_scanner))

        if not scanners:
            raise ValueError(f"No scanners initialized for languages: {languages}")

        # Run scanners
        for lang, scanner in scanners:
            logger.info(f"Running {lang} scanner")
            scanner.scan()

            # Save scanner results
            scanner_results[lang] = {
                "components": [comp.to_dict() for comp in scanner.dependency_graph.get_components()],
                "relationships": [rel.to_dict() for rel in scanner.dependency_graph.get_relationships()]
            }

            if hasattr(scanner, "integration_points"):
                scanner_results[lang]["integration_points"] = [
                    ip.to_dict() for ip in scanner.integration_points
                ]

        # Save combined results
        logger.info("Saving scanner results")
        results_path = scan_output / "scan_results.json"
        with open(results_path, 'w') as f:
            json.dump(scanner_results, f, indent=2)

        return scan_output


def analyze_dependencies(scan_path: Path, output_path: Path) -> Path:
    """Analyze dependencies from scan results."""
    from src.models.dependency_graph import DependencyGraph

    # Create output directory
    dep_output = output_path
    dep_output.mkdir(parents=True, exist_ok=True)

    # Load scan results
    logger.info(f"Loading scan results from {scan_path}")
    scan_results_path = scan_path / "scan_results.json"

    if not scan_results_path.exists():
        raise FileNotFoundError(f"Scan results not found at {scan_results_path}")

    with open(scan_results_path, 'r') as f:
        scan_results = json.load(f)

    # Combine results from all languages
    all_components = []
    all_relationships = []
    all_integration_points = []

    for lang, results in scan_results.items():
        all_components.extend(results.get("components", []))
        all_relationships.extend(results.get("relationships", []))
        all_integration_points.extend(results.get("integration_points", []))

    # Create a combined dependency graph
    logger.info("Building combined dependency graph")
    dependency_graph = DependencyGraph()

    # Add components and relationships to graph
    for comp_dict in all_components:
        dependency_graph.add_component_from_dict(comp_dict)

    for rel_dict in all_relationships:
        dependency_graph.add_relationship_from_dict(rel_dict)

    # Save dependency graph
    logger.info("Saving dependency graph")
    graph_path = dep_output / "dependency_graph.json"
    with open(graph_path, 'w') as f:
        json.dump(dependency_graph.to_dict(), f, indent=2)

    # Save integration points
    if all_integration_points:
        logger.info("Saving integration points")
        ip_path = dep_output / "integration_points.json"
        with open(ip_path, 'w') as f:
            json.dump(all_integration_points, f, indent=2)

    # Generate graph metrics
    logger.info("Computing graph metrics")
    metrics = {
        "component_count": len(dependency_graph.get_components()),
        "relationship_count": len(dependency_graph.get_relationships()),
        "integration_point_count": len(all_integration_points),
        "cycles": len(dependency_graph.find_cycles()),
        "max_depth": dependency_graph.get_max_depth()
    }

    metrics_path = dep_output / "graph_metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)

    return dep_output


def generate_strategy(dependency_path: Path, output_path: Path, algorithm: str) -> Path:
    """Generate test strategy from dependency analysis."""
    # Create output directory
    strategy_output = output_path
    strategy_output.mkdir(parents=True, exist_ok=True)

    # Load dependency graph
    logger.info(f"Loading dependency graph from {dependency_path}")
    graph_path = dependency_path / "dependency_graph.json"

    if not graph_path.exists():
        raise FileNotFoundError(f"Dependency graph not found at {graph_path}")

    # Load integration points if available
    ip_path = dependency_path / "integration_points.json"
    integration_points = []

    if ip_path.exists():
        logger.info(f"Loading integration points from {ip_path}")
        with open(ip_path, 'r') as f:
            ip_data = json.load(f)

        from src.models.integration_points.base import IntegrationPoint
        integration_points = [IntegrationPoint.from_dict(ip) for ip in ip_data]

    # Load dependency graph
    from src.models.dependency_graph import DependencyGraph

    with open(graph_path, 'r') as f:
        graph_data = json.load(f)

    dependency_graph = DependencyGraph.from_dict(graph_data)

    # Generate test approach recommendations
    logger.info("Generating test approach recommendations")
    from src.strategy.approach_recommender import TestApproachRecommender

    recommender = TestApproachRecommender(dependency_graph, integration_points)
    approach = recommender.recommend_approach()

    # Save approach recommendation
    approach_path = strategy_output / "approach_recommendation.json"
    with open(approach_path, 'w') as f:
        json.dump(approach.to_dict(), f, indent=2)

    # Generate test order
    logger.info(f"Generating test order using {algorithm} algorithm")
    from src.strategy.test_order.tai_daniels import TaiDanielsOrderGenerator
    from src.strategy.test_order.tjjm import TJJMOrderGenerator
    from src.strategy.test_order.blw import BLWOrderGenerator

    # Select algorithm
    if algorithm.lower() == "auto":
        # Auto-select algorithm based on graph properties
        if len(dependency_graph.find_cycles()) > 0:
            logger.info("Cycles detected, using TJJM algorithm")
            generator = TJJMOrderGenerator(dependency_graph)
        else:
            logger.info("No cycles detected, using Tai-Daniels algorithm")
            generator = TaiDanielsOrderGenerator(dependency_graph)
    elif algorithm.lower() == "tai_daniels":
        generator = TaiDanielsOrderGenerator(dependency_graph)
    elif algorithm.lower() == "tjjm":
        generator = TJJMOrderGenerator(dependency_graph)
    elif algorithm.lower() == "blw":
        generator = BLWOrderGenerator(dependency_graph)
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")

    test_order = generator.generate_order()

    # Save test order
    order_path = strategy_output / f"test_order_{algorithm.lower()}.json"
    with open(order_path, 'w') as f:
        order_data = {
            "order": [comp.name for comp in test_order.order],
            "metrics": test_order.metrics,
            "level_assignments": {comp.name: level for comp, level in test_order.level_assignments.items()},
            "stubs": {comp.name: [stub.name for stub in stubs] for comp, stubs in test_order.stubs.items()}
        }
        json.dump(order_data, f, indent=2)

    # Save complete strategy
    strategy_data = {
        "approach": approach.to_dict(),
        "test_order": {
            "algorithm": algorithm,
            "order": [comp.name for comp in test_order.order],
            "metrics": test_order.metrics,
            "stubs": {comp.name: [stub.name for stub in stubs] for comp, stubs in test_order.stubs.items()}
        },
        "graph_statistics": {
            "component_count": len(dependency_graph.get_components()),
            "relationship_count": len(dependency_graph.get_relationships()),
            "integration_point_count": len(integration_points),
            "cycle_count": len(dependency_graph.find_cycles())
        }
    }

    strategy_path = strategy_output / "test_strategy.json"
    with open(strategy_path, 'w') as f:
        json.dump(strategy_data, f, indent=2)

    return strategy_output


def perform_llm_analysis(strategy_path: Path, output_path: Path) -> Path:
    """Enhance strategy with LLM-powered analysis."""
    # Create output directory
    llm_output = output_path
    llm_output.mkdir(parents=True, exist_ok=True)

    # Load test strategy
    logger.info(f"Loading test strategy from {strategy_path}")
    strategy_file = strategy_path / "test_strategy.json"

    if not strategy_file.exists():
        raise FileNotFoundError(f"Test strategy not found at {strategy_file}")

    with open(strategy_file, 'r') as f:
        strategy_data = json.load(f)

    # Initialize LLM client
    logger.info("Initializing LLM client")
    from src.llm.openai import OpenAIClient
    from src.llm.prompts.component_analysis import ComponentAnalysisPrompt
    from src.llm.prompts.strategy_analysis import StrategyAnalysisPrompt

    llm_client = OpenAIClient()

    # Generate LLM analysis
    logger.info("Generating LLM component analysis")
    component_prompt = ComponentAnalysisPrompt()
    prompt_text = component_prompt.render(
        components=strategy_data.get("graph_statistics", {}).get("component_count", 0),
        relationships=strategy_data.get("graph_statistics", {}).get("relationship_count", 0),
        integration_points=strategy_data.get("graph_statistics", {}).get("integration_point_count", 0),
        cycles=strategy_data.get("graph_statistics", {}).get("cycle_count", 0),
        test_order=strategy_data.get("test_order", {}).get("order", [])
    )

    component_analysis = llm_client.generate_json(
        prompt=prompt_text,
        schema=component_prompt.get_schema()
    )

    # Generate test strategy analysis
    logger.info("Generating LLM strategy analysis")
    strategy_prompt = StrategyAnalysisPrompt()
    prompt_text = strategy_prompt.render(
        approach=strategy_data.get("approach", {}),
        test_order=strategy_data.get("test_order", {})
    )

    strategy_analysis = llm_client.generate_json(
        prompt=prompt_text,
        schema=strategy_prompt.get_schema()
    )

    # Combine analyses
    llm_analysis = {
        "component_analysis": component_analysis,
        "strategy_analysis": strategy_analysis,
        "timestamp": datetime.now().isoformat()
    }

    # Save LLM analysis
    analysis_path = llm_output / "llm_analysis.json"
    with open(analysis_path, 'w') as f:
        json.dump(llm_analysis, f, indent=2)

    # Save enhanced strategy
    enhanced_strategy = {**strategy_data, "llm_analysis": llm_analysis}
    enhanced_path = llm_output / "enhanced_strategy.json"
    with open(enhanced_path, 'w') as f:
        json.dump(enhanced_strategy, f, indent=2)

    return llm_output


def generate_report(input_path: Path, output_path: Path, report_format: str) -> Path:
    """Generate reports from analysis results."""
    # Create output directory
    report_output = output_path
    report_output.mkdir(parents=True, exist_ok=True)

    # Load input data (either enhanced strategy or regular strategy)
    logger.info(f"Loading analysis results from {input_path}")

    enhanced_strategy_path = input_path / "enhanced_strategy.json"
    regular_strategy_path = input_path / "test_strategy.json"

    if enhanced_strategy_path.exists():
        strategy_path = enhanced_strategy_path
        has_llm = True
    elif regular_strategy_path.exists():
        strategy_path = regular_strategy_path
        has_llm = False
    else:
        raise FileNotFoundError(f"Strategy data not found in {input_path}")

    with open(strategy_path, 'r') as f:
        strategy_data = json.load(f)

    # Load dependency graph
    dependency_path = None
    for parent in [input_path, input_path.parent / "dependencies", input_path.parent.parent / "dependencies"]:
        if (parent / "dependency_graph.json").exists():
            dependency_path = parent / "dependency_graph.json"
            break

    if not dependency_path:
        logger.warning("Dependency graph not found, some report features will be limited")
    else:
        logger.info(f"Loading dependency graph from {dependency_path}")

    from src.models.dependency_graph import DependencyGraph

    if dependency_path and dependency_path.exists():
        with open(dependency_path, 'r') as f:
            graph_data = json.load(f)

        dependency_graph = DependencyGraph.from_dict(graph_data)
    else:
        dependency_graph = DependencyGraph()

    # Load integration points
    ip_path = None
    for parent in [input_path, input_path.parent / "dependencies", input_path.parent.parent / "dependencies"]:
        if (parent / "integration_points.json").exists():
            ip_path = parent / "integration_points.json"
            break

    integration_points = []
    if ip_path and ip_path.exists():
        logger.info(f"Loading integration points from {ip_path}")
        with open(ip_path, 'r') as f:
            ip_data = json.load(f)

        from src.models.integration_points.base import IntegrationPoint
        integration_points = [IntegrationPoint.from_dict(ip) for ip in ip_data]

    # Initialize report generator
    logger.info("Initializing report generator")
    from src.reporting.test_strategy_report import TestStrategyReportGenerator

    llm_analysis = strategy_data.get("llm_analysis") if has_llm else None

    report_generator = TestStrategyReportGenerator(
        dependency_graph=dependency_graph,
        integration_points=integration_points,
        llm_analysis=llm_analysis
    )

    # Extract test approach and order
    from src.strategy.approach_recommender import TestingApproach
    from src.strategy.test_order.base import TestOrderResult

    # Create TestingApproach object from dict
    approach_data = strategy_data.get("approach", {})
    approach = TestingApproach(
        name=approach_data.get("name", "Unknown"),
        score=approach_data.get("score", 0.0),
        advantages=approach_data.get("advantages", []),
        disadvantages=approach_data.get("disadvantages", []),
        prerequisites=approach_data.get("prerequisites", []),
        risks=approach_data.get("risks", []),
        estimated_effort=approach_data.get("estimated_effort", "Unknown")
    )

    # Create TestOrderResult object from dict
    test_order_data = strategy_data.get("test_order", {})
    test_order = TestOrderResult(
        order=[dependency_graph.get_component(name) for name in test_order_data.get("order", [])],
        metrics=test_order_data.get("metrics", {}),
        stubs={},
        level_assignments={}
    )

    # Generate report
    logger.info(f"Generating {report_format} report")
    report_generator.generate_report(
        recommended_approach=approach,
        test_order=test_order,
        output_dir=str(report_output),
        title=f"Test Strategy Report"
    )

    return report_output


if __name__ == "__main__":
    app()


def main():
    """Entry point for the CLI when installed as a package."""
    app()


if __name__ == "__main__":
    main()
