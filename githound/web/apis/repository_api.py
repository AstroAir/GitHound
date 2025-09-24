"""
Repository management API endpoints.

Provides Git repository operations including init, clone, branch management,
commit operations, and tag management.
"""

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from ..core.git_operations import GitOperationError, GitOperationsManager
from ..middleware.rate_limiting import get_limiter
from ..models.api_models import ApiResponse
from ..services.auth_service import require_admin, require_user
from ..utils.validation import (
    get_request_id,
    validate_branch_name,
    validate_commit_hash,
    validate_repo_path,
    validate_tag_name,
)

# Create router
router = APIRouter(prefix="/api/repository", tags=["repository"])
limiter = get_limiter()
git_ops_manager = GitOperationsManager()


# Repository Models
class RepositoryInitRequest(BaseModel):
    """Request for repository initialization."""

    path: str = Field(..., description="Repository path")
    bare: bool = Field(False, description="Create bare repository")


class RepositoryCloneRequest(BaseModel):
    """Request for repository cloning."""

    url: str = Field(..., description="Repository URL")
    path: str = Field(..., description="Local path")
    branch: str | None = Field(None, description="Branch to clone")
    depth: int | None = Field(None, description="Clone depth")
    recursive: bool = Field(False, description="Clone submodules")


class BranchCreateRequest(BaseModel):
    """Request for branch creation."""

    branch_name: str = Field(..., description="Branch name")
    start_point: str | None = Field(None, description="Starting commit/branch")


class BranchDeleteRequest(BaseModel):
    """Request for branch deletion."""

    branch_name: str = Field(..., description="Branch name")
    force: bool = Field(False, description="Force deletion")


class CommitCreateRequest(BaseModel):
    """Request for commit creation."""

    message: str = Field(..., description="Commit message")
    author_name: str | None = Field(None, description="Author name")
    author_email: str | None = Field(None, description="Author email")
    add_all: bool = Field(False, description="Add all changes")


class TagCreateRequest(BaseModel):
    """Request for tag creation."""

    tag_name: str = Field(..., description="Tag name")
    message: str | None = Field(None, description="Tag message")
    commit: str | None = Field(None, description="Target commit")


# Repository Operations


@router.post("/init", response_model=ApiResponse)
@limiter.limit("10/minute")
async def init_repository(
    request: Request,
    init_request: RepositoryInitRequest,
    current_user: dict[str, Any] = Depends(require_admin),
    request_id: str = Depends(get_request_id),
) -> ApiResponse:
    """
    Initialize a new Git repository.

    Creates a new Git repository at the specified path.
    Requires admin privileges.
    """
    try:
        result = git_ops_manager.init_repository(path=init_request.path, bare=init_request.bare)

        return ApiResponse(
            success=True,
            message=f"Repository {result['status']} at {init_request.path}",
            data=result,
            request_id=request_id,
        )

    except GitOperationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize repository: {str(e)}",
        )


@router.post("/clone", response_model=ApiResponse)
@limiter.limit("5/minute")
async def clone_repository(
    request: Request,
    clone_request: RepositoryCloneRequest,
    current_user: dict[str, Any] = Depends(require_admin),
    request_id: str = Depends(get_request_id),
) -> ApiResponse:
    """
    Clone a remote Git repository.

    Clones a repository from a remote URL to a local path.
    Requires admin privileges.
    """
    try:
        result = git_ops_manager.clone_repository(
            url=clone_request.url,
            path=clone_request.path,
            branch=clone_request.branch,
            depth=clone_request.depth,
            recursive=clone_request.recursive,
        )

        return ApiResponse(
            success=True,
            message=f"Repository cloned to {clone_request.path}",
            data=result,
            request_id=request_id,
        )

    except GitOperationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clone repository: {str(e)}",
        )


@router.get("/status", response_model=ApiResponse)
@limiter.limit("30/minute")
async def get_repository_status(
    request: Request,
    repo_path: str = Query(..., description="Repository path"),
    current_user: dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id),
) -> ApiResponse:
    """
    Get comprehensive repository status.

    Returns detailed information about the repository state including
    modified files, staged changes, branches, and more.
    """
    try:
        await validate_repo_path(repo_path)

        status_info = git_ops_manager.get_repository_status(repo_path)

        return ApiResponse(
            success=True,
            message="Repository status retrieved",
            data=status_info,
            request_id=request_id,
        )

    except GitOperationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get repository status: {str(e)}",
        )


# Branch Operations


