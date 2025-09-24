"""
Test Helper Utilities

This module provides utility functions and classes for testing MCP server
examples. It includes mock implementations, test data generators, and
common testing patterns.
"""

import asyncio
import json
import tempfile
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, cast, Tuple, Any
import logging

logger = logging.getLogger(__name__)


class MockGitRepository:
    """Mock Git repository for testing."""

    def __init__(self, name: str = "test-repo", commit_count: int = 10) -> None:
        """
        Initialize mock Git repository.

        Args:
            name: Repository name
            commit_count: Number of commits to simulate
        """
        self.name = name
        self.commit_count = commit_count
        self.authors = [
            {"name": "Alice Developer", "email": "alice@example.com"},
            {"name": "Bob Coder", "email": "bob@example.com"},
            {"name": "Carol Contributor", "email": "carol@example.com"}
        ]
        self.files = ["README.md", "src/main.py", "tests/test_main.py", "setup.py"]
        self.branches = ["main", "develop", "feature/new-feature"]
        self.tags = ["v1.0.0", "v1.1.0", "v2.0.0"]

    def generate_commits(self) -> List[Dict[str, Any]]:
        """Generate mock commit data."""
        commits: list[Any] = []
        base_date = datetime.now() - timedelta(days=self.commit_count)

        for i in range(self.commit_count):
            author = self.authors[i % len(self.authors)]
            commit_date = base_date + timedelta(days=i)

            commits.append({
                "hash": f"commit_hash_{i:03d}",
                "author": author["name"],
                "author_email": author["email"],
                "date": commit_date.isoformat if commit_date is not None else None(),
                "message": f"Commit message {i}",
                "files_changed": min(3, len(self.files)),
                "insertions": 10 + (i * 2),
                "deletions": 2 + i
            })

        return commits

    def generate_author_stats(self) -> Dict[str, Any]:
        """Generate mock author statistics."""
        commits = self.generate_commits()
        author_stats: dict[str, Any] = {}

        for commit in commits:
            author_key = (commit["author"], commit["author_email"])
            if author_key not in author_stats:
                author_stats[author_key] = {
                    "name": commit["author"],
                    "email": commit["author_email"],
                    "commits": 0,
                    "insertions": 0,
                    "deletions": 0,
                    "files_modified": set()
                }

            stats = author_stats[author_key]
            stats["commits"] += 1
            stats["insertions"] += commit["insertions"]
            stats["deletions"] += commit["deletions"]
            stats["files_modified"].update(self.files[:commit["files_changed"]])

        # Convert sets to counts
        authors: list[Any] = []
        for stats in author_stats.values():
            authors.append({
                "name": stats["name"],
                "email": stats["email"],
                "commits": stats["commits"],
                "insertions": stats["insertions"],
                "deletions": stats["deletions"],
                "files_modified": len(stats["files_modified"])
            })

        return {
            "total_authors": len(authors),
            "authors": authors
        }

    def generate_repository_info(self) -> Dict[str, Any]:
        """Generate mock repository information."""
        commits = self.generate_commits()

        return {
            "name": self.name,
            "path": f"/tmp/{self.name}",
            "total_commits": len(commits),
            "total_files": len(self.files),
            "total_authors": len(self.authors),
            "branches": self.branches,
            "tags": self.tags,
            "first_commit_date": commits[0]["date"] if commits else None,
            "last_commit_date": commits[-1]["date"] if commits else None
        }


