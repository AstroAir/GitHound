"""Core data models for GitHound."""

import dataclasses
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, ConfigDict


class SearchType(str, Enum):
    """Types of searches supported by GitHound."""
    CONTENT = "content"
    COMMIT_HASH = "commit_hash"
    AUTHOR = "author"
    MESSAGE = "message"
    DATE_RANGE = "date_range"
    FILE_PATH = "file_path"
    FILE_TYPE = "file_type"
    COMBINED = "combined"


class OutputFormat(str, Enum):
    """Supported output formats."""
    TEXT = "text"
    JSON = "json"
    CSV = "csv"


class SearchQuery(BaseModel):
    """Enhanced search query supporting multiple search types."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Content search
    content_pattern: Optional[str] = Field(None, description="Regex pattern to search in file content")

    # Commit-based search
    commit_hash: Optional[str] = Field(None, description="Specific commit hash to search")
    author_pattern: Optional[str] = Field(None, description="Author name or email pattern")
    message_pattern: Optional[str] = Field(None, description="Commit message pattern")

    # Date-based search
    date_from: Optional[datetime] = Field(None, description="Search commits from this date")
    date_to: Optional[datetime] = Field(None, description="Search commits until this date")

    # File-based search
    file_path_pattern: Optional[str] = Field(None, description="File path pattern")
    file_extensions: Optional[List[str]] = Field(None, description="File extensions to include")

    # Search behavior
    case_sensitive: bool = Field(False, description="Whether search should be case sensitive")
    fuzzy_search: bool = Field(False, description="Enable fuzzy matching")
    fuzzy_threshold: float = Field(0.8, description="Fuzzy matching threshold (0.0-1.0)")

    # Filtering
    include_globs: Optional[List[str]] = Field(None, description="Glob patterns to include")
    exclude_globs: Optional[List[str]] = Field(None, description="Glob patterns to exclude")
    max_file_size: Optional[int] = Field(None, description="Maximum file size in bytes")
    min_commit_size: Optional[int] = Field(None, description="Minimum number of files changed in commit")
    max_commit_size: Optional[int] = Field(None, description="Maximum number of files changed in commit")


class CommitInfo(BaseModel):
    """Detailed information about a Git commit."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    hash: str = Field(..., description="Commit hash")
    short_hash: str = Field(..., description="Short commit hash")
    author_name: str = Field(..., description="Author name")
    author_email: str = Field(..., description="Author email")
    committer_name: str = Field(..., description="Committer name")
    committer_email: str = Field(..., description="Committer email")
    message: str = Field(..., description="Commit message")
    date: datetime = Field(..., description="Commit date")
    files_changed: int = Field(..., description="Number of files changed")
    insertions: int = Field(0, description="Number of lines inserted")
    deletions: int = Field(0, description="Number of lines deleted")
    parents: List[str] = Field(default_factory=list, description="Parent commit hashes")


class SearchResult(BaseModel):
    """Enhanced search result with relevance scoring and metadata."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Core result data
    commit_hash: str = Field(..., description="Commit hash where match was found")
    file_path: Path = Field(..., description="Path to the file containing the match")
    line_number: Optional[int] = Field(None, description="Line number of the match (for content searches)")
    matching_line: Optional[str] = Field(None, description="The actual matching line (for content searches)")

    # Enhanced metadata
    commit_info: Optional[CommitInfo] = Field(None, description="Detailed commit information")
    search_type: SearchType = Field(..., description="Type of search that found this result")
    relevance_score: float = Field(0.0, description="Relevance score (0.0-1.0)")
    match_context: Optional[Dict[str, Any]] = Field(None, description="Additional context about the match")

    # Performance metadata
    search_time_ms: Optional[float] = Field(None, description="Time taken to find this result in milliseconds")


class SearchMetrics(BaseModel):
    """Performance and statistics metrics for a search operation."""

    total_commits_searched: int = Field(0, description="Total number of commits searched")
    total_files_searched: int = Field(0, description="Total number of files searched")
    total_results_found: int = Field(0, description="Total number of results found")
    search_duration_ms: float = Field(0.0, description="Total search duration in milliseconds")
    cache_hits: int = Field(0, description="Number of cache hits")
    cache_misses: int = Field(0, description="Number of cache misses")
    memory_usage_mb: Optional[float] = Field(None, description="Peak memory usage in MB")


class SearchConfig(BaseModel):
    """Advanced configuration for a search operation."""

    # Legacy compatibility
    include_globs: Optional[List[str]] = Field(None, description="Glob patterns to include")
    exclude_globs: Optional[List[str]] = Field(None, description="Glob patterns to exclude")
    case_sensitive: bool = Field(False, description="Whether search should be case sensitive")

    # Performance settings
    max_results: Optional[int] = Field(None, description="Maximum number of results to return")
    timeout_seconds: Optional[int] = Field(None, description="Search timeout in seconds")
    enable_caching: bool = Field(True, description="Whether to enable result caching")
    cache_ttl_seconds: int = Field(3600, description="Cache TTL in seconds")

    # Progress reporting
    enable_progress: bool = Field(True, description="Whether to report search progress")
    progress_callback: Optional[Any] = Field(None, description="Progress callback function")


class GitHoundConfig(BaseModel):
    """Enhanced configuration for a GitHound search operation."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Core settings
    repo_path: Path = Field(..., description="Path to the Git repository")
    search_query: Union[str, SearchQuery] = Field(..., description="Search query (string for backward compatibility)")
    branch: Optional[str] = Field(None, description="Branch to search (defaults to current branch)")
    output_format: OutputFormat = Field(OutputFormat.TEXT, description="Output format")

    # Enhanced settings
    search_config: SearchConfig = Field(default_factory=SearchConfig, description="Advanced search configuration")
    enable_ranking: bool = Field(True, description="Whether to enable result ranking")
    parallel_search: bool = Field(True, description="Whether to enable parallel searching")

    @property
    def is_legacy_query(self) -> bool:
        """Check if this is a legacy string query."""
        return isinstance(self.search_query, str)

    def get_search_query(self) -> SearchQuery:
        """Get the search query as a SearchQuery object."""
        if isinstance(self.search_query, str):
            # Convert legacy string query to SearchQuery
            return SearchQuery(content_pattern=self.search_query)
        return self.search_query


# Legacy dataclass models for backward compatibility
@dataclasses.dataclass
class LegacySearchResult:
    """Legacy search result for backward compatibility."""
    commit_hash: str
    file_path: Path
    line_number: int
    matching_line: str


@dataclasses.dataclass
class LegacySearchConfig:
    """Legacy search config for backward compatibility."""
    include_globs: Optional[List[str]] = None
    exclude_globs: Optional[List[str]] = None
    case_sensitive: bool = False


@dataclasses.dataclass
class LegacyGitHoundConfig:
    """Legacy GitHound config for backward compatibility."""
    repo_path: Path
    search_query: str
    branch: Optional[str] = None
    output_format: Literal["text", "json"] = "text"
    search_config: LegacySearchConfig = dataclasses.field(default_factory=LegacySearchConfig)