"""Direct wrapper functions for MCP tools (used by integration tests)."""

from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from git import GitCommandError

from ..git_blame import get_author_statistics
from ..git_blame import get_file_blame as get_file_blame_impl
from ..git_diff import compare_commits
from ..git_handler import (
    extract_commit_metadata,
    get_commits_with_filters,
    get_repository,
    get_repository_metadata,
)
from .models import (
    AuthorStatsInput,
    CommitAnalysisInput,
    CommitComparisonInput,
    CommitHistoryInput,
    ExportInput,
    FileBlameInput,
    RepositoryInput,
)


# Import Context for type compatibility
try:
    from fastmcp import Context as BaseContext
except ImportError:
    # Create a base context class for type compatibility
    class BaseContext:  # type: ignore
        async def info(self, message: str) -> None: ...
        async def error(self, message: str) -> None: ...

class MockContext(BaseContext):
    """Mock context for direct function calls."""

    def __init__(self, fastmcp: Any = None) -> None:
        """Initialize mock context."""
        # Don't set fastmcp as it's read-only in the base class
        pass

    async def info(self, message: str, logger_name: str | None = None, extra: Mapping[str, Any] | None = None) -> None:
        """Mock info logging."""
        print(f"INFO: {message}")

    async def error(self, message: str, logger_name: str | None = None, extra: Mapping[str, Any] | None = None) -> None:
        """Mock error logging."""
        print(f"ERROR: {message}")


async def analyze_repository_direct(input_data: RepositoryInput) -> dict[str, Any]:
    """Direct wrapper for analyze_repository MCP tool."""
    ctx = MockContext()
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


