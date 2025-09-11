# GitHound Build Automation
# Cross-platform Makefile for development and CI/CD

# Variables
PYTHON := python
PIP := pip
PYTEST := pytest
PACKAGE_NAME := githound
SRC_DIR := githound
TEST_DIR := tests
DOCS_DIR := docs
BUILD_DIR := build
DIST_DIR := dist

# Virtual environment detection
ifdef VIRTUAL_ENV
    VENV_ACTIVE := true
else
    VENV_ACTIVE := false
endif

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Default target
.DEFAULT_GOAL := help

# Help target
.PHONY: help
help: ## Show this help message
	@echo "$(BLUE)GitHound Build System$(NC)"
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Environment setup
.PHONY: install
install: ## Install package and dependencies
	@echo "$(BLUE)Installing GitHound and dependencies...$(NC)"
	$(PIP) install -e .

.PHONY: install-dev
install-dev: ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	$(PIP) install -e ".[dev,test,docs,build]"

.PHONY: install-test
install-test: ## Install test dependencies only
	@echo "$(BLUE)Installing test dependencies...$(NC)"
	$(PIP) install -e ".[test]"

# Code quality
.PHONY: format
format: ## Format code with black and isort
	@echo "$(BLUE)Formatting code...$(NC)"
	black $(SRC_DIR) $(TEST_DIR)
	isort $(SRC_DIR) $(TEST_DIR)

.PHONY: lint
lint: ## Run linting with ruff
	@echo "$(BLUE)Running linter...$(NC)"
	ruff check $(SRC_DIR) $(TEST_DIR)

.PHONY: lint-fix
lint-fix: ## Run linting with automatic fixes
	@echo "$(BLUE)Running linter with fixes...$(NC)"
	ruff check --fix $(SRC_DIR) $(TEST_DIR)

.PHONY: type-check
type-check: ## Run type checking with mypy
	@echo "$(BLUE)Running type checker...$(NC)"
	mypy $(SRC_DIR)

.PHONY: quality
quality: format lint type-check ## Run all code quality checks

# Testing
.PHONY: test
test: ## Run unit tests
	@echo "$(BLUE)Running unit tests...$(NC)"
	$(PYTEST) $(TEST_DIR)/test_*.py -v

.PHONY: test-unit
test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	$(PYTEST) $(TEST_DIR)/test_*.py -m "not integration and not performance" -v

.PHONY: test-integration
test-integration: ## Run integration tests
	@echo "$(BLUE)Running integration tests...$(NC)"
	$(PYTEST) $(TEST_DIR)/integration/ -v

.PHONY: test-performance
test-performance: ## Run performance tests
	@echo "$(BLUE)Running performance tests...$(NC)"
	$(PYTEST) $(TEST_DIR)/performance/ -v

.PHONY: test-all
test-all: ## Run all tests including integration and performance
	@echo "$(BLUE)Running all tests...$(NC)"
	$(PYTEST) -v

.PHONY: test-fast
test-fast: ## Run tests in parallel (requires pytest-xdist)
	@echo "$(BLUE)Running tests in parallel...$(NC)"
	$(PYTEST) -n auto -v

.PHONY: test-cov
test-cov: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	$(PYTEST) --cov=$(SRC_DIR) --cov-report=html --cov-report=term-missing

.PHONY: benchmark
benchmark: ## Run benchmark tests
	@echo "$(BLUE)Running benchmarks...$(NC)"
	$(PYTEST) $(TEST_DIR)/performance/ --benchmark-only

# Web frontend testing targets
.PHONY: test-web-install
test-web-install: ## Install web frontend test dependencies
	@echo "$(BLUE)Installing web frontend test dependencies...$(NC)"
	pip install playwright pytest-playwright axe-playwright
	playwright install
	cd githound/web/tests && npm install

.PHONY: test-web
test-web: ## Run web frontend tests
	@echo "$(BLUE)Running web frontend tests...$(NC)"
	python githound/web/tests/run_tests.py all

.PHONY: test-web-auth
test-web-auth: ## Run web authentication tests
	@echo "$(BLUE)Running web authentication tests...$(NC)"
	python githound/web/tests/run_tests.py auth

.PHONY: test-web-search
test-web-search: ## Run web search functionality tests
	@echo "$(BLUE)Running web search tests...$(NC)"
	python githound/web/tests/run_tests.py search

.PHONY: test-web-api
test-web-api: ## Run web API integration tests
	@echo "$(BLUE)Running web API tests...$(NC)"
	python githound/web/tests/run_tests.py api

.PHONY: test-web-ui
test-web-ui: ## Run web UI/UX tests
	@echo "$(BLUE)Running web UI/UX tests...$(NC)"
	python githound/web/tests/run_tests.py ui

