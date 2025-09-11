# GitHound API Test Suite

This directory contains a comprehensive test suite for the GitHound API, covering unit tests, integration tests, end-to-end tests, performance tests, and security tests.

## Test Structure

```
tests/
├── conftest.py                 # Shared fixtures and test configuration
├── unit/                       # Unit tests for individual components
│   ├── test_git_operations.py  # Git operations manager tests
│   ├── test_auth.py            # Authentication system tests
│   └── test_webhooks.py        # Webhook system tests
├── integration/                # Integration tests for API endpoints
│   ├── test_repository_api.py  # Repository management API tests
│   ├── test_analysis_api.py    # Analysis API tests
│   └── test_search_api.py      # Search API tests
├── e2e/                        # End-to-end workflow tests
│   └── test_complete_workflows.py
├── performance/                # Performance and load tests
│   └── test_load_testing.py
├── security/                   # Security tests
│   └── test_security.py
└── README.md                   # This file
```

## Test Categories

### Unit Tests (`tests/unit/`)

- **Purpose**: Test individual components in isolation
- **Speed**: Fast (< 1 second per test)
- **Dependencies**: Minimal, mostly mocked
- **Coverage**: Core business logic, utilities, data models

**Key Test Files:**

- `test_git_operations.py`: Tests for GitOperationsManager class
- `test_auth.py`: Authentication and authorization logic
- `test_webhooks.py`: Webhook event system

### Integration Tests (`tests/integration/`)

- **Purpose**: Test API endpoints with real HTTP requests
- **Speed**: Medium (1-5 seconds per test)
- **Dependencies**: FastAPI test client, mocked external services
- **Coverage**: API endpoints, request/response handling, validation

**Key Test Files:**

- `test_repository_api.py`: Repository management endpoints
- `test_analysis_api.py`: Code analysis and blame endpoints
- `test_search_api.py`: Search functionality endpoints

### End-to-End Tests (`tests/e2e/`)

- **Purpose**: Test complete user workflows
- **Speed**: Slow (5-30 seconds per test)
- **Dependencies**: Full application stack
- **Coverage**: User journeys, cross-component interactions

### Performance Tests (`tests/performance/`)

- **Purpose**: Test system performance under load
- **Speed**: Very slow (30+ seconds per test)
- **Dependencies**: Load testing tools, potentially external services
- **Coverage**: Rate limiting, concurrent operations, large datasets

### Security Tests (`tests/security/`)

- **Purpose**: Test security measures and vulnerability protection
- **Speed**: Medium (1-10 seconds per test)
- **Dependencies**: Security testing tools
- **Coverage**: Authentication bypass, authorization, input validation, XSS, injection attacks

## Test Markers

Tests are categorized using pytest markers:

- `@pytest.mark.unit`: Unit tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.e2e`: End-to-end tests
- `@pytest.mark.performance`: Performance tests
- `@pytest.mark.security`: Security tests
- `@pytest.mark.slow`: Tests that take longer to run
- `@pytest.mark.redis`: Tests requiring Redis connection
- `@pytest.mark.websocket`: WebSocket functionality tests

## Running Tests

### Prerequisites

Install test dependencies:

```bash
pip install pytest pytest-asyncio pytest-cov pytest-timeout pytest-xdist httpx fastapi[all] redis aiohttp
```

### Quick Start

```bash
# Run all fast tests (excludes slow and performance tests)
python run_tests.py fast

# Run unit tests only
python run_tests.py unit

# Run integration tests
python run_tests.py integration

# Run all tests with coverage
python run_tests.py all
```

### Using the Test Runner

The `run_tests.py` script provides various execution modes:

```bash
# Unit tests with coverage
python run_tests.py unit

# Integration tests
python run_tests.py integration

# End-to-end tests
python run_tests.py e2e

# Performance tests
python run_tests.py performance

# Security tests
python run_tests.py security

# Fast tests (unit + quick integration)
python run_tests.py fast

# All tests
python run_tests.py all

# Generate coverage report
python run_tests.py coverage

# Run specific test file
python run_tests.py specific --test-path tests/unit/test_auth.py

# Run tests by marker
python run_tests.py marker --marker security

# Run with options
python run_tests.py all --parallel --no-coverage --quiet
```

## Key Testing Patterns

### 1. In-Memory Testing (FastMCP Best Practice)

```python
@pytest.mark.asyncio
async def test_in_memory_pattern(mcp_server: FastMCP):
    """Test using FastMCP in-memory pattern."""
    # Pass server instance directly to client
    async with Client(mcp_server) as client:
        await client.ping()
        tools = await client.list_tools()
        assert len(tools) > 0
