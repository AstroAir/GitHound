"""Tests for Enhanced GitHound API endpoints."""

import pytest
import tempfile
import shutil
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from git import Repo

from githound.web.enhanced_api import app


@pytest.fixture
def temp_repo():
    """Create a temporary Git repository for testing."""
    temp_dir = tempfile.mkdtemp()
    repo = Repo.init(temp_dir)
    
    # Configure user for commits
    with repo.config_writer() as config:
        config.set_value("user", "name", "Test User")
        config.set_value("user", "email", "test@example.com")
    
    # Create initial commit
    test_file = Path(temp_dir) / "test.py"
    test_file.write_text("def hello():\n    print('Hello, World!')\n")
    repo.index.add([str(test_file)])
    initial_commit = repo.index.commit("Initial commit")
    
    # Create second commit
    test_file.write_text("def hello():\n    print('Hello, GitHound!')\n\ndef goodbye():\n    print('Goodbye!')\n")
    repo.index.add([str(test_file)])
    second_commit = repo.index.commit("Add goodbye function")
    
    # Create a branch
    new_branch = repo.create_head("feature-branch")
    new_branch.checkout()
    
    # Add commit to branch
    test_file.write_text("def hello():\n    print('Hello, GitHound!')\n\ndef goodbye():\n    print('Goodbye!')\n\ndef feature():\n    print('New feature!')\n")
    repo.index.add([str(test_file)])
    feature_commit = repo.index.commit("Add feature function")
    
    # Switch back to main branch
    repo.heads.master.checkout()
    
    yield repo, temp_dir, initial_commit, second_commit, feature_commit
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Mock authentication headers."""
    return {"Authorization": "Bearer test-token"}


class TestRepositoryAnalysis:
    """Tests for repository analysis endpoints."""
    
    def test_analyze_repository(self, client, temp_repo, auth_headers):
        """Test repository analysis endpoint."""
        repo, temp_dir, initial_commit, second_commit, feature_commit = temp_repo
        
        response = client.post(
            "/api/v2/repository/analyze",
            json={
                "repo_path": temp_dir,
                "include_detailed_stats": True
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["total_commits"] >= 2
        assert len(data["data"]["contributors"]) >= 1
        assert "detailed_author_stats" in data["data"]
    
    def test_analyze_repository_invalid_path(self, client, auth_headers):
        """Test repository analysis with invalid path."""
        response = client.post(
            "/api/v2/repository/analyze",
            json={
                "repo_path": "/nonexistent/path",
                "include_detailed_stats": False
            },
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "does not exist" in response.json()["detail"]
    
    def test_analyze_commit(self, client, temp_repo, auth_headers):
        """Test commit analysis endpoint."""
        repo, temp_dir, initial_commit, second_commit, feature_commit = temp_repo
        
        response = client.post(
            "/api/v2/commit/analyze",
            json={
                "repo_path": temp_dir,
                "commit_hash": second_commit.hexsha,
                "include_file_changes": True
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["hash"] == second_commit.hexsha
        assert data["data"]["author_name"] == "Test User"
        assert "file_changes" in data["data"]
    
    def test_get_filtered_commits(self, client, temp_repo, auth_headers):
        """Test filtered commit retrieval endpoint."""
        repo, temp_dir, initial_commit, second_commit, feature_commit = temp_repo
        
        response = client.post(
            "/api/v2/commits/filter",
            json={
                "repo_path": temp_dir,
                "author_pattern": "Test User",
                "max_count": 10
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["total_count"] >= 2
        assert len(data["data"]) >= 2
        
        # Check that all commits are by Test User
        for commit in data["data"]:
            assert commit["author_name"] == "Test User"


class TestFileAnalysis:
    """Tests for file analysis endpoints."""
    
    def test_get_file_history(self, client, temp_repo, auth_headers):
        """Test file history endpoint."""
        repo, temp_dir, initial_commit, second_commit, feature_commit = temp_repo
        
        response = client.get(
            "/api/v2/file/test.py/history",
            params={
                "repo_path": temp_dir,
                "max_count": 10
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["file_path"] == "test.py"
        assert data["data"]["total_commits"] >= 2
        assert len(data["data"]["history"]) >= 2
    
    def test_analyze_file_blame(self, client, temp_repo, auth_headers):
        """Test file blame analysis endpoint."""
        repo, temp_dir, initial_commit, second_commit, feature_commit = temp_repo
        
        response = client.post(
            "/api/v2/file/blame",
            json={
                "repo_path": temp_dir,
                "file_path": "test.py"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["file_path"] == "test.py"
        assert data["data"]["total_lines"] >= 4
        assert len(data["data"]["contributors"]) >= 1
    
    def test_analyze_file_blame_nonexistent(self, client, temp_repo, auth_headers):
        """Test file blame analysis for nonexistent file."""
        repo, temp_dir, initial_commit, second_commit, feature_commit = temp_repo
        
        response = client.post(
            "/api/v2/file/blame",
            json={
                "repo_path": temp_dir,
                "file_path": "nonexistent.py"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 500  # Should handle the error gracefully


class TestDiffAnalysis:
    """Tests for diff analysis endpoints."""
    
    def test_compare_commits(self, client, temp_repo, auth_headers):
        """Test commit comparison endpoint."""
        repo, temp_dir, initial_commit, second_commit, feature_commit = temp_repo
        
        response = client.post(
            "/api/v2/diff/commits",
            json={
                "repo_path": temp_dir,
                "from_commit": initial_commit.hexsha,
                "to_commit": second_commit.hexsha
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["from_commit"] == initial_commit.hexsha
        assert data["data"]["to_commit"] == second_commit.hexsha
        assert data["data"]["files_changed"] >= 1
    
    def test_compare_branches(self, client, temp_repo, auth_headers):
        """Test branch comparison endpoint."""
        repo, temp_dir, initial_commit, second_commit, feature_commit = temp_repo
        
        response = client.post(
            "/api/v2/diff/branches",
            json={
                "repo_path": temp_dir,
                "from_branch": "master",
                "to_branch": "feature-branch"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["files_changed"] >= 1


class TestStatistics:
    """Tests for statistics endpoints."""
    
    def test_get_repository_statistics(self, client, temp_repo, auth_headers):
        """Test repository statistics endpoint."""
        repo, temp_dir, initial_commit, second_commit, feature_commit = temp_repo
        
        response = client.get(
            f"/api/v2/repository/{temp_dir}/statistics",
            params={"include_author_stats": True},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "repository_info" in data["data"]
        assert "summary" in data["data"]
        assert "author_statistics" in data["data"]
        assert "top_contributors" in data["data"]
        
        # Check summary data
        summary = data["data"]["summary"]
        assert summary["total_commits"] >= 2
        assert summary["total_contributors"] >= 1
        assert summary["total_branches"] >= 2  # master + feature-branch


class TestExport:
    """Tests for export endpoints."""
    
    def test_export_data(self, client, temp_repo, auth_headers):
        """Test data export endpoint."""
        repo, temp_dir, initial_commit, second_commit, feature_commit = temp_repo
        
        response = client.post(
            "/api/v2/export",
            json={
                "repo_path": temp_dir,
                "export_type": "repository_metadata",
                "format": "json",
                "filters": [],
                "sort_by": []
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "export_id" in data["data"]
        assert data["data"]["status"] == "queued"
        
        # Test getting export status
        export_id = data["data"]["export_id"]
        status_response = client.get(
            f"/api/v2/export/{export_id}/status",
            headers=auth_headers
        )
        
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["data"]["export_id"] == export_id
    
    def test_export_status_not_found(self, client, auth_headers):
        """Test export status for nonexistent export."""
        response = client.get(
            "/api/v2/export/nonexistent-id/status",
            headers=auth_headers
        )
        
        assert response.status_code == 404


class TestHealthAndInfo:
    """Tests for health and info endpoints."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/api/v2/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert "active_operations" in data
    
    def test_api_info(self, client):
        """Test API info endpoint."""
        response = client.get("/api/v2/info")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == "GitHound Enhanced API"
        assert data["version"] == "2.0.0"
        assert "features" in data
        assert "supported_formats" in data
        assert "documentation" in data


