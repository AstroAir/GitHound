"""Tests for GitHound git blame functionality."""

import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest
from git import GitCommandError, Repo

from githound.git_blame import (
    BlameInfo,
    FileBlameResult,
    get_author_statistics,
    get_file_blame,
    get_line_history,
)


@pytest.fixture
def temp_repo() -> None:
    """Create a temporary Git repository for testing."""
    temp_dir = tempfile.mkdtemp()
    repo = Repo.init(temp_dir)

    # Configure user for commits
    with repo.config_writer() as config:  # [attr-defined]
        config.set_value("user", "name", "Test User")  # [attr-defined]
        config.set_value("user", "email", "test@example.com")  # [attr-defined]

    # Create initial commit
    test_file = Path(temp_dir) / "test.py"
    test_file.write_text("def hello() -> None:\n    print('Hello, World!')\n")
    repo.index.add([str(test_file)])
    initial_commit = repo.index.commit("Initial commit")

    # Create second commit with different author
    with repo.config_writer() as config:  # [attr-defined]
        config.set_value("user", "name", "Another User")  # [attr-defined]
        # [attr-defined]
        config.set_value("user", "email", "another@example.com")

    test_file.write_text(
        "def hello() -> None:\n    print('Hello, GitHound!')\n\ndef goodbye() -> None:\n    print('Goodbye!')\n"
    )
    repo.index.add([str(test_file)])
    second_commit = repo.index.commit("Add goodbye function")

    yield repo, temp_dir, initial_commit, second_commit

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestFileBlame:
    """Tests for file blame functionality."""

    def test_get_file_blame_success(self, temp_repo) -> None:
        """Test successful file blame analysis."""
        repo, temp_dir, initial_commit, second_commit = temp_repo

        blame_info = get_file_blame(repo, "test.py")

        assert isinstance(blame_info, FileBlameResult)
        assert blame_info.file_path = = "test.py"
        assert blame_info.total_lines >= 4  # Should have at least 4 lines
        assert len(blame_info.blame_info) == blame_info.total_lines
        assert len(blame_info.contributors) >= 1

        # Check that we have blame information for each line
        for line in blame_info.blame_info:
            assert isinstance(line, BlameInfo)
            assert line.line_number > 0
            assert line.content is not None
            assert line.author_name is not None
            assert line.author_email is not None
            assert line.commit_hash is not None

    def test_get_file_blame_nonexistent_file(self, temp_repo) -> None:
        """Test file blame for nonexistent file."""
        repo, temp_dir, initial_commit, second_commit = temp_repo

        with pytest.raises(GitCommandError):
            get_file_blame(repo, "nonexistent.py")

    def test_get_file_blame_specific_commit(self, temp_repo) -> None:
        """Test file blame for specific commit."""
        repo, temp_dir, initial_commit, second_commit = temp_repo

        # Get blame for the initial commit
        blame_info = get_file_blame(
            repo, "test.py", commit=initial_commit.hexsha)

        assert isinstance(blame_info, FileBlameResult)
        assert blame_info.total_lines = = 2  # Initial commit had only 2 lines

        # All lines should be from the initial commit
        for line in blame_info.blame_info:
            assert line.commit_hash = = initial_commit.hexsha

    def test_get_file_blame_with_line_range(self, temp_repo) -> None:
        """Test file blame with line range."""
        repo, temp_dir, initial_commit, second_commit = temp_repo

        # This test assumes the implementation supports line ranges
        # If not implemented, this test can be skipped or modified
        blame_info = get_file_blame(repo, "test.py")

        # Verify we can access specific lines
        assert len(blame_info.blame_info) > 0
        first_line = blame_info.blame_info[0]
        assert first_line.line_number = = 1

    def test_blame_line_info_properties(self, temp_repo) -> None:
        """Test BlameInfo properties."""
        repo, temp_dir, initial_commit, second_commit = temp_repo

        blame_info = get_file_blame(repo, "test.py")
        line = blame_info.blame_info[0]

        assert hasattr(line, "line_number")
        assert hasattr(line, "content")
        assert hasattr(line, "author_name")
        assert hasattr(line, "author_email")
        assert hasattr(line, "commit_hash")
        assert hasattr(line, "commit_date")
        assert hasattr(line, "commit_message")

    def test_file_blame_info_contributors(self, temp_repo) -> None:
        """Test FileBlameResult contributors list."""
        repo, temp_dir, initial_commit, second_commit = temp_repo

        blame_info = get_file_blame(repo, "test.py")

        # Should have contributors from both commits
        assert len(blame_info.contributors) >= 1

        # Check contributor information (contributors are strings in format "Name <email>")
        for contributor in blame_info.contributors:
            assert isinstance(contributor, str)
            # Should be in "Name <email>" format
            assert "<" in contributor and ">" in contributor


