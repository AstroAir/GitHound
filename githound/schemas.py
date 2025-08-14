"""Standardized JSON/YAML schemas for GitHound data structures."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, ConfigDict


class OutputFormat(str, Enum):
    """Supported output formats."""
    JSON = "json"
    YAML = "yaml"
    CSV = "csv"
    XML = "xml"
    TEXT = "text"


class SortOrder(str, Enum):
    """Sort order options."""
    ASC = "asc"
    DESC = "desc"


class FilterOperator(str, Enum):
    """Filter operators for data filtering."""
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    GREATER_EQUAL = "gte"
    LESS_EQUAL = "lte"
    IN = "in"
    NOT_IN = "not_in"
    REGEX = "regex"


class DataFilter(BaseModel):
    """Generic data filter for structured output."""
    
    field: str = Field(..., description="Field name to filter on")
    operator: FilterOperator = Field(..., description="Filter operator")
    value: Union[str, int, float, bool, List[Any]] = Field(..., description="Filter value")
    case_sensitive: bool = Field(True, description="Whether string comparisons are case sensitive")


class SortCriteria(BaseModel):
    """Sort criteria for structured output."""
    
    field: str = Field(..., description="Field name to sort by")
    order: SortOrder = Field(SortOrder.ASC, description="Sort order")


class PaginationInfo(BaseModel):
    """Pagination information for large datasets."""
    
    page: int = Field(1, description="Current page number (1-based)")
    page_size: int = Field(100, description="Number of items per page")
    total_items: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_previous: bool = Field(..., description="Whether there is a previous page")


class ExportOptions(BaseModel):
    """Options for data export."""
    
    format: OutputFormat = Field(OutputFormat.JSON, description="Output format")
    include_metadata: bool = Field(True, description="Include metadata in output")
    pretty_print: bool = Field(True, description="Pretty print output")
    filters: List[DataFilter] = Field(default_factory=list, description="Data filters")
    sort_by: List[SortCriteria] = Field(default_factory=list, description="Sort criteria")
    pagination: Optional[PaginationInfo] = Field(None, description="Pagination info")
    fields: Optional[List[str]] = Field(None, description="Specific fields to include")
    exclude_fields: Optional[List[str]] = Field(None, description="Fields to exclude")


# Git-specific schemas

class AuthorSchema(BaseModel):
    """Schema for git author information."""
    
    name: str = Field(..., description="Author name")
    email: str = Field(..., description="Author email")
    commits_count: Optional[int] = Field(None, description="Number of commits by this author")
    lines_authored: Optional[int] = Field(None, description="Number of lines authored")
    first_commit_date: Optional[datetime] = Field(None, description="Date of first commit")
    last_commit_date: Optional[datetime] = Field(None, description="Date of last commit")
    files_touched: Optional[int] = Field(None, description="Number of files touched")


class BranchSchema(BaseModel):
    """Schema for git branch information."""
    
    name: str = Field(..., description="Branch name")
    commit_hash: str = Field(..., description="Current commit hash")
    is_remote: bool = Field(False, description="Whether this is a remote branch")
    remote_name: Optional[str] = Field(None, description="Remote name if remote branch")
    ahead_count: Optional[int] = Field(None, description="Commits ahead of base branch")
    behind_count: Optional[int] = Field(None, description="Commits behind base branch")
    last_commit_date: Optional[datetime] = Field(None, description="Date of last commit")
    last_commit_author: Optional[str] = Field(None, description="Author of last commit")


class TagSchema(BaseModel):
    """Schema for git tag information."""
    
    name: str = Field(..., description="Tag name")
    commit_hash: str = Field(..., description="Tagged commit hash")
    message: Optional[str] = Field(None, description="Tag message")
    tagger: Optional[str] = Field(None, description="Tagger name and email")
    tag_date: Optional[datetime] = Field(None, description="Tag creation date")
    is_annotated: bool = Field(False, description="Whether this is an annotated tag")


class FileChangeSchema(BaseModel):
    """Schema for file change information."""
    
    file_path: str = Field(..., description="Path to the file")
    change_type: str = Field(..., description="Type of change (A/M/D/R/C)")
    lines_added: int = Field(0, description="Number of lines added")
    lines_deleted: int = Field(0, description="Number of lines deleted")
    is_binary: bool = Field(False, description="Whether the file is binary")
    old_file_path: Optional[str] = Field(None, description="Old file path for renames")


class CommitSchema(BaseModel):
    """Schema for git commit information."""
    
    hash: str = Field(..., description="Full commit hash")
    short_hash: str = Field(..., description="Short commit hash")
    author: AuthorSchema = Field(..., description="Commit author")
    committer: AuthorSchema = Field(..., description="Commit committer")
    message: str = Field(..., description="Commit message")
    date: datetime = Field(..., description="Commit date")
    parent_hashes: List[str] = Field(default_factory=list, description="Parent commit hashes")
    files_changed: List[FileChangeSchema] = Field(default_factory=list, description="Files changed in this commit")
    stats: Dict[str, int] = Field(default_factory=dict, description="Commit statistics")
    branches: List[str] = Field(default_factory=list, description="Branches containing this commit")
    tags: List[str] = Field(default_factory=list, description="Tags pointing to this commit")


class BlameLineSchema(BaseModel):
    """Schema for git blame line information."""
    
    line_number: int = Field(..., description="Line number (1-based)")
    content: str = Field(..., description="Line content")
    commit_hash: str = Field(..., description="Commit hash that last modified this line")
    author: AuthorSchema = Field(..., description="Author of the line")
    commit_date: datetime = Field(..., description="Date of the commit")
    commit_message: str = Field(..., description="Commit message")


class FileBlameSchema(BaseModel):
    """Schema for complete file blame information."""
    
    file_path: str = Field(..., description="Path to the file")
    total_lines: int = Field(..., description="Total number of lines")
    lines: List[BlameLineSchema] = Field(..., description="Blame information for each line")
    contributors: List[AuthorSchema] = Field(..., description="All contributors to this file")
    oldest_line_date: Optional[datetime] = Field(None, description="Date of the oldest line")
    newest_line_date: Optional[datetime] = Field(None, description="Date of the newest line")
    file_age_days: Optional[int] = Field(None, description="Age of the file in days")


class DiffLineSchema(BaseModel):
    """Schema for diff line information."""
    
    line_number_old: Optional[int] = Field(None, description="Line number in old file")
    line_number_new: Optional[int] = Field(None, description="Line number in new file")
    content: str = Field(..., description="Line content")
    change_type: str = Field(..., description="Type of change (+/-/ )")


class FileDiffSchema(BaseModel):
    """Schema for file diff information."""
    
    file_path: str = Field(..., description="Path to the file")
    old_file_path: Optional[str] = Field(None, description="Old file path for renames")
    change_type: str = Field(..., description="Type of change")
    lines_added: int = Field(0, description="Number of lines added")
    lines_deleted: int = Field(0, description="Number of lines deleted")
    is_binary: bool = Field(False, description="Whether the file is binary")
    diff_lines: List[DiffLineSchema] = Field(default_factory=list, description="Line-by-line diff")
    similarity_index: Optional[float] = Field(None, description="Similarity index for renames")


class CommitDiffSchema(BaseModel):
    """Schema for commit comparison results."""
    
    from_commit: str = Field(..., description="Source commit hash")
    to_commit: str = Field(..., description="Target commit hash")
    files_changed: int = Field(..., description="Number of files changed")
    total_additions: int = Field(..., description="Total lines added")
    total_deletions: int = Field(..., description="Total lines deleted")
    file_diffs: List[FileDiffSchema] = Field(..., description="File-by-file diff information")
    commit_range_info: Optional[Dict[str, Any]] = Field(None, description="Additional commit range information")


class RepositorySchema(BaseModel):
    """Schema for complete repository information."""
    
    path: str = Field(..., description="Repository path")
    name: str = Field(..., description="Repository name")
    is_bare: bool = Field(..., description="Whether repository is bare")
    head_commit: Optional[str] = Field(None, description="Current HEAD commit")
    active_branch: Optional[str] = Field(None, description="Currently active branch")
    branches: List[BranchSchema] = Field(..., description="All branches")
    tags: List[TagSchema] = Field(..., description="All tags")
    remotes: List[Dict[str, str]] = Field(..., description="Remote repositories")
    total_commits: int = Field(..., description="Total number of commits")
    contributors: List[AuthorSchema] = Field(..., description="All contributors")
    first_commit_date: Optional[datetime] = Field(None, description="Date of first commit")
    last_commit_date: Optional[datetime] = Field(None, description="Date of last commit")
    repository_age_days: Optional[int] = Field(None, description="Age of repository in days")
    size_info: Optional[Dict[str, Any]] = Field(None, description="Repository size information")


class SearchResultSchema(BaseModel):
    """Schema for search results."""
    
    commit: CommitSchema = Field(..., description="Commit information")
    file_path: str = Field(..., description="File path where match was found")
    line_number: Optional[int] = Field(None, description="Line number of match")
    matching_line: Optional[str] = Field(None, description="The matching line content")
    context_lines: Optional[List[str]] = Field(None, description="Context lines around the match")
    search_type: str = Field(..., description="Type of search that found this result")
    relevance_score: float = Field(0.0, description="Relevance score (0.0-1.0)")
    match_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional match metadata")


class SearchResultsCollectionSchema(BaseModel):
    """Schema for a collection of search results."""
    
    query: str = Field(..., description="Search query")
    results: List[SearchResultSchema] = Field(..., description="Search results")
    total_results: int = Field(..., description="Total number of results")
    search_time_ms: float = Field(..., description="Search time in milliseconds")
    filters_applied: List[DataFilter] = Field(default_factory=list, description="Filters applied")
    sort_criteria: List[SortCriteria] = Field(default_factory=list, description="Sort criteria applied")
    pagination: Optional[PaginationInfo] = Field(None, description="Pagination information")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional search metadata")


# Configuration for all schemas
for schema_class in [
    AuthorSchema, BranchSchema, TagSchema, FileChangeSchema, CommitSchema,
    BlameLineSchema, FileBlameSchema, DiffLineSchema, FileDiffSchema,
    CommitDiffSchema, RepositorySchema, SearchResultSchema, SearchResultsCollectionSchema
]:
    try:
        schema_class.model_config = ConfigDict(  # type: ignore[attr-defined]
            json_encoders={
                datetime: lambda v: v.isoformat(),
            },
            validate_assignment=True,
            use_enum_values=True
        )
    except AttributeError:
        # Skip if model_config is not available
        pass
