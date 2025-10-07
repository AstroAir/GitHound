"""Consolidated API models for GitHound web interface."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from ...models import OutputFormat, SearchMetrics, SearchQuery, SearchResult


# Base API Models

class ApiResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Human-readable message")
    data: dict[str, Any] | list[Any] | None = Field(None, description="Response data")
    request_id: str | None = Field(None, description="Request identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = Field(False, description="Always false for errors")
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: dict[str, Any] | None = Field(None, description="Additional error details")
    request_id: str | None = Field(None, description="Request identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")


# Search Models

class SearchRequest(BaseModel):
    """Request model for search operations."""

    # Repository settings
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
    date_from: datetime | None = Field(None, description="Start date")
    date_to: datetime | None = Field(None, description="End date")
    file_path_pattern: str | None = Field(
        None, description="File path pattern")
    file_extensions: list[str] | None = Field(
        None, description="File extensions to search")

    # Search options
    case_sensitive: bool = Field(False, description="Case sensitive search")
    fuzzy_search: bool = Field(False, description="Enable fuzzy matching")
    fuzzy_threshold: float = Field(
        0.8, ge=0.0, le=1.0, description="Fuzzy match threshold")
    include_globs: list[str] | None = Field(
        None, description="Include file patterns")
    exclude_globs: list[str] | None = Field(
        None, description="Exclude file patterns")

    # Limits
    max_results: int | None = Field(
        1000, ge=1, le=10000, description="Maximum number of results")
    max_file_size: int | None = Field(
        None, description="Maximum file size in bytes")
    timeout_seconds: int = Field(
        300, ge=10, le=3600, description="Search timeout in seconds")

    # Result formatting
    include_context: bool = Field(
        True, description="Include surrounding context lines")
    context_lines: int = Field(
        3, ge=0, le=20, description="Number of context lines")
    include_metadata: bool = Field(True, description="Include commit metadata")

    def to_search_query(self) -> SearchQuery:
        """Convert this request to the internal SearchQuery model."""
        return SearchQuery(
            content_pattern=self.content_pattern,
            commit_hash=self.commit_hash,
            author_pattern=self.author_pattern,
            message_pattern=self.message_pattern,
            date_from=self.date_from,
            date_to=self.date_to,
            file_path_pattern=self.file_path_pattern,
            file_extensions=self.file_extensions,
            case_sensitive=self.case_sensitive,
            fuzzy_search=self.fuzzy_search,
            fuzzy_threshold=self.fuzzy_threshold,
            include_globs=self.include_globs,
            exclude_globs=self.exclude_globs,
            max_file_size=self.max_file_size,
        )


class SearchResultResponse(BaseModel):
    """Response model for individual search results."""

    # Core result data
    commit_hash: str = Field(..., description="Commit hash")
    file_path: str = Field(..., description="File path")
    line_number: int | None = Field(None, description="Line number")
    matching_line: str | None = Field(None, description="Matching line content")
    search_type: str = Field(..., description="Type of search match")

    # Match details
    relevance_score: float = Field(
        0.0, ge=0.0, le=1.0, description="Relevance score")
    match_context: list[str] = Field(
        default_factory=list, description="Context lines around match")

    # Commit metadata
    author_name: str | None = Field(None, description="Commit author name")
    author_email: str | None = Field(None, description="Commit author email")
    commit_date: datetime | None = Field(None, description="Commit date")
    commit_message: str | None = Field(None, description="Commit message")

    # File metadata
    file_size: int | None = Field(None, description="File size in bytes")
    file_type: str | None = Field(None, description="File type/extension")

    @classmethod
    def from_search_result(cls, result: SearchResult, include_metadata: bool = True) -> "SearchResultResponse":
        """Build a response object from a core SearchResult."""
        data: dict[str, Any] = {
            "commit_hash": result.commit_hash,
            "file_path": str(result.file_path),
            "line_number": result.line_number,
            "matching_line": result.matching_line,
            "search_type": result.search_type.value if hasattr(result.search_type, "value") else str(result.search_type),
            "relevance_score": result.relevance_score,
        }

        if include_metadata and result.commit_info is not None:
            ci = result.commit_info
            data.update(
                {
                    "author_name": getattr(ci, "author_name", None),
                    "author_email": getattr(ci, "author_email", None),
                    "commit_date": getattr(ci, "date", None),
                    "commit_message": getattr(ci, "message", None),
                }
            )

        return cls(**data)


class SearchResponse(BaseModel):
    """Response model for search operations."""

    results: list[SearchResultResponse] = Field(
        ..., description="Search results")
    total_count: int = Field(..., description="Total number of results")
    search_id: str = Field(..., description="Unique search identifier")
    status: str = Field(...,
                        description="Search status (completed, error, cancelled)")

    # Metrics
    commits_searched: int = Field(0, description="Number of commits searched")
    files_searched: int = Field(0, description="Number of files searched")
    search_duration_ms: float = Field(
        0.0, description="Search duration in milliseconds")

    # Optional error information
    error_message: str | None = Field(
        None, description="Error message if search failed")

    # Pagination
    has_more: bool = Field(False, description="Whether more results are available")
    next_page_token: str | None = Field(
        None, description="Token for next page of results")

    # Query information
    query_info: dict[str, Any] = Field(
        default_factory=dict, description="Information about the search query")
    filters_applied: dict[str, Any] = Field(
        default_factory=dict, description="Filters that were applied")

    @classmethod
    def from_results(
        cls,
        results: list[SearchResult],
        search_id: str,
        metrics: SearchMetrics | None = None,
        include_metadata: bool = True,
        status: str = "completed",
    ) -> "SearchResponse":
        """Create a SearchResponse from core SearchResult objects and metrics."""
        result_items = [
            SearchResultResponse.from_search_result(r, include_metadata=include_metadata) for r in results
        ]
        total_count = len(result_items)
        metrics = metrics or SearchMetrics(
            total_commits_searched=0, total_files_searched=0, search_duration_ms=0.0
        )
        return cls(
            results=result_items,
            total_count=total_count,
            search_id=search_id,
            status=status,
            commits_searched=getattr(metrics, "total_commits_searched", 0),
            files_searched=getattr(metrics, "total_files_searched", 0),
            search_duration_ms=getattr(metrics, "search_duration_ms", 0.0),
        )


class SearchStatusResponse(BaseModel):
    """Response model for search status queries."""

    search_id: str = Field(..., description="Search identifier")
    status: str = Field(..., description="Current search status")
    progress: float = Field(
        0.0, ge=0.0, le=1.0, description="Search progress (0.0 to 1.0)")
    message: str = Field(..., description="Current status message")

    # Progress details
    commits_searched: int = Field(0, description="Commits searched so far")
    files_searched: int = Field(0, description="Files searched so far")
    results_found: int = Field(0, description="Results found so far")
    # For backward-compat in tests that pass results_count:
    results_count: int = Field(0, description="Results found so far (alias)")

    # Timing
    started_at: datetime | None = Field(None, description="Search start time")
    estimated_completion: datetime | None = Field(
        None, description="Estimated completion time")
    elapsed_seconds: float = Field(0.0, description="Elapsed time in seconds")

    # Error information
    error_message: str | None = Field(
        None, description="Error message if search failed")


# Export Models

class ExportRequest(BaseModel):
    """Request model for exporting search results."""

    search_id: str = Field(..., description="Search identifier")
    format: OutputFormat = Field(..., description="Export format")
    include_metadata: bool = Field(
        False, description="Include commit metadata")
    filename: str | None = Field(None, description="Custom filename")


class ExportResponse(BaseModel):
    """Response model for export operations."""

    export_id: str = Field(..., description="Export identifier")
    status: str = Field(..., description="Export status")
    download_url: str | None = Field(None, description="Download URL")
    filename: str = Field(..., description="Generated filename")
    file_size: int | None = Field(None, description="File size in bytes")
    format: OutputFormat = Field(..., description="Export format")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Export creation time")
    expires_at: datetime | None = Field(
        None, description="Export expiration time")


# Health and Status Models

class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="GitHound version")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
    active_searches: int = Field(..., description="Number of active searches")
    system_info: dict[str, Any] = Field(
        default_factory=dict, description="System information")


class ServiceInfo(BaseModel):
    """Service information model."""

    name: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    description: str = Field(..., description="Service description")
    features: list[str] = Field(..., description="Available features")
    endpoints: dict[str, str] = Field(..., description="Available endpoints")
    documentation_url: str | None = Field(None, description="Documentation URL")


# Repository Models

class RepositoryInfo(BaseModel):
    """Repository information model."""

    path: str = Field(..., description="Repository path")
    name: str = Field(..., description="Repository name")
    is_bare: bool = Field(..., description="Whether repository is bare")
    current_branch: str | None = Field(None, description="Current branch")
    head_commit: str | None = Field(None, description="HEAD commit hash")
    total_commits: int = Field(0, description="Total number of commits")
    total_branches: int = Field(0, description="Total number of branches")
    total_tags: int = Field(0, description="Total number of tags")
    contributors: list[str] = Field(
        default_factory=list, description="List of contributors")
    last_commit_date: datetime | None = Field(
        None, description="Date of last commit")
    repository_size: int | None = Field(
        None, description="Repository size in bytes")


# Pagination Models

class PaginationInfo(BaseModel):
    """Pagination information model."""

    page: int = Field(1, ge=1, description="Current page number")
    page_size: int = Field(50, ge=1, le=1000, description="Items per page")
    total_items: int = Field(0, ge=0, description="Total number of items")
    total_pages: int = Field(0, ge=0, description="Total number of pages")
    has_next: bool = Field(False, description="Whether next page exists")
    has_previous: bool = Field(False, description="Whether previous page exists")
    next_page_token: str | None = Field(None, description="Next page token")
    previous_page_token: str | None = Field(None, description="Previous page token")


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""

    items: list[Any] = Field(..., description="Response items")
    pagination: PaginationInfo = Field(..., description="Pagination information")
    total_count: int = Field(..., description="Total number of items")
    request_id: str | None = Field(None, description="Request identifier")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Response timestamp")