```

### 2. Mocking External Dependencies

```python
@pytest.mark.asyncio
async def test_with_mocks(mcp_server: FastMCP, mock_external_dependencies):
    """Test with mocked dependencies for deterministic results."""
    # Configure mocks
    mock_repo = MagicMock()
    mock_external_dependencies['get_repository'].return_value = mock_repo

    async with Client(mcp_server) as client:
        result = await client.call_tool("validate_repository", {"repo_path": "/mock"})
        assert result is not None
```

### 3. Error Handling Testing

```python
@pytest.mark.asyncio
async def test_error_scenarios(mcp_client: Client):
    """Test error handling patterns."""
    with pytest.raises((ToolError, Exception)):
        await mcp_client.call_tool("invalid_tool", {})
```

## Test Fixtures

### Core Fixtures

- `mcp_server`: Fresh server instance for in-memory testing
- `mcp_client`: Connected client using in-memory pattern
- `temp_repo`: Temporary Git repository with test data
- `mock_external_dependencies`: Mocked external services

### Data Fixtures

- `mock_search_data`: Sample search results
- `auth_headers`: Authentication headers for testing
- `performance_test_data`: Large datasets for performance testing
- `error_scenarios`: Various error conditions

## Running Tests

### Using Test Runner Script

```bash
# List available test suites
python scripts/run_mcp_tests.py --list

# Run specific suite
python scripts/run_mcp_tests.py unit

# Run with coverage
python scripts/run_mcp_tests.py --coverage

# Run with verbose output
python scripts/run_mcp_tests.py unit --verbose

# Run in parallel
python scripts/run_mcp_tests.py unit --parallel 4
```

### Using Pytest Directly

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_mcp_fastmcp_patterns.py

# Run with markers
pytest -m "unit and not slow"

# Run with coverage
pytest --cov=githound --cov-report=html

# Run specific test class
pytest tests/test_mcp_fastmcp_patterns.py::TestFastMCPInMemoryTesting
```

## Test Markers

Tests are organized using pytest markers:

- `unit`: Fast unit tests
- `integration`: Integration tests requiring external services
- `performance`: Performance and scalability tests
- `slow`: Tests that take significant time
- `auth`: Authentication and authorization tests
- `http`: HTTP transport tests
- `fastmcp`: Tests following FastMCP patterns

## Configuration

### pytest.ini

Main pytest configuration with:

- Test discovery settings
- Marker definitions
- Coverage configuration
- Async testing setup

### conftest.py

Comprehensive fixtures including:

- Server and client instances
- Test repositories
- Mock data and dependencies
- Performance testing utilities

## Best Practices

### 1. Default to In-Memory Testing

Use the FastMCP in-memory pattern for most tests:

```python
async with Client(mcp_server) as client:
    # Test operations
```

### 2. Mock External Dependencies

Keep tests deterministic by mocking external services:

```python
with patch('githound.git_handler.get_repository') as mock_repo:
    # Test with mocked dependencies
```

### 3. Test Error Cases

Always test error scenarios and edge cases:

```python
with pytest.raises(ToolError):
    await client.call_tool("tool", {"invalid": "args"})
```

### 4. Use Appropriate Markers

Mark tests appropriately for selective execution:

```python
@pytest.mark.performance
@pytest.mark.slow
async def test_large_repository():
    # Performance test
```

## Continuous Integration

For CI/CD pipelines:

```bash
# Fast tests for PR validation
python scripts/run_mcp_tests.py unit

# Full test suite for main branch
python scripts/run_mcp_tests.py all --coverage

# Performance regression testing
python scripts/run_mcp_tests.py performance
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure PYTHONPATH includes project root
2. **Async Test Failures**: Check pytest-asyncio configuration
3. **Mock Issues**: Verify mock patches target correct modules
4. **Performance Test Timeouts**: Adjust timeout settings in pytest.ini

### Debug Mode

Run tests with debug logging:

```bash
pytest --log-cli-level=DEBUG tests/test_mcp_fastmcp_patterns.py
```

## Contributing

When adding new tests:

1. Follow FastMCP testing patterns
2. Use appropriate fixtures from conftest.py
3. Add proper markers for test categorization
4. Include both success and error scenarios
5. Mock external dependencies for deterministic results

## References

- [FastMCP Testing Documentation](https://gofastmcp.com/deployment/testing)
- [FastMCP Best Practices](https://gofastmcp.com/patterns/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
