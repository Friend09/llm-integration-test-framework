# LLM Integration Test Framework Installation Guide

## Installation Options

### Option 1: Install via pip (Recommended)

The simplest way to install the framework is using pip:

```bash
# Install from PyPI (when published)
pip install llm-test-framework

# Install from GitHub
pip install git+https://github.com/Friend09/llm-smoke-test-framework.git
```

### Option 2: Install for development

If you want to modify the code or contribute to the project:

```bash
# Clone the repository
git clone https://github.com/Friend09/llm-smoke-test-framework.git
cd llm-smoke-test-framework

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e .
```

## Environment Setup

1. Create an `.env` file in the root directory of the project:

```bash
cp .env.example .env
```

2. Edit the `.env` file to add your OpenAI API key:

```
# OpenAI API key (required for full LLM analysis)
OPENAI_API_KEY=your_api_key_here

# Default LLM settings
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=4000
```

## Quick Start

After installation, you can use the framework in two ways:

### Command Line Interface

The framework provides a powerful CLI with several command options:

```bash
# Quick analysis of a GitHub repository (no OpenAI API required)
python -m src.test_end_to_end https://github.com/username/repo.git

# or via the CLI module
python -m src.cli.main quick-test --repo-url https://github.com/username/repo.git

# Full analysis with LLM capabilities
python -m src.cli.main analyze --repo-url https://github.com/username/repo.git --output-dir ./output

# For more options
python -m src.cli.main --help
```

### Using as a Python Library

```python
# Basic import
from src.test_end_to_end import run_analysis

# Quick analysis without OpenAI API
report_path = run_analysis(
    repo_url="https://github.com/username/repo.git",
    output_dir="./reports"
)

# Using the advanced pipeline
from src.cli.main import scan_repository, analyze_dependencies, generate_strategy
from pathlib import Path

# Step 1: Scan repository
scan_result = scan_repository(
    repo_url="https://github.com/username/repo.git",
    output_path=Path("./output"),
    languages=["python"]
)

# Step 2: Analyze dependencies
dependency_result = analyze_dependencies(scan_result, Path("./output/dependencies"))

# Step 3: Generate test strategy
strategy_result = generate_strategy(
    dependency_result,
    Path("./output/strategy"),
    algorithm="tai_daniels"
)
```

## Verifying Installation

To verify that the installation is working correctly:

```bash
# Run a quick test
python -m src.test_end_to_end https://github.com/psf/requests.git
```

This should clone the repository, analyze its structure, and generate a report in the `./reports` directory.

## Troubleshooting

1. **ImportError: No module named 'src'**
   - Make sure you've installed the package using pip, or if running from source, make sure you're in the project root directory.

2. **OpenAI API errors**
   - Verify your API key is correctly set in the `.env` file.
   - If you don't have an API key, use the `quick-test` command which doesn't require one.

3. **Git errors during repository cloning**
   - Ensure you have git installed and accessible in your PATH.
   - Check that the repository URL is correct and accessible.

## Next Steps

- Read the [User Guide](./docs/user_guide.md) for more advanced usage
- Check the [API Documentation](./docs/api.md) for programmatic usage
- See [Examples](./docs/examples.md) for common use cases

# Development Setup

This document provides instructions for setting up the development environment for the LLM Integration Test Framework.

## Prerequisites

- Python 3.9 or higher
- Git
- OpenAI API key (optional for mock mode)

## Installation for Development

1. Clone the repository:

```bash
git clone https://github.com/Friend09/llm-smoke-test-framework.git
cd llm-smoke-test-framework
```

2. Create a virtual environment and activate it:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install the package in development mode:

```bash
pip install -e ".[dev]"
```

This will install all dependencies, including development dependencies.

4. Set up environment variables:

Create a `.env` file in the project root:

```
OPENAI_API_KEY=your_openai_api_key_here
MOCK_MODE=true  # Set to false for real OpenAI API calls
```

## Running Tests

The project uses pytest for testing:

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_repository_analyzer.py
```

## Linting and Type Checking

```bash
# Run flake8
flake8 src tests

# Run mypy for type checking
mypy src
```

## Project Structure

```
src/
├── analysis/       # Code analysis components
├── llm/            # LLM integration
│   └── prompts/    # Prompt templates
├── models/         # Data models
├── repository/     # Repository management
├── reporting/      # Report generation
│   └── templates/  # HTML templates
├── strategy/       # Test strategy generation
├── utils/          # Utility functions
└── cli/            # Command line interface
tests/              # Test suite
```

## Development Workflow

1. Create a new branch for your feature or bug fix:

```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and add tests as needed

3. Run tests and linting to ensure code quality:

```bash
pytest
flake8 src tests
mypy src
```

4. Commit your changes with descriptive commit messages:

```bash
git commit -m "Add feature X" -m "This feature does Y and Z"
```

5. Push your branch and create a pull request on GitHub:

```bash
git push -u origin feature/your-feature-name
```

## Best Practices

- Follow PEP 8 style guidelines
- Add type hints to all functions and methods
- Write docstrings for all modules, classes, and functions
- Write tests for new features
- Keep dependencies minimal and well-justified

## Troubleshooting

### Import Errors

If you encounter import errors, make sure:
- You're running commands from the project root
- The virtual environment is activated
- The package is installed in development mode (`pip install -e .`)

### LLM API Errors

- For testing without an API key, set `MOCK_MODE=true` in your `.env` file
- Check the mock data in `src/llm/mock.py` for testing

### Git Errors

- Ensure git is installed and accessible in your PATH
- Check repository URLs are correct and accessible

## Release Process

1. Update version in `setup.py`
2. Update CHANGELOG.md with recent changes
3. Create a new tag with the version number:

```bash
git tag v0.1.0
git push origin v0.1.0
```

4. Build the distribution:

```bash
python -m build
```

5. Publish to PyPI (authorized contributors only):

```bash
python -m twine upload dist/*
```
