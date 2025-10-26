"""Core data models for GitHound."""

import dataclasses
from collections.abc import Callable
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class SearchType(str, Enum):
    """Types of searches supported by GitHound."""

    # Basic search types
    CONTENT = "content"
    COMMIT_HASH = "commit_hash"
    AUTHOR = "author"
    MESSAGE = "message"
    DATE_RANGE = "date_range"
    FILE_PATH = "file_path"
    FILE_TYPE = "file_type"
    COMBINED = "combined"

    # Advanced analysis types
    BRANCH_ANALYSIS = "branch_analysis"
    DIFF_ANALYSIS = "diff_analysis"
    PATTERN_DETECTION = "pattern_detection"
    STATISTICAL_ANALYSIS = "statistical_analysis"
    TEMPORAL_ANALYSIS = "temporal_analysis"
    TAG_ANALYSIS = "tag_analysis"
    CODE_QUALITY = "code_quality"
    SECURITY_ANALYSIS = "security_analysis"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    REPOSITORY_INSIGHTS = "repository_insights"


class OutputFormat(str, Enum):
    """Supported output formats."""

    TEXT = "text"
    JSON = "json"
    CSV = "csv"


class SearchQuery(BaseModel):
    """Enhanced search query supporting multiple search types."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Content search
    content_pattern: str | None = Field(None, description="Regex pattern to search in file content")

    # Commit-based search
    commit_hash: str | None = Field(None, description="Specific commit hash to search")
    author_pattern: str | None = Field(None, description="Author name or email pattern")
    message_pattern: str | None = Field(None, description="Commit message pattern")

    # Date-based search
    date_from: datetime | None = Field(None, description="Search commits from this date")
    date_to: datetime | None = Field(None, description="Search commits until this date")

    # File-based search
    file_path_pattern: str | None = Field(None, description="File path pattern")
    file_extensions: list[str] | None = Field(None, description="File extensions to include")

    # Search behavior
    case_sensitive: bool = Field(False, description="Whether search should be case sensitive")
    fuzzy_search: bool = Field(False, description="Enable fuzzy matching")
    fuzzy_threshold: float = Field(0.8, description="Fuzzy matching threshold (0.0-1.0)")

    # Filtering
    include_globs: list[str] | None = Field(None, description="Glob patterns to include")
    exclude_globs: list[str] | None = Field(None, description="Glob patterns to exclude")
    max_file_size: int | None = Field(None, description="Maximum file size in bytes")
    min_commit_size: int | None = Field(
        None, description="Minimum number of files changed in commit"
    )
    max_commit_size: int | None = Field(
        None, description="Maximum number of files changed in commit"
    )

    # Advanced analysis modes
    branch_analysis: bool = Field(
        False, description="Enable branch structure and relationship analysis"
    )
    branch_pattern: str | None = Field(None, description="Pattern to match branch names")
    compare_branches: bool = Field(False, description="Enable branch comparison analysis")

    diff_analysis: bool = Field(False, description="Enable diff and change pattern analysis")
    change_analysis: bool = Field(False, description="Enable detailed change analysis")
    commit_range: str | None = Field(
        None, description="Commit range for diff analysis (e.g., 'HEAD~10..HEAD')"
    )

    pattern_analysis: bool = Field(False, description="Enable code pattern detection")
    code_quality: bool = Field(False, description="Enable code quality analysis")
    security_patterns: bool = Field(False, description="Enable security vulnerability detection")

    statistical_analysis: bool = Field(False, description="Enable statistical repository analysis")
    temporal_analysis: bool = Field(False, description="Enable temporal pattern analysis")

    tag_pattern: str | None = Field(None, description="Pattern to match tag names")
    version_analysis: bool = Field(False, description="Enable version and release analysis")
    release_analysis: bool = Field(False, description="Enable release pattern analysis")

    # Performance and behavior settings
    enable_caching: bool = Field(True, description="Enable result caching")
    cache_ttl_seconds: int = Field(3600, description="Cache time-to-live in seconds")
    enable_ranking: bool = Field(True, description="Enable result ranking")
    enable_parallel: bool = Field(True, description="Enable parallel search execution")
    max_workers: int = Field(4, description="Maximum number of parallel workers")

    # Result processing options
    enable_enrichment: bool = Field(
        False, description="Enable result enrichment with additional context"
    )
    context_lines: int = Field(3, description="Number of context lines around matches")
    group_results: bool = Field(False, description="Enable result grouping")
    group_by: list[str] | None = Field(
        None, description="Fields to group results by (file_type, author, etc.)"
    )

    # Search scope and limits
    max_results: int | None = Field(None, description="Maximum number of results to return")
    timeout_seconds: int | None = Field(None, description="Search timeout in seconds")
    search_depth: int | None = Field(None, description="Maximum search depth (commits to analyze)")

    # Text processing options
    text: str | None = Field(
        None, description="Free-form text query for natural language processing"
    )
    semantic_search: bool = Field(False, description="Enable semantic search capabilities")
    language_detection: bool = Field(
        False, description="Enable programming language detection and filtering"
    )

    # Helper methods for query analysis
    def has_basic_search_criteria(self) -> bool:
        """Check if query has basic search criteria."""
        return any(
            [
                self.content_pattern,
                self.commit_hash,
                self.author_pattern,
                self.message_pattern,
                self.file_path_pattern,
                self.file_extensions,
                self.date_from,
                self.date_to,
            ]
        )

    def has_advanced_analysis(self) -> bool:
        """Check if query requests advanced analysis."""
        return any(
            [
                self.branch_analysis,
                self.diff_analysis,
                self.pattern_analysis,
                self.statistical_analysis,
                self.temporal_analysis,
                self.version_analysis,
                self.code_quality,
                self.security_patterns,
            ]
        )

    def get_enabled_analysis_types(self) -> list[str]:
        """Get list of enabled analysis types."""
        analysis_types = []
        if self.branch_analysis:
            analysis_types.append("branch")
        if self.diff_analysis or self.change_analysis:
            analysis_types.append("diff")
        if self.pattern_analysis or self.code_quality or self.security_patterns:
            analysis_types.append("pattern")
        if self.statistical_analysis:
            analysis_types.append("statistical")
        if self.temporal_analysis:
            analysis_types.append("temporal")
        if self.version_analysis or self.release_analysis:
            analysis_types.append("version")
        return analysis_types

    def is_complex_query(self) -> bool:
        """Check if this is a complex query requiring multiple searchers."""
        criteria_count = sum(
            [
                bool(self.content_pattern),
                bool(self.author_pattern),
                bool(self.message_pattern),
                bool(self.file_path_pattern),
                bool(self.commit_hash),
                bool(self.date_from or self.date_to),
            ]
        )
        return criteria_count >= 2 or self.has_advanced_analysis()

    def get_search_scope(self) -> dict[str, Any]:
        """Get search scope configuration."""
        return {
            "max_results": self.max_results,
            "timeout_seconds": self.timeout_seconds,
            "search_depth": self.search_depth,
            "max_workers": self.max_workers,
            "enable_parallel": self.enable_parallel,
        }

    def get_processing_options(self) -> dict[str, Any]:
        """Get result processing options."""
        return {
            "enable_enrichment": self.enable_enrichment,
            "context_lines": self.context_lines,
            "group_results": self.group_results,
            "group_by": self.group_by or [],
            "enable_ranking": self.enable_ranking,
        }

    def get_caching_config(self) -> dict[str, Any]:
        """Get caching configuration."""
        return {
            "enable_caching": self.enable_caching,
            "cache_ttl_seconds": self.cache_ttl_seconds,
        }


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
    parents: list[str] = Field(default_factory=list, description="Parent commit hashes")


class SearchResult(BaseModel):
    """Enhanced search result with relevance scoring and metadata."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Core result data
    commit_hash: str = Field(..., description="Commit hash where match was found")
    file_path: Path = Field(..., description="Path to the file containing the match")
    line_number: int | None = Field(
        None, description="Line number of the match (for content searches)"
    )
    matching_line: str | None = Field(
        None, description="The actual matching line (for content searches)"
    )

    # Enhanced metadata
    commit_info: CommitInfo | None = Field(None, description="Detailed commit information")
    search_type: SearchType = Field(..., description="Type of search that found this result")
    relevance_score: float = Field(0.0, description="Relevance score (0.0-1.0)")
    match_context: dict[str, Any] | None = Field(
        None, description="Additional context about the match"
    )

    # Performance metadata
    search_time_ms: float | None = Field(
        None, description="Time taken to find this result in milliseconds"
    )


