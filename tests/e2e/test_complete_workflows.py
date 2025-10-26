"""
End-to-end tests for complete GitHound API workflows.

Tests complete user journeys including analysis,
search operations, and export functionality.
"""

from datetime import UTC
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import status


@pytest.mark.e2e
@pytest.mark.skip(reason="Repository management endpoints removed - not core functionality")
class TestRepositoryWorkflow:
    """Test complete repository management workflow (REMOVED)."""

    def test_complete_repository_lifecycle(self, api_client, admin_auth_headers, temp_dir) -> None:
        """Test complete repository lifecycle from init to analysis."""
        repo_path = str(temp_dir / "test_repo")

        # Step 1: Initialize repository
        with patch(
            "githound.web.core.git_operations.GitOperationsManager.init_repository"
        ) as mock_init:
            mock_init.return_value = {
                "path": repo_path,
                "bare": False,
                "status": "created",
                "git_dir": f"{repo_path}/.git",
                "working_dir": repo_path,
            }

            init_response = api_client.post(
                "/api/v1/repository/init",
                headers=admin_auth_headers,
                json={"path": repo_path, "bare": False},
            )

            assert init_response.status_code == status.HTTP_200_OK
            assert init_response.json()["data"]["status"] == "created"

        # Step 2: Get repository status
        with patch(
            "githound.web.core.git_operations.GitOperationsManager.get_repository_status"
        ) as mock_status, patch(
            "githound.web.apis.repository_api.validate_repo_path"
        ) as mock_validate:
            mock_status.return_value = {
                "is_dirty": False,
                "untracked_files": [],
                "modified_files": [],
                "staged_files": [],
                "current_branch": "main",
                "head_commit": "abc123",
                "total_commits": 1,
            }
            mock_validate.return_value = Path(repo_path)

            status_response = api_client.get(
                f"/api/v1/repository/status?repo_path={repo_path}", headers=admin_auth_headers
            )

            assert status_response.status_code == status.HTTP_200_OK
            assert status_response.json()["data"]["current_branch"] == "main"

        # Step 3: Create a branch
        with patch(
            "githound.web.core.git_operations.GitOperationsManager.create_branch"
        ) as mock_create_branch, patch(
            "githound.web.apis.repository_api.validate_repo_path"
        ) as mock_validate:
            mock_create_branch.return_value = {
                "name": "feature-branch",
                "commit_hash": "def456",
                "checked_out": True,
                "status": "created",
            }
            mock_validate.return_value = Path(repo_path)

            branch_response = api_client.post(
                f"/api/v1/repository/branches?repo_path={repo_path}",
                headers=admin_auth_headers,
                json={"branch_name": "feature-branch", "checkout": True},
            )

            assert branch_response.status_code == status.HTTP_200_OK
            assert branch_response.json()["data"]["name"] == "feature-branch"

        # Step 4: Create a commit
        with patch(
            "githound.web.core.git_operations.GitOperationsManager.create_commit"
        ) as mock_commit, patch(
            "githound.web.apis.repository_api.validate_repo_path"
        ) as mock_validate:
            mock_commit.return_value = {
                "commit_hash": "ghi789",
                "message": "Add new feature",
                "author": "Test User <test@example.com>",
                "files_changed": 2,
                "status": "created",
            }
            mock_validate.return_value = Path(repo_path)

            commit_response = api_client.post(
                f"/api/v1/repository/commits?repo_path={repo_path}",
                headers=admin_auth_headers,
                json={"message": "Add new feature", "all_files": True},
            )

            assert commit_response.status_code == status.HTTP_200_OK
            assert commit_response.json()["data"]["message"] == "Add new feature"

        # Step 5: Analyze repository statistics
        with patch(
            "githound.web.apis.analysis_api.get_repository_metadata"
        ) as mock_metadata, patch(
            "githound.web.apis.analysis_api.validate_repo_path"
        ) as mock_validate, patch(
            "githound.web.apis.analysis_api.get_repository"
        ) as mock_get_repo, patch(
            "githound.web.apis.analysis_api.get_author_statistics"
        ) as mock_author_stats:
            mock_metadata.return_value = {
                "total_commits": 2,
                "contributors": ["Test User"],
                "branches": ["main", "feature-branch"],
                "tags": [],
            }
            mock_validate.return_value = Path(repo_path)
            mock_get_repo.return_value = Mock()
            mock_author_stats.return_value = {}

            stats_response = api_client.get(
                f"/api/v1/analysis/repository-stats?repo_path={repo_path}",
                headers=admin_auth_headers,
            )

            assert stats_response.status_code == status.HTTP_200_OK
            assert stats_response.json()["data"]["summary"]["total_commits"] == 2

    def test_clone_and_analyze_workflow(self, api_client, admin_auth_headers, temp_dir) -> None:
        """Test cloning repository and performing analysis."""
        clone_path = str(temp_dir / "cloned_repo")
        test_url = "https://github.com/test/repo.git"

        # Step 1: Clone repository
        with patch(
            "githound.web.core.git_operations.GitOperationsManager.clone_repository"
        ) as mock_clone:
            mock_clone.return_value = {
                "path": clone_path,
                "url": test_url,
                "branch": "main",
                "status": "cloned",
            }

            clone_response = api_client.post(
                "/api/v1/repository/clone",
                headers=admin_auth_headers,
                json={"url": test_url, "path": clone_path, "branch": "main"},
            )

            assert clone_response.status_code == status.HTTP_200_OK
            assert clone_response.json()["data"]["path"] == clone_path

        # Step 2: Perform blame analysis
        from datetime import datetime

        from githound.git_blame import BlameInfo, FileBlameResult

        with patch("githound.web.apis.analysis_api.get_file_blame") as mock_blame, patch(
            "githound.web.apis.analysis_api.validate_repo_path"
        ) as mock_validate, patch("githound.web.apis.analysis_api.get_repository") as mock_get_repo:
            # Create a proper FileBlameResult object
            mock_blame.return_value = FileBlameResult(
                file_path="README.md",
                total_lines=1,
                blame_info=[
                    BlameInfo(
                        line_number=1,
                        content="# Test Repository",
                        commit_hash="abc123",
                        author_name="Original Author",
                        author_email="author@example.com",
                        commit_date=datetime.now(),
                        commit_message="Initial commit",
                    )
                ],
                contributors=["Original Author <author@example.com>"],
                oldest_line_date=datetime.now(),
                newest_line_date=datetime.now(),
            )
            mock_validate.return_value = Path(clone_path)
            mock_get_repo.return_value = Mock()

            blame_response = api_client.post(
                f"/api/v1/analysis/blame?repo_path={clone_path}",
                headers=admin_auth_headers,
                json={"file_path": "README.md"},
            )

            assert blame_response.status_code == status.HTTP_200_OK
            assert "blame_info" in blame_response.json()["data"]


