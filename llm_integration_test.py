#!/usr/bin/env python3
"""
LLM Integration Testing Framework

This script analyzes GitHub repositories to identify critical integration points
and generates a comprehensive testing strategy report using OpenAI's API.
"""

import os
import sys
import json
import tempfile
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import subprocess
from dotenv import load_dotenv
import requests
from openai import OpenAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("llm_integration_test")

# Load environment variables
load_dotenv()

@dataclass
class RepoInfo:
    """Data class to store repository information."""
    url: str
    local_path: str
    files: List[Dict[str, Any]]
    languages: List[str]


@dataclass
class IntegrationPoint:
    """Data class to store integration point information."""
    source: str
    target: str
    type: str
    complexity: int
    description: str


@dataclass
class Component:
    """Data class to store component information."""
    name: str
    path: str
    language: str
    importance: int
    dependencies: List[str]
    integration_points: List[IntegrationPoint]


class LLMIntegrationTestFramework:
    """
    Main class for the LLM Integration Testing Framework.

    This framework analyzes GitHub repositories to identify critical integration
    points and generates a comprehensive testing strategy report.
    """

    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize the framework.

        Args:
            openai_api_key: OpenAI API key. If not provided, it will be loaded from
                the OPENAI_API_KEY environment variable.
        """
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")

        self.client = OpenAI(api_key=self.openai_api_key)

    def clone_repository(self, repo_url: str) -> str:
        """
        Clone a GitHub repository to a temporary directory.

        Args:
            repo_url: URL of the GitHub repository.

        Returns:
            Path to the cloned repository.

        Raises:
            RuntimeError: If the repository cannot be cloned.
        """
        logger.info(f"Cloning repository: {repo_url}")

        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()

        try:
            # Clone the repository
            result = subprocess.run(
                ["git", "clone", repo_url, temp_dir],
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(f"Repository cloned to {temp_dir}")
            return temp_dir
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to clone repository: {e.stderr}")
            raise RuntimeError(f"Failed to clone repository: {e.stderr}")

    def scan_repository(self, repo_path: str) -> RepoInfo:
        """
        Scan a repository to extract file information.

        Args:
            repo_path: Path to the repository.

        Returns:
            RepoInfo object containing repository information.
        """
        logger.info(f"Scanning repository: {repo_path}")

        repo_url = self._get_repo_url(repo_path)
        files = []
        languages = set()

        # Walk through the repository
        for root, _, filenames in os.walk(repo_path):
            for filename in filenames:
                # Skip hidden files and directories
                if filename.startswith('.') or '/.git/' in root:
                    continue

                file_path = Path(root) / filename
                relative_path = file_path.relative_to(repo_path)

                # Try to detect language based on file extension
                ext = file_path.suffix.lower()
                language = self._detect_language(ext)
                if language:
                    languages.add(language)

                # Only include relevant files
                if language or ext in ['.json', '.yaml', '.yml', '.xml', '.md']:
                    try:
                        # Read file content (limit to first 1000 lines to avoid memory issues)
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = ''.join(f.readlines()[:1000])

                        files.append({
                            'path': str(relative_path),
                            'language': language,
                            'content': content if len(content) < 50000 else f"{content[:25000]}... [content truncated] ...{content[-25000:]}",
                            'size': file_path.stat().st_size
                        })
                    except Exception as e:
                        logger.warning(f"Error reading file {file_path}: {str(e)}")

        return RepoInfo(
            url=repo_url,
            local_path=repo_path,
            files=files,
            languages=list(languages)
        )

    def _get_repo_url(self, repo_path: str) -> str:
        """Get the remote URL of a Git repository."""
        try:
            result = subprocess.run(
                ["git", "-C", repo_path, "config", "--get", "remote.origin.url"],
                check=True,
                capture_output=True,
                text=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return "Unknown"

    def _detect_language(self, extension: str) -> Optional[str]:
        """Detect programming language based on file extension."""
        language_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.jsx': 'JavaScript',
            '.tsx': 'TypeScript',
            '.java': 'Java',
            '.c': 'C',
            '.cpp': 'C++',
            '.h': 'C/C++',
            '.cs': 'C#',
            '.go': 'Go',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.rs': 'Rust',
            '.scala': 'Scala',
            '.html': 'HTML',
            '.css': 'CSS',
            '.sql': 'SQL',
        }
        return language_map.get(extension)

    def analyze_repository(self, repo_info: RepoInfo) -> Dict[str, Any]:
        """
        Analyze a repository to identify components and integration points.

        Args:
            repo_info: Repository information.

        Returns:
            Dictionary containing analysis results.
        """
        logger.info(f"Analyzing repository: {repo_info.url}")

        # Prepare the prompt for OpenAI
        prompt = self._create_analysis_prompt(repo_info)

        # Call OpenAI API
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert software architect specializing in integration testing. You analyze code repositories to identify critical components, integration points, and recommend testing strategies."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )

            analysis_text = response.choices[0].message.content

            # Try to extract JSON from the response
            try:
                # Look for JSON block in the response
                json_start = analysis_text.find("```json")
                json_end = analysis_text.rfind("```")

                if json_start != -1 and json_end != -1:
                    json_text = analysis_text[json_start + 7:json_end].strip()
                    analysis_result = json.loads(json_text)
                else:
                    # Try to parse the entire response as JSON
                    analysis_result = json.loads(analysis_text)

                return analysis_result
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON from OpenAI response, returning raw text")
                return {"raw_analysis": analysis_text}

        except Exception as e:
            logger.error(f"Error calling OpenAI API: {str(e)}")
            raise

    def _create_analysis_prompt(self, repo_info: RepoInfo) -> str:
        """Create a prompt for the OpenAI API to analyze the repository."""
        # Create a summary of the repository
        file_count = len(repo_info.files)
        language_summary = ", ".join(repo_info.languages)

        # Build a list of files to include in the prompt
        included_files = []
        total_content_length = 0
        max_content_length = 100000  # Limit to avoid exceeding OpenAI's token limit

        for file in repo_info.files:
            # Skip very large files
            if file['size'] > 100000:
                continue

            # Add file content until we reach the maximum
            content_length = len(file['content'])
            if total_content_length + content_length <= max_content_length:
                included_files.append(file)
                total_content_length += content_length
            else:
                # Just add the file path without content
                included_files.append({
                    'path': file['path'],
                    'language': file['language'],
                    'content': "[Content omitted due to size constraints]",
                    'size': file['size']
                })

        # Create the prompt
        prompt = f"""
        # Repository Analysis Request

        Analyze the following GitHub repository to identify integration testing needs:

        - Repository URL: {repo_info.url}
        - Languages: {language_summary}
        - File count: {file_count}

        ## Repository Structure

        I'll provide a selection of file contents below. Please analyze these to identify:

        1. Critical components and their dependencies
        2. Integration points between components
        3. Recommended integration testing approaches
        4. Test prioritization based on component criticality
        5. Specific test strategy recommendations

        For each integration point, assess:
        - Type (API, database, service-to-service, etc.)
        - Complexity (1-5 scale, where 5 is most complex)
        - Testing approach recommendations

        ## Files

        """

        for file in included_files:
            prompt += f"""
        ### {file['path']} ({file['language'] or 'Unknown'})

        ```
        {file['content']}
        ```

        """

        prompt += """
        ## Response Format

        Please provide your analysis in JSON format with the following structure:

        ```json
        {
          "components": [
            {
              "name": "string",
              "path": "string",
              "language": "string",
              "description": "string",
              "dependencies": ["string"],
              "importance": 1-5
            }
          ],
          "integration_points": [
            {
              "source": "string",
              "target": "string",
              "type": "string",
              "complexity": 1-5,
              "description": "string",
              "testing_approach": "string"
            }
          ],
          "testing_strategy": {
            "recommended_approach": "string",
            "justification": "string",
            "test_order": ["string"],
            "critical_areas": ["string"]
          },
          "recommendations": [
            {
              "description": "string",
              "priority": "string",
              "effort": "string"
            }
          ]
        }
        ```

        Focus on providing actionable insights for integration testing.
        """

        return prompt

    def generate_report(self, analysis_result: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """
        Generate a comprehensive HTML report from the analysis results.

        Args:
            analysis_result: Analysis results from OpenAI.
            output_path: Path to save the HTML report. If not provided, a default path
                will be used.

        Returns:
            Path to the generated report.
        """
        logger.info("Generating report")

        # Default output path if not provided
        if not output_path:
            output_path = f"integration_test_report_{int(time.time())}.html"

        # Generate HTML content
        html_content = self._generate_html_report(analysis_result)

        # Write the HTML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"Report generated: {output_path}")
        return output_path

    def _generate_html_report(self, analysis_result: Dict[str, Any]) -> str:
        """Generate HTML content for the report."""
        # Check if we have structured data or raw text
        if "raw_analysis" in analysis_result:
            # Simple HTML for raw text
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <title>Integration Testing Analysis Report</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; }}
                    h1, h2, h3 {{ color: #333; }}
                    pre {{ background-color: #f4f4f4; padding: 10px; border-radius: 5px; white-space: pre-wrap; }}
                </style>
            </head>
            <body>
                <h1>Integration Testing Analysis Report</h1>
                <h2>Raw Analysis</h2>
                <pre>{analysis_result["raw_analysis"]}</pre>
            </body>
            </html>
            """

        # Function to safely get values with default
        def safe_get(data, *keys, default="N/A"):
            for key in keys:
                if not isinstance(data, dict) or key not in data:
                    return default
                data = data[key]
            return data

        # Build a more structured HTML report
        components_html = ""
        for comp in safe_get(analysis_result, "components", default=[]):
            dependencies = ", ".join(safe_get(comp, "dependencies", default=[]))
            components_html += f"""
            <div class="component-card">
                <h3>{safe_get(comp, "name")}</h3>
                <p><strong>Path:</strong> {safe_get(comp, "path")}</p>
                <p><strong>Language:</strong> {safe_get(comp, "language")}</p>
                <p><strong>Importance:</strong> {safe_get(comp, "importance")}</p>
                <p><strong>Dependencies:</strong> {dependencies}</p>
                <p>{safe_get(comp, "description")}</p>
            </div>
            """

        integration_points_html = ""
        for point in safe_get(analysis_result, "integration_points", default=[]):
            integration_points_html += f"""
            <tr>
                <td>{safe_get(point, "source")}</td>
                <td>{safe_get(point, "target")}</td>
                <td>{safe_get(point, "type")}</td>
                <td>{safe_get(point, "complexity")}</td>
                <td>{safe_get(point, "description")}</td>
                <td>{safe_get(point, "testing_approach")}</td>
            </tr>
            """

        recommendations_html = ""
        for rec in safe_get(analysis_result, "recommendations", default=[]):
            recommendations_html += f"""
            <tr>
                <td>{safe_get(rec, "description")}</td>
                <td>{safe_get(rec, "priority")}</td>
                <td>{safe_get(rec, "effort")}</td>
            </tr>
            """

        # Get testing strategy
        strategy = safe_get(analysis_result, "testing_strategy", default={})
        approach = safe_get(strategy, "recommended_approach")
        justification = safe_get(strategy, "justification")
        test_order = ", ".join(safe_get(strategy, "test_order", default=[]))
        critical_areas = ", ".join(safe_get(strategy, "critical_areas", default=[]))

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Integration Testing Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; color: #333; }}
                h1, h2, h3 {{ color: #2c3e50; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .summary-box {{ background-color: #f8f9fa; border-left: 4px solid #4CAF50; padding: 15px; margin-bottom: 20px; }}
                table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .component-card {{ background-color: #fff; border: 1px solid #ddd; border-radius: 4px; padding: 15px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .strategy-section {{ background-color: #e8f4f8; padding: 15px; border-radius: 4px; margin-bottom: 20px; }}
                .priority-high {{ color: #d9534f; }}
                .priority-medium {{ color: #f0ad4e; }}
                .priority-low {{ color: #5bc0de; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Integration Testing Analysis Report</h1>

                <div class="summary-box">
                    <h2>Testing Strategy Summary</h2>
                    <p><strong>Recommended Approach:</strong> {approach}</p>
                    <p><strong>Justification:</strong> {justification}</p>
                    <p><strong>Suggested Test Order:</strong> {test_order}</p>
                    <p><strong>Critical Areas:</strong> {critical_areas}</p>
                </div>

                <h2>Components</h2>
                <div class="components-container">
                    {components_html}
                </div>

                <h2>Integration Points</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Source</th>
                            <th>Target</th>
                            <th>Type</th>
                            <th>Complexity</th>
                            <th>Description</th>
                            <th>Testing Approach</th>
                        </tr>
                    </thead>
                    <tbody>
                        {integration_points_html}
                    </tbody>
                </table>

                <h2>Recommendations</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Description</th>
                            <th>Priority</th>
                            <th>Effort</th>
                        </tr>
                    </thead>
                    <tbody>
                        {recommendations_html}
                    </tbody>
                </table>
            </div>
        </body>
        </html>
        """


def analyze_github_repo(repo_url: str, output_path: Optional[str] = None) -> str:
    """
    Analyze a GitHub repository and generate an integration testing report.

    Args:
        repo_url: URL of the GitHub repository.
        output_path: Path to save the HTML report. If not provided, a default path
            will be used.

    Returns:
        Path to the generated report.
    """
    try:
        # Initialize the framework
        framework = LLMIntegrationTestFramework()

        # Clone the repository
        repo_path = framework.clone_repository(repo_url)

        # Scan the repository
        repo_info = framework.scan_repository(repo_path)

        # Analyze the repository
        analysis_result = framework.analyze_repository(repo_info)

        # Generate the report
        report_path = framework.generate_report(analysis_result, output_path)

        return report_path
    except Exception as e:
        logger.error(f"Error analyzing repository: {str(e)}")
        raise


if __name__ == "__main__":
    import time

    # Check command line arguments
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <github_repo_url> [output_path]")
        sys.exit(1)

    # Get repository URL from command line
    repo_url = sys.argv[1]

    # Get output path if provided
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    # Run the analysis
    try:
        report_path = analyze_github_repo(repo_url, output_path)
        print(f"Integration testing report generated: {report_path}")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
