"""End-to-end test script for the LLM Integration Test Framework."""
import asyncio
import os
import logging
import traceback
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# Import the report generator
from src.reporting.comprehensive_report import ComprehensiveReport
from src.utils.repo_manager import RepoManager

# Configure logging
logger = logging.getLogger(__name__)

async def analyze_repo(repo_path: Path):
    """
    Analyze the repository and extract information about its structure.

    Args:
        repo_path: Path to the cloned repository

    Returns:
        Dict containing analysis results
    """
    logger.info(f"Analyzing repository at {repo_path}")

    # Component detection: Find key directories and files
    components = []
    integration_points = []

    # Track which directories contain which types of files
    dir_file_types = {}
    key_files = {}

    # Scan repository
    for root, dirs, files in os.walk(repo_path):
        rel_path = Path(root).relative_to(repo_path)

        # Skip hidden directories and common non-code directories
        if any(part.startswith('.') for part in rel_path.parts) or \
           any(part in ['node_modules', '__pycache__', 'venv', '.venv', 'dist'] for part in rel_path.parts):
            continue

        # Categorize files by extension
        file_types = {}
        for file in files:
            # Skip hidden files
            if file.startswith('.'):
                continue

            file_path = Path(root) / file
            suffix = file_path.suffix.lower()

            # Track file types in this directory
            if suffix not in file_types:
                file_types[suffix] = []
            file_types[suffix].append(file)

            # Find key files like package.json, requirements.txt, etc.
            if file.lower() in ['package.json', 'requirements.txt', 'pom.xml', 'build.gradle', 'cargo.toml', 'makefile']:
                key_files[file] = file_path

        # Store directory file types
        if file_types:
            dir_file_types[str(rel_path)] = file_types

    # Identify components based on directory structure
    for dir_path, file_types in dir_file_types.items():
        if not dir_path or dir_path == '.':
            continue

        # Determine the most common file type
        flat_files = [f for files in file_types.values() for f in files]
        main_file_type = max(file_types.keys(), key=lambda k: len(file_types[k]), default=None)

        if not main_file_type:
            continue

        # Create component
        component_name = dir_path.replace('/', '.').title()
        component_type = "Unknown"

        # Try to determine component type
        if '.py' in file_types:
            component_type = "Python Module"
        elif '.js' in file_types or '.jsx' in file_types or '.ts' in file_types or '.tsx' in file_types:
            component_type = "JavaScript/TypeScript Module"
        elif '.java' in file_types:
            component_type = "Java Module"
        elif '.cs' in file_types:
            component_type = "C# Module"
        elif '.go' in file_types:
            component_type = "Go Module"
        elif '.cpp' in file_types or '.hpp' in file_types or '.c' in file_types or '.h' in file_types:
            component_type = "C/C++ Module"

        # Determine if this is likely an integration component
        is_integration = any(term in dir_path.lower() for term in ['api', 'service', 'client', 'connector', 'interface', 'adapter'])

        components.append({
            "name": component_name,
            "requirements": [
                f"Test {component_name} functionality",
                f"Verify {component_name} error handling"
            ]
        })

        # Find potential integration points
        if is_integration:
            for other_dir in dir_file_types.keys():
                if dir_path != other_dir and not (dir_path.startswith(other_dir) or other_dir.startswith(dir_path)):
                    integration_points.append({
                        "source": component_name,
                        "target": other_dir.replace('/', '.').title(),
                        "requirements": [f"Test integration between {component_name} and {other_dir.replace('/', '.').title()}"]
                    })

    # Analyze complexity and risk
    risk_factors = []
    complexity_components = []

    for component in components:
        name = component["name"]

        # Determine risk level
        risk_level = "Low"
        risk_description = "Standard component"

        # Higher risk for integration components, security, or payment related code
        if any(term in name.lower() for term in ['api', 'auth', 'security', 'payment', 'user', 'login', 'password']):
            risk_level = "High"
            risk_description = "Security-critical component"
        elif any(term in name.lower() for term in ['service', 'database', 'storage', 'cache', 'config']):
            risk_level = "Medium"
            risk_description = "Core system component"

        risk_factors.append({
            "component": name,
            "risk_level": risk_level,
            "description": risk_description
        })

        # Determine complexity
        complexity_level = "Low"
        complexity_factors = ["Standard implementation"]

        # Higher complexity for specific component types
        if any(term in name.lower() for term in ['service', 'manager', 'controller', 'processor']):
            complexity_level = "Medium"
            complexity_factors = ["Business logic complexity", "Multiple dependencies"]

        if any(term in name.lower() for term in ['api', 'auth', 'security', 'gateway', 'engine']):
            complexity_level = "High"
            complexity_factors = ["Integration complexity", "Critical functionality", "Error handling requirements"]

        complexity_components.append({
            "name": name,
            "complexity": complexity_level,
            "factors": complexity_factors
        })

    # Determine overall risk and complexity
    risk_levels = [r["risk_level"] for r in risk_factors]
    complexity_levels = [c["complexity"] for c in complexity_components]

    overall_risk = "Medium"
    if "High" in risk_levels and risk_levels.count("High") >= len(risk_levels) / 3:
        overall_risk = "High"
    elif "Low" in risk_levels and risk_levels.count("Low") >= len(risk_levels) * 2 / 3:
        overall_risk = "Low"

    overall_complexity = "Medium"
    if "High" in complexity_levels and complexity_levels.count("High") >= len(complexity_levels) / 3:
        overall_complexity = "High"
    elif "Low" in complexity_levels and complexity_levels.count("Low") >= len(complexity_levels) * 2 / 3:
        overall_complexity = "Low"

    # Generate recommendations based on analysis
    tool_recommendations = ["Pytest for unit tests"]

    # Add more recommendations based on detected file types
    all_file_types = set()
    for file_types in dir_file_types.values():
        all_file_types.update(file_types.keys())

    if ".js" in all_file_types or ".ts" in all_file_types:
        tool_recommendations.append("Jest for JavaScript/TypeScript testing")

    if any(ext in all_file_types for ext in [".html", ".css", ".js", ".jsx", ".ts", ".tsx"]):
        tool_recommendations.append("Cypress for E2E testing")

    if "api" in ''.join(dir_file_types.keys()).lower() or "service" in ''.join(dir_file_types.keys()).lower():
        tool_recommendations.append("Postman for API testing")

    # Generate resource allocation
    resource_allocation = {}
    high_risk_components = [r["component"] for r in risk_factors if r["risk_level"] == "High"]
    medium_risk_components = [r["component"] for r in risk_factors if r["risk_level"] == "Medium"]

    # Allocate more resources to high risk components
    total_allocation = 100
    high_risk_allocation = min(60, len(high_risk_components) * 20)
    medium_risk_allocation = min(30, len(medium_risk_components) * 10)
    remaining_allocation = total_allocation - high_risk_allocation - medium_risk_allocation

    # Distribute high risk allocation
    if high_risk_components:
        per_high_component = high_risk_allocation // len(high_risk_components)
        for component in high_risk_components:
            resource_allocation[component] = f"{per_high_component}%"

    # Distribute medium risk allocation
    if medium_risk_components:
        per_medium_component = medium_risk_allocation // len(medium_risk_components)
        for component in medium_risk_components:
            resource_allocation[component] = f"{per_medium_component}%"

    # Add "Other" for remaining allocation
    if remaining_allocation > 0:
        resource_allocation["Other"] = f"{remaining_allocation}%"

    # Assemble final analysis results
    analysis_results = {
        "test_requirements": {
            "components": components,
            "integration_points": integration_points,
            "test_approach": f"Risk-based testing for {len(components)} components with focus on high-risk areas"
        },
        "risk_assessment": {
            "risk_factors": risk_factors,
            "overall_risk": overall_risk
        },
        "complexity_assessment": {
            "components": complexity_components,
            "overall_complexity": overall_complexity
        },
        "recommendations": {
            "testing_approach": f"{'Risk-based' if overall_risk == 'High' else 'Feature-based'} testing with focus on {'security' if 'High' in risk_levels else 'functionality'} testing",
            "tool_recommendations": tool_recommendations,
            "resource_allocation": resource_allocation
        }
    }

    return analysis_results

