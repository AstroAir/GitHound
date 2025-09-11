"""Pydantic models for GitHound MCP server input/output validation."""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
# Pydantic v1/v2 compatibility shims for validators
try:  # Prefer v2-style if available
    from pydantic import field_validator as field_validator
    from pydantic import model_validator as model_validator
except Exception:
    # Fallback to v1 validators
    from pydantic import validator as _validator  # type: ignore
    from pydantic import root_validator as _root_validator  # type: ignore

    def field_validator(*fields):
        def _decorator(fn):
            return _validator(*fields, allow_reuse=True)(fn)
        return _decorator

    def model_validator(*, mode: str = "after"):
        def _decorator(fn):
            if mode == "before" or mode == "pre":
                return _root_validator(pre=True, allow_reuse=True)(fn)
            return _root_validator(allow_reuse=True)(fn)
        return _decorator


# Authentication and Configuration Models

class ServerConfig(BaseModel):
    """Configuration for the MCP server."""

    name: str = Field(default="GitHound MCP Server", description="Server name")
    version: str = Field(default="2.0.0", description="Server version")
    transport: str = Field(default="stdio", description="Transport type")
    host: str = Field(default="localhost",
                      description="Host for HTTP/SSE transports")
    port: int = Field(default=3000, description="Port for HTTP/SSE transports")
    log_level: str = Field(default="INFO", description="Logging level")
    enable_auth: bool = Field(
        default=False, description="Enable authentication")
    rate_limit_enabled: bool = Field(
        default=False, description="Enable rate limiting")


class MCPServerConfig(BaseModel):
    """Configuration for a single MCP server in MCP.json format."""  # [attr-defined]

    command: str = Field(..., description="Executable command to run the MCP server")
    args: list[str] = Field(default_factory=list, description="Command-line arguments")
    env: dict[str, str] = Field(default_factory=dict, description="Environment variables")
    description: str | None = Field(None, description="Server description")

    @field_validator("command")
    @classmethod
    def validate_command(cls, v: str) -> str:
        """Validate that command is not empty."""
        if not v.strip():
            raise ValueError("Command cannot be empty")
        return v.strip()


class MCPJsonConfig(BaseModel):
    """Configuration structure for MCP.json files."""  # [attr-defined]

    mcpServers: dict[str, MCPServerConfig] = Field(
        ...,
        description="Dictionary of MCP server configurations keyed by server name"
    )

    @field_validator("mcpServers")
    @classmethod
    def validate_servers(cls, v: dict[str, MCPServerConfig]) -> dict[str, MCPServerConfig]:
        """Validate that at least one server is configured."""
        if not v:
            raise ValueError("At least one MCP server must be configured")
        return v

    def get_githound_server(self) -> tuple[str, MCPServerConfig] | None:
        """
        Find and return the GitHound server configuration.

        Returns:
            Tuple of (server_name, server_config) if found, None otherwise
        """
        # Look for servers that might be GitHound
        githound_indicators = [
            "githound",
            "GitHound",
            "git-hound",
            "git_hound"
        ]

        # First, try exact matches
        for name, config in self.mcpServers.items():  # [attr-defined]
            if name.lower() in [indicator.lower() for indicator in githound_indicators]:
                return name, config

        # Then, try partial matches
        for name, config in self.mcpServers.items():  # [attr-defined]
            name_lower = name.lower()
            if any(indicator.lower() in name_lower for indicator in githound_indicators):
                return name, config

        # Finally, check if any server uses GitHound module
        for name, config in self.mcpServers.items():  # [attr-defined]
            args_str = " ".join(config.args).lower()  # [attr-defined]
            if "githound" in args_str or "mcp_server" in args_str:
                return name, config

        return None


class User(BaseModel):
    """User model for authentication."""

    username: str = Field(..., description="Username")
    role: str = Field(
        default="user", description="User role (admin, user, readonly)")
    permissions: list[str] = Field(
        default_factory=list, description="User permissions")


# MCP Tool Input/Output Models

class RepositoryInput(BaseModel):
    """Input for repository operations."""

    repo_path: str = Field(..., description="Path to the Git repository")


class CommitAnalysisInput(BaseModel):
    """Input for commit analysis operations."""

    repo_path: str = Field(..., description="Path to the Git repository")
    commit_hash: str | None = Field(
        None, description="Specific commit hash (defaults to HEAD)")


class CommitFilterInput(BaseModel):
    """Input for filtered commit retrieval."""

    repo_path: str = Field(..., description="Path to the Git repository")
    branch: str | None = Field(None, description="Branch to search")
    author_pattern: str | None = Field(
        None, description="Author name/email pattern")
    message_pattern: str | None = Field(
        None, description="Commit message pattern")
    date_from: str | None = Field(None, description="Start date (ISO format)")
    date_to: str | None = Field(None, description="End date (ISO format)")
    file_patterns: list[str] | None = Field(
        None, description="File patterns to filter")
    max_count: int | None = Field(100, description="Maximum number of commits")


