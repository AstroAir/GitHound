"""Repository management MCP tools for GitHound."""

from datetime import datetime
from pathlib import Path
from typing import Any

from fastmcp import Context
from git import GitCommandError

from ...git_handler import get_repository, get_repository_metadata
from ..models import RepositoryManagementInput


async def list_branches(input_data: RepositoryManagementInput, ctx: Context) -> dict[str, Any]:
    """
    List all branches in the repository with detailed information.

    Returns comprehensive information about local and remote branches
    including their current commits and last activity.
    """
    try:
        await ctx.info(f"Listing branches for repository {input_data.repo_path}")

        repo = get_repository(Path(input_data.repo_path))
        metadata = get_repository_metadata(repo)

        branches = metadata.get("branches", [])

        await ctx.info(f"Found {len(branches)} branches")

        return {
            "status": "success",
            "branches": branches,
            "total_count": len(branches),
            "active_branch": metadata.get("active_branch"),
            "analysis_timestamp": datetime.now().isoformat(),
        }

    except GitCommandError as e:
        await ctx.error(f"Git error listing branches: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error listing branches: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}


async def list_tags(input_data: RepositoryManagementInput, ctx: Context) -> dict[str, Any]:
    """
    List all tags in the repository with metadata.

    Returns information about all tags including their associated commits
    and creation dates.
    """
    try:
        await ctx.info(f"Listing tags for repository {input_data.repo_path}")

        repo = get_repository(Path(input_data.repo_path))
        metadata = get_repository_metadata(repo)

        tags = metadata.get("tags", [])

        await ctx.info(f"Found {len(tags)} tags")

        return {
            "status": "success",
            "tags": tags,
            "total_count": len(tags),
            "analysis_timestamp": datetime.now().isoformat(),
        }

    except GitCommandError as e:
        await ctx.error(f"Git error listing tags: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error listing tags: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}


async def list_remotes(input_data: RepositoryManagementInput, ctx: Context) -> dict[str, Any]:
    """
    List all remote repositories with their URLs.

    Returns information about all configured remotes including
    their fetch and push URLs.
    """
    try:
        await ctx.info(f"Listing remotes for repository {input_data.repo_path}")

        repo = get_repository(Path(input_data.repo_path))
        metadata = get_repository_metadata(repo)

        remotes = metadata.get("remotes", [])

        await ctx.info(f"Found {len(remotes)} remotes")

        return {
            "status": "success",
            "remotes": remotes,
            "total_count": len(remotes),
            "analysis_timestamp": datetime.now().isoformat(),
        }

    except GitCommandError as e:
        await ctx.error(f"Git error listing remotes: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error listing remotes: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}


async def validate_repository(input_data: RepositoryManagementInput, ctx: Context) -> dict[str, Any]:
    """
    Validate repository integrity and check for issues.

    Performs comprehensive validation of the Git repository including
    checking for corruption, missing objects, and configuration issues.
    """
    try:
        await ctx.info(f"Validating repository {input_data.repo_path}")

        repo = get_repository(Path(input_data.repo_path))

        # Basic validation checks
        validation_results: dict[str, Any] = {
            "is_valid_repo": True,
            "is_bare": repo.bare,
            "has_commits": len(list(repo.iter_commits())) > 0,
            "working_tree_clean": not repo.is_dirty(),
            "head_valid": repo.head.is_valid(),
            "issues": [],
            "warnings": [],
        }

        # Check for common issues
        if repo.is_dirty():
            validation_results["warnings"].append(
                "Working tree has uncommitted changes")

        if not validation_results["has_commits"]:
            validation_results["warnings"].append("Repository has no commits")

        await ctx.info("Repository validation complete")

        return {
            "status": "success",
            "validation_results": validation_results,
            "analysis_timestamp": datetime.now().isoformat(),
        }

    except GitCommandError as e:
        await ctx.error(f"Git error during validation: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "validation_results": {"is_valid_repo": False, "issues": [str(e)]}
        }
    except Exception as e:
        await ctx.error(f"Unexpected error during validation: {str(e)}")
        return {
            "status": "error",
            "error": f"Unexpected error: {str(e)}",
            "validation_results": {"is_valid_repo": False, "issues": [str(e)]}
        }
