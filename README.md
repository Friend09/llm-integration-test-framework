# LLM Integration Test Framework

A comprehensive framework for analyzing repositories and generating test strategies using Large Language Models.

## Features

- **Repository Analysis**: Automatically analyze repository structure and identify components for testing
- **Test Strategy Generation**: Use LLM to generate comprehensive test strategies based on code analysis
- **Risk Assessment**: Identify high-risk components and integration points
- **Comprehensive Reporting**: Generate detailed HTML reports with visualizations
- **Mock Mode**: Test the framework without making actual LLM API calls
- **PDF Export**: Export reports to PDF format for sharing

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/llm-integration-test-framework.git
   cd llm-integration-test-framework
   ```

2. Set up your environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e .
   ```

3. Create a `.env` file using the provided template:
   ```bash
   cp .env.example .env
   ```

4. Edit the `.env` file to add your OpenAI API key and configure other settings.

5. Run a test analysis:
   ```bash
   python test_end_to_end.py
   ```

## Documentation

For detailed installation and usage instructions, see:

- [Installation Guide](INSTALL.md)
- [API Documentation](docs/api.md)
- [Configuration Options](docs/configuration.md)

## Example Output

The framework generates comprehensive HTML reports including:
- Executive Summary
- Component Analysis
- Test Strategy Recommendations
- Risk Assessment
- Complexity Analysis
- Test Order Recommendations

Reports are saved to the `reports/` directory.

## License

MIT License

## Contributing

Contributions are welcome! Please see [INSTALL.md](INSTALL.md) for development setup and contribution guidelines.
