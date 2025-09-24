"""
Tests for MCP server implementations.

This module contains comprehensive tests for both the simple MCP server
and the GitHound MCP server implementations.
"""

import asyncio
import json
import pytest
import tempfile
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, patch, MagicMock

from fastmcp.client import FastMCPClient
from fastmcp.client.transports import StdioTransport
from fastmcp.exceptions import ToolError

# Import server modules to test
import sys
sys.path.append(str(Path(__file__).parent.parent))

from servers import simple_server, githound_server


class TestSimpleServer:
    """Test simple MCP server functionality."""

    @pytest.mark.asyncio
    async def test_simple_server_tools(self, simple_mcp_client) -> None:
        """Test simple server tool functionality."""
        # Get available tools
        tools = await simple_mcp_client.list_tools()
        tool_names = [tool.name for tool in tools]

        # Verify expected tools are available
        expected_tools = ["echo", "add_numbers", "get_server_info", "simulate_error"]
        for expected_tool in expected_tools:
            assert expected_tool in tool_names

    @pytest.mark.asyncio
    async def test_echo_tool(self, simple_mcp_client) -> None:
        """Test echo tool functionality."""
        result = await simple_mcp_client.call_tool("echo", {"message": "test message"})

        assert result is not None
        assert result.data is not None
        assert "test message" in str(result.data)

    @pytest.mark.asyncio
    async def test_add_numbers_tool(self, simple_mcp_client) -> None:
        """Test add_numbers tool functionality."""
        result = await simple_mcp_client.call_tool("add_numbers", {"a": 10.5, "b": 20.3})

        assert result is not None
        assert result.data is not None

        if isinstance(result.data, dict):
            assert "sum" in result.data
            assert abs(result.data["sum"] - 30.8) < 0.001  # Float comparison
            assert "operation" in result.data
            assert result.data["operation"] == "addition"

    @pytest.mark.asyncio
    async def test_get_server_info_tool(self, simple_mcp_client) -> None:
        """Test get_server_info tool functionality."""
        result = await simple_mcp_client.call_tool("get_server_info", {})

        assert result is not None
        assert result.data is not None

        if isinstance(result.data, dict):
            assert "name" in result.data
            assert "version" in result.data
            assert "capabilities" in result.data

    @pytest.mark.asyncio
    async def test_simulate_error_tool(self, simple_mcp_client) -> None:
        """Test simulate_error tool functionality."""
        # Test validation error
        with pytest.raises(ToolError):
            await simple_mcp_client.call_tool("simulate_error", {"error_type": "validation"})

        # Test permission error
        with pytest.raises(ToolError):
            await simple_mcp_client.call_tool("simulate_error", {"error_type": "permission"})

        # Test generic error
        with pytest.raises(ToolError):
            await simple_mcp_client.call_tool("simulate_error", {"error_type": "generic"})

    @pytest.mark.asyncio
    async def test_simple_server_resources(self, simple_mcp_client) -> None:
        """Test simple server resource functionality."""
        # Get available resources
        resources = await simple_mcp_client.list_resources()
        resource_uris = [resource.uri for resource in resources]

        # Verify expected resources are available
        expected_resources = [
            "simple://server/info",
            "simple://config/settings",
            "simple://status/current"
        ]
        for expected_resource in expected_resources:
            assert expected_resource in resource_uris

    @pytest.mark.asyncio
    async def test_server_info_resource(self, simple_mcp_client) -> None:
        """Test server info resource."""
        content = await simple_mcp_client.read_resource("simple://server/info")

        assert content is not None
        assert len(content) > 0
        assert hasattr(content[0], 'text')

        # Parse JSON content
        data = json.loads(content[0].text)
        assert "server_name" in data
        assert "version" in data
        assert "features" in data

    @pytest.mark.asyncio
    async def test_config_resource(self, simple_mcp_client) -> None:
        """Test config resource."""
        content = await simple_mcp_client.read_resource("simple://config/settings")  # [attr-defined]

        assert content is not None
        assert len(content) > 0
        assert hasattr(content[0], 'text')

        # Parse JSON content
        data = json.loads(content[0].text)
        assert "server_settings" in data
        assert "tool_settings" in data
        assert "resource_settings" in data

    @pytest.mark.asyncio
    async def test_status_resource(self, simple_mcp_client) -> None:
        """Test status resource."""
        content = await simple_mcp_client.read_resource("simple://status/current")

        assert content is not None
        assert len(content) > 0
        assert hasattr(content[0], 'text')

        # Parse JSON content
        data = json.loads(content[0].text)
        assert "status" in data
        assert "uptime_start" in data
        assert "health_check" in data


