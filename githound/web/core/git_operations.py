"""
Git operations manager for comprehensive Git functionality.

Provides high-level Git operations with proper error handling and validation.
"""

from pathlib import Path
from typing import Any, Optional

from git import Actor, InvalidGitRepositoryError, Repo

from ...git_handler import get_repository


class GitOperationError(Exception):
    """Custom exception for Git operation errors."""
    pass


class GitOperationsManager:
    """Manages all Git operations with comprehensive error handling."""

    def __init__(self) -> None:
        self.operation_timeout = 300  # 5 minutes default timeout

    # Repository Operations

    def init_repository(self, path: str, bare: bool = False) -> dict[str, Any]:
        """Initialize a new Git repository."""
        try:
            repo_path = Path(path)

            # Check if directory exists and is empty (or create it)
            if repo_path.exists():
                if any(repo_path.iterdir()):
                    # Check if it's already a git repo
                    try:
                        existing_repo = Repo(repo_path)
                        return {
                            "path": str(repo_path),
                            "bare": existing_repo.bare,
                            "status": "already_exists",
                            "head_commit": existing_repo.head.commit.hexsha if not existing_repo.bare else None
                        }
                    except InvalidGitRepositoryError:
                        raise GitOperationError(
                            f"Directory {path} is not empty and not a Git repository")
            else:
                repo_path.mkdir(parents=True, exist_ok=True)

            # Initialize repository
            repo = Repo.init(repo_path, bare=bare)

            return {
                "path": str(repo_path),
                "bare": bare,
                "status": "created",
                "git_dir": str(repo.git_dir),
                "working_dir": str(repo.working_dir) if not bare else None
            }

        except Exception as e:
            raise GitOperationError(f"Failed to initialize repository: {e}")

    def clone_repository(
        self,
        url: str,
        path: str,
        branch: str | None = None,
        depth: int | None = None,
        recursive: bool = False
    ) -> dict[str, Any]:
        """Clone a remote repository."""
        try:
            repo_path = Path(path)

            # Check if target directory exists
            if repo_path.exists() and any(repo_path.iterdir()):
                raise GitOperationError(
                    f"Target directory {path} is not empty")

            # Clone repository
            if branch and depth and recursive:
                repo = Repo.clone_from(
                    url, str(repo_path), branch=branch, depth=depth, recursive=recursive)
            elif branch and depth:
                repo = Repo.clone_from(
                    url, str(repo_path), branch=branch, depth=depth)
            elif branch and recursive:
                repo = Repo.clone_from(
                    url, str(repo_path), branch=branch, recursive=recursive)
            elif depth and recursive:
                repo = Repo.clone_from(
                    url, str(repo_path), depth=depth, recursive=recursive)
            elif branch:
                repo = Repo.clone_from(url, str(repo_path), branch=branch)
            elif depth:
                repo = Repo.clone_from(url, str(repo_path), depth=depth)
            elif recursive:
                repo = Repo.clone_from(
                    url, str(repo_path), recursive=recursive)
            else:
                repo = Repo.clone_from(url, str(repo_path))

            return {
                "path": str(repo_path),
                "url": url,
                "branch": branch or "main",
                "status": "cloned",
                "git_dir": str(repo.git_dir),
                "working_dir": str(repo.working_dir),
                "head_commit": repo.head.commit.hexsha
            }

        except Exception as e:
            raise GitOperationError(f"Failed to clone repository: {e}")

    def get_repository_status(self, path: str) -> dict[str, Any]:
        """Get comprehensive repository status."""
        try:
            repo = get_repository(Path(path))

            # Get status information
            status = {
                "path": str(repo.working_dir),
                "is_dirty": repo.is_dirty(),
                "untracked_files": repo.untracked_files,
                "modified_files": [item.a_path for item in repo.index.diff(None)],
                "staged_files": [item.a_path for item in repo.index.diff("HEAD")],
                "current_branch": repo.active_branch.name if repo.active_branch else None,
                "head_commit": repo.head.commit.hexsha,
                "total_commits": len(list(repo.iter_commits())),
                "branches": [branch.name for branch in repo.branches],
                "tags": [tag.name for tag in repo.tags],
                "remotes": [remote.name for remote in repo.remotes]
            }

            return status

        except Exception as e:
            raise GitOperationError(f"Failed to get repository status: {e}")

    def get_merge_conflicts(self, path: str) -> dict[str, Any]:
        """Get information about current merge conflicts."""
        try:
            repo = get_repository(Path(path))

            # Check for merge conflicts
            conflicts = []
            if repo.is_dirty():
                for item in repo.index.diff(None):
                    if item.change_type == 'M':  # Modified files might have conflicts
                        file_path = item.a_path
                        try:
                            with open(repo.working_dir / file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                if '<<<<<<< HEAD' in content:
                                    conflicts.append({
                                        "file_path": file_path,
                                        "status": "conflicted",
                                        "conflict_markers": True
                                    })
                        except (UnicodeDecodeError, FileNotFoundError):
                            # Skip binary files or missing files
                            pass

            return {
                "has_conflicts": len(conflicts) > 0,
                "conflicted_files": conflicts,
                "total_conflicts": len(conflicts),
                "merge_in_progress": repo.git.status().find("You have unmerged paths") != -1
            }

        except Exception as e:
            raise GitOperationError(f"Failed to get merge conflicts: {e}")

    # Branch Operations

    def create_branch(self, path: str, branch_name: str, start_point: str | None = None) -> dict[str, Any]:
        """Create a new branch."""
        try:
            repo = get_repository(Path(path))

            # Check if branch already exists
            if branch_name in [branch.name for branch in repo.branches]:
                raise GitOperationError(f"Branch '{branch_name}' already exists")

            # Create branch
            if start_point:
                new_branch = repo.create_head(branch_name, start_point)
            else:
                new_branch = repo.create_head(branch_name)

            return {
                "branch_name": branch_name,
                "start_point": start_point or "HEAD",
                "status": "created",
                "commit": new_branch.commit.hexsha
            }

        except Exception as e:
            raise GitOperationError(f"Failed to create branch: {e}")

    def delete_branch(self, path: str, branch_name: str, force: bool = False) -> dict[str, Any]:
        """Delete a branch."""
        try:
            repo = get_repository(Path(path))

            # Check if branch exists
            if branch_name not in [branch.name for branch in repo.branches]:
                raise GitOperationError(f"Branch '{branch_name}' does not exist")

            # Check if it's the current branch
            if repo.active_branch and repo.active_branch.name == branch_name:
                raise GitOperationError("Cannot delete the currently active branch")

            # Delete branch
            branch = repo.heads[branch_name]
            repo.delete_head(branch, force=force)

            return {
                "branch_name": branch_name,
                "status": "deleted",
                "force": force
            }

        except Exception as e:
            raise GitOperationError(f"Failed to delete branch: {e}")

    def switch_branch(self, path: str, branch_name: str) -> dict[str, Any]:
        """Switch to a different branch."""
        try:
            repo = get_repository(Path(path))

            # Check if branch exists
            if branch_name not in [branch.name for branch in repo.branches]:
                raise GitOperationError(f"Branch '{branch_name}' does not exist")

            # Check for uncommitted changes
            if repo.is_dirty():
                raise GitOperationError("Cannot switch branches with uncommitted changes")

            # Switch branch
            branch = repo.heads[branch_name]
            branch.checkout()

            return {
                "previous_branch": repo.active_branch.name if repo.active_branch else None,
                "current_branch": branch_name,
                "status": "switched",
                "head_commit": repo.head.commit.hexsha
            }

        except Exception as e:
            raise GitOperationError(f"Failed to switch branch: {e}")

    # Commit Operations

    def create_commit(
        self,
        path: str,
        message: str,
        author_name: str | None = None,
        author_email: str | None = None,
        add_all: bool = False
    ) -> dict[str, Any]:
        """Create a new commit."""
        try:
            repo = get_repository(Path(path))

            # Add files if requested
            if add_all:
                repo.git.add(A=True)

            # Check if there are changes to commit
            if not repo.index.diff("HEAD") and not repo.untracked_files:
                raise GitOperationError("No changes to commit")

            # Set author if provided
            author = None
            if author_name and author_email:
                author = Actor(author_name, author_email)

            # Create commit
            commit = repo.index.commit(message, author=author)

            return {
                "commit_hash": commit.hexsha,
                "message": message,
                "author": f"{commit.author.name} <{commit.author.email}>",
                "timestamp": commit.committed_datetime.isoformat(),
                "files_changed": len(commit.stats.files),
                "status": "created"
            }

        except Exception as e:
            raise GitOperationError(f"Failed to create commit: {e}")

    # Tag Operations

    def create_tag(self, path: str, tag_name: str, message: str | None = None, commit: str | None = None) -> dict[str, Any]:
        """Create a new tag."""
        try:
            repo = get_repository(Path(path))

            # Check if tag already exists
            if tag_name in [tag.name for tag in repo.tags]:
                raise GitOperationError(f"Tag '{tag_name}' already exists")

            # Create tag
            if commit:
                target_commit = repo.commit(commit)
            else:
                target_commit = repo.head.commit

            if message:
                tag = repo.create_tag(tag_name, ref=target_commit, message=message)
            else:
                tag = repo.create_tag(tag_name, ref=target_commit)

            return {
                "tag_name": tag_name,
                "commit": target_commit.hexsha,
                "message": message,
                "status": "created",
                "timestamp": target_commit.committed_datetime.isoformat()
            }

        except Exception as e:
            raise GitOperationError(f"Failed to create tag: {e}")

    def delete_tag(self, path: str, tag_name: str) -> dict[str, Any]:
        """Delete a tag."""
        try:
            repo = get_repository(Path(path))

            # Check if tag exists
            if tag_name not in [tag.name for tag in repo.tags]:
                raise GitOperationError(f"Tag '{tag_name}' does not exist")

            # Delete tag
            tag = repo.tags[tag_name]
            repo.delete_tag(tag)

            return {
                "tag_name": tag_name,
                "status": "deleted"
            }

        except Exception as e:
            raise GitOperationError(f"Failed to delete tag: {e}")
