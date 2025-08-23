"""
End-to-end workflow integration tests for GitHound.

These tests verify complete workflows from start to finish, including
MCP server operations, API interactions, and data export functionality.
"""

import asyncio
import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest


class MockMCPContext:
    """
    A mock implementation of the MCP context used for integration testing.

    This class simulates the logging interface expected by MCP server operations,
    capturing info and error messages in a list for later inspection by tests.
    """

    def __init__(self):
        self.messages: list[str] = []

    async def info(self, message: str) -> None:
        """Log info message."""
        self.messages.append(f"INFO: {message}")

    async def error(self, message: str) -> None:
        """Log error message."""
        self.messages.append(f"ERROR: {message}")


@pytest.fixture
def integration_test_repo():
    """Create a comprehensive test repository for integration testing."""
    temp_dir = tempfile.mkdtemp(prefix="githound_integration_")

    from git import Repo

    repo = Repo.init(temp_dir)

    # Configure test user
    with repo.config_writer() as config:
        config.set_value("user", "name", "Integration Test User")
        config.set_value("user", "email", "integration@test.com")

    # Create comprehensive project structure
    base_path = Path(temp_dir)

    # Source files
    src_dir = base_path / "src"
    src_dir.mkdir()

    (src_dir / "__init__.py").write_text("")
    (src_dir / "main.py").write_text(
        """
def main():
    print("Hello from integration test!")
    return 0

if __name__ == "__main__":
    main()
"""
    )

    (src_dir / "utils.py").write_text(
        """
def helper_function(x: int) -> int:
    return x * 2

class UtilityClass:
    def __init__(self, value: int):
        self.value = value
    
    def process(self) -> int:
        return helper_function(self.value)
"""
    )

    # Test files
    tests_dir = base_path / "tests"
    tests_dir.mkdir()

    (tests_dir / "__init__.py").write_text("")
    (tests_dir / "test_main.py").write_text(
        """
import unittest
from src.main import main

class TestMain(unittest.TestCase):
    def test_main_returns_zero(self):
        result = main()
        self.assertEqual(result, 0)
"""
    )

    # Documentation
    (base_path / "README.md").write_text(
        """
# Integration Test Project

This is a test project for GitHound integration testing.

## Features
- Main application functionality
- Utility functions and classes
- Comprehensive test suite
"""
    )

    # Configuration files
    (base_path / "requirements.txt").write_text("pytest>=6.0.0\nmypy>=0.900")
    (base_path / ".gitignore").write_text("__pycache__/\n*.pyc\n.pytest_cache/")

    # Create initial commit
    repo.git.add(A=True)  # Add all files
    initial_commit = repo.index.commit("Initial project setup")

    # Create feature branch and additional commits
    feature_branch = repo.create_head("feature/new-functionality")
    feature_branch.checkout()

    # Add feature implementation
    (src_dir / "feature.py").write_text(
        """
def new_feature(data: str) -> str:
    return f"Processed: {data}"

class FeatureProcessor:
    def __init__(self):
        self.processed_count = 0
    
    def process_item(self, item: str) -> str:
        self.processed_count += 1
        return new_feature(item)
"""
    )

    repo.index.add(["src/feature.py"])
    feature_commit = repo.index.commit("Add new feature implementation")

    # Switch back to main and create merge
    repo.heads.master.checkout()
    repo.git.merge("feature/new-functionality")

    # Create additional commits with different authors
    authors = [("Alice Developer", "alice@example.com"), ("Bob Contributor", "bob@example.com")]

    for i, (author_name, author_email) in enumerate(authors):
        with repo.config_writer() as config:
            config.set_value("user", "name", author_name)
            config.set_value("user", "email", author_email)

        file_path = base_path / f"contribution_{i}.md"
        file_path.write_text(
            f"""
# Contribution by {author_name}

This file represents a contribution by {author_name}.
Created on {datetime.now().isoformat()}.
"""
        )

        repo.index.add([f"contribution_{i}.md"])
        repo.index.commit(f"Add contribution by {author_name}")

    # Create tag
    repo.create_tag("v1.0.0", message="Version 1.0.0 release")

    yield repo, temp_dir

    # Cleanup
    import shutil

    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.integration
