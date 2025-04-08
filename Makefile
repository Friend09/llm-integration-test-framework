.PHONY: setup lint test clean analyze update-deps

# Default target
all: setup lint test

# Setup the project
setup:
	@echo "Setting up virtual environment..."
	@if [ ! -d ".venv" ]; then \
		python3 -m venv .venv; \
		echo "Installing dependencies..."; \
		./.venv/bin/pip install -r requirements.txt; \
		echo "Setup complete! Activate the virtual environment with: source .venv/bin/activate"; \
	else \
		echo "Virtual environment already exists. Use 'make update-deps' to update dependencies."; \
	fi

# Update dependencies only
update-deps:
	@echo "Updating dependencies..."
	./.venv/bin/pip install -r requirements.txt
	@echo "Dependencies updated!"

# Run linting checks
lint:
	@echo "Running linting checks..."
	./.venv/bin/black src tests --check
	./.venv/bin/isort src tests --check
	./.venv/bin/flake8 src tests

# Format code
format:
	@echo "Formatting code..."
	./.venv/bin/black src tests
	./.venv/bin/isort src tests

# Run tests
test:
	@echo "Running tests..."
	./.venv/bin/pytest tests/ -v --cov=src --cov-report=term-missing

# Clean temporary files
clean:
	@echo "Cleaning temporary files..."
	rm -rf reports/*
	rm -rf temp_repos/*
	rm -rf __pycache__
	rm -rf .coverage
	rm -rf .pytest_cache
	rm -rf **/__pycache__

# Run the framework in test mode (no LLM calls)
test-run:
	@echo "Running in test mode (no LLM calls)..."
	./.venv/bin/python -m src.main analyze https://github.com/psf/requests --test --verbose

# Run with actual LLM analysis
run-llm:
	@echo "Running with LLM analysis..."
	@if [ -f .env ]; then \
		export $$(grep -v '^#' .env | sed 's/\#.*//g' | xargs) && \
		./.venv/bin/python -m src.main analyze https://github.com/psf/requests --verbose; \
	else \
		echo "Error: .env file not found"; \
		exit 1; \
	fi

# Run analysis on a repo (replace with actual repo)
analyze:
	@echo "Running analysis..."
	python -m src.main analyze https://github.com/psf/requests

# Create Docker container
docker-build:
	@echo "Building Docker container..."
	docker build -t llm-integration-test-framework .

# Run Docker container
docker-run:
	@echo "Running Docker container..."
	docker run -it --env-file .env llm-integration-test-framework analyze https://github.com/psf/requests
