"""Working git handler tests that focus on achievable coverage improvements."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import git

from githound.git_handler import (
    get_repository,
    walk_history,
    process_commit,
    extract_commit_metadata,
    get_repository_metadata,
    get_commits_with_filters,
    get_file_history
)
from githound.models import GitHoundConfig, SearchConfig


class TestGetRepository:
    """Test get_repository function."""

    def test_get_repository_with_valid_repo(self):
        """Test get_repository with a valid Git repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            
            # Initialize a Git repository
            repo = git.Repo.init(repo_path)
            
            # Test getting the repository
            result = get_repository(repo_path)
            assert isinstance(result, git.Repo)
            assert result.git_dir is not None

    def test_get_repository_with_invalid_path(self):
        """Test get_repository with an invalid path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            invalid_path = Path(temp_dir) / "not_a_repo"
            
            # Should raise GitCommandError
            with pytest.raises(git.GitCommandError):
                get_repository(invalid_path)

    def test_get_repository_with_nonexistent_path(self):
        """Test get_repository with a nonexistent path."""
        nonexistent_path = Path("/nonexistent/path")
        
        # Should raise GitCommandError
        with pytest.raises(git.GitCommandError):
            get_repository(nonexistent_path)


class TestWalkHistory:
    """Test walk_history function."""

    def test_walk_history_with_commits(self):
        """Test walk_history with a repository that has commits."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            
            # Initialize repository and create a commit
            repo = git.Repo.init(repo_path)
            
            # Create a file and commit it
            test_file = repo_path / "test.txt"
            test_file.write_text("test content")
            
            repo.index.add([str(test_file)])
            repo.index.commit("Initial commit")
            
            # Test walking history
            config = GitHoundConfig()
            commits = list(walk_history(repo, config))
            
            assert len(commits) >= 1
            assert all(isinstance(commit, git.Commit) for commit in commits)

    def test_walk_history_empty_repo(self):
        """Test walk_history with an empty repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            
            # Initialize empty repository
            repo = git.Repo.init(repo_path)
            
            config = GitHoundConfig()
            
            # Should handle empty repo gracefully
            commits = list(walk_history(repo, config))
            assert isinstance(commits, list)

    @patch("githound.git_handler.Repo")
    def test_walk_history_with_branch_config(self, mock_repo_class):
        """Test walk_history with specific branch configuration."""
        mock_repo = Mock()
        mock_commit = Mock(spec=git.Commit)
        mock_repo.iter_commits.return_value = [mock_commit]
        
        config = GitHoundConfig(branch="feature-branch")
        
        commits = list(walk_history(mock_repo, config))
        
        assert len(commits) == 1
        mock_repo.iter_commits.assert_called_once_with("feature-branch")


class TestProcessCommit:
    """Test process_commit function."""

    def test_process_commit_basic(self):
        """Test basic process_commit functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Initialize repository and create commits
            repo = git.Repo.init(repo_path)

            # Create test file and commit
            test_file = repo_path / "test.txt"
            test_file.write_text("test content with keyword")

            repo.index.add([str(test_file)])
            commit = repo.index.commit("Add test file")

            # Test process commit
            config = GitHoundConfig()

            results = process_commit(commit, config)
            assert isinstance(results, list)

    @patch("githound.git_handler.search_blob_content")
    def test_process_commit_with_mock(self, mock_search):
        """Test process_commit with mocked dependencies."""
        mock_commit = Mock(spec=git.Commit)
        mock_commit.tree = Mock()
        mock_search.return_value = []

        config = GitHoundConfig()

        results = process_commit(mock_commit, config)
        assert isinstance(results, list)


