# Integration Testing Tool

An AI-powered application that analyzes GitHub repositories, identifies integration testing needs, generates comprehensive reports, and creates executable integration tests for any type of application.

## Features

- **Repository Analysis**: Automatically clones and analyzes GitHub repositories
- **Language Detection**: Supports multiple programming languages (Python, JavaScript, Java, C/C++, C#, Go, Rust, PHP, Ruby)
- **Integration Point Identification**: Uses AST parsing and pattern recognition to identify potential integration points
- **Test Scenario Generation**: Generates comprehensive test scenarios based on identified integration patterns
- **Test Code Generation**: Creates executable test code in multiple frameworks (pytest, Jest, JUnit)
- **Web Interface**: User-friendly web interface for easy interaction
- **RESTful API**: Programmatic access for CI/CD integration

## Architecture

The application follows a modular architecture with the following components:

### 1. Repository Ingestion Module
- Clones GitHub repositories using GitPython
- Manages temporary storage and cleanup
- Handles various repository structures

### 2. Code Analysis Module
- Analyzes repository structure and file types
- Identifies programming languages
- Parses code using AST (Abstract Syntax Tree) analysis
- Detects integration patterns through static analysis

### 3. Integration Point Detection
- Database integrations (SQLite, PostgreSQL, MongoDB, SQLAlchemy, Django ORM)
- HTTP/API integrations (requests, Flask, Django, FastAPI, Express.js)
- File I/O operations
- External service integrations (AWS, Redis, Celery, Kafka)
- Authentication and authorization systems

### 4. Test Generation Module
- Generates test scenarios based on identified integration points
- Creates executable test code for multiple frameworks
- Supports Python (pytest), JavaScript (Jest), and Java (JUnit)
- Includes proper setup/teardown, mocking, and assertions

### 5. Web Interface
- Modern, responsive design
- Step-by-step workflow visualization
- Real-time analysis progress
- Test code preview and download

## Installation

### Prerequisites
- Python 3.11+
- Git
- Virtual environment support

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd integration_testing_app
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables (optional):
```bash
export OPENAI_API_KEY="your-openai-api-key"  # For AI-enhanced analysis
```

## Usage

### Starting the Application

```bash
cd integration_testing_app
source venv/bin/activate
python src/main.py
```

The application will be available at `http://localhost:5000`

### Web Interface Usage

1. **Repository Input**: Enter a GitHub repository URL
2. **Analysis**: Click "Analyze Repository" to start the analysis
3. **Test Generation**: Select programming language and click "Generate Integration Tests"
4. **Download**: Download the generated test files

### API Usage

#### Analyze Repository
```bash
curl -X POST http://localhost:5000/api/integration/analyze \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/username/repository"}'
```

#### Generate Tests
```bash
curl -X POST http://localhost:5000/api/integration/generate-tests \
  -H "Content-Type: application/json" \
  -d '{
    "test_scenarios": [...],
    "language": "python"
  }'
```

#### Health Check
```bash
curl http://localhost:5000/api/integration/health
```

## Integration Patterns Detected

### Database Integrations
- **SQLite**: `sqlite3` module usage
- **PostgreSQL**: `psycopg2`, `asyncpg` imports
- **MongoDB**: `pymongo` imports
- **ORM**: `sqlalchemy`, `django.db` imports

### HTTP/API Integrations
- **HTTP Clients**: `requests`, `urllib`, `httpx`, `aiohttp`
- **Web Frameworks**: `flask`, `django`, `fastapi`, `express`
- **API Testing**: Endpoint validation, authentication, error handling

### File I/O Operations
- File reading/writing operations
- Configuration file handling
- Data import/export functionality

### External Services
- **Cloud Services**: `boto3` (AWS), Google Cloud, Azure SDKs
- **Message Queues**: `celery`, `kafka-python`, `pika` (RabbitMQ)
- **Caching**: `redis-py`, `memcached`
- **Monitoring**: Logging, metrics, health checks

## Generated Test Examples

### Python (pytest)
```python
import pytest
import tempfile
import shutil
from unittest.mock import Mock, patch

class TestIntegration:
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_database_connection(self):
        # Test database connectivity
        assert True, "Database connection test"
    
    def test_api_endpoint_response(self):
        # Test API endpoint functionality
        assert True, "API endpoint test"
```

### JavaScript (Jest)
```javascript
describe('Integration Tests', () => {
    let tempDir;
    
    beforeEach(() => {
        tempDir = fs.mkdtempSync(path.join(__dirname, 'temp-'));
    });
    
    afterEach(() => {
        if (fs.existsSync(tempDir)) {
            fs.rmSync(tempDir, { recursive: true });
        }
    });
    
    test('API endpoint integration', () => {
        expect(true).toBe(true);
    });
});
```

## Configuration

### Environment Variables
- `OPENAI_API_KEY`: OpenAI API key for enhanced AI analysis (optional)
- `FLASK_ENV`: Flask environment (development/production)
- `FLASK_DEBUG`: Enable/disable debug mode

### Application Settings
- Default port: 5000
- CORS enabled for all origins
- SQLite database for user management (optional)

## Development

### Project Structure
```
integration_testing_app/
├── src/
│   ├── main.py                 # Flask application entry point
│   ├── models/                 # Database models
│   ├── routes/                 # API routes
│   │   ├── user.py            # User management routes
│   │   └── simple_integration_testing.py  # Main integration testing logic
│   └── static/                # Frontend files
│       └── index.html         # Web interface
├── venv/                      # Virtual environment
├── requirements.txt           # Python dependencies
└── README.md                 # This file
```

### Adding New Language Support

1. Update `analyze_repository_structure()` to detect new file extensions
2. Add language-specific analysis in `analyze_<language>_files()`
3. Implement test generation in `generate_<language>_tests()`
4. Update the web interface language selector

### Adding New Integration Patterns

1. Add pattern detection logic in `identify_integration_patterns()`
2. Define test scenarios for the new pattern
3. Update test generation templates

## Limitations

- Currently focuses on static analysis (no runtime analysis)
- Limited to publicly accessible GitHub repositories
- Generated tests are templates that may require customization
- AI-enhanced features require OpenAI API access

## Future Enhancements

- **Dynamic Analysis**: Runtime behavior analysis
- **Private Repository Support**: GitHub token authentication
- **CI/CD Integration**: GitHub Actions, Jenkins plugins
- **Test Execution**: Built-in test runner with reporting
- **Machine Learning**: Improved pattern recognition
- **Multi-language Support**: Additional programming languages
- **Performance Testing**: Load and stress test generation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation
- Review the API endpoints

## Acknowledgments

- Built with Flask, GitPython, and modern web technologies
- Inspired by the need for automated integration testing
- Designed for developers and QA engineers

