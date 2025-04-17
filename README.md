# LLM Integration Testing Framework

A tool that leverages LLM capabilities to analyze GitHub repositories, identify critical integration points, and generate comprehensive integration testing strategy reports.

## Problem Statement

Many applications lack integration testing due to resource constraints, including a shortage of dedicated testers and limited expertise in integration testing methodologies. This framework helps tackle this challenge by automating the identification of critical integration points and recommending testing strategies.

## Key Features

- **Repository Analysis**: Scan GitHub repositories to extract code structure and dependencies
- **Integration Point Detection**: Identify API endpoints, database connections, service communications, and other integration points
- **Intelligent Component Analysis**: Use OpenAI's API to analyze component relationships and criticality
- **Test Strategy Recommendation**: Apply test order generation algorithms (TD, TJJM, BLW methods) to recommend optimal testing approaches
- **Comprehensive Reporting**: Generate detailed HTML reports with visualizations and actionable recommendations

## Installation

### Prerequisites

- Python 3.7+
- Git
- OpenAI API key

### Installation Steps

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/llm-integration-test-framework.git
   cd llm-integration-test-framework
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate
   ```

3. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage

### Basic Usage

Run the tool with a GitHub repository URL:

```bash
python llm_integration_test.py https://github.com/username/repository
```

This will:
1. Clone the repository
2. Analyze its structure
3. Identify components and integration points
4. Generate a testing strategy report in HTML format

### Command-line Options

```
Usage: python llm_integration_test.py <github_repo_url> [output_path]

Arguments:
  github_repo_url     URL of the GitHub repository to analyze
  output_path         (Optional) Path to save the generated HTML report
```

## Architecture

The framework consists of the following main components:

1. **Repository Scanner**: Clones and extracts code structure from GitHub repositories
2. **Repository Analyzer**: Identifies components, dependencies, and integration points
3. **LLM Analyzer**: Uses OpenAI to analyze the repository and generate recommendations
4. **Report Generator**: Creates a comprehensive HTML report with visualizations

The workflow is as follows:

```
Repository URL → Clone Repository → Scan Files →
LLM Analysis → Generate Report → HTML Output
```

## Understanding Integration Testing Approaches

The framework recommends one of these integration testing approaches based on your codebase:

### Top-Down Integration Testing
- Testing begins with high-level components and moves down
- Uses stubs to simulate lower-level components
- Good for clear hierarchical structures and business-critical workflows

### Bottom-Up Integration Testing
- Testing begins with low-level components and moves up
- Uses drivers to simulate higher-level components
- Good for complex low-level components and database interactions

### Hybrid/Sandwich Testing
- Combines both approaches
- Tests high-level and low-level components simultaneously
- Good for large, well-defined layered architectures

### Big Bang Testing
- Integrates all components at once
- Simpler initial approach but harder to isolate issues
- Only recommended for very small applications

## Test Order Generation Algorithms

The framework applies these algorithms to determine the optimal order for testing components:

### Tai-Daniels (TD) Method
- Groups components by levels based on dependencies
- Assigns major levels based on inheritance and aggregation
- Assigns minor levels to minimize stub count

### Traon-Jéron-Jézéquel-Morel (TJJM) Method
- Identifies strongly connected components (cycles)
- Breaks cycles to create directed acyclic graph
- Determines test order to minimize total stub count

### Briand-Labiche-Wang (BLW) Method
- Similar to TJJM but focuses on minimizing specific stubs
- Prioritizes breaking association edges
- Calculates the impact of each potential cycle break

## Output

The generated HTML report includes:

- **Testing Strategy Summary**: Recommended approach with justification
- **Component Analysis**: Details of key components and their importance
- **Integration Point Mapping**: Visualization of component relationships
- **Test Recommendations**: Prioritized list of testing recommendations
- **Implementation Plan**: Suggested phased approach with effort estimates

## Development

### Setting Up Development Environment

1. Clone the repository
2. Create a virtual environment
3. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

### Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Future Enhancements

- Support for additional programming languages
- Test case generation
- Integration with CI/CD pipelines
- Web-based interface for report exploration

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- This framework builds on integration testing theories from software engineering research
- Integration testing approach selection criteria based on industry best practices
- Test order generation algorithms based on academic research by Tai-Daniels, Traon-Jéron-Jézéquel-Morel, and Briand-Labiche-Wang
