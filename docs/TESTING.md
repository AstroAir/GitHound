# GitHound Testing Guide

This document provides comprehensive information about GitHound's testing infrastructure, including how to run tests, understand test categories, and contribute new tests.

## Test Structure

GitHound uses a comprehensive testing approach with multiple test categories:

```
tests/
├── unit/                    # Unit tests for individual components
├── integration/             # End-to-end integration tests
├── performance/             # Performance benchmarks and limits
├── fixtures/                # Reusable test fixtures and utilities
│   ├── builders/           # Test data builders
│   ├── mocks/              # Mock objects and services
│   └── utilities/          # Test helper functions
└── conftest.py             # Shared pytest configuration
```

## Test Categories

### Unit Tests

Unit tests focus on individual functions and classes in isolation:

- **Location**: `tests/unit/` and main `tests/` directory
- **Purpose**: Test individual components without external dependencies
- **Coverage**: All core functionality, edge cases, error conditions
- **Speed**: Fast execution (< 1 second per test)

```bash
# Run all unit tests
pytest tests/test_*.py

# Run specific unit test files
pytest tests/test_git_handler.py
pytest tests/test_mcp_server.py
pytest tests/test_enhanced_api.py
```

### Integration Tests

Integration tests verify complete workflows and component interactions:

- **Location**: `tests/integration/`
- **Purpose**: Test end-to-end functionality and component integration
- **Coverage**: Complete user workflows, API interactions, MCP server operations
- **Speed**: Moderate execution (1-10 seconds per test)

```bash
# Run all integration tests
pytest tests/integration/

# Run specific integration tests
pytest tests/integration/test_end_to_end_workflows.py
pytest -m integration
```

### Performance Tests

Performance tests ensure operations complete within acceptable time and memory limits:

- **Location**: `tests/performance/`
- **Purpose**: Benchmark performance and detect regressions
- **Coverage**: Git operations, search functionality, API response times
- **Speed**: Variable (can be slow for large datasets)

```bash
# Run all performance tests
pytest tests/performance/

# Run performance tests with benchmarks
pytest tests/performance/ --benchmark-only

# Run performance tests with specific markers
pytest -m performance
pytest -m "performance and not slow"
```

## Running Tests

### Basic Test Execution

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with output capture disabled (see print statements)
pytest -s

# Run specific test file
pytest tests/test_git_handler.py

# Run specific test function
pytest tests/test_git_handler.py::test_get_repository

# Run specific test class
pytest tests/test_mcp_server.py::TestMCPRepositoryAnalysis
```

### Test Markers

GitHound uses pytest markers to categorize tests:

```bash
# Run tests by marker
pytest -m "not slow"          # Skip slow tests
pytest -m "performance"       # Only performance tests
pytest -m "integration"       # Only integration tests
pytest -m "benchmark"         # Only benchmark tests

# Combine markers
pytest -m "performance and not slow"
```

Available markers:
- `slow` - Tests that take longer than 5 seconds
- `performance` - Performance benchmark tests
- `integration` - Integration tests
- `benchmark` - Benchmark tests using pytest-benchmark

### Coverage Testing

```bash
# Run tests with coverage
pytest --cov=githound

# Generate HTML coverage report
pytest --cov=githound --cov-report=html

# Generate terminal coverage report
pytest --cov=githound --cov-report=term

# Fail if coverage below threshold
pytest --cov=githound --cov-fail-under=90

# Coverage for specific modules
pytest --cov=githound.git_handler --cov=githound.mcp_server
```

### Parallel Test Execution

```bash
# Install pytest-xdist for parallel execution
pip install pytest-xdist

# Run tests in parallel
pytest -n auto              # Auto-detect CPU count
pytest -n 4                 # Use 4 processes
```

## Test Configuration

### pytest.ini Configuration

```ini
[tool:pytest]
minversion = 6.0
addopts = 
    -ra
    --strict-markers
    --strict-config
    --cov=githound
    --cov-report=term-missing:skip-covered
    --cov-fail-under=85
testpaths = tests
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    performance: marks tests as performance tests
    integration: marks tests as integration tests
    benchmark: marks tests as benchmark tests
```

### Test Environment Variables

```bash
# Set test environment
export GITHOUND_TEST_MODE=true

# Configure test repository paths
export GITHOUND_TEST_REPO_PATH=/path/to/test/repo

# Configure test timeouts
export GITHOUND_TEST_TIMEOUT=30
```

## Writing Tests

### Test Structure Guidelines

1. **Arrange-Act-Assert Pattern**:
   ```python
   def test_function_behavior():
       # Arrange
       input_data = create_test_data()
       
       # Act
       result = function_under_test(input_data)
       
       # Assert
       assert result.status == "success"
       assert len(result.items) == 5
   ```

2. **Descriptive Test Names**:
   ```python
   def test_get_repository_metadata_returns_correct_commit_count():
       # Test implementation
       pass
   
   def test_analyze_commit_handles_invalid_hash_gracefully():
       # Test implementation
       pass
   ```

3. **Use Fixtures for Setup**:
   ```python
   @pytest.fixture
   def sample_repository():
       # Create test repository
       return create_test_repo()
   
   def test_repository_analysis(sample_repository):
       # Use fixture in test
       result = analyze_repository(sample_repository)
       assert result is not None
   ```

### Test Fixtures

GitHound provides comprehensive test fixtures:

```python
# Repository fixtures
def test_with_temp_repo(temp_repo):
    # temp_repo provides a temporary Git repository
    assert temp_repo.head.commit is not None

