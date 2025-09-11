"""
Enhanced search API for GitHound.

Provides comprehensive search capabilities including multi-modal search,
fuzzy matching, pattern-based queries, and historical code search.
"""

import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Dict, List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field

from ..git_handler import get_repository
from ..models import SearchQuery, SearchResult, SearchMetrics
from ..search_engine import (
    AuthorSearcher,
    CommitHashSearcher,
    ContentSearcher,
    DateRangeSearcher,
    FilePathSearcher,
    FileTypeSearcher,
    FuzzySearcher,
    MessageSearcher,
    SearchOrchestrator,
)
from .auth import require_user
from .comprehensive_api import ApiResponse, get_request_id, validate_repo_path
from .rate_limiting import get_limiter, search_rate_limit_dependency
from .websocket import connection_manager

# Create router
router = APIRouter(prefix="/api/v3/search", tags=["search"])
limiter = get_limiter()

# Global state for search operations
active_searches: Dict[str, Dict[str, Any]] = {}


# Enhanced Search Models
class AdvancedSearchRequest(BaseModel):
    """Advanced search request with comprehensive options."""
    
    # Repository settings
    repo_path: str = Field(..., description="Path to the Git repository")
    branch: Optional[str] = Field(None, description="Branch to search")
    
    # Multi-modal search criteria
    content_pattern: Optional[str] = Field(None, description="Content pattern to search for")
    commit_hash: Optional[str] = Field(None, description="Specific commit hash")
    author_pattern: Optional[str] = Field(None, description="Author name or email pattern")
    message_pattern: Optional[str] = Field(None, description="Commit message pattern")
    
    # Date and time filtering
    date_from: Optional[datetime] = Field(None, description="Search from this date")
    date_to: Optional[datetime] = Field(None, description="Search until this date")
    
    # File and path filtering
    file_path_pattern: Optional[str] = Field(None, description="File path pattern")
    file_extensions: Optional[List[str]] = Field(None, description="File extensions to include")
    include_globs: Optional[List[str]] = Field(None, description="Glob patterns to include")
    exclude_globs: Optional[List[str]] = Field(None, description="Glob patterns to exclude")
    
    # Search behavior and options
    case_sensitive: bool = Field(False, description="Case-sensitive search")
    regex_mode: bool = Field(False, description="Use regular expressions")
    whole_words: bool = Field(False, description="Match whole words only")
    
    # Fuzzy search options
    fuzzy_search: bool = Field(False, description="Enable fuzzy matching")
    fuzzy_threshold: float = Field(0.8, ge=0.0, le=1.0, description="Fuzzy matching threshold")
    fuzzy_max_distance: int = Field(2, ge=1, le=10, description="Maximum edit distance for fuzzy search")
    
    # Performance and limits
    max_results: Optional[int] = Field(1000, ge=1, le=10000, description="Maximum number of results")
    max_file_size: Optional[int] = Field(None, description="Maximum file size in bytes")
    timeout_seconds: int = Field(300, ge=10, le=3600, description="Search timeout in seconds")
    
    # Result formatting
    include_context: bool = Field(True, description="Include surrounding context lines")
    context_lines: int = Field(3, ge=0, le=20, description="Number of context lines")
    include_metadata: bool = Field(True, description="Include commit metadata")
    
    # Historical search options
    search_history: bool = Field(False, description="Search across entire repository history")
    max_commits: Optional[int] = Field(None, description="Maximum commits to search in history mode")


class SearchFilters(BaseModel):
    """Additional search filters."""
    min_commit_size: Optional[int] = Field(None, description="Minimum commit size")
    max_commit_size: Optional[int] = Field(None, description="Maximum commit size")
    merge_commits_only: bool = Field(False, description="Search only merge commits")
    exclude_merge_commits: bool = Field(False, description="Exclude merge commits")
    binary_files: bool = Field(False, description="Include binary files")


class SearchResponse(BaseModel):
    """Enhanced search response."""
    search_id: str = Field(..., description="Unique search identifier")
    status: str = Field(..., description="Search status")
    results: List[Dict[str, Any]] = Field(..., description="Search results")
    total_count: int = Field(..., description="Total number of results")
    
    # Search metrics
    commits_searched: int = Field(0, description="Number of commits searched")
    files_searched: int = Field(0, description="Number of files searched")
    search_duration_ms: float = Field(0.0, description="Search duration in milliseconds")
    
    # Search metadata
    query_info: Dict[str, Any] = Field(..., description="Query information")
    filters_applied: Dict[str, Any] = Field(..., description="Applied filters")
    
    # Pagination info
    page: Optional[int] = Field(None, description="Current page")
    page_size: Optional[int] = Field(None, description="Page size")
    has_more: bool = Field(False, description="More results available")


