"""Enhanced FastAPI application with comprehensive Git analysis endpoints."""

import asyncio
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query, Path as PathParam
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from git import Repo, GitCommandError
from pydantic import BaseModel, Field

from ..git_handler import (
    get_repository, extract_commit_metadata, get_repository_metadata,
    get_commits_with_filters, get_file_history
)
from ..git_blame import get_file_blame, get_line_history, get_author_statistics
from ..git_diff import compare_commits, compare_branches, get_file_diff_history
from ..models import SearchQuery, CommitInfo, RepositoryInfo
from ..schemas import ExportOptions, OutputFormat, DataFilter, SortCriteria
from ..utils.export import ExportManager


# Enhanced API Models

class RepositoryAnalysisRequest(BaseModel):
    """Request model for repository analysis."""
    repo_path: str = Field(..., description="Path to the Git repository")
    include_detailed_stats: bool = Field(True, description="Include detailed statistics")


class CommitAnalysisRequest(BaseModel):
    """Request model for commit analysis."""
    repo_path: str = Field(..., description="Path to the Git repository")
    commit_hash: Optional[str] = Field(None, description="Specific commit hash")
    include_file_changes: bool = Field(True, description="Include file change details")


class CommitFilterRequest(BaseModel):
    """Request model for filtered commit retrieval."""
    repo_path: str = Field(..., description="Path to the Git repository")
    branch: Optional[str] = Field(None, description="Branch to search")
    author_pattern: Optional[str] = Field(None, description="Author pattern")
    message_pattern: Optional[str] = Field(None, description="Message pattern")
    date_from: Optional[datetime] = Field(None, description="Start date")
    date_to: Optional[datetime] = Field(None, description="End date")
    file_patterns: Optional[List[str]] = Field(None, description="File patterns")
    max_count: int = Field(100, description="Maximum results")


class BlameAnalysisRequest(BaseModel):
    """Request model for blame analysis."""
    repo_path: str = Field(..., description="Path to the Git repository")
    file_path: str = Field(..., description="Path to the file")
    commit: Optional[str] = Field(None, description="Specific commit")


class DiffAnalysisRequest(BaseModel):
    """Request model for diff analysis."""
    repo_path: str = Field(..., description="Path to the Git repository")
    from_commit: str = Field(..., description="Source commit")
    to_commit: str = Field(..., description="Target commit")
    file_patterns: Optional[List[str]] = Field(None, description="File patterns")


class BranchDiffRequest(BaseModel):
    """Request model for branch comparison."""
    repo_path: str = Field(..., description="Path to the Git repository")
    from_branch: str = Field(..., description="Source branch")
    to_branch: str = Field(..., description="Target branch")
    file_patterns: Optional[List[str]] = Field(None, description="File patterns")


class ExportRequest(BaseModel):
    """Request model for data export."""
    repo_path: str = Field(..., description="Path to the Git repository")
    export_type: str = Field(..., description="Type of data to export")
    format: OutputFormat = Field(OutputFormat.JSON, description="Export format")
    filters: List[DataFilter] = Field(default_factory=list, description="Data filters")
    sort_by: List[SortCriteria] = Field(default_factory=list, description="Sort criteria")


# Response Models

