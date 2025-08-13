"""Handles Git repository operations using GitPython."""

import fnmatch
from pathlib import Path
from typing import Generator, List

import git
from git import Repo, Commit, GitCommandError

from githound.models import GitHoundConfig, SearchResult
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
    branch = config.branch or repo.active_branch.name
    try:
        for commit in repo.iter_commits(branch):
            yield commit
    except GitCommandError:
        raise GitCommandError(f"Branch '{branch}' not found.")


def process_commit(commit: Commit, config: GitHoundConfig) -> List[SearchResult]:
    """
    Processes a single commit, searching for the query in its blobs.

    Args:
        commit: The commit to process.
        config: The search configuration.

    Returns:
        A list of search results found in the commit.
    """
    results: List[SearchResult] = []
    if not commit.parents:
        return results

    for parent in commit.parents:
        diffs = commit.diff(parent)
        for diff in diffs:
            if diff.b_blob is None or diff.b_path is None:
                continue

            file_path = diff.b_path
            if config.search_config.include_globs and not any(
                fnmatch.fnmatch(file_path, pattern)
                for pattern in config.search_config.include_globs
            ):
                continue

            if config.search_config.exclude_globs and any(
                fnmatch.fnmatch(file_path, pattern)
                for pattern in config.search_config.exclude_globs
            ):
                continue

            try:
                content = diff.b_blob.data_stream.read()
                results.extend(
                    search_blob_content(
                        content,
                        config.search_query,
                        config.search_config,
                        commit.hexsha,
                        file_path,
                    )
                )
            except (UnicodeDecodeError, AttributeError):
                continue
    return results
