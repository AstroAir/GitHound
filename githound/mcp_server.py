"""GitHound MCP (Model Context Protocol) Server implementation using FastMCP 2.0."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from fastmcp import Context, FastMCP
from git import GitCommandError
from pydantic import BaseModel, Field, field_validator, model_validator

from .git_blame import get_author_statistics, get_file_blame as get_file_blame_impl
from .git_diff import compare_branches, compare_commits
from .git_handler import (
    extract_commit_metadata,
    get_commits_with_filters,
    get_file_history,
    get_repository,
    get_repository_metadata,
)
from .models import SearchQuery
from .schemas import ExportOptions, OutputFormat, PaginationInfo
from .search_engine import SearchOrchestrator
from .search_engine import (
    AuthorSearcher,
    CommitHashSearcher,
    ContentSearcher,
    DateRangeSearcher,
    FilePathSearcher,
    FileTypeSearcher,
    FuzzySearcher,
    MessageSearcher,
)
from .utils.export import ExportManager

# MCP Tool Input/Output Models


class RepositoryInput(BaseModel):
    """Input for repository operations."""

    repo_path: str = Field(..., description="Path to the Git repository")


class CommitAnalysisInput(BaseModel):
    """Input for commit analysis operations."""

    repo_path: str = Field(..., description="Path to the Git repository")
    commit_hash: str | None = Field(
        None, description="Specific commit hash (defaults to HEAD)")


class CommitFilterInput(BaseModel):
    """Input for filtered commit retrieval."""

    repo_path: str = Field(..., description="Path to the Git repository")
    branch: str | None = Field(None, description="Branch to search")
    author_pattern: str | None = Field(
        None, description="Author name/email pattern")
    message_pattern: str | None = Field(
        None, description="Commit message pattern")
    date_from: str | None = Field(None, description="Start date (ISO format)")
    date_to: str | None = Field(None, description="End date (ISO format)")
    file_patterns: list[str] | None = Field(
        None, description="File patterns to filter")
    max_count: int | None = Field(100, description="Maximum number of commits")


class FileHistoryInput(BaseModel):
    """Input for file history operations."""

    repo_path: str = Field(..., description="Path to the Git repository")
    file_path: str = Field(..., description="Path to the file")
    branch: str | None = Field(None, description="Branch to search")
    max_count: int | None = Field(50, description="Maximum number of commits")


class BlameInput(BaseModel):
    """Input for blame operations."""

    repo_path: str = Field(..., description="Path to the Git repository")
    file_path: str = Field(..., description="Path to the file")
    commit: str | None = Field(None, description="Specific commit to blame")


class DiffInput(BaseModel):
    """Input for diff operations."""

    repo_path: str = Field(..., description="Path to the Git repository")
    from_commit: str = Field(...,
                             description="Source commit hash or reference")
    to_commit: str = Field(..., description="Target commit hash or reference")
    file_patterns: list[str] | None = Field(
        None, description="File patterns to filter")


class BranchDiffInput(BaseModel):
    """Input for branch comparison."""

    repo_path: str = Field(..., description="Path to the Git repository")
    from_branch: str = Field(..., description="Source branch name")
    to_branch: str = Field(..., description="Target branch name")
    file_patterns: list[str] | None = Field(
        None, description="File patterns to filter")


class ExportInput(BaseModel):
    """Input for data export operations."""

    repo_path: str = Field(..., description="Path to the Git repository")
    output_path: str = Field(..., description="Output file path")
    format: str = Field("json", description="Export format (json, yaml, csv)")
    include_metadata: bool = Field(
        True, description="Include metadata in export")
    pagination: dict[str, Any] | None = Field(
        None, description="Pagination options")
    fields: list[str] | None = Field(
        None, description="Specific fields to include")
    exclude_fields: list[str] | None = Field(
        None, description="Fields to exclude")


class CommitHistoryInput(BaseModel):
    """Input for commit history operations."""

    repo_path: str = Field(..., description="Path to the Git repository")
    max_count: int = Field(
        100, description="Maximum number of commits to retrieve")
    branch: str | None = Field(None, description="Branch to search")
    author: str | None = Field(None, description="Author name/email pattern")
    since: str | None = Field(None, description="Start date (ISO format)")
    until: str | None = Field(None, description="End date (ISO format)")


class FileBlameInput(BaseModel):
    """Input for file blame operations."""

    repo_path: str = Field(..., description="Path to the Git repository")
    file_path: str = Field(..., description="Path to the file")
    commit: str | None = Field(None, description="Specific commit to blame")


class CommitComparisonInput(BaseModel):
    """Input for commit comparison operations."""

    repo_path: str = Field(..., description="Path to the Git repository")
    from_commit: str = Field(...,
                             description="Source commit hash or reference")
    to_commit: str = Field(..., description="Target commit hash or reference")


class AuthorStatsInput(BaseModel):
    """Input for author statistics operations."""

    repo_path: str = Field(..., description="Path to the Git repository")
    branch: str | None = Field(None, description="Branch to analyze")
    since: str | None = Field(None, description="Start date (ISO format)")
    until: str | None = Field(None, description="End date (ISO format)")


class AdvancedSearchInput(BaseModel):
    """Input for advanced multi-modal search operations."""

    repo_path: str = Field(..., description="Path to the Git repository")
    branch: str | None = Field(
        None, description="Branch to search (defaults to current)")

    # Search criteria
    content_pattern: str | None = Field(
        None, description="Content pattern to search for")
    commit_hash: str | None = Field(None, description="Specific commit hash")
    author_pattern: str | None = Field(
        None, description="Author name or email pattern")
    message_pattern: str | None = Field(
        None, description="Commit message pattern")
    date_from: str | None = Field(None, description="Start date (ISO format)")
    date_to: str | None = Field(None, description="End date (ISO format)")
    file_path_pattern: str | None = Field(
        None, description="File path pattern")
    file_extensions: list[str] | None = Field(
        None, description="File extensions to include")

    # Search options
    case_sensitive: bool = Field(False, description="Case sensitive search")
    fuzzy_search: bool = Field(False, description="Enable fuzzy matching")
    fuzzy_threshold: float = Field(
        0.8, description="Fuzzy matching threshold (0.0-1.0)")
    max_results: int | None = Field(
        100, description="Maximum number of results")

    # File filtering
    include_globs: list[str] | None = Field(
        None, description="Glob patterns to include")
    exclude_globs: list[str] | None = Field(
        None, description="Glob patterns to exclude")
    max_file_size: int | None = Field(
        None, description="Maximum file size in bytes")

    @field_validator("repo_path")
    @classmethod
    def validate_repo_path(cls, v: str) -> str:
        """Validate that the repository path exists and is a directory."""
        path = Path(v)
        if not path.exists():
            raise ValueError(f"Repository path does not exist: {v}")
        if not path.is_dir():
            raise ValueError(f"Repository path is not a directory: {v}")
        return v

    @field_validator("fuzzy_threshold")
    @classmethod
    def validate_fuzzy_threshold(cls, v: float) -> float:
        """Validate fuzzy threshold is between 0.0 and 1.0."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Fuzzy threshold must be between 0.0 and 1.0")
        return v

    @field_validator("max_results")
    @classmethod
    def validate_max_results(cls, v: int | None) -> int | None:
        """Validate max_results is positive."""
        if v is not None and v <= 0:
            raise ValueError("max_results must be positive")
        if v is not None and v > 10000:
            raise ValueError("max_results cannot exceed 10000")
        return v

    @field_validator("max_file_size")
    @classmethod
    def validate_max_file_size(cls, v: int | None) -> int | None:
        """Validate max_file_size is positive."""
        if v is not None and v <= 0:
            raise ValueError("max_file_size must be positive")
        return v

    @model_validator(mode="after")
    def validate_search_criteria(self) -> "AdvancedSearchInput":
        """Validate that at least one search criterion is provided."""
        search_fields = [
            self.content_pattern,
            self.commit_hash,
            self.author_pattern,
            self.message_pattern,
            self.file_path_pattern,
        ]

        if not any(field for field in search_fields):
            raise ValueError("At least one search criterion must be provided")

        return self


