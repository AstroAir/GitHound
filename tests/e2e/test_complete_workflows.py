"""
End-to-end tests for complete GitHound API workflows.

Tests complete user journeys including repository setup, analysis,
search operations, and export functionality.
"""

import pytest
import time
from unittest.mock import patch, Mock
from fastapi import status


@pytest.mark.e2e
class TestRepositoryWorkflow:
    """Test complete repository management workflow."""

    def test_complete_repository_lifecycle(self, api_client, admin_auth_headers, temp_dir) -> None:
        """Test complete repository lifecycle from init to analysis."""
        repo_path = str(temp_dir / "test_repo")

        # Step 1: Initialize repository
        with patch('githound.web.git_operations.GitOperationsManager.init_repository') as mock_init:
            mock_init.return_value = {
                "path": repo_path,
                "bare": False,
                "status": "created",
                "git_dir": f"{repo_path}/.git",
                "working_dir": repo_path
            }

            init_response = api_client.post(
                "/api/v3/repository/init",
                headers=admin_auth_headers,
                json={"path": repo_path, "bare": False}
            )

            assert init_response.status_code == status.HTTP_200_OK
            assert init_response.json()["data"]["status"] == "created"

        # Step 2: Get repository status
        with patch('githound.web.git_operations.GitOperationsManager.get_repository_status') as mock_status:
            mock_status.return_value = {
                "is_dirty": False,
                "untracked_files": [],
                "modified_files": [],
                "staged_files": [],
                "current_branch": "main",
                "head_commit": "abc123",
                "total_commits": 1
            }

            encoded_path = repo_path.replace("/", "%2F")
            status_response = api_client.get(
                f"/api/v3/repository/{encoded_path}/status",
                headers=admin_auth_headers
            )

            assert status_response.status_code == status.HTTP_200_OK
            assert status_response.json()["data"]["current_branch"] == "main"

        # Step 3: Create a branch
        with patch('githound.web.git_operations.GitOperationsManager.create_branch') as mock_create_branch:
            mock_create_branch.return_value = {
                "name": "feature-branch",
                "commit_hash": "def456",
                "checked_out": True,
                "status": "created"
            }

            branch_response = api_client.post(
                f"/api/v3/repository/{encoded_path}/branches",
                headers=admin_auth_headers,
                json={
                    "repo_path": repo_path,
                    "branch_name": "feature-branch",
                    "checkout": True
                }
            )

            assert branch_response.status_code == status.HTTP_200_OK
            assert branch_response.json()["data"]["name"] == "feature-branch"

        # Step 4: Create a commit
        with patch('githound.web.git_operations.GitOperationsManager.create_commit') as mock_commit:
            mock_commit.return_value = {
                "commit_hash": "ghi789",
                "message": "Add new feature",
                "author": "Test User <test@example.com>",
                "files_changed": 2,
                "status": "created"
            }

            commit_response = api_client.post(
                f"/api/v3/repository/{encoded_path}/commits",
                headers=admin_auth_headers,
                json={
                    "repo_path": repo_path,
                    "message": "Add new feature",
                    "all_files": True
                }
            )

            assert commit_response.status_code == status.HTTP_200_OK
            assert commit_response.json(
            )["data"]["message"] == "Add new feature"

        # Step 5: Analyze repository statistics
        with patch('githound.web.analysis_api.get_repository_metadata') as mock_metadata:
            mock_metadata.return_value = {
                "total_commits": 2,
                "contributors": ["Test User"],
                "branches": ["main", "feature-branch"],
                "tags": []
            }

            stats_response = api_client.get(
                "/api/v3/analysis/repository-stats",
                headers=admin_auth_headers,
                params={"repo_path": repo_path}
            )

            assert stats_response.status_code == status.HTTP_200_OK
            assert stats_response.json(
            )["data"]["summary"]["total_commits"] == 2

    def test_clone_and_analyze_workflow(self, api_client, admin_auth_headers, temp_dir) -> None:
        """Test cloning repository and performing analysis."""
        clone_path = str(temp_dir / "cloned_repo")
        test_url = "https://github.com/test/repo.git"

        # Step 1: Start clone operation
        with patch('githound.web.comprehensive_api.perform_clone_operation'):
            clone_response = api_client.post(
                "/api/v3/repository/clone",
                headers=admin_auth_headers,
                json={
                    "url": test_url,
                    "path": clone_path,
                    "branch": "main"
                }
            )

            assert clone_response.status_code == status.HTTP_200_OK
            operation_id = clone_response.json()["data"]["operation_id"]

        # Step 2: Check operation status
        with patch('githound.web.comprehensive_api.active_operations', {
            operation_id: {
                "type": "clone",
                "status": "completed",
                "result": {
                    "path": clone_path,
                    "url": test_url,
                    "status": "cloned"
                }
            }
        }):
            status_response = api_client.get(
                f"/api/v3/operations/{operation_id}/status",
                headers=admin_auth_headers
            )

            assert status_response.status_code == status.HTTP_200_OK
            assert status_response.json()["data"]["status"] == "completed"

        # Step 3: Perform blame analysis
        with patch('githound.web.analysis_api.get_file_blame') as mock_blame:
            mock_blame.return_value = Mock(
                dict=lambda: {
                    "file_path": "README.md",
                    "line_blame": {
                        1: {
                            "commit_hash": "abc123",
                            "author": "Original Author",
                            "line_content": "# Test Repository"
                        }
                    }
                }
            )

            blame_response = api_client.post(
                "/api/v3/analysis/blame",
                headers=admin_auth_headers,
                params={"repo_path": clone_path},
                json={"file_path": "README.md"}
            )

            assert blame_response.status_code == status.HTTP_200_OK
            assert "line_blame" in blame_response.json()["data"]


