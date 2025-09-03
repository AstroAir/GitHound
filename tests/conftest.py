"""Shared test fixtures and configuration for GitHound tests."""

import asyncio
import shutil
import tempfile
from collections.abc import AsyncGenerator, Generator
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest
import pytest_asyncio
from git import Repo
from unittest.mock import AsyncMock, MagicMock, patch

# Try to import FastMCP components, skip if not available
try:
    from fastmcp import FastMCP, Client
    from fastmcp.client.transports import StreamableHttpTransport
    from fastmcp.exceptions import ToolError, McpError
    FASTMCP_AVAILABLE = True
except ImportError:
    # Create mock classes for when FastMCP is not available
    FastMCP = None
    Client = None
    StreamableHttpTransport = None
    ToolError = Exception
    McpError = Exception
    FASTMCP_AVAILABLE = False

try:
    from githound.mcp_server import mcp, get_mcp_server
    MCP_SERVER_AVAILABLE = True
except ImportError:
    mcp = None
    get_mcp_server = None
    MCP_SERVER_AVAILABLE = False

from githound.models import CommitInfo, RepositoryInfo, SearchQuery
from githound.search_engine import SearchOrchestrator


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
    test_file2.write_text(
        "def main():\n    print('Hello, World!')\n\nif __name__ == '__main__':\n    main()"
    )
    repo.index.add([str(test_file2)])
    repo.index.commit("Add main.py")

    # Create a third commit
    test_file.write_text(
        "# Test Repository\n\nThis is a test repository for GitHound tests.\n\n## Features\n- Testing\n- Git operations"
    )
    repo.index.add([str(test_file)])
    repo.index.commit("Update README with features")

    yield repo


@pytest.fixture
def temp_repo_with_commits(temp_dir: Path) -> Generator[tuple, None, None]:
    """Create a temporary Git repository with commit references for performance testing."""
    repo = Repo.init(temp_dir)

    # Configure user for commits
    with repo.config_writer() as config:
        config.set_value("user", "name", "Test User")
        config.set_value("user", "email", "test@example.com")

    # Create initial commit
    test_file = temp_dir / "README.md"
    test_file.write_text("# Test Repository\n\nThis is a test repository for GitHound tests.")
    repo.index.add([str(test_file)])
    initial_commit = repo.index.commit("Initial commit")

    # Create a second commit
    test_file2 = temp_dir / "src" / "main.py"
    test_file2.parent.mkdir(exist_ok=True)
    test_file2.write_text(
        "def main():\n    print('Hello, World!')\n\nif __name__ == '__main__':\n    main()"
    )
    repo.index.add([str(test_file2)])
    second_commit = repo.index.commit("Add main.py")

    # Create a third commit
    test_file.write_text(
        "# Test Repository\n\nThis is a test repository for GitHound tests.\n\n## Features\n- Testing\n- Git operations"
    )
    repo.index.add([str(test_file)])
    third_commit = repo.index.commit("Update README with features")

    yield (repo, temp_dir, initial_commit, second_commit)


@pytest.fixture
def sample_search_query() -> SearchQuery:
    """Create a sample search query for testing."""
    return SearchQuery(
        content_pattern="test",
        author_pattern="Test User",
        message_pattern="commit",
        fuzzy_search=True,
        fuzzy_threshold=0.8,
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
        deletions=5,
    )


@pytest.fixture
def sample_repository_info() -> RepositoryInfo:
    """Create a sample repository info for testing."""
    return RepositoryInfo(
        path="/test/repo",
        name="test-repo",
        is_bare=False,
        total_commits=100,
        contributors=["Test User", "Another User"],
    )


@pytest.fixture
def search_orchestrator() -> SearchOrchestrator:
    """Create a search orchestrator for testing."""
    return SearchOrchestrator()