class FileHistoryInput(BaseModel):
    """Input for file history operations."""

    repo_path: str = Field(..., description="Path to the Git repository")
    file_path: str = Field(..., description="Path to the file")
    branch: str | None = Field(None, description="Branch to search")
    max_count: int | None = Field(50, description="Maximum number of commits")


class BlameInput(BaseModel):
    """Input for blame operations."""

    repo_path: str = Field(..., description="Path to the Git repository")
    file_path: str = Field(..., description="Path to the file")
    commit: str | None = Field(None, description="Specific commit to blame")


class DiffInput(BaseModel):
    """Input for diff operations."""

    repo_path: str = Field(..., description="Path to the Git repository")
    from_commit: str = Field(...,
                             description="Source commit hash or reference")
    to_commit: str = Field(..., description="Target commit hash or reference")
    file_patterns: list[str] | None = Field(
        None, description="File patterns to filter")


class BranchDiffInput(BaseModel):
    """Input for branch comparison."""

    repo_path: str = Field(..., description="Path to the Git repository")
    from_branch: str = Field(..., description="Source branch name")
    to_branch: str = Field(..., description="Target branch name")
    file_patterns: list[str] | None = Field(
        None, description="File patterns to filter")


class ExportInput(BaseModel):
    """Input for data export operations."""

    repo_path: str = Field(..., description="Path to the Git repository")
    output_path: str = Field(..., description="Output file path")
    format: str = Field("json", description="Export format (json, yaml, csv)")
    include_metadata: bool = Field(
        True, description="Include metadata in export")
    pagination: dict[str, Any] | None = Field(
        None, description="Pagination options")
    fields: list[str] | None = Field(
        None, description="Specific fields to include")
    exclude_fields: list[str] | None = Field(
        None, description="Fields to exclude")


class CommitHistoryInput(BaseModel):
    """Input for commit history operations."""

    repo_path: str = Field(..., description="Path to the Git repository")
    max_count: int = Field(
        100, description="Maximum number of commits to retrieve")
    branch: str | None = Field(None, description="Branch to search")
    author: str | None = Field(None, description="Author name/email pattern")
    since: str | None = Field(None, description="Start date (ISO format)")
    until: str | None = Field(None, description="End date (ISO format)")


class FileBlameInput(BaseModel):
    """Input for file blame operations."""

    repo_path: str = Field(..., description="Path to the Git repository")
    file_path: str = Field(..., description="Path to the file")
    commit: str | None = Field(None, description="Specific commit to blame")


class CommitComparisonInput(BaseModel):
    """Input for commit comparison operations."""

    repo_path: str = Field(..., description="Path to the Git repository")
    from_commit: str = Field(...,
                             description="Source commit hash or reference")
    to_commit: str = Field(..., description="Target commit hash or reference")


class AuthorStatsInput(BaseModel):
    """Input for author statistics operations."""

    repo_path: str = Field(..., description="Path to the Git repository")
    branch: str | None = Field(None, description="Branch to analyze")
    since: str | None = Field(None, description="Start date (ISO format)")
    until: str | None = Field(None, description="End date (ISO format)")


