"""
Integration tests for MCP server examples.

This module contains end-to-end integration tests that verify the complete
functionality of the MCP server examples, including client-server interactions,
real-world scenarios, and performance characteristics.
"""

import asyncio
import json
import subprocess

# Import example modules
import sys
import time
from pathlib import Path
from typing import Any

import pytest
from fastmcp.client import FastMCPClient
from fastmcp.client.transports import StdioTransport

sys.path.append(str(Path(__file__).parent.parent))

from clients import githound_client


class TestEndToEndWorkflows:
    """Test complete end-to-end workflows."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_basic_client_workflow(self) -> None:
        """Test complete basic client workflow."""
        from clients import basic_client

        # Run the complete basic client workflow
        result = await basic_client.main()

        assert isinstance(result, dict)
        assert "setup" in result
        assert "tools" in result
        assert "resources" in result
        assert "error_handling" in result

        # Verify each section completed successfully
        for section_name, section_result in result.items():
            if isinstance(section_result, dict) and "status" in section_result:
                # Allow some failures for HTTP/SSE transports that may not be available
                if section_result["status"] == "failed" and "transport" in section_name:
                    continue
                assert (
                    section_result["status"] == "success"
                ), f"Section {section_name} failed: {section_result.get('error', 'Unknown error')}"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_transport_examples_workflow(self) -> None:
        """Test complete transport examples workflow."""
        from clients import transport_examples

        # Run the complete transport examples workflow
        result = await transport_examples.main()

        assert isinstance(result, dict)
        assert "stdio" in result
        assert "http" in result
        assert "sse" in result
        assert "inmemory" in result

        # STDIO transport should always work
        assert result["stdio"]["status"] == "success"

        # HTTP and SSE may fail if servers aren't running (expected)
        # In-memory should work
        assert result["inmemory"]["status"] == "success"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_tool_operations_workflow(self) -> None:
        """Test complete tool operations workflow."""
        from clients import tool_operations

        # Run the complete tool operations workflow
        result = await tool_operations.main()

        assert isinstance(result, dict)
        assert "discovery" in result
        assert "simple_execution" in result
        assert "complex_arguments" in result
        assert "error_handling" in result

        # All sections should succeed
        for section_name, section_result in result.items():
            if isinstance(section_result, dict) and "status" in section_result:
                assert section_result["status"] == "success", f"Section {section_name} failed"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_resource_operations_workflow(self) -> None:
        """Test complete resource operations workflow."""
        from clients import resource_operations

        # Run the complete resource operations workflow
        result = await resource_operations.main()

        assert isinstance(result, dict)
        assert "discovery" in result
        assert "static_access" in result
        assert "templated_resources" in result
        assert "content_types" in result
        assert "resource_patterns" in result

        # All sections should succeed
        for section_name, section_result in result.items():
            if isinstance(section_result, dict) and "status" in section_result:
                assert section_result["status"] == "success", f"Section {section_name} failed"

    @pytest.mark.integration
    @pytest.mark.requires_git
    @pytest.mark.asyncio
    async def test_githound_client_workflow(self, temp_git_repo) -> None:
        """Test complete GitHound client workflow."""
        # Run the GitHound client analysis
        result = await githound_client.main(str(temp_git_repo))

        assert isinstance(result, dict)

        if "error" not in result:
            assert "repository_analysis" in result
            assert "resource_access" in result
            assert "advanced_queries" in result

            # Verify repository analysis
            repo_analysis = result["repository_analysis"]
            if "repository" in repo_analysis:
                repo_info = repo_analysis["repository"]
                assert "name" in repo_info
                assert "total_commits" in repo_info
                assert repo_info["total_commits"] > 0


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    @pytest.mark.integration
    @pytest.mark.requires_git
    @pytest.mark.asyncio
    async def test_analyze_current_repository(self) -> None:
        """Test analyzing the current GitHound repository."""
        # Use the current directory (GitHound repository)
        current_repo = Path(__file__).parent.parent.parent.parent

        if not (current_repo / ".git").exists():
            pytest.skip("Not in a Git repository")

        # Run GitHound client on current repository
        result = await githound_client.main(str(current_repo))

        assert isinstance(result, dict)

        if "error" not in result:
            # Should have meaningful data for GitHound repository
            repo_analysis = result.get("repository_analysis", {})
            if "repository" in repo_analysis:
                repo_info = repo_analysis["repository"]
                assert repo_info.get("total_commits", 0) > 0
                assert repo_info.get("total_files", 0) > 0
                assert repo_info.get("total_authors", 0) > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_client_connections(self) -> None:
        """Test multiple concurrent client connections."""
        server_script = Path(__file__).parent.parent / "servers" / "simple_server.py"

        async def create_client_and_test() -> None:
            transport = StdioTransport("python", str(server_script))
            async with FastMCPClient(transport) as client:
                # Perform basic operations
                tools = await client.list_tools()
                resources = await client.list_resources()

                # Execute a tool
                result = await client.call_tool("echo", {"message": "concurrent test"})

                return {
                    "tools_count": len(tools),
                    "resources_count": len(resources),
                    "tool_result": result.data,
                }

        # Create multiple concurrent clients
        tasks = [create_client_and_test() for _ in range(3)]
        results = await asyncio.gather(*tasks)

        # All clients should succeed
        assert len(results) == 3
        for result in results:
            assert result["tools_count"] > 0
            assert result["resources_count"] > 0
            assert result["tool_result"] is not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_large_data_handling(self, simple_mcp_client) -> None:
        """Test handling of large data sets."""
        # Test with large message
        large_message = "x" * 10000  # 10KB message

        result = await simple_mcp_client.call_tool("echo", {"message": large_message})
        assert result is not None
        assert large_message in str(result.data)

        # Test with large numbers
        result = await simple_mcp_client.call_tool(
            "add_numbers", {"a": 999999999.999999, "b": 888888888.888888}
        )
        assert result is not None
        assert result.data is not None

    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_long_running_operations(self, temp_git_repo) -> None:
        """Test long-running operations."""
        # Create a larger repository for testing
        repo_path = temp_git_repo

        # Add more commits to make operations take longer
        for i in range(10):
            test_file = repo_path / f"large_file_{i}.py"
            content = "\n".join([f"# Line {j} in file {i}" for j in range(100)])
            test_file.write_text(content)

            subprocess.run(["git", "add", f"large_file_{i}.py"], cwd=repo_path, check=True)
            subprocess.run(
                ["git", "commit", "-m", f"Add large file {i}"], cwd=repo_path, check=True
            )

        # Test GitHound operations on larger repository
        server_script = Path(__file__).parent.parent / "servers" / "githound_server.py"
        transport = StdioTransport("python", str(server_script))

        async with FastMCPClient(transport) as client:
            start_time = time.time()

            # Analyze repository
            result = await client.call_tool("analyze_repository", {"repo_path": str(repo_path)})

            execution_time = time.time() - start_time

            assert result is not None
            assert execution_time < 30.0  # Should complete within 30 seconds

            if isinstance(result.data, dict):
                assert result.data.get("total_commits", 0) > 10


class TestErrorRecovery:
    """Test error recovery and resilience."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_server_restart_recovery(self) -> None:
        """Test recovery from server restart."""
        server_script = Path(__file__).parent.parent / "servers" / "simple_server.py"

        # First connection
        transport1 = StdioTransport("python", str(server_script))
        async with FastMCPClient(transport1) as client1:
            result1 = await client1.call_tool("echo", {"message": "first connection"})
            assert result1 is not None

        # Second connection (simulates restart)
        transport2 = StdioTransport("python", str(server_script))
        async with FastMCPClient(transport2) as client2:
            result2 = await client2.call_tool("echo", {"message": "second connection"})
            assert result2 is not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_malformed_request_handling(self, simple_mcp_client) -> None:
        """Test handling of malformed requests."""
        # Test with invalid tool arguments
        try:
            await simple_mcp_client.call_tool("add_numbers", {"invalid": "args"})
        except Exception:
            # Should handle gracefully
            pass

        # Server should still be responsive after malformed request
        result = await simple_mcp_client.call_tool("echo", {"message": "recovery test"})
        assert result is not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_resource_not_found_recovery(self, simple_mcp_client) -> None:
        """Test recovery from resource not found errors."""
        # Try to access non-existent resource
        try:
            await simple_mcp_client.read_resource("simple://non/existent/resource")
        except Exception:
            # Should handle gracefully
            pass

        # Server should still be responsive
        resources = await simple_mcp_client.list_resources()
        assert len(resources) > 0