async def test_framework(repo_url: str, output_dir: str = "./reports", cleanup: bool = True):
    """
    Run end-to-end test of the LLM Integration Test Framework.
    This version performs basic analysis on the repository structure.

    Args:
        repo_url: URL of the repository to analyze
        output_dir: Directory to store generated reports
        cleanup: Whether to clean up repository files after analysis

    Returns:
        Path to the generated report if successful, None otherwise
    """
    repo_manager = None
    repo_path = None
    report_path = None

    try:
        # Create a base directory for repositories
        base_dir = Path("./temp_repos")
        base_dir.mkdir(exist_ok=True)

        logger.info("Initializing repository manager")
        repo_manager = RepoManager(base_dir=base_dir)

        logger.info(f"Cloning repository: {repo_url}")
        repo_path = await repo_manager.clone_repo(repo_url)

        logger.info(f"Repository cloned to {repo_path}")

        # Create output directory for reports
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True, parents=True)

        # Analyze the repository
        analysis_results = await analyze_repo(repo_path)

        logger.info(f"Analysis complete: Identified {len(analysis_results['test_requirements']['components'])} components and {len(analysis_results['test_requirements']['integration_points'])} integration points")

        logger.info("Generating comprehensive report")
        report_generator = ComprehensiveReport(output_dir=output_path)
        report_path = report_generator.generate(analysis_results)

        if report_path and report_path.exists():
            logger.info(f"✅ Report generated successfully at {report_path}")
            return report_path
        else:
            logger.error("❌ Failed to generate report")
            return None

    except Exception as e:
        logger.error(f"❌ End-to-end test failed: {str(e)}")
        logger.error(traceback.format_exc())
        return None

    finally:
        # Clean up repository files if requested
        if cleanup and repo_manager and repo_path:
            logger.info("Cleaning up repository files")
            await repo_manager.cleanup()

def run_analysis(repo_url: str, output_dir: str = "./reports", cleanup: bool = True):
    """
    Synchronous wrapper for the asynchronous test framework function.

    Args:
        repo_url: URL of the repository to analyze
        output_dir: Directory to store generated reports
        cleanup: Whether to clean up repository files after analysis

    Returns:
        Path to the generated report if successful, None otherwise
    """
    # Configure logging for the module
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='[%H:%M:%S]',
    )

    # Load environment variables
    load_dotenv()

    return asyncio.run(test_framework(repo_url, output_dir, cleanup))

# Command-line interface
if __name__ == "__main__":
    # Get repository URL from command line arguments if provided
    if len(sys.argv) > 1:
        repo_url = sys.argv[1]
        output_dir = sys.argv[2] if len(sys.argv) > 2 else "./reports"
    else:
        repo_url = "https://github.com/Friend09/llm-smoke-test-framework"
        output_dir = "./reports"

    logger.info(f"Starting end-to-end test with repository: {repo_url}")
    run_analysis(repo_url, output_dir)
