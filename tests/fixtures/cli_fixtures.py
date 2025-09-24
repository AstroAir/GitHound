"""Test fixtures specifically for CLI testing."""

import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import Mock, patch

import pytest
from git import Repo
from typer.testing import CliRunner

from githound.cli import app
from githound.models import OutputFormat, SearchQuery


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def temp_git_repo() -> Generator[Path, None, None]:
    """Create a temporary Git repository with sample content for CLI testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = Path(temp_dir)
        repo = Repo.init(repo_path)

        # Configure user for commits
        with repo.config_writer() as config:
            config.set_value("user", "name", "Test User")
            config.set_value("user", "email", "test@example.com")

        # Create sample files and commits
        # Initial commit
        readme_file = repo_path / "README.md"
        readme_file.write_text(
            "# Test Repository\n\nThis is a test repository for GitHound CLI testing."
        )
        repo.index.add([str(readme_file)])
        repo.index.commit("Initial commit")

        # Add Python file
        src_dir = repo_path / "src"
        src_dir.mkdir()
        main_file = src_dir / "main.py"
        main_file.write_text(
            """#!/usr/bin/env python3
\"\"\"Main module for the test application.\"\"\"

def main() -> None:
    \"\"\"Main function.\"\"\"
    print("Hello, World!")
    return None

def helper_function(x: int, y: int) -> int:
    \"\"\"Helper function for testing.\"\"\"
    return x + y

if __name__ == "__main__":
    main()
"""
        )
        repo.index.add([str(main_file)])
        repo.index.commit("Add main.py with functions")

        # Add configuration file
        config_file = repo_path / "config.json"
        config_file.write_text('{"name": "test-app", "version": "1.0.0"}')
        repo.index.add([str(config_file)])
        repo.index.commit("Add configuration file")

        # Add test file
        test_dir = repo_path / "tests"
        test_dir.mkdir()
        test_file = test_dir / "test_main.py"
        test_file.write_text(
            """import unittest
from src.main import helper_function

class TestMain(unittest.TestCase):
    def test_helper_function(self):
        self.assertEqual(helper_function(2, 3), 5)

if __name__ == "__main__":
    unittest.main()
"""
        )
        repo.index.add([str(test_file)])
        repo.index.commit("Add test file")

        # Create a branch and add more content
        feature_branch = repo.create_head("feature/new-feature")
        feature_branch.checkout()

        feature_file = src_dir / "feature.py"
        feature_file.write_text(
            """\"\"\"New feature module.\"\"\"

class FeatureClass:
    def __init__(self, name: str) -> None:
        self.name = name
    
    def process(self) -> str:
        return f"Processing {self.name}"
