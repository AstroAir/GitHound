"""GitHound MCP (Model Context Protocol) Server implementation using FastMCP."""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP, Context
from git import Repo, GitCommandError
from pydantic import BaseModel, Field

from .git_handler import (
    get_repository, extract_commit_metadata, get_repository_metadata,
    get_commits_with_filters, get_file_history
)
from .git_blame import get_file_blame, get_line_history, get_author_statistics
from .git_diff import compare_commits, compare_branches, get_file_diff_history
from .models import SearchQuery, SearchResult, CommitInfo
from .schemas import ExportOptions, OutputFormat, PaginationInfo
from .utils.export import ExportManager


# MCP Tool Input/Output Models

class RepositoryInput(BaseModel):
    """Input for repository operations."""
    repo_path: str = Field(..., description="Path to the Git repository")


class CommitAnalysisInput(BaseModel):
    """Input for commit analysis operations."""
    repo_path: str = Field(..., description="Path to the Git repository")
    commit_hash: Optional[str] = Field(None, description="Specific commit hash (defaults to HEAD)")


class CommitFilterInput(BaseModel):
    """Input for filtered commit retrieval."""
    repo_path: str = Field(..., description="Path to the Git repository")
    branch: Optional[str] = Field(None, description="Branch to search")
    author_pattern: Optional[str] = Field(None, description="Author name/email pattern")
    message_pattern: Optional[str] = Field(None, description="Commit message pattern")
    date_from: Optional[str] = Field(None, description="Start date (ISO format)")
    date_to: Optional[str] = Field(None, description="End date (ISO format)")
    file_patterns: Optional[List[str]] = Field(None, description="File patterns to filter")
    max_count: Optional[int] = Field(100, description="Maximum number of commits")


class FileHistoryInput(BaseModel):
    """Input for file history operations."""
    repo_path: str = Field(..., description="Path to the Git repository")
    file_path: str = Field(..., description="Path to the file")
    branch: Optional[str] = Field(None, description="Branch to search")
    max_count: Optional[int] = Field(50, description="Maximum number of commits")


class BlameInput(BaseModel):
    """Input for blame operations."""
    repo_path: str = Field(..., description="Path to the Git repository")
    file_path: str = Field(..., description="Path to the file")
    commit: Optional[str] = Field(None, description="Specific commit to blame")


class DiffInput(BaseModel):
    """Input for diff operations."""
    repo_path: str = Field(..., description="Path to the Git repository")
    from_commit: str = Field(..., description="Source commit hash or reference")
    to_commit: str = Field(..., description="Target commit hash or reference")
    file_patterns: Optional[List[str]] = Field(None, description="File patterns to filter")


class BranchDiffInput(BaseModel):
    """Input for branch comparison."""
    repo_path: str = Field(..., description="Path to the Git repository")
    from_branch: str = Field(..., description="Source branch name")
    to_branch: str = Field(..., description="Target branch name")
    file_patterns: Optional[List[str]] = Field(None, description="File patterns to filter")


class ExportInput(BaseModel):
    """Input for data export operations."""
    repo_path: str = Field(..., description="Path to the Git repository")
    output_path: str = Field(..., description="Output file path")
    format: str = Field("json", description="Export format (json, yaml, csv)")
    include_metadata: bool = Field(True, description="Include metadata in export")
    pagination: Optional[Dict[str, Any]] = Field(None, description="Pagination options")
    fields: Optional[List[str]] = Field(None, description="Specific fields to include")
    exclude_fields: Optional[List[str]] = Field(None, description="Fields to exclude")


# MCP Server Factory
def get_mcp_server() -> FastMCP:
    return FastMCP(
        name="GitHound MCP Server",
        instructions="""
        GitHound MCP Server provides comprehensive Git repository analysis capabilities.
        
        Available tools:
        - Repository analysis and metadata extraction
        - Commit history retrieval with advanced filtering
        - File history and blame analysis
        - Diff analysis between commits and branches
        - Author statistics and contribution analysis
        - Data export in multiple formats
        
        Use these tools to analyze Git repositories, track changes, understand code evolution,
        and generate insights about development patterns and contributor activity.
        """
    )

mcp: FastMCP = get_mcp_server()


# Repository Analysis Tools

