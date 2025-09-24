# GitHound Testing Guidelines

This document outlines the testing standards and patterns for the GitHound project to ensure comprehensive, maintainable, and high-quality test coverage.

## Testing Philosophy

### Core Principles

1. **Meaningful Coverage**: Focus on testing actual functionality, not just achieving line coverage
2. **Test Behavior, Not Implementation**: Tests should verify expected behavior rather than internal implementation details
3. **Comprehensive Scenarios**: Cover success paths, error conditions, edge cases, and boundary conditions
4. **Maintainable Tests**: Write clear, readable tests that are easy to maintain and understand
5. **Fast Feedback**: Prioritize fast unit tests while maintaining comprehensive integration tests

### Coverage Goals

- **Overall Target**: 90% line coverage minimum
- **Critical Modules**: 95% coverage for core modules (CLI, search engine, Git operations)
- **Branch Coverage**: 80% minimum for decision points
- **Quality over Quantity**: Prefer fewer, comprehensive tests over many superficial tests

## Test Structure and Organization

### Directory Structure

```
tests/
├── unit/                    # Fast, isolated unit tests
├── integration/             # Integration tests with external dependencies
├── e2e/                     # End-to-end workflow tests
├── performance/             # Performance and load tests
├── security/                # Security-focused tests
├── fixtures/                # Shared test fixtures and data
│   ├── cli_fixtures.py      # CLI-specific fixtures
│   ├── search_fixtures.py   # Search engine fixtures
│   └── builders/            # Test data builders
├── conftest.py              # Global fixtures and configuration
└── README.md                # Test suite documentation
```

### Test Categories and Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.unit           # Fast, isolated tests
@pytest.mark.integration    # Tests requiring external services
@pytest.mark.e2e           # End-to-end workflow tests
@pytest.mark.performance   # Performance tests
@pytest.mark.security      # Security tests
@pytest.mark.slow          # Tests that take significant time
@pytest.mark.cli           # CLI-specific tests
@pytest.mark.mcp           # MCP server tests
@pytest.mark.web           # Web API tests
```

## Test Quality Standards

### Test Naming Conventions

```python
# Good: Descriptive test names that explain what is being tested
def test_search_command_with_content_pattern_returns_matching_results():
    """Test that search command with content pattern returns expected results."""

def test_analyze_command_with_invalid_repo_path_shows_error():
    """Test that analyze command shows error for invalid repository path."""

# Bad: Vague or implementation-focused names
def test_search():
def test_function_call():
```

### Test Structure Pattern

Follow the Arrange-Act-Assert (AAA) pattern:

```python
def test_search_command_with_content_pattern():
    """Test search command with content pattern."""
    # Arrange
    runner = CliRunner()
    repo_path = create_test_repo()

    # Act
    result = runner.invoke(app, ["search", "--repo-path", str(repo_path), "--content", "function"])

    # Assert
    assert result.exit_code == 0
    assert "function" in result.stdout
    assert "No results found" not in result.stdout
```

### Assertion Guidelines

1. **Specific Assertions**: Use specific assertions rather than generic ones
2. **Multiple Assertions**: Use multiple assertions to verify different aspects
3. **Error Messages**: Include descriptive error messages in assertions

```python
# Good: Specific assertions with context
assert result.exit_code == 0, f"Command failed with output: {result.stdout}"
assert "3 results found" in result.stdout
assert "src/main.py" in result.stdout

# Bad: Generic assertions without context
assert result.exit_code == 0
assert "results" in result.stdout
```

### Mock Usage Guidelines

1. **Mock External Dependencies**: Always mock external services, file systems, and network calls
2. **Verify Interactions**: Use mocks to verify that functions are called with correct parameters
3. **Realistic Mock Data**: Provide realistic mock data that represents actual usage

```python
@patch("githound.git_handler.get_repository")
def test_analyze_command_calls_git_handler(mock_get_repo, cli_runner, temp_git_repo):
    """Test that analyze command properly calls git handler."""
    # Arrange
    mock_repo = Mock()
    mock_get_repo.return_value = mock_repo

    # Act
    result = cli_runner.invoke(app, ["analyze", str(temp_git_repo)])

    # Assert
    assert result.exit_code == 0
    mock_get_repo.assert_called_once_with(temp_git_repo)
```

## Module-Specific Testing Patterns

### CLI Testing

```python
def test_cli_command_with_valid_arguments(cli_runner, temp_git_repo):
    """Test CLI command with valid arguments."""
    result = cli_runner.invoke(app, ["command", "--arg", "value"])

    assert result.exit_code == 0
    assert "expected output" in result.stdout

def test_cli_command_with_invalid_arguments(cli_runner):
    """Test CLI command with invalid arguments."""
    result = cli_runner.invoke(app, ["command", "--invalid-arg"])

    assert result.exit_code != 0
    assert "error" in result.stderr.lower()
