.PHONY: install test lint format clean

# Development setup
install:
	python -m pip install -r requirements.txt

# Testing
test:
	python -m pytest tests/ --cov=src --cov-report=html

# Code quality
lint:
	flake8 src/
	mypy src/
	black src/ --check
	isort src/ --check-only

format:
	black src/
	isort src/

# Cleaning
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "build" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +

# Run all checks
check: lint test