class FuzzySearchInput(BaseModel):
    """Input for fuzzy search operations."""

    repo_path: str = Field(..., description="Path to the Git repository")
    search_term: str = Field(...,
                             description="Term to search for with fuzzy matching")
    threshold: float = Field(
        0.8, description="Fuzzy matching threshold (0.0-1.0)")
    search_types: list[str] | None = Field(
        None, description="Types to search: content, author, message, file_path"
    )
    branch: str | None = Field(None, description="Branch to search")
    max_results: int | None = Field(
        50, description="Maximum number of results")

    @field_validator("repo_path")
    @classmethod
    def validate_repo_path(cls, v: str) -> str:
        """Validate that the repository path exists and is a directory."""
        path = Path(v)
        if not path.exists():
            raise ValueError(f"Repository path does not exist: {v}")
        if not path.is_dir():
            raise ValueError(f"Repository path is not a directory: {v}")
        return v

    @field_validator("search_term")
    @classmethod
    def validate_search_term(cls, v: str) -> str:
        """Validate search term is not empty."""
        if not v.strip():
            raise ValueError("Search term cannot be empty")
        return v.strip()

    @field_validator("threshold")
    @classmethod
    def validate_threshold(cls, v: float) -> float:
        """Validate threshold is between 0.0 and 1.0."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Threshold must be between 0.0 and 1.0")
        return v

    @field_validator("search_types")
    @classmethod
    def validate_search_types(cls, v: list[str] | None) -> list[str] | None:
        """Validate search types are valid."""
        if v is not None:
            valid_types = {"content", "author", "message", "file_path"}
            invalid_types = set(v) - valid_types
            if invalid_types:
                raise ValueError(
                    f"Invalid search types: {invalid_types}. Valid types: {valid_types}")
        return v

    @field_validator("max_results")
    @classmethod
    def validate_max_results(cls, v: int | None) -> int | None:
        """Validate max_results is positive."""
        if v is not None and v <= 0:
            raise ValueError("max_results must be positive")
        if v is not None and v > 10000:
            raise ValueError("max_results cannot exceed 10000")
        return v


class ContentSearchInput(BaseModel):
    """Input for content-specific search operations."""

    repo_path: str = Field(..., description="Path to the Git repository")
    pattern: str = Field(..., description="Content pattern to search for")
    file_extensions: list[str] | None = Field(
        None, description="File extensions to include")
    case_sensitive: bool = Field(False, description="Case sensitive search")
    whole_word: bool = Field(False, description="Match whole words only")
    branch: str | None = Field(None, description="Branch to search")
    max_results: int | None = Field(
        100, description="Maximum number of results")


class RepositoryManagementInput(BaseModel):
    """Input for repository management operations."""

    repo_path: str = Field(..., description="Path to the Git repository")


class WebServerInput(BaseModel):
    """Input for web server operations."""

    repo_path: str = Field(..., description="Path to the Git repository")
    host: str = Field("localhost", description="Host to bind the server")
    port: int = Field(8000, description="Port to bind the server")
    auto_open: bool = Field(True, description="Automatically open browser")

    @field_validator("repo_path")
    @classmethod
    def validate_repo_path(cls, v: str) -> str:
        """Validate that the repository path exists and is a directory."""
        path = Path(v)
        if not path.exists():
            raise ValueError(f"Repository path does not exist: {v}")
        if not path.is_dir():
            raise ValueError(f"Repository path is not a directory: {v}")
        return v

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Validate port is in valid range."""
        if not 1024 <= v <= 65535:
            raise ValueError("Port must be between 1024 and 65535")
        return v

    @field_validator("host")
    @classmethod
    def validate_host(cls, v: str) -> str:
        """Validate host is not empty."""
        if not v.strip():
            raise ValueError("Host cannot be empty")
        return v.strip()