class SearchMetrics(BaseModel):
    """Performance and statistics metrics for a search operation."""

    total_commits_searched: int = Field(0, description="Total number of commits searched")
    total_files_searched: int = Field(0, description="Total number of files searched")
    total_results_found: int = Field(0, description="Total number of results found")
    search_duration_ms: float = Field(0.0, description="Total search duration in milliseconds")
    cache_hits: int = Field(0, description="Number of cache hits")
    cache_misses: int = Field(0, description="Number of cache misses")
    memory_usage_mb: float | None = Field(None, description="Peak memory usage in MB")


class SearchConfig(BaseModel):
    """Advanced configuration for a search operation."""

    # Legacy compatibility
    include_globs: list[str] | None = Field(None, description="Glob patterns to include")
    exclude_globs: list[str] | None = Field(None, description="Glob patterns to exclude")
    case_sensitive: bool = Field(False, description="Whether search should be case sensitive")

    # Performance settings
    max_results: int | None = Field(None, description="Maximum number of results to return")
    timeout_seconds: int | None = Field(None, description="Search timeout in seconds")
    enable_caching: bool = Field(True, description="Whether to enable result caching")
    cache_ttl_seconds: int = Field(3600, description="Cache TTL in seconds")

    # Progress reporting
    enable_progress: bool = Field(True, description="Whether to report search progress")
    progress_callback: Callable[[str, float], None] | None = Field(
        None, description="Progress callback function"
    )