class TestPerformanceIntegration:
    """Integration tests for performance characteristics."""

    @pytest.mark.performance
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_throughput_performance(self, simple_mcp_client) -> None:
        """Test throughput performance."""
        start_time = time.time()

        # Execute many operations
        tasks: list[Any] = []
        for i in range(50):
            if i % 2 == 0:
                task = simple_mcp_client.call_tool("echo", {"message": f"test {i}"})
            else:
                task = simple_mcp_client.call_tool("add_numbers", {"a": i, "b": i + 1})
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        execution_time = time.time() - start_time
        throughput = len(results) / execution_time

        # Should achieve reasonable throughput
        assert throughput > 5.0  # At least 5 operations per second
        assert all(result is not None for result in results)

    @pytest.mark.performance
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_memory_usage_stability(self, simple_mcp_client) -> None:
        """Test memory usage stability over time."""
        import os

        import psutil

        process = psutil.Process(os.getpid if os is not None else None())
        initial_memory = process.memory_info().rss

        # Perform many operations
        for i in range(100):
            await simple_mcp_client.call_tool("echo", {"message": f"memory test {i}"})

            if i % 20 == 0:
                current_memory = process.memory_info().rss
                memory_growth = current_memory - initial_memory

                # Memory growth should be reasonable (less than 50MB)
                assert memory_growth < 50 * 1024 * 1024

    @pytest.mark.performance
    @pytest.mark.integration
    @pytest.mark.requires_git
    @pytest.mark.asyncio
    async def test_git_operations_performance(self, temp_git_repo) -> None:
        """Test performance of Git operations."""
        server_script = Path(__file__).parent.parent / "servers" / "githound_server.py"
        transport = StdioTransport("python", str(server_script))

        async with FastMCPClient(transport) as client:
            # Test repository analysis performance
            start_time = time.time()
            result = await client.call_tool("analyze_repository", {"repo_path": str(temp_git_repo)})
            analysis_time = time.time() - start_time

            assert result is not None
            assert analysis_time < 10.0  # Should complete within 10 seconds

            # Test commit history performance
            start_time = time.time()
            result = await client.call_tool(
                "get_commit_history", {"repo_path": str(temp_git_repo), "limit": 10}
            )
            history_time = time.time() - start_time

            assert result is not None
            assert history_time < 5.0  # Should complete within 5 seconds


