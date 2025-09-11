"""
Consolidated search API for GitHound.

Provides comprehensive search capabilities including multi-modal search,
fuzzy matching, pattern-based queries, and historical code search.
"""

import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from pydantic import BaseModel, Field

from ...git_handler import get_repository
from ...models import SearchQuery, SearchResult
from ...search_engine import (
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
from ..core.search_orchestrator import create_search_orchestrator
from ..middleware.rate_limiting import get_limiter
from ..models.api_models import (
    SearchRequest,
    SearchResponse,
    SearchStatusResponse,
)
from ..services.auth_service import require_user
from ..utils.validation import get_request_id, validate_repo_path

# Create router
router = APIRouter(prefix="/api/search", tags=["search"])
limiter = get_limiter()


# Enhanced Search Models
class AdvancedSearchRequest(BaseModel):
    """Advanced search request with comprehensive options."""

    # Repository settings
    repo_path: str = Field(..., description="Path to the Git repository")
    branch: str | None = Field(None, description="Branch to search")

    # Multi-modal search criteria
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

    # Performance and limits
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

    # Historical search options
    search_history: bool = Field(
        False, description="Search across entire repository history")
    max_commits: int | None = Field(
        None, description="Maximum commits to search in history mode")


class SearchFilters(BaseModel):
    """Additional search filters."""
    min_commit_size: int | None = Field(
        None, description="Minimum commit size")
    max_commit_size: int | None = Field(
        None, description="Maximum commit size")
    merge_commits_only: bool = Field(
        False, description="Search only merge commits")
    exclude_merge_commits: bool = Field(
        False, description="Exclude merge commits")
    binary_files: bool = Field(False, description="Include binary files")


# Search Endpoints

@router.post("/advanced", response_model=SearchResponse)
@limiter.limit("10/minute")
async def advanced_search(
    request: Request,
    search_request: AdvancedSearchRequest,
    filters: SearchFilters | None = None,
    background_tasks: BackgroundTasks | None = None,
    current_user: dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id)
) -> SearchResponse:
    """
    Perform advanced multi-modal search with comprehensive options.
    
    Supports content, author, message, date range, and file pattern searches
    with fuzzy matching and historical search capabilities.
    """
    try:
        await validate_repo_path(search_request.repo_path)
        
        # Create search orchestrator
        orchestrator = create_search_orchestrator()
        
        # Convert to internal search query
        search_query = _convert_to_search_query(search_request, filters)
        
        # Determine if this should be a background search
        is_background = (
            search_request.search_history or
            search_request.timeout_seconds > 60 or
            (search_request.max_commits and search_request.max_commits > 100)
        )
        
        if is_background and background_tasks:
            # Start background search
            search_id = str(uuid.uuid4())
            background_tasks.add_task(
                _perform_background_search,
                search_id,
                orchestrator,
                search_query,
                search_request.repo_path
            )
            
            return SearchResponse(
                results=[],
                total_count=0,
                search_id=search_id,
                status="started",
                commits_searched=0,
                files_searched=0,
                search_duration_ms=0.0
            )
        else:
            # Perform synchronous search
            results = await _perform_sync_search(
                orchestrator,
                search_query,
                search_request.repo_path
            )
            
            return SearchResponse(
                results=results.get("results", []),
                total_count=results.get("total_count", 0),
                search_id=results.get("search_id", str(uuid.uuid4())),
                status="completed",
                commits_searched=results.get("commits_searched", 0),
                files_searched=results.get("files_searched", 0),
                search_duration_ms=results.get("search_duration_ms", 0.0)
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/fuzzy", response_model=SearchResponse)
@limiter.limit("15/minute")
async def fuzzy_search(
    request: Request,
    repo_path: str = Query(..., description="Repository path"),
    pattern: str = Query(..., description="Search pattern"),
    threshold: float = Query(
        0.8, ge=0.0, le=1.0, description="Similarity threshold"),
    max_distance: int = Query(
        2, ge=1, le=10, description="Maximum edit distance"),
    file_types: list[str] | None = Query(
        None, description="File types to search"),
    current_user: dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id)
) -> SearchResponse:
    """
    Perform fuzzy search with configurable similarity thresholds.
    
    Uses approximate string matching to find similar content even
    with typos or variations.
    """
    try:
        await validate_repo_path(repo_path)
        
        # Create fuzzy search request
        search_request = AdvancedSearchRequest(
            repo_path=repo_path,
            content_pattern=pattern,
            fuzzy_search=True,
            fuzzy_threshold=threshold,
            file_extensions=file_types,
            max_results=1000
        )
        
        # Perform search
        orchestrator = create_search_orchestrator()
        search_query = _convert_to_search_query(search_request, None)
        
        results = await _perform_sync_search(
            orchestrator,
            search_query,
            repo_path
        )
        
        return SearchResponse(
            results=results.get("results", []),
            total_count=results.get("total_count", 0),
            search_id=results.get("search_id", str(uuid.uuid4())),
            status="completed",
            commits_searched=results.get("commits_searched", 0),
            files_searched=results.get("files_searched", 0),
            search_duration_ms=results.get("search_duration_ms", 0.0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fuzzy search failed: {str(e)}"
        )


@router.get("/historical", response_model=SearchResponse)
@limiter.limit("5/minute")
async def historical_search(
    request: Request,
    repo_path: str = Query(..., description="Repository path"),
    pattern: str = Query(..., description="Search pattern"),
    max_commits: int = Query(1000, ge=10, le=10000,
                             description="Maximum commits to search"),
    date_from: datetime | None = Query(None, description="Start date"),
    date_to: datetime | None = Query(None, description="End date"),
    background_tasks: BackgroundTasks | None = None,
    current_user: dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id)
) -> SearchResponse:
    """
    Search across entire repository history timeline.
    
    Searches through historical commits to find when specific
    content was added, modified, or removed.
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
            timeout_seconds=600  # Longer timeout for historical searches
        )
        
        # Always use background processing for historical searches
        if background_tasks:
            search_id = str(uuid.uuid4())
            orchestrator = create_search_orchestrator()
            search_query = _convert_to_search_query(search_request, None)
            
            background_tasks.add_task(
                _perform_background_search,
                search_id,
                orchestrator,
                search_query,
                repo_path
            )
            
            return SearchResponse(
                results=[],
                total_count=0,
                search_id=search_id,
                status="started",
                commits_searched=0,
                files_searched=0,
                search_duration_ms=0.0
            )
        else:
            # Fallback to sync search with reduced scope
            search_request.max_commits = min(max_commits, 100)
            orchestrator = create_search_orchestrator()
            search_query = _convert_to_search_query(search_request, None)
            
            results = await _perform_sync_search(
                orchestrator,
                search_query,
                repo_path
            )
            
            return SearchResponse(
                results=results.get("results", []),
                total_count=results.get("total_count", 0),
                search_id=results.get("search_id", str(uuid.uuid4())),
                status="completed",
                commits_searched=results.get("commits_searched", 0),
                files_searched=results.get("files_searched", 0),
                search_duration_ms=results.get("search_duration_ms", 0.0)
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Historical search failed: {str(e)}"
        )


# Helper functions

def _convert_to_search_query(
    request: AdvancedSearchRequest,
    filters: SearchFilters | None
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
        merge_commits_only=filters.merge_commits_only if filters else False,
        exclude_merge_commits=filters.exclude_merge_commits if filters else False,
        binary_files=filters.binary_files if filters else False,
    )


async def _perform_sync_search(
    orchestrator: SearchOrchestrator,
    search_query: SearchQuery,
    repo_path: str
) -> dict[str, Any]:
    """Perform synchronous search operation."""
    start_time = datetime.now()
    
    try:
        repo = get_repository(Path(repo_path))
        results = orchestrator.search(repo, search_query)
        
        search_duration = (datetime.now() - start_time).total_seconds() * 1000
        
        return {
            "search_id": str(uuid.uuid4()),
            "status": "completed",
            "results": [result.dict() if hasattr(result, 'dict') else result for result in results],
            "total_count": len(results),
            "commits_searched": getattr(orchestrator, 'commits_searched', 0),
            "files_searched": getattr(orchestrator, 'files_searched', 0),
            "search_duration_ms": search_duration,
        }
    except Exception as e:
        return {
            "search_id": str(uuid.uuid4()),
            "status": "error",
            "results": [],
            "total_count": 0,
            "commits_searched": 0,
            "files_searched": 0,
            "search_duration_ms": (datetime.now() - start_time).total_seconds() * 1000,
            "error_message": str(e)
        }


async def _perform_background_search(
    search_id: str,
    orchestrator: SearchOrchestrator,
    search_query: SearchQuery,
    repo_path: str
) -> None:
    """Perform background search operation."""
    # This would integrate with the WebSocket system for real-time updates
    # Implementation would depend on the existing background task system
    pass