class GitHoundConfig(BaseModel):
    """Enhanced configuration for a GitHound search operation."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Core settings
    repo_path: Path = Field(..., description="Path to the Git repository")
    search_query: str | SearchQuery = Field(
        ..., description="Search query (string for backward compatibility)"
    )
    branch: str | None = Field(None, description="Branch to search (defaults to current branch)")
    output_format: OutputFormat = Field(OutputFormat.TEXT, description="Output format")

    # Enhanced settings
    search_config: SearchConfig | None = Field(None, description="Advanced search configuration")
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
                max_commit_size=None,
            )
        return self.search_query


class SearchEngineConfig(BaseModel):
    """Comprehensive configuration for the GitHound search engine."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Core engine settings
    enable_advanced_searchers: bool = Field(
        True, description="Enable advanced searchers (branch, diff, pattern, etc.)"
    )
    enable_basic_searchers: bool = Field(
        True, description="Enable basic searchers (content, author, etc.)"
    )

    # Performance settings
    max_workers: int = Field(4, description="Maximum number of parallel workers")
    enable_parallel_execution: bool = Field(True, description="Enable parallel searcher execution")
    search_timeout_seconds: int = Field(300, description="Global search timeout in seconds")
    max_memory_mb: int = Field(1024, description="Maximum memory usage in MB")

    # Caching configuration
    enable_caching: bool = Field(True, description="Enable result caching")
    cache_backend: Literal["memory", "redis"] = Field("memory", description="Cache backend type")
    cache_ttl_seconds: int = Field(3600, description="Default cache TTL in seconds")
    cache_max_size: int = Field(1000, description="Maximum cache entries (memory backend)")
    redis_url: str = Field("redis://localhost:6379", description="Redis URL for caching")

    # Result processing
    enable_ranking: bool = Field(True, description="Enable result ranking")
    enable_result_processing: bool = Field(True, description="Enable result processing pipeline")
    default_max_results: int = Field(1000, description="Default maximum results per search")

    # Ranking configuration
    ranking_weights: dict[str, float] = Field(
        default_factory=lambda: {
            "query_match": 0.3,
            "recency": 0.2,
            "file_importance": 0.15,
            "author_relevance": 0.1,
            "commit_quality": 0.1,
            "context_relevance": 0.1,
            "frequency": 0.05,
        },
        description="Weights for ranking factors",
    )

    # Feature toggles
    enable_fuzzy_search: bool = Field(True, description="Enable fuzzy search capabilities")
    enable_semantic_search: bool = Field(False, description="Enable semantic search (experimental)")
    enable_pattern_detection: bool = Field(True, description="Enable code pattern detection")
    enable_security_analysis: bool = Field(
        True, description="Enable security vulnerability detection"
    )

    # Monitoring and analytics
    enable_metrics: bool = Field(True, description="Enable search metrics collection")
    enable_analytics: bool = Field(False, description="Enable search analytics")
    metrics_retention_days: int = Field(30, description="Metrics retention period in days")

    # Repository limits
    max_commits_to_analyze: int = Field(5000, description="Maximum commits to analyze per search")
    max_files_per_commit: int = Field(100, description="Maximum files to analyze per commit")
    max_file_size_mb: int = Field(10, description="Maximum file size to analyze in MB")

    # Error handling
    continue_on_errors: bool = Field(
        True, description="Continue search when individual searchers fail"
    )
    max_error_rate: float = Field(0.1, description="Maximum acceptable error rate (0.0-1.0)")

    # Logging configuration
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        "INFO", description="Logging level"
    )
    log_search_queries: bool = Field(False, description="Log search queries for debugging")
    log_performance_metrics: bool = Field(True, description="Log performance metrics")

    def get_cache_config(self) -> dict[str, Any]:
        """Get cache configuration."""
        return {
            "enable_caching": self.enable_caching,
            "backend": self.cache_backend,
            "ttl_seconds": self.cache_ttl_seconds,
            "max_size": self.cache_max_size,
            "redis_url": self.redis_url,
        }

    def get_performance_config(self) -> dict[str, Any]:
        """Get performance configuration."""
        return {
            "max_workers": self.max_workers,
            "enable_parallel": self.enable_parallel_execution,
            "timeout_seconds": self.search_timeout_seconds,
            "max_memory_mb": self.max_memory_mb,
            "max_commits": self.max_commits_to_analyze,
            "max_files_per_commit": self.max_files_per_commit,
            "max_file_size_mb": self.max_file_size_mb,
        }

    def get_feature_flags(self) -> dict[str, bool]:
        """Get feature flags."""
        return {
            "advanced_searchers": self.enable_advanced_searchers,
            "basic_searchers": self.enable_basic_searchers,
            "fuzzy_search": self.enable_fuzzy_search,
            "semantic_search": self.enable_semantic_search,
            "pattern_detection": self.enable_pattern_detection,
            "security_analysis": self.enable_security_analysis,
            "ranking": self.enable_ranking,
            "result_processing": self.enable_result_processing,
            "metrics": self.enable_metrics,
            "analytics": self.enable_analytics,
        }

    def validate_config(self) -> list[str]:
        """Validate configuration and return list of issues."""
        issues = []

        if self.max_workers < 1:
            issues.append("max_workers must be at least 1")

        if self.search_timeout_seconds < 1:
            issues.append("search_timeout_seconds must be at least 1")

        if self.cache_ttl_seconds < 0:
            issues.append("cache_ttl_seconds must be non-negative")

        if not (0.0 <= self.max_error_rate <= 1.0):
            issues.append("max_error_rate must be between 0.0 and 1.0")

        # Validate ranking weights sum to approximately 1.0
        weight_sum = sum(self.ranking_weights.values())
        if abs(weight_sum - 1.0) > 0.01:
            issues.append(f"ranking_weights should sum to 1.0, got {weight_sum}")

        return issues


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

    include_globs: list[str] | None = None
    exclude_globs: list[str] | None = None
    case_sensitive: bool = False