class TestDataConsistency:
    """Test data consistency across operations."""

    @pytest.mark.integration
    @pytest.mark.requires_git
    @pytest.mark.asyncio
    async def test_repository_data_consistency(self, temp_git_repo, githound_mcp_client) -> None:
        """Test consistency of repository data across different operations."""
        repo_path = str(temp_git_repo)

        # Get repository info
        repo_result = await githound_mcp_client.call_tool(
            "analyze_repository", {"repo_path": repo_path}
        )

        # Get commit history
        history_result = await githound_mcp_client.call_tool(
            "get_commit_history", {"repo_path": repo_path, "limit": 100}  # Get all commits
        )

        # Get author stats
        author_result = await githound_mcp_client.call_tool(
            "get_author_stats", {"repo_path": repo_path}
        )

        if (
            repo_result.data
            and history_result.data
            and author_result.data
            and isinstance(repo_result.data, dict)
            and isinstance(history_result.data, list)
            and isinstance(author_result.data, dict)
        ):
            # Verify consistency
            repo_commits = repo_result.data.get("total_commits", 0)
            history_commits = len(history_result.data)

            # History should not exceed total commits
            assert history_commits <= repo_commits

            # Author count should be consistent
            repo_authors = repo_result.data.get("total_authors", 0)
            stats_authors = author_result.data.get("total_authors", 0)

            assert repo_authors == stats_authors

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_resource_tool_consistency(self, githound_mcp_client, temp_git_repo) -> None:
        """Test consistency between resource data and tool results."""
        repo_path = str(temp_git_repo)

        # Get data via tool
        tool_result = await githound_mcp_client.call_tool(
            "get_author_stats", {"repo_path": repo_path}
        )

        # Get data via resource
        resource_content = await githound_mcp_client.read_resource(
            f"githound://repository/{repo_path}/contributors"
        )

        if (
            tool_result.data
            and resource_content
            and isinstance(tool_result.data, dict)
            and len(resource_content) > 0
        ):
            resource_data = json.loads(resource_content[0].text)

            # Compare author counts
            tool_authors = tool_result.data.get("total_authors", 0)
            resource_authors = resource_data.get("summary", {}).get("total_contributors", 0)

            assert tool_authors == resource_authors


class TestScalability:
    """Test scalability characteristics."""

    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_multiple_repository_analysis(self, temp_git_repo) -> None:
        """Test analyzing multiple repositories."""
        server_script = Path(__file__).parent.parent / "servers" / "githound_server.py"
        transport = StdioTransport("python", str(server_script))

        async with FastMCPClient(transport) as client:
            # Analyze the same repository multiple times (simulating different repos)
            tasks = [
                client.call_tool("analyze_repository", {"repo_path": str(temp_git_repo)})
                for _ in range(5)
            ]

            results = await asyncio.gather(*tasks)

            # All analyses should succeed
            assert len(results) == 5
            for result in results:
                assert result is not None
                assert result.data is not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_high_frequency_requests(self, simple_mcp_client) -> None:
        """Test handling of high-frequency requests."""
        # Send requests rapidly
        tasks: list[Any] = []
        for i in range(20):
            task = simple_mcp_client.call_tool("get_server_info", {})
            tasks.append(task)

        start_time = time.time()
        results = await asyncio.gather(*tasks)
        execution_time = time.time() - start_time

        # All requests should succeed
        assert len(results) == 20
        for result in results:
            assert result is not None

        # Should handle requests efficiently
        assert execution_time < 10.0  # All requests within 10 seconds