async def analyze_commit_direct(input_data: CommitAnalysisInput) -> dict[str, Any]:
    """Direct wrapper for analyze_commit MCP tool."""
    ctx = MockContext()
    try:
        await ctx.info(f"Analyzing commit {input_data.commit_hash} in {input_data.repo_path}")

        repo = get_repository(Path(input_data.repo_path))
        commit = repo.commit(input_data.commit_hash)
        commit_metadata = extract_commit_metadata(commit)

        await ctx.info(f"Commit analysis complete for {input_data.commit_hash}")

        return {
            "status": "success",
            "commit_metadata": commit_metadata,
            "analysis_timestamp": datetime.now().isoformat(),
        }

    except GitCommandError as e:
        await ctx.error(f"Git error during commit analysis: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error during commit analysis: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}


async def export_repository_data_direct(input_data: ExportInput) -> dict[str, Any]:
    """Direct wrapper for export_repository_data MCP tool."""
    ctx = MockContext()
    try:
        await ctx.info(f"Exporting repository data from {input_data.repo_path}")

        repo = get_repository(Path(input_data.repo_path))

        # Get repository metadata
        metadata = get_repository_metadata(repo)

        # Create export data structure
        export_data = {
            "repository_metadata": metadata,
            "export_timestamp": datetime.now().isoformat(),
            "export_format": input_data.format,
        }

        # Write the export data to file
        import json

        import yaml

        output_path = Path(input_data.output_path)

        if input_data.format.lower() == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, default=str)
        elif input_data.format.lower() == "yaml":
            with open(output_path, "w", encoding="utf-8") as f:
                yaml.dump(export_data, f, default_flow_style=False)
        else:
            # Default to JSON
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, default=str)

        await ctx.info(f"Repository data export complete: {output_path}")

        return {
            "status": "success",
            "export_data": export_data,
            "format": input_data.format,
            "output_path": str(output_path),
        }

    except GitCommandError as e:
        await ctx.error(f"Git error during export: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error during export: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}


async def get_commit_history_direct(input_data: CommitHistoryInput) -> dict[str, Any]:
    """Direct wrapper for get_commit_history MCP tool."""
    ctx = MockContext()
    try:
        await ctx.info(f"Retrieving commit history from {input_data.repo_path}")

        repo = get_repository(Path(input_data.repo_path))
        commit_objects = list(
            get_commits_with_filters(
                repo,
                max_count=input_data.max_count,
                author_pattern=input_data.author,
                branch=input_data.branch,
            )
        )

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


async def get_file_blame_direct(input_data: FileBlameInput) -> dict[str, Any]:
    """Direct wrapper for get_file_blame MCP tool."""
    ctx = MockContext()
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


async def compare_commits_direct(input_data: CommitComparisonInput) -> dict[str, Any]:
    """Direct wrapper for compare_commits MCP tool."""
    ctx = MockContext()
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


async def get_author_stats_direct(input_data: AuthorStatsInput) -> dict[str, Any]:
    """Direct wrapper for get_author_stats MCP tool."""
    ctx = MockContext()
    try:
        await ctx.info(f"Getting author statistics from {input_data.repo_path}")

        repo = get_repository(Path(input_data.repo_path))
        author_stats = get_author_statistics(repo, branch=input_data.branch)

        await ctx.info("Author statistics complete")

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


# Direct wrapper functions for MCP resources
async def get_repository_config_direct(repo_path: str) -> str:
    """Direct wrapper for get_repository_config MCP resource."""
    ctx = MockContext()
    try:
        # [attr-defined]
        await ctx.info(f"Getting repository configuration for {repo_path}")

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

**Repository Path:** {config_info['repository_path']}
**Is Bare Repository:** {config_info['is_bare']}
**Active Branch:** {config_info['active_branch']}

## Statistics
- **Total Commits:** {config_info['total_commits']}
- **Total Branches:** {config_info['total_branches']}
- **Total Tags:** {config_info['total_tags']}
- **Total Remotes:** {config_info['total_remotes']}
- **Total Contributors:** {config_info['total_contributors']}

## Timeline
- **First Commit:** {config_info['first_commit_date'] or 'N/A'}
- **Last Commit:** {config_info['last_commit_date'] or 'N/A'}

Generated at: {datetime.now().isoformat()}
"""

    except Exception as e:
        # [attr-defined]
        await ctx.error(f"Error retrieving repository config: {str(e)}")
        return f"Error: Could not retrieve repository configuration - {str(e)}"


async def get_repository_contributors_direct(repo_path: str) -> str:
    """Direct wrapper for get_repository_contributors MCP resource."""
    ctx = MockContext()
    try:
        await ctx.info(f"Getting repository contributors for {repo_path}")

        repo = get_repository(Path(repo_path))
        metadata = get_repository_metadata(repo)

        contributors = metadata.get("contributors", [])

        result_lines = [
            "# Repository Contributors",
            "",
            f"**Repository:** {repo_path}",
            f"**Total Contributors:** {len(contributors)}",
            "",
            "## Contributor List",
        ]

        for i, contributor in enumerate(contributors, 1):
            if isinstance(contributor, dict):
                name = contributor.get("name", "Unknown")
                commits = contributor.get("commits", 0)
                result_lines.append(f"{i}. **{name}** - {commits} commits")
            else:
                result_lines.append(f"{i}. **{contributor}**")

        result_lines.extend(
            ["", f"Generated at: {datetime.now().isoformat() if datetime is not None else None}"]
        )

        return "\n".join(result_lines)

    except Exception as e:
        await ctx.error(f"Error retrieving contributor information: {str(e)}")
        return f"Error: Could not retrieve contributor information - {str(e)}"


async def get_repository_summary_direct(repo_path: str) -> str:
    """Direct wrapper for get_repository_summary MCP resource."""
    ctx = MockContext()
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
        if metadata.get("recent_commits"):
            for commit in metadata["recent_commits"][:5]:  # Show last 5 commits
                summary_lines.append(f"  - {commit['hash'][:8]}: {commit['message'][:60]}...")

        # Add top contributors
        if metadata.get("contributors"):
            summary_lines.extend(
                [
                    "",
                    "Top Contributors:",
                ]
            )
            contributors = metadata["contributors"]
            if isinstance(contributors, list):
                for i, contributor in enumerate(contributors[:5], 1):
                    if isinstance(contributor, dict):
                        name = contributor.get("name", "Unknown")
                        commits = contributor.get("commits", 0)
                        summary_lines.append(f"  - {name}: {commits} commits")
                    else:
                        summary_lines.append(f"  - {contributor}")

        await ctx.info("Repository summary generated successfully")
        return "\n".join(summary_lines)

    except GitCommandError as e:
        await ctx.error(f"Git error generating repository summary: {str(e)}")
        return f"Error: Could not generate repository summary - {str(e)}"
    except Exception as e:
        await ctx.error(f"Error generating repository summary: {str(e)}")
        return f"Error: Could not generate repository summary - {str(e)}"