# MCP Server Factory
def get_mcp_server() -> FastMCP:
    """Create and configure the GitHound MCP server with FastMCP 2.0."""
    return FastMCP("GitHound MCP Server")


# Global MCP server instance
mcp: FastMCP = get_mcp_server()

# Initialize search orchestrator with all searchers
_search_orchestrator: SearchOrchestrator | None = None


def get_search_orchestrator() -> SearchOrchestrator:
    """Get or create the search orchestrator with all searchers registered."""
    global _search_orchestrator
    if _search_orchestrator is None:
        _search_orchestrator = SearchOrchestrator()

        # Register all available searchers
        _search_orchestrator.register_searcher(CommitHashSearcher())
        _search_orchestrator.register_searcher(AuthorSearcher())
        _search_orchestrator.register_searcher(MessageSearcher())
        _search_orchestrator.register_searcher(DateRangeSearcher())
        _search_orchestrator.register_searcher(FilePathSearcher())
        _search_orchestrator.register_searcher(FileTypeSearcher())
        _search_orchestrator.register_searcher(ContentSearcher())
        _search_orchestrator.register_searcher(FuzzySearcher())

    return _search_orchestrator


# Advanced Search Tools


@mcp.tool
async def advanced_search(input_data: AdvancedSearchInput, ctx: Context) -> dict[str, Any]:
    """
    Perform advanced multi-modal search across the repository.

    Supports searching by content, commit hash, author, message, date range,
    file patterns, and more. Uses GitHound's powerful search engine with
    fuzzy matching and intelligent result ranking.
    """
    try:
        await ctx.info(f"Starting advanced search in repository {input_data.repo_path}")

        repo = get_repository(Path(input_data.repo_path))
        orchestrator = get_search_orchestrator()

        # Create SearchQuery from input
        query = SearchQuery(
            content_pattern=input_data.content_pattern,
            commit_hash=input_data.commit_hash,
            author_pattern=input_data.author_pattern,
            message_pattern=input_data.message_pattern,
            date_from=datetime.fromisoformat(input_data.date_from.replace(
                "Z", "+00:00")) if input_data.date_from else None,
            date_to=datetime.fromisoformat(input_data.date_to.replace(
                "Z", "+00:00")) if input_data.date_to else None,
            file_path_pattern=input_data.file_path_pattern,
            file_extensions=input_data.file_extensions,
            case_sensitive=input_data.case_sensitive,
            fuzzy_search=input_data.fuzzy_search,
            fuzzy_threshold=input_data.fuzzy_threshold,
            include_globs=input_data.include_globs,
            exclude_globs=input_data.exclude_globs,
            max_file_size=input_data.max_file_size,
        )

        # Perform search
        results = []
        result_count = 0

        async for result in orchestrator.search(
            repo=repo,
            query=query,
            branch=input_data.branch,
            max_results=input_data.max_results,
        ):
            results.append({
                "commit_hash": result.commit_hash,
                "file_path": str(result.file_path),
                "line_number": result.line_number,
                "matching_line": result.matching_line,
                "search_type": result.search_type.value,
                "relevance_score": result.relevance_score,
                "match_context": result.match_context,
                "commit_info": {
                    "author_name": result.commit_info.author_name if result.commit_info else None,
                    "author_email": result.commit_info.author_email if result.commit_info else None,
                    "date": result.commit_info.date.isoformat() if result.commit_info and result.commit_info.date else None,
                    "message": result.commit_info.message if result.commit_info else None,
                } if result.commit_info else None,
            })
            result_count += 1

            if result_count % 10 == 0:
                await ctx.info(f"Found {result_count} results so far...")

        await ctx.info(f"Advanced search complete: {len(results)} results found")

        return {
            "status": "success",
            "results": results,
            "total_count": len(results),
            "search_criteria": input_data.model_dump(),
            "search_timestamp": datetime.now().isoformat(),
        }

    except GitCommandError as e:
        await ctx.error(f"Git error during advanced search: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error during advanced search: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def fuzzy_search(input_data: FuzzySearchInput, ctx: Context) -> dict[str, Any]:
    """
    Perform fuzzy search with configurable similarity threshold.

    Searches across multiple dimensions (content, authors, messages, file paths)
    using fuzzy string matching to find approximate matches.
    """
    try:
        await ctx.info(f"Starting fuzzy search for '{input_data.search_term}' with threshold {input_data.threshold}")

        repo = get_repository(Path(input_data.repo_path))
        orchestrator = get_search_orchestrator()

        # Create SearchQuery for fuzzy search
        query = SearchQuery(
            content_pattern=input_data.search_term,
            author_pattern=input_data.search_term,
            message_pattern=input_data.search_term,
            file_path_pattern=input_data.search_term,
            fuzzy_search=True,
            fuzzy_threshold=input_data.threshold,
            case_sensitive=False,
        )

        # Perform search
        results = []
        async for result in orchestrator.search(
            repo=repo,
            query=query,
            branch=input_data.branch,
            max_results=input_data.max_results,
        ):
            results.append({
                "commit_hash": result.commit_hash,
                "file_path": str(result.file_path),
                "line_number": result.line_number,
                "matching_line": result.matching_line,
                "search_type": result.search_type.value,
                "relevance_score": result.relevance_score,
                "match_context": result.match_context,
                # For fuzzy search, relevance is similarity
                "similarity_score": result.relevance_score,
            })

        await ctx.info(f"Fuzzy search complete: {len(results)} results found")

        return {
            "status": "success",
            "results": results,
            "total_count": len(results),
            "search_term": input_data.search_term,
            "threshold": input_data.threshold,
            "search_timestamp": datetime.now().isoformat(),
        }

    except GitCommandError as e:
        await ctx.error(f"Git error during fuzzy search: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error during fuzzy search: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def content_search(input_data: ContentSearchInput, ctx: Context) -> dict[str, Any]:
    """
    Perform content-specific search with advanced pattern matching.

    Searches file content using regex patterns with support for file type
    filtering, case sensitivity, and whole word matching.
    """
    try:
        await ctx.info(f"Starting content search for pattern '{input_data.pattern}'")

        repo = get_repository(Path(input_data.repo_path))
        orchestrator = get_search_orchestrator()

        # Create SearchQuery for content search
        query = SearchQuery(
            content_pattern=input_data.pattern,
            file_extensions=input_data.file_extensions,
            case_sensitive=input_data.case_sensitive,
            fuzzy_search=False,
        )

        # Perform search
        results = []
        async for result in orchestrator.search(
            repo=repo,
            query=query,
            branch=input_data.branch,
            max_results=input_data.max_results,
        ):
            results.append({
                "commit_hash": result.commit_hash,
                "file_path": str(result.file_path),
                "line_number": result.line_number,
                "matching_line": result.matching_line,
                "match_context": result.match_context,
                "relevance_score": result.relevance_score,
            })

        await ctx.info(f"Content search complete: {len(results)} results found")

        return {
            "status": "success",
            "results": results,
            "total_count": len(results),
            "pattern": input_data.pattern,
            "search_timestamp": datetime.now().isoformat(),
        }

    except GitCommandError as e:
        await ctx.error(f"Git error during content search: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error during content search: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}


# Repository Analysis Tools


@mcp.tool
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


@mcp.tool
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
            "commit_metadata": commit_info.model_dump(),
            "analysis_timestamp": datetime.now().isoformat(),
        }

    except GitCommandError as e:
        await ctx.error(f"Git error during commit analysis: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error during commit analysis: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}


@mcp.tool
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
            "analysis_timestamp": datetime.now().isoformat(),
        }

    except GitCommandError as e:
        await ctx.error(f"Git error during commit filtering: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error during commit filtering: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}


@mcp.tool
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


# Blame and Diff Analysis Tools


@mcp.tool
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
            "file_blame": blame_result.model_dump(),
            "analysis_timestamp": datetime.now().isoformat(),
        }

    except GitCommandError as e:
        await ctx.error(f"Git error during blame analysis: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error during blame analysis: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}


@mcp.tool
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
            "commit_diff": diff_result.model_dump(),
            "analysis_timestamp": datetime.now().isoformat(),
        }

    except GitCommandError as e:
        await ctx.error(f"Git error during commit comparison: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error during commit comparison: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}


@mcp.tool
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
            "branch_diff": diff_result.model_dump(),
            "analysis_timestamp": datetime.now().isoformat(),
        }

    except GitCommandError as e:
        await ctx.error(f"Git error during branch comparison: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error during branch comparison: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def get_author_stats(input_data: RepositoryInput, ctx: Context) -> dict[str, Any]:
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
            "analysis_timestamp": datetime.now().isoformat(),
        }

    except GitCommandError as e:
        await ctx.error(f"Git error during author statistics: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error during author statistics: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}


@mcp.tool
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
        commits = []
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


@mcp.tool
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
            "oldest_line_date": blame_result.oldest_line_date.isoformat() if blame_result.oldest_line_date else None,
            "newest_line_date": blame_result.newest_line_date.isoformat() if blame_result.newest_line_date else None,
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
            ]
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


@mcp.tool
async def compare_commits_mcp(input_data: CommitComparisonInput, ctx: Context) -> dict[str, Any]:
    """
    Compare two commits and return detailed diff information.

    Returns comprehensive comparison between two commits.
    """
    try:
        await ctx.info(f"Comparing commits {input_data.from_commit} and {input_data.to_commit}")

        repo = get_repository(Path(input_data.repo_path))
        diff_result = compare_commits(
            repo, input_data.from_commit, input_data.to_commit)

        await ctx.info(f"Commit comparison complete")

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


@mcp.tool
async def export_repository_data(input_data: ExportInput, ctx: Context) -> dict[str, Any]:
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
        pagination_info = PaginationInfo(
            **input_data.pagination) if input_data.pagination else None

        export_options = ExportOptions(
            format=OutputFormat(input_data.format.lower()),
            include_metadata=input_data.include_metadata,
            pretty_print=True,
            pagination=pagination_info,
            fields=input_data.fields,
            exclude_fields=input_data.exclude_fields,
        )

        # For now, export the metadata (can be extended to export other data types)
        output_path = Path(input_data.output_path)

        if export_options.format == OutputFormat.JSON:
            import json

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, default=str)
        elif export_options.format == OutputFormat.YAML:
            import yaml

            with open(output_path, "w", encoding="utf-8") as f:
                yaml.dump(metadata, f, default_flow_style=False,
                          allow_unicode=True)
        else:
            return {"status": "error", "error": f"Unsupported export format: {input_data.format}"}

        await ctx.info(f"Export complete: {output_path}")

        return {
            "status": "success",
            "output_path": str(output_path),
            "format": input_data.format,
            "exported_items": len(metadata),
            "analysis_timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        await ctx.error(f"Error during data export: {str(e)}")
        return {"status": "error", "error": f"Export failed: {str(e)}"}


# Repository Management Tools


@mcp.tool
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


@mcp.tool
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


@mcp.tool
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


@mcp.tool
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


# Web Interface Integration Tools


@mcp.tool
async def start_web_server(input_data: WebServerInput, ctx: Context) -> dict[str, Any]:
    """
    Start the GitHound web interface server.

    Launches the web interface for interactive repository analysis
    with the specified configuration.
    """
    try:
        await ctx.info(f"Starting web server for repository {input_data.repo_path}")

        # Import web server components
        try:
            from .web.api import app
            import uvicorn
            import threading
            import time
        except ImportError as e:
            return {
                "status": "error",
                "error": f"Web server dependencies not available: {str(e)}"
            }

        # Validate repository
        repo = get_repository(Path(input_data.repo_path))

        # Use the existing web app
        web_app = app

        # Start server in background thread
        def run_server():
            uvicorn.run(
                web_app,
                host=input_data.host,
                port=input_data.port,
                log_level="info"
            )

        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()

        # Give server time to start
        time.sleep(2)

        server_url = f"http://{input_data.host}:{input_data.port}"

        await ctx.info(f"Web server started at {server_url}")

        # Optionally open browser
        if input_data.auto_open:
            try:
                import webbrowser
                webbrowser.open(server_url)
                await ctx.info("Browser opened automatically")
            except Exception as e:
                await ctx.info(f"Could not open browser: {str(e)}")

        return {
            "status": "success",
            "server_url": server_url,
            "host": input_data.host,
            "port": input_data.port,
            "repository_path": input_data.repo_path,
            "auto_opened": input_data.auto_open,
            "start_timestamp": datetime.now().isoformat(),
        }

    except GitCommandError as e:
        await ctx.error(f"Git error starting web server: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error starting web server: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}


@mcp.tool
async def generate_repository_report(input_data: RepositoryInput, ctx: Context) -> dict[str, Any]:
    """
    Generate a comprehensive repository analysis report.

    Creates a detailed report including repository statistics, contributor analysis,
    recent activity, and code quality metrics.
    """
    try:
        await ctx.info(f"Generating comprehensive report for {input_data.repo_path}")

        repo = get_repository(Path(input_data.repo_path))

        # Gather comprehensive data
        metadata = get_repository_metadata(repo)
        author_stats = get_author_statistics(repo)

        # Create comprehensive report
        report = {
            "repository_path": input_data.repo_path,
            "generation_timestamp": datetime.now().isoformat(),
            "summary": {
                "total_commits": metadata.get("total_commits", 0),
                "total_contributors": len(metadata.get("contributors", [])),
                "total_branches": len(metadata.get("branches", [])),
                "total_tags": len(metadata.get("tags", [])),
                "total_remotes": len(metadata.get("remotes", [])),
                "active_branch": metadata.get("active_branch"),
                "first_commit_date": metadata.get("first_commit_date"),
                "last_commit_date": metadata.get("last_commit_date"),
            },
            "contributors": author_stats,
            "branches": metadata.get("branches", []),
            "tags": metadata.get("tags", []),
            "remotes": metadata.get("remotes", []),
            # Last 20 commits
            "recent_activity": metadata.get("recent_commits", [])[:20],
        }

        await ctx.info("Repository report generation complete")

        return {
            "status": "success",
            "report": report,
            "generation_timestamp": datetime.now().isoformat(),
        }

    except GitCommandError as e:
        await ctx.error(f"Git error generating report: {str(e)}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        await ctx.error(f"Unexpected error generating report: {str(e)}")
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}


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


@mcp.resource("githound://repository/{repo_path}/summary")
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

    except GitCommandError as e:
        await ctx.error(f"Git error generating repository summary: {str(e)}")
        return f"Error: Could not generate repository summary - {str(e)}"
    except Exception as e:
        await ctx.error(f"Error generating repository summary: {str(e)}")
        return f"Error: Could not generate repository summary - {str(e)}"


@mcp.resource("githound://repository/{repo_path}/files/{file_path}/history")
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


@mcp.resource("githound://repository/{repo_path}/commits/{commit_hash}/details")
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


@mcp.resource("githound://repository/{repo_path}/blame/{file_path}")
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


# MCP Prompts for Common Workflows


@mcp.prompt
def investigate_bug(
    bug_description: str,
    suspected_files: str = "",
    time_frame: str = "last 30 days"
) -> str:
    """
    Generate a prompt for investigating a bug using GitHound's analysis capabilities.

    Provides a structured approach to bug investigation including relevant
    search queries, blame analysis, and commit history examination.
    """
    return f"""# Bug Investigation Workflow

## Bug Description
{bug_description}

## Investigation Steps

### 1. Search for Related Changes
Use GitHound's advanced search to find commits related to this bug:

**Content Search:**
- Search for error messages, function names, or keywords from the bug description
- Use fuzzy search if exact terms don't yield results
- Check recent commits in the specified time frame: {time_frame}

**Recommended Search Queries:**
```
advanced_search:
  content_pattern: "{bug_description.split()[0] if bug_description else 'error'}"
  date_from: "{time_frame}"
  fuzzy_search: true
  fuzzy_threshold: 0.7
```

### 2. Analyze Suspected Files
{f"Focus on these suspected files: {suspected_files}" if suspected_files else "Identify files that might be related to the bug"}

**File Analysis:**
- Use `get_file_blame` to see who last modified critical lines
- Use `get_file_history` to understand recent changes
- Look for patterns in commit messages

### 3. Examine Recent Changes
**Author Analysis:**
- Identify contributors who worked on related code
- Check their recent commits for similar changes
- Look for patterns in their commit history

### 4. Timeline Analysis
**Commit History:**
- Use `get_commit_history` with date filtering
- Look for commits around the time the bug was introduced
- Check for related changes in the same time period

### 5. Generate Report
**Documentation:**
- Export findings using `export_repository_data`
- Include relevant commit hashes, file changes, and author information
- Prepare summary for team discussion

## Next Steps
1. Execute the recommended searches
2. Analyze the results for patterns
3. Identify the root cause
4. Plan the fix strategy
"""


@mcp.prompt
def prepare_code_review(
    branch_name: str,
    base_branch: str = "main",
    focus_areas: str = ""
) -> str:
    """
    Generate a prompt for preparing a comprehensive code review.

    Provides guidance on analyzing changes, checking history, and
    identifying potential issues before code review.
    """
    return f"""# Code Review Preparation Workflow

## Review Target
**Branch:** {branch_name}
**Base:** {base_branch}
{f"**Focus Areas:** {focus_areas}" if focus_areas else ""}

## Pre-Review Analysis

### 1. Compare Branches
Get an overview of all changes:
```
compare_branches_diff:
  from_branch: "{base_branch}"
  to_branch: "{branch_name}"
```

### 2. Analyze Changed Files
For each modified file:
- Use `get_file_blame` to understand current ownership
- Use `get_file_history` to see change patterns
- Check if changes follow established patterns

### 3. Author Analysis
**Contributor Review:**
- Use `get_author_stats` to understand the contributor's history
- Check their typical commit patterns and quality
- Identify if this is a new contributor who might need extra attention

### 4. Search for Related Changes
**Pattern Detection:**
- Search for similar changes in the codebase
- Look for related bug fixes or features
- Check for consistency with existing implementations

### 5. Quality Checks
**Code Quality:**
- Look for large commits that might need breaking down
- Check for appropriate commit message quality
- Identify any files with high change frequency (potential hotspots)

### 6. Security and Performance
**Risk Assessment:**
- Search for changes to security-sensitive areas
- Look for performance-critical code modifications
- Check for changes to configuration or deployment files

## Review Checklist
- [ ] All changes are properly documented
- [ ] Commit messages are clear and descriptive
- [ ] No large files or sensitive data added
- [ ] Changes follow project conventions
- [ ] Related tests are included
- [ ] Documentation is updated if needed

## Tools to Use
1. `compare_branches_diff` - Overall change analysis
2. `get_file_blame` - Understand file ownership
3. `advanced_search` - Find related code patterns
4. `get_author_stats` - Contributor analysis
5. `export_repository_data` - Generate review summary
"""


@mcp.prompt
def analyze_performance_regression(
    performance_issue: str,
    suspected_timeframe: str = "last 2 weeks",
    affected_components: str = ""
) -> str:
    """
    Generate a prompt for analyzing performance regressions.

    Provides a systematic approach to identifying commits that might
    have introduced performance issues.
    """
    return f"""# Performance Regression Analysis

## Issue Description
{performance_issue}

## Analysis Timeframe
{suspected_timeframe}

{f"## Affected Components{chr(10)}{affected_components}{chr(10)}" if affected_components else ""}

## Investigation Strategy

### 1. Timeline Analysis
**Commit History Review:**
```
get_commit_history:
  date_from: "{suspected_timeframe}"
  max_count: 100
```

Look for:
- Large commits that might contain performance-impacting changes
- Changes to core algorithms or data structures
- Database query modifications
- Caching or optimization changes

### 2. File-Specific Analysis
**Hot Spot Identification:**
- Use `advanced_search` to find performance-related keywords:
  - "performance", "optimization", "cache", "query", "algorithm"
  - "slow", "timeout", "memory", "cpu"
- Focus on files with high change frequency

### 3. Author Pattern Analysis
**Contributor Investigation:**
- Identify who made changes during the regression period
- Use `get_author_stats` to understand their typical change patterns
- Look for unusual activity or large commits

### 4. Code Pattern Search
**Performance-Related Changes:**
```
advanced_search:
  content_pattern: "(loop|query|cache|memory|performance)"
  date_from: "{suspected_timeframe}"
  fuzzy_search: true
```

### 5. Diff Analysis
**Change Impact Assessment:**
For suspicious commits:
- Use `compare_commits` to see exact changes
- Look for algorithmic complexity changes
- Check for removed optimizations
- Identify new expensive operations

### 6. Blame Analysis
**Ownership Tracking:**
- Use `get_file_blame` on performance-critical files
- Identify recent changes to hot code paths
- Track down specific lines that might be problematic

## Red Flags to Look For
- O(n²) algorithms replacing O(n) ones
- Removed caching mechanisms
- Added database queries in loops
- Memory leaks or excessive allocations
- Synchronous operations replacing asynchronous ones

## Documentation
Use `export_repository_data` to create a comprehensive report including:
- Timeline of suspicious commits
- Author analysis
- File change patterns
- Specific code changes that might impact performance

## Next Steps
1. Execute the analysis workflow
2. Identify the most likely culprit commits
3. Create test cases to reproduce the issue
4. Plan the performance fix
"""


# Wrapper functions for direct calling (used by integration tests)
# These functions provide the same logic as the MCP tools but can be called directly

class MockContext:
    """Mock context for direct function calls."""

    async def info(self, message: str) -> None:
        """Mock info logging."""
        print(f"INFO: {message}")

    async def error(self, message: str) -> None:
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
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, default=str)
        elif input_data.format.lower() == "yaml":
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(export_data, f, default_flow_style=False)
        else:
            # Default to JSON
            with open(output_path, 'w', encoding='utf-8') as f:
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
        commit_objects = list(get_commits_with_filters(
            repo,
            max_count=input_data.max_count,
            author_pattern=input_data.author,
            branch=input_data.branch
        ))

        # Convert commit objects to dictionaries
        commits = []
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
            "oldest_line_date": blame_result.oldest_line_date.isoformat() if blame_result.oldest_line_date else None,
            "newest_line_date": blame_result.newest_line_date.isoformat() if blame_result.newest_line_date else None,
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
            ]
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
        diff_result = compare_commits(
            repo, input_data.from_commit, input_data.to_commit)

        await ctx.info(f"Commit comparison complete")

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

        await ctx.info(f"Author statistics complete")

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

        result_lines.extend([
            "",
            f"Generated at: {datetime.now().isoformat()}"
        ])

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
            contributors = metadata['contributors']
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


# Main server runner
def run_mcp_server(
    transport: str = "stdio",
    host: str = "localhost",
    port: int = 3000,
    log_level: str = "INFO"
) -> None:
    """
    Run the GitHound MCP server with FastMCP 2.0.

    Args:
        transport: Transport type ("stdio", "http", "sse")
        host: Host to bind for HTTP/SSE transports
        port: Port to bind for HTTP/SSE transports
        log_level: Logging level
    """
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logger = logging.getLogger("githound.mcp_server")
    logger.info(f"Starting GitHound MCP Server 2.0 with {transport} transport")

    # Log server capabilities
    logger.info("Server capabilities:")
    logger.info("  🔍 Advanced multi-modal search")
    logger.info("  📊 Repository analysis and statistics")
    logger.info("  📝 File blame and history analysis")
    logger.info("  🔄 Commit and branch comparison")
    logger.info("  📤 Data export in multiple formats")
    logger.info("  📚 Dynamic resources and prompts")

    try:
        # Run the server with specified transport
        if transport == "stdio":
            mcp.run()
        elif transport == "http":
            mcp.run(transport="http", host=host, port=port)
        elif transport == "sse":
            mcp.run(transport="sse", host=host, port=port)
        else:
            raise ValueError(f"Unsupported transport: {transport}")

    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


if __name__ == "__main__":
    import sys

    # Simple command line argument parsing
    transport = "stdio"
    host = "localhost"
    port = 3000
    log_level = "INFO"

    if len(sys.argv) > 1:
        if "--http" in sys.argv:
            transport = "http"
        elif "--sse" in sys.argv:
            transport = "sse"

        # Parse port
        for i, arg in enumerate(sys.argv):
            if arg == "--port" and i + 1 < len(sys.argv):
                port = int(sys.argv[i + 1])
            elif arg == "--host" and i + 1 < len(sys.argv):
                host = sys.argv[i + 1]
            elif arg == "--log-level" and i + 1 < len(sys.argv):
                log_level = sys.argv[i + 1]

    run_mcp_server(transport=transport, host=host,
                   port=port, log_level=log_level)