.PHONY: test-web-performance
test-web-performance: ## Run web performance tests
	@echo "$(BLUE)Running web performance tests...$(NC)"
	python githound/web/tests/run_tests.py performance

.PHONY: test-web-accessibility
test-web-accessibility: ## Run web accessibility tests
	@echo "$(BLUE)Running web accessibility tests...$(NC)"
	python githound/web/tests/run_tests.py accessibility

.PHONY: test-web-smoke
test-web-smoke: ## Run web smoke tests
	@echo "$(BLUE)Running web smoke tests...$(NC)"
	python githound/web/tests/run_tests.py smoke

.PHONY: test-web-headed
test-web-headed: ## Run web tests in headed mode (visible browser)
	@echo "$(BLUE)Running web tests in headed mode...$(NC)"
	python githound/web/tests/run_tests.py all --headed

.PHONY: test-web-firefox
test-web-firefox: ## Run web tests in Firefox
	@echo "$(BLUE)Running web tests in Firefox...$(NC)"
	python githound/web/tests/run_tests.py all --browser firefox

.PHONY: test-web-webkit
test-web-webkit: ## Run web tests in WebKit/Safari
	@echo "$(BLUE)Running web tests in WebKit...$(NC)"
	python githound/web/tests/run_tests.py all --browser webkit

.PHONY: test-web-report
test-web-report: ## Generate web test reports
	@echo "$(BLUE)Generating web test reports...$(NC)"
	python githound/web/tests/run_tests.py report

# Build and distribution
.PHONY: clean
clean: ## Clean build artifacts
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	rm -rf $(BUILD_DIR)/ $(DIST_DIR)/ *.egg-info/
	rm -rf .pytest_cache/ .coverage htmlcov/ .mypy_cache/ .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

.PHONY: build
build: clean ## Build package
	@echo "$(BLUE)Building package...$(NC)"
	$(PYTHON) -m build

.PHONY: build-wheel
build-wheel: clean ## Build wheel only
	@echo "$(BLUE)Building wheel...$(NC)"
	$(PYTHON) -m build --wheel

.PHONY: build-sdist
build-sdist: clean ## Build source distribution only
	@echo "$(BLUE)Building source distribution...$(NC)"
	$(PYTHON) -m build --sdist

# Documentation
.PHONY: docs
docs: ## Build documentation
	@echo "$(BLUE)Building documentation...$(NC)"
	cd $(DOCS_DIR) && mkdocs build

.PHONY: docs-serve
docs-serve: ## Serve documentation locally
	@echo "$(BLUE)Serving documentation at http://localhost:8000$(NC)"
	cd $(DOCS_DIR) && mkdocs serve

.PHONY: docs-clean
docs-clean: ## Clean documentation build
	@echo "$(BLUE)Cleaning documentation...$(NC)"
	cd $(DOCS_DIR) && mkdocs build --clean

# Development workflow
.PHONY: dev-setup
dev-setup: install-dev ## Complete development environment setup
	@echo "$(BLUE)Setting up development environment...$(NC)"
	pre-commit install

.PHONY: check
check: quality test-unit ## Run quality checks and unit tests
	@echo "$(GREEN)All checks passed!$(NC)"

.PHONY: ci
ci: quality test-all build ## Full CI pipeline
	@echo "$(GREEN)CI pipeline completed successfully!$(NC)"

# Utility targets
.PHONY: deps-update
deps-update: ## Update dependencies
	@echo "$(BLUE)Updating dependencies...$(NC)"
	$(PIP) install --upgrade pip
	$(PIP) install --upgrade -e ".[dev,test,docs,build]"

.PHONY: security-check
security-check: ## Run security checks
	@echo "$(BLUE)Running security checks...$(NC)"
	$(PIP) install safety bandit
	safety check
	bandit -r $(SRC_DIR)

.PHONY: profile
profile: ## Profile test execution
	@echo "$(BLUE)Profiling test execution...$(NC)"
	$(PYTEST) --profile --profile-svg

.PHONY: version
version: ## Show version information
	@echo "$(BLUE)Version Information:$(NC)"
	@$(PYTHON) --version
	@$(PIP) --version
	@$(PYTEST) --version

# Environment info
.PHONY: env-info
env-info: ## Show environment information
	@echo "$(BLUE)Environment Information:$(NC)"
	@echo "Virtual Environment Active: $(VENV_ACTIVE)"
	@echo "Python: $(shell $(PYTHON) --version)"
	@echo "Pip: $(shell $(PIP) --version)"
	@echo "Working Directory: $(shell pwd)"
	@if [ "$(VENV_ACTIVE)" = "true" ]; then \
		echo "Virtual Environment: $(VIRTUAL_ENV)"; \
	fi
