"""Shared test fixtures and configuration for GitHound tests."""

import asyncio
import shutil
import tempfile
from collections.abc import Generator
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest
import pytest_asyncio
from git import Repo

# Try to import FastMCP components, skip if not available
try:
    from fastmcp import Client, FastMCP
    from fastmcp.client.transports import StreamableHttpTransport
    from fastmcp.exceptions import McpError, ToolError

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
    from githound.mcp_server import get_mcp_server, mcp

    MCP_SERVER_AVAILABLE = True
except (ImportError, TypeError, AttributeError):
    # Handle various import errors including Pydantic compatibility issues
    mcp = None
    get_mcp_server = None
    MCP_SERVER_AVAILABLE = False

from githound.models import CommitInfo, RepositoryInfo, SearchQuery
from githound.search_engine import SearchOrchestrator


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    import os

    temp_dir = tempfile.mkdtemp()
    # Normalize path to handle Windows 8.3 short names
    normalized_path = Path(os.path.realpath(temp_dir))
    yield normalized_path
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_repo(temp_dir: Path) -> Generator[Repo, None, None]:
    """Create a temporary Git repository for testing."""
    repo = Repo.init(temp_dir)

    # Configure user for commits
    with repo.config_writer() as config:  # [attr-defined]
        config.set_value("user", "name", "Test User")  # [attr-defined]
        config.set_value("user", "email", "test@example.com")  # [attr-defined]

    # Create initial commit
    test_file = temp_dir / "README.md"
    test_file.write_text("# Test Repository\n\nThis is a test repository for GitHound tests.")
    repo.index.add([str(test_file)])
    repo.index.commit("Initial commit")

    # Create a second commit
    test_file2 = temp_dir / "src" / "main.py"
    test_file2.parent.mkdir(exist_ok=True)
    test_file2.write_text(
        "def main() -> None:\n    print('Hello, World!')\n\nif __name__ == '__main__':\n    main()"
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

    # Cleanup: Close the repository to release file handles
    repo.close()


@pytest.fixture
def temp_repo_with_commits(temp_dir: Path) -> Generator[tuple, None, None]:
    """Create a temporary Git repository with commit references for performance testing."""
    repo = Repo.init(temp_dir)

    # Configure user for commits
    with repo.config_writer() as config:  # [attr-defined]
        config.set_value("user", "name", "Test User")  # [attr-defined]
        config.set_value("user", "email", "test@example.com")  # [attr-defined]

    # Create initial commit
    test_file = temp_dir / "README.md"
    test_file.write_text("# Test Repository\n\nThis is a test repository for GitHound tests.")
    repo.index.add([str(test_file)])
    initial_commit = repo.index.commit("Initial commit")

    # Create a second commit
    test_file2 = temp_dir / "src" / "main.py"
    test_file2.parent.mkdir(exist_ok=True)
    test_file2.write_text(
        "def main() -> None:\n    print('Hello, World!')\n\nif __name__ == '__main__':\n    main()"
    )
    repo.index.add([str(test_file2)])
    second_commit = repo.index.commit("Add main.py")

    # Create a third commit
    test_file.write_text(
        "# Test Repository\n\nThis is a test repository for GitHound tests.\n\n## Features\n- Testing\n- Git operations"
    )
    repo.index.add([str(test_file)])
    repo.index.commit("Update README with features")

    yield (repo, temp_dir, initial_commit, second_commit)

    # Cleanup: Close the repository to release file handles
    repo.close()


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
async def mcp_server() -> None:
    """Create a fresh GitHound MCP server instance for testing.

    This fixture provides a clean server instance for in-memory testing
    following FastMCP best practices.
    """
    if not FASTMCP_AVAILABLE or not MCP_SERVER_AVAILABLE or mcp is None:
        pytest.skip("FastMCP or MCP server not available")

    return mcp


@pytest_asyncio.fixture
async def mcp_client(mcp_server) -> None:
    """Create a FastMCP client connected to the GitHound server using in-memory testing.

    This fixture demonstrates the FastMCP in-memory testing pattern where the server
    instance is passed directly to the client for zero-overhead testing.
    """
    if not FASTMCP_AVAILABLE:
        pytest.skip("FastMCP not available")
    async with Client(mcp_server) as client:
        yield client


@pytest_asyncio.fixture
async def mcp_client_legacy() -> None:
    """Create an MCP client for testing with the global server instance."""
    if not FASTMCP_AVAILABLE or not MCP_SERVER_AVAILABLE:
        pytest.skip("FastMCP or MCP server not available")
    async with Client(mcp) as client:
        yield client


@pytest_asyncio.fixture
async def http_mcp_client() -> None:
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
def reset_caches() -> None:
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
    mock_commits: list[Any] = []
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
def git_error_mock() -> None:
    """Create a mock that raises GitCommandError."""
    from git import GitCommandError

    mock = Mock()
    mock.side_effect = GitCommandError("git command failed", 1)
    return mock


# FastMCP Testing Fixtures following latest documentation patterns


@pytest.fixture
def mock_search_data() -> None:
    """Provide mock search data for testing search functionality."""
    return {
        "commits": [
            {
                "hash": "abc123",
                "message": "Add feature X",
                "author": "Test User",
                "date": "2024-01-01T00:00:00Z",
            },
            {
                "hash": "def456",
                "message": "Fix bug Y",
                "author": "Another User",
                "date": "2024-01-02T00:00:00Z",
            },
        ],
        "files": [
            {"path": "src/main.py", "content": "def main() -> None: pass"},
            {"path": "README.md", "content": "# Project"},
        ],
    }


@pytest.fixture
def auth_headers() -> None:
    """Provide authentication headers for testing."""
    return {
        "bearer": {"Authorization": "Bearer test-token-123"},
        "oauth": {"Authorization": "Bearer oauth-token-456"},
    }


@pytest.fixture
def mock_external_dependencies() -> None:
    """Mock external dependencies for deterministic testing."""
    with (
        patch("githound.git_handler.get_repository") as mock_get_repo,
        patch("githound.search_engine.SearchOrchestrator") as mock_orchestrator,
        patch("pathlib.Path.exists") as mock_path_exists,
    ):
        mock_path_exists.return_value = True
        mock_get_repo.return_value = Mock()
        mock_orchestrator.return_value = Mock()

        yield {
            "get_repository": mock_get_repo,
            "search_orchestrator": mock_orchestrator,
            "path_exists": mock_path_exists,
        }


@pytest.fixture
def performance_test_data() -> None:
    """Generate test data for performance testing."""
    return {
        "large_commit_list": [f"commit_{i:06d}" for i in range(10000)],
        "large_file_list": [f"file_{i:04d}.py" for i in range(1000)],
        "complex_search_patterns": [
            "function.*test.*",
            "class.*[A-Z][a-z]+.*",
            "import.*numpy.*",
            "def.*async.*",
        ],
    }


@pytest.fixture
def error_scenarios() -> None:
    """Provide various error scenarios for testing."""
    return {
        "invalid_repo_path": "/nonexistent/repo/path",
        "permission_denied": "/root/restricted/repo",
        "corrupted_git": "/corrupted/.git",
        "network_timeout": "https://timeout.example.com/repo.git",
        "invalid_commit_hash": "invalid_hash_123",
        "malformed_search_query": {"invalid": "query", "structure": None},
    }


# Enhanced API Test Fixtures


@pytest.fixture
def unauthenticated_client() -> None:
    """FastAPI test client WITHOUT authentication bypass (for security tests)."""
    from fastapi.testclient import TestClient

    from githound.web.main import app

    client = TestClient(app)
    yield client

    # Clean up any overrides
    app.dependency_overrides.clear()


@pytest.fixture
def api_client() -> None:
    """FastAPI test client for the enhanced API."""
    from fastapi.testclient import TestClient

    from githound.web.main import app
    from githound.web.services import auth_service

    # Override auth dependencies to bypass authentication in tests
    async def override_get_current_user():
        return {
            "user_id": "test_admin",
            "username": "test_admin",
            "email": "test@example.com",
            "roles": ["admin", "user"],
            "is_active": True,
            "created_at": "2024-01-01T00:00:00",
            "last_login": None,
        }

    # Override the dependency functions
    app.dependency_overrides[auth_service.get_current_user] = override_get_current_user
    app.dependency_overrides[auth_service.require_admin] = override_get_current_user
    app.dependency_overrides[auth_service.require_user] = override_get_current_user

    client = TestClient(app)
    yield client

    # Clean up overrides
    app.dependency_overrides.clear()


@pytest.fixture
async def async_api_client() -> None:
    """Async FastAPI test client for the enhanced API."""
    from httpx import AsyncClient

    from githound.web.main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def auth_manager() -> None:
    """Authentication manager for testing."""
    from githound.web.services.auth_service import AuthManager

    return AuthManager()


@pytest.fixture
def admin_token(auth_manager) -> None:
    """Generate admin JWT token for testing."""
    # Create the admin user first
    from githound.web.services.auth_service import UserCreate

    admin_user = UserCreate(
        username="test_admin",
        email="admin@example.com",
        password="admin123",
        roles=["admin", "user"],
    )

    try:
        auth_manager.create_user(admin_user)
    except Exception:
        # User might already exist, which is fine
        pass

    # Get the created user to get the proper user_id
    user = auth_manager.get_user("test_admin")
    if user:
        token_data = auth_manager.create_access_token(
            data={"sub": user.user_id, "username": user.username, "roles": user.roles}
        )
    else:
        # Fallback if user creation failed
        token_data = auth_manager.create_access_token(
            data={"sub": "test_admin", "username": "test_admin", "roles": ["admin", "user"]}
        )

    return token_data


@pytest.fixture
def user_token(auth_manager) -> None:
    """Generate user JWT token for testing."""
    token_data = auth_manager.create_access_token(
        data={"sub": "test_user", "username": "test_user", "roles": ["user"]}
    )
    return token_data


@pytest.fixture
def readonly_token(auth_manager) -> None:
    """Generate read-only JWT token for testing."""
    # Create the readonly user first
    from githound.web.services.auth_service import UserCreate

    readonly_user = UserCreate(
        username="test_readonly",
        email="readonly@example.com",
        password="readonly123",
        roles=["read_only"],
    )

    try:
        auth_manager.create_user(readonly_user)
    except Exception:
        # User might already exist, which is fine
        pass

    # Get the created user to get the proper user_id
    user = auth_manager.get_user("test_readonly")
    if user:
        token_data = auth_manager.create_access_token(
            data={"sub": user.user_id, "username": user.username, "roles": user.roles}
        )
    else:
        # Fallback if user creation failed
        token_data = auth_manager.create_access_token(
            data={"sub": "test_readonly", "username": "test_readonly", "roles": ["read_only"]}
        )

    return token_data


@pytest.fixture
def admin_auth_headers(admin_token) -> None:
    """Admin authentication headers for API requests."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def user_auth_headers(user_token) -> None:
    """User authentication headers for API requests."""
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def readonly_auth_headers(readonly_token) -> None:
    """Read-only authentication headers for API requests."""
    return {"Authorization": f"Bearer {readonly_token}"}


@pytest.fixture
def redis_client() -> None:
    """Redis client for testing rate limiting."""
    try:
        import redis

        client = redis.from_url("redis://localhost:6379/15", decode_responses=True)
        client.ping()  # Test connection
        client.flushdb()  # Clear test database
        yield client
        client.flushdb()  # Cleanup
        client.close()
    except (ImportError, redis.ConnectionError):
        pytest.skip("Redis not available for testing")


@pytest.fixture
def complex_git_repo(temp_dir) -> None:
    """Create a complex Git repository with multiple branches, merges, and history."""
    repo_path = temp_dir / "complex_repo"
    repo_path.mkdir()

    # Initialize repository
    repo = Repo.init(repo_path)

    # Configure user
    repo.config_writer().set_value("user", "name", "Test User").release()  # [attr-defined]
    repo.config_writer().set_value("user", "email", "test@example.com").release()  # [attr-defined]

    # Create main branch with multiple commits
    from git import Actor

    for i in range(5):
        file_path = repo_path / f"main_file_{i}.py"
        file_path.write_text(
            f"""
def function_{i}():
    '''Function {i} implementation'''
    return {i}

class Class{i}:
    def __init__(self) -> None:
        self.value = {i}

    def method(self) -> None:
        return self.value * 2
"""
        )
        repo.index.add([f"main_file_{i}.py"])

        # Use different authors for some commits
        if i % 2 == 0:
            author = Actor("Alice Developer", "alice@example.com")
        else:
            author = Actor("Bob Developer", "bob@example.com")

        repo.index.commit(f"Add main_file_{i}.py", author=author)

    # Create development branch
    dev_branch = repo.create_head("development")
    dev_branch.checkout()

    # Add commits to development branch
    for i in range(3):
        file_path = repo_path / f"dev_file_{i}.js"
        file_path.write_text(
            f"""
function devFunction{i}() {{
    console.log('Development function {i}');
    return {i};
}}

const devConstant{i} = {i * 10};
"""
        )
        repo.index.add([f"dev_file_{i}.js"])
        repo.index.commit(
            f"Add dev_file_{i}.js", author=Actor("Charlie Developer", "charlie@example.com")
        )

    # Create feature branch from development
    feature_branch = repo.create_head("feature/new-api", dev_branch)
    feature_branch.checkout()

    # Add feature commits
    api_file = repo_path / "api.py"
    api_file.write_text(
        """
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root() -> None:
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int) -> None:
    return {"item_id": item_id}