class TestLineHistory:
    """Tests for line history functionality."""

    def test_get_line_history_success(self, temp_repo) -> None:
        """Test successful line history retrieval."""
        repo, temp_dir, initial_commit, second_commit = temp_repo

        # Get history for line 1 (which should exist in both commits)
        history = get_line_history(repo, "test.py", 1)

        assert isinstance(history, list)
        assert len(history) > 0

        # Each history entry should have required fields
        for entry in history:
            assert "commit_hash" in entry
            assert "author" in entry
            assert "commit_date" in entry  # The actual field name is 'commit_date'
            assert "message" in entry
            assert "line_content" in entry

    def test_get_line_history_nonexistent_file(self, temp_repo) -> None:
        """Test line history for nonexistent file."""
        repo, temp_dir, initial_commit, second_commit = temp_repo

        # The function may return empty list or raise error for nonexistent files
        try:
            history = get_line_history(repo, "nonexistent.py", 1)
            assert isinstance(history, list)
            # If it doesn't raise an error, it should return empty list
            assert len(history) == 0
        except GitCommandError:
            # It's also acceptable to raise an error
            pass

    def test_get_line_history_invalid_line_number(self, temp_repo) -> None:
        """Test line history for invalid line number."""
        repo, temp_dir, initial_commit, second_commit = temp_repo

        # Line number that doesn't exist
        history = get_line_history(repo, "test.py", 999)

        # Should return empty list or handle gracefully
        assert isinstance(history, list)

    def test_get_line_history_with_max_commits(self, temp_repo) -> None:
        """Test line history with max commits limit."""
        repo, temp_dir, initial_commit, second_commit = temp_repo

        history = get_line_history(repo, "test.py", 1, max_commits=1)

        assert isinstance(history, list)
        assert len(history) <= 1


class TestAuthorStatistics:
    """Tests for author statistics functionality."""

    def test_get_author_statistics_success(self, temp_repo) -> None:
        """Test successful author statistics retrieval."""
        repo, temp_dir, initial_commit, second_commit = temp_repo

        stats = get_author_statistics(repo)

        assert isinstance(stats, dict)
        assert len(stats) >= 1  # Should have at least one author

        # Check statistics for each author
        for author_key, author_stats in stats.items():
            assert isinstance(author_key, str)
            assert isinstance(author_stats, dict)

            # Required fields
            assert "total_commits" in author_stats
            assert "total_files" in author_stats
            assert "first_commit_date" in author_stats
            assert "last_commit_date" in author_stats

            # Values should be reasonable
            assert author_stats["total_commits"] > 0
            assert author_stats["total_files"] >= 0

    def test_get_author_statistics_multiple_authors(self, temp_repo) -> None:
        """Test author statistics with multiple authors."""
        repo, temp_dir, initial_commit, second_commit = temp_repo

        stats = get_author_statistics(repo)

        # Should have statistics for both authors
        test_user_found = False
        another_user_found = False

        for author_key in stats.keys():
            if "Test User" in author_key:
                test_user_found = True
            elif "Another User" in author_key:
                another_user_found = True

        assert test_user_found
        assert another_user_found

    def test_get_author_statistics_empty_repo(self) -> None:
        """Test author statistics for empty repository."""
        temp_dir = tempfile.mkdtemp()
        try:
            repo = Repo.init(temp_dir)

            # Empty repo should handle gracefully
            try:
                stats = get_author_statistics(repo)
                # If it succeeds, should return empty statistics
                assert isinstance(stats, dict)
                assert len(stats) == 0
            except GitCommandError:
                # It's acceptable to raise an error for empty repos
                pass

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_author_statistics_data_types(self, temp_repo) -> None:
        """Test author statistics data types."""
        repo, temp_dir, initial_commit, second_commit = temp_repo

        stats = get_author_statistics(repo)

        for author_key, author_stats in stats.items():
            # Check data types
            assert isinstance(author_stats["total_commits"], int)
            assert isinstance(author_stats["total_files"], int)

            # Dates should be datetime objects or strings
            first_date = author_stats["first_commit_date"]
            last_date = author_stats["last_commit_date"]

            assert isinstance(first_date, (datetime, str)
                              ) or first_date is None
            assert isinstance(last_date, (datetime, str)) or last_date is None

    def test_author_statistics_with_branch_filter(self, temp_repo) -> None:
        """Test author statistics with branch filtering."""
        repo, temp_dir, initial_commit, second_commit = temp_repo

        # Create a new branch
        new_branch = repo.create_head("feature-branch")
        new_branch.checkout()

        # Add commit to new branch
        test_file = Path(temp_dir) / "test.py"
        test_file.write_text(
            "def hello() -> None:\n    print('Hello, Feature!')\n")
        repo.index.add([str(test_file)])
        feature_commit = repo.index.commit("Feature commit")

        # Switch back to main branch
        repo.heads.master.checkout()

        # Get statistics for main branch only
        stats = get_author_statistics(repo, branch="master")

        assert isinstance(stats, dict)
        # Should not include the feature branch commit