"""
        )
        repo.index.add([str(feature_file)])
        repo.index.commit("Add new feature")

        # Switch back to main
        repo.heads.master.checkout()

        # Create a tag
        repo.create_tag("v1.0.0", message="Version 1.0.0")

        yield repo_path


@pytest.fixture
def sample_search_queries() -> dict:
    """Provide sample search queries for testing."""
    return {
        "content_search": SearchQuery(
            content_pattern="function", case_sensitive=False, fuzzy_search=False
        ),
        "author_search": SearchQuery(author_pattern="Test User", fuzzy_search=False),
        "message_search": SearchQuery(message_pattern="Add.*file", fuzzy_search=False),
        "fuzzy_search": SearchQuery(
            content_pattern="functon", fuzzy_search=True, fuzzy_threshold=0.8  # Typo intentional
        ),
        "complex_search": SearchQuery(
            content_pattern="class.*:",
            author_pattern="Test User",
            file_extensions=["py"],
            fuzzy_search=False,
        ),
    }


@pytest.fixture
def mock_githound_instance():
    """Create a mock GitHound instance for testing."""
    mock_gh = Mock()

    # Mock repository info
    mock_gh.analyze_repository.return_value = Mock(
        path="/test/repo",
        name="test-repo",
        total_commits=4,
        contributors=["Test User"],
        branches=["master", "feature/new-feature"],
        tags=["v1.0.0"],
    )

    # Mock search results
    mock_gh.search_advanced.return_value = [
        Mock(
            commit_hash="abc123",
            file_path="src/main.py",
            line_number=5,
            content="def main() -> None:",
            author="Test User",
            message="Add main.py with functions",
        )
    ]

    # Mock blame results
    mock_gh.analyze_blame.return_value = Mock(
        file_path="src/main.py",
        lines=[
            Mock(line_number=1, content="#!/usr/bin/env python3", author="Test User"),
            Mock(
                line_number=2,
                content='"""Main module for the test application."""',
                author="Test User",
            ),
        ],
    )

    # Mock diff results
    mock_gh.compare_commits.return_value = Mock(
        from_commit="abc123", to_commit="def456", files_changed=1, insertions=10, deletions=2
    )

    return mock_gh


@pytest.fixture
def cli_output_formats():
    """Provide output format options for testing."""
    return {"text": OutputFormat.TEXT, "json": OutputFormat.JSON, "csv": OutputFormat.CSV}


@pytest.fixture
def mock_file_operations():
    """Mock file operations for testing output functionality."""
    with (
        patch("builtins.open", create=True) as mock_open,
        patch("pathlib.Path.write_text") as mock_write_text,
        patch("pathlib.Path.exists") as mock_exists,
    ):

        mock_exists.return_value = True
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file

        yield {
            "open": mock_open,
            "write_text": mock_write_text,
            "exists": mock_exists,
            "file": mock_file,
        }


@pytest.fixture
def cli_error_scenarios():
    """Provide error scenarios for CLI testing."""
    return {
        "invalid_repo": {"path": "/nonexistent/repo", "error": "Not a Git repository"},
        "permission_denied": {"path": "/root/restricted", "error": "Permission denied"},
        "invalid_commit": {"commit": "invalid_hash_123", "error": "Invalid commit hash"},
        "missing_file": {"file": "nonexistent.py", "error": "File not found"},
    }


@pytest.fixture
def mock_external_services():
    """Mock external services for CLI testing."""
    with (
        patch("uvicorn.run") as mock_uvicorn,
        patch("webbrowser.open") as mock_browser,
        patch("githound.mcp_server.run_mcp_server") as mock_mcp,
    ):

        yield {"uvicorn": mock_uvicorn, "browser": mock_browser, "mcp_server": mock_mcp}


@pytest.fixture
def cli_command_examples():
    """Provide example CLI commands for testing."""
    return {
        "search": [
            ["search", "--repo-path", ".", "--content", "function"],
            ["search", "--repo-path", ".", "--author", "Test User"],
            ["search", "--repo-path", ".", "--message", "Add.*file"],
            ["search", "--repo-path", ".", "--content", "class", "--format", "json"],
        ],
        "analyze": [
            ["analyze", "."],
            ["analyze", ".", "--format", "json"],
            ["analyze", ".", "--output", "analysis.json"],
        ],
        "blame": [
            ["blame", ".", "src/main.py"],
            ["blame", ".", "src/main.py", "--format", "json"],
            ["blame", ".", "src/main.py", "--commit", "HEAD~1"],
        ],
        "diff": [
            ["diff", ".", "HEAD~1", "HEAD"],
            ["diff", ".", "master", "feature/new-feature"],
            ["diff", ".", "abc123", "def456", "--format", "json"],
        ],
        "web": [
            ["web", "."],
            ["web", ".", "--port", "8080"],
            ["web", ".", "--host", "0.0.0.0", "--port", "8000"],
        ],
        "mcp-server": [
            ["mcp-server", "."],
            ["mcp-server", ".", "--port", "3001"],
            ["mcp-server", ".", "--host", "localhost", "--log-level", "DEBUG"],
        ],
    }
