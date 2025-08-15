"""Shared test fixtures and configuration for GitHound tests."""

import asyncio
import tempfile
import shutil
import pytest
from datetime import datetime
from pathlib import Path
from typing import Generator, Dict, Any, AsyncGenerator
from unittest.mock import Mock, AsyncMock, patch

from git import Repo
from fastapi.testclient import TestClient
from fastmcp import Client as MCPClient

from githound.models import SearchQuery, CommitInfo, RepositoryInfo
from githound.search_engine import SearchOrchestrator
from githound.mcp_server import mcp


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_repo(temp_dir: Path) -> Generator[Repo, None, None]:
    """Create a temporary Git repository for testing."""
    repo = Repo.init(temp_dir)
    
    # Configure user for commits
    with repo.config_writer() as config:
        config.set_value("user", "name", "Test User")
        config.set_value("user", "email", "test@example.com")
    
    # Create initial commit
    test_file = temp_dir / "README.md"
    test_file.write_text("# Test Repository\n\nThis is a test repository for GitHound tests.")
    repo.index.add([str(test_file)])
    repo.index.commit("Initial commit")
    
    # Create a second commit
    test_file2 = temp_dir / "src" / "main.py"
    test_file2.parent.mkdir(exist_ok=True)
    test_file2.write_text("def main():\n    print('Hello, World!')\n\nif __name__ == '__main__':\n    main()")
    repo.index.add([str(test_file2)])
    repo.index.commit("Add main.py")
    
    # Create a third commit
    test_file.write_text("# Test Repository\n\nThis is a test repository for GitHound tests.\n\n## Features\n- Testing\n- Git operations")
    repo.index.add([str(test_file)])
    repo.index.commit("Update README with features")
    
    yield repo


@pytest.fixture
def sample_search_query() -> SearchQuery:
    """Create a sample search query for testing."""
    return SearchQuery(
        content_pattern="test",
        author_pattern="Test User",
        message_pattern="commit",
        fuzzy_search=True,
        fuzzy_threshold=0.8
    )


@pytest.fixture
def sample_commit_info() -> CommitInfo:
    """Create a sample commit info for testing."""
    return CommitInfo(
        hash="abc123def456",
        short_hash="abc123d",
        author_name="Test User",
        author_email="test@example.com",
        committer_name="Test User",
        committer_email="test@example.com",
        message="Test commit message",
        date=datetime(2024, 1, 1, 12, 0, 0),
        files_changed=2,
        insertions=10,
        deletions=5
    )


@pytest.fixture
def sample_repository_info() -> RepositoryInfo:
    """Create a sample repository info for testing."""
    return RepositoryInfo(
        path="/test/repo",
        name="test-repo",
        is_bare=False,
        total_commits=100,
        contributors=["Test User", "Another User"]
    )


@pytest.fixture
def search_orchestrator() -> SearchOrchestrator:
    """Create a search orchestrator for testing."""
    return SearchOrchestrator()


@pytest.fixture
async def mcp_client() -> AsyncGenerator[MCPClient, None]:
    """Create an MCP client for testing."""
    client = MCPClient(mcp)
    await client._connect()
    yield client
    await client._disconnect()


@pytest.fixture
def mock_repo() -> Mock:
    """Create a mock Git repository."""
    mock_repo = Mock(spec=Repo)
    mock_repo.git_dir = "/test/repo/.git"
    mock_repo.working_dir = "/test/repo"
    mock_repo.heads = []
    mock_repo.tags = []
    mock_repo.remotes = []
    return mock_repo


@pytest.fixture
def mock_commit() -> Mock:
    """Create a mock Git commit."""
    mock_commit = Mock()
    mock_commit.hexsha = "abc123def456789"
    mock_commit.author.name = "Test User"
    mock_commit.author.email = "test@example.com"
    mock_commit.committer.name = "Test User"
    mock_commit.committer.email = "test@example.com"
    mock_commit.message = "Test commit message"
    mock_commit.committed_datetime.isoformat.return_value = "2024-01-01T12:00:00Z"
    mock_commit.stats.files = {"test.py": {"insertions": 10, "deletions": 5}}
    return mock_commit


@pytest.fixture
def test_data_dir() -> Path:
    """Get the test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture(autouse=True)
def reset_caches():
    """Reset any global caches before each test."""
    # Add any cache clearing logic here
    yield
    # Cleanup after test if needed


# Performance test fixtures
@pytest.fixture
def large_repo_mock() -> Mock:
    """Create a mock for a large repository for performance testing."""
    mock_repo = Mock(spec=Repo)
    mock_repo.git_dir = "/large/repo/.git"
    mock_repo.working_dir = "/large/repo"
    
    # Simulate large repository
    mock_commits = []
    for i in range(10000):
        commit = Mock()
        commit.hexsha = f"commit{i:06d}" + "0" * 34
        commit.author.name = f"User {i % 100}"
        commit.author.email = f"user{i % 100}@example.com"
        commit.message = f"Commit {i}: Some changes"
        mock_commits.append(commit)
    
    mock_repo.iter_commits.return_value = mock_commits
    return mock_repo


# Error simulation fixtures
@pytest.fixture
def git_error_mock():
    """Create a mock that raises GitCommandError."""
    from git import GitCommandError
    mock = Mock()
    mock.side_effect = GitCommandError("git command failed", 1)
    return mock