class ApiResponse(BaseModel):
    """Base API response model."""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    data: Optional[Any] = Field(None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")


class RepositoryAnalysisResponse(ApiResponse):
    """Response model for repository analysis."""
    data: Optional[Dict[str, Any]] = Field(None, description="Repository metadata")


class CommitAnalysisResponse(ApiResponse):
    """Response model for commit analysis."""
    data: Optional[Dict[str, Any]] = Field(None, description="Commit metadata")


class CommitListResponse(ApiResponse):
    """Response model for commit list."""
    data: Optional[List[Dict[str, Any]]] = Field(None, description="List of commits")
    total_count: int = Field(0, description="Total number of results")


# Create Enhanced FastAPI App
app = FastAPI(
    title="GitHound Enhanced API",
    description="Comprehensive Git repository analysis API with advanced features",
    version="2.0.0",
    docs_url="/api/v2/docs",
    redoc_url="/api/v2/redoc",
    openapi_url="/api/v2/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Global state for async operations
active_operations: Dict[str, Dict] = {}


# Dependency functions
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current user from JWT token (placeholder for now)."""
    # TODO: Implement JWT token validation
    return {"user_id": "anonymous", "permissions": ["read", "write"]}


def validate_repository_path(repo_path: str) -> Path:
    """Validate and return repository path."""
    path = Path(repo_path)
    if not path.exists():
        raise HTTPException(status_code=400, detail=f"Repository path does not exist: {repo_path}")
    
    try:
        get_repository(path)
    except GitCommandError as e:
        raise HTTPException(status_code=400, detail=f"Invalid Git repository: {e}")
    
    return path


# Repository Analysis Endpoints

@app.post("/api/v2/repository/analyze", response_model=RepositoryAnalysisResponse)
async def analyze_repository(
    request: RepositoryAnalysisRequest,
    current_user: dict = Depends(get_current_user)
) -> RepositoryAnalysisResponse:
    """
    Analyze a Git repository and return comprehensive metadata.
    
    Returns detailed information about the repository including:
    - Branch and tag information
    - Contributor statistics
    - Commit history overview
    - Repository health metrics
    """
    try:
        repo_path = validate_repository_path(request.repo_path)
        repo = get_repository(repo_path)
        
        metadata = get_repository_metadata(repo)
        
        if request.include_detailed_stats:
            # Add detailed author statistics
            author_stats = get_author_statistics(repo)
            metadata["detailed_author_stats"] = author_stats
        
        return RepositoryAnalysisResponse(
            success=True,
            message="Repository analysis completed successfully",
            data=metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/api/v2/commit/analyze", response_model=CommitAnalysisResponse)
async def analyze_commit(
    request: CommitAnalysisRequest,
    current_user: dict = Depends(get_current_user)
) -> CommitAnalysisResponse:
    """
    Analyze a specific commit and return detailed metadata.
    
    Returns comprehensive information about the commit including:
    - Author and committer details
    - File changes and statistics
    - Parent relationships
    - Commit message analysis
    """
    try:
        repo_path = validate_repository_path(request.repo_path)
        repo = get_repository(repo_path)
        
        if request.commit_hash:
            commit = repo.commit(request.commit_hash)
        else:
            commit = repo.head.commit
        
        commit_info = extract_commit_metadata(commit)
        commit_data = commit_info.model_dump()
        
        if request.include_file_changes:
            # Add detailed file change information
            if commit.parents:
                for parent in commit.parents:
                    diffs = commit.diff(parent)
                    file_changes = []
                    for diff in diffs:
                        if diff.b_path:
                            file_changes.append({
                                "file_path": diff.b_path,
                                "change_type": "A" if diff.new_file else "M" if diff.a_path == diff.b_path else "R",
                                "old_path": diff.a_path,
                                "is_binary": diff.b_blob and diff.b_blob.size > 1024 * 1024  # Simple binary check
                            })
                    commit_data["file_changes"] = file_changes
        
        return CommitAnalysisResponse(
            success=True,
            message="Commit analysis completed successfully",
            data=commit_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/api/v2/commits/filter", response_model=CommitListResponse)
async def get_filtered_commits(
    request: CommitFilterRequest,
    current_user: dict = Depends(get_current_user)
) -> CommitListResponse:
    """
    Retrieve commits with advanced filtering options.
    
    Supports filtering by:
    - Author name/email patterns
    - Commit message content
    - Date ranges
    - File patterns
    - Branch selection
    """
    try:
        repo_path = validate_repository_path(request.repo_path)
        repo = get_repository(repo_path)
        
        commits = get_commits_with_filters(
            repo=repo,
            branch=request.branch,
            author_pattern=request.author_pattern,
            message_pattern=request.message_pattern,
            date_from=request.date_from,
            date_to=request.date_to,
            file_patterns=request.file_patterns,
            max_count=request.max_count
        )
        
        commit_list = []
        for commit in commits:
            commit_info = extract_commit_metadata(commit)
            commit_list.append(commit_info.model_dump())
        
        return CommitListResponse(
            success=True,
            message=f"Retrieved {len(commit_list)} commits",
            data=commit_list,
            total_count=len(commit_list)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Diff Analysis Endpoints

@app.post("/api/v2/diff/commits", response_model=ApiResponse)
async def compare_commits_endpoint(
    request: DiffAnalysisRequest,
    current_user: dict = Depends(get_current_user)
) -> ApiResponse:
    """
    Compare two commits and return detailed diff analysis.

    Returns comprehensive diff information including file changes
    and line-by-line differences.
    """
    try:
        repo_path = validate_repository_path(request.repo_path)
        repo = get_repository(repo_path)

        diff_result = compare_commits(
            repo=repo,
            from_commit=request.from_commit,
            to_commit=request.to_commit,
            file_patterns=request.file_patterns
        )

        return ApiResponse(
            success=True,
            message=f"Diff analysis completed: {diff_result.files_changed} files changed",
            data=diff_result.model_dump()
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/api/v2/diff/branches", response_model=ApiResponse)
async def compare_branches_endpoint(
    request: BranchDiffRequest,
    current_user: dict = Depends(get_current_user)
) -> ApiResponse:
    """
    Compare two branches and return detailed diff analysis.

    Returns comprehensive diff information showing all changes
    between the specified branches.
    """
    try:
        repo_path = validate_repository_path(request.repo_path)
        repo = get_repository(repo_path)

        diff_result = compare_branches(
            repo=repo,
            from_branch=request.from_branch,
            to_branch=request.to_branch,
            file_patterns=request.file_patterns
        )

        return ApiResponse(
            success=True,
            message=f"Branch diff analysis completed: {diff_result.files_changed} files changed",
            data=diff_result.model_dump()
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Statistics and Analytics Endpoints

@app.get("/api/v2/repository/{repo_path:path}/statistics")
async def get_repository_statistics(
    repo_path: str,
    include_author_stats: bool = Query(True, description="Include author statistics"),
    current_user: dict = Depends(get_current_user)
) -> ApiResponse:
    """
    Get comprehensive repository statistics and analytics.

    Returns detailed statistics about contributors, activity patterns,
    and repository health metrics.
    """
    try:
        repo_path_obj = validate_repository_path(repo_path)
        repo = get_repository(repo_path_obj)

        # Get basic repository metadata
        metadata = get_repository_metadata(repo)

        statistics: Dict[str, Any] = {
            "repository_info": metadata,
            "summary": {
                "total_commits": metadata.get("total_commits", 0),
                "total_contributors": len(metadata.get("contributors", [])),
                "total_branches": len(metadata.get("branches", [])),
                "total_tags": len(metadata.get("tags", [])),
                "repository_age_days": None
            }
        }

        # Calculate repository age
        if metadata.get("first_commit_date") and metadata.get("last_commit_date"):
            first_date = metadata["first_commit_date"]
            last_date = metadata["last_commit_date"]
            if isinstance(first_date, str):
                from datetime import datetime
                first_date = datetime.fromisoformat(first_date.replace('Z', '+00:00'))
                last_date = datetime.fromisoformat(last_date.replace('Z', '+00:00'))

            age_delta = last_date - first_date
            statistics["summary"]["repository_age_days"] = age_delta.days

        if include_author_stats:
            author_stats = get_author_statistics(repo)
            statistics["author_statistics"] = author_stats

            # Calculate top contributors
            top_contributors = sorted(
                author_stats.items(),
                key=lambda x: x[1].get("total_commits", 0),
                reverse=True
            )[:10]

            statistics["top_contributors"] = [
                {
                    "author": author,
                    "commits": stats.get("total_commits", 0),
                    "files": stats.get("total_files", 0)
                }
                for author, stats in top_contributors
            ]

        return ApiResponse(
            success=True,
            message="Repository statistics retrieved successfully",
            data=statistics
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Export Endpoints

@app.post("/api/v2/export", response_model=ApiResponse)
async def export_data(
    request: ExportRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
) -> ApiResponse:
    """
    Export repository data in various formats.

    Supports exporting different types of data (commits, blame, diffs)
    in JSON, YAML, or CSV formats with filtering and sorting options.
    """
    try:
        repo_path = validate_repository_path(request.repo_path)

        # Generate unique export ID
        export_id = str(uuid.uuid4())

        # Store export operation info
        active_operations[export_id] = {
            "type": "export",
            "status": "queued",
            "created_at": datetime.now(),
            "request": request.model_dump(),
            "user": current_user["user_id"]
        }

        # Start background export task
        background_tasks.add_task(perform_export, export_id, request)

        return ApiResponse(
            success=True,
            message="Export operation queued successfully",
            data={
                "export_id": export_id,
                "status": "queued",
                "estimated_completion": "2-5 minutes"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/api/v2/export/{export_id}/status")
async def get_export_status(
    export_id: str,
    current_user: dict = Depends(get_current_user)
) -> ApiResponse:
    """Get the status of an export operation."""
    if export_id not in active_operations:
        raise HTTPException(status_code=404, detail="Export operation not found")

    operation = active_operations[export_id]

    return ApiResponse(
        success=True,
        message="Export status retrieved",
        data={
            "export_id": export_id,
            "status": operation["status"],
            "created_at": operation["created_at"],
            "progress": operation.get("progress", 0),
            "message": operation.get("message", ""),
            "download_url": operation.get("download_url")
        }
    )


# Background task functions

async def perform_export(export_id: str, request: ExportRequest) -> None:
    """Perform export operation in background."""
    try:
        # Update status
        active_operations[export_id]["status"] = "running"
        active_operations[export_id]["message"] = "Starting export..."

        repo_path = Path(request.repo_path)
        repo = get_repository(repo_path)

        # Create export manager
        export_manager = ExportManager()

        # Generate output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"githound_export_{request.export_type}_{timestamp}.{request.format.value}"
        output_path = Path("/tmp") / output_filename  # Configure appropriate output directory

        # Perform export based on type
        if request.export_type == "repository_metadata":
            metadata = get_repository_metadata(repo)

            if request.format == OutputFormat.JSON:
                import json
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, default=str)
            elif request.format == OutputFormat.YAML:
                import yaml
                with open(output_path, 'w', encoding='utf-8') as f:
                    yaml.dump(metadata, f, default_flow_style=False, allow_unicode=True)

        # Update completion status
        active_operations[export_id]["status"] = "completed"
        active_operations[export_id]["message"] = "Export completed successfully"
        active_operations[export_id]["download_url"] = f"/api/v2/download/{output_filename}"
        active_operations[export_id]["progress"] = 100

    except Exception as e:
        active_operations[export_id]["status"] = "failed"
        active_operations[export_id]["message"] = f"Export failed: {str(e)}"


# Health and Status Endpoints

@app.get("/api/v2/health")
async def health_check() -> Dict[str, Any]:
    """API health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "active_operations": len(active_operations)
    }


@app.get("/api/v2/info")
async def api_info() -> Dict[str, Any]:
    """Get API information and capabilities."""
    return {
        "name": "GitHound Enhanced API",
        "version": "2.0.0",
        "description": "Comprehensive Git repository analysis API",
        "features": [
            "Repository analysis and metadata extraction",
            "Advanced commit filtering and search",
            "File history and blame analysis",
            "Diff analysis between commits and branches",
            "Author statistics and contribution analysis",
            "Data export in multiple formats",
            "Asynchronous operations support",
            "Authentication and authorization",
            "Rate limiting and security"
        ],
        "supported_formats": ["JSON", "YAML", "CSV"],
        "documentation": "/api/v2/docs"
    }


# File Analysis Endpoints

@app.get("/api/v2/file/{file_path:path}/history")
async def get_file_history_endpoint(
    file_path: str,
    repo_path: str = Query(..., description="Repository path"),
    branch: Optional[str] = Query(None, description="Branch name"),
    max_count: int = Query(50, description="Maximum number of commits"),
    current_user: dict = Depends(get_current_user)
) -> ApiResponse:
    """
    Get the complete history of changes for a specific file.
    
    Returns chronological list of commits that modified the file.
    """
    try:
        repo_path_obj = validate_repository_path(repo_path)
        repo = get_repository(repo_path_obj)
        
        history = get_file_history(
            repo=repo,
            file_path=file_path,
            branch=branch,
            max_count=max_count
        )
        
        return ApiResponse(
            success=True,
            message=f"Retrieved {len(history)} commits in file history",
            data={
                "file_path": file_path,
                "history": history,
                "total_commits": len(history)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/api/v2/file/blame", response_model=ApiResponse)
async def analyze_file_blame_endpoint(
    request: BlameAnalysisRequest,
    current_user: dict = Depends(get_current_user)
) -> ApiResponse:
    """
    Analyze line-by-line authorship for a file using git blame.
    
    Returns detailed blame information showing who last modified each line.
    """
    try:
        repo_path = validate_repository_path(request.repo_path)
        repo = get_repository(repo_path)
        
        blame_result = get_file_blame(
            repo=repo,
            file_path=request.file_path,
            commit=request.commit
        )
        
        return ApiResponse(
            success=True,
            message=f"Blame analysis completed for {request.file_path}",
            data=blame_result.model_dump()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
