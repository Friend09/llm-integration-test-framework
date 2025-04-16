"""End-to-end test script for the LLM Integration Test Framework with OpenAI analysis."""
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
from src.llm.openai import OpenAIClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

async def analyze_repo_with_llm(repo_path: Path):
    """
    Analyze the repository using OpenAI LLM for more detailed insights.

    Args:
        repo_path: Path to the cloned repository

    Returns:
        Dict containing analysis results
    """
    logger.info(f"Analyzing repository at {repo_path}")

    # Basic analysis: Find key directories and files
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
    component_names = []
    for dir_path, file_types in dir_file_types.items():
        if not dir_path or dir_path == '.':
            continue

        # Create component
        component_name = dir_path.replace('/', '.').title()
        component_names.append(component_name)

    # Initialize OpenAI client
    llm_client = OpenAIClient()

    # Generate more detailed analysis with OpenAI
    prompt = f"""
    Analyze the following repository structure and provide detailed test requirements,
    risk assessment, complexity analysis, and test strategy recommendations.

    Repository Components:
    {json.dumps(component_names, indent=2)}

    Key Files:
    {json.dumps(list(key_files.keys()), indent=2)}

    Directory Structure by File Types:
    {json.dumps(dir_file_types, indent=2)}

    Please provide:
    1. Test requirements for each component
    2. Risk assessment for each component (High, Medium, Low) with justification
    3. Complexity assessment for each component (High, Medium, Low) with factors
    4. Testing approach and tool recommendations
    5. Resource allocation recommendations
    """

    try:
        # Define schema for structured response
        response_schema = {
            "type": "object",
            "properties": {
                "test_requirements": {
                    "type": "object",
                    "properties": {
                        "components": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "requirements": {"type": "array", "items": {"type": "string"}}
                                }
                            }
                        },
                        "integration_points": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "source": {"type": "string"},
                                    "target": {"type": "string"},
                                    "requirements": {"type": "array", "items": {"type": "string"}}
                                }
                            }
                        },
                        "test_approach": {"type": "string"}
                    }
                },
                "risk_assessment": {
                    "type": "object",
                    "properties": {
                        "risk_factors": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "component": {"type": "string"},
                                    "risk_level": {"type": "string"},
                                    "description": {"type": "string"}
                                }
                            }
                        },
                        "overall_risk": {"type": "string"}
                    }
                },
                "complexity_assessment": {
                    "type": "object",
                    "properties": {
                        "components": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "complexity": {"type": "string"},
                                    "factors": {"type": "array", "items": {"type": "string"}}
                                }
                            }
                        },
                        "overall_complexity": {"type": "string"}
                    }
                },
                "recommendations": {
                    "type": "object",
                    "properties": {
                        "testing_approach": {"type": "string"},
                        "tool_recommendations": {"type": "array", "items": {"type": "string"}},
                        "resource_allocation": {"type": "object"}
                    }
                }
            }
        }

        logger.info("Generating analysis with OpenAI...")
        analysis_results = await llm_client.generate_json(prompt, schema=response_schema)
        logger.info("OpenAI analysis complete")

        return analysis_results

    except Exception as e:
        logger.error(f"Error during OpenAI analysis: {str(e)}")
        logger.error(traceback.format_exc())

        # Fallback to basic analysis
        logger.info("Falling back to basic analysis")
        return {
            "test_requirements": {
                "components": [{"name": name, "requirements": [f"Test {name} functionality", f"Verify {name} error handling"]} for name in component_names],
                "integration_points": [],
                "test_approach": "Basic testing for all components"
            },
            "risk_assessment": {
                "risk_factors": [{"component": name, "risk_level": "Low", "description": "Standard component"} for name in component_names],
                "overall_risk": "Low"
            },
            "complexity_assessment": {
                "components": [{"name": name, "complexity": "Low", "factors": ["Standard implementation"]} for name in component_names],
                "overall_complexity": "Low"
            },
            "recommendations": {
                "testing_approach": "Feature-based testing with focus on functionality testing",
                "tool_recommendations": ["Pytest for unit tests"],
                "resource_allocation": {"Other": "100%"}
            }
        }

async def test_framework_with_openai(repo_url: str, output_dir: str = "./reports", cleanup: bool = True):
    """
    Run end-to-end test of the LLM Integration Test Framework with OpenAI.

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

        # Check for OpenAI API key
        if not os.getenv("OPENAI_API_KEY"):
            logger.error("OpenAI API key not found. Please set OPENAI_API_KEY in your .env file")
            return None

        # Analyze the repository with OpenAI
        analysis_results = await analyze_repo_with_llm(repo_path)

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

def run_openai_analysis(repo_url: str, output_dir: str = "./reports", cleanup: bool = True):
    """
    Synchronous wrapper for the asynchronous test framework function.

    Args:
        repo_url: URL of the repository to analyze
        output_dir: Directory to store generated reports
        cleanup: Whether to clean up repository files after analysis

    Returns:
        Path to the generated report if successful, None otherwise
    """
    # Load environment variables
    load_dotenv()

    return asyncio.run(test_framework_with_openai(repo_url, output_dir, cleanup))

# Command-line interface
if __name__ == "__main__":
    # Get repository URL from command line arguments if provided
    if len(sys.argv) > 1:
        repo_url = sys.argv[1]
        output_dir = sys.argv[2] if len(sys.argv) > 2 else "./reports"
    else:
        repo_url = "https://github.com/psf/requests"
        output_dir = "./reports"

    logger.info(f"Starting OpenAI-enhanced analysis with repository: {repo_url}")
    run_openai_analysis(repo_url, output_dir)
