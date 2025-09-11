"""FastAPI application for GitHound web interface."""

from typing import TypedDict, Any
import asyncio
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from git import GitCommandError

from ..git_handler import get_repository
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
from ..utils import get_export_manager
from ..models import SearchMetrics, SearchResult
from .models import (
    ErrorResponse,
    ExportRequest,
    HealthResponse,
    SearchRequest,
    SearchResponse,
    SearchStatusResponse,
)
from .websocket import connection_manager, websocket_endpoint

from dataclasses import dataclass, field


@dataclass
class ActiveSearchState:
    id: str
    status: str = "starting"
    progress: float = 0.0
    message: str = ""
    results_count: int = 0
    started_at: datetime = field(default_factory=datetime.now)
    request: SearchRequest | None = None
    response: SearchResponse | None = None
    results: list[SearchResult] | None = None
    metrics: SearchMetrics | None = None
    error: str | None = None


# Global state for managing searches


class SearchListItem(TypedDict):
    search_id: str
    status: str
    progress: float
    message: str
    results_count: int
    started_at: datetime


active_searches: dict[str, ActiveSearchState] = {}
app_start_time = time.time()


# Create FastAPI app
app = FastAPI(
    title="GitHound API",
    description="Advanced Git history search API with multi-modal search capabilities",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


def create_search_orchestrator() -> SearchOrchestrator:
    """Create and configure a search orchestrator."""
    orchestrator = SearchOrchestrator()

    # Register all searchers
    orchestrator.register_searcher(CommitHashSearcher())
    orchestrator.register_searcher(AuthorSearcher())
    orchestrator.register_searcher(MessageSearcher())
    orchestrator.register_searcher(DateRangeSearcher())
    orchestrator.register_searcher(FilePathSearcher())
    orchestrator.register_searcher(FileTypeSearcher())
    orchestrator.register_searcher(ContentSearcher())
    orchestrator.register_searcher(FuzzySearcher())

    return orchestrator


async def perform_search(search_id: str, request: SearchRequest) -> None:
    """Perform search in background task."""
    try:
        # Update search status
        state = active_searches[search_id]
        state.status = "running"
        state.message = "Initializing search..."

        # Validate repository path
        repo_path = Path(request.repo_path)
        if not repo_path.exists():
            raise HTTPException(
                status_code=400, detail=f"Repository path does not exist: {repo_path}"
            )

        # Get repository
        try:
            repo = get_repository(repo_path)
        except GitCommandError as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid Git repository: {e}")

        # Create search orchestrator
        orchestrator = create_search_orchestrator()

        # Convert request to search query
        query = request.to_search_query()

        # Set up progress callback with WebSocket broadcasting
        def progress_callback(message: str, progress: float) -> None:
            if search_id in active_searches:
                state = active_searches[search_id]
                state.progress = progress
                state.message = message

                # Broadcast progress via WebSocket
                asyncio.create_task(
                    connection_manager.broadcast_progress(
                        search_id, progress, message, state.results_count
                    )
                )

        # Perform search
        results: list[Any] = []
        async for result in orchestrator.search(
            repo=repo,
            query=query,
            branch=request.branch,
            progress_callback=progress_callback,
            max_results=request.max_results,
        ):
            results.append(result)
            state.results_count = len(results)

        # Get metrics
        metrics = orchestrator.metrics

        # Create response
        response = SearchResponse.from_results(
            results=results,
            search_id=search_id,
            metrics=metrics,
            include_metadata=True,
            status="completed",
        )

        # Store results
        state = active_searches[search_id]
        state.status = "completed"
        state.progress = 1.0
        state.message = f"Found {len(results)} results"
        state.response = response
        state.results = results
        state.metrics = metrics

        # Broadcast completion via WebSocket
        await connection_manager.broadcast_completion(search_id, "completed", len(results))

    except Exception as e:
        # Handle errors
        error_message = str(e)
        state = active_searches[search_id]
        state.status = "error"
        state.message = error_message
        state.error = error_message

        # Broadcast error via WebSocket
        await connection_manager.broadcast_error(search_id, error_message)


@app.get("/", response_class=HTMLResponse, response_model=None)
async def root() -> Response | str:
    """Serve the main web interface."""
    static_path = Path(__file__).parent / "static" / "index.html"
    if static_path.exists():
        return FileResponse(static_path)
    else:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>GitHound - Git History Search</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 800px; margin: 0 auto; }
                h1 { color: #333; }
                .info { background: #f0f8ff; padding: 20px; border-radius: 5px; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🐕 GitHound Web Interface</h1>
                <div class="info">
                    <h3>Welcome to GitHound!</h3>
                    <p>GitHound is an advanced Git history search tool with multi-modal search capabilities.</p>
                    <h4>Available Endpoints:</h4>
                    <ul>
                        <li><a href="/api/docs">📚 API Documentation (Swagger)</a></li>
                        <li><a href="/api/redoc">📖 API Documentation (ReDoc)</a></li>
                        <li><a href="/health">💚 Health Check</a></li>
                    </ul>
                    <h4>Quick Start:</h4>
                    <p>Use the API documentation to explore available endpoints and test search functionality.</p>
                </div>
            </div>
        </body>
        </html>
        """


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    uptime = time.time() - app_start_time
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        uptime_seconds=uptime,
        active_searches=len(active_searches),
    )


@app.post("/api/search", response_model=SearchResponse)
async def start_search(request: SearchRequest, background_tasks: BackgroundTasks) -> SearchResponse:
    """Start a new search operation."""
    # Generate unique search ID
    search_id = str(uuid.uuid4())

    # Initialize search state
    active_searches[search_id] = ActiveSearchState(
        id=search_id,
        status="starting",
        progress=0.0,
        message="Search queued",
        results_count=0,
        started_at=datetime.now(),
        request=request,
    )

    # Start search in background
    background_tasks.add_task(perform_search, search_id, request)

    # Return immediate response with search ID
    return SearchResponse(
        results=[],
        total_count=0,
        search_id=search_id,
        status="started",
        commits_searched=0,
        files_searched=0,
        search_duration_ms=0.0,
    )


@app.get("/api/search/{search_id}/status", response_model=SearchStatusResponse)
async def get_search_status(search_id: str) -> SearchStatusResponse:
    """Get the status of a search operation."""
    if search_id not in active_searches:
        raise HTTPException(status_code=404, detail="Search not found")

    state = active_searches[search_id]

    return SearchStatusResponse(
        search_id=search_id,
        status=state.status,
        progress=state.progress,
        message=state.message,
        results_count=state.results_count,
        started_at=state.started_at,
    )


@app.get("/api/search/{search_id}/results", response_model=SearchResponse)
async def get_search_results(search_id: str, include_metadata: bool = False) -> SearchResponse:
    """Get the results of a completed search."""
    if search_id not in active_searches:
        raise HTTPException(status_code=404, detail="Search not found")

    state = active_searches[search_id]

    if state.status == "error":
        raise HTTPException(
            status_code=500, detail=state.error or "Search failed")

    if state.status != "completed":
        raise HTTPException(status_code=202, detail="Search not yet completed")

    # Return stored response or create new one
    if state.response is not None:
        response: SearchResponse = state.response
        if include_metadata:
            # Update response to include metadata if requested
            results = state.results or []
            metrics = state.metrics
            response = SearchResponse.from_results(
                results=results,
                search_id=search_id,
                metrics=metrics,
                include_metadata=include_metadata,
                status="completed",
            )
        return response
    else:
        raise HTTPException(
            status_code=500, detail="Search results not available")


@app.delete("/api/search/{search_id}")
async def cancel_search(search_id: str) -> dict[str, str]:
    """Cancel a running search operation."""
    if search_id not in active_searches:
        raise HTTPException(status_code=404, detail="Search not found")

    state = active_searches[search_id]

    if state.status in ["completed", "error", "cancelled"]:
        return {"message": f"Search already {state.status}"}

    # Mark as cancelled
    state.status = "cancelled"
    state.message = "Search cancelled by user"

    return {"message": "Search cancelled successfully"}


@app.get("/api/searches", response_model=None)
async def list_searches() -> dict[str, list[SearchListItem]]:
    """List all searches (active and completed)."""
    searches: list[SearchListItem] = []
    for search_id, state in active_searches.items():
        searches.append(
            SearchListItem(
                search_id=search_id,
                status=state.status,
                progress=state.progress,
                message=state.message,
                results_count=state.results_count,
                started_at=state.started_at,
            )
        )

    return {"searches": searches}


@app.websocket("/ws/{search_id}")
async def websocket_progress(websocket: WebSocket, search_id: str) -> None:
    """WebSocket endpoint for real-time search progress updates."""
    await websocket_endpoint(websocket, search_id)


@app.post("/api/search/{search_id}/export")
async def export_search_results(search_id: str, export_request: ExportRequest) -> FileResponse:
    """Export search results to file."""
    if search_id not in active_searches:
        raise HTTPException(status_code=404, detail="Search not found")

    state = active_searches[search_id]

    if state.status != "completed":
        raise HTTPException(status_code=400, detail="Search not completed")

    if state.results is None:
        raise HTTPException(
            status_code=500, detail="Search results not available")

    results = state.results

    # Generate filename if not provided
    if not export_request.filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        extension = export_request.format.value
        export_request.filename = f"githound_results_{timestamp}.{extension}"

    # Create temporary export file
    export_path = Path(f"/tmp/{export_request.filename}")
    ExportManagerCls: type[Any] = get_export_manager()
    export_manager = ExportManagerCls()

    try:
        if export_request.format.value == "json":
            export_manager.export_to_json(
                results, export_path, export_request.include_metadata)
        elif export_request.format.value == "csv":
            export_manager.export_to_csv(
                results, export_path, export_request.include_metadata)
        elif export_request.format.value == "text":
            export_manager.export_to_text(
                results, export_path, "detailed" if export_request.include_metadata else "simple"
            )
        else:
            raise HTTPException(
                status_code=400, detail=f"Unsupported export format: {export_request.format}"
            )

        # Return file for download
        return FileResponse(
            path=export_path,
            filename=export_request.filename,
            media_type="application/octet-stream",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {e}")


# Cleanup endpoint for removing old searches
@app.delete("/api/searches/cleanup")
async def cleanup_searches(max_age_hours: int = 24) -> dict[str, str]:
    """Clean up old search results."""
    cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)

    to_remove: list[Any] = []
    for search_id, state in active_searches.items():
        if state.started_at.timestamp() < cutoff_time:
            to_remove.append(search_id)

    for search_id in to_remove:
        del active_searches[search_id]

    return {"message": f"Cleaned up {len(to_remove)} old searches"}


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Any, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    error_response = ErrorResponse(
        error="HTTPException", message=exc.detail, details={"status_code": exc.status_code}
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict()  # Use dict() for Pydantic v1 compatibility
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Any, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    error_response = ErrorResponse(
        error=type(exc).__name__, message=str(exc), details={"request_url": str(request.url)}
    )
    return JSONResponse(
        status_code=500,
        content=error_response.dict()  # Use dict() for Pydantic v1 compatibility
    )
