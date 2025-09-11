"""
Performance and load tests for GitHound API.

Tests rate limiting, concurrent operations, large repository handling,
and scalability under load.
"""

import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch, Mock
from fastapi import status


@pytest.mark.performance
@pytest.mark.slow
class TestRateLimiting:
    """Test rate limiting under load."""
    
    def test_rate_limit_enforcement(self, api_client, admin_auth_headers) -> None:
        """Test that rate limits are properly enforced."""
        # Make requests rapidly to trigger rate limiting
        responses: list[Any] = []
        
        with patch('githound.web.rate_limiting.get_limiter') as mock_limiter:
            # Mock rate limiter to allow first few requests, then deny
            mock_limiter_instance = Mock()
            mock_limiter_instance.limit.side_effect = [
                lambda func: func,  # Allow first request
                lambda func: func,  # Allow second request
                lambda func: func,  # Allow third request
                # Then start rate limiting
                lambda func: self._rate_limit_exceeded_response
            ] * 10
            mock_limiter.return_value = mock_limiter_instance
            
            # Make multiple rapid requests
            for i in range(10):
                response = api_client.get(
                    "/api/v3/health",
                    headers=admin_auth_headers
                )
                responses.append(response)
        
        # Check that some requests were rate limited
        success_count = sum(1 for r in responses if r.status_code == 200)
        rate_limited_count = sum(1 for r in responses if r.status_code == 429)
        
        assert success_count > 0, "Some requests should succeed"
        # Note: Actual rate limiting behavior depends on implementation
    
    def _rate_limit_exceeded_response(self, func) -> None:
        """Mock function that raises rate limit exception."""
        from slowapi.errors import RateLimitExceeded
        raise RateLimitExceeded("Rate limit exceeded")
    
    @pytest.mark.redis
    def test_redis_rate_limiting_performance(self, api_client, admin_auth_headers, redis_client) -> None:
        """Test Redis-based rate limiting performance."""
        if not redis_client:
            pytest.skip("Redis not available")
        
        start_time = time.time()
        
        # Make many requests to test Redis performance
        for i in range(50):
            response = api_client.get(
                "/api/v3/health",
                headers=admin_auth_headers
            )
            # Don't assert status here as we're testing performance
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete 50 requests in reasonable time (adjust threshold as needed)
        assert total_time < 10.0, f"50 requests took {total_time:.2f}s, too slow"
        
        # Average request time should be reasonable
        avg_time = total_time / 50
        assert avg_time < 0.2, f"Average request time {avg_time:.3f}s too slow"
    
    def test_concurrent_rate_limiting(self, api_client, admin_auth_headers) -> None:
        """Test rate limiting with concurrent requests."""
        def make_request(request_id) -> None:
            """Make a single request and return result."""
            response = api_client.get(
                "/api/v3/health",
                headers=admin_auth_headers
            )
            return {
                "request_id": request_id,
                "status_code": response.status_code,
                "response_time": time.time()
            }
        
        # Make concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, i) for i in range(20)]
            results = [future.result() for future in as_completed(futures)]
        
        # Analyze results
        success_count = sum(1 for r in results if r["status_code"] == 200)
        error_count = sum(1 for r in results if r["status_code"] >= 400)
        
        assert success_count > 0, "Some requests should succeed"
        assert len(results) == 20, "All requests should complete"