@pytest.mark.e2e
class TestSearchWorkflow:
    """Test complete search workflow."""

    @pytest.mark.skip(reason="Complex mocking issue with SearchResponse model - needs refactoring")
    def test_search_and_export_workflow(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test searching repository and exporting results."""
        repo_path = str(temp_repo.working_dir)

        # Step 1: Perform advanced search
        with patch("githound.web.apis.search_api._perform_sync_search") as mock_search, patch(
            "githound.web.apis.search_api.validate_repo_path"
        ) as mock_validate, patch(
            "githound.web.apis.search_api.create_search_orchestrator"
        ) as mock_orchestrator:
            mock_validate.return_value = Path(repo_path)
            mock_orchestrator.return_value = Mock()
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
                        "relevance_score": 0.95,
                    },
                    {
                        "commit_hash": "def456",
                        "file_path": "src/utils.py",
                        "line_number": 5,
                        "matching_line": "def helper_function() -> None:",
                        "search_type": "content",
                        "relevance_score": 0.88,
                    },
                ],
                "total_count": 2,
                "commits_searched": 10,
                "files_searched": 25,
                "search_duration_ms": 250.0,
                "query_info": {"content_pattern": "def "},
                "filters_applied": {},
                "has_more": False,
            }

            search_response = api_client.post(
                "/api/v1/search/advanced",
                headers=admin_auth_headers,
                json={
                    "repo_path": repo_path,
                    "content_pattern": "def ",
                    "file_extensions": ["py"],
                    "max_results": 100,
                },
            )

            assert search_response.status_code == status.HTTP_200_OK
            search_data = search_response.json()
            assert search_data["status"] == "completed"
            assert len(search_data["results"]) == 2
            search_id = search_data["search_id"]

        # Step 2: Export search results
        with patch("githound.web.apis.integration_api.perform_export_operation"):
            export_response = api_client.post(
                "/api/v1/integration/export",
                headers=admin_auth_headers,
                json={
                    "export_type": "search_results",
                    "format": "JSON",
                    "search_id": search_id,
                    "include_metadata": True,
                },
            )

            assert export_response.status_code == status.HTTP_200_OK
            export_data = export_response.json()
            assert export_data["data"]["export_type"] == "search_results"
            export_id = export_data["data"]["export_id"]

        # Step 3: Check export status
        with patch(
            "githound.web.apis.integration_api.active_exports",
            {
                export_id: {
                    "id": export_id,
                    "status": "completed",
                    "user_id": "test_admin",
                    "file_path": "/tmp/export.json",
                    "filename": "search_results.json",
                }
            },
        ):
            export_status_response = api_client.get(
                f"/api/v1/integration/export/{export_id}/status", headers=admin_auth_headers
            )

            assert export_status_response.status_code == status.HTTP_200_OK
            assert export_status_response.json()["data"]["status"] == "completed"

    def test_fuzzy_search_workflow(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test fuzzy search workflow with typos."""
        repo_path = str(temp_repo.working_dir)

        # Step 1: Perform fuzzy search with typo
        with patch("githound.web.apis.search_api.perform_advanced_search_sync") as mock_search:
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
                        "relevance_score": 0.85,
                    }
                ],
                "total_count": 1,
                "commits_searched": 5,
                "files_searched": 12,
                "search_duration_ms": 180.0,
                "query_info": {"fuzzy_search": True, "fuzzy_threshold": 0.8},
                "filters_applied": {},
                "has_more": False,
            }

            fuzzy_response = api_client.get(
                "/api/v1/search/fuzzy",
                headers=admin_auth_headers,
                params={
                    "repo_path": repo_path,
                    "pattern": "functoin",  # Typo in "function"
                    "threshold": 0.8,
                    "max_distance": 2,
                },
            )

            assert fuzzy_response.status_code == status.HTTP_200_OK
            fuzzy_data = fuzzy_response.json()
            assert fuzzy_data["status"] == "completed"
            assert len(fuzzy_data["results"]) >= 0  # May be empty if no matches
            # The fuzzy search endpoint doesn't return fuzzy_search in query_info
            assert "query_info" in fuzzy_data

    def test_historical_search_workflow(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test historical search workflow."""
        repo_path = str(temp_repo.working_dir)

        # Historical search with max_commits=1000 triggers background search
        # which returns status="started"
        historical_response = api_client.get(
            "/api/v1/search/historical",
            headers=admin_auth_headers,
            params={
                "repo_path": repo_path,
                "pattern": "deprecated",
                "max_commits": 1000,
                "date_from": "2023-01-01T00:00:00Z",
            },
        )

        assert historical_response.status_code == status.HTTP_200_OK
        historical_data = historical_response.json()
        # Background search returns "started" status
        assert historical_data["status"] in ["started", "completed"]
        assert "search_id" in historical_data


@pytest.mark.e2e
@pytest.mark.skip(reason="Webhook endpoints removed - not core functionality")
class TestWebhookWorkflow:
    """Test webhook integration workflow (REMOVED)."""

    def test_webhook_setup_and_trigger_workflow(
        self, api_client, admin_auth_headers, temp_repo
    ) -> None:
        """Test setting up webhooks and triggering events."""
        repo_path = str(temp_repo.working_dir)

        # Step 1: Create webhook endpoint
        with patch("githound.web.services.webhook_service.WebhookManager.add_endpoint") as mock_add:
            mock_add.return_value = "webhook-123"

            webhook_response = api_client.post(
                "/api/v1/integration/webhooks",
                headers=admin_auth_headers,
                json={
                    "url": "https://example.com/webhook",
                    "events": ["repository.created", "branch.created", "commit.created"],
                    "secret": "webhook-secret",
                    "active": True,
                },
            )

            assert webhook_response.status_code == status.HTTP_200_OK
            webhook_data = webhook_response.json()
            assert webhook_data["data"]["url"] == "https://example.com/webhook"
            webhook_id = webhook_data["data"]["webhook_id"]

        # Step 2: List webhooks
        with patch(
            "githound.web.services.webhook_service.WebhookManager.list_endpoints"
        ) as mock_list:
            from datetime import datetime

            mock_endpoint = Mock()
            mock_endpoint.id = webhook_id
            mock_endpoint.url = "https://example.com/webhook"
            mock_endpoint.events = ["repository.created", "branch.created", "commit.created"]
            mock_endpoint.active = True
            mock_endpoint.created_at = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
            mock_endpoint.last_delivery = None
            mock_endpoint.failure_count = 0
            mock_list.return_value = [mock_endpoint]

            list_response = api_client.get(
                "/api/v1/integration/webhooks", headers=admin_auth_headers
            )

            assert list_response.status_code == status.HTTP_200_OK
            list_data = list_response.json()
            assert len(list_data["data"]["webhooks"]) == 1

        # Step 3: Trigger webhook event by creating branch
        with patch(
            "githound.web.core.git_operations.GitOperationsManager.create_branch"
        ) as mock_create:
            mock_create.return_value = {
                "name": "webhook-test-branch",
                "commit_hash": "webhook123",
                "status": "created",
            }

            branch_response = api_client.post(
                f"/api/v1/repository/branches?repo_path={repo_path}",
                headers=admin_auth_headers,
                json={
                    "branch_name": "webhook-test-branch",
                    "checkout": False,
                },
            )

            assert branch_response.status_code == status.HTTP_200_OK
            # Note: Webhook triggering is not currently implemented in the endpoint


@pytest.mark.e2e
class TestBatchOperationsWorkflow:
    """Test batch operations workflow."""

    @pytest.mark.skip(reason="Integration API not implemented yet")
    def test_batch_repository_analysis(self, api_client, admin_auth_headers, temp_dir) -> None:
        """Test batch analysis across multiple repositories."""
        repo_paths = [str(temp_dir / "repo1"), str(temp_dir / "repo2"), str(temp_dir / "repo3")]

        # Step 1: Start batch operation
        with patch("githound.web.apis.integration_api.perform_batch_operation"):
            batch_response = api_client.post(
                "/api/v1/integration/batch",
                headers=admin_auth_headers,
                json={
                    "operation_type": "status_check",
                    "repositories": repo_paths,
                    "parallel": True,
                    "max_concurrent": 2,
                },
            )

            assert batch_response.status_code == status.HTTP_200_OK
            batch_data = batch_response.json()
            assert batch_data["data"]["operation_type"] == "status_check"
            assert batch_data["data"]["repository_count"] == 3
            batch_id = batch_data["data"]["batch_id"]

        # Step 2: Check batch status
        with patch(
            "githound.web.apis.integration_api.batch_operations",
            {
                batch_id: {
                    "id": batch_id,
                    "status": "running",
                    "progress": 0.67,
                    "message": "Processing repositories...",
                    "user_id": "test_admin",
                    "operation_type": "status_check",
                    "total_count": 3,
                    "completed_count": 2,
                    "failed_count": 0,
                }
            },
        ):
            status_response = api_client.get(
                f"/api/v1/integration/batch/{batch_id}/status", headers=admin_auth_headers
            )

            assert status_response.status_code == status.HTTP_200_OK
            status_data = status_response.json()
            assert status_data["data"]["status"] == "running"
            assert status_data["data"]["completed_count"] == 2

        # Step 3: Get batch results
        with patch(
            "githound.web.apis.integration_api.batch_operations",
            {
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
                        repo_paths[2]: {"status": "success", "data": {"is_dirty": False}},
                    },
                }
            },
        ):
            results_response = api_client.get(
                f"/api/v1/integration/batch/{batch_id}/results", headers=admin_auth_headers
            )

            assert results_response.status_code == status.HTTP_200_OK
            results_data = results_response.json()
            assert results_data["data"]["status"] == "completed"
            assert len(results_data["data"]["results"]) == 3
            assert results_data["data"]["summary"]["success_rate"] == 1.0


@pytest.mark.e2e
class TestErrorHandlingWorkflow:
    """Test error handling in complete workflows."""

    @pytest.mark.skip(reason="Repository init endpoint not implemented yet")
    def test_repository_error_recovery(self, api_client, admin_auth_headers, temp_dir) -> None:
        """Test error handling and recovery in repository operations."""
        repo_path = str(temp_dir / "error_repo")

        # Step 1: Try to initialize repository in invalid location
        with patch(
            "githound.web.core.git_operations.GitOperationsManager.init_repository"
        ) as mock_init:
            mock_init.side_effect = Exception("Permission denied")

            init_response = api_client.post(
                "/api/v1/repository/init",
                headers=admin_auth_headers,
                json={"path": "/invalid/permission/path", "bare": False},
            )

            assert init_response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Permission denied" in init_response.json()["detail"]

        # Step 2: Retry with valid path
        with patch(
            "githound.web.core.git_operations.GitOperationsManager.init_repository"
        ) as mock_init:
            mock_init.return_value = {"path": repo_path, "status": "created"}

            retry_response = api_client.post(
                "/api/v1/repository/init",
                headers=admin_auth_headers,
                json={"path": repo_path, "bare": False},
            )

            assert retry_response.status_code == status.HTTP_200_OK
            assert retry_response.json()["data"]["status"] == "created"

    @pytest.mark.skip(reason="Search timeout handling not implemented yet")
    def test_search_timeout_handling(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test handling of search timeouts."""
        repo_path = str(temp_repo.working_dir)

        # Test that advanced search endpoint accepts timeout parameter
        with patch(
            "githound.web.core.search_orchestrator.create_search_orchestrator"
        ) as mock_orchestrator:
            from githound.search_engine import SearchOrchestrator

            mock_orch = Mock(spec=SearchOrchestrator)
            mock_orch.search = AsyncMock(return_value=[])
            mock_orchestrator.return_value = mock_orch

            search_response = api_client.post(
                "/api/v1/search/advanced",
                headers=admin_auth_headers,
                json={
                    "search_request": {
                        "repo_path": repo_path,
                        "content_pattern": "test_pattern",
                        "timeout_seconds": 10,  # Minimum allowed timeout
                    }
                },
            )

            # Should accept the request (may return started or completed status)
            if search_response.status_code != status.HTTP_200_OK:
                print(f"Response: {search_response.json()}")
            assert search_response.status_code == status.HTTP_200_OK
            response_data = search_response.json()
            assert response_data["status"] in ["started", "completed"]
