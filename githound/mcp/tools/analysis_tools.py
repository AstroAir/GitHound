"""Repository and commit analysis MCP tools for GitHound."""

from datetime import datetime
from pathlib import Path
from typing import Any

from fastmcp import Context
from git import GitCommandError

from ...git_handler import (
    extract_commit_metadata,
    get_commits_with_filters,
    get_file_history,
    get_repository,
    get_repository_metadata,
)
from ..models import (
    CommitAnalysisInput,
    CommitFilterInput,
    CommitHistoryInput,
    FileHistoryInput,
    RepositoryInput,
)


async def analyze_repository(input_data: RepositoryInput, ctx: Context) -> dict[str, Any]:
    """
    Analyze a Git repository and return comprehensive metadata.

    Returns repository information including branches, tags, remotes,
    contributor statistics, and overall repository health metrics.
    """
    try:
        await ctx.info(f"Analyzing repository at {input_data.repo_path}")

        repo = get_repository(Path(input_data.repo_path))
        metadata = get_repository_metadata(repo)

        await ctx.info(
            f"Repository analysis complete: {metadata['total_commits']} commits, {len(metadata['contributors'])} contributors"
        )

        return {
            "status": "success",
            "repository_metadata": metadata,
            "analysis_timestamp": datetime.now().isoformat(),
        }

    except GitCommandError as e:
        await ctx.error(f"Git error during repository analysis: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error during repository analysis: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}


async def analyze_commit(input_data: CommitAnalysisInput, ctx: Context) -> dict[str, Any]:
    """
    Analyze a specific commit and return detailed metadata.

    Returns comprehensive information about the commit including
    author details, file changes, statistics, and parent relationships.
    """
    try:
        await ctx.info(f"Analyzing commit in repository {input_data.repo_path}")

        repo = get_repository(Path(input_data.repo_path))

        if input_data.commit_hash:
            commit = repo.commit(input_data.commit_hash)
        else:
            commit = repo.head.commit

        commit_info = extract_commit_metadata(commit)

        await ctx.info(
            f"Commit analysis complete: {commit_info.hash[:8]} by {commit_info.author_name}"
        )

        return {
            "status": "success",
            "commit_metadata": commit_info.dict(),
            "analysis_timestamp": datetime.now().isoformat(),
        }

    except GitCommandError as e:
        await ctx.error(f"Git error during commit analysis: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error during commit analysis: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}


async def get_filtered_commits(input_data: CommitFilterInput, ctx: Context) -> dict[str, Any]:
    """
    Retrieve commits with advanced filtering options.

    Supports filtering by author, message content, date range, and file patterns.
    Returns a list of commits matching the specified criteria.
    """
    try:
        await ctx.info(f"Retrieving filtered commits from {input_data.repo_path}")

        repo = get_repository(Path(input_data.repo_path))

        # Parse date strings if provided
        date_from = None
        date_to = None
        if input_data.date_from:
            date_from = datetime.fromisoformat(
                input_data.date_from.replace("Z", "+00:00"))
        if input_data.date_to:
            date_to = datetime.fromisoformat(
                input_data.date_to.replace("Z", "+00:00"))

        commits = get_commits_with_filters(
            repo=repo,
            branch=input_data.branch,
            author_pattern=input_data.author_pattern,
            message_pattern=input_data.message_pattern,
            date_from=date_from,
            date_to=date_to,
            file_patterns=input_data.file_patterns,
            max_count=input_data.max_count,
        )

        commit_list: list[Any] = []
        for commit in commits:
            commit_info = extract_commit_metadata(commit)
            commit_list.append(commit_info.dict()
                               if commit_info is not None else {})

        await ctx.info(f"Retrieved {len(commit_list)} commits matching filter criteria")

        return {
            "status": "success",
            "commits": commit_list,
            "filter_criteria": input_data.dict(),
            "total_results": len(commit_list),
            "analysis_timestamp": datetime.now().isoformat(),
        }

    except GitCommandError as e:
        await ctx.error(f"Git error during commit filtering: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error during commit filtering: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}


async def get_file_history_mcp(input_data: FileHistoryInput, ctx: Context) -> dict[str, Any]:
    """
    Get the complete history of changes for a specific file.

    Returns chronological list of commits that modified the file,
    including content changes and metadata for each revision.
    """
    try:
        await ctx.info(f"Retrieving history for file {input_data.file_path}")

        repo = get_repository(Path(input_data.repo_path))

        history = get_file_history(
            repo=repo,
            file_path=input_data.file_path,
            branch=input_data.branch,
            max_count=input_data.max_count,
        )

        await ctx.info(f"Retrieved {len(history)} commits in file history")

        return {
            "status": "success",
            "file_path": input_data.file_path,
            "history": history,
            "total_commits": len(history),
            "analysis_timestamp": datetime.now().isoformat(),
        }

    except GitCommandError as e:
        await ctx.error(f"Git error during file history retrieval: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error during file history retrieval: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}


async def get_commit_history(input_data: CommitHistoryInput, ctx: Context) -> dict[str, Any]:
    """
    Get commit history with optional filtering and pagination.

    Returns a list of commits with metadata, supporting various filtering options.
    """
    try:
        await ctx.info(f"Retrieving commit history from {input_data.repo_path}")

        repo = get_repository(Path(input_data.repo_path))
        commit_objects = list(get_commits_with_filters(
            repo,
            max_count=input_data.max_count,
            author_pattern=getattr(input_data, 'author', None),
            branch=getattr(input_data, 'branch', None)
        ))

        # Convert commit objects to dictionaries
        commits: list[Any] = []
        for commit in commit_objects:
            commit_dict = {
                "hash": commit.hexsha,
                "short_hash": commit.hexsha[:8],
                "author_name": commit.author.name,
                "author_email": commit.author.email,
                "message": commit.message.strip(),
                "date": commit.committed_datetime.isoformat(),
                "files_changed": len(commit.stats.files) if commit.stats else 0,
            }
            commits.append(commit_dict)

        await ctx.info(f"Retrieved {len(commits)} commits")

        return {
            "status": "success",
            "commits": commits,
            "total_count": len(commits),
            "retrieval_timestamp": datetime.now().isoformat(),
        }

    except GitCommandError as e:
        await ctx.error(f"Git error during commit history retrieval: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error during commit history retrieval: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}