```

### Search Engine Testing

```python
async def test_search_orchestrator_with_complex_query(search_orchestrator, complex_git_repo):
    """Test search orchestrator with complex query."""
    query = SearchQuery(
        content_pattern="function",
        author_pattern="Alice",
        file_extensions=["py"]
    )

    results = []
    async for result in search_orchestrator.search(complex_git_repo, query):
        results.append(result)

    assert len(results) > 0
    assert all(result.file_path.endswith('.py') for result in results)
    assert all('function' in result.content.lower() for result in results)
```

### MCP Server Testing

```python
@pytest.mark.asyncio
async def test_mcp_tool_execution(mcp_client):
    """Test MCP tool execution."""
    result = await mcp_client.call_tool("search_repository", {
        "repo_path": "/test/repo",
        "query": "function"
    })

    assert result is not None
    assert "results" in result
    assert isinstance(result["results"], list)
```

### Web API Testing

```python
def test_api_endpoint_with_valid_request(api_client):
    """Test API endpoint with valid request."""
    response = api_client.post("/api/search", json={
        "repo_path": "/test/repo",
        "query": "function"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "results" in data
```

## Error Handling and Edge Cases

### Error Scenario Testing

Always test error conditions:

```python
def test_command_with_nonexistent_repository(cli_runner):
    """Test command behavior with nonexistent repository."""
    result = cli_runner.invoke(app, ["analyze", "/nonexistent/path"])

    assert result.exit_code != 0
    assert "not found" in result.stderr.lower() or "not found" in result.stdout.lower()

def test_command_with_permission_denied(cli_runner, mock_permission_error):
    """Test command behavior when permission is denied."""
    with patch("pathlib.Path.exists", side_effect=PermissionError("Permission denied")):
        result = cli_runner.invoke(app, ["analyze", "/restricted/path"])

        assert result.exit_code != 0
        assert "permission" in result.stderr.lower()
```

### Edge Case Testing

```python
def test_search_with_empty_repository(cli_runner, empty_git_repo):
    """Test search behavior with empty repository."""
    result = cli_runner.invoke(app, ["search", "--repo-path", str(empty_git_repo), "--content", "test"])

    assert result.exit_code == 0
    assert "No results found" in result.stdout

def test_search_with_very_large_pattern(cli_runner, temp_git_repo):
    """Test search behavior with very large search pattern."""
    large_pattern = "a" * 10000
    result = cli_runner.invoke(app, ["search", "--repo-path", str(temp_git_repo), "--content", large_pattern])

    # Should handle gracefully without crashing
    assert result.exit_code in [0, 1]  # Either success or expected failure
```

## Performance Testing Guidelines

### Performance Test Structure

```python
@pytest.mark.performance
def test_search_performance_with_large_repository(large_git_repo):
    """Test search performance with large repository."""
    import time

    start_time = time.time()

    # Perform operation
    result = perform_search(large_git_repo, "function")

    end_time = time.time()
    execution_time = end_time - start_time

    # Assert performance requirements
    assert execution_time < 5.0  # Should complete within 5 seconds
    assert len(result) > 0  # Should find results
```

## Continuous Integration Guidelines

### Test Execution Strategy

1. **Fast Tests**: Run unit tests on every commit
2. **Integration Tests**: Run on pull requests
3. **Performance Tests**: Run nightly or on release branches
4. **Full Suite**: Run before releases

### Coverage Requirements

- Pull requests must maintain or improve coverage
- No decrease in coverage below 85% allowed
- New code must have 90% coverage minimum

## Best Practices Summary

1. **Write tests first** when fixing bugs (TDD approach)
2. **Use descriptive test names** that explain the scenario
3. **Keep tests focused** - one concept per test
4. **Use fixtures** for common setup and teardown
5. **Mock external dependencies** to ensure test isolation
6. **Test both success and failure paths**
7. **Include edge cases and boundary conditions**
8. **Maintain test performance** - keep unit tests fast
9. **Review test coverage** regularly and address gaps
10. **Document complex test scenarios** with clear comments

## Common Anti-Patterns to Avoid

1. **Testing implementation details** instead of behavior
2. **Overly complex test setup** that's hard to understand
3. **Tests that depend on external state** or other tests
4. **Trivial tests** that don't add value (e.g., testing getters/setters)
5. **Ignoring error conditions** and edge cases
6. **Using real external services** in unit tests
7. **Hardcoded values** without explanation
8. **Tests that are too broad** and test multiple concepts

## Tools and Utilities

### Recommended Testing Tools

- **pytest**: Primary testing framework
- **pytest-cov**: Coverage reporting
- **pytest-asyncio**: Async test support
- **pytest-mock**: Mocking utilities
- **pytest-benchmark**: Performance testing
- **pytest-xdist**: Parallel test execution

### Custom Test Utilities

Use the provided test utilities in `tests/fixtures/` for common scenarios:
- `cli_fixtures.py`: CLI testing utilities
- `search_fixtures.py`: Search engine test data
- `builders/`: Test data builders for complex scenarios