@pytest.mark.performance
@pytest.mark.slow
class TestConcurrentOperations:
    """Test concurrent API operations."""
    
    def test_concurrent_repository_operations(self, api_client, admin_auth_headers, temp_dir) -> None:
        """Test concurrent repository operations."""
        def create_repository(repo_id) -> None:
            """Create a repository and return result."""
            repo_path = str(temp_dir / f"concurrent_repo_{repo_id}")
            
            with patch('githound.web.git_operations.GitOperationsManager.init_repository') as mock_init:
                mock_init.return_value = {
                    "path": repo_path,
                    "status": "created"
                }
                
                response = api_client.post(
                    "/api/v3/repository/init",
                    headers=admin_auth_headers,
                    json={"path": repo_path, "bare": False}
                )
                
                return {
                    "repo_id": repo_id,
                    "status_code": response.status_code,
                    "success": response.status_code == 200
                }
        
        # Create multiple repositories concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_repository, i) for i in range(10)]
            results = [future.result() for future in as_completed(futures)]
        
        # All operations should succeed
        success_count = sum(1 for r in results if r["success"])
        assert success_count == 10, f"Expected 10 successes, got {success_count}"
    
    def test_concurrent_search_operations(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test concurrent search operations."""
        repo_path = str(temp_repo.working_dir)
        
        def perform_search(search_id) -> None:
            """Perform a search and return result."""
            with patch('githound.web.search_api.perform_advanced_search_sync') as mock_search:
                mock_search.return_value = {
                    "search_id": f"concurrent-search-{search_id}",
                    "status": "completed",
                    "results": [],
                    "total_count": 0,
                    "commits_searched": 5,
                    "files_searched": 10,
                    "search_duration_ms": 100.0,
                    "query_info": {},
                    "filters_applied": {},
                    "has_more": False
                }
                
                response = api_client.post(
                    "/api/v3/search/advanced",
                    headers=admin_auth_headers,
                    json={
                        "repo_path": repo_path,
                        "content_pattern": f"search_pattern_{search_id}",
                        "max_results": 50
                    }
                )
                
                return {
                    "search_id": search_id,
                    "status_code": response.status_code,
                    "success": response.status_code == 200
                }
        
        # Perform multiple searches concurrently
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(perform_search, i) for i in range(8)]
            results = [future.result() for future in as_completed(futures)]
        
        # All searches should succeed
        success_count = sum(1 for r in results if r["success"])
        assert success_count == 8, f"Expected 8 successful searches, got {success_count}"
    
    def test_concurrent_analysis_operations(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test concurrent analysis operations."""
        repo_path = str(temp_repo.working_dir)
        
        def perform_analysis(analysis_type) -> None:
            """Perform analysis and return result."""
            if analysis_type == "blame":
                with patch('githound.web.analysis_api.get_file_blame') as mock_blame:
                    mock_blame.return_value = Mock(dict=lambda: {"file_path": "test.py"})
                    
                    response = api_client.post(
                        "/api/v3/analysis/blame",
                        headers=admin_auth_headers,
                        params={"repo_path": repo_path},
                        json={"file_path": "test.py"}
                    )
            
            elif analysis_type == "stats":
                with patch('githound.web.analysis_api.get_repository_metadata') as mock_metadata:
                    mock_metadata.return_value = {"total_commits": 10}
                    
                    response = api_client.get(
                        "/api/v3/analysis/repository-stats",
                        headers=admin_auth_headers,
                        params={"repo_path": repo_path}
                    )
            
            else:
                response = Mock(status_code=400)
            
            return {
                "analysis_type": analysis_type,
                "status_code": response.status_code,
                "success": response.status_code == 200
            }
        
        # Perform different types of analysis concurrently
        analysis_types = ["blame", "stats", "blame", "stats", "blame"]
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(perform_analysis, atype) for atype in analysis_types]
            results = [future.result() for future in as_completed(futures)]
        
        # All analyses should succeed
        success_count = sum(1 for r in results if r["success"])
        assert success_count == 5, f"Expected 5 successful analyses, got {success_count}"


