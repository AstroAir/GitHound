"""
Pytest configuration and fixtures for MCP server examples tests.

This module provides shared fixtures and configuration for testing
FastMCP client examples and server implementations.
"""

import asyncio
import logging
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Dict, Any, Optional
import pytest
import pytest_asyncio

from fastmcp.client import Client as FastMCPClient
from fastmcp.client import StdioTransport

# Configure test logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_git_repo():
    """
    Create a temporary Git repository for testing.
    
    Returns:
        Path to the temporary Git repository
    """
    import subprocess
    
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = Path(temp_dir)
        
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)
        
        # Create initial commit
        readme_file = repo_path / "README.md"
        readme_file.write_text("# Test Repository\n\nThis is a test repository for MCP examples.")
        
        subprocess.run(["git", "add", "README.md"], cwd=repo_path, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True)
        
        # Create additional commits
        for i in range(3):
            test_file = repo_path / f"test_{i}.py"
            test_file.write_text(f"# Test file {i}\nprint('Hello from test {i}')\n")
            
            subprocess.run(["git", "add", f"test_{i}.py"], cwd=repo_path, check=True)
            subprocess.run(["git", "commit", "-m", f"Add test file {i}"], cwd=repo_path, check=True)
        
        yield repo_path


@pytest_asyncio.fixture
async def simple_mcp_client() -> AsyncGenerator[FastMCPClient, None]:
    """
    Create a FastMCP client connected to the simple server.
    
    Yields:
        Connected FastMCP client instance
    """
    server_script = Path(__file__).parent.parent / "servers" / "simple_server.py"
    transport = StdioTransport("python", str(server_script))
    
    async with FastMCPClient(transport) as client:
        yield client


@pytest_asyncio.fixture
async def githound_mcp_client() -> AsyncGenerator[FastMCPClient, None]:
    """
    Create a FastMCP client connected to the GitHound server.
    
    Yields:
        Connected FastMCP client instance
    """
    server_script = Path(__file__).parent.parent / "servers" / "githound_server.py"
    transport = StdioTransport("python", str(server_script))
    
    async with FastMCPClient(transport) as client:
        yield client


@pytest.fixture
def mock_server_data():
    """
    Provide mock data for server testing.
    
    Returns:
        Dictionary containing mock server data
    """
    return {
        "repository": {
            "name": "test-repo",
            "path": "/tmp/test-repo",
            "total_commits": 10,
            "total_files": 5,
            "total_authors": 2,
            "branches": ["main", "develop"],
            "tags": ["v1.0.0"]
        },
        "commits": [
            {
                "hash": "abc123",
                "author": "Test Author",
                "author_email": "test@example.com",
                "date": "2024-01-15T10:30:00Z",
                "message": "Test commit",
                "files_changed": 2,
                "insertions": 10,
                "deletions": 5
            }
        ],
        "authors": [
            {
                "name": "Test Author",
                "email": "test@example.com",
                "commits": 8,
                "insertions": 100,
                "deletions": 20,
                "files_modified": 5
            },
            {
                "name": "Another Author", 
                "email": "another@example.com",
                "commits": 2,
                "insertions": 30,
                "deletions": 10,
                "files_modified": 2
            }
        ]
    }


@pytest.fixture
def sample_tool_args():
    """
    Provide sample arguments for tool testing.
    
    Returns:
        Dictionary containing sample tool arguments
    """
    return {
        "echo": {"message": "Test message"},
        "add_numbers": {"a": 10.5, "b": 20.3},
        "analyze_repository": {"repo_path": "."},
        "get_commit_history": {"repo_path": ".", "limit": 5},
        "get_author_stats": {"repo_path": "."}
    }


@pytest.fixture
def sample_resource_uris():
    """
    Provide sample resource URIs for testing.
    
    Returns:
        List of sample resource URIs
    """
    return [
        "simple://server/info",
        "simple://config/settings", 
        "simple://status/current",
        "githound://repository/./summary",
        "githound://repository/./contributors"
    ]


class MockMCPServer:
    """Mock MCP server for testing client functionality."""
    
    def __init__(self, tools: Optional[Dict[str, Any]] = None, resources: Optional[Dict[str, Any]] = None):
        self.tools = tools or {}
        self.resources = resources or {}
        self.call_count = 0
        self.last_call = None
    
    async def list_tools(self):
        """Mock list_tools implementation."""
        return list(self.tools.keys())
    
    async def call_tool(self, name: str, args: Dict[str, Any]):
        """Mock call_tool implementation."""
        self.call_count += 1
        self.last_call = {"tool": name, "args": args}
        
        if name in self.tools:
            return self.tools[name]
        else:
            raise ValueError(f"Tool {name} not found")
    
    async def list_resources(self):
        """Mock list_resources implementation."""
        return list(self.resources.keys())
    
    async def read_resource(self, uri: str):
        """Mock read_resource implementation."""
        if uri in self.resources:
            return self.resources[uri]
        else:
            raise ValueError(f"Resource {uri} not found")


@pytest.fixture
def mock_mcp_server():
    """
    Create a mock MCP server for testing.
    
    Returns:
        MockMCPServer instance
    """
    tools = {
        "echo": {"data": "Echo response", "content": []},
        "add_numbers": {"data": {"sum": 30.8, "operation": "addition"}, "content": []},
        "get_server_info": {"data": {"name": "Mock Server", "version": "1.0.0"}, "content": []}
    }
    
    resources = {
        "mock://server/info": [{"text": '{"server": "mock", "version": "1.0.0"}'}],
        "mock://config/settings": [{"text": '{"setting1": "value1", "setting2": "value2"}'}]
    }
    
    return MockMCPServer(tools, resources)


@pytest.fixture
def client_test_config():
    """
    Provide configuration for client testing.
    
    Returns:
        Dictionary containing test configuration
    """
    return {
        "timeout": 30.0,
        "retry_attempts": 3,
        "retry_delay": 1.0,
        "max_content_size": 1024 * 1024,  # 1MB
        "supported_transports": ["stdio", "http", "sse", "inmemory"],
        "test_repo_path": ".",
        "mock_mode": True
    }


@pytest.fixture
def performance_thresholds():
    """
    Provide performance thresholds for testing.
    
    Returns:
        Dictionary containing performance thresholds
    """
    return {
        "tool_execution_max_time": 5.0,  # seconds
        "resource_access_max_time": 2.0,  # seconds
        "connection_max_time": 10.0,  # seconds
        "max_memory_usage": 100 * 1024 * 1024,  # 100MB
        "max_response_size": 10 * 1024 * 1024  # 10MB
    }


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_git: mark test as requiring git repository"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Add integration marker to integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Add performance marker to performance tests
        if "performance" in item.nodeid:
            item.add_marker(pytest.mark.performance)
        
        # Add slow marker to tests that might be slow
        if any(keyword in item.nodeid for keyword in ["comprehensive", "full", "end_to_end"]):
            item.add_marker(pytest.mark.slow)
        
        # Add requires_git marker to tests that need git
        if any(keyword in item.nodeid for keyword in ["git", "repository", "commit"]):
            item.add_marker(pytest.mark.requires_git)
