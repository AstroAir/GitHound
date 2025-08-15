# Integration Tests

This directory contains comprehensive integration tests for GitHound's end-to-end functionality.

## Test Categories

### End-to-End Workflows
- Complete repository analysis workflows
- MCP server integration with real clients
- REST API integration testing
- Multi-component interaction testing
- Data flow validation

### System Integration
- File system integration
- Git repository integration
- Database integration (if applicable)
- External service integration
- Configuration management

### Cross-Component Testing
- MCP server + Git operations
- REST API + Search engine
- Export system + Multiple formats
- Error handling across components
- Performance under realistic loads

## Test Structure

### Integration Test Organization
```
tests/integration/
├── test_end_to_end_workflows.py     # Complete workflow testing
├── test_mcp_integration.py          # MCP server integration
├── test_api_integration.py          # REST API integration
├── test_export_integration.py       # Export system integration
├── test_search_integration.py       # Search engine integration
├── test_error_integration.py        # Cross-component error handling
├── fixtures/                        # Integration test fixtures
│   ├── sample_repositories/         # Test repository data
│   ├── test_configs/               # Configuration files
│   └── mock_services/              # Mock external services
└── utils/                          # Integration test utilities
    ├── test_helpers.py             # Common test utilities
    ├── repository_builder.py       # Test repository creation
    └── service_mocks.py            # Service mocking utilities
```

## Running Integration Tests

Run all integration tests:
```bash
pytest tests/integration/ -m integration
```

Run specific integration test categories:
```bash
pytest tests/integration/test_end_to_end_workflows.py
pytest tests/integration/test_mcp_integration.py
pytest tests/integration/test_api_integration.py
```

Run with verbose output:
```bash
pytest tests/integration/ -v -s
```

Run with coverage:
```bash
pytest tests/integration/ --cov=githound --cov-report=html
```

## Test Scenarios

### End-to-End Workflow Testing
- Complete repository analysis from start to finish
- MCP client connecting and performing operations
- REST API client performing search and export
- Error recovery and retry scenarios
- Performance under realistic conditions

### MCP Server Integration
- Real MCP client connections
- Tool invocation with complex parameters
- Resource access patterns
- Concurrent client handling
- Error propagation and handling

### REST API Integration
- Full API workflow testing
- Authentication and authorization
- WebSocket real-time communication
- File upload and download
- Pagination and filtering

### Export System Integration
- Multi-format export workflows
- Large data export scenarios
- Export with various configurations
- Error handling during export
- Performance with large datasets

## Test Fixtures and Data

### Repository Fixtures
```python
@pytest.fixture(scope="session")
def integration_test_repo():
    """Create a comprehensive test repository for integration testing."""
    # Create repository with:
    # - Multiple branches
    # - Various file types
    # - Complex history
    # - Merge commits
    # - Tags and releases
    pass

@pytest.fixture
def real_git_repository():
    """Use a real Git repository for testing."""
    # Clone or use existing repository
    # Ensure consistent state
    pass
```

### Service Fixtures
```python
@pytest.fixture
def mcp_server_instance():
    """Start MCP server instance for testing."""
    # Start server
    # Wait for ready state
    # Provide cleanup
    pass

@pytest.fixture
def api_server_instance():
    """Start REST API server for testing."""
    # Start FastAPI server
    # Configure test database
    # Provide cleanup
    pass
```

### Client Fixtures
```python
@pytest.fixture
def mcp_client():
    """MCP client for integration testing."""
    # Create authenticated client
    # Configure for test server
    pass

@pytest.fixture
def api_client():
    """HTTP client for API testing."""
    # Create HTTP client
    # Configure authentication
    # Set base URL
    pass
```

## Integration Test Patterns

