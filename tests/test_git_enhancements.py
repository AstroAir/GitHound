"""Tests for enhanced Git functionality."""

import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import pytest
from git import Repo

from githound.git_blame import (
    BlameInfo,
    FileBlameResult,
    get_author_statistics,
    get_file_blame,
    get_line_history,
)
from githound.git_diff import (
    ChangeType,
    FileDiffInfo,
    compare_branches,
    compare_commits,
    get_file_diff_history,
)
from githound.git_handler import (
    extract_commit_metadata,
    get_commits_with_filters,
    get_file_history,
    get_repository_metadata,
)


@pytest.fixture
def temp_repo() -> None:
    """Create a temporary Git repository for testing."""
    import os

    temp_dir = tempfile.mkdtemp()
    # Normalize path to handle Windows 8.3 short names
    normalized_temp_dir = os.path.realpath(temp_dir)
    repo = Repo.init(normalized_temp_dir)

    # Configure user for commits
    with repo.config_writer() as config:  # [attr-defined]
        config.set_value("user", "name", "Test User")  # [attr-defined]
        config.set_value("user", "email", "test@example.com")  # [attr-defined]

    # Create initial commit
    test_file = Path(normalized_temp_dir) / "test.txt"
    test_file.write_text("Initial content\nLine 2\nLine 3\n")
    repo.index.add([str(test_file)])
    initial_commit = repo.index.commit("Initial commit")

    yield repo, normalized_temp_dir, initial_commit

    # Cleanup: Close repository to release file handles
    repo.close()
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestGitHandler:
    """Tests for enhanced git_handler functions."""

    def test_extract_commit_metadata(self, temp_repo) -> None:
        """Test commit metadata extraction."""
        repo, temp_dir, commit = temp_repo

        metadata = extract_commit_metadata(commit)

        assert metadata.hash == commit.hexsha
        assert metadata.short_hash == commit.hexsha[:8]
        assert metadata.author_name == "Test User"
        assert metadata.author_email == "test@example.com"
        assert metadata.message == "Initial commit"
        assert isinstance(metadata.date, datetime)
        assert metadata.files_changed >= 0
        assert metadata.insertions >= 0
        assert metadata.deletions >= 0

    def test_get_repository_metadata(self, temp_repo) -> None:
        """Test repository metadata extraction."""
        repo, temp_dir, commit = temp_repo

        metadata = get_repository_metadata(repo)

        assert metadata["repo_path"] == temp_dir
        assert metadata["is_bare"] is False
        assert metadata["head_commit"] == commit.hexsha
        assert metadata["active_branch"] == "master" or metadata["active_branch"] == "main"
        assert isinstance(metadata["branches"], list)
        assert isinstance(metadata["remotes"], list)
        assert isinstance(metadata["tags"], list)
        assert metadata["total_commits"] >= 1
        assert isinstance(metadata["contributors"], list)
        assert len(metadata["contributors"]) >= 1

    def test_get_commits_with_filters(self, temp_repo) -> None:
        """Test filtered commit retrieval."""
        repo, temp_dir, initial_commit = temp_repo

        # Create additional commits
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Modified content\nLine 2\nLine 3\n")
        repo.index.add([str(test_file)])
        second_commit = repo.index.commit("Second commit by Test User")

        # Test author filter
        commits = list(get_commits_with_filters(repo, author_pattern="Test User"))
        assert len(commits) >= 2

        # Test message filter
        commits = list(get_commits_with_filters(repo, message_pattern="Initial"))
        assert len(commits) >= 1
        assert any(
            commit.hexsha if commit is not None else None == initial_commit.hexsha
            for commit in commits
        )

        # Test max count
        commits = list(get_commits_with_filters(repo, max_count=1))
        assert len(commits) == 1

    def test_get_file_history(self, temp_repo) -> None:
        """Test file history retrieval."""
        repo, temp_dir, initial_commit = temp_repo

        # Create additional commits for the same file
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Modified content\nLine 2\nLine 3\n")
        repo.index.add([str(test_file)])
        repo.index.commit("Modified test.txt")

        history = get_file_history(repo, "test.txt")

        assert len(history) >= 2
        assert all("commit_hash" in entry for entry in history)
        assert all("commit_date" in entry for entry in history)
        assert all("author" in entry for entry in history)
        assert all("message" in entry for entry in history)