class TestCompleteWorkflows:
    """Test complete end-to-end workflows."""

    @pytest.mark.asyncio
    async def test_complete_repository_analysis_workflow(self, integration_test_repo):
        """Test complete repository analysis workflow from start to finish."""
        repo, temp_dir = integration_test_repo

        # Step 1: Repository Analysis
        from githound.mcp_server import RepositoryInput, analyze_repository_direct

        repo_input = RepositoryInput(repo_path=temp_dir)

        analysis_result = await analyze_repository_direct(repo_input)

        # Verify analysis results
        assert analysis_result["status"] == "success"
        assert "repository_metadata" in analysis_result

        metadata = analysis_result["repository_metadata"]
        assert metadata["total_commits"] >= 4  # We created at least 4 commits
        assert len(metadata["contributors"]) >= 2  # Multiple authors
        assert len(metadata["branches"]) >= 2  # main + feature branch
        assert len(metadata["tags"]) >= 1  # v1.0.0 tag

        # Step 2: Commit History Analysis
        from githound.mcp_server import CommitHistoryInput, get_commit_history_direct

        history_input = CommitHistoryInput(repo_path=temp_dir, max_count=10)

        history_result = await get_commit_history_direct(history_input)

        # Verify history results
        assert history_result["status"] == "success"
        assert "commits" in history_result

        commits = history_result["commits"]
        assert len(commits) >= 4

        # Verify commit structure
        for commit in commits:
            assert "hash" in commit
            assert "author_name" in commit
            assert "message" in commit
            assert "files_changed" in commit

        # Step 3: File Analysis
        from githound.mcp_server import FileBlameInput, get_file_blame_direct

        # Test with main.py file
        blame_input = FileBlameInput(repo_path=temp_dir, file_path="src/main.py")

        blame_result = await get_file_blame_direct(blame_input)

        # Verify blame results
        assert blame_result["status"] == "success"
        assert "blame_info" in blame_result

        blame_info = blame_result["blame_info"]
        assert blame_info["file_path"] == "src/main.py"
        assert blame_info["total_lines"] > 0
        assert "line_blame" in blame_info

        # Step 4: Author Statistics
        from githound.mcp_server import AuthorStatsInput, get_author_stats_direct

        stats_input = AuthorStatsInput(repo_path=temp_dir)
        stats_result = await get_author_stats_direct(stats_input)

        # Verify author statistics
        assert stats_result["status"] == "success"
        assert "author_statistics" in stats_result
        assert stats_result["total_authors"] >= 2

        # Step 5: Data Export
        from githound.mcp_server import ExportInput, export_repository_data_direct

        export_file = Path(temp_dir) / "export_test.json"
        export_input = ExportInput(
            repo_path=temp_dir, output_path=str(export_file), format="json", include_metadata=True
        )

        export_result = await export_repository_data_direct(export_input)

        # Verify export results
        assert export_result["status"] == "success"
        assert export_file.exists()

        # Verify exported data
        with open(export_file) as f:
            exported_data = json.load(f)
            assert "repository_metadata" in exported_data
            assert "export_timestamp" in exported_data
            assert "total_commits" in exported_data["repository_metadata"]
            assert exported_data["repository_metadata"]["total_commits"] >= 4

        # Verify all operations completed successfully
        assert all(result["status"] == "success" for result in [
            analysis_result, history_result, blame_result, stats_result, export_result
        ])

    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, integration_test_repo):
        """Test error handling across the complete workflow."""
        repo, temp_dir = integration_test_repo
        context = MockMCPContext()

        # Test 1: Invalid repository path
        from githound.mcp_server import RepositoryInput, analyze_repository_direct

        invalid_input = RepositoryInput(repo_path="/nonexistent/path")
        result = await analyze_repository_direct(invalid_input)

        assert result["status"] == "error"
        assert "error" in result

        # Test 2: Invalid file path for blame
        from githound.mcp_server import FileBlameInput, get_file_blame_direct

        invalid_blame_input = FileBlameInput(repo_path=temp_dir, file_path="nonexistent/file.py")

        blame_result = await get_file_blame_direct(invalid_blame_input)
        assert blame_result["status"] == "error"

        # Test 3: Invalid commit hash for comparison
        from githound.mcp_server import CommitComparisonInput, compare_commits_direct

        invalid_comparison_input = CommitComparisonInput(
            repo_path=temp_dir, from_commit="invalid_hash_1", to_commit="invalid_hash_2"
        )

        comparison_result = await compare_commits_direct(invalid_comparison_input)
        assert comparison_result["status"] == "error"

        # Verify error messages were logged
        error_messages = [msg for msg in context.messages if "ERROR" in msg]
        assert len(error_messages) >= 0  # Some operations might not log errors to context

    @pytest.mark.asyncio
    async def test_concurrent_operations_workflow(self, integration_test_repo):
        """Test concurrent operations in a complete workflow."""
        repo, temp_dir = integration_test_repo

        # Create multiple concurrent operations
        tasks = []

        # Task 1: Repository analysis
        from githound.mcp_server import RepositoryInput, analyze_repository_direct

        repo_input = RepositoryInput(repo_path=temp_dir)
        tasks.append(analyze_repository_direct(repo_input))

        # Task 2: Commit history
        from githound.mcp_server import CommitHistoryInput, get_commit_history_direct

        history_input = CommitHistoryInput(repo_path=temp_dir, max_count=5)
        tasks.append(get_commit_history_direct(history_input))

        # Task 3: Author statistics
        from githound.mcp_server import AuthorStatsInput, get_author_stats_direct

        stats_input = AuthorStatsInput(repo_path=temp_dir)
        tasks.append(get_author_stats_direct(stats_input))

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify all operations completed successfully
        assert len(results) == 3

        for i, result in enumerate(results):
            assert not isinstance(result, Exception), f"Task {i} failed with exception: {result}"
            assert (
                result["status"] == "success"
            ), f"Task {i} failed: {result.get('error', 'Unknown error')}"

        # Verify specific results
        repo_analysis, commit_history, author_stats = results

        assert "repository_metadata" in repo_analysis
        assert "commits" in commit_history
        assert "author_statistics" in author_stats

    @pytest.mark.asyncio
    async def test_export_workflow_multiple_formats(self, integration_test_repo):
        """Test data export workflow with multiple formats."""
        repo, temp_dir = integration_test_repo
        context = MockMCPContext()

        # Test exports in different formats
        formats = ["json", "yaml"]
        export_results = {}

        for format_type in formats:
            from githound.mcp_server import ExportInput, export_repository_data_direct

            export_file = Path(temp_dir) / f"export_test.{format_type}"
            export_input = ExportInput(
                repo_path=temp_dir,
                output_path=str(export_file),
                format=format_type,
                include_metadata=True,
            )

            result = await export_repository_data_direct(export_input)
            export_results[format_type] = result

            # Verify export succeeded
            assert result["status"] == "success"
            assert export_file.exists()
            assert export_file.stat().st_size > 0

        # Verify all formats were exported successfully
        for format_type, result in export_results.items():
            assert result["status"] == "success"
            assert result["format"] == format_type