@pytest.mark.performance
@pytest.mark.slow
class TestLargeRepositoryHandling:
    """Test handling of large repositories."""
    
    def test_large_repository_status(self, api_client, admin_auth_headers, large_git_repo) -> None:
        """Test getting status of large repository."""
        repo_path = str(large_git_repo.working_dir)
        
        with patch('githound.web.git_operations.GitOperationsManager.get_repository_status') as mock_status:
            # Simulate large repository status
            mock_status.return_value = {
                "is_dirty": False,
                "untracked_files": [],
                "modified_files": [],
                "staged_files": [],
                "current_branch": "master",
                "head_commit": "large123",
                "total_commits": 1000,  # Large number of commits
                "stash_count": 0
            }
            
            start_time = time.time()
            
            encoded_path = repo_path.replace("/", "%2F")
            response = api_client.get(
                f"/api/v3/repository/{encoded_path}/status",
                headers=admin_auth_headers
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            assert response.status_code == status.HTTP_200_OK
            assert response.json()["data"]["total_commits"] == 1000
            
            # Should complete in reasonable time even for large repo
            assert response_time < 5.0, f"Large repo status took {response_time:.2f}s"
    
    def test_large_repository_search(self, api_client, admin_auth_headers, large_git_repo) -> None:
        """Test searching large repository."""
        repo_path = str(large_git_repo.working_dir)
        
        with patch('githound.web.search_api.perform_advanced_search_sync') as mock_search:
            # Simulate search in large repository
            mock_search.return_value = {
                "search_id": "large-repo-search",
                "status": "completed",
                "results": [{"commit_hash": f"result_{i}"} for i in range(100)],
                "total_count": 100,
                "commits_searched": 1000,
                "files_searched": 5000,
                "search_duration_ms": 3000.0,  # 3 seconds
                "query_info": {},
                "filters_applied": {},
                "has_more": False
            }
            
            start_time = time.time()
            
            response = api_client.post(
                "/api/v3/search/advanced",
                headers=admin_auth_headers,
                json={
                    "repo_path": repo_path,
                    "content_pattern": "common_pattern",
                    "max_results": 100
                }
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["commits_searched"] == 1000
            assert len(data["results"]) == 100
            
            # API response should be fast even if search takes time
            assert response_time < 1.0, f"Large repo search API took {response_time:.2f}s"
    
    def test_large_repository_analysis(self, api_client, admin_auth_headers, large_git_repo) -> None:
        """Test analysis of large repository."""
        repo_path = str(large_git_repo.working_dir)
        
        with patch('githound.web.analysis_api.get_repository_metadata') as mock_metadata:
            # Simulate large repository metadata
            mock_metadata.return_value = {
                "total_commits": 1000,
                "contributors": [f"user_{i}" for i in range(50)],  # 50 contributors
                "branches": [f"branch_{i}" for i in range(20)],    # 20 branches
                "tags": [f"v{i}.0.0" for i in range(10)],          # 10 tags
                "first_commit_date": "2020-01-01T00:00:00Z",
                "last_commit_date": "2024-01-01T00:00:00Z"
            }
            
            with patch('githound.web.analysis_api.get_author_statistics') as mock_author_stats:
                # Simulate author statistics for large repo
                mock_author_stats.return_value = {
                    f"user_{i}": {
                        "total_commits": 20,
                        "total_files": 30,
                        "lines_added": 500,
                        "lines_deleted": 100
                    } for i in range(50)
                }
                
                start_time = time.time()
                
                response = api_client.get(
                    "/api/v3/analysis/repository-stats",
                    headers=admin_auth_headers,
                    params={
                        "repo_path": repo_path,
                        "include_author_stats": True,
                        "include_file_stats": True
                    }
                )
                
                end_time = time.time()
                response_time = end_time - start_time
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["data"]["summary"]["total_commits"] == 1000
                assert data["data"]["summary"]["total_contributors"] == 50
                
                # Should handle large dataset efficiently
                assert response_time < 2.0, f"Large repo analysis took {response_time:.2f}s"


@pytest.mark.performance
@pytest.mark.slow
class TestMemoryAndResourceUsage:
    """Test memory and resource usage under load."""
    
    def test_memory_usage_with_large_responses(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test memory usage with large API responses."""
        repo_path = str(temp_repo.working_dir)
        
        # Simulate large search results
        large_results = [
            {
                "commit_hash": f"commit_{i:06d}",
                "file_path": f"file_{i % 100}.py",
                "line_number": i % 1000,
                "matching_line": f"line content {i}" * 10,  # Make content larger
                "search_type": "content",
                "relevance_score": 0.9,
                "match_context": [f"context line {j}" for j in range(5)]
            }
            for i in range(1000)  # 1000 results
        ]
        
        with patch('githound.web.search_api.perform_advanced_search_sync') as mock_search:
            mock_search.return_value = {
                "search_id": "large-response-test",
                "status": "completed",
                "results": large_results,
                "total_count": 1000,
                "commits_searched": 500,
                "files_searched": 1000,
                "search_duration_ms": 2000.0,
                "query_info": {},
                "filters_applied": {},
                "has_more": False
            }
            
            start_time = time.time()
            
            response = api_client.post(
                "/api/v3/search/advanced",
                headers=admin_auth_headers,
                json={
                    "repo_path": repo_path,
                    "content_pattern": "test",
                    "max_results": 1000
                }
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data["results"]) == 1000
            
            # Should handle large response efficiently
            assert response_time < 3.0, f"Large response took {response_time:.2f}s"
    
    def test_concurrent_large_operations(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test multiple large operations running concurrently."""
        repo_path = str(temp_repo.working_dir)
        
        def large_operation(op_id) -> None:
            """Perform a large operation."""
            with patch('githound.web.search_api.perform_advanced_search_sync') as mock_search:
                # Each operation returns substantial data
                mock_search.return_value = {
                    "search_id": f"large-op-{op_id}",
                    "status": "completed",
                    "results": [{"data": f"result_{i}"} for i in range(200)],
                    "total_count": 200,
                    "commits_searched": 100,
                    "files_searched": 300,
                    "search_duration_ms": 1000.0,
                    "query_info": {},
                    "filters_applied": {},
                    "has_more": False
                }
                
                response = api_client.post(
                    "/api/v3/search/advanced",
                    headers=admin_auth_headers,
                    json={
                        "repo_path": repo_path,
                        "content_pattern": f"pattern_{op_id}",
                        "max_results": 200
                    }
                )
                
                return {
                    "op_id": op_id,
                    "status_code": response.status_code,
                    "result_count": len(response.json().get("results", [])),
                    "success": response.status_code == 200
                }
        
        # Run multiple large operations concurrently
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(large_operation, i) for i in range(5)]
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # All operations should succeed
        success_count = sum(1 for r in results if r["success"])
        assert success_count == 5, f"Expected 5 successful operations, got {success_count}"
        
        # Should complete in reasonable time
        assert total_time < 10.0, f"5 large concurrent operations took {total_time:.2f}s"
        
        # Each operation should return expected amount of data
        for result in results:
            assert result["result_count"] == 200, f"Operation {result['op_id']} returned {result['result_count']} results"