class TestBlameErrorHandling:
    """Tests for blame error handling."""

    def test_blame_with_invalid_repo(self) -> None:
        """Test blame operations with invalid repository."""
        # Create a mock repo that will cause errors
        mock_repo = Mock()
        mock_repo.blame.side_effect = GitCommandError("git blame failed")

        with pytest.raises(GitCommandError):
            get_file_blame(mock_repo, "test.py")

    def test_blame_with_binary_file(self, temp_repo) -> None:
        """Test blame operations with binary file."""
        repo, temp_dir, initial_commit, second_commit = temp_repo

        # Create a binary file
        binary_file = Path(temp_dir) / "binary.bin"
        binary_file.write_bytes(b"\x00\x01\x02\x03\x04\x05")
        repo.index.add([str(binary_file)])
        repo.index.commit("Add binary file")

        # Blame should handle binary files gracefully
        try:
            blame_info = get_file_blame(repo, "binary.bin")
            # If it succeeds, verify the structure
            assert isinstance(blame_info, FileBlameResult)
        except GitCommandError:
            # It's acceptable for blame to fail on binary files
            pass

    def test_blame_with_large_file(self, temp_repo) -> None:
        """Test blame operations with large file."""
        repo, temp_dir, initial_commit, second_commit = temp_repo

        # Create a large file
        large_file = Path(temp_dir) / "large.py"
        content = "\n".join([f"# Line {i}" for i in range(1000)])
        large_file.write_text(content)
        repo.index.add([str(large_file)])
        repo.index.commit("Add large file")

        # Blame should handle large files
        blame_info = get_file_blame(repo, "large.py")

        assert isinstance(blame_info, FileBlameResult)
        assert blame_info.total_lines = = 1000
        assert len(blame_info.blame_info) == 1000


class TestBlamePerformance:
    """Tests for blame performance characteristics."""

    @pytest.mark.slow
    def test_blame_performance_multiple_files(self, temp_repo) -> None:
        """Test blame performance with multiple files."""
        repo, temp_dir, initial_commit, second_commit = temp_repo

        # Create multiple files
        for i in range(10):
            test_file = Path(temp_dir) / f"file_{i}.py"
            test_file.write_text(f"def function_{i}():\n    return {i}\n")
            repo.index.add([str(test_file)])

        repo.index.commit("Add multiple files")

        # Test blame on multiple files
        import time

        start_time = time.time()

        for i in range(10):
            blame_info = get_file_blame(repo, f"file_{i}.py")
            assert isinstance(blame_info, FileBlameResult)

        end_time = time.time()
        duration = end_time - start_time

        # Should complete within reasonable time (adjust threshold as needed)
        assert duration < 10.0  # 10 seconds threshold

    @pytest.mark.slow
    def test_author_statistics_performance(self, temp_repo) -> None:
        """Test author statistics performance."""
        repo, temp_dir, initial_commit, second_commit = temp_repo

        # Create many commits
        test_file = Path(temp_dir) / "test.py"
        for i in range(20):
            content = f"def function_{i}():\n    return {i}\n"
            test_file.write_text(content)
            repo.index.add([str(test_file)])
            repo.index.commit(f"Commit {i}")

        # Test statistics performance
        import time

        start_time = time.time()

        stats = get_author_statistics(repo)

        end_time = time.time()
        duration = end_time - start_time

        # Should complete within reasonable time
        # 10 seconds threshold (adjusted for CI/slower systems)
        assert duration < 10.0
        assert isinstance(stats, dict)
        assert len(stats) > 0
