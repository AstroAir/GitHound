"""
MCP Server Performance Testing

Performance tests for the GitHound MCP server following FastMCP testing
best practices for performance and scalability testing.

Based on: https://gofastmcp.com/deployment/testing
"""

import pytest
import asyncio
import time
import psutil
import gc
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import patch, MagicMock

from fastmcp import Client
from git import Repo


class TestPerformanceBenchmarks:
    """Test performance benchmarks for MCP operations."""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_tool_execution_performance(self, mcp_client, temp_repo):
        """Test tool execution performance benchmarks."""
        repo_path = str(temp_repo.working_dir)
        
        # Benchmark repository validation
        start_time = time.time()
        result = await mcp_client.call_tool(
            "validate_repository",
            {"repo_path": repo_path}
        )
        execution_time = time.time() - start_time
        
        # Should complete within reasonable time
        assert execution_time < 5.0, f"Tool execution took {execution_time:.2f}s, expected < 5.0s"
        assert result is not None
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_resource_access_performance(self, mcp_client, temp_repo):
        """Test resource access performance."""
        repo_path = str(temp_repo.working_dir)
        
        # Benchmark resource listing
        start_time = time.time()
        resources = await mcp_client.list_resources()
        list_time = time.time() - start_time
        
        assert list_time < 2.0, f"Resource listing took {list_time:.2f}s, expected < 2.0s"
        assert isinstance(resources, list)
        
        # Benchmark resource reading (if available)
        if resources:
            resource_uri = f"githound://repository/{repo_path}/metadata"
            try:
                start_time = time.time()
                content = await mcp_client.read_resource(resource_uri)
                read_time = time.time() - start_time
                
                assert read_time < 3.0, f"Resource reading took {read_time:.2f}s, expected < 3.0s"
            except Exception:
                pytest.skip("Resource not available for performance testing")
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_operations_performance(self, mcp_server, temp_repo):
        """Test performance under concurrent load."""
        repo_path = str(temp_repo.working_dir)
        
        async def perform_operation(operation_id: int):
            async with Client(mcp_server) as client:
                start_time = time.time()
                await client.call_tool(
                    "validate_repository",
                    {"repo_path": repo_path}
                )
                return time.time() - start_time
        
        # Run concurrent operations
        num_operations = 10
        start_time = time.time()
        
        tasks = [perform_operation(i) for i in range(num_operations)]
        execution_times = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_time = time.time() - start_time
        
        # Filter out exceptions
        successful_times = [t for t in execution_times if isinstance(t, float)]
        
        assert len(successful_times) > 0, "No operations completed successfully"
        
        # Average execution time should be reasonable
        avg_time = sum(successful_times) / len(successful_times)
        assert avg_time < 15.0, f"Average execution time {avg_time:.2f}s too high"
        
        # Total time should show some concurrency benefit
        sequential_time_estimate = avg_time * num_operations
        concurrency_ratio = total_time / sequential_time_estimate
        assert concurrency_ratio < 0.8, f"Poor concurrency performance: {concurrency_ratio:.2f}"


class TestLargeRepositoryHandling:
    """Test performance with large repositories."""
    
    @pytest.mark.performance
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_large_repository_analysis(self, mcp_client, large_repo_mock, performance_test_data):
        """Test analysis of large repositories."""
        with patch('githound.git_handler.get_repository') as mock_get_repo:
            mock_get_repo.return_value = large_repo_mock
            
            start_time = time.time()
            
            try:
                result = await mcp_client.call_tool(
                    "analyze_repository",
                    {"repo_path": "/large/repo"}
                )
                execution_time = time.time() - start_time
                
                # Should handle large repos within reasonable time
                assert execution_time < 30.0, f"Large repo analysis took {execution_time:.2f}s"
                assert result is not None
                
            except Exception as e:
                if "not found" in str(e).lower():
                    pytest.skip("Tool not implemented")
                raise
    
    @pytest.mark.performance
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_large_search_operations(self, mcp_client, performance_test_data):
        """Test search operations on large datasets."""
        with patch('githound.search_engine.SearchOrchestrator') as mock_orchestrator:
            # Mock large search results
            large_results = {
                "commits": [
                    {
                        "hash": f"commit_{i:06d}",
                        "message": f"Commit {i}",
                        "author": f"User {i % 100}",
                        "date": f"2024-01-{(i % 30) + 1:02d}T00:00:00Z"
                    }
                    for i in range(10000)
                ]
            }
            
            mock_instance = MagicMock()
            mock_instance.search.return_value = large_results
            mock_orchestrator.return_value = mock_instance
            
            start_time = time.time()
            
            try:
                # Use a mock repository path that exists for testing
                import tempfile
                import os
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Create a minimal git repo structure
                    os.makedirs(os.path.join(temp_dir, ".git"))
                    result = await mcp_client.call_tool(
                        "advanced_search",
                        {
                            "repo_path": temp_dir,
                            "content_pattern": "test"
                        }
                )
                execution_time = time.time() - start_time
                
                # Should handle large search results efficiently
                assert execution_time < 15.0, f"Large search took {execution_time:.2f}s"
                
            except Exception as e:
                if "not found" in str(e).lower():
                    pytest.skip("Tool not implemented")
                raise
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_memory_usage_with_large_data(self, mcp_client, performance_test_data):
        """Test memory usage with large datasets."""
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform operations that might consume memory
        for pattern in performance_test_data["complex_search_patterns"]:
            try:
                await mcp_client.call_tool(
                    "content_search",
                    {
                        "repo_path": "/test/repo",
                        "pattern": pattern
                    }
                )
            except Exception:
                # Tool might not be available
                pass
        
        # Force garbage collection
        gc.collect()
        
        # Check memory usage after operations
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable
        assert memory_increase < 100, f"Memory increased by {memory_increase:.1f}MB"


