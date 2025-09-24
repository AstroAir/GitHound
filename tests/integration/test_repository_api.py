"""
Integration tests for repository API endpoints.

Tests all repository operations including initialization, cloning, status,
branch management, commit operations, tag management, and remote operations.
"""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from fastapi import status


@pytest.mark.integration
class TestRepositoryInitialization:
    """Test repository initialization endpoints."""

    def test_init_repository_success(self, api_client, admin_auth_headers, temp_dir) -> None:
        """Test successful repository initialization."""
        repo_path = str(temp_dir / "new_repo")

        with patch("githound.web.git_operations.GitOperationsManager.init_repository") as mock_init:
            mock_init.return_value = {
                "path": repo_path,
                "bare": False,
                "status": "created",
                "git_dir": f"{repo_path}/.git",
                "working_dir": repo_path,
            }

            response = api_client.post(
                "/api/v3/repository/init",
                headers=admin_auth_headers,
                json={"path": repo_path, "bare": False},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["path"] == repo_path
            assert data["data"]["status"] == "created"
            mock_init.assert_called_once_with(path=repo_path, bare=False)

    def test_init_repository_unauthorized(self, api_client, temp_dir) -> None:
        """Test repository initialization without authentication."""
        repo_path = str(temp_dir / "new_repo")

        response = api_client.post(
            "/api/v3/repository/init", json={"path": repo_path, "bare": False}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_init_repository_insufficient_permissions(
        self, api_client, readonly_auth_headers, temp_dir
    ) -> None:
        """Test repository initialization with insufficient permissions."""
        repo_path = str(temp_dir / "new_repo")

        response = api_client.post(
            "/api/v3/repository/init",
            headers=readonly_auth_headers,
            json={"path": repo_path, "bare": False},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_init_repository_invalid_path(self, api_client, admin_auth_headers) -> None:
        """Test repository initialization with invalid path."""
        with patch("githound.web.git_operations.GitOperationsManager.init_repository") as mock_init:
            mock_init.side_effect = Exception("Invalid path")

            response = api_client.post(
                "/api/v3/repository/init",
                headers=admin_auth_headers,
                json={"path": "/invalid/path", "bare": False},
            )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.integration
class TestRepositoryCloning:
    """Test repository cloning endpoints."""

    def test_clone_repository_success(self, api_client, admin_auth_headers, temp_dir) -> None:
        """Test successful repository cloning."""
        clone_path = str(temp_dir / "cloned_repo")
        test_url = "https://github.com/test/repo.git"

        with patch("githound.web.comprehensive_api.perform_clone_operation") as mock_clone:
            response = api_client.post(
                "/api/v3/repository/clone",
                headers=admin_auth_headers,
                json={
                    "url": test_url,
                    "path": clone_path,
                    "branch": "main",
                    "depth": None,
                    "recursive": False,
                },
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert "operation_id" in data["data"]
            assert data["data"]["url"] == test_url
            assert data["data"]["path"] == clone_path

    def test_clone_repository_with_options(self, api_client, admin_auth_headers, temp_dir) -> None:
        """Test repository cloning with additional options."""
        clone_path = str(temp_dir / "cloned_repo")
        test_url = "https://github.com/test/repo.git"

        response = api_client.post(
            "/api/v3/repository/clone",
            headers=admin_auth_headers,
            json={
                "url": test_url,
                "path": clone_path,
                "branch": "develop",
                "depth": 1,
                "recursive": True,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True


@pytest.mark.integration
class TestRepositoryStatus:
    """Test repository status endpoints."""

    def test_get_repository_status_success(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test successful repository status retrieval."""
        repo_path = str(temp_repo.working_dir)

        with patch(
            "githound.web.git_operations.GitOperationsManager.get_repository_status"
        ) as mock_status:
            mock_status.return_value = {
                "is_dirty": False,
                "untracked_files": [],
                "modified_files": [],
                "staged_files": [],
                "deleted_files": [],
                "current_branch": "master",
                "ahead_behind": None,
                "head_commit": "abc123",
                "total_commits": 1,
                "stash_count": 0,
            }

            # URL encode the path
            encoded_path = repo_path.replace("/", "%2F")
            response = api_client.get(
                f"/api/v3/repository/{encoded_path}/status", headers=admin_auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["current_branch"] == "master"
            assert data["data"]["is_dirty"] is False

    def test_get_repository_status_invalid_repo(self, api_client, admin_auth_headers) -> None:
        """Test repository status with invalid repository."""
        with patch("githound.web.comprehensive_api.validate_repo_path") as mock_validate:
            mock_validate.side_effect = Exception("Invalid repository")

            response = api_client.get(
                "/api/v3/repository/invalid%2Fpath/status", headers=admin_auth_headers
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.integration
class TestBranchOperations:
    """Test branch management endpoints."""

    def test_list_branches_success(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test successful branch listing."""
        repo_path = str(temp_repo.working_dir)

        with patch("githound.web.git_operations.GitOperationsManager.list_branches") as mock_list:
            mock_list.return_value = [
                {
                    "name": "master",
                    "commit_hash": "abc123",
                    "commit_message": "Initial commit",
                    "author": "Test User <test@example.com>",
                    "date": "2024-01-01T00:00:00Z",
                    "is_current": True,
                    "is_remote": False,
                    "tracking_branch": None,
                }
            ]

            encoded_path = repo_path.replace("/", "%2F")
            response = api_client.get(
                f"/api/v3/repository/{encoded_path}/branches", headers=admin_auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]["branches"]) == 1
            assert data["data"]["branches"][0]["name"] == "master"
            assert data["data"]["total_count"] == 1

    def test_create_branch_success(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test successful branch creation."""
        repo_path = str(temp_repo.working_dir)

        with patch("githound.web.git_operations.GitOperationsManager.create_branch") as mock_create:
            mock_create.return_value = {
                "name": "feature-branch",
                "commit_hash": "def456",
                "start_point": "HEAD",
                "checked_out": True,
                "status": "created",
            }

            encoded_path = repo_path.replace("/", "%2F")
            response = api_client.post(
                f"/api/v3/repository/{encoded_path}/branches",
                headers=admin_auth_headers,
                json={
                    "repo_path": repo_path,
                    "branch_name": "feature-branch",
                    "start_point": None,
                    "checkout": True,
                },
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["name"] == "feature-branch"
            assert data["data"]["status"] == "created"

    def test_delete_branch_success(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test successful branch deletion."""
        repo_path = str(temp_repo.working_dir)
        branch_name = "feature-branch"

        with patch("githound.web.git_operations.GitOperationsManager.delete_branch") as mock_delete:
            mock_delete.return_value = {
                "name": branch_name,
                "last_commit": "abc123",
                "forced": False,
                "status": "deleted",
            }

            encoded_path = repo_path.replace("/", "%2F")
            response = api_client.delete(
                f"/api/v3/repository/{encoded_path}/branches/{branch_name}",
                headers=admin_auth_headers,
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["name"] == branch_name
            assert data["data"]["status"] == "deleted"

    def test_checkout_branch_success(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test successful branch checkout."""
        repo_path = str(temp_repo.working_dir)
        branch_name = "feature-branch"

        with patch(
            "githound.web.git_operations.GitOperationsManager.checkout_branch"
        ) as mock_checkout:
            mock_checkout.return_value = {
                "branch": branch_name,
                "commit_hash": "abc123",
                "status": "checked_out",
            }

            encoded_path = repo_path.replace("/", "%2F")
            response = api_client.post(
                f"/api/v3/repository/{encoded_path}/branches/{branch_name}/checkout",
                headers=admin_auth_headers,
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["branch"] == branch_name
            assert data["data"]["status"] == "checked_out"

    def test_merge_branches_success(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test successful branch merge."""
        repo_path = str(temp_repo.working_dir)

        with patch("githound.web.git_operations.GitOperationsManager.merge_branch") as mock_merge:
            mock_merge.return_value = {
                "status": "merged",
                "commit_hash": "merge123",
                "source_branch": "feature",
                "target_branch": "main",
                "strategy": "merge",
                "message": "Merge branch 'feature' into main",
            }

            encoded_path = repo_path.replace("/", "%2F")
            response = api_client.post(
                f"/api/v3/repository/{encoded_path}/branches/merge",
                headers=admin_auth_headers,
                json={
                    "repo_path": repo_path,
                    "source_branch": "feature",
                    "target_branch": "main",
                    "strategy": "merge",
                    "message": None,
                },
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["status"] == "merged"


@pytest.mark.integration
class TestCommitOperations:
    """Test commit management endpoints."""

    def test_create_commit_success(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test successful commit creation."""
        repo_path = str(temp_repo.working_dir)

        with patch("githound.web.git_operations.GitOperationsManager.create_commit") as mock_commit:
            mock_commit.return_value = {
                "commit_hash": "new123",
                "message": "Test commit",
                "author": "Test User <test@example.com>",
                "date": "2024-01-01T00:00:00Z",
                "files_changed": 1,
                "insertions": 5,
                "deletions": 0,
                "status": "created",
            }

            encoded_path = repo_path.replace("/", "%2F")
            response = api_client.post(
                f"/api/v3/repository/{encoded_path}/commits",
                headers=admin_auth_headers,
                json={
                    "repo_path": repo_path,
                    "message": "Test commit",
                    "files": None,
                    "all_files": True,
                    "author_name": None,
                    "author_email": None,
                },
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["commit_hash"] == "new123"
            assert data["data"]["status"] == "created"

    def test_amend_commit_success(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test successful commit amendment."""
        repo_path = str(temp_repo.working_dir)

        with patch("githound.web.git_operations.GitOperationsManager.amend_commit") as mock_amend:
            mock_amend.return_value = {
                "old_commit_hash": "old123",
                "new_commit_hash": "new456",
                "message": "Amended commit message",
                "author": "Test User <test@example.com>",
                "date": "2024-01-01T00:00:00Z",
                "status": "amended",
            }

            encoded_path = repo_path.replace("/", "%2F")
            response = api_client.patch(
                f"/api/v3/repository/{encoded_path}/commits/amend",
                headers=admin_auth_headers,
                json={"repo_path": repo_path, "message": "Amended commit message", "files": None},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["status"] == "amended"

    def test_revert_commit_success(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test successful commit revert."""
        repo_path = str(temp_repo.working_dir)
        commit_hash = "abc123"

        with patch("githound.web.git_operations.GitOperationsManager.revert_commit") as mock_revert:
            mock_revert.return_value = {
                "reverted_commit": commit_hash,
                "revert_commit": "revert456",
                "message": f'Revert "Original commit"\n\nThis reverts commit {commit_hash}.',
                "status": "reverted",
            }

            encoded_path = repo_path.replace("/", "%2F")
            response = api_client.post(
                f"/api/v3/repository/{encoded_path}/commits/{commit_hash}/revert",
                headers=admin_auth_headers,
                json={"repo_path": repo_path, "no_commit": False},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["reverted_commit"] == commit_hash
            assert data["data"]["status"] == "reverted"

    def test_cherry_pick_commit_success(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test successful commit cherry-pick."""
        repo_path = str(temp_repo.working_dir)
        commit_hash = "abc123"

        with patch(
            "githound.web.git_operations.GitOperationsManager.cherry_pick_commit"
        ) as mock_cherry:
            mock_cherry.return_value = {
                "original_commit": commit_hash,
                "cherry_pick_commit": "cherry456",
                "message": "Original commit message",
                "author": "Original Author <author@example.com>",
                "status": "cherry_picked",
            }

            encoded_path = repo_path.replace("/", "%2F")
            response = api_client.post(
                f"/api/v3/repository/{encoded_path}/commits/{commit_hash}/cherry-pick",
                headers=admin_auth_headers,
                json={"repo_path": repo_path, "no_commit": False},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["original_commit"] == commit_hash
            assert data["data"]["status"] == "cherry_picked"
