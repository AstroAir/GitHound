"""Consolidated API models for GitHound web interface."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from ...models import OutputFormat, SearchMetrics, SearchResult

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
    branch: str | None = Field(None, description="Branch to search (defaults to current)")

    # Search criteria
    content_pattern: str | None = Field(None, description="Content pattern to search for")
    commit_hash: str | None = Field(None, description="Specific commit hash")
    author_pattern: str | None = Field(None, description="Author name or email pattern")
    message_pattern: str | None = Field(None, description="Commit message pattern")
    date_from: datetime | None = Field(None, description="Start date")
    date_to: datetime | None = Field(None, description="End date")
    file_path_pattern: str | None = Field(None, description="File path pattern")
    file_extensions: list[str] | None = Field(None, description="File extensions to search")

    # Search options
    case_sensitive: bool = Field(False, description="Case sensitive search")
    fuzzy_search: bool = Field(False, description="Enable fuzzy matching")
    fuzzy_threshold: float = Field(0.8, ge=0.0, le=1.0, description="Fuzzy match threshold")
    include_globs: list[str] | None = Field(None, description="Include file patterns")
    exclude_globs: list[str] | None = Field(None, description="Exclude file patterns")

    # Limits
    max_results: int | None = Field(1000, ge=1, le=10000, description="Maximum number of results")
    max_file_size: int | None = Field(None, description="Maximum file size in bytes")
    timeout_seconds: int = Field(300, ge=10, le=3600, description="Search timeout in seconds")

    # Result formatting
    include_context: bool = Field(True, description="Include surrounding context lines")
    context_lines: int = Field(3, ge=0, le=20, description="Number of context lines")
    include_metadata: bool = Field(True, description="Include commit metadata")


class SearchResultResponse(BaseModel):
    """Response model for individual search results."""

    # Core result data
    commit_hash: str = Field(..., description="Commit hash")
    file_path: str = Field(..., description="File path")
    line_number: int | None = Field(None, description="Line number")
    matching_line: str | None = Field(None, description="Matching line content")
    search_type: str = Field(..., description="Type of search match")

    # Match details
    relevance_score: float = Field(0.0, ge=0.0, le=1.0, description="Relevance score")
    match_context: list[str] = Field(default_factory=list, description="Context lines around match")

    # Commit metadata
    author_name: str | None = Field(None, description="Commit author name")
    author_email: str | None = Field(None, description="Commit author email")
    commit_date: datetime | None = Field(None, description="Commit date")
    commit_message: str | None = Field(None, description="Commit message")

    # File metadata
    file_size: int | None = Field(None, description="File size in bytes")
    file_type: str | None = Field(None, description="File type/extension")

    @classmethod
    def from_search_result(cls, result: SearchResult) -> SearchResultResponse:
        """Create a response item from a SearchResult instance."""
        context_lines: list[str] = []
        match_context = result.match_context

        if isinstance(match_context, dict):
            found_list = False
            for key in ("lines", "context", "match_context", "surrounding_lines"):
                value = match_context.get(key)
                if isinstance(value, list):
                    context_lines = [str(line) for line in value]
                    found_list = True
                    break
            if not found_list:
                context_lines = [
                    str(value) for value in match_context.values() if value is not None
                ]

        author_name = None
        author_email = None
        commit_date = None
        commit_message = None
        if result.commit_info is not None:
            author_name = getattr(result.commit_info, "author_name", None)
            author_email = getattr(result.commit_info, "author_email", None)
            commit_message = getattr(result.commit_info, "message", None)
            commit_date = getattr(result.commit_info, "date", None)
            if isinstance(commit_date, str):
                try:
                    commit_date = datetime.fromisoformat(commit_date)
                except ValueError:
                    commit_date = None

        return cls(
            commit_hash=result.commit_hash,
            file_path=str(result.file_path),
            line_number=result.line_number,
            matching_line=result.matching_line,
            search_type=result.search_type.value,
            relevance_score=result.relevance_score,
            match_context=context_lines,
            author_name=author_name,
            author_email=author_email,
            commit_date=commit_date,
            commit_message=commit_message,
            file_size=None,
            file_type=result.file_path.suffix.lstrip(".") if result.file_path.suffix else None,
        )


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

    # Pagination
    has_more: bool = Field(False, description="Whether more results are available")
    next_page_token: str | None = Field(None, description="Token for next page of results")

    # Query information
    query_info: dict[str, Any] = Field(
        default_factory=dict, description="Information about the search query"
    )
    filters_applied: dict[str, Any] = Field(
        default_factory=dict, description="Filters that were applied"
    )


@dataclass
class ActiveSearchState:
    """Track the lifecycle and data for an active search."""

    id: str
    status: str = "starting"
    progress: float = 0.0
    message: str = ""
    results_count: int = 0
    request: BaseModel | None = None
    response: SearchResponse | None = None
    results: list[SearchResult | SearchResultResponse | dict[str, Any]] | None = None
    metrics: SearchMetrics | None = None
    error: str | None = None
    user_id: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def update_results(
        self, results: Sequence[SearchResult | SearchResultResponse | dict[str, Any]] | None
    ) -> None:
        """Update stored results and synchronize counters."""
        if results is not None:
            self.results = list(results)
            self.results_count = len(self.results)

    def set_response(self, response: SearchResponse | dict[str, Any]) -> None:
        """Assign a response, accepting either model or raw mapping."""
        if isinstance(response, SearchResponse):
            self.response = response
            self.results_count = response.total_count
        else:
            parsed_results: list[SearchResultResponse] = []
            for item in response.get("results", []):
                if isinstance(item, SearchResultResponse):
                    parsed_results.append(item)
                elif isinstance(item, SearchResult):
                    parsed_results.append(SearchResultResponse.from_search_result(item))
                elif isinstance(item, dict):
                    parsed_results.append(SearchResultResponse(**item))

            self.response = SearchResponse(
                results=parsed_results,
                total_count=response.get("total_count", len(parsed_results)),
                search_id=response.get("search_id", self.id),
                status=response.get("status", self.status),
                commits_searched=response.get("commits_searched", 0),
                files_searched=response.get("files_searched", 0),
                search_duration_ms=response.get("search_duration_ms", 0.0),
                error_message=response.get("error_message"),
                has_more=response.get("has_more", False),
                next_page_token=response.get("next_page_token"),
                query_info=response.get("query_info", {}),
                filters_applied=response.get("filters_applied", {}),
            )
            self.results_count = self.response.total_count

    def to_status_payload(self) -> dict[str, Any]:
        """Create a serializable payload describing current status."""
        started = self.started_at.isoformat() if isinstance(self.started_at, datetime) else None
        completed = (
            self.completed_at.isoformat() if isinstance(self.completed_at, datetime) else None
        )

        metrics = self.metrics
        commits = 0
        files = 0
        duration = 0.0
        if metrics is not None:
            commits = metrics.total_commits_searched
            files = metrics.total_files_searched
            duration = metrics.search_duration_ms

        if self.response is not None:
            commits = self.response.commits_searched
            files = self.response.files_searched
            duration = self.response.search_duration_ms

        payload: dict[str, Any] = {
            "search_id": self.id,
            "status": self.status,
            "progress": self.progress,
            "message": self.message,
            "results_count": self.results_count,
            "started_at": started,
            "completed_at": completed,
            "commits_searched": commits,
            "files_searched": files,
            "search_duration_ms": duration,
        }

        if self.error:
            payload["error"] = self.error

        if self.extra:
            payload.update(self.extra)

        return payload

    def to_results_payload(self, page: int, page_size: int) -> dict[str, Any]:
        """Create a paginated results payload for API responses."""
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 50

        payload_results: list[dict[str, Any]]
        if self.response is not None:
            payload_results = [result.dict() for result in self.response.results]
            total_count = self.response.total_count
            status = self.response.status
            commits = self.response.commits_searched
            files = self.response.files_searched
            duration = self.response.search_duration_ms
            query_info = self.response.query_info
            filters_applied = self.response.filters_applied
        else:
            payload_results = []
            for item in self.results or []:
                if isinstance(item, SearchResultResponse):
                    payload_results.append(item.dict())
                elif isinstance(item, SearchResult):
                    payload_results.append(SearchResultResponse.from_search_result(item).dict())
                elif isinstance(item, dict):
                    payload_results.append(dict(item))

            total_count = len(payload_results)
            status = self.status
            metrics = self.metrics
            commits = (
                metrics.total_commits_searched if metrics else self.extra.get("commits_searched", 0)
            )
            files = metrics.total_files_searched if metrics else self.extra.get("files_searched", 0)
            duration = (
                metrics.search_duration_ms if metrics else self.extra.get("search_duration_ms", 0.0)
            )
            query_info = self.extra.get("query_info", {})
            filters_applied = self.extra.get("filters_applied", {})

        source_results = payload_results

        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paged_results = source_results[start_index:end_index]

        return {
            "search_id": self.id,
            "status": status,
            "results": paged_results,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "has_more": end_index < total_count,
            "commits_searched": commits,
            "files_searched": files,
            "search_duration_ms": duration,
            "query_info": query_info,
            "filters_applied": filters_applied,
        }

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> ActiveSearchState:
        """Create an ActiveSearchState from a plain mapping."""
        search_id = data.get("id") or data.get("search_id")
        state = cls(
            id=str(search_id) if search_id is not None else "",
            status=data.get("status", "starting"),
            progress=float(data.get("progress", 0.0)),
            message=data.get("message", ""),
            results_count=int(data.get("results_count", len(data.get("results", []) or []))),
            error=data.get("error"),
            user_id=data.get("user_id"),
        )

        request_data = data.get("request")
        if isinstance(request_data, SearchRequest):
            state.request = request_data
        elif isinstance(request_data, dict):
            try:
                state.request = SearchRequest(**request_data)
            except Exception:
                state.extra.setdefault("request_raw", request_data)

        response_data = data.get("response")
        if isinstance(response_data, SearchResponse):
            state.response = response_data
        elif isinstance(response_data, dict):
            try:
                state.set_response(response_data)
            except Exception:
                state.extra.setdefault("response_raw", response_data)

        metrics_data = data.get("metrics")
        if isinstance(metrics_data, SearchMetrics):
            state.metrics = metrics_data
        elif isinstance(metrics_data, dict):
            try:
                state.metrics = SearchMetrics(**metrics_data)
            except Exception:
                state.extra.setdefault("metrics_raw", metrics_data)

        results_data = data.get("results")
        if isinstance(results_data, list):
            normalized: list[SearchResult | SearchResultResponse | dict[str, Any]] = []
            for item in results_data:
                if isinstance(item, SearchResult | SearchResultResponse | dict):
                    normalized.append(item)
                else:
                    normalized.append({"value": item})
            if normalized:
                state.results = normalized
                state.results_count = len(normalized)

        for key in ("started_at", "completed_at"):
            value = data.get(key)
            parsed_value = _parse_datetime(value)
            if parsed_value is not None:
                setattr(state, key, parsed_value)
            elif value is not None:
                state.extra[f"{key}_raw"] = value

        # Preserve any additional fields for downstream use
        known_keys = {
            "id",
            "search_id",
            "status",
            "progress",
            "message",
            "results_count",
            "request",
            "response",
            "results",
            "metrics",
            "error",
            "user_id",
            "started_at",
            "completed_at",
        }
        for key, value in data.items():
            if key not in known_keys:
                state.extra.setdefault(key, value)

        return state


def _parse_datetime(value: Any) -> datetime | None:
    """Parse a datetime value from multiple representations."""
    if isinstance(value, datetime):
        result = value
    elif isinstance(value, str):
        text = value.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            result = datetime.fromisoformat(text)
        except ValueError:
            return None
    else:
        return None

    if result.tzinfo is None:
        return result.replace(tzinfo=UTC)
    return result.astimezone(UTC)


class SearchStatusResponse(BaseModel):
    """Response model for search status queries."""

    search_id: str = Field(..., description="Search identifier")
    status: str = Field(..., description="Current search status")
    progress: float = Field(0.0, ge=0.0, le=1.0, description="Search progress (0.0 to 1.0)")
    message: str = Field(..., description="Current status message")

    # Progress details
    commits_searched: int = Field(0, description="Commits searched so far")
    files_searched: int = Field(0, description="Files searched so far")
    results_found: int = Field(0, description="Results found so far")

    # Timing
    started_at: datetime | None = Field(None, description="Search start time")
    estimated_completion: datetime | None = Field(None, description="Estimated completion time")
    elapsed_seconds: float = Field(0.0, description="Elapsed time in seconds")

    # Error information
    error_message: str | None = Field(None, description="Error message if search failed")


# Export Models


class ExportRequest(BaseModel):
    """Request model for exporting search results."""

    search_id: str = Field(..., description="Search identifier")
    format: OutputFormat = Field(..., description="Export format")
    include_metadata: bool = Field(False, description="Include commit metadata")
    filename: str | None = Field(None, description="Custom filename")


class ExportResponse(BaseModel):
    """Response model for export operations."""

    export_id: str = Field(..., description="Export identifier")
    status: str = Field(..., description="Export status")
    download_url: str | None = Field(None, description="Download URL")
    filename: str = Field(..., description="Generated filename")
    file_size: int | None = Field(None, description="File size in bytes")
    format: OutputFormat = Field(..., description="Export format")
    created_at: datetime = Field(default_factory=datetime.now, description="Export creation time")
    expires_at: datetime | None = Field(None, description="Export expiration time")


# Health and Status Models


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="GitHound version")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
    active_searches: int = Field(..., description="Number of active searches")
    system_info: dict[str, Any] = Field(default_factory=dict, description="System information")


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
    contributors: list[str] = Field(default_factory=list, description="List of contributors")
    last_commit_date: datetime | None = Field(None, description="Date of last commit")
    repository_size: int | None = Field(None, description="Repository size in bytes")


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
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
