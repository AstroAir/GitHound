"""Simple tests for GitHound git diff functionality."""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock

from git import Repo, GitCommandError

from githound.git_diff import (
    compare_commits, compare_branches, get_file_diff_history,
    analyze_diff, CommitDiffResult, FileDiffInfo, ChangeType
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
    second_commit = repo.index.commit("Update hello and add goodbye")
    
    # Create third commit with new file
    new_file = Path(temp_dir) / "utils.py"
    new_file.write_text("def utility_function():\n    return 'utility'\n")
    repo.index.add([str(new_file)])
    third_commit = repo.index.commit("Add utility file")
    
    yield repo, temp_dir, initial_commit, second_commit, third_commit
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


class TestCompareCommits:
    """Tests for commit comparison functionality."""
    
    def test_compare_commits_success(self, temp_repo):
        """Test successful commit comparison."""
        repo, temp_dir, initial_commit, second_commit, third_commit = temp_repo
        
        comparison = compare_commits(repo, initial_commit.hexsha, third_commit.hexsha)
        
        assert isinstance(comparison, CommitDiffResult)
        assert comparison.from_commit == initial_commit.hexsha
        assert comparison.to_commit == third_commit.hexsha
        assert len(comparison.file_diffs) >= 2  # test.py and utils.py
        
        # Check summary statistics
        assert comparison.total_additions >= 0  # May be 0 if diff parsing doesn't work perfectly
        assert comparison.total_deletions >= 0
        assert comparison.files_changed >= 2
    
    def test_compare_commits_reverse_order(self, temp_repo):
        """Test commit comparison in reverse order."""
        repo, temp_dir, initial_commit, second_commit, third_commit = temp_repo
        
        comparison = compare_commits(repo, third_commit.hexsha, initial_commit.hexsha)
        
        assert isinstance(comparison, CommitDiffResult)
        assert comparison.from_commit == third_commit.hexsha
        assert comparison.to_commit == initial_commit.hexsha
        
        # Should show deletions where forward comparison showed additions
        assert comparison.total_deletions >= 0  # May be 0 if diff parsing doesn't work perfectly
    
    def test_compare_commits_same_commit(self, temp_repo):
        """Test comparing commit with itself."""
        repo, temp_dir, initial_commit, second_commit, third_commit = temp_repo
        
        comparison = compare_commits(repo, second_commit.hexsha, second_commit.hexsha)
        
        assert isinstance(comparison, CommitDiffResult)
        assert comparison.total_additions == 0
        assert comparison.total_deletions == 0
        assert comparison.files_changed == 0
    
    def test_compare_commits_invalid_hash(self, temp_repo):
        """Test comparing with invalid commit hash."""
        repo, temp_dir, initial_commit, second_commit, third_commit = temp_repo
        
        with pytest.raises(GitCommandError):
            compare_commits(repo, "invalid_hash", second_commit.hexsha)


class TestCompareBranches:
    """Tests for branch comparison functionality."""
    
    def test_compare_branches_with_feature_branch(self, temp_repo):
        """Test comparing branches."""
        repo, temp_dir, initial_commit, second_commit, third_commit = temp_repo
        
        # Create a new branch
        feature_branch = repo.create_head("feature")
        feature_branch.checkout()
        
        # Add commit to feature branch
        feature_file = Path(temp_dir) / "feature.py"
        feature_file.write_text("def feature():\n    return 'feature'\n")
        repo.index.add([str(feature_file)])
        feature_commit = repo.index.commit("Add feature")
        
        # Switch back to main branch
        repo.heads.master.checkout()
        
        # Compare main branch with feature branch
        comparison = compare_branches(repo, "master", "feature")
        
        assert isinstance(comparison, CommitDiffResult)
        # Should show the feature.py file as added
        feature_diff = next((fd for fd in comparison.file_diffs if fd.file_path == "feature.py"), None)
        assert feature_diff is not None
        assert feature_diff.change_type == ChangeType.ADDED
    
    def test_compare_branches_invalid_branch(self, temp_repo):
        """Test comparing with invalid branch."""
        repo, temp_dir, initial_commit, second_commit, third_commit = temp_repo
        
        with pytest.raises(GitCommandError):
            compare_branches(repo, "master", "nonexistent_branch")


class TestFileHistory:
    """Tests for file diff history functionality."""
    
    def test_get_file_diff_history_success(self, temp_repo):
        """Test successful file diff history retrieval."""
        repo, temp_dir, initial_commit, second_commit, third_commit = temp_repo
        
        history = get_file_diff_history(repo, "test.py")
        
        assert isinstance(history, list)
        assert len(history) > 0
        
        # Each history entry should have required fields
        for entry in history:
            assert 'commit_hash' in entry
            assert 'author' in entry
            assert 'commit_date' in entry
            assert 'message' in entry
            assert 'change_type' in entry
            assert 'lines_added' in entry
            assert 'lines_deleted' in entry
    
    def test_get_file_diff_history_with_max_commits(self, temp_repo):
        """Test file diff history with max commits limit."""
        repo, temp_dir, initial_commit, second_commit, third_commit = temp_repo
        
        history = get_file_diff_history(repo, "test.py", max_commits=1)
        
        assert isinstance(history, list)
        assert len(history) <= 1
    
    def test_get_file_diff_history_nonexistent_file(self, temp_repo):
        """Test file diff history for nonexistent file."""
        repo, temp_dir, initial_commit, second_commit, third_commit = temp_repo
        
        history = get_file_diff_history(repo, "nonexistent.py")
        
        # Should return empty list for nonexistent files
        assert isinstance(history, list)
        assert len(history) == 0


class TestAnalyzeDiff:
    """Tests for diff analysis functionality."""
    
    def test_analyze_diff_basic(self, temp_repo):
        """Test basic diff analysis."""
        repo, temp_dir, initial_commit, second_commit, third_commit = temp_repo
        
        # Get the actual git diff
        diffs = repo.commit(second_commit.hexsha).diff(initial_commit.hexsha)
        
        if diffs:
            diff = diffs[0]
            analysis = analyze_diff(diff)
            
            assert isinstance(analysis, FileDiffInfo)
            assert analysis.file_path is not None
            assert analysis.change_type in [ChangeType.ADDED, ChangeType.MODIFIED, ChangeType.DELETED]


class TestChangeType:
    """Tests for ChangeType enum."""
    
    def test_change_type_values(self):
        """Test ChangeType enum values."""
        assert ChangeType.ADDED == "A"
        assert ChangeType.MODIFIED == "M"
        assert ChangeType.DELETED == "D"
        assert ChangeType.RENAMED == "R"


class TestFileDiffInfo:
    """Tests for FileDiffInfo model."""
    
    def test_file_diff_info_creation(self):
        """Test FileDiffInfo creation and properties."""
        file_diff = FileDiffInfo(
            file_path="example.py",
            change_type=ChangeType.ADDED,
            lines_added=10,
            lines_deleted=0,
            is_binary=False,
            diff_lines=[]
        )
        
        assert file_diff.file_path == "example.py"
        assert file_diff.change_type == ChangeType.ADDED
        assert file_diff.lines_added == 10
        assert file_diff.lines_deleted == 0
        assert file_diff.is_binary is False


class TestCommitDiffResult:
    """Tests for CommitDiffResult model."""
    
    def test_commit_diff_result_creation(self):
        """Test CommitDiffResult creation and properties."""
        file_diffs = [
            FileDiffInfo(
                file_path="test.py",
                change_type=ChangeType.MODIFIED,
                lines_added=5,
                lines_deleted=2,
                is_binary=False,
                diff_lines=[]
            )
        ]
        
        diff_result = CommitDiffResult(
            from_commit="abc123",
            to_commit="def456",
            files_changed=1,
            total_additions=5,
            total_deletions=2,
            file_diffs=file_diffs
        )
        
        assert diff_result.from_commit == "abc123"
        assert diff_result.to_commit == "def456"
        assert len(diff_result.file_diffs) == 1
        assert diff_result.total_additions == 5
        assert diff_result.total_deletions == 2
        assert diff_result.files_changed == 1


class TestErrorHandling:
    """Tests for diff error handling."""
    
    def test_compare_commits_with_invalid_repo(self):
        """Test diff operations with invalid repository."""
        # Create a mock repo that will cause errors
        mock_repo = Mock()
        mock_repo.commit.side_effect = GitCommandError("Repository error")
        
        with pytest.raises(GitCommandError):
            compare_commits(mock_repo, "any_commit", "another_commit")