class AdvancedSearchInput(BaseModel):
    """Input for advanced multi-modal search operations."""

    repo_path: str = Field(..., description="Path to the Git repository")
    branch: str | None = Field(
        None, description="Branch to search (defaults to current)")

    # Search criteria
    content_pattern: str | None = Field(
        None, description="Content pattern to search for")
    commit_hash: str | None = Field(None, description="Specific commit hash")
    author_pattern: str | None = Field(
        None, description="Author name or email pattern")
    message_pattern: str | None = Field(
        None, description="Commit message pattern")
    date_from: str | None = Field(None, description="Start date (ISO format)")
    date_to: str | None = Field(None, description="End date (ISO format)")
    file_path_pattern: str | None = Field(
        None, description="File path pattern")
    file_extensions: list[str] | None = Field(
        None, description="File extensions to include")

    # Search options
    case_sensitive: bool = Field(False, description="Case sensitive search")
    fuzzy_search: bool = Field(False, description="Enable fuzzy matching")
    fuzzy_threshold: float = Field(
        0.8, description="Fuzzy matching threshold (0.0-1.0)")
    max_results: int | None = Field(
        100, description="Maximum number of results")

    # File filtering
    include_globs: list[str] | None = Field(
        None, description="Glob patterns to include")
    exclude_globs: list[str] | None = Field(
        None, description="Glob patterns to exclude")
    max_file_size: int | None = Field(
        None, description="Maximum file size in bytes")
    min_commit_size: int | None = Field(
        None, description="Minimum number of files changed in commit")
    max_commit_size: int | None = Field(
        None, description="Maximum number of files changed in commit")

    @field_validator("repo_path")
    @classmethod
    def validate_repo_path(cls, v: str) -> str:
        """Validate that the repository path exists and is a directory."""
        path = Path(v)
        if not path.exists():
            raise ValueError(f"Repository path does not exist: {v}")
        if not path.is_dir():
            raise ValueError(f"Repository path is not a directory: {v}")
        return v

    @field_validator("fuzzy_threshold")
    @classmethod
    def validate_fuzzy_threshold(cls, v: float) -> float:
        """Validate fuzzy threshold is between 0.0 and 1.0."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Fuzzy threshold must be between 0.0 and 1.0")
        return v

    @field_validator("max_results")
    @classmethod
    def validate_max_results(cls, v: int | None) -> int | None:
        """Validate max_results is positive."""
        if v is not None and v <= 0:
            raise ValueError("max_results must be positive")
        if v is not None and v > 10000:
            raise ValueError("max_results cannot exceed 10000")
        return v

    @field_validator("max_file_size")
    @classmethod
    def validate_max_file_size(cls, v: int | None) -> int | None:
        """Validate max_file_size is positive."""
        if v is not None and v <= 0:
            raise ValueError("max_file_size must be positive")
        return v

    @model_validator(mode="after")
    def validate_search_criteria(self) -> "AdvancedSearchInput":
        """Validate that at least one search criterion is provided."""
        search_fields = [
            self.content_pattern,
            self.commit_hash,
            self.author_pattern,
            self.message_pattern,
            self.file_path_pattern,
        ]

        if not any(field for field in search_fields):
            raise ValueError("At least one search criterion must be provided")

        return self


class FuzzySearchInput(BaseModel):
    """Input for fuzzy search operations."""

    repo_path: str = Field(..., description="Path to the Git repository")
    search_term: str = Field(...,
                             description="Term to search for with fuzzy matching")
    threshold: float = Field(
        0.8, description="Fuzzy matching threshold (0.0-1.0)")
    search_types: list[str] | None = Field(
        None, description="Types to search: content, author, message, file_path"
    )
    branch: str | None = Field(None, description="Branch to search")
    max_results: int | None = Field(
        50, description="Maximum number of results")

    @field_validator("repo_path")
    @classmethod
    def validate_repo_path(cls, v: str) -> str:
        """Validate that the repository path exists and is a directory."""
        path = Path(v)
        if not path.exists():
            raise ValueError(f"Repository path does not exist: {v}")
        if not path.is_dir():
            raise ValueError(f"Repository path is not a directory: {v}")
        return v

    @field_validator("search_term")
    @classmethod
    def validate_search_term(cls, v: str) -> str:
        """Validate search term is not empty."""
        if not v.strip():
            raise ValueError("Search term cannot be empty")
        return v.strip()

    @field_validator("threshold")
    @classmethod
    def validate_threshold(cls, v: float) -> float:
        """Validate threshold is between 0.0 and 1.0."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Threshold must be between 0.0 and 1.0")
        return v

    @field_validator("search_types")
    @classmethod
    def validate_search_types(cls, v: list[str] | None) -> list[str] | None:
        """Validate search types are valid."""
        if v is not None:
            valid_types = {"content", "author", "message", "file_path"}
            invalid_types = set(v) - valid_types
            if invalid_types:
                raise ValueError(
                    f"Invalid search types: {invalid_types}. Valid types: {valid_types}")
        return v

    @field_validator("max_results")
    @classmethod
    def validate_max_results(cls, v: int | None) -> int | None:
        """Validate max_results is positive."""
        if v is not None and v <= 0:
            raise ValueError("max_results must be positive")
        if v is not None and v > 10000:
            raise ValueError("max_results cannot exceed 10000")
        return v


class ContentSearchInput(BaseModel):
    """Input for content-specific search operations."""

    repo_path: str = Field(..., description="Path to the Git repository")
    pattern: str = Field(..., description="Content pattern to search for")
    file_extensions: list[str] | None = Field(
        None, description="File extensions to include")
    case_sensitive: bool = Field(False, description="Case sensitive search")
    whole_word: bool = Field(False, description="Match whole words only")
    branch: str | None = Field(None, description="Branch to search")
    max_results: int | None = Field(
        100, description="Maximum number of results")


class RepositoryManagementInput(BaseModel):
    """Input for repository management operations."""

    repo_path: str = Field(..., description="Path to the Git repository")


class WebServerInput(BaseModel):
    """Input for web server operations."""

    repo_path: str = Field(..., description="Path to the Git repository")
    host: str = Field("localhost", description="Host to bind the server")
    port: int = Field(8000, description="Port to bind the server")
    auto_open: bool = Field(True, description="Automatically open browser")

    @field_validator("repo_path")
    @classmethod
    def validate_repo_path(cls, v: str) -> str:
        """Validate that the repository path exists and is a directory."""
        path = Path(v)
        if not path.exists():
            raise ValueError(f"Repository path does not exist: {v}")
        if not path.is_dir():
            raise ValueError(f"Repository path is not a directory: {v}")
        return v

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Validate port is in valid range."""
        if not 1024 <= v <= 65535:
            raise ValueError("Port must be between 1024 and 65535")
        return v

    @field_validator("host")
    @classmethod
    def validate_host(cls, v: str) -> str:
        """Validate host is not empty."""
        if not v.strip():
            raise ValueError("Host cannot be empty")
        return v.strip()
