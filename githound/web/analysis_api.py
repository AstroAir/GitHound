"""
Advanced Git analysis API endpoints.

Provides comprehensive Git analysis capabilities including blame, diff, 
merge conflict detection, and repository statistics.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from ..git_blame import get_author_statistics, get_file_blame
from ..git_diff import compare_branches, compare_commits
from ..git_handler import (
    extract_commit_metadata,
    get_commits_with_filters,
    get_file_history,
    get_repository,
    get_repository_metadata,
)
from .auth import require_user
from .comprehensive_api import ApiResponse, get_request_id, validate_repo_path
from .git_operations import GitOperationsManager
from .rate_limiting import get_limiter

# Create router
router = APIRouter(prefix="/api/v3/analysis", tags=["analysis"])
limiter = get_limiter()
git_ops_manager = GitOperationsManager()


# Analysis Models
class BlameAnalysisRequest(BaseModel):
    """Request for file blame analysis."""
    file_path: str = Field(..., description="Path to the file")
    commit: Optional[str] = Field(None, description="Specific commit hash")
    line_range: Optional[List[int]] = Field(None, description="Line range [start, end]")


class DiffAnalysisRequest(BaseModel):
    """Request for diff analysis."""
    from_commit: str = Field(..., description="Source commit hash")
    to_commit: str = Field(..., description="Target commit hash")
    file_patterns: Optional[List[str]] = Field(None, description="File patterns to include")
    context_lines: int = Field(3, description="Number of context lines")


class BranchDiffRequest(BaseModel):
    """Request for branch comparison."""
    from_branch: str = Field(..., description="Source branch")
    to_branch: str = Field(..., description="Target branch")
    file_patterns: Optional[List[str]] = Field(None, description="File patterns to include")
    context_lines: int = Field(3, description="Number of context lines")


class CommitFilterRequest(BaseModel):
    """Request for filtered commit retrieval."""
    branch: Optional[str] = Field(None, description="Branch to search")
    author_pattern: Optional[str] = Field(None, description="Author pattern")
    message_pattern: Optional[str] = Field(None, description="Message pattern")
    date_from: Optional[datetime] = Field(None, description="Start date")
    date_to: Optional[datetime] = Field(None, description="End date")
    file_patterns: Optional[List[str]] = Field(None, description="File patterns")
    max_count: int = Field(100, ge=1, le=1000, description="Maximum results")


class ConflictResolutionRequest(BaseModel):
    """Request for conflict resolution."""
    file_path: str = Field(..., description="File with conflicts")
    resolution: str = Field(..., pattern="^(ours|theirs)$", description="Resolution strategy")


# Blame Analysis Endpoints

@router.post("/blame", response_model=ApiResponse)
@limiter.limit("20/minute")
async def analyze_file_blame(
    request: Request,
    repo_path: str = Query(..., description="Repository path"),
    blame_request: BlameAnalysisRequest = ...,
    current_user: Dict[str, Any] = Depends(require_user),
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
            data=blame_result.dict() if hasattr(blame_result, 'dict') else blame_result,
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
    repo_path: str = Query(..., description="Repository path"),
    diff_request: DiffAnalysisRequest = ...,
    current_user: Dict[str, Any] = Depends(require_user),
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
            data=diff_result.dict() if hasattr(diff_result, 'dict') else diff_result,
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
    repo_path: str = Query(..., description="Repository path"),
    branch_diff_request: BranchDiffRequest = ...,
    current_user: Dict[str, Any] = Depends(require_user),
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
            data=diff_result.dict() if hasattr(diff_result, 'dict') else diff_result,
            request_id=request_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare branches: {str(e)}"
        )


# Commit History and Filtering

@router.post("/commits/filter", response_model=ApiResponse)
@limiter.limit("30/minute")
async def get_filtered_commits(
    request: Request,
    repo_path: str = Query(..., description="Repository path"),
    filter_request: CommitFilterRequest = ...,
    current_user: Dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id)
) -> ApiResponse:
    """
    Retrieve commits with advanced filtering options.
    
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
            commit_list.append(commit_info.dict if commit_info is not None else None() if hasattr(commit_info, 'dict') else commit_info)
        
        return ApiResponse(
            success=True,
            message=f"Retrieved {len(commit_list)} commits",
            data={
                "commits": commit_list,
                "total_count": len(commit_list),
                "filters_applied": {
                    "branch": filter_request.branch,
                    "author_pattern": filter_request.author_pattern,
                    "message_pattern": filter_request.message_pattern,
                    "date_range": [filter_request.date_from, filter_request.date_to],
                    "file_patterns": filter_request.file_patterns
                }
            },
            request_id=request_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to filter commits: {str(e)}"
        )