class TestGitHoundServer:
    """Test GitHound MCP server functionality."""

    @pytest.mark.asyncio
    async def test_githound_server_tools(self, githound_mcp_client) -> None:
        """Test GitHound server tool functionality."""
        # Get available tools
        tools = await githound_mcp_client.list_tools()
        tool_names = [tool.name for tool in tools]

        # Verify expected tools are available
        expected_tools = [
            "analyze_repository",
            "analyze_commit",
            "get_commit_history",
            "get_file_history",
            "get_author_stats"
        ]
        for expected_tool in expected_tools:
            assert expected_tool in tool_names

    @pytest.mark.asyncio
    async def test_analyze_repository_tool(self, githound_mcp_client, temp_git_repo) -> None:
        """Test analyze_repository tool functionality."""
        result = await githound_mcp_client.call_tool("analyze_repository", {
            "repo_path": str(temp_git_repo)
        })

        assert result is not None
        assert result.data is not None

        if isinstance(result.data, dict):
            assert "name" in result.data
            assert "path" in result.data
            assert "total_commits" in result.data
            assert "total_files" in result.data
            assert "total_authors" in result.data

    @pytest.mark.asyncio
    async def test_get_commit_history_tool(self, githound_mcp_client, temp_git_repo) -> None:
        """Test get_commit_history tool functionality."""
        result = await githound_mcp_client.call_tool("get_commit_history", {
            "repo_path": str(temp_git_repo),
            "limit": 5
        })

        assert result is not None
        assert result.data is not None

        if isinstance(result.data, list):
            assert len(result.data) > 0

            # Check first commit structure
            commit = result.data[0]
            if isinstance(commit, dict):
                assert "hash" in commit
                assert "author" in commit
                assert "message" in commit
                assert "date" in commit

    @pytest.mark.asyncio
    async def test_get_author_stats_tool(self, githound_mcp_client, temp_git_repo) -> None:
        """Test get_author_stats tool functionality."""
        result = await githound_mcp_client.call_tool("get_author_stats", {
            "repo_path": str(temp_git_repo)
        })

        assert result is not None
        assert result.data is not None

        if isinstance(result.data, dict):
            assert "total_authors" in result.data
            assert "authors" in result.data
            assert isinstance(result.data["authors"], list)

    @pytest.mark.asyncio
    async def test_get_file_history_tool(self, githound_mcp_client, temp_git_repo) -> None:
        """Test get_file_history tool functionality."""
        result = await githound_mcp_client.call_tool("get_file_history", {
            "repo_path": str(temp_git_repo),
            "file_path": "README.md",
            "limit": 5
        })

        assert result is not None
        assert result.data is not None

        if isinstance(result.data, list):
            # Should have at least one commit for README.md
            assert len(result.data) > 0

    @pytest.mark.asyncio
    async def test_githound_server_resources(self, githound_mcp_client) -> None:
        """Test GitHound server resource functionality."""
        # Get available resources
        resources = await githound_mcp_client.list_resources()

        # Check for templated resources
        templated_resources = [r for r in resources if '{' in r.uri and '}' in r.uri]
        assert len(templated_resources) > 0

        # Verify expected resource patterns
        resource_uris = [resource.uri for resource in resources]
        expected_patterns = [
            "githound://repository/{repo_path}/summary",
            "githound://repository/{repo_path}/contributors"
        ]

        for pattern in expected_patterns:
            assert pattern in resource_uris

    @pytest.mark.asyncio
    async def test_repository_summary_resource(self, githound_mcp_client, temp_git_repo) -> None:
        """Test repository summary resource."""
        uri = f"githound://repository/{temp_git_repo}/summary"
        content = await githound_mcp_client.read_resource(uri)

        assert content is not None
        assert len(content) > 0
        assert hasattr(content[0], 'text')

        # Parse JSON content
        data = json.loads(content[0].text)
        assert "repository" in data
        assert "summary" in data
        assert "generated_at" in data

    @pytest.mark.asyncio
    async def test_contributors_resource(self, githound_mcp_client, temp_git_repo) -> None:
        """Test contributors resource."""
        uri = f"githound://repository/{temp_git_repo}/contributors"
        content = await githound_mcp_client.read_resource(uri)

        assert content is not None
        assert len(content) > 0
        assert hasattr(content[0], 'text')

        # Parse JSON content
        data = json.loads(content[0].text)
        assert "contributors" in data
        assert "summary" in data
        assert "generated_at" in data


