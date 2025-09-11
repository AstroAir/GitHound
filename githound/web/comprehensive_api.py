"""
Comprehensive GitHound API with complete Git functionality coverage.

This module provides a complete REST API for all Git operations including:
- Core Git operations (init, clone, status, branch, commit, tag, remote)
- Advanced analysis (blame, diff, merge conflicts, statistics)
- Search and query capabilities
- Integration features (export, webhooks, batch operations)
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional, Dict, List

from fastapi import (
    BackgroundTasks, 
    Depends, 
    FastAPI, 
    HTTPException, 
    Query, 
    Request,
    status
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import FileResponse, JSONResponse
from git import GitCommandError, Repo
from pydantic import BaseModel, Field

from .auth import get_current_active_user, require_roles

# Auth dependencies
require_user = require_roles(["user", "admin"])
require_admin = require_roles(["admin"])
import redis
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from ..git_handler import get_repository
from ..models import SearchResult, SearchMetrics
from .models import ErrorResponse
from .git_operations import GitOperationsManager
from .auth import AuthManager, get_current_user
from .rate_limiting import get_limiter
from .webhooks import WebhookManager

# Create comprehensive FastAPI app
app = FastAPI(
    title="GitHound Comprehensive API",
    description="""
    Complete Git repository analysis and management API.
    
    Features:
    - Full Git operations (init, clone, branch, commit, tag, remote)
    - Advanced analysis (blame, diff, merge conflicts, statistics)
    - Multi-modal search with fuzzy matching
    - Real-time updates via WebSocket
    - Export in multiple formats
    - Webhook notifications
    - Batch operations
    - Authentication and rate limiting
    """,
    version="3.0.0",
    docs_url="/api/v3/docs",
    redoc_url="/api/v3/redoc",
    openapi_url="/api/v3/openapi.json",
    contact={
        "name": "GitHound API Support",
        "url": "https://github.com/AstroAir/GitHound",
        "email": "support@githound.dev"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }
)

# Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting setup
limiter = get_limiter()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Global managers
auth_manager = AuthManager()
git_ops_manager = GitOperationsManager()
webhook_manager = WebhookManager()

# Global state
active_operations: Dict[str, Dict[str, Any]] = {}
operation_results: Dict[str, Any] = {}

# Security
security = HTTPBearer()

# Base Models
class ApiResponse(BaseModel):
    """Standard API response format."""
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")
    data: Optional[Any] = Field(None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: Optional[str] = Field(None, description="Request tracking ID")

class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(50, ge=1, le=1000, description="Page size")
    
class SortParams(BaseModel):
    """Sorting parameters."""
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: str = Field("asc", pattern="^(asc|desc)$", description="Sort order")

# Repository Models
class RepositoryCreateRequest(BaseModel):
    """Request to create/initialize a repository."""
    path: str = Field(..., description="Repository path")
    bare: bool = Field(False, description="Create bare repository")
    template: Optional[str] = Field(None, description="Template repository URL")

class RepositoryCloneRequest(BaseModel):
    """Request to clone a repository."""
    url: str = Field(..., description="Repository URL to clone")
    path: str = Field(..., description="Local path for cloned repository")
    branch: Optional[str] = Field(None, description="Specific branch to clone")
    depth: Optional[int] = Field(None, description="Clone depth")
    recursive: bool = Field(False, description="Clone submodules recursively")

class RepositoryStatusResponse(BaseModel):
    """Repository status information."""
    is_dirty: bool = Field(..., description="Repository has uncommitted changes")
    untracked_files: List[str] = Field(..., description="Untracked files")
    modified_files: List[str] = Field(..., description="Modified files")
    staged_files: List[str] = Field(..., description="Staged files")
    deleted_files: List[str] = Field(..., description="Deleted files")
    current_branch: Optional[str] = Field(None, description="Current branch name")
    ahead_behind: Optional[Dict[str, int]] = Field(None, description="Commits ahead/behind remote")

# Branch Models
class BranchCreateRequest(BaseModel):
    """Request to create a branch."""
    repo_path: str = Field(..., description="Repository path")
    branch_name: str = Field(..., description="New branch name")
    start_point: Optional[str] = Field(None, description="Starting commit/branch")
    checkout: bool = Field(True, description="Checkout new branch")

class BranchMergeRequest(BaseModel):
    """Request to merge branches."""
    repo_path: str = Field(..., description="Repository path")
    source_branch: str = Field(..., description="Source branch to merge")
    target_branch: Optional[str] = Field(None, description="Target branch (current if None)")
    strategy: str = Field("merge", pattern="^(merge|rebase|squash)$", description="Merge strategy")
    message: Optional[str] = Field(None, description="Merge commit message")

class BranchInfo(BaseModel):
    """Branch information."""
    name: str = Field(..., description="Branch name")
    commit_hash: str = Field(..., description="Latest commit hash")
    commit_message: str = Field(..., description="Latest commit message")
    author: str = Field(..., description="Latest commit author")
    date: datetime = Field(..., description="Latest commit date")
    is_current: bool = Field(..., description="Is current branch")
    is_remote: bool = Field(..., description="Is remote branch")
    tracking_branch: Optional[str] = Field(None, description="Tracking remote branch")

# Commit Models
class CommitCreateRequest(BaseModel):
    """Request to create a commit."""
    repo_path: str = Field(..., description="Repository path")
    message: str = Field(..., description="Commit message")
    files: Optional[List[str]] = Field(None, description="Specific files to commit")
    all_files: bool = Field(False, description="Commit all modified files")
    author_name: Optional[str] = Field(None, description="Author name override")
    author_email: Optional[str] = Field(None, description="Author email override")

class CommitAmendRequest(BaseModel):
    """Request to amend the last commit."""
    repo_path: str = Field(..., description="Repository path")
    message: Optional[str] = Field(None, description="New commit message")
    files: Optional[List[str]] = Field(None, description="Additional files to include")

class CommitRevertRequest(BaseModel):
    """Request to revert a commit."""
    repo_path: str = Field(..., description="Repository path")
    commit_hash: str = Field(..., description="Commit to revert")
    no_commit: bool = Field(False, description="Don't create revert commit")

class CommitCherryPickRequest(BaseModel):
    """Request to cherry-pick a commit."""
    repo_path: str = Field(..., description="Repository path")
    commit_hash: str = Field(..., description="Commit to cherry-pick")
    no_commit: bool = Field(False, description="Don't create cherry-pick commit")

# Tag Models
class TagCreateRequest(BaseModel):
    """Request to create a tag."""
    repo_path: str = Field(..., description="Repository path")
    tag_name: str = Field(..., description="Tag name")
    commit: Optional[str] = Field(None, description="Commit to tag (HEAD if None)")
    message: Optional[str] = Field(None, description="Tag message (creates annotated tag)")
    force: bool = Field(False, description="Force tag creation")

class TagInfo(BaseModel):
    """Tag information."""
    name: str = Field(..., description="Tag name")
    commit_hash: str = Field(..., description="Tagged commit hash")
    message: Optional[str] = Field(None, description="Tag message")
    tagger: Optional[str] = Field(None, description="Tagger name")
    date: Optional[datetime] = Field(None, description="Tag date")
    is_annotated: bool = Field(..., description="Is annotated tag")

# Remote Models
class RemoteAddRequest(BaseModel):
    """Request to add a remote."""
    repo_path: str = Field(..., description="Repository path")
    name: str = Field(..., description="Remote name")
    url: str = Field(..., description="Remote URL")

class RemoteInfo(BaseModel):
    """Remote information."""
    name: str = Field(..., description="Remote name")
    url: str = Field(..., description="Remote URL")
    fetch_url: str = Field(..., description="Fetch URL")
    push_url: str = Field(..., description="Push URL")

# Dependency functions
async def get_request_id() -> str:
    """Generate unique request ID."""
    return str(uuid.uuid4())

async def validate_repo_path(repo_path: str) -> Path:
    """Validate repository path."""
    path = Path(repo_path)
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Repository path does not exist: {repo_path}"
        )
    
    try:
        get_repository(path)
    except GitCommandError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid Git repository: {e}"
        )
    
    return path

# Health and Info Endpoints
@app.get("/api/v3/health", response_model=ApiResponse)
async def health_check(request_id: str = Depends(get_request_id)) -> ApiResponse:
    """API health check."""
    return ApiResponse(
        success=True,
        message="GitHound API is healthy",
        data={
            "version": "3.0.0",
            "status": "operational",
            "active_operations": len(active_operations),
            "features": [
                "git_operations",
                "advanced_analysis", 
                "search_capabilities",
                "webhooks",
                "batch_operations",
                "real_time_updates"
            ]
        },
        request_id=request_id
    )

@app.get("/api/v3/info", response_model=ApiResponse)
async def api_info(request_id: str = Depends(get_request_id)) -> ApiResponse:
    """Get comprehensive API information."""
    return ApiResponse(
        success=True,
        message="GitHound API information",
        data={
            "name": "GitHound Comprehensive API",
            "version": "3.0.0",
            "description": "Complete Git repository analysis and management API",
            "endpoints": {
                "repository": "Repository operations (init, clone, status)",
                "branches": "Branch management (create, delete, merge, list)",
                "commits": "Commit operations (create, amend, revert, cherry-pick)",
                "tags": "Tag management (create, delete, list)",
                "remotes": "Remote repository operations",
                "analysis": "Advanced Git analysis (blame, diff, conflicts)",
                "search": "Multi-modal search capabilities",
                "export": "Data export in multiple formats",
                "webhooks": "Event notifications",
                "batch": "Batch operations"
            },
            "authentication": "JWT Bearer token",
            "rate_limits": "100 requests per minute per IP",
            "websocket_support": True,
            "supported_formats": ["JSON", "YAML", "CSV", "XML"]
        },
        request_id=request_id
    )


# Repository Operations Endpoints

@app.post("/api/v3/repository/init", response_model=ApiResponse)
@limiter.limit("10/minute")
async def init_repository(
    request: Request,
    repo_request: RepositoryCreateRequest,
    current_user: Dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id)
) -> ApiResponse:
    """Initialize a new Git repository."""
    try:
        result = git_ops_manager.init_repository(
            path=repo_request.path,
            bare=repo_request.bare
        )

        # Trigger webhook event
        from .webhooks import WebhookEvent, webhook_manager
        await webhook_manager.trigger_event(WebhookEvent(
            event_type="repository.created",
            event_id=f"repo_init_{request_id}",
            repository_path=repo_request.path,
            user_id=current_user["user_id"],
            data=result
        ))

        return ApiResponse(
            success=True,
            message="Repository initialized successfully",
            data=result,
            request_id=request_id
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize repository: {str(e)}"
        )


@app.post("/api/v3/repository/clone", response_model=ApiResponse)
@limiter.limit("5/minute")
async def clone_repository(
    request: Request,
    clone_request: RepositoryCloneRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id)
) -> ApiResponse:
    """Clone a remote repository."""
    try:
        # Start clone operation in background
        operation_id = f"clone_{request_id}"
        active_operations[operation_id] = {
            "type": "clone",
            "status": "started",
            "progress": 0,
            "message": "Clone operation started",
            "user_id": current_user["user_id"],
            "started_at": datetime.now()
        }

        background_tasks.add_task(
            perform_clone_operation,
            operation_id,
            clone_request,
            current_user["user_id"]
        )

        return ApiResponse(
            success=True,
            message="Clone operation started",
            data={
                "operation_id": operation_id,
                "status": "started",
                "url": clone_request.url,
                "path": clone_request.path
            },
            request_id=request_id
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start clone operation: {str(e)}"
        )


@app.get("/api/v3/repository/{repo_path:path}/status", response_model=ApiResponse)
@limiter.limit("30/minute")
async def get_repository_status(
    request: Request,
    repo_path: str,
    current_user: Dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id)
) -> ApiResponse:
    """Get repository status information."""
    try:
        await validate_repo_path(repo_path)

        status_info = git_ops_manager.get_repository_status(repo_path)

        return ApiResponse(
            success=True,
            message="Repository status retrieved successfully",
            data=status_info,
            request_id=request_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get repository status: {str(e)}"
        )


# Background task functions
async def perform_clone_operation(operation_id: str, clone_request: RepositoryCloneRequest, user_id: str) -> None:
    """Perform clone operation in background."""
    try:
        active_operations[operation_id]["status"] = "cloning"
        active_operations[operation_id]["message"] = "Cloning repository..."
        active_operations[operation_id]["progress"] = 10

        result = git_ops_manager.clone_repository(
            url=clone_request.url,
            path=clone_request.path,
            branch=clone_request.branch,
            depth=clone_request.depth,
            recursive=clone_request.recursive
        )

        active_operations[operation_id]["status"] = "completed"
        active_operations[operation_id]["message"] = "Clone completed successfully"
        active_operations[operation_id]["progress"] = 100
        active_operations[operation_id]["result"] = result

        # Trigger webhook event
        from .webhooks import WebhookEvent, webhook_manager
        await webhook_manager.trigger_event(WebhookEvent(
            event_type="repository.cloned",
            event_id=f"repo_clone_{operation_id}",
            repository_path=clone_request.path,
            user_id=user_id,
            data=result
        ))

    except Exception as e:
        active_operations[operation_id]["status"] = "failed"
        active_operations[operation_id]["message"] = f"Clone failed: {str(e)}"
        active_operations[operation_id]["error"] = str(e)


# Branch Operations Endpoints

@app.get("/api/v3/repository/{repo_path:path}/branches", response_model=ApiResponse)
@limiter.limit("50/minute")
async def list_branches(
    request: Request,
    repo_path: str,
    include_remote: bool = Query(True, description="Include remote branches"),
    current_user: Dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id)
) -> ApiResponse:
    """List all branches in the repository."""
    try:
        await validate_repo_path(repo_path)

        branches = git_ops_manager.list_branches(repo_path, include_remote)

        return ApiResponse(
            success=True,
            message=f"Retrieved {len(branches)} branches",
            data={
                "branches": branches,
                "total_count": len(branches),
                "local_count": len([b for b in branches if not b["is_remote"]]),
                "remote_count": len([b for b in branches if b["is_remote"]])
            },
            request_id=request_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list branches: {str(e)}"
        )


@app.post("/api/v3/repository/{repo_path:path}/branches", response_model=ApiResponse)
@limiter.limit("20/minute")
async def create_branch(
    request: Request,
    repo_path: str,
    branch_request: BranchCreateRequest,
    current_user: Dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id)
) -> ApiResponse:
    """Create a new branch."""
    try:
        await validate_repo_path(repo_path)

        result = git_ops_manager.create_branch(
            repo_path=repo_path,
            branch_name=branch_request.branch_name,
            start_point=branch_request.start_point,
            checkout=branch_request.checkout
        )

        # Trigger webhook event
        from .webhooks import WebhookEvent, webhook_manager
        await webhook_manager.trigger_event(WebhookEvent(
            event_type="branch.created",
            event_id=f"branch_create_{request_id}",
            repository_path=repo_path,
            user_id=current_user["user_id"],
            data=result
        ))

        return ApiResponse(
            success=True,
            message=f"Branch '{branch_request.branch_name}' created successfully",
            data=result,
            request_id=request_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create branch: {str(e)}"
        )


@app.delete("/api/v3/repository/{repo_path:path}/branches/{branch_name}", response_model=ApiResponse)
@limiter.limit("20/minute")
async def delete_branch(
    request: Request,
    repo_path: str,
    branch_name: str,
    force: bool = Query(False, description="Force delete branch"),
    current_user: Dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id)
) -> ApiResponse:
    """Delete a branch."""
    try:
        await validate_repo_path(repo_path)

        result = git_ops_manager.delete_branch(
            repo_path=repo_path,
            branch_name=branch_name,
            force=force
        )

        # Trigger webhook event
        from .webhooks import WebhookEvent, webhook_manager
        await webhook_manager.trigger_event(WebhookEvent(
            event_type="branch.deleted",
            event_id=f"branch_delete_{request_id}",
            repository_path=repo_path,
            user_id=current_user["user_id"],
            data=result
        ))

        return ApiResponse(
            success=True,
            message=f"Branch '{branch_name}' deleted successfully",
            data=result,
            request_id=request_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete branch: {str(e)}"
        )


@app.post("/api/v3/repository/{repo_path:path}/branches/{branch_name}/checkout", response_model=ApiResponse)
@limiter.limit("30/minute")
async def checkout_branch(
    request: Request,
    repo_path: str,
    branch_name: str,
    current_user: Dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id)
) -> ApiResponse:
    """Checkout a branch."""
    try:
        await validate_repo_path(repo_path)

        result = git_ops_manager.checkout_branch(
            repo_path=repo_path,
            branch_name=branch_name
        )

        return ApiResponse(
            success=True,
            message=f"Checked out branch '{branch_name}'",
            data=result,
            request_id=request_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to checkout branch: {str(e)}"
        )


@app.post("/api/v3/repository/{repo_path:path}/branches/merge", response_model=ApiResponse)
@limiter.limit("10/minute")
async def merge_branches(
    request: Request,
    repo_path: str,
    merge_request: BranchMergeRequest,
    current_user: Dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id)
) -> ApiResponse:
    """Merge branches."""
    try:
        await validate_repo_path(repo_path)

        result = git_ops_manager.merge_branch(
            repo_path=repo_path,
            source_branch=merge_request.source_branch,
            target_branch=merge_request.target_branch,
            strategy=merge_request.strategy,
            message=merge_request.message
        )

        # Trigger webhook event
        from .webhooks import WebhookEvent, webhook_manager
        await webhook_manager.trigger_event(WebhookEvent(
            event_type="branch.merged",
            event_id=f"branch_merge_{request_id}",
            repository_path=repo_path,
            user_id=current_user["user_id"],
            data=result
        ))

        return ApiResponse(
            success=True,
            message="Branch merge completed",
            data=result,
            request_id=request_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to merge branches: {str(e)}"
        )


# Commit Operations Endpoints

@app.post("/api/v3/repository/{repo_path:path}/commits", response_model=ApiResponse)
@limiter.limit("30/minute")
async def create_commit(
    request: Request,
    repo_path: str,
    commit_request: CommitCreateRequest,
    current_user: Dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id)
) -> ApiResponse:
    """Create a new commit."""
    try:
        await validate_repo_path(repo_path)

        result = git_ops_manager.create_commit(
            repo_path=repo_path,
            message=commit_request.message,
            files=commit_request.files,
            all_files=commit_request.all_files,
            author_name=commit_request.author_name,
            author_email=commit_request.author_email
        )

        # Trigger webhook event
        from .webhooks import WebhookEvent, webhook_manager
        await webhook_manager.trigger_event(WebhookEvent(
            event_type="commit.created",
            event_id=f"commit_create_{request_id}",
            repository_path=repo_path,
            user_id=current_user["user_id"],
            data=result
        ))

        return ApiResponse(
            success=True,
            message="Commit created successfully",
            data=result,
            request_id=request_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create commit: {str(e)}"
        )


@app.patch("/api/v3/repository/{repo_path:path}/commits/amend", response_model=ApiResponse)
@limiter.limit("20/minute")
async def amend_commit(
    request: Request,
    repo_path: str,
    amend_request: CommitAmendRequest,
    current_user: Dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id)
) -> ApiResponse:
    """Amend the last commit."""
    try:
        await validate_repo_path(repo_path)

        result = git_ops_manager.amend_commit(
            repo_path=repo_path,
            message=amend_request.message,
            files=amend_request.files
        )

        return ApiResponse(
            success=True,
            message="Commit amended successfully",
            data=result,
            request_id=request_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to amend commit: {str(e)}"
        )


@app.post("/api/v3/repository/{repo_path:path}/commits/{commit_hash}/revert", response_model=ApiResponse)
@limiter.limit("20/minute")
async def revert_commit(
    request: Request,
    repo_path: str,
    commit_hash: str,
    revert_request: CommitRevertRequest,
    current_user: Dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id)
) -> ApiResponse:
    """Revert a commit."""
    try:
        await validate_repo_path(repo_path)

        result = git_ops_manager.revert_commit(
            repo_path=repo_path,
            commit_hash=commit_hash,
            no_commit=revert_request.no_commit
        )

        return ApiResponse(
            success=True,
            message=f"Commit {commit_hash} reverted successfully",
            data=result,
            request_id=request_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revert commit: {str(e)}"
        )


@app.post("/api/v3/repository/{repo_path:path}/commits/{commit_hash}/cherry-pick", response_model=ApiResponse)
@limiter.limit("20/minute")
async def cherry_pick_commit(
    request: Request,
    repo_path: str,
    commit_hash: str,
    cherry_pick_request: CommitCherryPickRequest,
    current_user: Dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id)
) -> ApiResponse:
    """Cherry-pick a commit."""
    try:
        await validate_repo_path(repo_path)

        result = git_ops_manager.cherry_pick_commit(
            repo_path=repo_path,
            commit_hash=commit_hash,
            no_commit=cherry_pick_request.no_commit
        )

        return ApiResponse(
            success=True,
            message=f"Commit {commit_hash} cherry-picked successfully",
            data=result,
            request_id=request_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cherry-pick commit: {str(e)}"
        )
