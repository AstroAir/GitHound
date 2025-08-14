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
    search_config: Optional[SearchConfig] = Field(None, description="Advanced search configuration")
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
            return SearchQuery(
                content_pattern=self.search_query,
                commit_hash=None,
                author_pattern=None,
                message_pattern=None,
                date_from=None,
                date_to=None,
                file_path_pattern=None,
                file_extensions=None,
                case_sensitive=False,
                fuzzy_search=False,
                fuzzy_threshold=0.8,
                include_globs=None,
                exclude_globs=None,
                max_file_size=None,
                min_commit_size=None,
                max_commit_size=None
            )
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


# Enhanced models for new git functionality

class BranchInfo(BaseModel):
    """Information about a Git branch."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = Field(..., description="Branch name")
    commit_hash: str = Field(..., description="Current commit hash")
    is_remote: bool = Field(False, description="Whether this is a remote branch")
    remote_name: Optional[str] = Field(None, description="Remote name if remote branch")
    ahead_count: Optional[int] = Field(None, description="Commits ahead of base branch")
    behind_count: Optional[int] = Field(None, description="Commits behind base branch")
    last_commit_date: Optional[datetime] = Field(None, description="Date of last commit")
    last_commit_author: Optional[str] = Field(None, description="Author of last commit")


class TagInfo(BaseModel):
    """Information about a Git tag."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = Field(..., description="Tag name")
    commit_hash: str = Field(..., description="Tagged commit hash")
    message: Optional[str] = Field(None, description="Tag message")
    tagger: Optional[str] = Field(None, description="Tagger name and email")
    tag_date: Optional[datetime] = Field(None, description="Tag creation date")
    is_annotated: bool = Field(False, description="Whether this is an annotated tag")


class RemoteInfo(BaseModel):
    """Information about a Git remote."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = Field(..., description="Remote name")
    url: str = Field(..., description="Remote URL")
    fetch_url: Optional[str] = Field(None, description="Fetch URL if different")
    push_url: Optional[str] = Field(None, description="Push URL if different")


class RepositoryInfo(BaseModel):
    """Comprehensive repository information."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    path: str = Field(..., description="Repository path")
    name: str = Field(..., description="Repository name")
    is_bare: bool = Field(..., description="Whether repository is bare")
    head_commit: Optional[str] = Field(None, description="Current HEAD commit")
    active_branch: Optional[str] = Field(None, description="Currently active branch")
    branches: List[BranchInfo] = Field(default_factory=list, description="All branches")
    tags: List[TagInfo] = Field(default_factory=list, description="All tags")
    remotes: List[RemoteInfo] = Field(default_factory=list, description="Remote repositories")
    total_commits: int = Field(0, description="Total number of commits")
    contributors: List[str] = Field(default_factory=list, description="All contributors")
    first_commit_date: Optional[datetime] = Field(None, description="Date of first commit")
    last_commit_date: Optional[datetime] = Field(None, description="Date of last commit")
    repository_age_days: Optional[int] = Field(None, description="Age of repository in days")


class FileChangeInfo(BaseModel):
    """Information about a file change in a commit."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    file_path: str = Field(..., description="Path to the file")
    change_type: str = Field(..., description="Type of change (A/M/D/R/C)")
    lines_added: int = Field(0, description="Number of lines added")
    lines_deleted: int = Field(0, description="Number of lines deleted")
    is_binary: bool = Field(False, description="Whether the file is binary")
    old_file_path: Optional[str] = Field(None, description="Old file path for renames")
    similarity_index: Optional[float] = Field(None, description="Similarity index for renames")


class EnhancedCommitInfo(BaseModel):
    """Enhanced commit information with additional metadata."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Basic commit info (extends existing CommitInfo)
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

    # Enhanced metadata
    file_changes: List[FileChangeInfo] = Field(default_factory=list, description="Detailed file changes")
    branches: List[str] = Field(default_factory=list, description="Branches containing this commit")
    tags: List[str] = Field(default_factory=list, description="Tags pointing to this commit")
    is_merge: bool = Field(False, description="Whether this is a merge commit")
    merge_base: Optional[str] = Field(None, description="Merge base commit for merge commits")
    commit_size: int = Field(0, description="Total size of commit changes")


class BlameLineInfo(BaseModel):
    """Information about a single line's blame."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    line_number: int = Field(..., description="Line number (1-based)")
    content: str = Field(..., description="Line content")
    commit_hash: str = Field(..., description="Commit hash that last modified this line")
    author_name: str = Field(..., description="Author name")
    author_email: str = Field(..., description="Author email")
    commit_date: datetime = Field(..., description="Date of the commit")
    commit_message: str = Field(..., description="Commit message")


class FileBlameInfo(BaseModel):
    """Complete blame information for a file."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    file_path: str = Field(..., description="Path to the file")
    total_lines: int = Field(..., description="Total number of lines")
    blame_lines: List[BlameLineInfo] = Field(..., description="Blame information for each line")
    contributors: List[str] = Field(..., description="List of unique contributors")
    oldest_line_date: Optional[datetime] = Field(None, description="Date of the oldest line")
    newest_line_date: Optional[datetime] = Field(None, description="Date of the newest line")
    file_age_days: Optional[int] = Field(None, description="Age of the file in days")


class DiffLineInfo(BaseModel):
    """Information about a single line in a diff."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    line_number_old: Optional[int] = Field(None, description="Line number in old file")
    line_number_new: Optional[int] = Field(None, description="Line number in new file")
    content: str = Field(..., description="Line content")
    change_type: str = Field(..., description="Type of change (+/-/ )")


class FileDiffInfo(BaseModel):
    """Detailed diff information for a single file."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    file_path: str = Field(..., description="Path to the file")
    old_file_path: Optional[str] = Field(None, description="Old file path for renames")
    change_type: str = Field(..., description="Type of change")
    lines_added: int = Field(0, description="Number of lines added")
    lines_deleted: int = Field(0, description="Number of lines deleted")
    is_binary: bool = Field(False, description="Whether the file is binary")
    diff_lines: List[DiffLineInfo] = Field(default_factory=list, description="Line-by-line diff")
    similarity_index: Optional[float] = Field(None, description="Similarity index for renames")


class CommitDiffInfo(BaseModel):
    """Complete diff result for a commit comparison."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    from_commit: str = Field(..., description="Source commit hash")
    to_commit: str = Field(..., description="Target commit hash")
    files_changed: int = Field(..., description="Number of files changed")
    total_additions: int = Field(..., description="Total lines added")
    total_deletions: int = Field(..., description="Total lines deleted")
    file_diffs: List[FileDiffInfo] = Field(..., description="Detailed file diffs")
    commit_range_info: Optional[Dict[str, Any]] = Field(None, description="Additional commit range information")