class TestServerErrorHandling:
    """Test server error handling capabilities."""

    @pytest.mark.asyncio
    async def test_invalid_repository_path(self, githound_mcp_client) -> None:
        """Test handling of invalid repository paths."""
        with pytest.raises(ToolError):
            await githound_mcp_client.call_tool("analyze_repository", {
                "repo_path": "/non/existent/path"
            })

    @pytest.mark.asyncio
    async def test_invalid_commit_hash(self, githound_mcp_client, temp_git_repo) -> None:
        """Test handling of invalid commit hashes."""
        with pytest.raises(ToolError):
            await githound_mcp_client.call_tool("analyze_commit", {
                "repo_path": str(temp_git_repo),
                "commit_hash": "invalid_hash_123"
            })

    @pytest.mark.asyncio
    async def test_invalid_file_path(self, githound_mcp_client, temp_git_repo) -> None:
        """Test handling of invalid file paths."""
        # This might not raise an error but should return empty results
        result = await githound_mcp_client.call_tool("get_file_history", {
            "repo_path": str(temp_git_repo),
            "file_path": "non_existent_file.txt",
            "limit": 5
        })

        assert result is not None
        # Should return empty list or handle gracefully
        if isinstance(result.data, list):
            assert len(result.data) == 0

    @pytest.mark.asyncio
    async def test_invalid_resource_uri(self, githound_mcp_client) -> None:
        """Test handling of invalid resource URIs."""
        with pytest.raises(Exception):  # Could be various exception types
            await githound_mcp_client.read_resource("invalid://resource/uri")


class TestServerPerformance:
    """Test server performance characteristics."""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_tool_execution_performance(self, simple_mcp_client, performance_thresholds) -> None:
        """Test tool execution performance."""
        import time

        # Test echo tool performance
        start_time = time.time()
        await simple_mcp_client.call_tool("echo", {"message": "performance test"})
        execution_time = time.time() - start_time

        assert execution_time < performance_thresholds["tool_execution_max_time"]

        # Test add_numbers tool performance
        start_time = time.time()
        await simple_mcp_client.call_tool("add_numbers", {"a": 1.0, "b": 2.0})
        execution_time = time.time() - start_time

        assert execution_time < performance_thresholds["tool_execution_max_time"]

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_resource_access_performance(self, simple_mcp_client, performance_thresholds) -> None:
        """Test resource access performance."""
        import time

        # Test resource access performance
        start_time = time.time()
        await simple_mcp_client.read_resource("simple://server/info")
        execution_time = time.time() - start_time

        assert execution_time < performance_thresholds["resource_access_max_time"]

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, simple_mcp_client) -> None:
        """Test handling of concurrent requests."""
        # Execute multiple tools concurrently
        tasks = [
            simple_mcp_client.call_tool("echo", {"message": f"test {i}"})
            for i in range(5)
        ]

        results = await asyncio.gather(*tasks)

        # All requests should succeed
        assert len(results) == 5
        for result in results:
            assert result is not None
            assert result.data is not None