def test_with_complex_repo(complex_test_repo):
    # complex_test_repo provides a repository with multiple branches, commits, etc.
    assert len(list(complex_test_repo.branches)) > 1

# Data fixtures
def test_with_sample_commits(sample_commits):
    # sample_commits provides a list of test commit objects
    assert len(sample_commits) == 10

def test_with_mock_api_client(mock_api_client):
    # mock_api_client provides a mocked HTTP client
    response = mock_api_client.get("/api/health")
    assert response.status_code == 200
```

### Performance Test Guidelines

```python
import pytest
from tests.fixtures.performance import PerformanceMonitor

class TestGitOperationPerformance:
    
    @pytest.mark.performance
    def test_repository_loading_performance(self, temp_repo, performance_monitor):
        """Test repository loading completes within time limit."""
        performance_monitor.start_monitoring()
        
        # Perform operation
        repo = get_repository(temp_repo.working_dir)
        
        metrics = performance_monitor.stop_monitoring()
        
        # Assert performance requirements
        assert metrics['duration_seconds'] < 2.0
        assert metrics['memory_increase_mb'] < 50
    
    @pytest.mark.benchmark
    def test_commit_metadata_extraction_benchmark(self, temp_repo, benchmark):
        """Benchmark commit metadata extraction."""
        commit = temp_repo.head.commit
        
        result = benchmark(extract_commit_metadata, commit)
        assert result.hash == commit.hexsha
```

## Type Checking

GitHound maintains strict type checking with mypy:

```bash
# Run mypy type checking
mypy githound

# Run mypy with specific configuration
mypy githound --config-file mypy.ini

# Run mypy on tests
mypy tests --config-file mypy.ini

# Check specific modules
mypy githound.git_handler githound.mcp_server
```

### Type Checking Requirements

- All code must pass mypy with zero errors
- Use proper type annotations for all functions
- Import types from `typing` module when needed
- Use `# type: ignore` sparingly and with comments

## Continuous Integration

### GitHub Actions Workflow

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]
    
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -e ".[dev]"
    
    - name: Run tests
      run: |
        pytest --cov=githound --cov-report=xml
    
    - name: Run type checking
      run: |
        mypy githound
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## Test Data Management

### Test Repository Creation

```python
from tests.fixtures.builders import RepositoryBuilder

def create_test_repository():
    """Create a test repository with specific characteristics."""
    builder = RepositoryBuilder()
    
    repo, path = (builder
                  .initialize_repository()
                  .add_realistic_project_structure()
                  .commit_changes("Initial commit")
                  .create_branch("feature/test")
                  .add_commits_with_pattern(10, "test")
                  .create_tag("v1.0.0")
                  .build())
    
    return repo, path
```

### Mock Data Generation

```python
from tests.fixtures.builders import CommitBuilder

def test_commit_analysis():
    """Test commit analysis with mock data."""
    commit = (CommitBuilder()
              .with_hash("abc123")
              .with_author("Test User", "test@example.com")
              .with_message("Test commit message")
              .with_file_changes("test.py", insertions=10, deletions=5)
              .build())
    
    result = analyze_commit_metadata(commit)
    assert result.hash == "abc123"
```

## Troubleshooting Tests

### Common Issues

1. **Test Isolation**: Ensure tests don't depend on each other
2. **Temporary Files**: Clean up temporary files and repositories
3. **Time-Dependent Tests**: Use fixed dates or mock time
4. **External Dependencies**: Mock external services and APIs

### Debugging Tests

```bash
# Run single test with debugging
pytest tests/test_file.py::test_function -v -s --pdb

# Run with logging enabled
pytest --log-cli-level=DEBUG

# Run with custom markers
pytest -m "debug"
```

### Performance Issues

```bash
# Profile test execution
pytest --profile

# Run only fast tests
pytest -m "not slow"

# Use parallel execution
pytest -n auto
```

## Contributing Tests

When contributing new functionality:

1. **Write tests first** (TDD approach)
2. **Include all test categories**: unit, integration, performance
3. **Maintain coverage**: Ensure new code is covered
4. **Update documentation**: Update this guide for new test patterns
5. **Run full test suite**: Verify all tests pass before submitting

### Test Review Checklist

- [ ] Tests follow naming conventions
- [ ] All test categories included (unit, integration, performance)
- [ ] Type annotations present and correct
- [ ] Fixtures used appropriately
- [ ] Performance tests have reasonable thresholds
- [ ] Tests are isolated and don't depend on each other
- [ ] Cleanup code present for temporary resources
- [ ] Documentation updated if needed