class SearchStatusResponse(BaseModel):
    """Search status response."""
    search_id: str = Field(..., description="Search identifier")
    status: str = Field(..., description="Current status")
    progress: float = Field(..., ge=0.0, le=1.0, description="Progress percentage")
    message: str = Field(..., description="Current status message")
    results_count: int = Field(0, description="Number of results found so far")
    started_at: datetime = Field(..., description="Search start time")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")


# Search orchestrator setup
def create_enhanced_search_orchestrator() -> SearchOrchestrator:
    """Create and configure an enhanced search orchestrator."""
    orchestrator = SearchOrchestrator()
    
    # Register all available searchers
    orchestrator.register_searcher(CommitHashSearcher())
    orchestrator.register_searcher(AuthorSearcher())
    orchestrator.register_searcher(MessageSearcher())
    orchestrator.register_searcher(DateRangeSearcher())
    orchestrator.register_searcher(FilePathSearcher())
    orchestrator.register_searcher(FileTypeSearcher())
    orchestrator.register_searcher(ContentSearcher())
    orchestrator.register_searcher(FuzzySearcher())
    
    return orchestrator


# Search Endpoints

@router.post("/advanced", response_model=SearchResponse)
@limiter.limit("10/minute")
async def advanced_search(
    request: Request,
    search_request: AdvancedSearchRequest,
    filters: Optional[SearchFilters] = None,
    background_tasks: Optional[BackgroundTasks] = None,
    current_user: Dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id)
) -> SearchResponse:
    """
    Perform advanced multi-modal search with comprehensive options.
    
    Supports content search, author filtering, date ranges, file patterns,
    fuzzy matching, and historical code search across repository timeline.
    """
    try:
        # Validate repository
        await validate_repo_path(search_request.repo_path)
        
        # Generate unique search ID
        search_id = str(uuid.uuid4())
        
        # Initialize search state
        search_state = {
            "id": search_id,
            "status": "starting",
            "progress": 0.0,
            "message": "Search queued",
            "results_count": 0,
            "started_at": datetime.now(),
            "user_id": current_user["user_id"],
            "request": search_request,
            "filters": filters
        }
        active_searches[search_id] = search_state
        
        # Start search in background if requested
        if background_tasks:
            background_tasks.add_task(
                perform_advanced_search,
                search_id,
                search_request,
                filters,
                current_user["user_id"]
            )
            
            return SearchResponse(
                search_id=search_id,
                status="started",
                results=[],
                total_count=0,
                query_info=_build_query_info(search_request),
                filters_applied=_build_filters_info(filters),
                has_more=False
            )
        else:
            # Perform synchronous search
            return await perform_advanced_search_sync(
                search_id,
                search_request,
                filters,
                current_user["user_id"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start search: {str(e)}"
        )


@router.get("/fuzzy", response_model=SearchResponse)
@limiter.limit("15/minute")
async def fuzzy_search(
    request: Request,
    repo_path: str = Query(..., description="Repository path"),
    pattern: str = Query(..., description="Search pattern"),
    threshold: float = Query(0.8, ge=0.0, le=1.0, description="Similarity threshold"),
    max_distance: int = Query(2, ge=1, le=10, description="Maximum edit distance"),
    file_types: Optional[List[str]] = Query(None, description="File types to search"),
    current_user: Dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id)
) -> SearchResponse:
    """
    Perform fuzzy search with configurable similarity thresholds.
    
    Uses approximate string matching to find similar patterns
    even with typos or variations.
    """
    try:
        await validate_repo_path(repo_path)
        
        # Create fuzzy search request
        search_request = AdvancedSearchRequest(
            repo_path=repo_path,
            content_pattern=pattern,
            fuzzy_search=True,
            fuzzy_threshold=threshold,
            fuzzy_max_distance=max_distance,
            file_extensions=file_types,
            max_results=500
        )
        
        # Perform search
        search_id = str(uuid.uuid4())
        return await perform_advanced_search_sync(
            search_id,
            search_request,
            None,
            current_user["user_id"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform fuzzy search: {str(e)}"
        )


@router.get("/historical", response_model=SearchResponse)
@limiter.limit("5/minute")
async def historical_search(
    request: Request,
    repo_path: str = Query(..., description="Repository path"),
    pattern: str = Query(..., description="Search pattern"),
    max_commits: int = Query(1000, ge=10, le=10000, description="Maximum commits to search"),
    date_from: Optional[datetime] = Query(None, description="Start date"),
    date_to: Optional[datetime] = Query(None, description="End date"),
    background_tasks: Optional[BackgroundTasks] = None,
    current_user: Dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id)
) -> SearchResponse:
    """
    Search across entire repository history timeline.
    
    Performs deep historical search across all commits in the repository,
    useful for finding when code was introduced or removed.
    """
    try:
        await validate_repo_path(repo_path)
        
        # Create historical search request
        search_request = AdvancedSearchRequest(
            repo_path=repo_path,
            content_pattern=pattern,
            search_history=True,
            max_commits=max_commits,
            date_from=date_from,
            date_to=date_to,
            timeout_seconds=600  # Longer timeout for historical search
        )
        
        search_id = str(uuid.uuid4())
        
        if background_tasks:
            # Start background search for historical queries
            active_searches[search_id] = {
                "id": search_id,
                "status": "starting",
                "progress": 0.0,
                "message": "Historical search queued",
                "results_count": 0,
                "started_at": datetime.now(),
                "user_id": current_user["user_id"],
                "request": search_request
            }
            
            background_tasks.add_task(
                perform_advanced_search,
                search_id,
                search_request,
                None,
                current_user["user_id"]
            )
            
            return SearchResponse(
                search_id=search_id,
                status="started",
                results=[],
                total_count=0,
                query_info=_build_query_info(search_request),
                filters_applied={},
                has_more=False
            )
        else:
            return await perform_advanced_search_sync(
                search_id,
                search_request,
                None,
                current_user["user_id"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start historical search: {str(e)}"
        )


# Search Status and Management Endpoints

@router.get("/{search_id}/status", response_model=SearchStatusResponse)
@limiter.limit("60/minute")
async def get_search_status(
    request: Request,
    search_id: str,
    current_user: Dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id)
) -> SearchStatusResponse:
    """Get the status of a running or completed search."""
    if search_id not in active_searches:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Search not found"
        )

    search_state = active_searches[search_id]

    # Check if user has access to this search
    if search_state["user_id"] != current_user["user_id"] and "admin" not in current_user.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this search"
        )

    return SearchStatusResponse(
        search_id=search_id,
        status=search_state["status"],
        progress=search_state["progress"],
        message=search_state["message"],
        results_count=search_state["results_count"],
        started_at=search_state["started_at"],
        estimated_completion=search_state.get("estimated_completion")
    )


