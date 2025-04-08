# LLM Integration Test Framework

A Python framework that uses Large Language Models to analyze codebases and generate detailed integration test recommendations.

## Overview

The LLM Integration Test Framework scans a codebase, analyzes dependencies between components, identifies integration points, and uses GPT-4o to generate detailed reports with test recommendations. It helps development teams:

- Identify critical integration points that need testing
- Understand dependency relationships between components
- Find gaps in existing test coverage
- Prioritize test efforts based on component importance
- Get detailed recommendations on testing approaches

## Features

- **Repository Scanning**: Clones and analyzes Git repositories
- **Dependency Analysis**: Creates dependency graphs and identifies component relationships
- **Integration Point Detection**: Automatically detects API, Database, UI, and External integration points
- **LLM-Powered Analysis**: Leverages GPT-4o for detailed test recommendations
- **Visual Reports**: Generates interactive HTML reports with visualizations
- **Test Coverage Analysis**: Identifies gaps in existing test coverage
- **Multi-Language Support**: Works with Python, JavaScript, TypeScript, Java and more

## Installation

### Prerequisites

- Python 3.9+
- Git
- OpenAI API key

### Setup

1. Clone this repository:

```bash
git clone https://github.com/yourusername/llm-integration-test-framework.git
cd llm-integration-test-framework
```

2. Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with your OpenAI API key:

```
OPENAI_API_KEY=your_api_key_here
```

## Usage

### Basic Usage

To analyze a repository and generate test recommendations:

```bash
python3 -m src.main analyze https://github.com/username/repository-name
```

### Command-line Options

```
Usage: python3 -m src.main analyze [OPTIONS] REPO_URL

Arguments:
  REPO_URL  URL of the GitHub repository to analyze  [required]

Options:
  -o, --output DIRECTORY         Directory to save output reports
  -v, --verbose                  Enable verbose logging
  -t, --test                     Run in test mode (skip LLM analysis)
  --help                         Show this message and exit.
```

### Environment Variables

You can configure the framework using the following environment variables in your `.env` file:

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `LLM_PROVIDER`: LLM provider to use (default: "openai")
- `LLM_MODEL`: Model name to use (default: "gpt-4o")
- `LLM_TEMPERATURE`: Temperature setting (default: 0.2)
- `LLM_MAX_TOKENS`: Maximum tokens for LLM responses (default: 4000)
- `LLM_TIMEOUT`: Timeout for LLM requests in seconds (default: 60.0)
- `OUTPUT_DIR`: Directory to save reports (default: "./reports")
- `TEMP_DIR`: Directory for temporary repository clones (default: "./temp_repos")
- `EXCLUDE_PATTERNS`: Comma-separated patterns to exclude from scanning (default: "node_modules,**pycache**,venv,.git")
- `LOG_LEVEL`: Logging level (default: "INFO")

## Output

The framework generates several outputs:

1. **HTML Report**: A comprehensive report with visualizations, recommendations, and test strategy
2. **JSON Data**: Raw data from the analysis in machine-readable format
3. **Visualizations**: Dependency graphs, heatmaps, and test coverage charts

### Report Structure

The HTML report includes:

- **Project Overview**: Summary of the analyzed codebase
- **Architecture Overview**: Analysis of the codebase architecture
- **Dependency Graph**: Visual representation of component dependencies
- **Integration Points**: Analysis of key integration points
- **Test Coverage Gaps**: Components with insufficient test coverage
- **Test Recommendations**: Specific testing recommendations for each component
- **Estimated Effort**: Estimated effort required to implement tests
- **Test Strategy**: Overall testing strategy recommendations
- **Next Steps**: Actionable next steps to improve test coverage

## Advanced Usage

### Using Makefile Targets

The framework provides several convenient Makefile targets for common operations:

```bash
# Run with test mode (no LLM API calls)
make test-run

# Run with full LLM analysis
make run-llm

# Update dependencies without recreating the virtual environment
make update-deps
```

### Testing Without LLM

For development or testing purposes, you can run the framework without making LLM API calls:

```bash
# Using Python directly
python -m src.main analyze https://github.com/username/repository-name --test

# Using the Makefile target
make test-run
```

### Verbose Logging

Enable detailed logging for troubleshooting:

```bash
python -m src.main analyze https://github.com/username/repository-name --verbose
```

### Custom Output Directory

```bash
python -m src.main analyze https://github.com/username/repository-name --output ./my-reports
```

## Development

### Project Structure

```
├── config/            # Configuration settings
├── src/
│   ├── analyzer/      # Code dependency analysis
│   ├── llm/           # LLM integration
│   ├── report/        # Report generation
│   ├── scanner/       # Repository scanning
│   └── templates/     # HTML templates
└── tests/             # Unit and integration tests
```

### Adding Support for New Languages

To add support for a new programming language:

1. Update the `LANGUAGE_EXTENSIONS` dictionary in `RepositoryScanner`
2. Add import extraction logic for the language in `_extract_dependencies`
3. Update the language-specific keywords in the `INTEGRATION_KEYWORDS` dictionary in `DependencyAnalyzer`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Acknowledgements

- OpenAI for GPT-4o
- NetworkX for dependency graph analysis
- Matplotlib for visualizations
- Jinja2 for report templating