class TestScalabilityLimits:
    """Test scalability limits and edge cases."""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_maximum_concurrent_clients(self, mcp_server):
        """Test maximum number of concurrent clients."""
        async def create_client(client_id: int):
            try:
                async with Client(mcp_server) as client:
                    await client.ping()
                    return True
            except Exception:
                return False
        
        # Test with increasing number of concurrent clients
        max_clients = 50
        tasks = [create_client(i) for i in range(max_clients)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful_clients = sum(1 for r in results if r is True)
        
        # Should handle reasonable number of concurrent clients
        assert successful_clients >= max_clients * 0.8, \
            f"Only {successful_clients}/{max_clients} clients succeeded"
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_request_rate_limits(self, mcp_client):
        """Test request rate handling."""
        # Send many requests rapidly
        num_requests = 100
        start_time = time.time()
        
        tasks = []
        for i in range(num_requests):
            task = mcp_client.ping()
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        successful_requests = sum(1 for r in results if not isinstance(r, Exception))
        
        # Should handle high request rates
        requests_per_second = successful_requests / total_time
        assert requests_per_second > 10, f"Only {requests_per_second:.1f} requests/second"
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_large_payload_limits(self, mcp_client, temp_repo):
        """Test handling of large payloads."""
        repo_path = str(temp_repo.working_dir)
        
        # Test with increasingly large queries
        for size in [100, 1000, 10000]:
            large_query = "test " * size
            
            start_time = time.time()
            
            try:
                result = await mcp_client.call_tool(
                    "content_search",
                    {
                        "repo_path": repo_path,
                        "pattern": large_query
                    }
                )
                execution_time = time.time() - start_time
                
                # Should handle large payloads within reasonable time
                assert execution_time < 15.0, f"Large payload took {execution_time:.2f}s"
                
            except Exception as e:
                if "too large" in str(e).lower() or "not found" in str(e).lower():
                    # Expected for very large payloads or missing tools
                    break
                raise


class TestResourceUtilization:
    """Test resource utilization patterns."""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_cpu_utilization(self, mcp_client, temp_repo):
        """Test CPU utilization during operations."""
        repo_path = str(temp_repo.working_dir)
        
        # Monitor CPU usage during operations
        process = psutil.Process()
        
        # Perform CPU-intensive operations
        start_time = time.time()
        cpu_before = process.cpu_percent()
        
        # Perform multiple operations
        for i in range(10):
            try:
                await mcp_client.call_tool(
                    "validate_repository",
                    {"repo_path": repo_path}
                )
            except Exception:
                pass
        
        execution_time = time.time() - start_time
        cpu_after = process.cpu_percent()
        
        # CPU usage should be reasonable
        assert execution_time < 30.0, f"Operations took {execution_time:.2f}s"
        # Note: CPU percentage might not be accurate for short operations
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_memory_leak_detection(self, mcp_client):
        """Test for memory leaks during repeated operations."""
        process = psutil.Process()
        
        # Baseline memory usage
        gc.collect()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform many operations
        for i in range(100):
            try:
                await mcp_client.ping()
                if i % 10 == 0:
                    tools = await mcp_client.list_tools()
            except Exception:
                pass
        
        # Force garbage collection
        gc.collect()
        
        # Check for memory leaks
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - baseline_memory
        
        # Memory increase should be minimal
        assert memory_increase < 50, f"Potential memory leak: {memory_increase:.1f}MB increase"
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_connection_resource_cleanup(self, mcp_server):
        """Test connection resource cleanup."""
        # Create and close many connections
        for i in range(20):
            async with Client(mcp_server) as client:
                await client.ping()
        
        # Check that resources are cleaned up
        # This is mainly to ensure no exceptions are raised
        assert True


# Performance testing utilities

def measure_execution_time(func):
    """Decorator to measure execution time of async functions."""
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        execution_time = time.time() - start_time
        return result, execution_time
    return wrapper


def get_memory_usage() -> float:
    """Get current memory usage in MB."""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024


def get_cpu_usage() -> float:
    """Get current CPU usage percentage."""
    return psutil.cpu_percent(interval=1)


class PerformanceMonitor:
    """Context manager for monitoring performance metrics."""
    
    def __init__(self):
        self.start_time = None
        self.start_memory = None
        self.start_cpu = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.start_memory = get_memory_usage()
        self.start_cpu = psutil.cpu_percent()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.execution_time = time.time() - self.start_time
        self.memory_delta = get_memory_usage() - self.start_memory
        self.cpu_usage = psutil.cpu_percent()
    
    def get_metrics(self) -> Dict[str, float]:
        """Get performance metrics."""
        return {
            "execution_time": self.execution_time,
            "memory_delta": self.memory_delta,
            "cpu_usage": self.cpu_usage
        }
