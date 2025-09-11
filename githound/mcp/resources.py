"""MCP resources for GitHound repository data access."""

from datetime import datetime
from pathlib import Path
from typing import Any

from fastmcp import Context

from ..git_blame import get_author_statistics, get_file_blame as get_file_blame_impl
from ..git_handler import (
    extract_commit_metadata,
    get_file_history,
    get_repository,
    get_repository_metadata,
)


async def get_repository_config(repo_path: str, ctx: Context) -> str:
    """
    Get repository configuration information.

    Returns Git configuration settings, remote URLs, and repository metadata
    in a structured format for easy consumption by AI models.
    """
    try:
        await ctx.info(f"Retrieving configuration for repository {repo_path}")  # [attr-defined]

        repo = get_repository(Path(repo_path))
        metadata = get_repository_metadata(repo)

        config_info = {
            "repository_path": repo_path,
            "is_bare": metadata.get("is_bare", False),
            "active_branch": metadata.get("active_branch"),
            "total_branches": len(metadata.get("branches", [])),
            "total_tags": len(metadata.get("tags", [])),
            "total_remotes": len(metadata.get("remotes", [])),
            "total_commits": metadata.get("total_commits", 0),
            "total_contributors": len(metadata.get("contributors", [])),
            "first_commit_date": metadata.get("first_commit_date"),
            "last_commit_date": metadata.get("last_commit_date"),
        }

        return f"""# GitHound Repository Configuration

## Repository: {repo_path}

### Basic Information
- **Type**: {'Bare' if config_info['is_bare'] else 'Working'}
- **Active Branch**: {config_info['active_branch'] or 'N/A'}
- **Total Commits**: {config_info['total_commits']}
- **Contributors**: {config_info['total_contributors']}

### Structure
- **Branches**: {config_info['total_branches']}
- **Tags**: {config_info['total_tags']}
- **Remotes**: {config_info['total_remotes']}

### Timeline
- **First Commit**: {config_info['first_commit_date'] or 'N/A'}
- **Last Commit**: {config_info['last_commit_date'] or 'N/A'}

This repository contains {config_info['total_commits']} commits from {config_info['total_contributors']} contributors across {config_info['total_branches']} branches.
"""

    except Exception as e:
        await ctx.error(f"Error retrieving repository config: {str(e)}")  # [attr-defined]
        return f"Error: Could not retrieve repository configuration - {str(e)}"


async def get_repository_branches(repo_path: str, ctx: Context) -> str:
    """
    Get detailed information about all branches in the repository.

    Returns a formatted list of branches with their current commits,
    last activity, and relationship to other branches.
    """
    try:
        await ctx.info(f"Retrieving branch information for repository {repo_path}")

        repo = get_repository(Path(repo_path))
        metadata = get_repository_metadata(repo)

        branches_info = metadata.get("branches", [])

        branch_details: list[Any] = []
        for branch in branches_info:
            branch_details.append(
                f"- **{branch['name']}**: {branch['commit'][:8]} {'(remote)' if branch.get('is_remote') else '(local)'}"
            )

        return f"""# Repository Branches

## Repository: {repo_path}

### All Branches ({len(branches_info)} total)

{chr(10).join(branch_details) if branch_details else 'No branches found'}

### Active Branch
Current: {metadata.get('active_branch', 'N/A')}
"""

    except Exception as e:
        await ctx.error(f"Error retrieving branch information: {str(e)}")
        return f"Error: Could not retrieve branch information - {str(e)}"


async def get_repository_contributors(repo_path: str, ctx: Context) -> str:
    """
    Get information about all contributors to the repository.

    Returns a formatted list of contributors with their contribution statistics.
    """
    try:
        await ctx.info(f"Retrieving contributor information for repository {repo_path}")

        repo = get_repository(Path(repo_path))
        author_stats = get_author_statistics(repo)

        contributor_details: list[Any] = []
        for author, stats in author_stats.items():
            contributor_details.append(
                f"- **{author}**: {stats.get('total_commits', 0)} commits, "
                f"{stats.get('total_files', 0)} files"
            )

        return f"""# Repository Contributors

## Repository: {repo_path}

### Contributors ({len(author_stats)} total)

{chr(10).join(contributor_details) if contributor_details else 'No contributors found'}

### Top Contributors
{chr(10).join(contributor_details[:10]) if contributor_details else 'No data available'}
"""

    except Exception as e:
        await ctx.error(f"Error retrieving contributor information: {str(e)}")
        return f"Error: Could not retrieve contributor information - {str(e)}"


async def get_repository_summary(repo_path: str, ctx: Context) -> str:
    """
    Get a comprehensive summary of the repository.

    Returns an overview including basic statistics, recent activity,
    and key repository information.
    """
    try:
        await ctx.info(f"Generating repository summary for {repo_path}")

        repo = get_repository(Path(repo_path))
        metadata = get_repository_metadata(repo)

        # Create a comprehensive summary
        summary_lines = [
            f"Repository Summary: {repo_path}",
            "=" * 50,
            f"Total Commits: {metadata['total_commits']}",
            f"Contributors: {len(metadata['contributors'])}",
            f"Branches: {len(metadata['branches'])}",
            f"Tags: {len(metadata['tags'])}",
            f"Remotes: {len(metadata['remotes'])}",
            "",
            "Recent Activity:",
        ]

        # Add recent commits if available
        if metadata.get('recent_commits'):
            for commit in metadata['recent_commits'][:5]:  # Show last 5 commits
                summary_lines.append(
                    f"  - {commit['hash'][:8]}: {commit['message'][:60]}...")

        # Add top contributors
        if metadata.get('contributors'):
            summary_lines.extend([
                "",
                "Top Contributors:",
            ])
            sorted_contributors = sorted(
                metadata['contributors'].items(),
                key=lambda x: x[1]['commits'],
                reverse=True
            )
            # Show top 5 contributors
            for name, stats in sorted_contributors[:5]:
                summary_lines.append(f"  - {name}: {stats['commits']} commits")

        await ctx.info("Repository summary generated successfully")
        return "\n".join(summary_lines)

    except Exception as e:
        await ctx.error(f"Error generating repository summary: {str(e)}")
        return f"Error: Could not generate repository summary - {str(e)}"