@pytest.mark.e2e
class TestSearchWorkflow:
    """Test complete search workflow."""

    def test_search_and_export_workflow(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test searching repository and exporting results."""
        repo_path = str(temp_repo.working_dir)

        # Step 1: Perform advanced search
        with patch('githound.web.search_api.perform_advanced_search_sync') as mock_search:
            mock_search.return_value = {
                "search_id": "search-workflow-123",
                "status": "completed",
                "results": [
                    {
                        "commit_hash": "abc123",
                        "file_path": "src/main.py",
                        "line_number": 10,
                        "matching_line": "def main() -> None:",
                        "search_type": "content",
                        "relevance_score": 0.95
                    },
                    {
                        "commit_hash": "def456",
                        "file_path": "src/utils.py",
                        "line_number": 5,
                        "matching_line": "def helper_function() -> None:",
                        "search_type": "content",
                        "relevance_score": 0.88
                    }
                ],
                "total_count": 2,
                "commits_searched": 10,
                "files_searched": 25,
                "search_duration_ms": 250.0,
                "query_info": {"content_pattern": "def "},
                "filters_applied": {},
                "has_more": False
            }

            search_response = api_client.post(
                "/api/v3/search/advanced",
                headers=admin_auth_headers,
                json={
                    "repo_path": repo_path,
                    "content_pattern": "def ",
                    "file_extensions": ["py"],
                    "max_results": 100
                }
            )

            assert search_response.status_code == status.HTTP_200_OK
            search_data = search_response.json()
            assert search_data["status"] == "completed"
            assert len(search_data["results"]) == 2
            search_id = search_data["search_id"]

        # Step 2: Export search results
        with patch('githound.web.integration_api.perform_export_operation'):
            export_response = api_client.post(
                "/api/v3/integration/export",
                headers=admin_auth_headers,
                json={
                    "export_type": "search_results",
                    "format": "JSON",
                    "search_id": search_id,
                    "include_metadata": True
                }
            )

            assert export_response.status_code == status.HTTP_200_OK
            export_data = export_response.json()
            assert export_data["data"]["export_type"] == "search_results"
            export_id = export_data["data"]["export_id"]

        # Step 3: Check export status
        with patch('githound.web.integration_api.active_exports', {
            export_id: {
                "id": export_id,
                "status": "completed",
                "user_id": "test_admin",
                "file_path": "/tmp/export.json",
                "filename": "search_results.json"
            }
        }):
            export_status_response = api_client.get(
                f"/api/v3/integration/export/{export_id}/status",
                headers=admin_auth_headers
            )

            assert export_status_response.status_code == status.HTTP_200_OK
            assert export_status_response.json(
            )["data"]["status"] == "completed"

    def test_fuzzy_search_workflow(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test fuzzy search workflow with typos."""
        repo_path = str(temp_repo.working_dir)

        # Step 1: Perform fuzzy search with typo
        with patch('githound.web.search_api.perform_advanced_search_sync') as mock_search:
            mock_search.return_value = {
                "search_id": "fuzzy-workflow-456",
                "status": "completed",
                "results": [
                    {
                        "commit_hash": "abc123",
                        "file_path": "test.py",
                        "line_number": 1,
                        "matching_line": "def function() -> None:",
                        "search_type": "fuzzy",
                        "relevance_score": 0.85
                    }
                ],
                "total_count": 1,
                "commits_searched": 5,
                "files_searched": 12,
                "search_duration_ms": 180.0,
                "query_info": {"fuzzy_search": True, "fuzzy_threshold": 0.8},
                "filters_applied": {},
                "has_more": False
            }

            fuzzy_response = api_client.get(
                "/api/v3/search/fuzzy",
                headers=admin_auth_headers,
                params={
                    "repo_path": repo_path,
                    "pattern": "functoin",  # Typo in "function"
                    "threshold": 0.8,
                    "max_distance": 2
                }
            )

            assert fuzzy_response.status_code == status.HTTP_200_OK
            fuzzy_data = fuzzy_response.json()
            assert fuzzy_data["status"] == "completed"
            assert len(fuzzy_data["results"]) == 1
            assert fuzzy_data["query_info"]["fuzzy_search"] is True

    def test_historical_search_workflow(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test historical search workflow."""
        repo_path = str(temp_repo.working_dir)

        # Step 1: Start historical search
        with patch('githound.web.search_api.perform_advanced_search') as mock_search:
            historical_response = api_client.get(
                "/api/v3/search/historical",
                headers=admin_auth_headers,
                params={
                    "repo_path": repo_path,
                    "pattern": "deprecated",
                    "max_commits": 1000,
                    "date_from": "2023-01-01T00:00:00Z"
                }
            )

            assert historical_response.status_code == status.HTTP_200_OK
            historical_data = historical_response.json()
            assert historical_data["status"] == "started"
            search_id = historical_data["search_id"]

        # Step 2: Check search progress
        with patch('githound.web.search_api.active_searches', {
            search_id: {
                "id": search_id,
                "status": "running",
                "progress": 0.6,
                "message": "Searching historical commits...",
                "results_count": 5,
                "started_at": "2024-01-01T00:00:00Z",
                "user_id": "test_admin"
            }
        }):
            progress_response = api_client.get(
                f"/api/v3/search/{search_id}/status",
                headers=admin_auth_headers
            )

            assert progress_response.status_code == status.HTTP_200_OK
            progress_data = progress_response.json()
            assert progress_data["status"] == "running"
            assert progress_data["progress"] == 0.6

        # Step 3: Get completed results
        with patch('githound.web.search_api.active_searches', {
            search_id: {
                "id": search_id,
                "status": "completed",
                "user_id": "test_admin",
                "results": [
                    {"commit_hash": "old123", "file_path": "legacy.py"},
                    {"commit_hash": "old456", "file_path": "deprecated.py"}
                ],
                "commits_searched": 1000,
                "files_searched": 2500,
                "search_duration_ms": 15000.0,
                "query_info": {"search_history": True},
                "filters_applied": {}
            }
        }):
            results_response = api_client.get(
                f"/api/v3/search/{search_id}/results",
                headers=admin_auth_headers,
                params={"page": 1, "page_size": 10}
            )

            assert results_response.status_code == status.HTTP_200_OK
            results_data = results_response.json()
            assert results_data["status"] == "completed"
            assert len(results_data["results"]) == 2
            assert results_data["commits_searched"] == 1000


@pytest.mark.e2e
class TestWebhookWorkflow:
    """Test webhook integration workflow."""

    def test_webhook_setup_and_trigger_workflow(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test setting up webhooks and triggering events."""
        repo_path = str(temp_repo.working_dir)

        # Step 1: Create webhook endpoint
        with patch('githound.web.webhooks.WebhookManager.add_endpoint') as mock_add:
            mock_add.return_value = "webhook-123"

            webhook_response = api_client.post(
                "/api/v3/integration/webhooks",
                headers=admin_auth_headers,
                json={
                    "url": "https://example.com/webhook",
                    "events": ["repository.created", "branch.created", "commit.created"],
                    "secret": "webhook-secret",
                    "active": True
                }
            )

            assert webhook_response.status_code == status.HTTP_200_OK
            webhook_data = webhook_response.json()
            assert webhook_data["data"]["url"] == "https://example.com/webhook"
            webhook_id = webhook_data["data"]["webhook_id"]

        # Step 2: List webhooks
        with patch('githound.web.webhooks.WebhookManager.list_endpoints') as mock_list:
            mock_endpoint = Mock()
            mock_endpoint.id = webhook_id
            mock_endpoint.url = "https://example.com/webhook"
            mock_endpoint.events = ["repository.created",
                                    "branch.created", "commit.created"]
            mock_endpoint.active = True
            mock_endpoint.created_at = "2024-01-01T00:00:00Z"
            mock_endpoint.last_delivery = None
            mock_endpoint.failure_count = 0
            mock_list.return_value = [mock_endpoint]

            with patch('githound.web.webhooks.WebhookManager.get_endpoint_stats') as mock_stats:
                mock_stats.return_value = {
                    "total_deliveries": 0,
                    "successful_deliveries": 0,
                    "failed_deliveries": 0,
                    "success_rate": 0
                }

                list_response = api_client.get(
                    "/api/v3/integration/webhooks",
                    headers=admin_auth_headers
                )

                assert list_response.status_code == status.HTTP_200_OK
                list_data = list_response.json()
                assert len(list_data["data"]["webhooks"]) == 1

        # Step 3: Trigger webhook event by creating branch
        with patch('githound.web.git_operations.GitOperationsManager.create_branch') as mock_create:
            mock_create.return_value = {
                "name": "webhook-test-branch",
                "commit_hash": "webhook123",
                "status": "created"
            }

            with patch('githound.web.webhooks.webhook_manager.trigger_event') as mock_trigger:
                mock_trigger.return_value = ["delivery-456"]

                encoded_path = repo_path.replace("/", "%2F")
                branch_response = api_client.post(
                    f"/api/v3/repository/{encoded_path}/branches",
                    headers=admin_auth_headers,
                    json={
                        "repo_path": repo_path,
                        "branch_name": "webhook-test-branch",
                        "checkout": False
                    }
                )

                assert branch_response.status_code == status.HTTP_200_OK
                # Webhook should be triggered automatically
                mock_trigger.assert_called_once()


@pytest.mark.e2e
class TestBatchOperationsWorkflow:
    """Test batch operations workflow."""

    def test_batch_repository_analysis(self, api_client, admin_auth_headers, temp_dir) -> None:
        """Test batch analysis across multiple repositories."""
        repo_paths = [
            str(temp_dir / "repo1"),
            str(temp_dir / "repo2"),
            str(temp_dir / "repo3")
        ]

        # Step 1: Start batch operation
        with patch('githound.web.integration_api.perform_batch_operation'):
            batch_response = api_client.post(
                "/api/v3/integration/batch",
                headers=admin_auth_headers,
                json={
                    "operation_type": "status_check",
                    "repositories": repo_paths,
                    "parallel": True,
                    "max_concurrent": 2
                }
            )

            assert batch_response.status_code == status.HTTP_200_OK
            batch_data = batch_response.json()
            assert batch_data["data"]["operation_type"] == "status_check"
            assert batch_data["data"]["repository_count"] == 3
            batch_id = batch_data["data"]["batch_id"]

        # Step 2: Check batch status
        with patch('githound.web.integration_api.batch_operations', {
            batch_id: {
                "id": batch_id,
                "status": "running",
                "progress": 0.67,
                "message": "Processing repositories...",
                "user_id": "test_admin",
                "operation_type": "status_check",
                "total_count": 3,
                "completed_count": 2,
                "failed_count": 0
            }
        }):
            status_response = api_client.get(
                f"/api/v3/integration/batch/{batch_id}/status",
                headers=admin_auth_headers
            )

            assert status_response.status_code == status.HTTP_200_OK
            status_data = status_response.json()
            assert status_data["data"]["status"] == "running"
            assert status_data["data"]["completed_count"] == 2

        # Step 3: Get batch results
        with patch('githound.web.integration_api.batch_operations', {
            batch_id: {
                "id": batch_id,
                "status": "completed",
                "user_id": "test_admin",
                "operation_type": "status_check",
                "total_count": 3,
                "completed_count": 3,
                "failed_count": 0,
                "results": {
                    repo_paths[0]: {"status": "success", "data": {"is_dirty": False}},
                    repo_paths[1]: {"status": "success", "data": {"is_dirty": True}},
                    repo_paths[2]: {"status": "success",
                                    "data": {"is_dirty": False}}
                }
            }
        }):
            results_response = api_client.get(
                f"/api/v3/integration/batch/{batch_id}/results",
                headers=admin_auth_headers
            )

            assert results_response.status_code == status.HTTP_200_OK
            results_data = results_response.json()
            assert results_data["data"]["status"] == "completed"
            assert len(results_data["data"]["results"]) == 3
            assert results_data["data"]["summary"]["success_rate"] == 1.0


@pytest.mark.e2e
class TestErrorHandlingWorkflow:
    """Test error handling in complete workflows."""

    def test_repository_error_recovery(self, api_client, admin_auth_headers, temp_dir) -> None:
        """Test error handling and recovery in repository operations."""
        repo_path = str(temp_dir / "error_repo")

        # Step 1: Try to initialize repository in invalid location
        with patch('githound.web.git_operations.GitOperationsManager.init_repository') as mock_init:
            mock_init.side_effect = Exception("Permission denied")

            init_response = api_client.post(
                "/api/v3/repository/init",
                headers=admin_auth_headers,
                json={"path": "/invalid/permission/path", "bare": False}
            )

            assert init_response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Permission denied" in init_response.json()["detail"]

        # Step 2: Retry with valid path
        with patch('githound.web.git_operations.GitOperationsManager.init_repository') as mock_init:
            mock_init.return_value = {
                "path": repo_path,
                "status": "created"
            }

            retry_response = api_client.post(
                "/api/v3/repository/init",
                headers=admin_auth_headers,
                json={"path": repo_path, "bare": False}
            )

            assert retry_response.status_code == status.HTTP_200_OK
            assert retry_response.json()["data"]["status"] == "created"

    def test_search_timeout_handling(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test handling of search timeouts."""
        repo_path = str(temp_repo.working_dir)

        # Step 1: Start search that will timeout
        with patch('githound.web.search_api.perform_advanced_search') as mock_search:
            search_response = api_client.post(
                "/api/v3/search/advanced",
                headers=admin_auth_headers,
                json={
                    "repo_path": repo_path,
                    "content_pattern": "complex_pattern",
                    "timeout_seconds": 1  # Very short timeout
                }
            )

            assert search_response.status_code == status.HTTP_200_OK
            search_id = search_response.json()["search_id"]

        # Step 2: Check search status shows timeout
        with patch('githound.web.search_api.active_searches', {
            search_id: {
                "id": search_id,
                "status": "error",
                "message": "Search timed out",
                "error": "Operation timed out after 1 seconds",
                "user_id": "test_admin"
            }
        }):
            status_response = api_client.get(
                f"/api/v3/search/{search_id}/status",
                headers=admin_auth_headers
            )

            assert status_response.status_code == status.HTTP_200_OK
            status_data = status_response.json()
            assert status_data["status"] == "error"
            assert "timed out" in status_data["message"]