@dataclasses.dataclass
class LegacyGitHoundConfig:
    """Legacy GitHound config for backward compatibility."""

    repo_path: Path
    search_query: str
    branch: str | None = None
    output_format: Literal["text", "json"] = "text"
    search_config: LegacySearchConfig = dataclasses.field(  # [attr-defined]
        default_factory=LegacySearchConfig
    )


# Enhanced models for new git functionality


class BranchInfo(BaseModel):
    """Information about a Git branch."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = Field(..., description="Branch name")
    commit_hash: str = Field(..., description="Current commit hash")
    is_remote: bool = Field(False, description="Whether this is a remote branch")
    remote_name: str | None = Field(None, description="Remote name if remote branch")
    ahead_count: int | None = Field(None, description="Commits ahead of base branch")
    behind_count: int | None = Field(None, description="Commits behind base branch")
    last_commit_date: datetime | None = Field(None, description="Date of last commit")
    last_commit_author: str | None = Field(None, description="Author of last commit")


class TagInfo(BaseModel):
    """Information about a Git tag."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = Field(..., description="Tag name")
    commit_hash: str = Field(..., description="Tagged commit hash")
    message: str | None = Field(None, description="Tag message")
    tagger: str | None = Field(None, description="Tagger name and email")
    tag_date: datetime | None = Field(None, description="Tag creation date")
    is_annotated: bool = Field(False, description="Whether this is an annotated tag")


