"""Handles Git repository operations using GitPython."""

import fnmatch
from collections.abc import Generator
from datetime import datetime
from pathlib import Path
from typing import Any

import git
from git import Commit, GitCommandError, Repo

# [attr-defined]
from githound.models import CommitInfo, GitHoundConfig, SearchConfig, SearchResult
from githound.searcher import search_blob_content


def get_repository(path: Path) -> Repo:
    """
    Gets a git.Repo object for the given path.

    Args:
        path: The path to the Git repository.

    Returns:
        A git.Repo object.

    Raises:
        GitCommandError: If the path is not a valid Git repository.
    """
    try:
        return Repo(path)
    except git.InvalidGitRepositoryError as e:
        raise GitCommandError(f"Invalid Git repository at '{path}': {e}")


def walk_history(repo: Repo, config: GitHoundConfig) -> Generator[Commit, None, None]:
    """
    Walks the Git history of the given branch.

    Args:
        repo: The repository to search.
        config: The search configuration.

    Yields:
        Commit objects from the history.
    """
    branch = config.branch or repo.active_branch.name  # [attr-defined]
    try:
        for commit in repo.iter_commits(branch):
            yield commit
    except GitCommandError:
        raise GitCommandError(f"Branch '{branch}' not found.")


def process_commit(commit: Commit, config: GitHoundConfig) -> list[SearchResult]:
    """
    Processes a single commit, searching for the query in its blobs.

    Args:
        commit: The commit to process.
        config: The search configuration.

    Returns:
        A list of search results found in the commit.
    """
    results: list[SearchResult] = []
    if not commit.parents:
        return results

    for parent in commit.parents:
        diffs = commit.diff(parent)
        for diff in diffs:
            if diff.b_blob is None or diff.b_path is None:
                continue

            file_path = diff.b_path
            if (
                config.search_config  # [attr-defined]
                and config.search_config.include_globs  # [attr-defined]
                and not any(
                    fnmatch.fnmatch(file_path, pattern)
                    # [attr-defined]
                    for pattern in config.search_config.include_globs
                )
            ):
                continue

            if (
                config.search_config  # [attr-defined]
                and config.search_config.exclude_globs  # [attr-defined]
                and any(
                    fnmatch.fnmatch(file_path, pattern)
                    # [attr-defined]
                    for pattern in config.search_config.exclude_globs
                )
            ):
                continue

            try:
                content = diff.b_blob.data_stream.read()
                # Convert search_query to string if it's a SearchQuery object
                query_str = (
                    config.search_query  # [attr-defined]
                    if isinstance(config.search_query, str)  # [attr-defined]
                    # [attr-defined]
                    else config.search_query.content_pattern or ""
                )
                search_config = config.search_config or SearchConfig(  # [attr-defined]
                    include_globs=[],
                    exclude_globs=[],
                    case_sensitive=False,
                    max_results=None,
                    timeout_seconds=None,
                    enable_caching=True,
                    cache_ttl_seconds=3600,
                    enable_progress=True,
                    progress_callback=None,
                )

                results.extend(
                    search_blob_content(
                        content,
                        query_str,
                        search_config,
                        commit.hexsha,
                        file_path,
                    )
                )
            except (UnicodeDecodeError, AttributeError):
                continue
    return results


# Enhanced Git Information Retrieval Functions


def extract_commit_metadata(commit: Commit) -> CommitInfo:
    """
    Extract comprehensive metadata from a Git commit.

    Args:
        commit: The Git commit object.

    Returns:
        CommitInfo object with detailed commit metadata.
    """
    # Calculate file change statistics
    files_changed = 0
    insertions = 0
    deletions = 0

    try:
        # Get stats from commit
        stats = commit.stats
        files_changed = stats.total.get("files", 0)
        insertions = stats.total.get("insertions", 0)
        deletions = stats.total.get("deletions", 0)
    except (AttributeError, KeyError):
        # Fallback: count from diffs if stats not available
        if commit.parents:
            for parent in commit.parents:
                diffs = commit.diff(parent)
                files_changed += len(diffs)
                for diff in diffs:
                    if hasattr(diff, "a_blob") and hasattr(diff, "b_blob"):
                        # Rough estimation based on diff
                        if diff.a_blob is None:  # New file
                            insertions += 1
                        elif diff.b_blob is None:  # Deleted file
                            deletions += 1

    return CommitInfo(
        hash=commit.hexsha,
        short_hash=commit.hexsha[:8],
        author_name=commit.author.name or "Unknown",
        author_email=commit.author.email or "unknown@example.com",
        committer_name=commit.committer.name or "Unknown",
        committer_email=commit.committer.email or "unknown@example.com",
        message=str(commit.message).strip() if commit.message else "",
        date=datetime.fromtimestamp(commit.committed_date),
        files_changed=files_changed,
        insertions=insertions,
        deletions=deletions,
        parents=[parent.hexsha for parent in commit.parents],
    )