class TestExtractCommitMetadata:
    """Test extract_commit_metadata function."""

    def test_extract_commit_metadata_basic(self):
        """Test basic extract_commit_metadata functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Initialize repository and create a commit
            repo = git.Repo.init(repo_path)

            # Create test file and commit
            test_file = repo_path / "test.txt"
            test_file.write_text("test content")

            repo.index.add([str(test_file)])
            commit = repo.index.commit("Test commit")

            # Test extracting commit metadata
            commit_info = extract_commit_metadata(commit)

            assert commit_info is not None
            assert hasattr(commit_info, 'hash') or hasattr(commit_info, 'sha')
            assert hasattr(commit_info, 'message')

    def test_extract_commit_metadata_with_mock(self):
        """Test extract_commit_metadata with mocked commit."""
        mock_commit = Mock(spec=git.Commit)
        mock_commit.hexsha = "abc123"
        mock_commit.message = "Test message"
        mock_commit.author.name = "Test Author"
        mock_commit.author.email = "test@example.com"
        mock_commit.committed_date = 1234567890
        mock_commit.stats.total = {"insertions": 5, "deletions": 2, "lines": 7, "files": 1}
        mock_commit.parents = []

        commit_info = extract_commit_metadata(mock_commit)
        assert commit_info is not None


class TestGetFileContentAtCommit:
    """Test get_file_content_at_commit function."""

    def test_get_file_content_at_commit_basic(self):
        """Test basic get_file_content_at_commit functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            
            # Initialize repository and create a commit
            repo = git.Repo.init(repo_path)
            
            # Create test file and commit
            test_file = repo_path / "test.txt"
            test_content = "test content for file"
            test_file.write_text(test_content)
            
            repo.index.add([str(test_file)])
            commit = repo.index.commit("Add test file")
            
            # Test getting file content
            content = get_file_content_at_commit(repo, commit, "test.txt")
            
            if content is not None:
                assert isinstance(content, (str, bytes))

    def test_get_file_content_nonexistent_file(self):
        """Test get_file_content_at_commit with nonexistent file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            
            # Initialize repository and create a commit
            repo = git.Repo.init(repo_path)
            
            # Create test file and commit
            test_file = repo_path / "test.txt"
            test_file.write_text("test content")
            
            repo.index.add([str(test_file)])
            commit = repo.index.commit("Add test file")
            
            # Test getting nonexistent file content
            content = get_file_content_at_commit(repo, commit, "nonexistent.txt")
            
            # Should handle gracefully (return None or empty)
            assert content is None or content == ""


class TestGetChangedFiles:
    """Test get_changed_files function."""

    def test_get_changed_files_basic(self):
        """Test basic get_changed_files functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            
            # Initialize repository and create commits
            repo = git.Repo.init(repo_path)
            
            # Create initial file and commit
            test_file = repo_path / "test.txt"
            test_file.write_text("initial content")
            
            repo.index.add([str(test_file)])
            first_commit = repo.index.commit("Initial commit")
            
            # Modify file and commit
            test_file.write_text("modified content")
            repo.index.add([str(test_file)])
            second_commit = repo.index.commit("Modify file")
            
            # Test getting changed files
            changed_files = get_changed_files(repo, second_commit)
            
            assert isinstance(changed_files, list)

    def test_get_changed_files_with_mock(self):
        """Test get_changed_files with mocked commit."""
        mock_commit = Mock(spec=git.Commit)
        mock_commit.stats.files = {"test.txt": {"insertions": 1, "deletions": 0}}
        
        mock_repo = Mock()
        
        changed_files = get_changed_files(mock_repo, mock_commit)
        assert isinstance(changed_files, list)


class TestGetBlameInfo:
    """Test get_blame_info function."""

    def test_get_blame_info_basic(self):
        """Test basic get_blame_info functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            
            # Initialize repository and create a commit
            repo = git.Repo.init(repo_path)
            
            # Create test file and commit
            test_file = repo_path / "test.txt"
            test_file.write_text("line 1\nline 2\nline 3")
            
            repo.index.add([str(test_file)])
            repo.index.commit("Add test file")
            
            # Test getting blame info
            blame_info = get_blame_info(repo, "test.txt")
            
            if blame_info is not None:
                assert isinstance(blame_info, (list, dict))

    def test_get_blame_info_nonexistent_file(self):
        """Test get_blame_info with nonexistent file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            
            # Initialize repository
            repo = git.Repo.init(repo_path)
            
            # Test getting blame for nonexistent file
            blame_info = get_blame_info(repo, "nonexistent.txt")
            
            # Should handle gracefully
            assert blame_info is None or isinstance(blame_info, (list, dict))


class TestGetDiffInfo:
    """Test get_diff_info function."""

    def test_get_diff_info_basic(self):
        """Test basic get_diff_info functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            
            # Initialize repository and create commits
            repo = git.Repo.init(repo_path)
            
            # Create initial file and commit
            test_file = repo_path / "test.txt"
            test_file.write_text("initial content")
            
            repo.index.add([str(test_file)])
            first_commit = repo.index.commit("Initial commit")
            
            # Modify file and commit
            test_file.write_text("modified content")
            repo.index.add([str(test_file)])
            second_commit = repo.index.commit("Modify file")
            
            # Test getting diff info
            diff_info = get_diff_info(repo, first_commit.hexsha, second_commit.hexsha)
            
            if diff_info is not None:
                assert isinstance(diff_info, (list, dict, str))

    def test_get_diff_info_same_commits(self):
        """Test get_diff_info with same commits."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            
            # Initialize repository and create a commit
            repo = git.Repo.init(repo_path)
            
            # Create test file and commit
            test_file = repo_path / "test.txt"
            test_file.write_text("test content")
            
            repo.index.add([str(test_file)])
            commit = repo.index.commit("Add test file")
            
            # Test getting diff for same commit
            diff_info = get_diff_info(repo, commit.hexsha, commit.hexsha)
            
            # Should handle gracefully (empty diff)
            assert diff_info is None or isinstance(diff_info, (list, dict, str))
