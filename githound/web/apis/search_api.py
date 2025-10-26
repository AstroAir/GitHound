"""
Consolidated search API for GitHound.

Provides comprehensive search capabilities including multi-modal search,
fuzzy matching, pattern-based queries, and historical code search.
"""

import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Query, Request, status
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field, model_validator

from githound.search_engine import create_search_orchestrator

from ...git_handler import get_repository
from ...models import OutputFormat, SearchMetrics, SearchQuery, SearchResult, SearchType
from ...search_engine import SearchOrchestrator
from ...utils.export import ExportManager
from ..middleware.rate_limiting import get_limiter
from ..models.api_models import (
    ActiveSearchState,
    ApiResponse,
    ExportRequest,
    SearchResponse,
    SearchResultResponse,
    SearchStatusResponse,
)
from ..services.auth_service import require_user
from ..utils.validation import get_request_id, validate_repo_path

# Create router
router = APIRouter(prefix="/search", tags=["search"])
limiter = get_limiter()

# Track running searches for status and export endpoints
active_searches: dict[str, ActiveSearchState | dict[str, Any]] = {}


def _utc_now() -> datetime:
    """Return the current time as a timezone-aware UTC datetime."""
    return datetime.now(UTC)


def _ensure_utc(dt: datetime) -> datetime:
    """Normalize datetimes to timezone-aware UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def get_export_manager() -> type[ExportManager] | ExportManager:
    """Provide an export manager factory for dependency overrides in tests."""
    return ExportManager


def _get_active_state(search_id: str) -> ActiveSearchState:
    """Retrieve and normalize an active search state."""
    state_obj = active_searches.get(search_id)
    if state_obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search not found")

    if isinstance(state_obj, ActiveSearchState):
        return state_obj

    if isinstance(state_obj, dict):
        state = ActiveSearchState.from_mapping(state_obj)
        active_searches[search_id] = state
        return state

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Invalid search state"
    )


def _enforce_user_access(state: ActiveSearchState, current_user: dict[str, Any]) -> None:
    """Ensure the requesting user is allowed to access the search."""
    owner_id = state.user_id
    if not owner_id:
        return

    user_id = current_user.get("user_id")
    if user_id != owner_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


def _normalize_export_manager(factory: type[ExportManager] | ExportManager) -> ExportManager:
    """Instantiate an export manager from a factory or return the instance."""
    if callable(factory):
        return factory()
    return factory


def _collect_export_results(state: ActiveSearchState) -> list[SearchResult]:
    """Collect search results suitable for exporting."""
    results: list[SearchResult] = []

    if state.results:
        for item in state.results:
            if isinstance(item, SearchResult):
                results.append(item)
            elif isinstance(item, SearchResultResponse):
                try:
                    search_type = (
                        SearchType(item.search_type)
                        if isinstance(item.search_type, str)
                        else item.search_type
                    )
                except ValueError:
                    search_type = SearchType.CONTENT

                results.append(
                    SearchResult(
                        commit_hash=item.commit_hash,
                        file_path=Path(item.file_path),
                        line_number=item.line_number,
                        matching_line=item.matching_line,
                        commit_info=None,
                        search_type=search_type,
                        relevance_score=item.relevance_score,
                        match_context={"lines": item.match_context} if item.match_context else None,
                        search_time_ms=None,
                    )
                )
            elif isinstance(item, dict):
                payload = dict(item)
                if "file_path" in payload:
                    payload["file_path"] = Path(payload["file_path"])
                payload.setdefault("line_number", None)
                payload.setdefault("matching_line", None)
                payload.setdefault("search_type", SearchType.CONTENT)
                payload.setdefault("relevance_score", 0.0)
                payload.setdefault("commit_info", None)
                payload.setdefault("match_context", None)
                payload.setdefault("search_time_ms", None)
                try:
                    if isinstance(payload["search_type"], str):
                        payload["search_type"] = SearchType(payload["search_type"])
                    results.append(SearchResult(**payload))
                except Exception:
                    continue

    if not results and state.response:
        for entry in state.response.results:
            try:
                search_type = SearchType(entry.search_type)
            except ValueError:
                search_type = SearchType.CONTENT

            result = SearchResult(
                commit_hash=entry.commit_hash,
                file_path=Path(entry.file_path),
                line_number=entry.line_number,
                matching_line=entry.matching_line,
                commit_info=None,
                search_type=search_type,
                relevance_score=entry.relevance_score,
                match_context={"lines": entry.match_context} if entry.match_context else None,
                search_time_ms=None,
            )
            results.append(result)

    return results


def _build_search_response(execution: dict[str, Any]) -> SearchResponse:
    """Create a SearchResponse model from execution data."""
    raw_results = execution.get("raw_results", [])
    parsed_results: list[SearchResultResponse] = []
    for item in execution.get("results", []):
        if isinstance(item, SearchResultResponse):
            parsed_results.append(item)
        elif isinstance(item, SearchResult):
            parsed_results.append(SearchResultResponse.from_search_result(item))
        elif isinstance(item, dict):
            parsed_results.append(SearchResultResponse(**item))
    if not parsed_results and raw_results:
        parsed_results = [SearchResultResponse.from_search_result(result) for result in raw_results]

    return SearchResponse(
        results=parsed_results,
        total_count=execution.get("total_count", len(parsed_results)),
        search_id=execution.get("search_id", str(uuid.uuid4())),
        status=execution.get("status", "completed"),
        commits_searched=execution.get("commits_searched", 0),
        files_searched=execution.get("files_searched", 0),
        search_duration_ms=execution.get("search_duration_ms", 0.0),
        error_message=execution.get("error_message"),
        has_more=execution.get("has_more", False),
        next_page_token=execution.get("next_page_token"),
        query_info=execution.get("query_info", {}),
        filters_applied=execution.get("filters_applied", {}),
    )


def _update_state_from_execution(
    search_id: str,
    execution: dict[str, Any],
    orchestrator: SearchOrchestrator,
    user_id: str | None,
) -> ActiveSearchState:
    """Persist execution results into the active search registry."""
    state = active_searches.get(search_id)
    if not isinstance(state, ActiveSearchState):
        state = ActiveSearchState(id=search_id, user_id=user_id)
    state.status = execution.get("status", "completed")
    state.progress = 1.0 if state.status == "completed" else state.progress
    state.message = execution.get("message", state.message)
    state.request = execution.get("request", state.request)
    state.started_at = state.started_at or _utc_now()
    state.completed_at = _utc_now()

    raw_results = execution.get("raw_results")
    if isinstance(raw_results, list):
        normalized: list[SearchResult] = []
        for item in raw_results:
            if isinstance(item, SearchResult):
                normalized.append(item)
            elif isinstance(item, dict):
                payload = dict(item)
                if "file_path" in payload:
                    payload["file_path"] = Path(payload["file_path"])
                payload.setdefault("line_number", None)
                payload.setdefault("matching_line", None)
                payload.setdefault("search_type", SearchType.CONTENT)
                payload.setdefault("relevance_score", 0.0)
                payload.setdefault("commit_info", None)
                payload.setdefault("match_context", None)
                payload.setdefault("search_time_ms", None)
                try:
                    if isinstance(payload["search_type"], str):
                        payload["search_type"] = SearchType(payload["search_type"])
                    normalized.append(SearchResult(**payload))
                except Exception:
                    continue
        if normalized:
            state.update_results(normalized)

    response_model = _build_search_response(execution)
    state.set_response(response_model)

    metrics_obj = getattr(orchestrator, "metrics", None)
    if isinstance(metrics_obj, SearchMetrics):
        state.metrics = metrics_obj

    active_searches[search_id] = state
    return state


# Enhanced Search Models
class AdvancedSearchRequest(BaseModel):
    """Advanced search request with comprehensive options."""

    model_config = ConfigDict(extra="allow")

    # Repository settings
    repo_path: str = Field(..., description="Path to the Git repository")
    branch: str | None = Field(None, description="Branch to search")

    # Multi-modal search criteria
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
    regex_mode: bool = Field(False, description="Interpret patterns as regular expressions")
    fuzzy_search: bool = Field(False, description="Enable fuzzy matching")
    fuzzy_threshold: float = Field(0.8, ge=0.0, le=1.0, description="Fuzzy match threshold")
    include_globs: list[str] | None = Field(None, description="Include file patterns")
    exclude_globs: list[str] | None = Field(None, description="Exclude file patterns")

    # Performance and limits
    max_results: int | None = Field(1000, ge=1, le=10000, description="Maximum number of results")
    max_file_size: int | None = Field(None, description="Maximum file size in bytes")
    timeout_seconds: int = Field(300, ge=10, le=3600, description="Search timeout in seconds")

    # Result formatting
    include_context: bool = Field(True, description="Include surrounding context lines")
    context_lines: int = Field(3, ge=0, le=20, description="Number of context lines")
    include_metadata: bool = Field(True, description="Include commit metadata")

    # Historical search options
    search_history: bool = Field(False, description="Search across entire repository history")
    max_commits: int | None = Field(None, description="Maximum commits to search in history mode")


class SearchFilters(BaseModel):
    """Additional search filters."""

    model_config = ConfigDict(extra="ignore")

    min_commit_size: int | None = Field(None, description="Minimum commit size")
    max_commit_size: int | None = Field(None, description="Maximum commit size")
    merge_commits_only: bool = Field(False, description="Search only merge commits")
    exclude_merge_commits: bool = Field(False, description="Exclude merge commits")
    binary_files: bool = Field(False, description="Include binary files")


class AdvancedSearchPayload(BaseModel):
    """Request payload wrapper supporting legacy body formats."""

    search_request: AdvancedSearchRequest | None = Field(None, description="Search options")
    filters: SearchFilters | None = Field(None, description="Additional filters")

    model_config = ConfigDict(extra="allow")

    @model_validator(mode="before")
    @classmethod
    def harmonize_payload(cls, data: Any) -> Any:
        """Normalize legacy payloads where search fields are at the root."""
        if not isinstance(data, dict):
            return data

        if "search_request" in data:
            return data

        # Treat top-level keys as the search definition, reserving "filters" if present.
        search_data = {key: value for key, value in data.items() if key != "filters"}
        filters_data = data.get("filters")

        normalized: dict[str, Any] = {
            "search_request": search_data or None,
            "filters": filters_data,
        }
        return normalized


# Search Endpoints


@router.post("/advanced", response_model=SearchResponse)
@limiter.limit("10/minute")
async def advanced_search(
    request: Request,
    background_tasks: BackgroundTasks,
    payload: AdvancedSearchPayload = Body(..., embed=False),
    current_user: dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id),
) -> SearchResponse:
    """
    Perform advanced multi-modal search with comprehensive options.

    Supports content, author, message, date range, and file pattern searches
    with fuzzy matching and historical search capabilities.
    """
    try:
        search_request = payload.search_request
        if search_request is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Search request is required",
            )

        filters = payload.filters

        await validate_repo_path(search_request.repo_path)

        orchestrator = create_search_orchestrator()
        search_query = _convert_to_search_query(search_request, filters)

        max_commits_limit = search_request.max_commits or 0
        is_background = (
            search_request.search_history
            or search_request.timeout_seconds >= 600
            or max_commits_limit >= 1000
        )

        if is_background and background_tasks:
            search_id = str(uuid.uuid4())
            state = ActiveSearchState(
                id=search_id,
                status="queued",
                progress=0.0,
                message="Search queued",
                request=search_request,
                user_id=current_user.get("user_id"),
                started_at=_utc_now(),
            )
            active_searches[search_id] = state

            background_tasks.add_task(
                perform_advanced_search,
                search_id,
                orchestrator,
                search_query,
                search_request.repo_path,
                current_user.get("user_id"),
                search_request,
            )

            return SearchResponse(
                results=[],
                total_count=0,
                search_id=search_id,
                status="started",
                commits_searched=0,
                files_searched=0,
                search_duration_ms=0.0,
                error_message=None,
                has_more=False,
                next_page_token=None,
                query_info={"mode": "background"},
                filters_applied=filters.model_dump(exclude_none=True) if filters else {},
            )

        execution = await perform_advanced_search_sync(
            orchestrator, search_query, search_request.repo_path
        )
        return _build_search_response(execution)

    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {exc}",
        ) from exc


@router.get("/fuzzy", response_model=SearchResponse)
@limiter.limit("15/minute")
async def fuzzy_search(
    request: Request,
    repo_path: str = Query(..., description="Repository path"),
    pattern: str = Query(..., description="Search pattern"),
    threshold: float = Query(0.8, ge=0.0, le=1.0, description="Similarity threshold"),
    max_distance: int = Query(2, ge=1, le=10, description="Maximum edit distance"),
    file_types: list[str] | None = Query(None, description="File types to search"),
    current_user: dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id),
) -> SearchResponse:
    """
    Perform fuzzy search with configurable similarity thresholds.

    Uses approximate string matching to find similar content even
    with typos or variations.
    """
    try:
        await validate_repo_path(repo_path)

        search_request = AdvancedSearchRequest.model_validate(
            {
                "repo_path": repo_path,
                "content_pattern": pattern,
                "fuzzy_search": True,
                "fuzzy_threshold": threshold,
                "file_extensions": file_types,
                "max_results": 1000,
            }
        )

        orchestrator = create_search_orchestrator()
        search_query = _convert_to_search_query(search_request, None)

        execution = await perform_advanced_search_sync(orchestrator, search_query, repo_path)
        return _build_search_response(execution)

    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fuzzy search failed: {exc}",
        ) from exc


@router.get("/historical", response_model=SearchResponse)
@limiter.limit("5/minute")
async def historical_search(
    request: Request,
    background_tasks: BackgroundTasks,
    repo_path: str = Query(..., description="Repository path"),
    pattern: str = Query(..., description="Search pattern"),
    max_commits: int = Query(1000, ge=10, le=10000, description="Maximum commits to search"),
    date_from: datetime | None = Query(None, description="Start date"),
    date_to: datetime | None = Query(None, description="End date"),
    current_user: dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id),
) -> SearchResponse:
    """
    Search across entire repository history timeline.

    Searches through historical commits to find when specific
    content was added, modified, or removed.
    """
    try:
        await validate_repo_path(repo_path)

        payload = {
            "repo_path": repo_path,
            "content_pattern": pattern,
            "search_history": True,
            "max_commits": max_commits,
            "date_from": date_from,
            "date_to": date_to,
            "timeout_seconds": 300,
        }
        search_request = AdvancedSearchRequest.model_validate(payload)
        orchestrator = create_search_orchestrator()
        max_commits_limit = max_commits
        is_background = max_commits_limit >= 1000
        if is_background and background_tasks:
            background_request = search_request.model_copy(update={"timeout_seconds": 600})
            search_query = _convert_to_search_query(background_request, None)
            search_id = str(uuid.uuid4())
            state = ActiveSearchState(
                id=search_id,
                status="queued",
                progress=0.0,
                message="Historical search queued",
                request=background_request,
                user_id=current_user.get("user_id"),
                started_at=_utc_now(),
            )
            active_searches[search_id] = state

            background_tasks.add_task(
                perform_advanced_search,
                search_id,
                orchestrator,
                search_query,
                repo_path,
                current_user.get("user_id"),
                background_request,
            )

            return SearchResponse(
                results=[],
                total_count=0,
                search_id=search_id,
                status="started",
                commits_searched=0,
                files_searched=0,
                search_duration_ms=0.0,
                error_message=None,
                has_more=False,
                next_page_token=None,
                query_info={"mode": "background", "search_history": True},
                filters_applied={},
            )

        # Fallback to synchronous execution with reduced scope
        reduced_request = search_request.model_copy(update={"max_commits": min(max_commits, 100)})
        search_query = _convert_to_search_query(reduced_request, None)
        execution = await perform_advanced_search_sync(orchestrator, search_query, repo_path)
        return _build_search_response(execution)

    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Historical search failed: {exc}",
        ) from exc


@router.get("/{search_id}/status", response_model=SearchStatusResponse)
@limiter.limit("30/minute")
async def get_search_status_endpoint(
    request: Request,
    search_id: str,
    current_user: dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id),
) -> SearchStatusResponse:
    """Retrieve status information for an active search."""
    state = _get_active_state(search_id)
    _enforce_user_access(state, current_user)

    payload = state.to_status_payload()
    if request_id:
        payload["request_id"] = request_id

    elapsed_seconds = 0.0
    normalized_started: datetime | None = None
    if state.started_at:
        normalized_started = _ensure_utc(state.started_at)
        end_time = _ensure_utc(state.completed_at) if state.completed_at else _utc_now()
        elapsed_seconds = max((end_time - normalized_started).total_seconds(), 0.0)

    return SearchStatusResponse(
        search_id=state.id,
        status=state.status,
        progress=state.progress,
        message=payload.get("message", state.message),
        commits_searched=payload.get("commits_searched", 0),
        files_searched=payload.get("files_searched", 0),
        results_found=payload.get("results_count", state.results_count),
        started_at=normalized_started or state.started_at,
        estimated_completion=None,
        elapsed_seconds=elapsed_seconds,
        error_message=state.error,
    )


@router.get("/{search_id}/results")
@limiter.limit("30/minute")
async def get_search_results_endpoint(
    request: Request,
    search_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    current_user: dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id),
) -> JSONResponse:
    """Return paginated results for a completed search."""
    state = _get_active_state(search_id)
    _enforce_user_access(state, current_user)

    if state.status not in {"completed", "error"} and state.response is None:
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "detail": "Search is still running",
                "search_id": search_id,
                "request_id": request_id,
            },
        )

    payload = state.to_results_payload(page, page_size)
    payload["request_id"] = request_id
    return JSONResponse(content=payload)


@router.delete("/{search_id}", response_model=ApiResponse)
@limiter.limit("20/minute")
async def cancel_search_endpoint(
    request: Request,
    search_id: str,
    current_user: dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id),
) -> ApiResponse:
    """Cancel a running search if possible."""
    state = _get_active_state(search_id)
    _enforce_user_access(state, current_user)

    if state.status == "completed":
        return ApiResponse(
            success=True,
            message="Search already completed",
            data={"status": "completed", "search_id": search_id},
            request_id=request_id,
        )

    state.status = "cancelled"
    state.progress = 1.0
    state.message = "Search cancelled"
    state.completed_at = _utc_now()
    active_searches[search_id] = state

    return ApiResponse(
        success=True,
        message="Search cancelled successfully",
        data={"status": "cancelled", "search_id": search_id},
        request_id=request_id,
    )


@router.get("/active", response_model=ApiResponse)
@limiter.limit("20/minute")
async def list_active_searches(
    request: Request,
    current_user: dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id),
) -> ApiResponse:
    """List searches currently tracked by the service."""
    searches: list[dict[str, Any]] = []
    for search_id, value in list(active_searches.items()):
        state = _get_active_state(search_id)
        if state.user_id and state.user_id != current_user.get("user_id"):
            continue
        searches.append(state.to_status_payload())

    return ApiResponse(
        success=True,
        message="Active searches retrieved",
        data={"searches": searches, "total_count": len(searches)},
        request_id=request_id,
    )


@router.post("/{search_id}/export")
@limiter.limit("10/minute")
async def export_search_results_endpoint(
    request: Request,
    search_id: str,
    export_request: ExportRequest,
    current_user: dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id),
) -> FileResponse:
    """Export results for a completed search."""
    state = _get_active_state(search_id)
    _enforce_user_access(state, current_user)

    results = _collect_export_results(state)
    if not results:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No results to export")

    export_manager = _normalize_export_manager(get_export_manager())
    export_dir = Path.cwd() / "exports" / search_id
    export_dir.mkdir(parents=True, exist_ok=True)

    filename = export_request.filename or f"{search_id}.{export_request.format.value}"
    export_path = export_dir / filename

    if export_request.format == OutputFormat.JSON:
        export_manager.export_to_json(
            results, export_path, include_metadata=export_request.include_metadata
        )
        media_type = "application/json"
    elif export_request.format == OutputFormat.CSV:
        export_manager.export_to_csv(
            results, export_path, include_metadata=export_request.include_metadata
        )
        media_type = "text/csv"
    else:
        export_manager.export_to_text(results, export_path)
        media_type = "text/plain"

    state.extra["last_export_path"] = str(export_path)
    active_searches[search_id] = state

    response = FileResponse(path=export_path, filename=filename, media_type=media_type)
    if request_id:
        response.headers["X-Request-ID"] = request_id
    return response


# Helper functions and background execution


def _convert_to_search_query(
    request: AdvancedSearchRequest, filters: SearchFilters | None
) -> SearchQuery:
    """Convert search request to internal SearchQuery."""
    payload: dict[str, Any] = {
        "content_pattern": request.content_pattern,
        "commit_hash": request.commit_hash,
        "author_pattern": request.author_pattern,
        "message_pattern": request.message_pattern,
        "date_from": request.date_from,
        "date_to": request.date_to,
        "file_path_pattern": request.file_path_pattern,
        "file_extensions": request.file_extensions,
        "case_sensitive": request.case_sensitive,
        "fuzzy_search": request.fuzzy_search,
        "fuzzy_threshold": request.fuzzy_threshold,
        "include_globs": request.include_globs,
        "exclude_globs": request.exclude_globs,
        "max_file_size": request.max_file_size,
        "max_results": request.max_results,
        "timeout_seconds": request.timeout_seconds,
        "context_lines": request.context_lines,
    }

    if filters:
        if filters.min_commit_size is not None:
            payload["min_commit_size"] = filters.min_commit_size
        if filters.max_commit_size is not None:
            payload["max_commit_size"] = filters.max_commit_size

    return SearchQuery.model_validate(payload)


async def perform_advanced_search_sync(
    orchestrator: SearchOrchestrator, search_query: SearchQuery, repo_path: str
) -> dict[str, Any]:
    """Execute a synchronous search and return execution metadata."""
    start_time = _utc_now()
    raw_results: list[SearchResult] = []
    result_payload: list[dict[str, Any]] = []

    try:
        repo = get_repository(Path(repo_path))

        async for result in orchestrator.search(repo, search_query):
            raw_results.append(result)
            result_payload.append(SearchResultResponse.from_search_result(result).dict())

        metrics_obj = getattr(orchestrator, "metrics", None)
        if isinstance(metrics_obj, SearchMetrics):
            commits_searched = metrics_obj.total_commits_searched
            files_searched = metrics_obj.total_files_searched
            duration_ms = metrics_obj.search_duration_ms
        else:
            commits_searched = 0
            files_searched = 0
            duration_ms = (_utc_now() - start_time).total_seconds() * 1000

        return {
            "search_id": str(uuid.uuid4()),
            "status": "completed",
            "results": result_payload,
            "raw_results": raw_results,
            "total_count": len(raw_results),
            "commits_searched": commits_searched,
            "files_searched": files_searched,
            "search_duration_ms": duration_ms,
            "error_message": None,
            "has_more": False,
            "next_page_token": None,
            "query_info": {},
            "filters_applied": {},
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "search_id": str(uuid.uuid4()),
            "status": "error",
            "results": [],
            "raw_results": [],
            "total_count": 0,
            "commits_searched": 0,
            "files_searched": 0,
            "search_duration_ms": (_utc_now() - start_time).total_seconds() * 1000,
            "error_message": str(exc),
            "has_more": False,
            "next_page_token": None,
            "query_info": {},
            "filters_applied": {},
        }


async def perform_advanced_search(
    search_id: str,
    orchestrator: SearchOrchestrator,
    search_query: SearchQuery,
    repo_path: str,
    user_id: str | None,
    original_request: AdvancedSearchRequest | None = None,
) -> None:
    """Execute a search in the background and update tracking state."""
    state = active_searches.get(search_id)
    if not isinstance(state, ActiveSearchState):
        state = ActiveSearchState(id=search_id, status="running", user_id=user_id)
    state.status = "running"
    state.started_at = state.started_at or _utc_now()
    if original_request is not None:
        state.request = original_request
    active_searches[search_id] = state

    try:
        execution = await perform_advanced_search_sync(orchestrator, search_query, repo_path)
        execution["request"] = state.request or original_request
        _update_state_from_execution(search_id, execution, orchestrator, user_id)
    except Exception as exc:  # noqa: BLE001
        state = active_searches.get(search_id)
        if isinstance(state, ActiveSearchState):
            state.status = "error"
            state.error = str(exc)
            state.completed_at = _utc_now()
            state.set_response(
                {
                    "search_id": search_id,
                    "status": "error",
                    "results": [],
                    "total_count": 0,
                    "commits_searched": 0,
                    "files_searched": 0,
                    "search_duration_ms": 0.0,
                    "error_message": str(exc),
                    "has_more": False,
                    "next_page_token": None,
                    "query_info": {},
                    "filters_applied": {},
                }
            )
            active_searches[search_id] = state


async def _perform_background_search(
    search_id: str,
    orchestrator: SearchOrchestrator,
    search_query: SearchQuery,
    repo_path: str,
    user_id: str | None = None,
    original_request: AdvancedSearchRequest | None = None,
) -> None:
    """Wrapper to execute background searches using the shared helper."""
    await perform_advanced_search(
        search_id,
        orchestrator,
        search_query,
        repo_path,
        user_id,
        original_request=original_request,
    )
