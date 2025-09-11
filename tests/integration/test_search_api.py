"""
Integration tests for search API endpoints.

Tests advanced search, fuzzy search, historical search,
search status management, and WebSocket functionality.
"""

from unittest.mock import patch

import pytest
from fastapi import status


@pytest.mark.integration
class TestAdvancedSearch:
    """Test advanced search endpoints."""

    def test_advanced_search_synchronous(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test synchronous advanced search."""
        repo_path = str(temp_repo.working_dir)

        with patch('githound.web.search_api.perform_advanced_search_sync') as mock_search:
            mock_search.return_value = {
                "search_id": "search-123",
                "status": "completed",
                "results": [
                    {
                        "commit_hash": "abc123",
                        "file_path": "test_file.py",
                        "line_number": 10,
                        "matching_line": "def test_function() -> None:",
                        "search_type": "content",
                        "relevance_score": 0.95,
                        "match_context": ["", "def test_function() -> None:", "    return True"]
                    }
                ],
                "total_count": 1,
                "commits_searched": 5,
                "files_searched": 10,
                "search_duration_ms": 150.0,
                "query_info": {"content_pattern": "test_function"},
                "filters_applied": {},
                "has_more": False
            }

            response = api_client.post(
                "/api/v3/search/advanced",
                headers=admin_auth_headers,
                json={
                    "repo_path": repo_path,
                    "content_pattern": "test_function",
                    "case_sensitive": False,
                    "regex_mode": False,
                    "max_results": 100,
                    "include_context": True,
                    "context_lines": 3
                }
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["search_id"] == "search-123"
            assert data["status"] == "completed"
            assert len(data["results"]) == 1
            assert data["total_count"] == 1

    def test_advanced_search_background(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test background advanced search."""
        repo_path = str(temp_repo.working_dir)

        with patch('githound.web.search_api.perform_advanced_search') as mock_search:
            response = api_client.post(
                "/api/v3/search/advanced",
                headers=admin_auth_headers,
                json={
                    "repo_path": repo_path,
                    "content_pattern": "complex_search",
                    "search_history": True,
                    "max_commits": 1000,
                    "timeout_seconds": 600
                }
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "started"
            assert "search_id" in data
            assert data["results"] == []
            assert data["total_count"] == 0

    def test_advanced_search_with_filters(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test advanced search with filters."""
        repo_path = str(temp_repo.working_dir)

        with patch('githound.web.search_api.perform_advanced_search_sync') as mock_search:
            mock_search.return_value = {
                "search_id": "search-456",
                "status": "completed",
                "results": [],
                "total_count": 0,
                "commits_searched": 0,
                "files_searched": 0,
                "search_duration_ms": 50.0,
                "query_info": {},
                "filters_applied": {"min_commit_size": 100},
                "has_more": False
            }

            response = api_client.post(
                "/api/v3/search/advanced",
                headers=admin_auth_headers,
                json={
                    "repo_path": repo_path,
                    "author_pattern": "alice@example.com",
                    "date_from": "2024-01-01T00:00:00Z",
                    "date_to": "2024-12-31T23:59:59Z",
                    "file_extensions": ["py", "js"],
                    "fuzzy_search": True,
                    "fuzzy_threshold": 0.8
                }
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "completed"

    def test_advanced_search_invalid_repo(self, api_client, admin_auth_headers) -> None:
        """Test advanced search with invalid repository."""
        with patch('githound.web.search_api.validate_repo_path') as mock_validate:
            mock_validate.side_effect = Exception("Invalid repository")

            response = api_client.post(
                "/api/v3/search/advanced",
                headers=admin_auth_headers,
                json={
                    "repo_path": "/invalid/path",
                    "content_pattern": "test"
                }
            )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.integration
class TestFuzzySearch:
    """Test fuzzy search endpoints."""

    def test_fuzzy_search_success(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test successful fuzzy search."""
        repo_path = str(temp_repo.working_dir)

        with patch('githound.web.search_api.perform_advanced_search_sync') as mock_search:
            mock_search.return_value = {
                "search_id": "fuzzy-123",
                "status": "completed",
                "results": [
                    {
                        "commit_hash": "abc123",
                        "file_path": "test_file.py",
                        "line_number": 5,
                        "matching_line": "def search_function() -> None:",
                        "search_type": "fuzzy",
                        "relevance_score": 0.85,
                        "match_context": []
                    }
                ],
                "total_count": 1,
                "commits_searched": 3,
                "files_searched": 8,
                "search_duration_ms": 200.0,
                "query_info": {"fuzzy_search": True, "fuzzy_threshold": 0.8},
                "filters_applied": {},
                "has_more": False
            }

            response = api_client.get(
                "/api/v3/search/fuzzy",
                headers=admin_auth_headers,
                params={
                    "repo_path": repo_path,
                    "pattern": "searhc",  # Typo in "search"
                    "threshold": 0.8,
                    "max_distance": 2
                }
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "completed"
            assert len(data["results"]) == 1
            assert data["query_info"]["fuzzy_search"] is True

    def test_fuzzy_search_with_file_types(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test fuzzy search with file type filtering."""
        repo_path = str(temp_repo.working_dir)

        with patch('githound.web.search_api.perform_advanced_search_sync') as mock_search:
            mock_search.return_value = {
                "search_id": "fuzzy-456",
                "status": "completed",
                "results": [],
                "total_count": 0,
                "commits_searched": 2,
                "files_searched": 3,
                "search_duration_ms": 100.0,
                "query_info": {},
                "filters_applied": {},
                "has_more": False
            }

            response = api_client.get(
                "/api/v3/search/fuzzy",
                headers=admin_auth_headers,
                params={
                    "repo_path": repo_path,
                    "pattern": "functoin",  # Typo in "function"
                    "threshold": 0.7,
                    "file_types": ["py", "js"]
                }
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "completed"


@pytest.mark.integration
class TestHistoricalSearch:
    """Test historical search endpoints."""

    def test_historical_search_synchronous(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test synchronous historical search."""
        repo_path = str(temp_repo.working_dir)

        with patch('githound.web.search_api.perform_advanced_search_sync') as mock_search:
            mock_search.return_value = {
                "search_id": "historical-123",
                "status": "completed",
                "results": [
                    {
                        "commit_hash": "old123",
                        "file_path": "legacy_file.py",
                        "line_number": 15,
                        "matching_line": "deprecated_function()",
                        "search_type": "content",
                        "relevance_score": 0.9,
                        "match_context": []
                    }
                ],
                "total_count": 1,
                "commits_searched": 100,
                "files_searched": 250,
                "search_duration_ms": 5000.0,
                "query_info": {"search_history": True},
                "filters_applied": {},
                "has_more": False
            }

            response = api_client.get(
                "/api/v3/search/historical",
                headers=admin_auth_headers,
                params={
                    "repo_path": repo_path,
                    "pattern": "deprecated",
                    "max_commits": 100,
                    "date_from": "2023-01-01T00:00:00Z"
                }
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "completed"
            assert data["commits_searched"] == 100

    def test_historical_search_background(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test background historical search."""
        repo_path = str(temp_repo.working_dir)

        with patch('githound.web.search_api.perform_advanced_search') as mock_search:
            response = api_client.get(
                "/api/v3/search/historical",
                headers=admin_auth_headers,
                params={
                    "repo_path": repo_path,
                    "pattern": "large_search",
                    "max_commits": 5000
                }
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "started"
            assert "search_id" in data


@pytest.mark.integration
class TestSearchManagement:
    """Test search status and management endpoints."""

    def test_get_search_status_success(self, api_client, admin_auth_headers) -> None:
        """Test getting search status."""
        search_id = "test-search-123"

        with patch('githound.web.search_api.active_searches', {
            search_id: {
                "id": search_id,
                "status": "running",
                "progress": 0.5,
                "message": "Searching files...",
                "results_count": 10,
                "started_at": "2024-01-01T00:00:00Z",
                "user_id": "test_admin"
            }
        }):
            response = api_client.get(
                f"/api/v3/search/{search_id}/status",
                headers=admin_auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["search_id"] == search_id
            assert data["status"] == "running"
            assert data["progress"] == 0.5
            assert data["results_count"] == 10

    def test_get_search_status_not_found(self, api_client, admin_auth_headers) -> None:
        """Test getting status for non-existent search."""
        response = api_client.get(
            "/api/v3/search/nonexistent-search/status",
            headers=admin_auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_search_status_access_denied(self, api_client, user_auth_headers) -> None:
        """Test getting status for another user's search."""
        search_id = "other-user-search"

        with patch('githound.web.search_api.active_searches', {
            search_id: {
                "id": search_id,
                "status": "completed",
                "user_id": "other_user"
            }
        }):
            response = api_client.get(
                f"/api/v3/search/{search_id}/status",
                headers=user_auth_headers
            )

            assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_search_results_success(self, api_client, admin_auth_headers) -> None:
        """Test getting search results."""
        search_id = "completed-search-123"

        with patch('githound.web.search_api.active_searches', {
            search_id: {
                "id": search_id,
                "status": "completed",
                "user_id": "test_admin",
                "results": [
                    {"commit_hash": "abc123", "file_path": "file1.py"},
                    {"commit_hash": "def456", "file_path": "file2.py"},
                    {"commit_hash": "ghi789", "file_path": "file3.py"}
                ],
                "commits_searched": 10,
                "files_searched": 25,
                "search_duration_ms": 1500.0,
                "query_info": {"content_pattern": "test"},
                "filters_applied": {}
            }
        }):
            response = api_client.get(
                f"/api/v3/search/{search_id}/results",
                headers=admin_auth_headers,
                params={"page": 1, "page_size": 2}
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["search_id"] == search_id
            assert data["status"] == "completed"
            assert len(data["results"]) == 2  # Paginated
            assert data["total_count"] == 3
            assert data["page"] == 1
            assert data["page_size"] == 2
            assert data["has_more"] is True

    def test_get_search_results_not_completed(self, api_client, admin_auth_headers) -> None:
        """Test getting results for incomplete search."""
        search_id = "running-search-123"

        with patch('githound.web.search_api.active_searches', {
            search_id: {
                "id": search_id,
                "status": "running",
                "user_id": "test_admin"
            }
        }):
            response = api_client.get(
                f"/api/v3/search/{search_id}/results",
                headers=admin_auth_headers
            )

            assert response.status_code == status.HTTP_202_ACCEPTED

    def test_cancel_search_success(self, api_client, admin_auth_headers) -> None:
        """Test successful search cancellation."""
        search_id = "running-search-456"

        with patch('githound.web.search_api.active_searches', {
            search_id: {
                "id": search_id,
                "status": "running",
                "user_id": "test_admin"
            }
        }) as mock_searches:
            response = api_client.delete(
                f"/api/v3/search/{search_id}",
                headers=admin_auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["status"] == "cancelled"

    def test_cancel_search_already_completed(self, api_client, admin_auth_headers) -> None:
        """Test cancelling already completed search."""
        search_id = "completed-search-789"

        with patch('githound.web.search_api.active_searches', {
            search_id: {
                "id": search_id,
                "status": "completed",
                "user_id": "test_admin"
            }
        }):
            response = api_client.delete(
                f"/api/v3/search/{search_id}",
                headers=admin_auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert "already completed" in data["message"]

    def test_list_active_searches(self, api_client, admin_auth_headers) -> None:
        """Test listing active searches."""
        with patch('githound.web.search_api.active_searches', {
            "search-1": {
                "id": "search-1",
                "status": "running",
                "progress": 0.3,
                "message": "Searching...",
                "results_count": 5,
                "started_at": "2024-01-01T00:00:00Z",
                "user_id": "test_admin"
            },
            "search-2": {
                "id": "search-2",
                "status": "completed",
                "progress": 1.0,
                "message": "Completed",
                "results_count": 15,
                "started_at": "2024-01-01T01:00:00Z",
                "user_id": "test_admin"
            }
        }):
            response = api_client.get(
                "/api/v3/search/active",
                headers=admin_auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]["searches"]) == 2
            assert data["data"]["total_count"] == 2


@pytest.mark.integration
class TestSearchValidation:
    """Test search input validation."""

    def test_advanced_search_missing_repo_path(self, api_client, admin_auth_headers) -> None:
        """Test advanced search without repository path."""
        response = api_client.post(
            "/api/v3/search/advanced",
            headers=admin_auth_headers,
            json={
                "content_pattern": "test"
                # Missing repo_path
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_fuzzy_search_invalid_threshold(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test fuzzy search with invalid threshold."""
        repo_path = str(temp_repo.working_dir)

        response = api_client.get(
            "/api/v3/search/fuzzy",
            headers=admin_auth_headers,
            params={
                "repo_path": repo_path,
                "pattern": "test",
                "threshold": 1.5  # Invalid: > 1.0
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_advanced_search_invalid_max_results(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test advanced search with invalid max_results."""
        repo_path = str(temp_repo.working_dir)

        response = api_client.post(
            "/api/v3/search/advanced",
            headers=admin_auth_headers,
            json={
                "repo_path": repo_path,
                "content_pattern": "test",
                "max_results": 50000  # Invalid: > 10000
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