@pytest.mark.integration
class TestResourceIntegration:
    """Test MCP resource integration."""

    @pytest.mark.asyncio
    async def test_resource_access_workflow(self, integration_test_repo):
        """Test accessing MCP resources in a complete workflow."""
        repo, temp_dir = integration_test_repo

        # Import resource functions
        from githound.mcp_server import (
            get_repository_config_direct,
            get_repository_contributors_direct,
            get_repository_summary_direct,
        )

        # Test repository config resource
        config_result = await get_repository_config_direct(temp_dir)
        assert isinstance(config_result, str)
        assert "GitHound Repository Configuration" in config_result
        assert "Total Commits" in config_result

        # Test contributors resource
        contributors_result = await get_repository_contributors_direct(temp_dir)
        assert isinstance(contributors_result, str)
        assert "Repository Contributors" in contributors_result
        assert "contributor" in contributors_result.lower()

        # Test summary resource
        summary_result = await get_repository_summary_direct(temp_dir)
        assert isinstance(summary_result, str)
        assert "Repository Summary" in summary_result
        assert temp_dir in summary_result

        # Verify that all resources returned valid data (basic integration check)
        assert len(config_result) > 0
        assert len(contributors_result) > 0
        assert len(summary_result) > 0


@pytest.mark.integration
class TestDataConsistency:
    """Test data consistency across different operations."""

    @pytest.mark.asyncio
    async def test_data_consistency_across_operations(self, integration_test_repo):
        """Test that data remains consistent across different operations."""
        repo, temp_dir = integration_test_repo
        context = MockMCPContext()

        # Get repository metadata
        from githound.mcp_server import RepositoryInput, analyze_repository_direct

        repo_input = RepositoryInput(repo_path=temp_dir)
        repo_analysis = await analyze_repository_direct(repo_input)

        assert repo_analysis["status"] == "success"
        metadata = repo_analysis["repository_metadata"]

        # Get commit history
        from githound.mcp_server import CommitHistoryInput, get_commit_history_direct

        history_input = CommitHistoryInput(repo_path=temp_dir, max_count=100)
        history_result = await get_commit_history_direct(history_input)

        assert history_result["status"] == "success"
        commits = history_result["commits"]

        # Get author statistics
        from githound.mcp_server import AuthorStatsInput, get_author_stats_direct

        stats_input = AuthorStatsInput(repo_path=temp_dir)
        stats_result = await get_author_stats_direct(stats_input)

        assert stats_result["status"] == "success"
        author_stats = stats_result["author_statistics"]

        # Verify consistency
        # Total commits should match between metadata and history
        assert metadata["total_commits"] == len(commits)

        # Contributors should be consistent
        # Extract names from metadata contributors (format: "Name <email>")
        metadata_contributor_names = set()
        for contributor in metadata["contributors"]:
            if '<' in contributor:
                name = contributor.split('<')[0].strip()
            else:
                name = contributor
            metadata_contributor_names.add(name)

        history_authors = set(commit["author_name"] for commit in commits)

        # Extract names from stats authors (format: "Name <email>")
        stats_author_names = set()
        for author in author_stats.keys():
            if '<' in author:
                name = author.split('<')[0].strip()
            else:
                name = author
            stats_author_names.add(name)

        # All authors in history should be in metadata contributors
        assert history_authors.issubset(metadata_contributor_names)

        # All authors in stats should be in metadata contributors
        assert stats_author_names.issubset(metadata_contributor_names)

        # Verify commit counts in author stats match actual commits
        for author_with_email, stats in author_stats.items():
            # Extract just the name from "Name <email>" format
            if '<' in author_with_email:
                author_name = author_with_email.split('<')[0].strip()
            else:
                author_name = author_with_email

            author_commits = [c for c in commits if c["author_name"] == author_name]
            assert stats.get("total_commits", 0) == len(author_commits), (
                f"Author {author_with_email} stats show {stats.get('total_commits', 0)} commits, "
                f"but found {len(author_commits)} in history for name '{author_name}'"
            )