def get_repository_metadata(repo: Repo) -> dict[str, Any]:
    """
    Extract comprehensive repository metadata.

    Args:
        repo: The Git repository object.

    Returns:
        Dictionary containing repository metadata.
    """
    metadata: dict[str, Any] = {
        "repo_path": str(repo.working_dir),
        "is_bare": repo.bare,
        "head_commit": repo.head.commit.hexsha if repo.head.is_valid() else None,
        "active_branch": repo.active_branch.name if not repo.head.is_detached else None,
        "branches": [],
        "remotes": [],
        "tags": [],
        "total_commits": 0,
        "contributors": set(),
        "first_commit_date": None,
        "last_commit_date": None,
    }

    # Get branch information
    for branch in repo.branches:
        metadata["branches"].append(
            {"name": branch.name, "commit": branch.commit.hexsha, "is_remote": False}
        )

    # Get remote branch information
    for remote in repo.remotes:
        metadata["remotes"].append(
            {"name": remote.name, "url": list(
                remote.urls)[0] if remote.urls else None}
        )

        for ref in remote.refs:
            if ref.name.startswith(f"{remote.name}/"):
                branch_name = ref.name[len(remote.name) + 1:]
                metadata["branches"].append(
                    {
                        "name": branch_name,
                        "commit": ref.commit.hexsha,
                        "is_remote": True,
                        "remote": remote.name,
                    }
                )

    # Get tag information
    for tag in repo.tags:
        metadata["tags"].append(
            {
                "name": tag.name,
                "commit": tag.commit.hexsha,
                "message": tag.tag.message if tag.tag else None,
            }
        )

    # Get commit statistics
    try:
        commits = list(repo.iter_commits())
        metadata["total_commits"] = len(commits)

        if commits:
            # Get contributors
            for commit in commits:
                metadata["contributors"].add(
                    f"{commit.author.name} <{commit.author.email}>")

            # Get date range
            metadata["first_commit_date"] = datetime.fromtimestamp(
                commits[-1].committed_date)
            metadata["last_commit_date"] = datetime.fromtimestamp(
                commits[0].committed_date)

        metadata["contributors"] = list(metadata["contributors"])

    except Exception as e:
        # If we can't get commit stats, continue with what we have
        metadata["error"] = f"Could not retrieve commit statistics: {str(e)}"

    return metadata


def get_commits_with_filters(
    repo: Repo,
    branch: str | None = None,
    author_pattern: str | None = None,
    message_pattern: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    file_patterns: list[str] | None = None,
    max_count: int | None = None,
) -> Generator[Commit, None, None]:
    """
    Get commits with advanced filtering options.

    Args:
        repo: The Git repository object.
        branch: Branch to search (defaults to current branch).
        author_pattern: Filter by author name/email pattern.
        message_pattern: Filter by commit message pattern.
        date_from: Filter commits from this date.
        date_to: Filter commits until this date.
        file_patterns: Filter commits that affect these file patterns.
        max_count: Maximum number of commits to return.

    Yields:
        Filtered commit objects.
    """
    # Build iter_commits arguments
    kwargs: dict[str, Any] = {}

    if branch:
        kwargs["rev"] = branch

    if date_from or date_to:
        if date_from and date_to:
            kwargs["since"] = date_from.isoformat()
            kwargs["until"] = date_to.isoformat()
        elif date_from:
            kwargs["since"] = date_from.isoformat()
        elif date_to:
            kwargs["until"] = date_to.isoformat()

    if max_count:
        kwargs["max_count"] = max_count

    if file_patterns:
        kwargs["paths"] = file_patterns

    try:
        for commit in repo.iter_commits(**kwargs):
            # Apply additional filters that can't be handled by iter_commits
            if author_pattern:
                author_text = f"{commit.author.name} {commit.author.email}".lower()
                if author_pattern.lower() not in author_text:
                    continue

            if message_pattern:
                commit_message = commit.message
                if isinstance(commit_message, (bytes, bytearray, memoryview)):
                    commit_message = bytes(commit_message).decode(
                        "utf-8", errors="ignore")

                if (
                    not isinstance(commit_message, str)
                    or message_pattern.lower() not in commit_message.lower()
                ):
                    continue

            yield commit

    except GitCommandError as e:
        raise GitCommandError(f"Error filtering commits: {e}")


def get_file_history(
    repo: Repo, file_path: str, branch: str | None = None, max_count: int | None = None
) -> list[dict[str, Any]]:
    """
    Get the complete history of a specific file.

    Args:
        repo: The Git repository object.
        file_path: Path to the file.
        branch: Branch to search (defaults to current branch).
        max_count: Maximum number of commits to return.

    Returns:
        List of dictionaries containing file history information.
    """
    history: list[Any] = []

    try:
        kwargs: dict[str, Any] = {"paths": [file_path]}
        if branch:
            kwargs["rev"] = branch
        if max_count:
            kwargs["max_count"] = max_count

        for commit in repo.iter_commits(**kwargs):
            # Get the file content at this commit
            try:
                file_content: str | None = None
                file_size = 0

                # Try to get the file from this commit
                try:
                    blob = commit.tree / file_path
                    file_size = blob.size
                    # Only read content for text files (reasonable size)
                    if file_size < 1024 * 1024:  # 1MB limit
                        file_content = blob.data_stream.read().decode("utf-8", errors="ignore")
                except (KeyError, UnicodeDecodeError):
                    # File doesn't exist in this commit or is binary
                    pass

                history.append(
                    {
                        "commit_hash": commit.hexsha,
                        "commit_date": datetime.fromtimestamp if datetime is not None else None(commit.committed_date),
                        "author": f"{commit.author.name} <{commit.author.email}>",
                        "message": commit.message.strip(),
                        "file_size": file_size,
                        "file_content": file_content,
                    }
                )

            except Exception:
                # Skip this commit if we can't process it
                continue

    except GitCommandError as e:
        raise GitCommandError(
            f"Error getting file history for '{file_path}': {e}")

    return history