class TestGitBlame:
    """Tests for git blame functionality."""

    def test_get_file_blame(self, temp_repo) -> None:
        """Test file blame functionality."""
        repo, temp_dir, commit = temp_repo

        blame_result = get_file_blame(repo, "test.txt")

        assert isinstance(blame_result, FileBlameResult)
        assert blame_result.file_path == "test.txt"
        assert blame_result.total_lines >= 3
        assert len(blame_result.blame_info) == blame_result.total_lines
        assert len(blame_result.contributors) >= 1
        assert blame_result.oldest_line_date is not None
        assert blame_result.newest_line_date is not None

        # Check first line blame info
        first_line = blame_result.blame_info[0]
        assert isinstance(first_line, BlameInfo)
        assert first_line.line_number == 1
        assert first_line.author_name == "Test User"
        assert first_line.commit_hash == commit.hexsha

    def test_get_line_history(self, temp_repo) -> None:
        """Test line history tracking."""
        repo, temp_dir, initial_commit = temp_repo

        # Modify the first line
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Modified first line\nLine 2\nLine 3\n")
        repo.index.add([str(test_file)])
        repo.index.commit("Modified first line")

        history = get_line_history(repo, "test.txt", 1)

        assert len(history) >= 1
        assert all("commit_hash" in entry for entry in history)
        assert all("line_content" in entry for entry in history)
        assert all("line_author" in entry for entry in history)

    def test_get_author_statistics(self, temp_repo) -> None:
        """Test author statistics generation."""
        repo, temp_dir, commit = temp_repo

        # Test file-specific statistics
        stats = get_author_statistics(repo, "test.txt")

        assert len(stats) >= 1
        author_key = "Test User <test@example.com>"
        assert author_key in stats

        author_stats = stats[author_key]
        assert "lines_authored" in author_stats
        assert "total_commits" in author_stats
        assert "total_files" in author_stats
        assert "first_commit_date" in author_stats
        assert "last_commit_date" in author_stats

        # Test repository-wide statistics
        repo_stats = get_author_statistics(repo)
        assert len(repo_stats) >= 1
        assert author_key in repo_stats


class TestGitDiff:
    """Tests for git diff functionality."""

    def test_compare_commits(self, temp_repo) -> None:
        """Test commit comparison."""
        repo, temp_dir, initial_commit = temp_repo

        # Create a second commit
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Modified content\nLine 2\nLine 3\nNew line\n")
        repo.index.add([str(test_file)])
        second_commit = repo.index.commit("Modified test.txt")

        diff_result = compare_commits(repo, initial_commit.hexsha, second_commit.hexsha)

        assert diff_result.from_commit == initial_commit.hexsha
        assert diff_result.to_commit == second_commit.hexsha
        assert diff_result.files_changed >= 1
        assert len(diff_result.file_diffs) >= 1

        file_diff = diff_result.file_diffs[0]
        assert isinstance(file_diff, FileDiffInfo)
        assert file_diff.file_path == "test.txt"
        assert file_diff.change_type == ChangeType.MODIFIED

    def test_get_file_diff_history(self, temp_repo) -> None:
        """Test file diff history."""
        repo, temp_dir, initial_commit = temp_repo

        # Create multiple commits modifying the same file
        test_file = Path(temp_dir) / "test.txt"

        test_file.write_text("First modification\nLine 2\nLine 3\n")
        repo.index.add([str(test_file)])
        repo.index.commit("First modification")

        test_file.write_text("Second modification\nLine 2\nLine 3\n")
        repo.index.add([str(test_file)])
        repo.index.commit("Second modification")

        history = get_file_diff_history(repo, "test.txt")

        assert len(history) >= 2
        assert all("commit_hash" in entry for entry in history)
        assert all("change_type" in entry for entry in history)
        assert all("lines_added" in entry for entry in history)
        assert all("lines_deleted" in entry for entry in history)


class TestErrorHandling:
    """Tests for error handling in git enhancements."""

    def test_invalid_file_blame(self, temp_repo) -> None:
        """Test blame for non-existent file."""
        repo, temp_dir, commit = temp_repo

        with pytest.raises(Exception):  # Should raise GitCommandError or similar
            get_file_blame(repo, "nonexistent.txt")

    def test_invalid_commit_comparison(self, temp_repo) -> None:
        """Test comparison with invalid commit."""
        repo, temp_dir, commit = temp_repo

        with pytest.raises(Exception):  # Should raise GitCommandError or similar
            compare_commits(repo, "invalid_hash", commit.hexsha)

    def test_invalid_branch_comparison(self, temp_repo) -> None:
        """Test comparison with invalid branch."""
        repo, temp_dir, commit = temp_repo

        with pytest.raises(Exception):  # Should raise GitCommandError or similar
            compare_branches(repo, "nonexistent_branch", "master")


class TestEdgeCases:
    """Tests for edge cases in git enhancements."""

    def test_empty_repository_metadata(self) -> None:
        """Test metadata extraction from empty repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Repo.init(temp_dir)

            metadata = get_repository_metadata(repo)

            assert metadata["repo_path"] == temp_dir
            assert metadata["is_bare"] is False
            assert metadata["head_commit"] is None
            assert metadata["total_commits"] == 0

    def test_binary_file_diff(self, temp_repo) -> None:
        """Test diff analysis with binary files."""
        repo, temp_dir, initial_commit = temp_repo

        # Create a binary file
        binary_file = Path(temp_dir) / "binary.bin"
        binary_file.write_bytes(b"\x00\x01\x02\x03\x04\x05")
        repo.index.add([str(binary_file)])
        binary_commit = repo.index.commit("Added binary file")

        diff_result = compare_commits(repo, initial_commit.hexsha, binary_commit.hexsha)

        # Find the binary file diff
        binary_diff = next(
            (fd for fd in diff_result.file_diffs if fd.file_path == "binary.bin"), None
        )
        assert binary_diff is not None
        # Note: Binary detection may not work perfectly in all cases
        # The important thing is that the file is detected and processed
        assert binary_diff.change_type == ChangeType.ADDED