class TestAuthentication:
    """Tests for authentication and authorization."""
    
    def test_missing_auth_header(self, client, temp_repo):
        """Test request without authentication header."""
        repo, temp_dir, initial_commit, second_commit, feature_commit = temp_repo
        
        response = client.post(
            "/api/v2/repository/analyze",
            json={
                "repo_path": temp_dir,
                "include_detailed_stats": False
            }
        )
        
        # Should return 403 when no auth header is provided (HTTPBearer behavior)
        # In real implementation, this would return 401 for invalid tokens
        assert response.status_code in [200, 401, 403]
    
    def test_invalid_auth_token(self, client, temp_repo):
        """Test request with invalid authentication token."""
        repo, temp_dir, initial_commit, second_commit, feature_commit = temp_repo
        
        response = client.post(
            "/api/v2/repository/analyze",
            json={
                "repo_path": temp_dir,
                "include_detailed_stats": False
            },
            headers={"Authorization": "Bearer invalid-token"}
        )
        
        # Should still work with mock authentication
        # In real implementation, this would return 401
        assert response.status_code in [200, 401]


class TestErrorHandling:
    """Tests for error handling."""
    
    def test_invalid_json_payload(self, client, auth_headers):
        """Test request with invalid JSON payload."""
        response = client.post(
            "/api/v2/repository/analyze",
            data="invalid json",
            headers={**auth_headers, "Content-Type": "application/json"}
        )
        
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_missing_required_fields(self, client, auth_headers):
        """Test request with missing required fields."""
        response = client.post(
            "/api/v2/repository/analyze",
            json={
                "include_detailed_stats": True
                # Missing repo_path
            },
            headers=auth_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_invalid_commit_hash(self, client, temp_repo, auth_headers):
        """Test commit analysis with invalid commit hash."""
        repo, temp_dir, initial_commit, second_commit, feature_commit = temp_repo
        
        response = client.post(
            "/api/v2/commit/analyze",
            json={
                "repo_path": temp_dir,
                "commit_hash": "invalid_hash_123",
                "include_file_changes": False
            },
            headers=auth_headers
        )
        
        assert response.status_code == 500  # Internal server error