class MockMCPClient:
    """Mock MCP client for testing."""

    def __init__(self, mock_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize mock MCP client.

        Args:
            mock_data: Optional mock data to return
        """
        self.mock_data = mock_data or {}
        self.call_history: List[Tuple[str, Dict[str, Any]]] = []
        self.connected = False

    async def __aenter__(self) -> None:
        """Async context manager entry."""
        self.connected = True
        return self

    async def __aexit__(self, _exc_type, _exc_val, _exc_tb) -> None:
        """Async context manager exit."""
        self.connected = False

    async def list_tools(self) -> List[Dict[str, Any]]:
        """Mock list_tools implementation."""
        self.call_history.append(("list_tools", {}))

        return cast(List[Dict[str, Any]], self.mock_data.get("tools", [
            {"name": "echo", "description": "Echo a message"},
            {"name": "add_numbers", "description": "Add two numbers"},
            {"name": "get_server_info", "description": "Get server information"}
        ]))

    async def call_tool(self, name: str, args: Dict[str, Any]) -> Any:
        """Mock call_tool implementation."""
        self.call_history.append(("call_tool", {"name": name, "args": args}))

        # Return mock data based on tool name
        if name == "echo":
            return MockToolResult({"message": args.get("message", "default")})
        elif name == "add_numbers":
            a = args.get("a", 0)
            b = args.get("b", 0)
            return MockToolResult({"sum": a + b, "operation": "addition"})
        elif name == "get_server_info":
            return MockToolResult({"name": "Mock Server", "version": "1.0.0"})
        else:
            raise ValueError(f"Unknown tool: {name}")

    async def list_resources(self) -> List[Dict[str, Any]]:
        """Mock list_resources implementation."""
        self.call_history.append(("list_resources", {}))

        return cast(List[Dict[str, Any]], self.mock_data.get("resources", [
            {"uri": "mock://server/info", "name": "Server Info"},
            {"uri": "mock://config/settings", "name": "Configuration"}
        ]))

    async def read_resource(self, uri: str) -> List[Dict[str, Any]]:
        """Mock read_resource implementation."""
        self.call_history.append(("read_resource", {"uri": uri}))

        # Return mock content based on URI
        if "info" in uri:
            content = {"server": "mock", "version": "1.0.0", "status": "running"}
        elif "config" in uri:
            content = {"setting1": "value1", "setting2": "value2"}
        else:
            content = {"message": "Mock resource content"}

        # Return as list of dicts to match the annotated return type
        return [{"text": json.dumps(content, indent=2)}]


class MockToolResult:
    """Mock tool result object."""

    def __init__(self, data: Any, content: Optional[List[Any]] = None) -> None:
        """
        Initialize mock tool result.

        Args:
            data: Result data
            content: Optional content blocks
        """
        self.data = data
        self.content = content or []


class MockResourceContent:
    """Mock resource content object."""

    def __init__(self, text: str) -> None:
        """
        Initialize mock resource content.

        Args:
            text: Text content
        """
        self.text = text


class TestDataGenerator:
    """Generate test data for various scenarios."""

    @staticmethod
    def generate_large_commit_history(count: int = 1000) -> List[Dict[str, Any]]:
        """
        Generate large commit history for performance testing.

        Args:
            count: Number of commits to generate

        Returns:
            List of commit dictionaries
        """
        commits: list[Any] = []
        base_date = datetime.now() - timedelta(days=count)
        authors = [
            "Alice Developer <alice@example.com>",
            "Bob Coder <bob@example.com>",
            "Carol Contributor <carol@example.com>",
            "Dave Designer <dave@example.com>",
            "Eve Engineer <eve@example.com>"
        ]

        for i in range(count):
            author = authors[i % len(authors)]
            commit_date = base_date + timedelta(hours=i * 2)

            commits.append({
                "hash": f"large_commit_{i:06d}",
                "author": author.split if author is not None else None(" <")[0],
                "author_email": author.split(" <")[1].rstrip(">"),
                "date": commit_date.isoformat(),
                "message": f"Large test commit {i}: Implement feature {i % 10}",
                "files_changed": (i % 5) + 1,
                "insertions": (i % 50) + 10,
                "deletions": (i % 20) + 2
            })

        return commits

    @staticmethod
    def generate_complex_repository_structure() -> Dict[str, Any]:
        """
        Generate complex repository structure for testing.

        Returns:
            Dictionary containing complex repository data
        """
        return {
            "name": "complex-project",
            "path": "/tmp/complex-project",
            "total_commits": 2500,
            "total_files": 150,
            "total_authors": 25,
            "branches": [
                "main", "develop", "release/v2.0", "feature/authentication",
                "feature/api-redesign", "hotfix/security-patch", "experimental/ml-integration"
            ],
            "tags": [
                "v1.0.0", "v1.1.0", "v1.2.0", "v1.3.0", "v2.0.0-alpha",
                "v2.0.0-beta", "v2.0.0-rc1", "v2.0.0"
            ],
            "languages": {
                "Python": 45.2,
                "JavaScript": 25.8,
                "TypeScript": 15.3,
                "HTML": 8.1,
                "CSS": 3.9,
                "Shell": 1.7
            },
            "directories": [
                "src/", "tests/", "docs/", "scripts/", "config/",
                "src/api/", "src/frontend/", "src/backend/", "src/shared/",
                "tests/unit/", "tests/integration/", "tests/e2e/"
            ]
        }


class PerformanceTimer:
    """Utility for measuring performance in tests."""

    def __init__(self, name: str) -> None:
        """
        Initialize performance timer.

        Args:
            name: Name of the operation being timed
        """
        self.name = name
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def __enter__(self) -> "PerformanceTimer":
        """Context manager entry."""
        self.start_time = asyncio.get_event_loop().time()
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_val: BaseException | None,
        _exc_tb: object | None
    ) -> None:
        """Context manager exit."""
        self.end_time = asyncio.get_event_loop().time()

    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        if self.start_time is None or self.end_time is None:
            return 0.0
        return self.end_time - self.start_time

    def assert_within_threshold(self, threshold: float) -> None:
        """
        Assert that elapsed time is within threshold.

        Args:
            threshold: Maximum allowed time in seconds
        """
        elapsed = self.elapsed_time
        assert elapsed <= threshold, f"{self.name} took {elapsed:.3f}s, expected <= {threshold}s"


class GitRepositoryBuilder:
    """Builder for creating test Git repositories."""

    def __init__(self, temp_dir: Optional[Path] = None) -> None:
        """
        Initialize Git repository builder.

        Args:
            temp_dir: Optional temporary directory to use
        """
        self.temp_dir = temp_dir or Path(tempfile.mkdtemp())
        self.repo_path: Optional[Path] = None
        self.commits: List[Dict[str, Any]] = []
        self.files: List[str] = []

    def create_repository(self, name: str = "test-repo") -> "GitRepositoryBuilder":
        """
        Create a new Git repository.

        Args:
            name: Repository name

        Returns:
            Self for method chaining
        """
        self.repo_path = self.temp_dir / name
        self.repo_path.mkdir(parents=True, exist_ok=True)

        # Initialize Git repository
        subprocess.run(["git", "init"], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.repo_path, check=True)  # [attr-defined]
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.repo_path, check=True)  # [attr-defined]

        return self

    def add_file(self, file_path: str, content: str) -> "GitRepositoryBuilder":
        """
        Add a file to the repository.

        Args:
            file_path: Path to the file within the repository
            content: File content

        Returns:
            Self for method chaining
        """
        if not self.repo_path:
            raise ValueError("Repository not created. Call create_repository() first.")
        assert self.repo_path is not None

        full_path = self.repo_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)

        self.files.append(file_path)
        return self

    def commit(self, message: str, author: Optional[str] = None) -> "GitRepositoryBuilder":
        """
        Create a commit with current changes.

        Args:
            message: Commit message
            author: Optional author override

        Returns:
            Self for method chaining
        """
        if not self.repo_path:
            raise ValueError("Repository not created. Call create_repository() first.")
        assert self.repo_path is not None

        # Add all files
        subprocess.run(["git", "add", "."], cwd=self.repo_path, check=True)

        # Create commit
        commit_args = ["git", "commit", "-m", message]
        if author:
            commit_args.extend(["--author", author])

        subprocess.run(commit_args, cwd=self.repo_path, check=True, capture_output=True)

        # Get commit hash
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.repo_path,
            check=True,
            capture_output=True,
            text=True
        )
        commit_hash = result.stdout.strip()

        self.commits.append({
            "hash": commit_hash,
            "message": message,
            "author": author or "Test User <test@example.com>"
        })

        return self

    def create_branch(self, branch_name: str) -> "GitRepositoryBuilder":
        """
        Create a new branch.

        Args:
            branch_name: Name of the branch to create

        Returns:
            Self for method chaining
        """
        if not self.repo_path:
            raise ValueError("Repository not created. Call create_repository() first.")
        assert self.repo_path is not None

        subprocess.run(["git", "checkout", "-b", branch_name], cwd=self.repo_path, check=True, capture_output=True)
        return self

    def checkout_branch(self, branch_name: str) -> "GitRepositoryBuilder":
        """
        Checkout an existing branch.

        Args:
            branch_name: Name of the branch to checkout

        Returns:
            Self for method chaining
        """
        if not self.repo_path:
            raise ValueError("Repository not created. Call create_repository() first.")
        assert self.repo_path is not None

        subprocess.run(["git", "checkout", branch_name], cwd=self.repo_path, check=True, capture_output=True)
        return self

    def create_tag(self, tag_name: str, message: Optional[str] = None) -> "GitRepositoryBuilder":
        """
        Create a Git tag.

        Args:
            tag_name: Name of the tag
            message: Optional tag message

        Returns:
            Self for method chaining
        """
        if not self.repo_path:
            raise ValueError("Repository not created. Call create_repository() first.")
        assert self.repo_path is not None

        tag_args = ["git", "tag"]
        if message:
            tag_args.extend(["-a", tag_name, "-m", message])
        else:
            tag_args.append(tag_name)

        subprocess.run(tag_args, cwd=self.repo_path, check=True, capture_output=True)
        return self

    def get_path(self) -> Path:
        """
        Get the path to the created repository.

        Returns:
            Path to the repository
        """
        if not self.repo_path:
            raise ValueError("Repository not created. Call create_repository() first.")

        return self.repo_path


def create_sample_repository() -> Path:
    """
    Create a sample Git repository for testing.

    Returns:
        Path to the created repository
    """
    builder = GitRepositoryBuilder()

    repo_path = (builder
                 .create_repository("sample-repo")
                 .add_file("README.md", "# Sample Repository\n\nThis is a sample repository for testing.")
                 .add_file("src/main.py", "#!/usr/bin/env python3\nprint('Hello, World!')\n")
                 .commit("Initial commit")
                 .add_file("src/utils.py", "def helper_function() -> None:\n    return 'helper'\n")
                 .commit("Add utility functions")
                 .add_file("tests/test_main.py", "import unittest\n\nclass TestMain(unittest.TestCase):\n    pass\n")
                 .commit("Add tests")
                 .create_branch("feature/new-feature")
                 .add_file("src/feature.py", "def new_feature() -> None:\n    return 'new feature'\n")
                 .commit("Implement new feature")
                 .checkout_branch("main")
                 .create_tag("v1.0.0", "Version 1.0.0 release")
                 .get_path())

    return repo_path