"""
    )
    repo.index.add(["api.py"])
    repo.index.commit(
        "Add FastAPI implementation", author=Actor("Alice Developer", "alice@example.com")
    )

    # Switch back to main and create tags
    repo.heads.master.checkout()
    repo.create_tag("v0.1.0", message="Initial version")
    repo.create_tag("v0.2.0", message="Second version")

    yield repo


@pytest.fixture
def large_git_repo(temp_dir) -> None:
    """Create a large Git repository for performance testing."""
    repo_path = temp_dir / "large_repo"
    repo_path.mkdir()

    # Initialize repository
    repo = Repo.init(repo_path)

    # Configure user
    repo.config_writer().set_value("user", "name", "Test User").release()  # [attr-defined]
    repo.config_writer().set_value("user", "email", "test@example.com").release()  # [attr-defined]

    # Create many files and commits
    from git import Actor

    for commit_num in range(50):  # 50 commits
        for file_num in range(5):  # 5 files per commit
            file_path = repo_path / f"dir_{commit_num % 10}" / f"file_{file_num}.txt"
            file_path.parent.mkdir(exist_ok=True)

            # Create file with substantial content
            content = f"Commit {commit_num}, File {file_num}\n"
            content += "\n".join([f"Line {i}: Some content here" for i in range(20)])
            file_path.write_text(content)

            repo.index.add([str(file_path.relative_to(repo_path))])

        # Vary commit authors
        authors = [
            Actor("Alice", "alice@example.com"),
            Actor("Bob", "bob@example.com"),
            Actor("Charlie", "charlie@example.com"),
            Actor("Diana", "diana@example.com"),
        ]
        author = authors[commit_num % len(authors)]

        repo.index.commit(f"Commit {commit_num}: Add batch of files", author=author)

    yield repo


# Test utilities
class TestUtils:
    """Utility functions for tests."""

    @staticmethod
    def create_test_file(repo_path: Path, filename: str, content: str) -> Path:
        """Create a test file in the repository."""
        file_path = repo_path / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return file_path

    @staticmethod
    def commit_file(repo: Repo, filename: str, message: str, author=None) -> str:
        """Commit a file and return the commit hash."""
        repo.index.add([filename])
        commit = repo.index.commit(message, author=author)
        return commit.hexsha

    @staticmethod
    def create_branch_with_commits(repo: Repo, branch_name: str, num_commits: int = 3) -> str:
        """Create a branch with specified number of commits."""
        branch = repo.create_head(branch_name)
        branch.checkout()

        last_commit = None
        for i in range(num_commits):
            file_path = Path(repo.working_dir) / f"{branch_name}_file_{i}.txt"
            file_path.write_text(f"Content for {branch_name} file {i}")
            repo.index.add([f"{branch_name}_file_{i}.txt"])
            commit = repo.index.commit(f"Add {branch_name}_file_{i}.txt")
            last_commit = commit.hexsha

        return last_commit

    @staticmethod
    def assert_api_response(
        response, expected_status: int = 200, expected_success: bool = True
    ) -> None:
        """Assert API response format and status."""
        assert response.status_code == expected_status

        if response.headers.get("content-type", "").startswith("application/json"):
            data = response.json()
            assert "success" in data
            assert data["success"] == expected_success
            assert "message" in data
            assert "timestamp" in data

            if expected_success:
                assert "data" in data


@pytest.fixture
def test_utils() -> None:
    """Test utilities fixture."""
    return TestUtils()


# Pytest configuration
def pytest_configure(config) -> None:
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")  # [attr-defined]
    config.addinivalue_line("markers", "integration: Integration tests")  # [attr-defined]
    config.addinivalue_line("markers", "e2e: End-to-end tests")  # [attr-defined]
    config.addinivalue_line("markers", "performance: Performance tests")  # [attr-defined]
    config.addinivalue_line("markers", "security: Security tests")  # [attr-defined]
    config.addinivalue_line("markers", "slow: Slow running tests")  # [attr-defined]
    config.addinivalue_line("markers", "redis: Tests requiring Redis")  # [attr-defined]
    config.addinivalue_line("markers", "websocket: WebSocket tests")  # [attr-defined]


def pytest_collection_modifyitems(config, items) -> None:
    """Modify test collection to add markers based on file paths."""
    for item in items:
        # Add markers based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        elif "security" in str(item.fspath):
            item.add_marker(pytest.mark.security)

        # Add slow marker for tests that might take longer
        if any(
            keyword in item.name.lower() for keyword in ["large", "performance", "load", "stress"]
        ):
            item.add_marker(pytest.mark.slow)
