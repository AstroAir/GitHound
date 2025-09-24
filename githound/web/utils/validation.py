"""
Validation utilities for GitHound web API.

Provides common validation functions and request ID generation.
"""

import uuid
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status
from git import InvalidGitRepositoryError

from ...git_handler import get_repository


def get_request_id() -> str:
    """Generate a unique request ID."""
    return str(uuid.uuid4())


async def validate_repo_path(repo_path: str) -> Path:
    """
    Validate that a repository path exists and is a valid Git repository.

    Args:
        repo_path: Path to the repository

    Returns:
        Path: Validated repository path

    Raises:
        HTTPException: If path is invalid or not a Git repository
    """
    try:
        path = Path(repo_path)

        # Check if path exists
        if not path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Repository path does not exist: {repo_path}",
            )

        # Check if it's a directory
        if not path.is_dir():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Repository path is not a directory: {repo_path}",
            )

        # Try to open as Git repository
        try:
            get_repository(path)
        except InvalidGitRepositoryError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Path is not a valid Git repository: {repo_path}",
            )

        return path

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate repository path: {str(e)}",
        )


def validate_file_path(repo_path: Path, file_path: str) -> Path:
    """
    Validate that a file path exists within a repository.

    Args:
        repo_path: Repository root path
        file_path: Relative file path within repository

    Returns:
        Path: Validated file path

    Raises:
        HTTPException: If file path is invalid or doesn't exist
    """
    try:
        # Resolve file path relative to repository
        full_path = repo_path / file_path

        # Check if file exists
        if not full_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"File does not exist: {file_path}"
            )

        # Check if it's a file
        if not full_path.is_file():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Path is not a file: {file_path}"
            )

        # Ensure file is within repository (security check)
        try:
            full_path.resolve().relative_to(repo_path.resolve())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File path is outside repository: {file_path}",
            )

        return full_path

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate file path: {str(e)}",
        )


def validate_commit_hash(commit_hash: str) -> str:
    """
    Validate a Git commit hash format.

    Args:
        commit_hash: Commit hash to validate

    Returns:
        str: Validated commit hash

    Raises:
        HTTPException: If commit hash format is invalid
    """
    if not commit_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Commit hash cannot be empty"
        )

    # Check length (Git hashes are typically 40 characters, but can be shorter)
    if len(commit_hash) < 4 or len(commit_hash) > 40:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Commit hash must be between 4 and 40 characters",
        )

    # Check if it contains only valid hexadecimal characters
    if not all(c in "0123456789abcdefABCDEF" for c in commit_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Commit hash must contain only hexadecimal characters",
        )

    return commit_hash.lower()


def validate_branch_name(branch_name: str) -> str:
    """
    Validate a Git branch name.

    Args:
        branch_name: Branch name to validate

    Returns:
        str: Validated branch name

    Raises:
        HTTPException: If branch name is invalid
    """
    if not branch_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Branch name cannot be empty"
        )

    # Check for invalid characters
    invalid_chars = [" ", "\t", "\n", "\r", "~", "^", ":", "?", "*", "[", "\\"]
    if any(char in branch_name for char in invalid_chars):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Branch name contains invalid characters: {branch_name}",
        )

    # Check for invalid patterns
    if branch_name.startswith(".") or branch_name.endswith("."):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Branch name cannot start or end with a dot",
        )

    if ".." in branch_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Branch name cannot contain consecutive dots",
        )

    if branch_name.startswith("/") or branch_name.endswith("/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Branch name cannot start or end with a slash",
        )

    return branch_name


def validate_tag_name(tag_name: str) -> str:
    """
    Validate a Git tag name.

    Args:
        tag_name: Tag name to validate

    Returns:
        str: Validated tag name

    Raises:
        HTTPException: If tag name is invalid
    """
    if not tag_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Tag name cannot be empty"
        )

    # Use similar validation as branch names
    return validate_branch_name(tag_name)


def validate_pagination_params(page: int, page_size: int) -> tuple[int, int]:
    """
    Validate pagination parameters.

    Args:
        page: Page number (1-based)
        page_size: Number of items per page

    Returns:
        tuple[int, int]: Validated (page, page_size)

    Raises:
        HTTPException: If pagination parameters are invalid
    """
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Page number must be 1 or greater"
        )

    if page_size < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Page size must be 1 or greater"
        )

    if page_size > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Page size cannot exceed 1000"
        )

    return page, page_size


def validate_search_pattern(pattern: str) -> str:
    """
    Validate a search pattern.

    Args:
        pattern: Search pattern to validate

    Returns:
        str: Validated search pattern

    Raises:
        HTTPException: If pattern is invalid
    """
    if not pattern:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Search pattern cannot be empty"
        )

    if len(pattern) > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search pattern cannot exceed 1000 characters",
        )

    return pattern


def validate_file_extensions(extensions: list[str]) -> list[str]:
    """
    Validate file extensions list.

    Args:
        extensions: List of file extensions

    Returns:
        list[str]: Validated extensions

    Raises:
        HTTPException: If extensions are invalid
    """
    if not extensions:
        return []

    validated = []
    for ext in extensions:
        if not ext:
            continue

        # Remove leading dot if present
        if ext.startswith("."):
            ext = ext[1:]

        # Check for invalid characters
        if any(char in ext for char in [" ", "/", "\\", ":", "*", "?", '"', "<", ">", "|"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid file extension: {ext}"
            )

        validated.append(ext.lower())

    return validated


def validate_timeout(timeout_seconds: int) -> int:
    """
    Validate timeout value.

    Args:
        timeout_seconds: Timeout in seconds

    Returns:
        int: Validated timeout

    Raises:
        HTTPException: If timeout is invalid
    """
    if timeout_seconds < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Timeout must be at least 1 second"
        )

    if timeout_seconds > 3600:  # 1 hour max
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Timeout cannot exceed 3600 seconds (1 hour)",
        )

    return timeout_seconds