@pytest_asyncio.fixture
async def mcp_server():
    """Create a fresh GitHound MCP server instance for testing.

    This fixture provides a clean server instance for in-memory testing
    following FastMCP best practices.
    """
    if not FASTMCP_AVAILABLE or not MCP_SERVER_AVAILABLE:
        pytest.skip("FastMCP or MCP server not available")
    from githound.mcp_server import mcp
    return mcp


@pytest_asyncio.fixture
async def mcp_client(mcp_server):
    """Create a FastMCP client connected to the GitHound server using in-memory testing.

    This fixture demonstrates the FastMCP in-memory testing pattern where the server
    instance is passed directly to the client for zero-overhead testing.
    """
    if not FASTMCP_AVAILABLE:
        pytest.skip("FastMCP not available")
    async with Client(mcp_server) as client:
        yield client


@pytest_asyncio.fixture
async def mcp_client_legacy():
    """Create an MCP client for testing with the global server instance."""
    if not FASTMCP_AVAILABLE or not MCP_SERVER_AVAILABLE:
        pytest.skip("FastMCP or MCP server not available")
    async with Client(mcp) as client:
        yield client


@pytest_asyncio.fixture
async def http_mcp_client():
    """Create an HTTP transport MCP client for integration testing.

    This fixture is for testing actual HTTP transport behavior.
    Note: Requires a running MCP server on localhost:3000
    """
    if not FASTMCP_AVAILABLE:
        pytest.skip("FastMCP not available")
    try:
        async with Client("http://localhost:3000/mcp/") as client:
            yield client
    except Exception:
        pytest.skip("HTTP MCP server not available for integration testing")


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


# FastMCP Testing Fixtures following latest documentation patterns

@pytest.fixture
def mock_search_data():
    """Provide mock search data for testing search functionality."""
    return {
        "commits": [
            {
                "hash": "abc123",
                "message": "Add feature X",
                "author": "Test User",
                "date": "2024-01-01T00:00:00Z"
            },
            {
                "hash": "def456",
                "message": "Fix bug Y",
                "author": "Another User",
                "date": "2024-01-02T00:00:00Z"
            }
        ],
        "files": [
            {"path": "src/main.py", "content": "def main(): pass"},
            {"path": "README.md", "content": "# Project"}
        ]
    }


@pytest.fixture
def auth_headers():
    """Provide authentication headers for testing."""
    return {
        "bearer": {"Authorization": "Bearer test-token-123"},
        "oauth": {"Authorization": "Bearer oauth-token-456"}
    }


@pytest.fixture
def mock_external_dependencies():
    """Mock external dependencies for deterministic testing."""
    with patch('githound.git_handler.get_repository') as mock_get_repo, \
         patch('githound.search_engine.SearchOrchestrator') as mock_orchestrator, \
         patch('pathlib.Path.exists') as mock_path_exists:

        mock_path_exists.return_value = True
        mock_get_repo.return_value = Mock()
        mock_orchestrator.return_value = Mock()

        yield {
            'get_repository': mock_get_repo,
            'search_orchestrator': mock_orchestrator,
            'path_exists': mock_path_exists
        }


@pytest.fixture
def performance_test_data():
    """Generate test data for performance testing."""
    return {
        "large_commit_list": [f"commit_{i:06d}" for i in range(10000)],
        "large_file_list": [f"file_{i:04d}.py" for i in range(1000)],
        "complex_search_patterns": [
            "function.*test.*",
            "class.*[A-Z][a-z]+.*",
            "import.*numpy.*",
            "def.*async.*"
        ]
    }


@pytest.fixture
def error_scenarios():
    """Provide various error scenarios for testing."""
    return {
        "invalid_repo_path": "/nonexistent/repo/path",
        "permission_denied": "/root/restricted/repo",
        "corrupted_git": "/corrupted/.git",
        "network_timeout": "https://timeout.example.com/repo.git",
        "invalid_commit_hash": "invalid_hash_123",
        "malformed_search_query": {"invalid": "query", "structure": None}
    }
