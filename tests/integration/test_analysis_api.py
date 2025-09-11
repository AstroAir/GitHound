"""
Integration tests for analysis API endpoints.

Tests blame analysis, diff analysis, repository statistics,
merge conflict detection, and file history tracking.
"""

import pytest
from unittest.mock import patch, Mock
from fastapi import status


@pytest.mark.integration
class TestBlameAnalysis:
    """Test file blame analysis endpoints."""

    def test_analyze_file_blame_success(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test successful file blame analysis."""
        repo_path = str(temp_repo.working_dir)

        with patch('githound.web.analysis_api.get_file_blame') as mock_blame:
            mock_blame.return_value = Mock(
                dict=lambda: {
                    "file_path": "test_file.py",
                    "line_blame": {
                        1: {
                            "commit_hash": "abc123",
                            "author": "Test User",
                            "date": "2024-01-01T00:00:00Z",
                            "message": "Initial commit",
                            "line_content": "def test_function() -> None:"
                        },
                        2: {
                            "commit_hash": "def456",
                            "author": "Another User",
                            "date": "2024-01-02T00:00:00Z",
                            "message": "Add implementation",
                            "line_content": "    return True"
                        }
                    }
                }
            )

            response = api_client.post(
                "/api/v3/analysis/blame",
                headers=admin_auth_headers,
                params={"repo_path": repo_path},
                json={
                    "file_path": "test_file.py",
                    "commit": None,
                    "line_range": None
                }
            )

            assert response.status_code = = status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert "line_blame" in data["data"]
            mock_blame.assert_called_once()

    def test_analyze_file_blame_with_line_range(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test file blame analysis with line range."""
        repo_path = str(temp_repo.working_dir)

        with patch('githound.web.analysis_api.get_file_blame') as mock_blame:
            mock_blame.return_value = Mock(
                line_blame={
                    5: {"commit_hash": "abc123", "author": "Test User"},
                    6: {"commit_hash": "def456", "author": "Another User"}
                }
            )

            response = api_client.post(
                "/api/v3/analysis/blame",
                headers=admin_auth_headers,
                params={"repo_path": repo_path},
                json={
                    "file_path": "test_file.py",
                    "commit": "abc123",
                    "line_range": [5, 10]
                }
            )

            assert response.status_code = = status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True

    def test_analyze_file_blame_invalid_file(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test file blame analysis with invalid file."""
        repo_path = str(temp_repo.working_dir)

        with patch('githound.web.analysis_api.get_file_blame') as mock_blame:
            mock_blame.side_effect = FileNotFoundError("File not found")

            response = api_client.post(
                "/api/v3/analysis/blame",
                headers=admin_auth_headers,
                params={"repo_path": repo_path},
                json={"file_path": "nonexistent.py"}
            )

            assert response.status_code = = status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.integration
class TestDiffAnalysis:
    """Test diff analysis endpoints."""

    def test_compare_commits_success(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test successful commit comparison."""
        repo_path = str(temp_repo.working_dir)

        with patch('githound.web.analysis_api.compare_commits') as mock_compare:
            mock_compare.return_value = Mock(
                dict=lambda: {
                    "from_commit": "abc123",
                    "to_commit": "def456",
                    "files_changed": 2,
                    "insertions": 15,
                    "deletions": 5,
                    "file_diffs": [
                        {
                            "file_path": "file1.py",
                            "change_type": "modified",
                            "insertions": 10,
                            "deletions": 2
                        },
                        {
                            "file_path": "file2.py",
                            "change_type": "added",
                            "insertions": 5,
                            "deletions": 0
                        }
                    ]
                }
            )

            response = api_client.post(
                "/api/v3/analysis/diff/commits",
                headers=admin_auth_headers,
                params={"repo_path": repo_path},
                json={
                    "from_commit": "abc123",
                    "to_commit": "def456",
                    "file_patterns": None,
                    "context_lines": 3
                }
            )

            assert response.status_code = = status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert "files_changed" in data["data"]
            assert data["data"]["files_changed"] == 2
            mock_compare.assert_called_once()

    def test_compare_branches_success(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test successful branch comparison."""
        repo_path = str(temp_repo.working_dir)

        with patch('githound.web.analysis_api.compare_branches') as mock_compare:
            mock_compare.return_value = Mock(
                dict=lambda: {
                    "from_branch": "main",
                    "to_branch": "feature",
                    "files_changed": 3,
                    "insertions": 25,
                    "deletions": 8,
                    "file_diffs": []
                }
            )

            response = api_client.post(
                "/api/v3/analysis/diff/branches",
                headers=admin_auth_headers,
                params={"repo_path": repo_path},
                json={
                    "from_branch": "main",
                    "to_branch": "feature",
                    "file_patterns": ["*.py"],
                    "context_lines": 5
                }
            )

            assert response.status_code = = status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["files_changed"] == 3

    def test_compare_commits_invalid_hash(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test commit comparison with invalid commit hash."""
        repo_path = str(temp_repo.working_dir)

        with patch('githound.web.analysis_api.compare_commits') as mock_compare:
            mock_compare.side_effect = ValueError("Invalid commit hash")

            response = api_client.post(
                "/api/v3/analysis/diff/commits",
                headers=admin_auth_headers,
                params={"repo_path": repo_path},
                json={
                    "from_commit": "invalid",
                    "to_commit": "also_invalid"
                }
            )

            assert response.status_code = = status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.integration
class TestCommitFiltering:
    """Test commit filtering endpoints."""

    def test_get_filtered_commits_success(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test successful commit filtering."""
        repo_path = str(temp_repo.working_dir)

        with patch('githound.web.analysis_api.get_commits_with_filters') as mock_filter:
            mock_commits = [Mock(), Mock()]
            mock_filter.return_value = mock_commits

            with patch('githound.web.analysis_api.extract_commit_metadata') as mock_extract:
                mock_extract.return_value = Mock(
                    dict=lambda: {
                        "commit_hash": "abc123",
                        "author": "Test User",
                        "date": "2024-01-01T00:00:00Z",
                        "message": "Test commit",
                        "files_changed": 1
                    }
                )

                response = api_client.post(
                    "/api/v3/analysis/commits/filter",
                    headers=admin_auth_headers,
                    params={"repo_path": repo_path},
                    json={
                        "branch": "main",
                        "author_pattern": "Test*",
                        "message_pattern": "fix",
                        "date_from": "2024-01-01T00:00:00Z",
                        "date_to": "2024-12-31T23:59:59Z",
                        "file_patterns": ["*.py"],
                        "max_count": 50
                    }
                )

                assert response.status_code = = status.HTTP_200_OK
                data = response.json()
                assert data["success"] is True
                assert len(data["data"]["commits"]) == 2
                assert "filters_applied" in data["data"]

    def test_get_filtered_commits_no_results(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test commit filtering with no results."""
        repo_path = str(temp_repo.working_dir)

        with patch('githound.web.analysis_api.get_commits_with_filters') as mock_filter:
            mock_filter.return_value = []

            response = api_client.post(
                "/api/v3/analysis/commits/filter",
                headers=admin_auth_headers,
                params={"repo_path": repo_path},
                json={
                    "author_pattern": "NonexistentAuthor",
                    "max_count": 10
                }
            )

            assert response.status_code = = status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]["commits"]) == 0


@pytest.mark.integration
class TestFileHistory:
    """Test file history endpoints."""

    def test_get_file_history_success(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test successful file history retrieval."""
        repo_path = str(temp_repo.working_dir)

        with patch('githound.web.analysis_api.get_file_history') as mock_history:
            mock_history.return_value = [
                {
                    "commit_hash": "abc123",
                    "author": "Test User",
                    "date": "2024-01-01T00:00:00Z",
                    "message": "Initial version",
                    "change_type": "added"
                },
                {
                    "commit_hash": "def456",
                    "author": "Another User",
                    "date": "2024-01-02T00:00:00Z",
                    "message": "Update file",
                    "change_type": "modified"
                }
            ]

            response = api_client.get(
                "/api/v3/analysis/file-history",
                headers=admin_auth_headers,
                params={
                    "repo_path": repo_path,
                    "file_path": "test_file.py",
                    "branch": "main",
                    "max_count": 50
                }
            )

            assert response.status_code = = status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]["history"]) == 2
            assert data["data"]["file_path"] == "test_file.py"
            assert data["data"]["total_commits"] == 2

    def test_get_file_history_nonexistent_file(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test file history for nonexistent file."""
        repo_path = str(temp_repo.working_dir)

        with patch('githound.web.analysis_api.get_file_history') as mock_history:
            mock_history.return_value = []

            response = api_client.get(
                "/api/v3/analysis/file-history",
                headers=admin_auth_headers,
                params={
                    "repo_path": repo_path,
                    "file_path": "nonexistent.py"
                }
            )

            assert response.status_code = = status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]["history"]) == 0


@pytest.mark.integration
class TestRepositoryStatistics:
    """Test repository statistics endpoints."""

    def test_get_repository_statistics_success(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test successful repository statistics retrieval."""
        repo_path = str(temp_repo.working_dir)

        with patch('githound.web.analysis_api.get_repository_metadata') as mock_metadata:
            mock_metadata.return_value = {
                "total_commits": 10,
                "contributors": ["Alice", "Bob"],
                "branches": ["main", "develop"],
                "tags": ["v1.0.0"],
                "first_commit_date": "2024-01-01T00:00:00Z",
                "last_commit_date": "2024-01-10T00:00:00Z"
            }

            with patch('githound.web.analysis_api.get_author_statistics') as mock_author_stats:
                mock_author_stats.return_value = {
                    "Alice": {
                        "total_commits": 6,
                        "total_files": 8,
                        "lines_added": 150,
                        "lines_deleted": 20
                    },
                    "Bob": {
                        "total_commits": 4,
                        "total_files": 5,
                        "lines_added": 80,
                        "lines_deleted": 10
                    }
                }

                response = api_client.get(
                    "/api/v3/analysis/repository-stats",
                    headers=admin_auth_headers,
                    params={
                        "repo_path": repo_path,
                        "include_author_stats": True,
                        "include_file_stats": True
                    }
                )

                assert response.status_code = = status.HTTP_200_OK
                data = response.json()
                assert data["success"] is True
                assert "repository_info" in data["data"]
                assert "author_statistics" in data["data"]
                assert "top_contributors" in data["data"]
                assert data["data"]["summary"]["total_commits"] == 10
                assert data["data"]["summary"]["total_contributors"] == 2

    def test_get_repository_statistics_minimal(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test repository statistics with minimal options."""
        repo_path = str(temp_repo.working_dir)

        with patch('githound.web.analysis_api.get_repository_metadata') as mock_metadata:
            mock_metadata.return_value = {
                "total_commits": 5,
                "contributors": ["Alice"],
                "branches": ["main"],
                "tags": []
            }

            response = api_client.get(
                "/api/v3/analysis/repository-stats",
                headers=admin_auth_headers,
                params={
                    "repo_path": repo_path,
                    "include_author_stats": False,
                    "include_file_stats": False
                }
            )

            assert response.status_code = = status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert "repository_info" in data["data"]
            assert "author_statistics" not in data["data"]


@pytest.mark.integration
class TestMergeConflicts:
    """Test merge conflict detection and resolution endpoints."""

    def test_get_merge_conflicts_no_conflicts(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test getting merge conflicts when none exist."""
        repo_path = str(temp_repo.working_dir)

        with patch('githound.web.git_operations.GitOperationsManager.get_merge_conflicts') as mock_conflicts:
            mock_conflicts.return_value = {
                "has_conflicts": False,
                "conflicts": [],
                "status": "no_conflicts"
            }

            response = api_client.get(
                "/api/v3/analysis/conflicts",
                headers=admin_auth_headers,
                params={"repo_path": repo_path}
            )

            assert response.status_code = = status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["has_conflicts"] is False
            assert len(data["data"]["conflicts"]) == 0

    def test_get_merge_conflicts_with_conflicts(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test getting merge conflicts when they exist."""
        repo_path = str(temp_repo.working_dir)

        with patch('githound.web.git_operations.GitOperationsManager.get_merge_conflicts') as mock_conflicts:
            mock_conflicts.return_value = {
                "has_conflicts": True,
                "conflicts": [
                    {
                        "file_path": "conflicted_file.py",
                        "stages": {
                            1: {"blob_hash": "abc123", "size": 100},
                            2: {"blob_hash": "def456", "size": 120},
                            3: {"blob_hash": "ghi789", "size": 110}
                        }
                    }
                ],
                "conflict_count": 1,
                "status": "conflicts_detected"
            }

            response = api_client.get(
                "/api/v3/analysis/conflicts",
                headers=admin_auth_headers,
                params={"repo_path": repo_path}
            )

            assert response.status_code = = status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["has_conflicts"] is True
            assert data["data"]["conflict_count"] == 1
            assert len(data["data"]["conflicts"]) == 1

    def test_resolve_conflict_success(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test successful conflict resolution."""
        repo_path = str(temp_repo.working_dir)

        with patch('githound.web.git_operations.GitOperationsManager.resolve_conflict') as mock_resolve:
            mock_resolve.return_value = {
                "file_path": "conflicted_file.py",
                "resolution": "ours",
                "status": "resolved"
            }

            response = api_client.post(
                "/api/v3/analysis/conflicts/resolve",
                headers=admin_auth_headers,
                params={"repo_path": repo_path},
                json={
                    "file_path": "conflicted_file.py",
                    "resolution": "ours"
                }
            )

            assert response.status_code = = status.HTTP_200_OK
            data = response.json()
            assert data["success"] is True
            assert data["data"]["file_path"] == "conflicted_file.py"
            assert data["data"]["resolution"] == "ours"
            assert data["data"]["status"] == "resolved"

    def test_resolve_conflict_invalid_strategy(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test conflict resolution with invalid strategy."""
        repo_path = str(temp_repo.working_dir)

        response = api_client.post(
            "/api/v3/analysis/conflicts/resolve",
            headers=admin_auth_headers,
            params={"repo_path": repo_path},
            json={
                "file_path": "conflicted_file.py",
                "resolution": "invalid_strategy"
            }
        )

        assert response.status_code = = status.HTTP_422_UNPROCESSABLE_ENTITY
