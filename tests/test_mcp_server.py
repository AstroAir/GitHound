"""Tests for GitHound MCP Server functionality."""

import pytest
import tempfile
import shutil
import asyncio
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from fastmcp import Client
from git import Repo

from githound.mcp_server import (
    mcp, RepositoryInput, CommitAnalysisInput, CommitFilterInput,
    FileHistoryInput, BlameInput, DiffInput, BranchDiffInput, ExportInput
)


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
    
    yield repo, temp_dir, initial_commit, second_commit
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mcp_client():
    """Create an MCP client for testing."""
    return Client(mcp)


class TestMCPRepositoryAnalysis:
    """Tests for MCP repository analysis tools."""
    
    @pytest.mark.asyncio
    async def test_analyze_repository(self, temp_repo, mcp_client):
        """Test repository analysis MCP tool."""
        repo, temp_dir, initial_commit, second_commit = temp_repo
        
        async with mcp_client:
            result = await mcp_client.call_tool(
                "analyze_repository",
                {"repo_path": temp_dir}
            )
            
            assert result is not None
            result_data = result.content[0].text
            
            # Parse the JSON response
            import json
            response = json.loads(result_data)
            
            assert response["status"] == "success"
            assert "repository_metadata" in response
            assert response["repository_metadata"]["total_commits"] >= 2
            assert len(response["repository_metadata"]["contributors"]) >= 1
    
    @pytest.mark.asyncio
    async def test_analyze_commit(self, temp_repo, mcp_client):
        """Test commit analysis MCP tool."""
        repo, temp_dir, initial_commit, second_commit = temp_repo
        
        async with mcp_client:
            result = await mcp_client.call_tool(
                "analyze_commit",
                {
                    "repo_path": temp_dir,
                    "commit_hash": second_commit.hexsha
                }
            )
            
            assert result is not None
            result_data = result.content[0].text
            
            import json
            response = json.loads(result_data)
            
            assert response["status"] == "success"
            assert "commit_metadata" in response
            assert response["commit_metadata"]["hash"] == second_commit.hexsha
            assert response["commit_metadata"]["author_name"] == "Test User"
    
    @pytest.mark.asyncio
    async def test_get_filtered_commits(self, temp_repo, mcp_client):
        """Test filtered commit retrieval MCP tool."""
        repo, temp_dir, initial_commit, second_commit = temp_repo
        
        async with mcp_client:
            result = await mcp_client.call_tool(
                "get_filtered_commits",
                {
                    "repo_path": temp_dir,
                    "author_pattern": "Test User",
                    "max_count": 10
                }
            )
            
            assert result is not None
            result_data = result.content[0].text
            
            import json
            response = json.loads(result_data)
            
            assert response["status"] == "success"
            assert "commits" in response
            assert response["total_results"] >= 2
            assert len(response["commits"]) >= 2
    
    @pytest.mark.asyncio
    async def test_get_file_history(self, temp_repo, mcp_client):
        """Test file history MCP tool."""
        repo, temp_dir, initial_commit, second_commit = temp_repo
        
        async with mcp_client:
            result = await mcp_client.call_tool(
                "get_file_history",
                {
                    "repo_path": temp_dir,
                    "file_path": "test.py",
                    "max_count": 10
                }
            )
            
            assert result is not None
            result_data = result.content[0].text
            
            import json
            response = json.loads(result_data)
            
            assert response["status"] == "success"
            assert "history" in response
            assert response["total_commits"] >= 2
            assert response["file_path"] == "test.py"


class TestMCPBlameAndDiff:
    """Tests for MCP blame and diff analysis tools."""
    
    @pytest.mark.asyncio
    async def test_analyze_file_blame(self, temp_repo, mcp_client):
        """Test file blame analysis MCP tool."""
        repo, temp_dir, initial_commit, second_commit = temp_repo
        
        async with mcp_client:
            result = await mcp_client.call_tool(
                "analyze_file_blame",
                {
                    "repo_path": temp_dir,
                    "file_path": "test.py"
                }
            )
            
            assert result is not None
            result_data = result.content[0].text
            
            import json
            response = json.loads(result_data)
            
            assert response["status"] == "success"
            assert "file_blame" in response
            assert response["file_blame"]["total_lines"] >= 4
            assert len(response["file_blame"]["contributors"]) >= 1
    
    @pytest.mark.asyncio
    async def test_compare_commits_diff(self, temp_repo, mcp_client):
        """Test commit comparison MCP tool."""
        repo, temp_dir, initial_commit, second_commit = temp_repo
        
        async with mcp_client:
            result = await mcp_client.call_tool(
                "compare_commits_diff",
                {
                    "repo_path": temp_dir,
                    "from_commit": initial_commit.hexsha,
                    "to_commit": second_commit.hexsha
                }
            )
            
            assert result is not None
            result_data = result.content[0].text
            
            import json
            response = json.loads(result_data)
            
            assert response["status"] == "success"
            assert "commit_diff" in response
            assert response["commit_diff"]["files_changed"] >= 1
            assert response["commit_diff"]["from_commit"] == initial_commit.hexsha
            assert response["commit_diff"]["to_commit"] == second_commit.hexsha
    
    @pytest.mark.asyncio
    async def test_get_author_stats(self, temp_repo, mcp_client):
        """Test author statistics MCP tool."""
        repo, temp_dir, initial_commit, second_commit = temp_repo
        
        async with mcp_client:
            result = await mcp_client.call_tool(
                "get_author_stats",
                {"repo_path": temp_dir}
            )
            
            assert result is not None
            result_data = result.content[0].text
            
            import json
            response = json.loads(result_data)
            
            assert response["status"] == "success"
            assert "author_statistics" in response
            assert response["total_authors"] >= 1
            
            # Check that Test User is in the statistics
            author_key = "Test User <test@example.com>"
            assert author_key in response["author_statistics"]