class RemoteInfo(BaseModel):
    """Information about a Git remote."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = Field(..., description="Remote name")
    url: str = Field(..., description="Remote URL")
    fetch_url: str | None = Field(None, description="Fetch URL if different")
    push_url: str | None = Field(None, description="Push URL if different")


class RepositoryInfo(BaseModel):
    """Comprehensive repository information."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    path: str = Field(..., description="Repository path")
    name: str = Field(..., description="Repository name")
    is_bare: bool = Field(..., description="Whether repository is bare")
    head_commit: str | None = Field(None, description="Current HEAD commit")
    active_branch: str | None = Field(None, description="Currently active branch")
    branches: list[BranchInfo] = Field(default_factory=list, description="All branches")
    tags: list[TagInfo] = Field(default_factory=list, description="All tags")
    remotes: list[RemoteInfo] = Field(default_factory=list, description="Remote repositories")
    total_commits: int = Field(0, description="Total number of commits")
    contributors: list[str] = Field(default_factory=list, description="All contributors")
    first_commit_date: datetime | None = Field(None, description="Date of first commit")
    last_commit_date: datetime | None = Field(None, description="Date of last commit")
    repository_age_days: int | None = Field(None, description="Age of repository in days")


class FileChangeInfo(BaseModel):
    """Information about a file change in a commit."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    file_path: str = Field(..., description="Path to the file")
    change_type: str = Field(..., description="Type of change (A/M/D/R/C)")
    lines_added: int = Field(0, description="Number of lines added")
    lines_deleted: int = Field(0, description="Number of lines deleted")
    is_binary: bool = Field(False, description="Whether the file is binary")
    old_file_path: str | None = Field(None, description="Old file path for renames")
    similarity_index: float | None = Field(None, description="Similarity index for renames")


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
    parents: list[str] = Field(default_factory=list, description="Parent commit hashes")

    # Enhanced metadata
    file_changes: list[FileChangeInfo] = Field(
        default_factory=list, description="Detailed file changes"
    )
    branches: list[str] = Field(default_factory=list, description="Branches containing this commit")
    tags: list[str] = Field(default_factory=list, description="Tags pointing to this commit")
    is_merge: bool = Field(False, description="Whether this is a merge commit")
    merge_base: str | None = Field(None, description="Merge base commit for merge commits")
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
    blame_lines: list[BlameLineInfo] = Field(..., description="Blame information for each line")
    contributors: list[str] = Field(..., description="List of unique contributors")
    oldest_line_date: datetime | None = Field(None, description="Date of the oldest line")
    newest_line_date: datetime | None = Field(None, description="Date of the newest line")
    file_age_days: int | None = Field(None, description="Age of the file in days")


class DiffLineInfo(BaseModel):
    """Information about a single line in a diff."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    line_number_old: int | None = Field(None, description="Line number in old file")
    line_number_new: int | None = Field(None, description="Line number in new file")
    content: str = Field(..., description="Line content")
    change_type: str = Field(..., description="Type of change (+/-/ )")


class FileDiffInfo(BaseModel):
    """Detailed diff information for a single file."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    file_path: str = Field(..., description="Path to the file")
    old_file_path: str | None = Field(None, description="Old file path for renames")
    change_type: str = Field(..., description="Type of change")
    lines_added: int = Field(0, description="Number of lines added")
    lines_deleted: int = Field(0, description="Number of lines deleted")
    is_binary: bool = Field(False, description="Whether the file is binary")
    diff_lines: list[DiffLineInfo] = Field(default_factory=list, description="Line-by-line diff")
    similarity_index: float | None = Field(None, description="Similarity index for renames")


class CommitDiffInfo(BaseModel):
    """Complete diff result for a commit comparison."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    from_commit: str = Field(..., description="Source commit hash")
    to_commit: str = Field(..., description="Target commit hash")
    files_changed: int = Field(..., description="Number of files changed")
    total_additions: int = Field(..., description="Total lines added")
    total_deletions: int = Field(..., description="Total lines deleted")
    file_diffs: list[FileDiffInfo] = Field(..., description="Detailed file diffs")
    commit_range_info: dict[str, Any] | None = Field(
        None, description="Additional commit range information"
    )
