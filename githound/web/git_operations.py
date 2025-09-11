"""
Git operations manager for comprehensive Git functionality.

Provides high-level Git operations with proper error handling and validation.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Dict, List

from git import (
    Actor, 
    Commit, 
    GitCommandError, 
    InvalidGitRepositoryError,
    Repo, 
    Remote,
    TagReference
)
from git.exc import GitError

from ..git_handler import get_repository


class GitOperationError(Exception):
    """Custom exception for Git operation errors."""
    pass


class GitOperationsManager:
    """Manages all Git operations with comprehensive error handling."""
    
    def __init__(self) -> None:
        self.operation_timeout = 300  # 5 minutes default timeout
    
    # Repository Operations
    
    def init_repository(self, path: str, bare: bool = False) -> Dict[str, Any]:
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
                        raise GitOperationError(f"Directory {path} is not empty and not a Git repository")
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
        branch: Optional[str] = None,
        depth: Optional[int] = None,
        recursive: bool = False
    ) -> Dict[str, Any]:
        """Clone a remote repository."""
        try:
            repo_path = Path(path)
            
            # Check if target directory exists
            if repo_path.exists() and any(repo_path.iterdir()):
                raise GitOperationError(f"Target directory {path} is not empty")
            
            # Clone repository
            if branch and depth and recursive:
                repo = Repo.clone_from(url, str(repo_path), branch=branch, depth=depth, recursive=recursive)
            elif branch and depth:
                repo = Repo.clone_from(url, str(repo_path), branch=branch, depth=depth)
            elif branch and recursive:
                repo = Repo.clone_from(url, str(repo_path), branch=branch, recursive=recursive)
            elif depth and recursive:
                repo = Repo.clone_from(url, str(repo_path), depth=depth, recursive=recursive)
            elif branch:
                repo = Repo.clone_from(url, str(repo_path), branch=branch)
            elif depth:
                repo = Repo.clone_from(url, str(repo_path), depth=depth)
            elif recursive:
                repo = Repo.clone_from(url, str(repo_path), recursive=recursive)
            else:
                repo = Repo.clone_from(url, str(repo_path))
            
            # Get repository info
            head_commit = repo.head.commit
            remotes = [{"name": remote.name, "url": list(remote.urls)[0]} for remote in repo.remotes]
            
            return {
                "path": str(repo_path),
                "url": url,
                "branch": branch or repo.active_branch.name,
                "head_commit": head_commit.hexsha,
                "commit_message": head_commit.message.strip(),
                "author": f"{head_commit.author.name} <{head_commit.author.email}>",
                "remotes": remotes,
                "status": "cloned"
            }
            
        except Exception as e:
            raise GitOperationError(f"Failed to clone repository: {e}")
    
    def get_repository_status(self, repo_path: str) -> Dict[str, Any]:
        """Get comprehensive repository status."""
        try:
            repo = get_repository(Path(repo_path))
            
            # Get file status
            untracked_files = list(repo.untracked_files)
            modified_files = [item.a_path for item in repo.index.diff(None)]
            staged_files = [item.a_path for item in repo.index.diff("HEAD")]
            deleted_files = [item.a_path for item in repo.index.diff(None) if item.deleted_file]
            
            # Get current branch
            try:
                current_branch = repo.active_branch.name
            except TypeError: Optional[current_branch] = None  # Detached HEAD
            
            # Get ahead/behind info if tracking remote
            ahead_behind = None
            if current_branch and repo.active_branch.tracking_branch():
                try:
                    ahead, behind = repo.git.rev_list(
                        "--left-right", "--count",
                        f"{repo.active_branch.tracking_branch()}...{current_branch}"
                    ).split("\t")
                    ahead_behind = {"ahead": int(ahead), "behind": int(behind)}
                except Exception:
                    pass
            
            return {
                "is_dirty": repo.is_dirty(),
                "untracked_files": untracked_files,
                "modified_files": modified_files,
                "staged_files": staged_files,
                "deleted_files": deleted_files,
                "current_branch": current_branch,
                "ahead_behind": ahead_behind,
                "head_commit": repo.head.commit.hexsha,
                "total_commits": len(list(repo.iter_commits())),
                "stash_count": len(repo.git.stash("list").splitlines()) if repo.git.stash("list") else 0
            }
            
        except Exception as e:
            raise GitOperationError(f"Failed to get repository status: {e}")
    
    # Branch Operations
    
    def list_branches(self, repo_path: str, include_remote: bool = True) -> List[Dict[str, Any]]:
        """List all branches in the repository."""
        try:
            repo = get_repository(Path(repo_path))
            branches: list[Any] = []
            
            # Local branches
            for branch in repo.branches:
                branch_info = {
                    "name": branch.name,
                    "commit_hash": branch.commit.hexsha,
                    "commit_message": branch.commit.message.strip(),
                    "author": f"{branch.commit.author.name} <{branch.commit.author.email}>",
                    "date": branch.commit.committed_datetime,
                    "is_current": branch == repo.active_branch,
                    "is_remote": False,
                    "tracking_branch": branch.tracking_branch().name if branch.tracking_branch() else None
                }
                branches.append(branch_info)
            
            # Remote branches
            if include_remote:
                for remote in repo.remotes:
                    for ref in remote.refs:
                        if ref.name.endswith("/HEAD"):
                            continue
                        
                        branch_info = {
                            "name": ref.name,
                            "commit_hash": ref.commit.hexsha,
                            "commit_message": ref.commit.message.strip(),
                            "author": f"{ref.commit.author.name} <{ref.commit.author.email}>",
                            "date": ref.commit.committed_datetime,
                            "is_current": False,
                            "is_remote": True,
                            "tracking_branch": None
                        }
                        branches.append(branch_info)
            
            return branches
            
        except Exception as e:
            raise GitOperationError(f"Failed to list branches: {e}")
    
    def create_branch(
        self, 
        repo_path: str, 
        branch_name: str, 
        start_point: Optional[str] = None,
        checkout: bool = True
    ) -> Dict[str, Any]:
        """Create a new branch."""
        try:
            repo = get_repository(Path(repo_path))
            
            # Check if branch already exists
            if branch_name in [b.name for b in repo.branches]:
                raise GitOperationError(f"Branch '{branch_name}' already exists")
            
            # Create branch
            if start_point:
                start_commit = repo.commit(start_point)
                new_branch = repo.create_head(branch_name, start_commit)
            else:
                new_branch = repo.create_head(branch_name)
            
            # Checkout if requested
            if checkout:
                new_branch.checkout()
            
            return {
                "name": branch_name,
                "commit_hash": new_branch.commit.hexsha,
                "start_point": start_point or "HEAD",
                "checked_out": checkout,
                "status": "created"
            }
            
        except Exception as e:
            raise GitOperationError(f"Failed to create branch: {e}")
    
    def delete_branch(self, repo_path: str, branch_name: str, force: bool = False) -> Dict[str, Any]:
        """Delete a branch."""
        try:
            repo = get_repository(Path(repo_path))
            
            # Check if branch exists
            if branch_name not in [b.name for b in repo.branches]:
                raise GitOperationError(f"Branch '{branch_name}' does not exist")
            
            # Check if it's the current branch
            if repo.active_branch.name == branch_name:
                raise GitOperationError(f"Cannot delete current branch '{branch_name}'")
            
            # Delete branch
            branch = repo.branches[branch_name]
            last_commit = branch.commit.hexsha
            
            repo.delete_head(branch, force=force)
            
            return {
                "name": branch_name,
                "last_commit": last_commit,
                "forced": force,
                "status": "deleted"
            }
            
        except Exception as e:
            raise GitOperationError(f"Failed to delete branch: {e}")
    
    def checkout_branch(self, repo_path: str, branch_name: str) -> Dict[str, Any]:
        """Checkout a branch."""
        try:
            repo = get_repository(Path(repo_path))
            
            # Check for uncommitted changes
            if repo.is_dirty():
                raise GitOperationError("Repository has uncommitted changes")
            
            # Checkout branch
            if branch_name in [b.name for b in repo.branches]:
                # Local branch
                branch = repo.branches[branch_name]
                branch.checkout()
            else:
                # Try remote branch
                remote_branches: list[Any] = []
                for remote in repo.remotes:
                    for ref in remote.refs:
                        if ref.name.endswith(f"/{branch_name}"):
                            remote_branches.append(ref)
                
                if not remote_branches:
                    raise GitOperationError(f"Branch '{branch_name}' not found")
                
                # Create local branch tracking remote
                remote_ref = remote_branches[0]
                local_branch = repo.create_head(branch_name, remote_ref)
                local_branch.set_tracking_branch(remote_ref)
                local_branch.checkout()
            
            return {
                "branch": branch_name,
                "commit_hash": repo.head.commit.hexsha,
                "status": "checked_out"
            }
            
        except Exception as e:
            raise GitOperationError(f"Failed to checkout branch: {e}")
    
    def merge_branch(
        self, 
        repo_path: str, 
        source_branch: str,
        target_branch: Optional[str] = None,
        strategy: str = "merge",
        message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Merge branches."""
        try:
            repo = get_repository(Path(repo_path))
            
            # Get target branch (current if not specified)
            if target_branch:
                if target_branch != repo.active_branch.name:
                    repo.branches[target_branch].checkout()
            else:
                target_branch = repo.active_branch.name
            
            # Get source branch
            if source_branch not in [b.name for b in repo.branches]:
                raise GitOperationError(f"Source branch '{source_branch}' not found")
            
            source_ref = repo.branches[source_branch]
            
            # Perform merge based on strategy
            if strategy == "merge":
                merge_base = repo.merge_base(repo.head.commit, source_ref.commit)[0]
                repo.index.merge_tree(source_ref.commit, base=merge_base)
                
                # Check for conflicts
                if repo.index.unmerged_blobs():
                    return {
                        "status": "conflict",
                        "conflicts": list(repo.index.unmerged_blobs().keys()),
                        "message": "Merge conflicts detected"
                    }
                
                # Create merge commit
                merge_msg = message or f"Merge branch '{source_branch}' into {target_branch}"
                commit = repo.index.commit(
                    merge_msg,
                    parent_commits=(repo.head.commit, source_ref.commit)
                )
                
                return {
                    "status": "merged",
                    "commit_hash": commit.hexsha,
                    "source_branch": source_branch,
                    "target_branch": target_branch,
                    "strategy": strategy,
                    "message": merge_msg
                }
            
            elif strategy == "rebase":
                # Rebase implementation would go here
                raise GitOperationError("Rebase strategy not yet implemented")
            
            elif strategy == "squash":
                # Squash merge implementation would go here
                raise GitOperationError("Squash strategy not yet implemented")
            
            else:
                raise GitOperationError(f"Unknown merge strategy: {strategy}")
                
        except Exception as e:
            raise GitOperationError(f"Failed to merge branches: {e}")

    # Commit Operations

    def create_commit(
        self,
        repo_path: str,
        message: str,
        files: Optional[List[str]] = None,
        all_files: bool = False,
        author_name: Optional[str] = None,
        author_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new commit."""
        try:
            repo = get_repository(Path(repo_path))

            # Stage files
            if all_files:
                repo.git.add(A=True)  # Add all files including untracked
            elif files:
                for file_path in files:
                    repo.index.add([file_path])
            else:
                # Stage all modified files
                repo.git.add(u=True)  # Add modified files only

            # Check if there are changes to commit
            if not repo.index.diff("HEAD"):
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
                "date": commit.committed_datetime,
                "files_changed": len(commit.stats.files),
                "insertions": commit.stats.total["insertions"],
                "deletions": commit.stats.total["deletions"],
                "status": "created"
            }

        except Exception as e:
            raise GitOperationError(f"Failed to create commit: {e}")

    def amend_commit(
        self,
        repo_path: str,
        message: Optional[str] = None,
        files: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Amend the last commit."""
        try:
            repo = get_repository(Path(repo_path))

            # Stage additional files if provided
            if files:
                for file_path in files:
                    repo.index.add([file_path])

            # Get current commit
            current_commit = repo.head.commit

            # Amend commit
            if message:
                amended_commit = repo.index.commit(
                    message,
                    amend=True
                )
            else:
                amended_commit = repo.index.commit(
                    current_commit.message,
                    amend=True
                )

            return {
                "old_commit_hash": current_commit.hexsha,
                "new_commit_hash": amended_commit.hexsha,
                "message": amended_commit.message.strip(),
                "author": f"{amended_commit.author.name} <{amended_commit.author.email}>",
                "date": amended_commit.committed_datetime,
                "status": "amended"
            }

        except Exception as e:
            raise GitOperationError(f"Failed to amend commit: {e}")

    def revert_commit(
        self,
        repo_path: str,
        commit_hash: str,
        no_commit: bool = False
    ) -> Dict[str, Any]:
        """Revert a commit."""
        try:
            repo = get_repository(Path(repo_path))

            # Get commit to revert
            commit_to_revert = repo.commit(commit_hash)

            # Create revert commit message
            revert_message = f"Revert \"{commit_to_revert.message.strip()}\"\n\nThis reverts commit {commit_hash}."

            # Perform revert
            repo.git.revert(commit_hash, no_commit=no_commit)

            if not no_commit:
                # Commit was created automatically
                revert_commit = repo.head.commit
                return {
                    "reverted_commit": commit_hash,
                    "revert_commit": revert_commit.hexsha,
                    "message": revert_message,
                    "status": "reverted"
                }
            else:
                # Changes staged but not committed
                return {
                    "reverted_commit": commit_hash,
                    "message": "Revert changes staged but not committed",
                    "status": "staged"
                }

        except Exception as e:
            raise GitOperationError(f"Failed to revert commit: {e}")

    def cherry_pick_commit(
        self,
        repo_path: str,
        commit_hash: str,
        no_commit: bool = False
    ) -> Dict[str, Any]:
        """Cherry-pick a commit."""
        try:
            repo = get_repository(Path(repo_path))

            # Get commit to cherry-pick
            commit_to_pick = repo.commit(commit_hash)

            # Perform cherry-pick
            repo.git.cherry_pick(commit_hash, no_commit=no_commit)

            if not no_commit:
                # Commit was created automatically
                cherry_pick_commit = repo.head.commit
                return {
                    "original_commit": commit_hash,
                    "cherry_pick_commit": cherry_pick_commit.hexsha,
                    "message": commit_to_pick.message.strip(),
                    "author": f"{commit_to_pick.author.name} <{commit_to_pick.author.email}>",
                    "status": "cherry_picked"
                }
            else:
                # Changes staged but not committed
                return {
                    "original_commit": commit_hash,
                    "message": "Cherry-pick changes staged but not committed",
                    "status": "staged"
                }

        except Exception as e:
            raise GitOperationError(f"Failed to cherry-pick commit: {e}")

    # Tag Operations

    def list_tags(self, repo_path: str) -> List[Dict[str, Any]]:
        """List all tags in the repository."""
        try:
            repo = get_repository(Path(repo_path))
            tags: list[Any] = []

            for tag in repo.tags:
                tag_info = {
                    "name": tag.name,
                    "commit_hash": tag.commit.hexsha,
                    "is_annotated": hasattr(tag.tag, 'message'),
                    "message": getattr(tag.tag, 'message', None) if hasattr(tag.tag, 'message') else None,
                    "tagger": f"{tag.tag.tagger.name} <{tag.tag.tagger.email}>" if hasattr(tag.tag, 'tagger') else None,
                    "date": getattr(tag.tag, 'tagged_date', None)
                }
                tags.append(tag_info)

            return sorted(tags, key=lambda x: x['name'])

        except Exception as e:
            raise GitOperationError(f"Failed to list tags: {e}")

    def create_tag(
        self,
        repo_path: str,
        tag_name: str,
        commit: Optional[str] = None,
        message: Optional[str] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """Create a new tag."""
        try:
            repo = get_repository(Path(repo_path))

            # Check if tag already exists
            if tag_name in [t.name for t in repo.tags] and not force:
                raise GitOperationError(f"Tag '{tag_name}' already exists")

            # Get commit to tag
            if commit:
                target_commit = repo.commit(commit)
            else:
                target_commit = repo.head.commit

            # Create tag
            if message:
                # Annotated tag
                tag = repo.create_tag(tag_name, ref=target_commit, message=message, force=force)
                return {
                    "name": tag_name,
                    "commit_hash": target_commit.hexsha,
                    "message": message,
                    "is_annotated": True,
                    "status": "created"
                }
            else:
                # Lightweight tag
                tag = repo.create_tag(tag_name, ref=target_commit, force=force)
                return {
                    "name": tag_name,
                    "commit_hash": target_commit.hexsha,
                    "is_annotated": False,
                    "status": "created"
                }

        except Exception as e:
            raise GitOperationError(f"Failed to create tag: {e}")

    def delete_tag(self, repo_path: str, tag_name: str) -> Dict[str, Any]:
        """Delete a tag."""
        try:
            repo = get_repository(Path(repo_path))

            # Check if tag exists
            if tag_name not in [t.name for t in repo.tags]:
                raise GitOperationError(f"Tag '{tag_name}' does not exist")

            # Get tag info before deletion
            tag = repo.tags[tag_name]
            commit_hash = tag.commit.hexsha

            # Delete tag
            repo.delete_tag(tag)

            return {
                "name": tag_name,
                "commit_hash": commit_hash,
                "status": "deleted"
            }

        except Exception as e:
            raise GitOperationError(f"Failed to delete tag: {e}")

    # Remote Operations

    def list_remotes(self, repo_path: str) -> List[Dict[str, Any]]:
        """List all remotes in the repository."""
        try:
            repo = get_repository(Path(repo_path))
            remotes: list[Any] = []

            for remote in repo.remotes:
                remote_info = {
                    "name": remote.name,
                    "url": list(remote.urls)[0] if remote.urls else None,
                    "fetch_url": remote.url,
                    "push_url": remote.pushurl or remote.url,
                    "refs": [ref.name for ref in remote.refs]
                }
                remotes.append(remote_info)

            return remotes

        except Exception as e:
            raise GitOperationError(f"Failed to list remotes: {e}")

    def add_remote(self, repo_path: str, name: str, url: str) -> Dict[str, Any]:
        """Add a new remote."""
        try:
            repo = get_repository(Path(repo_path))

            # Check if remote already exists
            if name in [r.name for r in repo.remotes]:
                raise GitOperationError(f"Remote '{name}' already exists")

            # Add remote
            remote = repo.create_remote(name, url)

            return {
                "name": name,
                "url": url,
                "status": "added"
            }

        except Exception as e:
            raise GitOperationError(f"Failed to add remote: {e}")

    def remove_remote(self, repo_path: str, name: str) -> Dict[str, Any]:
        """Remove a remote."""
        try:
            repo = get_repository(Path(repo_path))

            # Check if remote exists
            if name not in [r.name for r in repo.remotes]:
                raise GitOperationError(f"Remote '{name}' does not exist")

            # Get remote info before deletion
            remote = repo.remotes[name]
            url = remote.url

            # Remove remote
            repo.delete_remote(remote)

            return {
                "name": name,
                "url": url,
                "status": "removed"
            }

        except Exception as e:
            raise GitOperationError(f"Failed to remove remote: {e}")

    def fetch_remote(
        self,
        repo_path: str,
        remote_name: str = "origin",
        prune: bool = False
    ) -> Dict[str, Any]:
        """Fetch from a remote repository."""
        try:
            repo = get_repository(Path(repo_path))

            # Check if remote exists
            if remote_name not in [r.name for r in repo.remotes]:
                raise GitOperationError(f"Remote '{remote_name}' does not exist")

            remote = repo.remotes[remote_name]

            # Fetch from remote
            fetch_info = remote.fetch(prune=prune)

            # Process fetch results
            fetched_refs: list[Any] = []
            for info in fetch_info:
                fetched_refs.append({
                    "ref": info.ref.name,
                    "old_commit": info.old_commit.hexsha if info.old_commit else None,
                    "new_commit": info.commit.hexsha,
                    "flags": str(info.flags)
                })

            return {
                "remote": remote_name,
                "fetched_refs": fetched_refs,
                "pruned": prune,
                "status": "fetched"
            }

        except Exception as e:
            raise GitOperationError(f"Failed to fetch from remote: {e}")

    def push_to_remote(
        self,
        repo_path: str,
        remote_name: str = "origin",
        branch: Optional[str] = None,
        force: bool = False,
        set_upstream: bool = False
    ) -> Dict[str, Any]:
        """Push to a remote repository."""
        try:
            repo = get_repository(Path(repo_path))

            # Check if remote exists
            if remote_name not in [r.name for r in repo.remotes]:
                raise GitOperationError(f"Remote '{remote_name}' does not exist")

            remote = repo.remotes[remote_name]

            # Determine branch to push
            if not branch:
                branch = repo.active_branch.name

            # Push to remote
            push_info = remote.push(
                refspec=f"{branch}:{branch}",
                force=force,
                set_upstream=set_upstream
            )

            # Process push results
            push_results: list[Any] = []
            for info in push_info:
                push_results.append({
                    "local_ref": info.local_ref.name if info.local_ref else None,
                    "remote_ref": info.remote_ref.name if info.remote_ref else None,
                    "old_commit": info.old_commit.hexsha if info.old_commit else None,
                    "new_commit": info.local_ref.commit.hexsha if info.local_ref else None,
                    "flags": str(info.flags),
                    "summary": info.summary
                })

            return {
                "remote": remote_name,
                "branch": branch,
                "push_results": push_results,
                "forced": force,
                "set_upstream": set_upstream,
                "status": "pushed"
            }

        except Exception as e:
            raise GitOperationError(f"Failed to push to remote: {e}")

    def pull_from_remote(
        self,
        repo_path: str,
        remote_name: str = "origin",
        branch: Optional[str] = None
    ) -> Dict[str, Any]:
        """Pull from a remote repository."""
        try:
            repo = get_repository(Path(repo_path))

            # Check if remote exists
            if remote_name not in [r.name for r in repo.remotes]:
                raise GitOperationError(f"Remote '{remote_name}' does not exist")

            remote = repo.remotes[remote_name]

            # Determine branch to pull
            if not branch:
                branch = repo.active_branch.name

            # Get current commit before pull
            old_commit = repo.head.commit.hexsha

            # Pull from remote (fetch + merge)
            pull_info = remote.pull(branch)

            # Get new commit after pull
            new_commit = repo.head.commit.hexsha

            # Process pull results
            pull_results: list[Any] = []
            for info in pull_info:
                pull_results.append({
                    "ref": info.ref.name,
                    "old_commit": info.old_commit.hexsha if info.old_commit else None,
                    "new_commit": info.commit.hexsha,
                    "flags": str(info.flags)
                })

            return {
                "remote": remote_name,
                "branch": branch,
                "old_commit": old_commit,
                "new_commit": new_commit,
                "pull_results": pull_results,
                "fast_forward": old_commit != new_commit,
                "status": "pulled"
            }

        except Exception as e:
            raise GitOperationError(f"Failed to pull from remote: {e}")

    # Utility Methods

    def get_merge_conflicts(self, repo_path: str) -> Dict[str, Any]:
        """Get information about merge conflicts."""
        try:
            repo = get_repository(Path(repo_path))

            # Check if there are unmerged blobs (conflicts)
            unmerged_blobs = repo.index.unmerged_blobs()

            if not unmerged_blobs:
                return {
                    "has_conflicts": False,
                    "conflicts": [],
                    "status": "no_conflicts"
                }

            conflicts: list[Any] = []
            for file_path, blob_info in unmerged_blobs.items():
                conflict_info: dict[str, Any] = {
                    "file_path": file_path,
                    "stages": {}
                }

                for stage, blob in blob_info:
                    conflict_info["stages"][stage] = {
                        "blob_hash": blob.hexsha,
                        "size": blob.size
                    }

                conflicts.append(conflict_info)

            return {
                "has_conflicts": True,
                "conflicts": conflicts,
                "conflict_count": len(conflicts),
                "status": "conflicts_detected"
            }

        except Exception as e:
            raise GitOperationError(f"Failed to get merge conflicts: {e}")

    def resolve_conflict(
        self,
        repo_path: str,
        file_path: str,
        resolution: str = "ours"
    ) -> Dict[str, Any]:
        """Resolve a merge conflict for a specific file."""
        try:
            repo = get_repository(Path(repo_path))

            # Check if file has conflicts
            unmerged_blobs = repo.index.unmerged_blobs()
            if file_path not in unmerged_blobs:
                raise GitOperationError(f"No conflicts found for file: {file_path}")

            # Resolve conflict based on strategy
            if resolution == "ours":
                repo.git.checkout("--ours", file_path)
            elif resolution == "theirs":
                repo.git.checkout("--theirs", file_path)
            else:
                raise GitOperationError(f"Unknown resolution strategy: {resolution}")

            # Stage the resolved file
            repo.index.add([file_path])

            return {
                "file_path": file_path,
                "resolution": resolution,
                "status": "resolved"
            }

        except Exception as e:
            raise GitOperationError(f"Failed to resolve conflict: {e}")