@mcp.tool
async def analyze_repository(input_data: RepositoryInput, ctx: Context) -> Dict[str, Any]:
    """
    Analyze a Git repository and return comprehensive metadata.
    
    Returns repository information including branches, tags, remotes,
    contributor statistics, and overall repository health metrics.
    """
    try:
        await ctx.info(f"Analyzing repository at {input_data.repo_path}")
        
        repo = get_repository(Path(input_data.repo_path))
        metadata = get_repository_metadata(repo)
        
        await ctx.info(f"Repository analysis complete: {metadata['total_commits']} commits, {len(metadata['contributors'])} contributors")
        
        return {
            "status": "success",
            "repository_metadata": metadata,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
    except GitCommandError as e:
        await ctx.error(f"Git error during repository analysis: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error during repository analysis: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def analyze_commit(input_data: CommitAnalysisInput, ctx: Context) -> Dict[str, Any]:
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
        
        await ctx.info(f"Commit analysis complete: {commit_info.hash[:8]} by {commit_info.author_name}")
        
        return {
            "status": "success",
            "commit_metadata": commit_info.model_dump(),
            "analysis_timestamp": datetime.now().isoformat()
        }
        
    except GitCommandError as e:
        await ctx.error(f"Git error during commit analysis: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error during commit analysis: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def get_filtered_commits(input_data: CommitFilterInput, ctx: Context) -> Dict[str, Any]:
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
            date_from = datetime.fromisoformat(input_data.date_from.replace('Z', '+00:00'))
        if input_data.date_to:
            date_to = datetime.fromisoformat(input_data.date_to.replace('Z', '+00:00'))
        
        commits = get_commits_with_filters(
            repo=repo,
            branch=input_data.branch,
            author_pattern=input_data.author_pattern,
            message_pattern=input_data.message_pattern,
            date_from=date_from,
            date_to=date_to,
            file_patterns=input_data.file_patterns,
            max_count=input_data.max_count
        )
        
        commit_list = []
        for commit in commits:
            commit_info = extract_commit_metadata(commit)
            commit_list.append(commit_info.model_dump())
        
        await ctx.info(f"Retrieved {len(commit_list)} commits matching filter criteria")
        
        return {
            "status": "success",
            "commits": commit_list,
            "filter_criteria": input_data.model_dump(),
            "total_results": len(commit_list),
            "analysis_timestamp": datetime.now().isoformat()
        }
        
    except GitCommandError as e:
        await ctx.error(f"Git error during commit filtering: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error during commit filtering: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def get_file_history_mcp(input_data: FileHistoryInput, ctx: Context) -> Dict[str, Any]:
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
            max_count=input_data.max_count
        )
        
        await ctx.info(f"Retrieved {len(history)} commits in file history")
        
        return {
            "status": "success",
            "file_path": input_data.file_path,
            "history": history,
            "total_commits": len(history),
            "analysis_timestamp": datetime.now().isoformat()
        }
        
    except GitCommandError as e:
        await ctx.error(f"Git error during file history retrieval: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error during file history retrieval: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}


# Blame and Diff Analysis Tools

@mcp.tool
async def analyze_file_blame(input_data: BlameInput, ctx: Context) -> Dict[str, Any]:
    """
    Analyze line-by-line authorship for a file using git blame.

    Returns detailed blame information showing who last modified each line,
    when it was changed, and the commit message for each change.
    """
    try:
        await ctx.info(f"Analyzing blame for file {input_data.file_path}")

        repo = get_repository(Path(input_data.repo_path))

        blame_result = get_file_blame(
            repo=repo,
            file_path=input_data.file_path,
            commit=input_data.commit
        )

        await ctx.info(f"Blame analysis complete: {blame_result.total_lines} lines, {len(blame_result.contributors)} contributors")

        return {
            "status": "success",
            "file_blame": blame_result.model_dump(),
            "analysis_timestamp": datetime.now().isoformat()
        }

    except GitCommandError as e:
        await ctx.error(f"Git error during blame analysis: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error during blame analysis: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def compare_commits_diff(input_data: DiffInput, ctx: Context) -> Dict[str, Any]:
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
            file_patterns=input_data.file_patterns
        )

        await ctx.info(f"Diff analysis complete: {diff_result.files_changed} files changed, +{diff_result.total_additions}/-{diff_result.total_deletions}")

        return {
            "status": "success",
            "commit_diff": diff_result.model_dump(),
            "analysis_timestamp": datetime.now().isoformat()
        }

    except GitCommandError as e:
        await ctx.error(f"Git error during commit comparison: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error during commit comparison: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def compare_branches_diff(input_data: BranchDiffInput, ctx: Context) -> Dict[str, Any]:
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
            file_patterns=input_data.file_patterns
        )

        await ctx.info(f"Branch diff analysis complete: {diff_result.files_changed} files changed")

        return {
            "status": "success",
            "branch_diff": diff_result.model_dump(),
            "analysis_timestamp": datetime.now().isoformat()
        }

    except GitCommandError as e:
        await ctx.error(f"Git error during branch comparison: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error during branch comparison: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def get_author_stats(input_data: RepositoryInput, ctx: Context) -> Dict[str, Any]:
    """
    Get comprehensive author statistics for the repository.

    Returns detailed statistics about each contributor including
    commit counts, lines authored, and activity timeline.
    """
    try:
        await ctx.info(f"Generating author statistics for {input_data.repo_path}")

        repo = get_repository(Path(input_data.repo_path))

        author_stats = get_author_statistics(repo)

        await ctx.info(f"Author statistics complete: {len(author_stats)} contributors analyzed")

        return {
            "status": "success",
            "author_statistics": author_stats,
            "total_authors": len(author_stats),
            "analysis_timestamp": datetime.now().isoformat()
        }

    except GitCommandError as e:
        await ctx.error(f"Git error during author statistics: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error during author statistics: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def export_repository_data(input_data: ExportInput, ctx: Context) -> Dict[str, Any]:
    """
    Export repository analysis data in various formats.

    Supports exporting repository metadata, commit history, and analysis
    results in JSON, YAML, or CSV formats for further processing.
    """
    try:
        await ctx.info(f"Exporting repository data to {input_data.output_path}")

        repo = get_repository(Path(input_data.repo_path))

        # Get comprehensive repository data
        metadata = get_repository_metadata(repo)

        # Create export manager and options
        export_manager = ExportManager()
        pagination_info = PaginationInfo(**input_data.pagination) if input_data.pagination else None

        export_options = ExportOptions(
            format=OutputFormat(input_data.format.lower()),
            include_metadata=input_data.include_metadata,
            pretty_print=True,
            pagination=pagination_info,
            fields=input_data.fields,
            exclude_fields=input_data.exclude_fields
        )

        # For now, export the metadata (can be extended to export other data types)
        output_path = Path(input_data.output_path)

        if export_options.format == OutputFormat.JSON:
            import json
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, default=str)
        elif export_options.format == OutputFormat.YAML:
            import yaml
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(metadata, f, default_flow_style=False, allow_unicode=True)
        else:
            return {"status": "error", "error": f"Unsupported export format: {input_data.format}"}

        await ctx.info(f"Export complete: {output_path}")

        return {
            "status": "success",
            "output_path": str(output_path),
            "format": input_data.format,
            "exported_items": len(metadata),
            "analysis_timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        await ctx.error(f"Error during data export: {str(e)}")
        return {"status": "error", "error": f"Export failed: {str(e)}"}


# Resources for repository configuration and metadata

@mcp.resource("githound://repository/{repo_path}/config")
async def get_repository_config(repo_path: str, ctx: Context) -> str:
    """
    Get repository configuration information.
    
    Returns Git configuration settings, remote URLs, and repository metadata
    in a structured format for easy consumption by AI models.
    """
    try:
        await ctx.info(f"Retrieving configuration for repository {repo_path}")
        
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
            "last_commit_date": metadata.get("last_commit_date")
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
        await ctx.error(f"Error retrieving repository config: {str(e)}")
        return f"Error: Could not retrieve repository configuration - {str(e)}"


@mcp.resource("githound://repository/{repo_path}/branches")
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

        branch_details = []
        for branch in branches_info:
            branch_details.append(f"- **{branch['name']}**: {branch['commit'][:8]} {'(remote)' if branch.get('is_remote') else '(local)'}")

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


@mcp.resource("githound://repository/{repo_path}/contributors")
async def get_repository_contributors(repo_path: str, ctx: Context) -> str:
    """
    Get information about all contributors to the repository.

    Returns a formatted list of contributors with their contribution statistics.
    """
    try:
        await ctx.info(f"Retrieving contributor information for repository {repo_path}")

        repo = get_repository(Path(repo_path))
        author_stats = get_author_statistics(repo)

        contributor_details = []
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


# Main server runner
def run_mcp_server():
    """Run the GitHound MCP server."""
    logging.basicConfig(level=logging.INFO)
    mcp.run()


if __name__ == "__main__":
    run_mcp_server()
