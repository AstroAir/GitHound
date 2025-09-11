"""
Consolidated Git analysis API endpoints.

Provides comprehensive Git analysis capabilities including blame, diff, 
merge conflict detection, and repository statistics.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from ...git_blame import get_author_statistics, get_file_blame
from ...git_diff import compare_branches, compare_commits
from ...git_handler import (
    extract_commit_metadata,
    get_commits_with_filters,
    get_repository,
    get_repository_metadata,
)
from ..core.git_operations import GitOperationsManager
from ..middleware.rate_limiting import get_limiter
from ..models.api_models import ApiResponse
from ..services.auth_service import require_user
from ..utils.validation import get_request_id, validate_repo_path

# Create router
router = APIRouter(prefix="/api/analysis", tags=["analysis"])
limiter = get_limiter()
git_ops_manager = GitOperationsManager()


# Analysis Models
class BlameAnalysisRequest(BaseModel):
    """Request for file blame analysis."""
    file_path: str = Field(..., description="Path to the file")
    commit: str | None = Field(None, description="Specific commit hash")
    line_range: list[int] | None = Field(
        None, description="Line range [start, end]")


class DiffAnalysisRequest(BaseModel):
    """Request for diff analysis."""
    from_commit: str = Field(..., description="Source commit hash")
    to_commit: str = Field(..., description="Target commit hash")
    file_patterns: list[str] | None = Field(
        None, description="File patterns to include")
    context_lines: int = Field(3, description="Number of context lines")


class BranchDiffRequest(BaseModel):
    """Request for branch comparison."""
    from_branch: str = Field(..., description="Source branch")
    to_branch: str = Field(..., description="Target branch")
    file_patterns: list[str] | None = Field(
        None, description="File patterns to include")
    context_lines: int = Field(3, description="Number of context lines")


class CommitFilterRequest(BaseModel):
    """Request for filtered commit retrieval."""
    branch: str | None = Field(None, description="Branch to search")
    author_pattern: str | None = Field(None, description="Author pattern")
    message_pattern: str | None = Field(None, description="Message pattern")
    date_from: datetime | None = Field(None, description="Start date")
    date_to: datetime | None = Field(None, description="End date")
    file_patterns: list[str] | None = Field(None, description="File patterns")
    max_count: int = Field(50, ge=1, le=1000, description="Maximum commits")


class RepositoryAnalysisRequest(BaseModel):
    """Request for repository analysis."""
    include_detailed_stats: bool = Field(
        True, description="Include detailed statistics")


# Blame Analysis Endpoints

@router.post("/blame", response_model=ApiResponse)
@limiter.limit("20/minute")
async def analyze_file_blame(
    request: Request,
    blame_request: BlameAnalysisRequest,
    repo_path: str = Query(..., description="Repository path"),
    current_user: dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id)
) -> ApiResponse:
    """
    Analyze line-by-line authorship for a file using git blame.

    Returns detailed blame information showing who last modified each line,
    when it was modified, and in which commit.
    """
    try:
        await validate_repo_path(repo_path)
        repo = get_repository(Path(repo_path))

        blame_result = get_file_blame(
            repo=repo,
            file_path=blame_request.file_path,
            commit=blame_request.commit
        )

        # Filter by line range if specified
        if blame_request.line_range and len(blame_request.line_range) == 2:
            start_line, end_line = blame_request.line_range
            if hasattr(blame_result, 'line_blame'):
                filtered_blame: dict[str, Any] = {}
                for line_num, blame_info in blame_result.line_blame.items():
                    if start_line <= line_num <= end_line:
                        filtered_blame[line_num] = blame_info
                blame_result.line_blame = filtered_blame

        return ApiResponse(
            success=True,
            message=f"Blame analysis completed for {blame_request.file_path}",
            data=blame_result.model_dump() if hasattr(blame_result, 'model_dump') else blame_result.__dict__,
            request_id=request_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze file blame: {str(e)}"
        )


# Diff Analysis Endpoints

@router.post("/diff/commits", response_model=ApiResponse)
@limiter.limit("15/minute")
async def compare_commits_endpoint(
    request: Request,
    diff_request: DiffAnalysisRequest,
    repo_path: str = Query(..., description="Repository path"),
    current_user: dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id)
) -> ApiResponse:
    """
    Compare two commits and return detailed diff analysis.

    Returns comprehensive diff information including file changes,
    line-by-line differences, and statistics.
    """
    try:
        await validate_repo_path(repo_path)
        repo = get_repository(Path(repo_path))

        diff_result = compare_commits(
            repo=repo,
            from_commit=diff_request.from_commit,
            to_commit=diff_request.to_commit,
            file_patterns=diff_request.file_patterns
        )

        return ApiResponse(
            success=True,
            message=f"Diff analysis completed: {diff_result.files_changed} files changed",
            data=diff_result.model_dump() if hasattr(diff_result, 'model_dump') else diff_result.__dict__,
            request_id=request_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare commits: {str(e)}"
        )


@router.post("/diff/branches", response_model=ApiResponse)
@limiter.limit("15/minute")
async def compare_branches_endpoint(
    request: Request,
    branch_diff_request: BranchDiffRequest,
    repo_path: str = Query(..., description="Repository path"),
    current_user: dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id)
) -> ApiResponse:
    """
    Compare two branches and return detailed diff analysis.

    Returns comprehensive diff information showing all changes
    between the specified branches.
    """
    try:
        await validate_repo_path(repo_path)
        repo = get_repository(Path(repo_path))

        diff_result = compare_branches(
            repo=repo,
            from_branch=branch_diff_request.from_branch,
            to_branch=branch_diff_request.to_branch,
            file_patterns=branch_diff_request.file_patterns
        )

        return ApiResponse(
            success=True,
            message=f"Branch diff analysis completed: {diff_result.files_changed} files changed",
            data=diff_result.model_dump() if hasattr(diff_result, 'model_dump') else diff_result.__dict__,
            request_id=request_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare branches: {str(e)}"
        )


# Commit Analysis Endpoints

@router.post("/commits/filter", response_model=ApiResponse)
@limiter.limit("20/minute")
async def get_filtered_commits(
    request: Request,
    filter_request: CommitFilterRequest,
    repo_path: str = Query(..., description="Repository path"),
    current_user: dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id)
) -> ApiResponse:
    """
    Get commits with advanced filtering options.

    Supports filtering by author, message content, date ranges,
    file patterns, and branch selection.
    """
    try:
        await validate_repo_path(repo_path)
        repo = get_repository(Path(repo_path))

        commits = get_commits_with_filters(
            repo=repo,
            branch=filter_request.branch,
            author_pattern=filter_request.author_pattern,
            message_pattern=filter_request.message_pattern,
            date_from=filter_request.date_from,
            date_to=filter_request.date_to,
            file_patterns=filter_request.file_patterns,
            max_count=filter_request.max_count,
        )

        commit_list: list[Any] = []
        for commit in commits:
            commit_info = extract_commit_metadata(commit)
            commit_list.append(commit_info.dict() if hasattr(commit_info, 'dict') else commit_info)

        return ApiResponse(
            success=True,
            message=f"Retrieved {len(commit_list)} filtered commits",
            data={
                "commits": commit_list,
                "total_count": len(commit_list),
                "filters_applied": filter_request.dict()
            },
            request_id=request_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get filtered commits: {str(e)}"
        )


@router.get("/file-history", response_model=ApiResponse)
@limiter.limit("30/minute")
async def get_file_history_endpoint(
    request: Request,
    repo_path: str = Query(..., description="Repository path"),
    file_path: str = Query(..., description="File path"),
    branch: str | None = Query(None, description="Branch name"),
    max_count: int = Query(
        50, ge=1, le=500, description="Maximum number of commits"),
    current_user: dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id)
) -> ApiResponse:
    """
    Get the complete history of changes for a specific file.

    Returns chronological list of commits that modified the file
    with detailed change information.
    """
    try:
        await validate_repo_path(repo_path)
        repo = get_repository(Path(repo_path))

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
                "branch": branch,
                "history": history,
                "total_commits": len(history)
            },
            request_id=request_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get file history: {str(e)}"
        )


# Repository Statistics and Analytics

@router.post("/repository", response_model=ApiResponse)
@limiter.limit("10/minute")
async def analyze_repository(
    request: Request,
    repo_path: str = Query(..., description="Repository path"),
    analysis_request: RepositoryAnalysisRequest = ...,
    current_user: dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id)
) -> ApiResponse:
    """
    Get comprehensive repository analysis and statistics.

    Returns detailed information about the repository including:
    - Branch and tag information
    - Contributor statistics
    - Commit history overview
    - Repository health metrics
    """
    try:
        await validate_repo_path(repo_path)
        repo = get_repository(Path(repo_path))

        metadata = get_repository_metadata(repo)

        if analysis_request.include_detailed_stats:
            # Add detailed author statistics
            author_stats = get_author_statistics(repo)
            metadata["detailed_author_stats"] = author_stats

        return ApiResponse(
            success=True,
            message="Repository analysis completed successfully",
            data=metadata,
            request_id=request_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze repository: {str(e)}"
        )


@router.get("/repository-stats", response_model=ApiResponse)
@limiter.limit("10/minute")
async def get_repository_statistics(
    request: Request,
    repo_path: str = Query(..., description="Repository path"),
    include_author_stats: bool = Query(
        True, description="Include author statistics"),
    include_file_stats: bool = Query(
        True, description="Include file statistics"),
    current_user: dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id)
) -> ApiResponse:
    """
    Get comprehensive repository statistics and analytics.

    Returns detailed statistics about contributors, activity patterns,
    file types, repository health metrics, and more.
    """
    try:
        await validate_repo_path(repo_path)
        repo = get_repository(Path(repo_path))

        # Get basic repository metadata
        metadata = get_repository_metadata(repo)

        statistics = {
            "repository_info": metadata,
            "summary": {
                "total_commits": metadata.get("total_commits", 0),
                "total_contributors": len(metadata.get("contributors", [])),
                "total_branches": len(metadata.get("branches", [])),
                "total_tags": len(metadata.get("tags", [])),
                "repository_age_days": None,
            },
        }

        # Add detailed author statistics if requested
        if include_author_stats:
            author_stats = get_author_statistics(repo)
            statistics["author_statistics"] = author_stats

        return ApiResponse(
            success=True,
            message="Repository statistics retrieved successfully",
            data=statistics,
            request_id=request_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get repository statistics: {str(e)}"
        )


# Merge Conflict Analysis

@router.get("/conflicts", response_model=ApiResponse)
@limiter.limit("30/minute")
async def get_merge_conflicts(
    request: Request,
    repo_path: str = Query(..., description="Repository path"),
    current_user: dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id)
) -> ApiResponse:
    """
    Get information about current merge conflicts in the repository.

    Returns detailed information about conflicted files and their status.
    """
    try:
        await validate_repo_path(repo_path)

        conflicts_info = git_ops_manager.get_merge_conflicts(repo_path)

        return ApiResponse(
            success=True,
            message="Merge conflicts information retrieved",
            data=conflicts_info,
            request_id=request_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get merge conflicts: {str(e)}"
        )