@router.get("/{search_id}/results", response_model=SearchResponse)
@limiter.limit("30/minute")
async def get_search_results(
    request: Request,
    search_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=1000, description="Results per page"),
    current_user: Dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id)
) -> SearchResponse:
    """Get results from a completed search with pagination."""
    if search_id not in active_searches:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Search not found"
        )

    search_state = active_searches[search_id]

    # Check access
    if search_state["user_id"] != current_user["user_id"] and "admin" not in current_user.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this search"
        )

    if search_state["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=search_state.get("error", "Search failed")
        )

    if search_state["status"] != "completed":
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail="Search not yet completed"
        )

    # Get paginated results
    results = search_state.get("results", [])
    total_count = len(results)

    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_results = results[start_idx:end_idx]

    has_more = end_idx < total_count

    return SearchResponse(
        search_id=search_id,
        status=search_state["status"],
        results=paginated_results,
        total_count=total_count,
        commits_searched=search_state.get("commits_searched", 0),
        files_searched=search_state.get("files_searched", 0),
        search_duration_ms=search_state.get("search_duration_ms", 0.0),
        query_info=search_state.get("query_info", {}),
        filters_applied=search_state.get("filters_applied", {}),
        page=page,
        page_size=page_size,
        has_more=has_more
    )


@router.delete("/{search_id}")
@limiter.limit("30/minute")
async def cancel_search(
    request: Request,
    search_id: str,
    current_user: Dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id)
) -> ApiResponse:
    """Cancel a running search operation."""
    if search_id not in active_searches:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Search not found"
        )

    search_state = active_searches[search_id]

    # Check access
    if search_state["user_id"] != current_user["user_id"] and "admin" not in current_user.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this search"
        )

    if search_state["status"] in ["completed", "error", "cancelled"]:
        return ApiResponse(
            success=True,
            message=f"Search already {search_state['status']}",
            data={"search_id": search_id, "status": search_state["status"]},
            request_id=request_id
        )

    # Mark as cancelled
    search_state["status"] = "cancelled"
    search_state["message"] = "Search cancelled by user"

    return ApiResponse(
        success=True,
        message="Search cancelled successfully",
        data={"search_id": search_id, "status": "cancelled"},
        request_id=request_id
    )