@router.post("/branches", response_model=ApiResponse)
@limiter.limit("20/minute")
async def create_branch(
    request: Request,
    repo_path: str = Query(..., description="Repository path"),
    branch_request: BranchCreateRequest = Body(...),
    current_user: dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id),
) -> ApiResponse:
    """
    Create a new branch.

    Creates a new branch in the repository, optionally from a specific
    starting point (commit or branch).
    """
    try:
        await validate_repo_path(repo_path)
        validate_branch_name(branch_request.branch_name)

        if branch_request.start_point:
            # Validate start point (could be commit hash or branch name)
            try:
                validate_commit_hash(branch_request.start_point)
            except HTTPException:
                validate_branch_name(branch_request.start_point)

        result = git_ops_manager.create_branch(
            path=repo_path,
            branch_name=branch_request.branch_name,
            start_point=branch_request.start_point,
        )

        return ApiResponse(
            success=True,
            message=f"Branch '{branch_request.branch_name}' created",
            data=result,
            request_id=request_id,
        )

    except GitOperationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create branch: {str(e)}",
        )


@router.delete("/branches/{branch_name}", response_model=ApiResponse)
@limiter.limit("20/minute")
async def delete_branch(
    request: Request,
    branch_name: str,
    repo_path: str = Query(..., description="Repository path"),
    force: bool = Query(False, description="Force deletion"),
    current_user: dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id),
) -> ApiResponse:
    """
    Delete a branch.

    Deletes the specified branch from the repository.
    Cannot delete the currently active branch.
    """
    try:
        await validate_repo_path(repo_path)
        validate_branch_name(branch_name)

        result = git_ops_manager.delete_branch(path=repo_path, branch_name=branch_name, force=force)

        return ApiResponse(
            success=True,
            message=f"Branch '{branch_name}' deleted",
            data=result,
            request_id=request_id,
        )

    except GitOperationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete branch: {str(e)}",
        )


@router.post("/branches/{branch_name}/checkout", response_model=ApiResponse)
@limiter.limit("30/minute")
async def switch_branch(
    request: Request,
    branch_name: str,
    repo_path: str = Query(..., description="Repository path"),
    current_user: dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id),
) -> ApiResponse:
    """
    Switch to a different branch.

    Checks out the specified branch, making it the active branch.
    Requires a clean working directory.
    """
    try:
        await validate_repo_path(repo_path)
        validate_branch_name(branch_name)

        result = git_ops_manager.switch_branch(path=repo_path, branch_name=branch_name)

        return ApiResponse(
            success=True,
            message=f"Switched to branch '{branch_name}'",
            data=result,
            request_id=request_id,
        )

    except GitOperationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to switch branch: {str(e)}",
        )


# Commit Operations


@router.post("/commits", response_model=ApiResponse)
@limiter.limit("20/minute")
async def create_commit(
    request: Request,
    repo_path: str = Query(..., description="Repository path"),
    commit_request: CommitCreateRequest = Body(...),
    current_user: dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id),
) -> ApiResponse:
    """
    Create a new commit.

    Creates a commit with the current staged changes or all changes
    if add_all is True.
    """
    try:
        await validate_repo_path(repo_path)

        result = git_ops_manager.create_commit(
            path=repo_path,
            message=commit_request.message,
            author_name=commit_request.author_name,
            author_email=commit_request.author_email,
            add_all=commit_request.add_all,
        )

        return ApiResponse(
            success=True, message="Commit created successfully", data=result, request_id=request_id
        )

    except GitOperationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create commit: {str(e)}",
        )


# Tag Operations


@router.post("/tags", response_model=ApiResponse)
@limiter.limit("20/minute")
async def create_tag(
    request: Request,
    repo_path: str = Query(..., description="Repository path"),
    tag_request: TagCreateRequest = Body(...),
    current_user: dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id),
) -> ApiResponse:
    """
    Create a new tag.

    Creates a tag pointing to the specified commit or HEAD.
    """
    try:
        await validate_repo_path(repo_path)
        validate_tag_name(tag_request.tag_name)

        if tag_request.commit:
            validate_commit_hash(tag_request.commit)

        result = git_ops_manager.create_tag(
            path=repo_path,
            tag_name=tag_request.tag_name,
            message=tag_request.message,
            commit=tag_request.commit,
        )

        return ApiResponse(
            success=True,
            message=f"Tag '{tag_request.tag_name}' created",
            data=result,
            request_id=request_id,
        )

    except GitOperationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create tag: {str(e)}",
        )


@router.delete("/tags/{tag_name}", response_model=ApiResponse)
@limiter.limit("20/minute")
async def delete_tag(
    request: Request,
    tag_name: str,
    repo_path: str = Query(..., description="Repository path"),
    current_user: dict[str, Any] = Depends(require_user),
    request_id: str = Depends(get_request_id),
) -> ApiResponse:
    """
    Delete a tag.

    Removes the specified tag from the repository.
    """
    try:
        await validate_repo_path(repo_path)
        validate_tag_name(tag_name)

        result = git_ops_manager.delete_tag(path=repo_path, tag_name=tag_name)

        return ApiResponse(
            success=True, message=f"Tag '{tag_name}' deleted", data=result, request_id=request_id
        )

    except GitOperationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete tag: {str(e)}",
        )