async def get_file_history_resource(repo_path: str, file_path: str, ctx: Context) -> str:
    """
    Get the complete history of changes for a specific file as a resource.

    Returns a formatted history of all commits that modified the specified file.
    """
    try:
        await ctx.info(f"Retrieving file history for {file_path} in {repo_path}")

        repo = get_repository(Path(repo_path))
        history = get_file_history(
            repo=repo, file_path=file_path, max_count=50)

        history_lines = [
            f"# File History: {file_path}",
            f"## Repository: {repo_path}",
            "",
            f"### Change History ({len(history)} commits)",
            "",
        ]

        for i, commit_info in enumerate(history, 1):
            history_lines.extend([
                f"#### {i}. Commit {commit_info['hash'][:8]}",
                f"- **Author**: {commit_info['author_name']} <{commit_info['author_email']}>",
                f"- **Date**: {commit_info['date']}",
                f"- **Message**: {commit_info['message'][:100]}{'...' if len(commit_info['message']) > 100 else ''}",
                "",
            ])

        return "\n".join(history_lines)

    except Exception as e:
        await ctx.error(f"Error retrieving file history: {str(e)}")
        return f"Error: Could not retrieve file history - {str(e)}"


async def get_commit_details_resource(repo_path: str, commit_hash: str, ctx: Context) -> str:
    """
    Get detailed information about a specific commit as a resource.

    Returns comprehensive commit information including changes, statistics, and metadata.
    """
    try:
        await ctx.info(f"Retrieving commit details for {commit_hash} in {repo_path}")

        repo = get_repository(Path(repo_path))
        commit = repo.commit(commit_hash)
        commit_info = extract_commit_metadata(commit)

        details_lines = [
            f"# Commit Details: {commit_hash[:8]}",
            f"## Repository: {repo_path}",
            "",
            "### Basic Information",
            f"- **Full Hash**: {commit_info.hash}",
            f"- **Short Hash**: {commit_info.hash[:8]}",
            f"- **Author**: {commit_info.author_name} <{commit_info.author_email}>",
            f"- **Date**: {commit_info.date}",
            f"- **Message**: {commit_info.message}",
            "",
            "### Statistics",
            f"- **Files Changed**: {commit_info.files_changed}",
            f"- **Insertions**: +{commit_info.insertions}",
            f"- **Deletions**: -{commit_info.deletions}",
            "",
            "### Parent Commits",
        ]

        if commit_info.parents:
            for parent in commit_info.parents:
                details_lines.append(f"- {parent[:8]}")
        else:
            details_lines.append("- (Initial commit)")

        details_lines.extend([
            "",
            f"Generated at: {datetime.now().isoformat()}",
        ])

        return "\n".join(details_lines)

    except Exception as e:
        await ctx.error(f"Error retrieving commit details: {str(e)}")
        return f"Error: Could not retrieve commit details - {str(e)}"


async def get_file_blame_resource(repo_path: str, file_path: str, ctx: Context) -> str:
    """
    Get file blame information as a resource.

    Returns line-by-line authorship information for the specified file.
    """
    try:
        await ctx.info(f"Retrieving blame information for {file_path} in {repo_path}")

        repo = get_repository(Path(repo_path))
        blame_result = get_file_blame_impl(repo, file_path)

        blame_lines = [
            f"# File Blame: {file_path}",
            f"## Repository: {repo_path}",
            "",
            f"### Summary",
            f"- **Total Lines**: {blame_result.total_lines}",
            f"- **Contributors**: {len(blame_result.contributors)}",
            f"- **Oldest Line**: {blame_result.oldest_line_date.isoformat() if blame_result.oldest_line_date else 'N/A'}",
            f"- **Newest Line**: {blame_result.newest_line_date.isoformat() if blame_result.newest_line_date else 'N/A'}",
            "",
            "### Contributors",
        ]

        for contributor in blame_result.contributors:
            blame_lines.append(f"- {contributor}")

        blame_lines.extend([
            "",
            "### Line-by-Line Blame (First 50 lines)",
            "",
        ])

        # Show first 50 lines of blame info
        for line in blame_result.blame_info[:50]:
            blame_lines.append(
                f"{line.line_number:4d} | {line.commit_hash[:8]} | {line.author_name:20s} | {line.content[:80]}"
            )

        if len(blame_result.blame_info) > 50:
            newline = "\n"
            blame_lines.append(
                f"{newline}... and {len(blame_result.blame_info) - 50} more lines")

        blame_lines.extend([
            "",
            f"Generated at: {datetime.now().isoformat()}",
        ])

        return "\n".join(blame_lines)

    except Exception as e:
        await ctx.error(f"Error retrieving blame information: {str(e)}")
        return f"Error: Could not retrieve blame information - {str(e)}"
