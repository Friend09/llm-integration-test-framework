# LLM Integration Testing Framework

A powerful framework that leverages LLMs to analyze codebases and generate comprehensive integration testing strategies.

## Current Status

The framework has completed Phase 2 of development. Here's what's working:

✓ Core infrastructure and utilities
✓ Repository management and cloning
✓ Python codebase analysis
  - Framework detection (Flask, Django, FastAPI)
  - Database integration detection
  - Service communication analysis
✓ .NET codebase analysis
  - ASP.NET Core detection
  - Entity Framework integration
  - Dependency injection analysis
✓ Dependency graph generation
✓ Integration point detection

## Features

Current capabilities:
- Repository analysis for Python and .NET codebases
- Critical component identification
- Integration point detection
- Framework-specific analysis
- Dependency graph generation
- Comprehensive test suite

Coming soon (Phase 3):
- Component relationship modeling
- Dependency analysis
- Test strategy recommendations
- Detailed HTML and JSON reports
- Command-line interface

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/llm-integration-test-framework.git
cd llm-integration-test-framework
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

The framework can be used programmatically to analyze both Python and .NET codebases:

```python
from src.scanner.repository import RepositoryManager
from src.scanner.dotnet_scanner import DotNetScanner
from src.scanner.python_scanner import PythonScanner
from pathlib import Path

# Clone and analyze a repository
with RepositoryManager("https://github.com/user/repo.git") as repo_path:
    # For .NET projects
    dotnet_scanner = DotNetScanner(repo_path)
    dotnet_scanner.scan()
    dotnet_graph = dotnet_scanner.dependency_graph

    # For Python projects
    python_scanner = PythonScanner(repo_path)
    python_scanner.scan()
    python_graph = python_scanner.dependency_graph

    # Access analysis results
    components = dotnet_graph.get_components()
    dependencies = dotnet_graph.get_dependencies()

    # Find integration points
    endpoints = [c for c in components if c.is_integration_point]
```

## Development

1. Install development dependencies:
```bash
pip install -r requirements.txt
```

2. Run tests:
```bash
pytest tests/
```

3. Run linting and type checking:
```bash
flake8 src/
mypy src/
```

## Project Structure

```
src/
├── config/         # Configuration management
├── utils/          # Utility functions
├── scanner/        # Repository scanning
│   ├── base.py    # Base scanner interface
│   ├── repository.py  # Repository management
│   ├── python_scanner.py  # Python analysis
│   └── dotnet_scanner.py  # .NET analysis
├── models/         # Data models
└── tests/         # Test suite
```

## Demo Capabilities

Current framework can demonstrate:
1. Repository Management
   - Clone and manage Git repositories
   - Support for HTTPS and SSH
   - Temporary directory handling

2. Python Analysis
   - Framework detection (Flask/Django/FastAPI)
   - Database integration detection
   - Service communication analysis
   - Package dependency mapping

3. .NET Analysis
   - ASP.NET Core component detection
   - Entity Framework integration
   - Dependency injection analysis
   - API endpoint mapping

4. Dependency Analysis
   - Component relationship mapping
   - Integration point detection
   - Dependency graph generation
   - Inheritance hierarchy analysis

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
