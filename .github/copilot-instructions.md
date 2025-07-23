# VS Code Copilot Instructions

## Code Generation
- Use Python 3.x syntax with type hints for all function parameters and returns
- Follow PEP 8 style guidelines strictly
- Use f-strings for string formatting, not %-formatting or .format()
- Implement Google style docstrings for all functions and classes
- Prefix private variables with underscore (_)
- Use dataclasses, named tuples, or Pydantic models for data structures
- Implement async patterns where I/O operations are involved

## Testing
- Generate pytest-based test cases with fixtures
- Use unittest.mock or pytest-mock for mocking/stubbing
- Include type hints in test functions
- Structure tests with Arrange-Act-Assert pattern
- Generate parallel test execution compatible code where possible

## Error Handling
- Use explicit exception types, not bare except clauses
- Include proper error messages in exceptions
- Implement context managers for resource cleanup

## Dependencies
- Use httpx for async HTTP operations, requests for sync
- Use SQLAlchemy for database operations
- Use networkx for dependency graph analysis
- Prefer standard library solutions when available

## Security
- Never generate hardcoded credentials or API keys
- Generate code that loads credentials from environment variables
- Include input validation for all external data

## Project Structure
- Separate test utilities from core implementations
- Place configuration in dedicated config files
- Use relative imports within packages
- Generate Docker-compatible code when relevant

## Documentation
- Include brief usage examples in docstrings
- Document any non-obvious algorithmic choices
- Add type hints in docstrings for complex return types
