"""Blame and diff analysis MCP tools for GitHound."""

from datetime import datetime
from pathlib import Path
from typing import Any

from fastmcp import Context
from git import GitCommandError

from ...git_blame import get_author_statistics
from ...git_blame import get_file_blame as get_file_blame_impl
from ...git_diff import compare_branches, compare_commits
from ...git_handler import get_repository
from ..models import (
    AuthorStatsInput,
    BlameInput,
    BranchDiffInput,
    CommitComparisonInput,
    DiffInput,
    FileBlameInput,
)


async def analyze_file_blame(input_data: BlameInput, ctx: Context) -> dict[str, Any]:
    """
    Analyze line-by-line authorship for a file using git blame.

    Returns detailed blame information showing who last modified each line,
    when it was changed, and the commit message for each change.
    """
    try:
        await ctx.info(f"Analyzing blame for file {input_data.file_path}")

        repo = get_repository(Path(input_data.repo_path))

        blame_result = get_file_blame_impl(
            repo=repo, file_path=input_data.file_path, commit=input_data.commit
        )

        await ctx.info(
            f"Blame analysis complete: {blame_result.total_lines} lines, {len(blame_result.contributors)} contributors"
        )

        return {
            "status": "success",
            "file_blame": blame_result.dict(),
            "analysis_timestamp": datetime.now().isoformat(),
        }

    except GitCommandError as e:
        await ctx.error(f"Git error during blame analysis: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error during blame analysis: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}


async def compare_commits_diff(input_data: DiffInput, ctx: Context) -> dict[str, Any]:
    """
    Compare two commits and return detailed diff analysis.

    Returns comprehensive diff information including file changes,
    line-by-line differences, and change statistics.
    """
    try:
        await ctx.info(f"Comparing commits {input_data.from_commit} and {input_data.to_commit}")

        repo = get_repository(Path(input_data.repo_path))

        diff_result = compare_commits(
            repo=repo,
            from_commit=input_data.from_commit,
            to_commit=input_data.to_commit,
            file_patterns=input_data.file_patterns,
        )

        await ctx.info(
            f"Diff analysis complete: {diff_result.files_changed} files changed, +{diff_result.total_additions}/-{diff_result.total_deletions}"
        )

        return {
            "status": "success",
            "commit_diff": diff_result.dict(),
            "analysis_timestamp": datetime.now().isoformat(),
        }

    except GitCommandError as e:
        await ctx.error(f"Git error during commit comparison: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error during commit comparison: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}


async def compare_branches_diff(input_data: BranchDiffInput, ctx: Context) -> dict[str, Any]:
    """
    Compare two branches and return detailed diff analysis.

    Returns comprehensive diff information showing all changes
    between the specified branches.
    """
    try:
        await ctx.info(f"Comparing branches {input_data.from_branch} and {input_data.to_branch}")

        repo = get_repository(Path(input_data.repo_path))

        diff_result = compare_branches(
            repo=repo,
            from_branch=input_data.from_branch,
            to_branch=input_data.to_branch,
            file_patterns=input_data.file_patterns,
        )

        await ctx.info(f"Branch diff analysis complete: {diff_result.files_changed} files changed")

        return {
            "status": "success",
            "branch_diff": diff_result.dict(),
            "analysis_timestamp": datetime.now().isoformat(),
        }

    except GitCommandError as e:
        await ctx.error(f"Git error during branch comparison: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error during branch comparison: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}


async def get_author_stats(input_data: AuthorStatsInput, ctx: Context) -> dict[str, Any]:
    """
    Get comprehensive author statistics for the repository.

    Returns detailed statistics about each contributor including
    commit counts, lines authored, and activity timeline.
    """
    try:
        await ctx.info(f"Generating author statistics for {input_data.repo_path}")

        repo = get_repository(Path(input_data.repo_path))

        author_stats = get_author_statistics(repo, branch=input_data.branch)

        await ctx.info(f"Author statistics complete: {len(author_stats)} contributors analyzed")

        return {
            "status": "success",
            "author_statistics": author_stats,
            "total_authors": len(author_stats),
            "analysis_timestamp": datetime.now().isoformat(),
        }

    except GitCommandError as e:
        await ctx.error(f"Git error during author statistics: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error during author statistics: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}


async def get_file_blame(input_data: FileBlameInput, ctx: Context) -> dict[str, Any]:
    """
    Get file blame information showing line-by-line authorship.

    Returns detailed blame information for the specified file.
    """
    try:
        await ctx.info(f"Getting blame information for {input_data.file_path}")

        repo = get_repository(Path(input_data.repo_path))
        blame_result = get_file_blame_impl(repo, input_data.file_path)

        # Convert FileBlameResult to dictionary
        blame_info = {
            "file_path": blame_result.file_path,
            "total_lines": blame_result.total_lines,
            "contributors": blame_result.contributors,
            "oldest_line_date": (
                blame_result.oldest_line_date.isoformat() if blame_result.oldest_line_date else None
            ),
            "newest_line_date": (
                blame_result.newest_line_date.isoformat() if blame_result.newest_line_date else None
            ),
            "line_blame": [
                {
                    "line_number": line.line_number,
                    "content": line.content,
                    "author_name": line.author_name,
                    "author_email": line.author_email,
                    "commit_hash": line.commit_hash,
                    "commit_date": line.commit_date.isoformat() if line.commit_date else None,
                    "commit_message": line.commit_message,
                }
                for line in blame_result.blame_info
            ],
        }

        await ctx.info(f"Blame analysis complete for {input_data.file_path}")

        return {
            "status": "success",
            "blame_info": blame_info,
            "analysis_timestamp": datetime.now().isoformat(),
        }

    except GitCommandError as e:
        await ctx.error(f"Git error during blame analysis: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error during blame analysis: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}


async def compare_commits_mcp(input_data: CommitComparisonInput, ctx: Context) -> dict[str, Any]:
    """
    Compare two commits and return detailed diff information.

    Returns comprehensive comparison between two commits.
    """
    try:
        await ctx.info(f"Comparing commits {input_data.from_commit} and {input_data.to_commit}")

        repo = get_repository(Path(input_data.repo_path))
        diff_result = compare_commits(repo, input_data.from_commit, input_data.to_commit)

        await ctx.info("Commit comparison complete")

        return {
            "status": "success",
            "comparison_result": diff_result,
            "comparison_timestamp": datetime.now().isoformat(),
        }

    except GitCommandError as e:
        await ctx.error(f"Git error during commit comparison: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error during commit comparison: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}
