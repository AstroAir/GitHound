#!/bin/bash
# GitHound Build Script for Unix-like systems
# Comprehensive build automation for Linux and macOS

set -e  # Exit on any error

# Configuration
PACKAGE_NAME="githound"
SRC_DIR="githound"
TEST_DIR="tests"
DOCS_DIR="docs"
BUILD_DIR="build"
DIST_DIR="dist"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}$1${NC}"
}

log_success() {
    echo -e "${GREEN}$1${NC}"
}

log_warning() {
    echo -e "${YELLOW}$1${NC}"
}

log_error() {
    echo -e "${RED}$1${NC}"
}

show_help() {
    log_info "GitHound Build System"
    echo "Usage: ./build.sh <command> [options]"
    echo ""
    echo "Available commands:"
    echo "  help              Show this help message"
    echo "  install           Install package and dependencies"
    echo "  install-dev       Install development dependencies"
    echo "  install-test      Install test dependencies only"
    echo "  format            Format code with black and isort"
    echo "  lint              Run linting with ruff"
    echo "  lint-fix          Run linting with automatic fixes"
    echo "  type-check        Run type checking with mypy"
    echo "  quality           Run all code quality checks"
    echo "  test              Run unit tests"
    echo "  test-unit         Run unit tests only"
    echo "  test-integration  Run integration tests"
    echo "  test-performance  Run performance tests"
    echo "  test-all          Run all tests"
    echo "  test-fast         Run tests in parallel"
    echo "  test-cov          Run tests with coverage"
    echo "  benchmark         Run benchmark tests"
    echo "  clean             Clean build artifacts"
    echo "  build             Build package"
    echo "  build-wheel       Build wheel only"
    echo "  build-sdist       Build source distribution only"
    echo "  docs              Build documentation"
    echo "  docs-serve        Serve documentation locally"
    echo "  dev-setup         Complete development setup"
    echo "  check             Run quality checks and unit tests"
    echo "  ci                Full CI pipeline"
    echo "  deps-update       Update dependencies"
    echo "  security-check    Run security checks"
    echo "  version           Show version information"
    echo "  env-info          Show environment information"
}

check_virtual_env() {
    if [[ -z "$VIRTUAL_ENV" ]]; then
        log_warning "No virtual environment detected. Consider activating one."
        return 1
    else
        log_info "Using virtual environment: $VIRTUAL_ENV"
        return 0
    fi
}

run_command() {
    local cmd="$1"
    local description="$2"
    
    if [[ -n "$description" ]]; then
        log_info "$description"
    fi
    
    if [[ "$VERBOSE" == "1" ]]; then
        echo -e "${CYAN}Executing: $cmd${NC}"
    fi
    
    eval "$cmd"
}

install_package() {
    run_command "pip install -e ." "Installing GitHound and dependencies..."
}

install_dev_dependencies() {
    run_command "pip install -e \".[dev,test,docs,build]\"" "Installing development dependencies..."
}

install_test_dependencies() {
    run_command "pip install -e \".[test]\"" "Installing test dependencies..."
}

format_code() {
    log_info "Formatting code..."
    run_command "black $SRC_DIR $TEST_DIR"
    run_command "isort $SRC_DIR $TEST_DIR"
}

run_linting() {
    run_command "ruff check $SRC_DIR $TEST_DIR" "Running linter..."
}

run_linting_with_fix() {
    run_command "ruff check --fix $SRC_DIR $TEST_DIR" "Running linter with fixes..."
}

run_type_check() {
    run_command "mypy $SRC_DIR" "Running type checker..."
}

run_quality_checks() {
    format_code
    run_linting
    run_type_check
}

run_tests() {
    run_command "pytest $TEST_DIR/test_*.py -v" "Running unit tests..."
}

run_unit_tests() {
    run_command "pytest $TEST_DIR/test_*.py -m \"not integration and not performance\" -v" "Running unit tests..."
}

run_integration_tests() {
    run_command "pytest $TEST_DIR/integration/ -v" "Running integration tests..."
}

run_performance_tests() {
    run_command "pytest $TEST_DIR/performance/ -v" "Running performance tests..."
}

run_all_tests() {
    run_command "pytest -v" "Running all tests..."
}

run_fast_tests() {
    run_command "pytest -n auto -v" "Running tests in parallel..."
}

run_tests_with_coverage() {
    run_command "pytest --cov=$SRC_DIR --cov-report=html --cov-report=term-missing" "Running tests with coverage..."
}