# File History Analysis

@router.get("/file-history", response_model=ApiResponse)
@limiter.limit("30/minute")
async def get_file_history_endpoint(
    request: Request,
    repo_path: str = Query(..., description="Repository path"),
    file_path: str = Query(..., description="File path"),
    branch: Optional[str] = Query(None, description="Branch name"),
    max_count: int = Query(50, ge=1, le=500, description="Maximum number of commits"),
    current_user: Dict[str, Any] = Depends(require_user),
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

@router.get("/repository-stats", response_model=ApiResponse)
@limiter.limit("10/minute")
async def get_repository_statistics(
    request: Request,
    repo_path: str = Query(..., description="Repository path"),
    include_author_stats: bool = Query(True, description="Include author statistics"),
    include_file_stats: bool = Query(True, description="Include file statistics"),
    current_user: Dict[str, Any] = Depends(require_user),
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

        # Calculate repository age
        if metadata.get("first_commit_date") and metadata.get("last_commit_date"):
            first_date = metadata["first_commit_date"]
            last_date = metadata["last_commit_date"]
            if isinstance(first_date, str):
                first_date = datetime.fromisoformat(first_date.replace("Z", "+00:00"))
                last_date = datetime.fromisoformat(last_date.replace("Z", "+00:00"))

            age_delta = last_date - first_date
            statistics["summary"]["repository_age_days"] = age_delta.days

        # Author statistics
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
                    "files": stats.get("total_files", 0),
                    "lines_added": stats.get("lines_added", 0),
                    "lines_deleted": stats.get("lines_deleted", 0),
                }
                for author, stats in top_contributors
            ]

        # File statistics
        if include_file_stats:
            file_stats = _calculate_file_statistics(repo)
            statistics["file_statistics"] = file_stats

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


# Merge Conflict Detection and Resolution

@router.get("/conflicts", response_model=ApiResponse)
@limiter.limit("30/minute")
async def get_merge_conflicts(
    request: Request,
    repo_path: str = Query(..., description="Repository path"),
    current_user: Dict[str, Any] = Depends(require_user),
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


@router.post("/conflicts/resolve", response_model=ApiResponse)
@limiter.limit("20/minute")
async def resolve_merge_conflict(
    request: Request,
    repo_path: str = Query(..., description="Repository path"),
    resolution_request: ConflictResolutionRequest = ...,
    current_user: Dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id)
) -> ApiResponse:
    """
    Resolve a merge conflict for a specific file.

    Supports automatic resolution strategies: 'ours' or 'theirs'.
    """
    try:
        await validate_repo_path(repo_path)

        result = git_ops_manager.resolve_conflict(
            repo_path=repo_path,
            file_path=resolution_request.file_path,
            resolution=resolution_request.resolution
        )

        return ApiResponse(
            success=True,
            message=f"Conflict resolved for {resolution_request.file_path}",
            data=result,
            request_id=request_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve conflict: {str(e)}"
        )


# Helper Functions

def _calculate_file_statistics(repo) -> Dict[str, Any]:
    """Calculate file statistics for the repository."""
    try:
        file_stats = {
            "total_files": 0,
            "file_types": {},
            "largest_files": [],
            "most_modified_files": []
        }

        # Get current tree
        tree = repo.head.commit.tree

        def analyze_tree(tree_obj, path="") -> None:
            for item in tree_obj.traverse():
                if item.type == 'blob':  # It's a file
                    file_path = item.path
                    file_stats["total_files"] += 1

                    # File extension analysis
                    if '.' in file_path:
                        ext = file_path.split('.')[-1].lower()
                        file_stats["file_types"][ext] = file_stats["file_types"].get(ext, 0) + 1

                    # File size analysis
                    try:
                        size = item.size
                        file_stats["largest_files"].append({
                            "path": file_path,
                            "size": size
                        })
                    except:
                        pass

        analyze_tree(tree)

        # Sort and limit largest files
        file_stats["largest_files"] = sorted(
            file_stats["largest_files"],
            key=lambda x: x["size"],
            reverse=True
        )[:10]

        # Sort file types by count
        file_stats["file_types"] = dict(sorted(
            file_stats["file_types"].items(),
            key=lambda x: x[1],
            reverse=True
        ))

        return file_stats

    except Exception:
        return {
            "total_files": 0,
            "file_types": {},
            "largest_files": [],
            "most_modified_files": []
        }
