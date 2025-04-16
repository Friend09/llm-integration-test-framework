.PHONY: setup run clean test lint install reports

# Default Python command (use python3 if available)
PYTHON := python3
UV := uv

# Directories
REPORTS_DIR := reports
TEMP_DIR := temp_repos

# Environment variables
ENV_FILE := .env

setup:
	$(UV) pip install -e .
	@echo "Creating .env file if it doesn't exist"
	@if [ ! -f $(ENV_FILE) ]; then cp .env.example $(ENV_FILE); fi
	@echo "Creating reports directory if it doesn't exist"
	@mkdir -p $(REPORTS_DIR)

install:
	$(UV) pip install -e .

run:
	$(PYTHON) test_end_to_end.py

run-with-repo:
	@echo "Running test on specified repository"
	$(PYTHON) -c "import sys; from test_end_to_end import test_framework; import asyncio; asyncio.run(test_framework(sys.argv[1]))" $(REPO_URL)

test:
	$(PYTHON) -m pytest tests/

lint:
	$(PYTHON) -m flake8 src/ tests/
	$(PYTHON) -m mypy src/ tests/

clean:
	@echo "Cleaning up temporary files and directories"
	@rm -rf $(TEMP_DIR)/* 2>/dev/null || true
	@echo "Removed temporary repos"

clean-reports:
	@echo "Cleaning up reports"
	@rm -rf $(REPORTS_DIR)/* 2>/dev/null || true
	@echo "Removed reports"

clean-all: clean clean-reports
	@echo "All temporary files and reports removed"

list-reports:
	@echo "Available reports:"
	@ls -la $(REPORTS_DIR)

# Generate HTML report for specific repository
report:
	@mkdir -p $(REPORTS_DIR)
	@if [ -z "$(REPO_URL)" ]; then \
		echo "Error: REPO_URL is required. Use 'make report REPO_URL=https://github.com/username/repo.git'"; \
		exit 1; \
	fi
	$(PYTHON) -c "import sys; from test_end_to_end import test_framework; import asyncio; asyncio.run(test_framework(sys.argv[1]))" $(REPO_URL)
	@echo "Report generated in $(REPORTS_DIR) directory"

help:
	@echo "Available commands:"
	@echo "  make setup         - Install dependencies and set up environment"
	@echo "  make install       - Install project in development mode"
	@echo "  make run           - Run default end-to-end test"
	@echo "  make run-with-repo REPO_URL=<url> - Run test on specified repository"
	@echo "  make test          - Run all tests"
	@echo "  make lint          - Run linting tools"
	@echo "  make clean         - Remove temporary repositories"
	@echo "  make clean-reports - Remove generated reports"
	@echo "  make clean-all     - Remove all temporary files and reports"
	@echo "  make list-reports  - List available reports"
	@echo "  make report REPO_URL=<url> - Generate report for specified repository"
	@echo "  make help          - Show this help message"