@router.get("/active", response_model=ApiResponse)
@limiter.limit("30/minute")
async def list_active_searches(
    request: Request,
    current_user: Dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id)
) -> ApiResponse:
    """List all active searches for the current user."""
    user_searches: list[Any] = []

    for search_id, search_state in active_searches.items():
        # Show only user's own searches unless admin
        if (search_state["user_id"] == current_user["user_id"] or
            "admin" in current_user.get("roles", [])):

            user_searches.append({
                "search_id": search_id,
                "status": search_state["status"],
                "progress": search_state["progress"],
                "message": search_state["message"],
                "results_count": search_state["results_count"],
                "started_at": search_state["started_at"],
                "user_id": search_state["user_id"]
            })

    return ApiResponse(
        success=True,
        message=f"Retrieved {len(user_searches)} active searches",
        data={"searches": user_searches, "total_count": len(user_searches)},
        request_id=request_id
    )


# WebSocket endpoint for real-time search updates
@router.websocket("/{search_id}/ws")
async def search_websocket(websocket: WebSocket, search_id: str) -> None:
    """WebSocket endpoint for real-time search progress updates."""
    await connection_manager.connect(websocket, search_id)

    try:
        while True:
            # Keep connection alive and handle client messages
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                # Handle client messages if needed
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await connection_manager.send_personal_message(
                    websocket,
                    {"type": "ping", "timestamp": datetime.now().isoformat()}
                )
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
    except Exception as e:
        connection_manager.disconnect(websocket)


# Background Search Functions

async def perform_advanced_search(
    search_id: str,
    search_request: AdvancedSearchRequest,
    filters: Optional[SearchFilters],
    user_id: str
) -> None:
    """Perform advanced search in background task."""
    try:
        search_state = active_searches[search_id]
        search_state["status"] = "running"
        search_state["message"] = "Initializing search..."
        search_state["progress"] = 0.1

        # Validate repository
        repo_path = Path(search_request.repo_path)
        repo = get_repository(repo_path)

        # Create search orchestrator
        orchestrator = create_enhanced_search_orchestrator()

        # Convert request to search query
        query = _convert_to_search_query(search_request, filters)

        # Set up progress callback
        def progress_callback(message: str, progress: float) -> None:
            if search_id in active_searches:
                search_state = active_searches[search_id]
                search_state["progress"] = progress
                search_state["message"] = message

                # Broadcast progress via WebSocket
                asyncio.create_task(
                    connection_manager.broadcast_progress(
                        search_id, progress, message, search_state["results_count"]
                    )
                )

        # Perform search
        results: list[Any] = []
        search_state["message"] = "Searching repository..."

        async for result in orchestrator.search(
            repo=repo,
            query=query,
            branch=search_request.branch,
            progress_callback=progress_callback,
            max_results=search_request.max_results,
        ):
            results.append(result)
            search_state["results_count"] = len(results)

        # Get metrics
        metrics = orchestrator.metrics

        # Store results
        search_state["status"] = "completed"
        search_state["progress"] = 1.0
        search_state["message"] = f"Found {len(results)} results"
        search_state["results"] = [_format_search_result(r) for r in results]
        search_state["commits_searched"] = metrics.total_commits_searched if metrics else 0
        search_state["files_searched"] = metrics.total_files_searched if metrics else 0
        search_state["search_duration_ms"] = metrics.search_duration_ms if metrics else 0.0
        search_state["query_info"] = _build_query_info(search_request)
        search_state["filters_applied"] = _build_filters_info(filters)

        # Broadcast completion
        await connection_manager.broadcast_completion(search_id, "completed", len(results))

    except Exception as e:
        # Handle errors
        search_state = active_searches[search_id]
        search_state["status"] = "error"
        search_state["message"] = f"Search failed: {str(e)}"
        search_state["error"] = str(e)

        # Broadcast error
        await connection_manager.broadcast_error(search_id, str(e))


