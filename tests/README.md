# GitHound MCP Server Testing

Comprehensive testing suite for GitHound MCP Server following [FastMCP testing best practices](https://gofastmcp.com/deployment/testing).

## Overview

This testing suite implements the latest FastMCP testing patterns including:

- **In-Memory Testing**: Direct server instance passing for zero-overhead testing
- **Comprehensive Fixtures**: Reusable server configurations and test data
- **Mock External Dependencies**: Deterministic testing with mocked Git operations
- **Authentication Testing**: Bearer tokens and OAuth flow testing
- **Performance Testing**: Scalability and resource utilization testing
- **Integration Testing**: HTTP transport and deployed server testing

## Test Structure

```
tests/
├── conftest.py                    # Test fixtures and configuration
├── test_mcp_server.py            # Enhanced main server tests
├── test_mcp_fastmcp_patterns.py  # FastMCP pattern tests
├── test_mcp_authentication.py    # Authentication testing
├── test_mcp_integration.py       # HTTP transport integration tests
├── test_mcp_performance.py       # Performance and scalability tests
└── README.md                     # This file
```

## Quick Start

### Install Test Dependencies

```bash
pip install pytest pytest-asyncio pytest-cov psutil
```

### Run Basic Tests

```bash
# Run unit tests (fast, in-memory)
python scripts/run_mcp_tests.py unit

# Run FastMCP pattern tests
python scripts/run_mcp_tests.py fastmcp

# Run quick check
python scripts/run_mcp_tests.py --quick

# Run all tests
python scripts/run_mcp_tests.py all
```

## Test Categories

### Unit Tests (`unit`)
Fast, isolated tests using in-memory testing patterns:
- Server creation and configuration
- Tool execution with mocked dependencies
- Resource access patterns
- Error handling scenarios

```bash
python scripts/run_mcp_tests.py unit
```

### FastMCP Pattern Tests (`fastmcp`)
Tests specifically following FastMCP documentation patterns:
- In-memory server-client connections
- Deterministic testing with mocks
- Concurrent operation patterns
- Best practice implementations

```bash
python scripts/run_mcp_tests.py fastmcp
```

### Integration Tests (`integration`)
Tests requiring external services or HTTP transport:
- HTTP server connectivity
- Real network behavior
- Deployed server scenarios
- End-to-end workflows

```bash
python scripts/run_mcp_tests.py integration
```

### Performance Tests (`performance`)
Scalability and resource utilization tests:
- Large repository handling
- Concurrent client connections
- Memory usage patterns
- Response time benchmarks

```bash
python scripts/run_mcp_tests.py performance
```

### Authentication Tests (`auth`)
Security and authentication scenarios:
- Bearer token authentication
- OAuth flow simulation
- Authorization patterns
- Security headers validation

```bash
python scripts/run_mcp_tests.py auth
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