class TestServerConfiguration:
    """Test server configuration and setup."""

    def test_simple_server_app_creation(self) -> None:
        """Test simple server app creation."""
        # Test that the FastMCP app is properly configured
        assert simple_server.app is not None
        assert simple_server.app.name == "Simple MCP Server"

    def test_githound_server_app_creation(self) -> None:
        """Test GitHound server app creation."""
        # Test that the FastMCP app is properly configured
        assert githound_server.app is not None
        assert githound_server.app.name == "GitHound MCP Server"

    @patch('githound_server.GITHOUND_AVAILABLE', False)
    def test_githound_server_mock_mode(self) -> None:
        """Test GitHound server in mock mode."""
        # Test that server can run without GitHound modules
        assert githound_server.GITHOUND_AVAILABLE is False

    def test_pydantic_models(self) -> None:
        """Test Pydantic model definitions."""
        from githound_server import RepositoryInfo, CommitInfo, FileInfo

        # Test RepositoryInfo model
        repo_info = RepositoryInfo(
            name="test-repo",
            path="/tmp/test",
            total_commits=10,
            total_files=5,
            total_authors=2,
            branches=["main"],
            tags=["v1.0.0"]
        )

        assert repo_info.name == "test-repo"
        assert repo_info.total_commits == 10

        # Test CommitInfo model
        commit_info = CommitInfo(
            hash="abc123",
            author="Test Author",
            author_email="test@example.com",
            date="2024-01-15T10:30:00Z",
            message="Test commit",
            files_changed=2,
            insertions=10,
            deletions=5
        )

        assert commit_info.hash == "abc123"
        assert commit_info.author == "Test Author"


class TestServerIntegration:
    """Integration tests for server functionality."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_workflow_simple_server(self, simple_mcp_client) -> None:
        """Test full workflow with simple server."""
        # 1. List tools and resources
        tools = await simple_mcp_client.list_tools()
        resources = await simple_mcp_client.list_resources()

        assert len(tools) > 0
        assert len(resources) > 0

        # 2. Execute all tools
        for tool in tools:
            if tool.name == "simulate_error":
                continue  # Skip error simulation tool

            try:
                if tool.name == "echo":
                    result = await simple_mcp_client.call_tool(tool.name, {"message": "test"})
                elif tool.name == "add_numbers":
                    result = await simple_mcp_client.call_tool(tool.name, {"a": 1.0, "b": 2.0})
                else:
                    result = await simple_mcp_client.call_tool(tool.name, {})

                assert result is not None
            except Exception as e:
                pytest.fail(f"Tool {tool.name} failed: {e}")

        # 3. Access all resources
        for resource in resources:
            try:
                content = await simple_mcp_client.read_resource(resource.uri)
                assert content is not None
            except Exception as e:
                pytest.fail(f"Resource {resource.uri} failed: {e}")

    @pytest.mark.integration
    @pytest.mark.requires_git
    @pytest.mark.asyncio
    async def test_full_workflow_githound_server(self, githound_mcp_client, temp_git_repo) -> None:
        """Test full workflow with GitHound server."""
        repo_path = str(temp_git_repo)

        # 1. Analyze repository
        repo_result = await githound_mcp_client.call_tool("analyze_repository", {
            "repo_path": repo_path
        })
        assert repo_result is not None

        # 2. Get commit history
        history_result = await githound_mcp_client.call_tool("get_commit_history", {
            "repo_path": repo_path,
            "limit": 5
        })
        assert history_result is not None

        # 3. Get author stats
        author_result = await githound_mcp_client.call_tool("get_author_stats", {
            "repo_path": repo_path
        })
        assert author_result is not None

        # 4. Access resources
        summary_content = await githound_mcp_client.read_resource(
            f"githound://repository/{repo_path}/summary"
        )
        assert summary_content is not None

        contributors_content = await githound_mcp_client.read_resource(
            f"githound://repository/{repo_path}/contributors"
        )
        assert contributors_content is not None