async def perform_advanced_search_sync(
    search_id: str,
    search_request: AdvancedSearchRequest,
    filters: Optional[SearchFilters],
    user_id: str
) -> SearchResponse:
    """Perform advanced search synchronously."""
    try:
        # Validate repository
        repo_path = Path(search_request.repo_path)
        repo = get_repository(repo_path)

        # Create search orchestrator
        orchestrator = create_enhanced_search_orchestrator()

        # Convert request to search query
        query = _convert_to_search_query(search_request, filters)

        # Perform search
        results: list[Any] = []
        async for result in orchestrator.search(
            repo=repo,
            query=query,
            branch=search_request.branch,
            max_results=search_request.max_results,
        ):
            results.append(result)

        # Get metrics
        metrics = orchestrator.metrics

        return SearchResponse(
            search_id=search_id,
            status="completed",
            results=[_format_search_result(r) for r in results],
            total_count=len(results),
            commits_searched=metrics.total_commits_searched if metrics else 0,
            files_searched=metrics.total_files_searched if metrics else 0,
            search_duration_ms=metrics.search_duration_ms if metrics else 0.0,
            query_info=_build_query_info(search_request),
            filters_applied=_build_filters_info(filters),
            has_more=False
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


# Helper Functions

def _convert_to_search_query(
    request: AdvancedSearchRequest,
    filters: Optional[SearchFilters]
) -> SearchQuery:
    """Convert search request to internal SearchQuery."""
    return SearchQuery(
        content_pattern=request.content_pattern,
        commit_hash=request.commit_hash,
        author_pattern=request.author_pattern,
        message_pattern=request.message_pattern,
        date_from=request.date_from,
        date_to=request.date_to,
        file_path_pattern=request.file_path_pattern,
        file_extensions=request.file_extensions,
        case_sensitive=request.case_sensitive,
        fuzzy_search=request.fuzzy_search,
        fuzzy_threshold=request.fuzzy_threshold,
        include_globs=request.include_globs,
        exclude_globs=request.exclude_globs,
        max_file_size=request.max_file_size,
        min_commit_size=filters.min_commit_size if filters else None,
        max_commit_size=filters.max_commit_size if filters else None,
    )


def _format_search_result(result: SearchResult) -> Dict[str, Any]:
    """Format search result for API response."""
    formatted = {
        "commit_hash": result.commit_hash,
        "file_path": str(result.file_path),
        "line_number": result.line_number,
        "matching_line": result.matching_line,
        "search_type": result.search_type.value,
        "relevance_score": result.relevance_score,
        "match_context": result.match_context
    }

    if result.commit_info:
        formatted["commit_info"] = {
            "author_name": result.commit_info.author_name,
            "author_email": result.commit_info.author_email,
            "date": result.commit_info.date.isoformat() if result.commit_info.date else None,
            "message": result.commit_info.message
        }

    return formatted


def _build_query_info(request: AdvancedSearchRequest) -> Dict[str, Any]:
    """Build query information for response."""
    return {
        "content_pattern": request.content_pattern,
        "author_pattern": request.author_pattern,
        "message_pattern": request.message_pattern,
        "file_path_pattern": request.file_path_pattern,
        "date_range": [request.date_from, request.date_to],
        "fuzzy_search": request.fuzzy_search,
        "fuzzy_threshold": request.fuzzy_threshold if request.fuzzy_search else None,
        "case_sensitive": request.case_sensitive,
        "search_history": request.search_history
    }


def _build_filters_info(filters: Optional[SearchFilters]) -> Dict[str, Any]:
    """Build filters information for response."""
    if not filters:
        return {}

    return {
        "min_commit_size": filters.min_commit_size,
        "max_commit_size": filters.max_commit_size,
        "merge_commits_only": filters.merge_commits_only,
        "exclude_merge_commits": filters.exclude_merge_commits,
        "binary_files": filters.binary_files
    }