run_benchmarks() {
    run_command "pytest $TEST_DIR/performance/ --benchmark-only" "Running benchmarks..."
}

clean_build_artifacts() {
    log_info "Cleaning build artifacts..."
    
    # Remove build directories
    for dir in "$BUILD_DIR" "$DIST_DIR" "*.egg-info" ".pytest_cache" "htmlcov" ".mypy_cache" ".ruff_cache"; do
        if [[ -d "$dir" ]] || [[ -f "$dir" ]]; then
            rm -rf "$dir"
            if [[ "$VERBOSE" == "1" ]]; then
                echo -e "${CYAN}Removed: $dir${NC}"
            fi
        fi
    done
    
    # Remove __pycache__ directories
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    
    # Remove .pyc files
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    
    # Remove .coverage file
    [[ -f ".coverage" ]] && rm ".coverage"
}

build_package() {
    clean_build_artifacts
    run_command "python -m build" "Building package..."
}

build_wheel() {
    clean_build_artifacts
    run_command "python -m build --wheel" "Building wheel..."
}

build_source_dist() {
    clean_build_artifacts
    run_command "python -m build --sdist" "Building source distribution..."
}

build_documentation() {
    run_command "cd $DOCS_DIR && mkdocs build" "Building documentation..."
}

serve_documentation() {
    log_info "Serving documentation at http://localhost:8000"
    run_command "cd $DOCS_DIR && mkdocs serve"
}

setup_development() {
    install_dev_dependencies
    run_command "pre-commit install" "Installing pre-commit hooks..."
}

run_check() {
    run_quality_checks
    run_unit_tests
    log_success "All checks passed!"
}

run_ci() {
    run_quality_checks
    run_all_tests
    build_package
    log_success "CI pipeline completed successfully!"
}

update_dependencies() {
    log_info "Updating dependencies..."
    run_command "pip install --upgrade pip"
    run_command "pip install --upgrade -e \".[dev,test,docs,build]\""
}

run_security_check() {
    log_info "Running security checks..."
    run_command "pip install safety bandit"
    run_command "safety check"
    run_command "bandit -r $SRC_DIR"
}

show_version() {
    log_info "Version Information:"
    python --version
    pip --version
    pytest --version
}

show_env_info() {
    log_info "Environment Information:"
    echo "Virtual Environment Active: $([[ -n "$VIRTUAL_ENV" ]] && echo "true" || echo "false")"
    echo "Python: $(python --version)"
    echo "Pip: $(pip --version)"
    echo "Working Directory: $(pwd)"
    [[ -n "$VIRTUAL_ENV" ]] && echo "Virtual Environment: $VIRTUAL_ENV"
}

# Parse command line arguments
VERBOSE=0
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE=1
            shift
            ;;
        *)
            COMMAND="$1"
            shift
            ;;
    esac
done

# Default command
COMMAND="${COMMAND:-help}"

# Main command dispatcher
case "$COMMAND" in
    help)
        show_help
        ;;
    install)
        install_package
        ;;
    install-dev)
        install_dev_dependencies
        ;;
    install-test)
        install_test_dependencies
        ;;
    format)
        format_code
        ;;
    lint)
        run_linting
        ;;
    lint-fix)
        run_linting_with_fix
        ;;
    type-check)
        run_type_check
        ;;
    quality)
        run_quality_checks
        ;;
    test)
        run_tests
        ;;
    test-unit)
        run_unit_tests
        ;;
    test-integration)
        run_integration_tests
        ;;
    test-performance)
        run_performance_tests
        ;;
    test-all)
        run_all_tests
        ;;
    test-fast)
        run_fast_tests
        ;;
    test-cov)
        run_tests_with_coverage
        ;;
    benchmark)
        run_benchmarks
        ;;
    clean)
        clean_build_artifacts
        ;;
    build)
        build_package
        ;;
    build-wheel)
        build_wheel
        ;;
    build-sdist)
        build_source_dist
        ;;
    docs)
        build_documentation
        ;;
    docs-serve)
        serve_documentation
        ;;
    dev-setup)
        setup_development
        ;;
    check)
        run_check
        ;;
    ci)
        run_ci
        ;;
    deps-update)
        update_dependencies
        ;;
    security-check)
        run_security_check
        ;;
    version)
        show_version
        ;;
    env-info)
        show_env_info
        ;;
    *)
        log_error "Unknown command: $COMMAND"
        log_warning "Use './build.sh help' to see available commands"
        exit 1
        ;;
esac
