"""
Unit tests for GitOperationsManager class.

Tests all Git operations including repository management, branch operations,
commit operations, tag management, and remote operations.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from git import GitCommandError, InvalidGitRepositoryError, Actor

from githound.web.git_operations import GitOperationsManager, GitOperationError


@pytest.fixture
def git_ops_manager() -> None:
    """Create GitOperationsManager instance for testing."""
    return GitOperationsManager()


class TestRepositoryOperations:
    """Test repository initialization, cloning, and status operations."""
    
    def test_init_repository_success(self, git_ops_manager, temp_dir) -> None:
        """Test successful repository initialization."""
        repo_path = str(temp_dir / "new_repo")
        
        with patch('githound.web.git_operations.Repo') as mock_repo_class:
            mock_repo = Mock()
            mock_repo.bare = False
            mock_repo.git_dir = f"{repo_path}/.git"
            mock_repo.working_dir = repo_path
            mock_repo_class.init.return_value = mock_repo
            
            result = git_ops_manager.init_repository(repo_path, bare=False)
            
            assert result["path"] == repo_path
            assert result["bare"] is False
            assert result["status"] == "created"
            assert result["git_dir"] == f"{repo_path}/.git"
            assert result["working_dir"] == repo_path
            
            mock_repo_class.init.assert_called_once_with(Path(repo_path), bare=False)
    
    def test_init_repository_already_exists(self, git_ops_manager, temp_repo) -> None:
        """Test initialization of existing repository."""
        repo_path = str(temp_repo.working_dir)
        
        with patch('githound.web.git_operations.Repo') as mock_repo_class:
            mock_repo_class.return_value = temp_repo
            
            result = git_ops_manager.init_repository(repo_path, bare=False)
            
            assert result["status"] == "already_exists"
            assert result["path"] == repo_path
    
    def test_init_repository_non_empty_directory(self, git_ops_manager, temp_dir) -> None:
        """Test initialization in non-empty, non-git directory."""
        repo_path = temp_dir / "non_empty"
        repo_path.mkdir()
        (repo_path / "existing_file.txt").write_text("content")
        
        with pytest.raises(GitOperationError, match="not empty and not a Git repository"):
            git_ops_manager.init_repository(str(repo_path))
    
    def test_clone_repository_success(self, git_ops_manager, temp_dir) -> None:
        """Test successful repository cloning."""
        clone_path = str(temp_dir / "cloned_repo")
        test_url = "https://github.com/test/repo.git"
        
        with patch('githound.web.git_operations.Repo') as mock_repo_class:
            mock_repo = Mock()
            mock_repo.head.commit.hexsha = "abc123"
            mock_repo.head.commit.message = "Initial commit"
            mock_repo.head.commit.author.name = "Test User"
            mock_repo.head.commit.author.email = "test@example.com"
            mock_repo.active_branch.name = "main"
            mock_repo.remotes = []
            
            mock_repo_class.clone_from.return_value = mock_repo
            
            result = git_ops_manager.clone_repository(test_url, clone_path)
            
            assert result["path"] == clone_path
            assert result["url"] == test_url
            assert result["branch"] == "main"
            assert result["head_commit"] == "abc123"
            assert result["status"] == "cloned"
            
            mock_repo_class.clone_from.assert_called_once()
    
    def test_clone_repository_with_options(self, git_ops_manager, temp_dir) -> None:
        """Test repository cloning with additional options."""
        clone_path = str(temp_dir / "cloned_repo")
        test_url = "https://github.com/test/repo.git"
        
        with patch('githound.web.git_operations.Repo') as mock_repo_class:
            mock_repo = Mock()
            mock_repo.head.commit.hexsha = "abc123"
            mock_repo.head.commit.message = "Initial commit"
            mock_repo.head.commit.author.name = "Test User"
            mock_repo.head.commit.author.email = "test@example.com"
            mock_repo.active_branch.name = "develop"
            mock_repo.remotes = []
            
            mock_repo_class.clone_from.return_value = mock_repo
            
            result = git_ops_manager.clone_repository(
                test_url, clone_path, branch="develop", depth=1, recursive=True
            )
            
            assert result["branch"] == "develop"
            mock_repo_class.clone_from.assert_called_once()
            call_args = mock_repo_class.clone_from.call_args
            assert call_args[1]["branch"] == "develop"
            assert call_args[1]["depth"] == 1
            assert call_args[1]["recursive"] is True
    
    def test_clone_repository_target_not_empty(self, git_ops_manager, temp_dir) -> None:
        """Test cloning to non-empty directory."""
        clone_path = temp_dir / "existing_dir"
        clone_path.mkdir()
        (clone_path / "file.txt").write_text("content")
        
        with pytest.raises(GitOperationError, match="not empty"):
            git_ops_manager.clone_repository("https://github.com/test/repo.git", str(clone_path))
    
    def test_get_repository_status_clean(self, git_ops_manager, temp_repo) -> None:
        """Test getting status of clean repository."""
        repo_path = str(temp_repo.working_dir)

        with patch('githound.web.git_operations.get_repository') as mock_get_repo:
            mock_repo = Mock()
            mock_repo.is_dirty = Mock(return_value=False)
            mock_repo.untracked_files = []
            mock_repo.index.diff = Mock(return_value=[])
            mock_repo.active_branch.name = "master"
            mock_repo.active_branch.tracking_branch = Mock(return_value=None)
            mock_repo.head.commit.hexsha = "abc123"
            mock_repo.iter_commits = Mock(return_value=["commit1", "commit2"])
            mock_repo.git.stash = Mock(return_value="")
            mock_get_repo.return_value = mock_repo

            result = git_ops_manager.get_repository_status(repo_path)

            assert result["is_dirty"] is False
            assert result["untracked_files"] == []
            assert result["modified_files"] == []
            assert result["staged_files"] == []
            assert result["current_branch"] == "master"
            assert result["head_commit"] == "abc123"
            assert result["total_commits"] == 2
    
    def test_get_repository_status_dirty(self, git_ops_manager, temp_repo) -> None:
        """Test getting status of dirty repository."""
        repo_path = str(temp_repo.working_dir)

        with patch('githound.web.git_operations.get_repository') as mock_get_repo:
            mock_repo = Mock()
            mock_repo.is_dirty = Mock(return_value=True)
            mock_repo.untracked_files = ["new_file.txt"]

            # Mock diff objects
            mock_diff = Mock()
            mock_diff.a_path = "modified_file.txt"
            mock_diff.deleted_file = False
            mock_repo.index.diff = Mock(return_value=[mock_diff])

            mock_repo.active_branch.name = "master"
            mock_repo.head.commit.hexsha = "abc123"
            mock_repo.iter_commits = Mock(return_value=["commit1"])
            mock_repo.git.stash = Mock(return_value="")
            mock_get_repo.return_value = mock_repo

            result = git_ops_manager.get_repository_status(repo_path)

            assert result["is_dirty"] is True
            assert "new_file.txt" in result["untracked_files"]
            assert "modified_file.txt" in result["modified_files"]


class TestBranchOperations:
    """Test branch management operations."""
    
    def test_list_branches_local_only(self, git_ops_manager, temp_repo) -> None:
        """Test listing local branches only."""
        repo_path = str(temp_repo.working_dir)

        with patch('githound.web.git_operations.get_repository') as mock_get_repo:
            mock_repo = Mock()

            # Mock branches
            mock_branch = Mock()
            mock_branch.name = "main"
            mock_branch.commit.hexsha = "abc123"
            mock_branch.commit.message = "Latest commit"
            mock_branch.commit.author.name = "Test User"
            mock_branch.commit.author.email = "test@example.com"
            mock_branch.commit.committed_datetime = "2024-01-01T00:00:00Z"
            mock_branch.tracking_branch = Mock(return_value=None)

            mock_repo.branches = [mock_branch]
            mock_repo.active_branch = mock_branch
            mock_repo.remotes = []
            mock_get_repo.return_value = mock_repo

            result = git_ops_manager.list_branches(repo_path, include_remote=False)

            assert len(result) == 1
            assert result[0]["name"] == "main"
            assert result[0]["commit_hash"] == "abc123"
            assert result[0]["is_current"] is True
            assert result[0]["is_remote"] is False
    
    def test_create_branch_success(self, git_ops_manager, temp_repo) -> None:
        """Test successful branch creation."""
        repo_path = str(temp_repo.working_dir)
        branch_name = "feature-branch"

        with patch('githound.web.git_operations.get_repository') as mock_get_repo:
            mock_repo = Mock()

            # Mock existing branches
            mock_repo.branches = []

            # Mock new branch creation
            mock_new_branch = Mock()
            mock_new_branch.commit.hexsha = "def456"
            mock_repo.create_head = Mock(return_value=mock_new_branch)
            mock_get_repo.return_value = mock_repo

            result = git_ops_manager.create_branch(repo_path, branch_name, checkout=True)

            assert result["name"] == branch_name
            assert result["commit_hash"] == "def456"
            assert result["checked_out"] is True
            assert result["status"] == "created"

            mock_repo.create_head.assert_called_once_with(branch_name)
            mock_new_branch.checkout.assert_called_once()
    
    def test_create_branch_already_exists(self, git_ops_manager, temp_repo) -> None:
        """Test creating branch that already exists."""
        repo_path = str(temp_repo.working_dir)
        branch_name = "existing-branch"
        
        with patch('githound.web.git_operations.get_repository') as mock_get_repo:
            mock_repo = Mock()

            # Mock existing branch
            mock_branch = Mock()
            mock_branch.name = branch_name
            mock_repo.branches = [mock_branch]
            mock_get_repo.return_value = mock_repo
            
            with pytest.raises(GitOperationError, match="already exists"):
                git_ops_manager.create_branch(repo_path, branch_name)
    
    def test_delete_branch_success(self, git_ops_manager, temp_repo) -> None:
        """Test successful branch deletion."""
        repo_path = str(temp_repo.working_dir)
        branch_name = "feature-branch"
        
        with patch('githound.web.git_operations.get_repository') as mock_get_repo:
            mock_repo = Mock()

            # Mock branches
            mock_branch = Mock()
            mock_branch.name = branch_name
            mock_branch.commit.hexsha = "abc123"

            mock_active_branch = Mock()
            mock_active_branch.name = "main"

            # Mock branches as both iterable and indexable
            mock_branches = Mock()
            mock_branches.__iter__ = Mock(return_value=iter([mock_branch]))
            mock_branches.__getitem__ = Mock(return_value=mock_branch)

            mock_repo.branches = mock_branches
            mock_repo.active_branch = mock_active_branch
            mock_repo.delete_head = Mock()
            mock_get_repo.return_value = mock_repo
            
            result = git_ops_manager.delete_branch(repo_path, branch_name, force=False)
            
            assert result["name"] == branch_name
            assert result["last_commit"] == "abc123"
            assert result["forced"] is False
            assert result["status"] == "deleted"
            
            mock_repo.delete_head.assert_called_once_with(mock_branch, force=False)
    
    def test_delete_current_branch(self, git_ops_manager, temp_repo) -> None:
        """Test deleting current branch (should fail)."""
        repo_path = str(temp_repo.working_dir)
        branch_name = "current-branch"
        
        with patch('githound.web.git_operations.get_repository') as mock_get_repo:
            mock_repo = Mock()

            # Mock current branch
            mock_branch = Mock()
            mock_branch.name = branch_name

            # Mock branches as both iterable and indexable
            mock_branches = Mock()
            mock_branches.__iter__ = Mock(return_value=iter([mock_branch]))
            mock_branches.__getitem__ = Mock(return_value=mock_branch)

            mock_repo.branches = mock_branches
            mock_repo.active_branch = mock_branch
            mock_get_repo.return_value = mock_repo
            
            with pytest.raises(GitOperationError, match="Cannot delete current branch"):
                git_ops_manager.delete_branch(repo_path, branch_name)
    
    def test_checkout_branch_success(self, git_ops_manager, temp_repo) -> None:
        """Test successful branch checkout."""
        repo_path = str(temp_repo.working_dir)
        branch_name = "feature-branch"
        
        with patch('githound.web.git_operations.get_repository') as mock_get_repo:
            mock_repo = Mock()

            # Mock clean repository
            mock_repo.is_dirty = Mock(return_value=False)

            # Mock branch
            mock_branch = Mock()
            mock_branch.name = branch_name

            # Mock branches as both iterable and indexable
            mock_branches = Mock()
            mock_branches.__iter__ = Mock(return_value=iter([mock_branch]))
            mock_branches.__getitem__ = Mock(return_value=mock_branch)

            mock_repo.branches = mock_branches
            mock_repo.head.commit.hexsha = "abc123"
            mock_get_repo.return_value = mock_repo
            
            result = git_ops_manager.checkout_branch(repo_path, branch_name)
            
            assert result["branch"] == branch_name
            assert result["commit_hash"] == "abc123"
            assert result["status"] == "checked_out"
            
            mock_branch.checkout.assert_called_once()
    
    def test_checkout_branch_dirty_repo(self, git_ops_manager, temp_repo) -> None:
        """Test checkout with uncommitted changes."""
        repo_path = str(temp_repo.working_dir)
        branch_name = "feature-branch"
        
        with patch('githound.web.git_operations.get_repository') as mock_get_repo:
            mock_repo = Mock()
            mock_repo.is_dirty = Mock(return_value=True)
            mock_get_repo.return_value = mock_repo
            
            with pytest.raises(GitOperationError, match="uncommitted changes"):
                git_ops_manager.checkout_branch(repo_path, branch_name)


class TestCommitOperations:
    """Test commit creation, amendment, revert, and cherry-pick operations."""

    def test_create_commit_success(self, git_ops_manager, temp_repo) -> None:
        """Test successful commit creation."""
        repo_path = str(temp_repo.working_dir)
        commit_message = "Test commit"

        with patch('githound.web.git_operations.get_repository') as mock_get_repo:
            mock_repo = Mock()

            # Mock commit creation
            mock_commit = Mock()
            mock_commit.hexsha = "abc123"
            mock_commit.message = commit_message
            mock_commit.author.name = "Test User"
            mock_commit.author.email = "test@example.com"
            mock_commit.committed_datetime = "2024-01-01T00:00:00Z"
            mock_commit.stats.files = {"file1.txt": {}, "file2.txt": {}}
            mock_commit.stats.total = {"insertions": 10, "deletions": 5}

            mock_repo.index.diff = Mock(return_value=[Mock()])  # Has changes
            mock_repo.index.commit = Mock(return_value=mock_commit)
            mock_repo.git.add = Mock()
            mock_get_repo.return_value = mock_repo

            result = git_ops_manager.create_commit(
                repo_path, commit_message, all_files=True
            )

            assert result["commit_hash"] == "abc123"
            assert result["message"] == commit_message
            assert result["files_changed"] == 2
            assert result["insertions"] == 10
            assert result["deletions"] == 5
            assert result["status"] == "created"

            mock_repo.git.add.assert_called_once_with(A=True)
            mock_repo.index.commit.assert_called_once()

    def test_create_commit_no_changes(self, git_ops_manager, temp_repo) -> None:
        """Test commit creation with no changes."""
        repo_path = str(temp_repo.working_dir)

        with patch('githound.web.git_operations.get_repository') as mock_get_repo:
            mock_repo = Mock()
            mock_repo.index.diff = Mock(return_value=[])  # No changes
            mock_get_repo.return_value = mock_repo

            with pytest.raises(GitOperationError, match="No changes to commit"):
                git_ops_manager.create_commit(repo_path, "Test commit")

    def test_create_commit_with_author(self, git_ops_manager, temp_repo) -> None:
        """Test commit creation with custom author."""
        repo_path = str(temp_repo.working_dir)

        with patch('githound.web.git_operations.get_repository') as mock_get_repo:
            mock_repo = Mock()

            mock_commit = Mock()
            mock_commit.hexsha = "abc123"
            mock_commit.author.name = "Custom Author"
            mock_commit.author.email = "custom@example.com"
            mock_commit.committed_datetime = "2024-01-01T00:00:00Z"
            mock_commit.stats.files = {}
            mock_commit.stats.total = {"insertions": 0, "deletions": 0}

            mock_repo.index.diff = Mock(return_value=[Mock()])
            mock_repo.index.commit = Mock(return_value=mock_commit)
            mock_repo.git.add = Mock()
            mock_get_repo.return_value = mock_repo

            result = git_ops_manager.create_commit(
                repo_path, "Test commit",
                author_name="Custom Author",
                author_email="custom@example.com"
            )

            # Verify Actor was created and passed to commit
            call_args = mock_repo.index.commit.call_args
            assert call_args[1]["author"] is not None

    def test_amend_commit_success(self, git_ops_manager, temp_repo) -> None:
        """Test successful commit amendment."""
        repo_path = str(temp_repo.working_dir)
        new_message = "Amended commit message"

        with patch('githound.web.git_operations.get_repository') as mock_get_repo:
            mock_repo = Mock()

            # Mock current commit
            mock_current_commit = Mock()
            mock_current_commit.hexsha = "old123"
            mock_current_commit.message = "Original message"
            mock_repo.head.commit = mock_current_commit

            # Mock amended commit
            mock_amended_commit = Mock()
            mock_amended_commit.hexsha = "new456"
            mock_amended_commit.message = new_message
            mock_amended_commit.author.name = "Test User"
            mock_amended_commit.author.email = "test@example.com"
            mock_amended_commit.committed_datetime = "2024-01-01T00:00:00Z"

            mock_repo.index.commit = Mock(return_value=mock_amended_commit)
            mock_get_repo.return_value = mock_repo

            result = git_ops_manager.amend_commit(repo_path, message=new_message)

            assert result["old_commit_hash"] == "old123"
            assert result["new_commit_hash"] == "new456"
            assert result["message"] == new_message
            assert result["status"] == "amended"

            mock_repo.index.commit.assert_called_once_with(new_message, amend=True)

    def test_revert_commit_success(self, git_ops_manager, temp_repo) -> None:
        """Test successful commit revert."""
        repo_path = str(temp_repo.working_dir)
        commit_hash = "abc123"

        with patch('githound.web.git_operations.get_repository') as mock_get_repo:
            mock_repo = Mock()

            # Mock commit to revert
            mock_commit = Mock()
            mock_commit.message = "Original commit message"
            mock_repo.commit = Mock(return_value=mock_commit)

            # Mock revert commit
            mock_revert_commit = Mock()
            mock_revert_commit.hexsha = "revert456"
            mock_repo.head.commit = mock_revert_commit
            mock_repo.git.revert = Mock()
            mock_get_repo.return_value = mock_repo

            result = git_ops_manager.revert_commit(repo_path, commit_hash, no_commit=False)

            assert result["reverted_commit"] == commit_hash
            assert result["revert_commit"] == "revert456"
            assert result["status"] == "reverted"

            mock_repo.git.revert.assert_called_once_with(commit_hash, no_commit=False)

    def test_cherry_pick_commit_success(self, git_ops_manager, temp_repo) -> None:
        """Test successful commit cherry-pick."""
        repo_path = str(temp_repo.working_dir)
        commit_hash = "abc123"

        with patch('githound.web.git_operations.get_repository') as mock_get_repo:
            mock_repo = Mock()

            # Mock commit to cherry-pick
            mock_commit = Mock()
            mock_commit.message = "Cherry-pick commit"
            mock_commit.author.name = "Original Author"
            mock_commit.author.email = "author@example.com"
            mock_repo.commit = Mock(return_value=mock_commit)

            # Mock cherry-pick commit
            mock_cherry_commit = Mock()
            mock_cherry_commit.hexsha = "cherry456"
            mock_repo.head.commit = mock_cherry_commit
            mock_repo.git.cherry_pick = Mock()
            mock_get_repo.return_value = mock_repo

            result = git_ops_manager.cherry_pick_commit(repo_path, commit_hash, no_commit=False)

            assert result["original_commit"] == commit_hash
            assert result["cherry_pick_commit"] == "cherry456"
            assert result["status"] == "cherry_picked"

            mock_repo.git.cherry_pick.assert_called_once_with(commit_hash, no_commit=False)


class TestTagOperations:
    """Test tag management operations."""

    def test_list_tags_success(self, git_ops_manager, temp_repo) -> None:
        """Test successful tag listing."""
        repo_path = str(temp_repo.working_dir)

        with patch('githound.web.git_operations.get_repository') as mock_get_repo:
            mock_repo = Mock()

            # Mock tags
            mock_tag1 = Mock()
            mock_tag1.name = "v1.0.0"
            mock_tag1.commit.hexsha = "abc123"
            mock_tag1.tag = None  # Lightweight tag

            mock_tag2 = Mock()
            mock_tag2.name = "v2.0.0"
            mock_tag2.commit.hexsha = "def456"
            mock_tag2.tag.message = "Version 2.0.0"
            mock_tag2.tag.tagger.name = "Test User"
            mock_tag2.tag.tagger.email = "test@example.com"
            mock_tag2.tag.tagged_date = "2024-01-01T00:00:00Z"

            mock_repo.tags = [mock_tag1, mock_tag2]
            mock_get_repo.return_value = mock_repo

            result = git_ops_manager.list_tags(repo_path)

            assert len(result) == 2
            assert result[0]["name"] == "v1.0.0"
            assert result[0]["is_annotated"] is False
            assert result[1]["name"] == "v2.0.0"
            assert result[1]["is_annotated"] is True
            assert result[1]["message"] == "Version 2.0.0"

    def test_create_lightweight_tag(self, git_ops_manager, temp_repo) -> None:
        """Test creating lightweight tag."""
        repo_path = str(temp_repo.working_dir)
        tag_name = "v1.0.0"

        with patch('githound.web.git_operations.get_repository') as mock_get_repo:
            mock_repo = Mock()

            # Mock tag creation
            mock_commit = Mock()
            mock_commit.hexsha = "abc123"
            mock_repo.head.commit = mock_commit
            mock_repo.tags = []
            mock_repo.create_tag = Mock()
            mock_get_repo.return_value = mock_repo

            result = git_ops_manager.create_tag(repo_path, tag_name)

            assert result["name"] == tag_name
            assert result["commit_hash"] == "abc123"
            assert result["is_annotated"] is False
            assert result["status"] == "created"

            mock_repo.create_tag.assert_called_once_with(tag_name, ref=mock_commit, force=False)

    def test_create_annotated_tag(self, git_ops_manager, temp_repo) -> None:
        """Test creating annotated tag."""
        repo_path = str(temp_repo.working_dir)
        tag_name = "v2.0.0"
        tag_message = "Version 2.0.0 release"

        with patch('githound.web.git_operations.get_repository') as mock_get_repo:
            mock_repo = Mock()

            mock_commit = Mock()
            mock_commit.hexsha = "def456"
            mock_repo.head.commit = mock_commit
            mock_repo.tags = []
            mock_repo.create_tag = Mock()
            mock_get_repo.return_value = mock_repo

            result = git_ops_manager.create_tag(repo_path, tag_name, message=tag_message)

            assert result["name"] == tag_name
            assert result["message"] == tag_message
            assert result["is_annotated"] is True
            assert result["status"] == "created"

            mock_repo.create_tag.assert_called_once_with(
                tag_name, ref=mock_commit, message=tag_message, force=False
            )

    def test_delete_tag_success(self, git_ops_manager, temp_repo) -> None:
        """Test successful tag deletion."""
        repo_path = str(temp_repo.working_dir)
        tag_name = "v1.0.0"

        with patch('githound.web.git_operations.get_repository') as mock_get_repo:
            mock_repo = Mock()

            # Mock tag
            mock_tag = Mock()
            mock_tag.commit.hexsha = "abc123"

            # Mock tags as indexable
            mock_tags = Mock()
            mock_tags.__getitem__ = Mock(return_value=mock_tag)

            mock_repo.tags = mock_tags
            mock_repo.delete_tag = Mock()
            mock_get_repo.return_value = mock_repo

            result = git_ops_manager.delete_tag(repo_path, tag_name)

            assert result["name"] == tag_name
            assert result["commit_hash"] == "abc123"
            assert result["status"] == "deleted"

            mock_repo.delete_tag.assert_called_once_with(mock_tag)