class TestMCPResources:
    """Tests for MCP resources."""
    
    @pytest.mark.asyncio
    async def test_repository_config_resource(self, temp_repo, mcp_client):
        """Test repository configuration resource."""
        repo, temp_dir, initial_commit, second_commit = temp_repo
        
        async with mcp_client:
            result = await mcp_client.read_resource(
                f"githound://repository/{temp_dir}/config"
            )
            
            assert result is not None
            assert len(result) > 0
            
            content = result[0].text
            assert "GitHound Repository Configuration" in content
            assert "Total Commits" in content
            assert "Contributors" in content
    
    @pytest.mark.asyncio
    async def test_repository_branches_resource(self, temp_repo, mcp_client):
        """Test repository branches resource."""
        repo, temp_dir, initial_commit, second_commit = temp_repo
        
        async with mcp_client:
            result = await mcp_client.read_resource(
                f"githound://repository/{temp_dir}/branches"
            )
            
            assert result is not None
            assert len(result) > 0
            
            content = result[0].text
            assert "Repository Branches" in content
            assert "master" in content or "main" in content
    
    @pytest.mark.asyncio
    async def test_repository_contributors_resource(self, temp_repo, mcp_client):
        """Test repository contributors resource."""
        repo, temp_dir, initial_commit, second_commit = temp_repo
        
        async with mcp_client:
            result = await mcp_client.read_resource(
                f"githound://repository/{temp_dir}/contributors"
            )
            
            assert result is not None
            assert len(result) > 0
            
            content = result[0].text
            assert "Repository Contributors" in content
            assert "Test User" in content


class TestMCPExport:
    """Tests for MCP export functionality."""
    
    @pytest.mark.asyncio
    async def test_export_repository_data_json(self, temp_repo, mcp_client):
        """Test repository data export in JSON format."""
        repo, temp_dir, initial_commit, second_commit = temp_repo
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_file = f.name
        
        try:
            async with mcp_client:
                result = await mcp_client.call_tool(
                    "export_repository_data",
                    {
                        "repo_path": temp_dir,
                        "output_path": output_file,
                        "format": "json",
                        "include_metadata": True
                    }
                )
                
                assert result is not None
                result_data = result.content[0].text
                
                import json
                response = json.loads(result_data)
                
                assert response["status"] == "success"
                assert response["format"] == "json"
                assert Path(output_file).exists()
                
                # Verify the exported file contains valid JSON
                with open(output_file, 'r') as f:
                    exported_data = json.load(f)
                    assert "total_commits" in exported_data
                    assert exported_data["total_commits"] >= 2
                    
        finally:
            if Path(output_file).exists():
                Path(output_file).unlink()


class TestMCPErrorHandling:
    """Tests for MCP error handling."""
    
    @pytest.mark.asyncio
    async def test_invalid_repository_path(self, mcp_client):
        """Test error handling for invalid repository path."""
        async with mcp_client:
            result = await mcp_client.call_tool(
                "analyze_repository",
                {"repo_path": "/nonexistent/path"}
            )
            
            assert result is not None
            result_data = result.content[0].text
            
            import json
            response = json.loads(result_data)
            
            assert response["status"] == "error"
            assert "error" in response
    
    @pytest.mark.asyncio
    async def test_invalid_commit_hash(self, temp_repo, mcp_client):
        """Test error handling for invalid commit hash."""
        repo, temp_dir, initial_commit, second_commit = temp_repo
        
        async with mcp_client:
            result = await mcp_client.call_tool(
                "analyze_commit",
                {
                    "repo_path": temp_dir,
                    "commit_hash": "invalid_hash_123"
                }
            )
            
            assert result is not None
            result_data = result.content[0].text
            
            import json
            response = json.loads(result_data)
            
            assert response["status"] == "error"
            assert "error" in response
    
    @pytest.mark.asyncio
    async def test_invalid_file_path_blame(self, temp_repo, mcp_client):
        """Test error handling for invalid file path in blame analysis."""
        repo, temp_dir, initial_commit, second_commit = temp_repo
        
        async with mcp_client:
            result = await mcp_client.call_tool(
                "analyze_file_blame",
                {
                    "repo_path": temp_dir,
                    "file_path": "nonexistent.py"
                }
            )
            
            assert result is not None
            result_data = result.content[0].text
            
            import json
            response = json.loads(result_data)
            
            assert response["status"] == "error"
            assert "error" in response