### End-to-End Test Pattern
```python
async def test_complete_analysis_workflow(
    integration_test_repo,
    mcp_server_instance,
    mcp_client
):
    """Test complete repository analysis workflow."""
    
    # 1. Connect to MCP server
    async with mcp_client:
        
        # 2. Analyze repository
        analysis_result = await mcp_client.call_tool(
            "analyze_repository",
            {"input_data": {"repo_path": str(integration_test_repo)}}
        )
        
        # 3. Verify analysis results
        assert analysis_result is not None
        # Additional assertions...
        
        # 4. Get commit history
        history_result = await mcp_client.call_tool(
            "get_commit_history",
            {
                "input_data": {
                    "repo_path": str(integration_test_repo),
                    "max_count": 10
                }
            }
        )
        
        # 5. Verify history results
        assert history_result is not None
        # Additional assertions...
        
        # 6. Export data
        export_result = await mcp_client.call_tool(
            "export_repository_data",
            {
                "input_data": {
                    "repo_path": str(integration_test_repo),
                    "output_path": "/tmp/test_export.json",
                    "format": "json"
                }
            }
        )
        
        # 7. Verify export
        assert export_result is not None
        assert Path("/tmp/test_export.json").exists()
```

### API Integration Test Pattern
```python
async def test_api_search_workflow(api_server_instance, api_client):
    """Test complete API search workflow."""
    
    # 1. Start search
    search_request = {
        "query": "test query",
        "repository_path": "/path/to/repo",
        "search_type": "message"
    }
    
    response = await api_client.post("/api/search", json=search_request)
    assert response.status_code == 200
    
    search_data = response.json()
    search_id = search_data["search_id"]
    
    # 2. Monitor search progress
    while True:
        status_response = await api_client.get(f"/api/search/{search_id}/status")
        status_data = status_response.json()
        
        if status_data["status"] in ["completed", "failed"]:
            break
        
        await asyncio.sleep(0.1)
    
    # 3. Get results
    results_response = await api_client.get(f"/api/search/{search_id}")
    assert results_response.status_code == 200
    
    results_data = results_response.json()
    assert "results" in results_data
    assert results_data["total_count"] >= 0
```

### Error Integration Test Pattern
```python
async def test_error_propagation_across_components(
    mcp_server_instance,
    mcp_client
):
    """Test error handling across multiple components."""
    
    async with mcp_client:
        # Test invalid repository path
        with pytest.raises(Exception) as exc_info:
            await mcp_client.call_tool(
                "analyze_repository",
                {"input_data": {"repo_path": "/nonexistent/path"}}
            )
        
        # Verify error details
        assert "Repository not found" in str(exc_info.value)
        
        # Test invalid commit hash
        with pytest.raises(Exception) as exc_info:
            await mcp_client.call_tool(
                "analyze_commit",
                {
                    "input_data": {
                        "repo_path": str(integration_test_repo),
                        "commit_hash": "invalid-hash"
                    }
                }
            )
        
        # Verify error details
        assert "Invalid commit" in str(exc_info.value)
```

## Test Environment Setup

### Docker Integration Testing
```dockerfile
# Dockerfile.integration-test
FROM python:3.11

WORKDIR /app
COPY . .

RUN pip install -e .
RUN pip install pytest pytest-asyncio httpx

CMD ["pytest", "tests/integration/", "-v"]
```

### Docker Compose for Integration Tests
```yaml
# docker-compose.integration.yml
version: '3.8'

services:
  githound-test:
    build:
      context: .
      dockerfile: Dockerfile.integration-test
    volumes:
      - ./tests/integration/fixtures:/app/test-data
    environment:
      - PYTHONPATH=/app
      - TEST_MODE=integration
    depends_on:
      - test-git-server
  
  test-git-server:
    image: gitea/gitea:latest
    environment:
      - USER_UID=1000
      - USER_GID=1000
    ports:
      - "3000:3000"
    volumes:
      - ./tests/integration/fixtures/git-repos:/data
```

## Continuous Integration

### GitHub Actions Integration Testing
```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
      with:
        fetch-depth: 0
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -e .
        pip install pytest pytest-asyncio httpx
    
    - name: Run integration tests
      run: |
        pytest tests/integration/ -v --tb=short
    
    - name: Upload test results
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: integration-test-results
        path: test-results/
```
