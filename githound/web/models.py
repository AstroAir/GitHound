"""Pydantic models for the GitHound web API."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from ..models import OutputFormat, SearchMetrics, SearchQuery, SearchResult


class SearchRequest(BaseModel):
    """Request model for search operations."""

    # Repository settings
    repo_path: str = Field(..., description="Path to the Git repository")
    branch: str | None = Field(None, description="Branch to search (defaults to current)")

    # Search criteria
    content_pattern: str | None = Field(None, description="Content pattern to search for")
    commit_hash: str | None = Field(None, description="Specific commit hash")
    author_pattern: str | None = Field(None, description="Author name or email pattern")
    message_pattern: str | None = Field(None, description="Commit message pattern")

    # Date range
    date_from: datetime | None = Field(None, description="Search from this date")
    date_to: datetime | None = Field(None, description="Search until this date")

    # File filtering
    file_path_pattern: str | None = Field(None, description="File path pattern")
    file_extensions: list[str] | None = Field(None, description="File extensions to include")

    # Search behavior
    case_sensitive: bool = Field(False, description="Case-sensitive search")
    fuzzy_search: bool = Field(False, description="Enable fuzzy matching")
    fuzzy_threshold: float = Field(0.8, description="Fuzzy matching threshold (0.0-1.0)")

    # Filtering options
    include_globs: list[str] | None = Field(None, description="Glob patterns to include")
    exclude_globs: list[str] | None = Field(None, description="Glob patterns to exclude")
    max_file_size: int | None = Field(None, description="Maximum file size in bytes")

    # Performance options
    max_results: int | None = Field(None, description="Maximum number of results")
    timeout_seconds: int | None = Field(300, description="Search timeout in seconds")

    def to_search_query(self) -> SearchQuery:
        """Convert to internal SearchQuery model."""
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
            min_commit_size=None,
            max_commit_size=None,
        )


class SearchResultResponse(BaseModel):
    """Response model for individual search results."""

    commit_hash: str = Field(..., description="Commit hash")
    file_path: str = Field(..., description="File path")
    line_number: int | None = Field(None, description="Line number")
    matching_line: str | None = Field(None, description="Matching line content")
    search_type: str = Field(..., description="Type of search that found this result")
    relevance_score: float = Field(..., description="Relevance score (0.0-1.0)")

    # Optional commit information
    author_name: str | None = Field(None, description="Commit author name")
    author_email: str | None = Field(None, description="Commit author email")
    commit_date: datetime | None = Field(None, description="Commit date")
    commit_message: str | None = Field(None, description="Commit message")

    # Match context
    match_context: dict[str, Any] | None = Field(None, description="Additional match context")

    @classmethod
    def from_search_result(
        cls, result: SearchResult, include_metadata: bool = False
    ) -> "SearchResultResponse":
        """Create from internal SearchResult model."""
        response = cls(
            commit_hash=result.commit_hash,
            file_path=str(result.file_path),
            line_number=result.line_number,
            matching_line=result.matching_line,
            search_type=result.search_type.value,
            relevance_score=result.relevance_score,
            match_context=result.match_context,
            author_name=result.commit_info.author_name if result.commit_info else None,
            author_email=result.commit_info.author_email if result.commit_info else None,
            commit_date=(
                result.commit_info.date
                if result.commit_info and isinstance(result.commit_info.date, datetime)
                else None
            ),
            commit_message=result.commit_info.message if result.commit_info else None,
        )

        return response


class SearchResponse(BaseModel):
    """Response model for search operations."""

    results: list[SearchResultResponse] = Field(..., description="Search results")
    total_count: int = Field(..., description="Total number of results")
    search_id: str = Field(..., description="Unique search identifier")
    status: str = Field(..., description="Search status (completed, error, cancelled)")

    # Metrics
    commits_searched: int = Field(0, description="Number of commits searched")
    files_searched: int = Field(0, description="Number of files searched")
    search_duration_ms: float = Field(0.0, description="Search duration in milliseconds")

    # Optional error information
    error_message: str | None = Field(None, description="Error message if search failed")

    @classmethod
    def from_results(
        cls,
        results: list[SearchResult],
        search_id: str,
        metrics: SearchMetrics | None = None,
        include_metadata: bool = False,
        status: str = "completed",
        error_message: str | None = None,
    ) -> "SearchResponse":
        """Create from search results and metrics."""
        response_results = [
            SearchResultResponse.from_search_result(r, include_metadata) for r in results
        ]

        return cls(
            results=response_results,
            total_count=len(results),
            search_id=search_id,
            status=status,
            commits_searched=metrics.total_commits_searched if metrics else 0,
            files_searched=metrics.total_files_searched if metrics else 0,
            search_duration_ms=metrics.search_duration_ms if metrics else 0.0,
            error_message=error_message,
        )


class SearchStatusResponse(BaseModel):
    """Response model for search status queries."""

    search_id: str = Field(..., description="Search identifier")
    status: str = Field(..., description="Current status")
    progress: float = Field(..., description="Progress percentage (0.0-1.0)")
    message: str = Field(..., description="Current status message")
    results_count: int = Field(0, description="Number of results found so far")

    # Time information
    started_at: datetime = Field(..., description="Search start time")
    estimated_completion: datetime | None = Field(None, description="Estimated completion time")


class ExportRequest(BaseModel):
    """Request model for exporting search results."""

    search_id: str = Field(..., description="Search identifier")
    format: OutputFormat = Field(..., description="Export format")
    include_metadata: bool = Field(False, description="Include commit metadata")
    filename: str | None = Field(None, description="Custom filename")


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="GitHound version")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
    active_searches: int = Field(..., description="Number of active searches")


class ErrorResponse(BaseModel):
    """Response model for API errors."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: dict[str, Any] | None = Field(None, description="Additional error details")
    request_id: str | None = Field(None, description="Request identifier for debugging")
