# Python API Reference

GitHound provides a comprehensive Python API for programmatic access to all Git repository analysis
capabilities. This guide covers the complete API with examples and best practices.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [GitHound Class](#githound-class)
- [Search Operations](#search-operations)
- [Repository Analysis](#repository-analysis)
- [File Operations](#file-operations)
- [Diff and Comparison](#diff-and-comparison)
- [Export and Data Management](#export-and-data-management)
- [Error Handling](#error-handling)
- [Advanced Usage](#advanced-usage)
- [Best Practices](#best-practices)

## Installation

**Note**: GitHound is currently in development and not yet published to PyPI.

Install from source:

```bash
git clone https://github.com/AstroAir/GitHound.git
cd GitHound
pip install -e .
```

For development installation:

```bash
git clone https://github.com/AstroAir/GitHound.git
cd GitHound
pip install -e . --dependency-groups dev,test
```

## Quick Start

```python
from githound import GitHound
from githound.models import SearchQuery
from pathlib import Path

# Initialize GitHound with a repository
gh = GitHound(Path("/path/to/your/repo"))

# Analyze repository
repo_info = gh.analyze_repository()
print(f"Repository has {repo_info['total_commits']} commits")

# Perform a simple search
query = SearchQuery(content_pattern="function")
results = gh.search_advanced_sync(query)
print(f"Found {len(results)} matches")

# Analyze file blame
blame_result = gh.analyze_blame("src/main.py")
print(f"File has {blame_result.total_lines} lines with {len(blame_result.contributors)} contributors")
```

## GitHound Class

The `GitHound` class is the main entry point for all GitHound functionality. It provides a unified
interface for repository analysis, search operations, and data export.

### Constructor

```python
class GitHound:
    def __init__(self, repo_path: Path, timeout: int = 300) -> None:
        """Initialize GitHound with a repository path.

        Args:
            repo_path: Path to the Git repository
            timeout: Default timeout for Git operations in seconds (default: 300)

        Raises:
            GitCommandError: If the path is not a valid Git repository
        """
```

**Example:**

```python
from githound import GitHound
from pathlib import Path

# Initialize with default timeout
gh = GitHound(Path("/path/to/repo"))

# Initialize with custom timeout
gh = GitHound(Path("/path/to/repo"), timeout=600)

# Use as context manager (recommended)
with GitHound(Path("/path/to/repo")) as gh:
    results = gh.analyze_repository()
```

### Properties

#### search_orchestrator

```python
@property
def search_orchestrator(self) -> SearchOrchestrator:
    """Get or create the search orchestrator with all searchers registered."""
```

The search orchestrator coordinates multiple search strategies and is automatically configured with
all available searchers:

- `CommitHashSearcher` - Search by commit hash
- `AuthorSearcher` - Search by author name/email
- `MessageSearcher` - Search by commit message
- `DateRangeSearcher` - Search by date range
- `FilePathSearcher` - Search by file path patterns
- `FileTypeSearcher` - Search by file extensions
- `ContentSearcher` - Search file contents
- `FuzzySearcher` - Fuzzy string matching

## Search Operations

GitHound provides powerful search capabilities across multiple dimensions of your Git repository.

### Advanced Search

```python
async def search_advanced(
    self,
    query: SearchQuery,
    branch: str | None = None,
    max_results: int | None = None,
    enable_progress: bool = False,
) -> list[SearchResult]:
    """Perform advanced multi-modal search.

    Args:
        query: SearchQuery object with search criteria
        branch: Branch to search (defaults to current branch)
        max_results: Maximum number of results to return
        enable_progress: Whether to enable progress reporting

    Returns:
        List of SearchResult objects

    Raises:
        GitCommandError: If search operation fails
    """
```

**Example:**

```python
from githound.models import SearchQuery
from datetime import datetime

# Create a comprehensive search query
query = SearchQuery(
    content_pattern="function.*authenticate",  # Regex pattern in content
    author_pattern="john.doe@example.com",     # Author email
    message_pattern="security",                # Commit message keyword
    date_from=datetime(2023, 1, 1),           # Start date
    date_to=datetime(2023, 12, 31),           # End date
    file_extensions=["py", "js"],              # File types
    fuzzy_search=True,                         # Enable fuzzy matching
    fuzzy_threshold=0.8,                       # Similarity threshold
    case_sensitive=False,                      # Case insensitive
    max_file_size=1024*1024,                  # Max file size (1MB)
)

# Perform async search
results = await gh.search_advanced(query, max_results=100)

# Process results
for result in results:
    print(f"Match in {result.file_path}:{result.line_number}")
    print(f"Commit: {result.commit_hash[:8]} by {result.author}")
    print(f"Relevance: {result.relevance_score:.2f}")
    print(f"Content: {result.content}")
    print("---")
```

### Synchronous Search

For convenience, GitHound also provides a synchronous version:

```python
def search_advanced_sync(
    self,
    query: SearchQuery,
    branch: str | None = None,
    max_results: int | None = None,
    enable_progress: bool = False,
) -> list[SearchResult]:
    """Synchronous version of search_advanced for convenience."""
```

**Example:**

```python
# Simple content search
query = SearchQuery(content_pattern="TODO")
results = gh.search_advanced_sync(query)

# Author-specific search
query = SearchQuery(author_pattern="alice")
results = gh.search_advanced_sync(query, branch="main")
```

### SearchQuery Parameters

The `SearchQuery` class supports comprehensive search criteria:

```python
class SearchQuery(BaseModel):
    # Content and pattern matching
    content_pattern: str | None = None          # Regex pattern in file content
    commit_hash: str | None = None              # Specific commit hash
    author_pattern: str | None = None           # Author name or email pattern
    message_pattern: str | None = None          # Commit message pattern

    # Date filtering
    date_from: datetime | None = None           # Start date
    date_to: datetime | None = None             # End date

    # File filtering
    file_path_pattern: str | None = None        # File path pattern
    file_extensions: list[str] | None = None    # File extensions (e.g., ["py", "js"])
    include_globs: list[str] | None = None      # Include patterns
    exclude_globs: list[str] | None = None      # Exclude patterns

    # Search options
    case_sensitive: bool = False                # Case sensitivity
    fuzzy_search: bool = False                  # Enable fuzzy matching
    fuzzy_threshold: float = 0.8                # Fuzzy similarity threshold

    # Size limits
    max_file_size: int | None = None            # Maximum file size in bytes
    min_commit_size: int | None = None          # Minimum commit size
    max_commit_size: int | None = None          # Maximum commit size
```

### SearchResult Structure

Search results contain comprehensive information:

```python
class SearchResult(BaseModel):
    commit_hash: str                    # Full commit hash
    file_path: str                      # Relative file path
    line_number: int                    # Line number (1-based)
    content: str                        # Matching content
    relevance_score: float              # Relevance score (0.0-1.0)

    # Commit information
    author: str                         # Author name and email
    commit_date: datetime               # Commit timestamp
    commit_message: str                 # Commit message

    # Context information
    context_before: list[str]           # Lines before match
    context_after: list[str]            # Lines after match

    # Metadata
    file_size: int                      # File size in bytes
    match_type: str                     # Type of match found
```

## Repository Analysis

GitHound provides comprehensive repository analysis capabilities to understand repository structure,
statistics, and health.

### Repository Metadata

```python
def analyze_repository(
    self,
    include_detailed_stats: bool = True,
    timeout: int | None = None
) -> dict[str, Any]:
    """Analyze repository and return comprehensive metadata.

    Args:
        include_detailed_stats: Whether to include detailed statistics
        timeout: Timeout in seconds (uses instance default if None)

    Returns:
        Dictionary containing repository metadata including:
        - Basic repository information (path, branches, tags, remotes)
        - Commit statistics (total commits, contributors, date range)
        - Repository health metrics

    Raises:
        GitCommandError: If repository analysis fails or times out
    """
```

**Example:**

```python
# Basic repository analysis
repo_info = gh.analyze_repository()

print(f"Repository: {repo_info['name']}")
print(f"Total commits: {repo_info['total_commits']}")
print(f"Total branches: {repo_info['total_branches']}")
print(f"Total contributors: {len(repo_info['contributors'])}")
print(f"Created: {repo_info['created_date']}")
print(f"Last activity: {repo_info['last_activity']}")

# Access detailed statistics
if 'author_statistics' in repo_info:
    stats = repo_info['author_statistics']
    print(f"Most active author: {stats['most_active_author']}")
    print(f"Total lines of code: {stats['total_lines']}")

# Repository structure
print(f"File types: {repo_info['file_types']}")
print(f"Repository size: {repo_info['repository_size_mb']} MB")
```

### Author Statistics

```python
def get_author_statistics(self, branch: str | None = None) -> dict[str, Any]:
    """Get author statistics for the repository.

    Args:
        branch: Branch to analyze (defaults to current branch)

    Returns:
        Dictionary containing author statistics

    Raises:
        GitCommandError: If author statistics retrieval fails
    """
```

**Example:**

```python
# Get author statistics for current branch
author_stats = gh.get_author_statistics()

print("Top contributors:")
for author in author_stats['top_contributors']:
    print(f"  {author['name']}: {author['commits']} commits, {author['lines_added']} lines")

print(f"Total authors: {author_stats['total_authors']}")
print(f"Most active period: {author_stats['most_active_period']}")

# Get statistics for specific branch
main_stats = gh.get_author_statistics(branch="main")
```

## File Operations

GitHound provides detailed file-level analysis including blame information and change history.

### File Blame Analysis

```python
def analyze_blame(self, file_path: str, commit: str | None = None) -> FileBlameResult:
    """Analyze file blame information.

    Args:
        file_path: Path to the file relative to repository root
        commit: Specific commit to blame (defaults to HEAD)

    Returns:
        FileBlameResult with line-by-line authorship information

    Raises:
        GitCommandError: If blame analysis fails
    """
```

**Example:**

```python
# Analyze blame for a file
blame_info = gh.analyze_blame("src/main.py")

print(f"File: {blame_info.file_path}")
print(f"Total lines: {blame_info.total_lines}")
print(f"Contributors: {len(blame_info.contributors)}")

# Access line-by-line information
for line in blame_info.blame_info[:10]:  # First 10 lines
    print(f"Line {line.line_number}: {line.author_name} ({line.commit_hash[:8]})")
    print(f"  Date: {line.commit_date}")
    print(f"  Content: {line.content}")

# Contributor statistics
for contributor in blame_info.contributors:
    print(f"{contributor}")

# Analyze blame for specific commit
historical_blame = gh.analyze_blame("src/main.py", commit="abc123")
```

### File History

```python
def get_file_history(
    self,
    file_path: str,
    max_count: int | None = None,
    branch: str | None = None
) -> list[dict[str, Any]]:
    """Get the commit history for a specific file.

    Args:
        file_path: Path to the file relative to repository root
        max_count: Maximum number of commits to return
        branch: Branch to search (defaults to current branch)

    Returns:
        List of commit information dictionaries

    Raises:
        GitCommandError: If file history retrieval fails
    """
```

**Example:**

```python
# Get complete file history
history = gh.get_file_history("src/main.py")

print(f"File has {len(history)} commits in its history")

for commit in history[:5]:  # Show first 5 commits
    print(f"Commit: {commit['hash'][:8]}")
    print(f"Author: {commit['author']}")
    print(f"Date: {commit['date']}")
    print(f"Message: {commit['message']}")
    print(f"Changes: +{commit['lines_added']} -{commit['lines_removed']}")
    print("---")

# Get limited history
recent_history = gh.get_file_history("src/main.py", max_count=10)

# Get history for specific branch
feature_history = gh.get_file_history("src/main.py", branch="feature/new-auth")
```

## Diff and Comparison

GitHound provides powerful diff and comparison capabilities for analyzing changes between commits,
branches, and files.

### Commit Comparison

```python
def compare_commits(
    self,
    from_commit: str,
    to_commit: str,
    file_patterns: list[str] | None = None
) -> CommitDiffResult:
    """Compare two commits and return detailed diff information.

    Args:
        from_commit: Source commit hash or reference
        to_commit: Target commit hash or reference
        file_patterns: Optional file patterns to filter the diff

    Returns:
        CommitDiffResult with detailed comparison information

    Raises:
        GitCommandError: If commit comparison fails
    """
```

**Example:**

```python
# Compare two commits
diff_result = gh.compare_commits("abc123", "def456")

print(f"Comparing {diff_result.from_commit} -> {diff_result.to_commit}")
print(f"Files changed: {diff_result.files_changed}")
print(f"Lines added: {diff_result.lines_added}")
print(f"Lines removed: {diff_result.lines_removed}")

# Access file-level changes
for file_diff in diff_result.file_diffs:
    print(f"\nFile: {file_diff.file_path}")
    print(f"Change type: {file_diff.change_type}")
    print(f"Lines: +{file_diff.lines_added} -{file_diff.lines_removed}")

    # Access detailed diff lines
    for line in file_diff.diff_lines[:5]:  # First 5 changes
        print(f"  {line.line_type}: {line.content}")

# Compare with file filtering
python_diff = gh.compare_commits("abc123", "def456", file_patterns=["*.py"])
```

### Branch Comparison

```python
def compare_branches(
    self,
    from_branch: str,
    to_branch: str,
    file_patterns: list[str] | None = None
) -> CommitDiffResult:
    """Compare two branches and return detailed diff information.

    Args:
        from_branch: Source branch name
        to_branch: Target branch name
        file_patterns: Optional file patterns to filter the diff

    Returns:
        CommitDiffResult with detailed comparison information

    Raises:
        GitCommandError: If branch comparison fails
    """
```

**Example:**

```python
# Compare main branch with feature branch
branch_diff = gh.compare_branches("main", "feature/new-auth")

print(f"Branch comparison: {branch_diff.from_commit} -> {branch_diff.to_commit}")
print(f"Commits ahead: {branch_diff.commits_ahead}")
print(f"Commits behind: {branch_diff.commits_behind}")

# Analyze the impact
print(f"Total changes: {branch_diff.files_changed} files")
print(f"Net lines: +{branch_diff.lines_added - branch_diff.lines_removed}")

# Check for conflicts
if branch_diff.has_conflicts:
    print("⚠️  Potential merge conflicts detected")
    for conflict in branch_diff.conflict_files:
        print(f"  - {conflict}")

# Compare specific file types
js_changes = gh.compare_branches("main", "feature/ui-update", file_patterns=["*.js", "*.jsx"])
```

## Export and Data Management

GitHound provides flexible export capabilities to save analysis results in various formats.

### Export Options

```python
from githound.schemas import ExportOptions, OutputFormat

# Create export options
export_options = ExportOptions(
    format=OutputFormat.JSON,           # JSON, YAML, CSV, XML, EXCEL
    include_metadata=True,              # Include metadata
    pretty_print=True,                  # Pretty formatting
    fields=["commit_hash", "author"],   # Specific fields to include
    exclude_fields=["content"],         # Fields to exclude
    pagination=PaginationInfo(          # Pagination settings
        page=1,
        per_page=100
    )
)
```

### Export Methods

```python
def export_with_options(
    self,
    data: Any,
    output_path: str | Path,
    options: ExportOptions
) -> dict[str, Any]:
    """Export data with comprehensive options.

    Args:
        data: Data to export (search results, analysis data, etc.)
        output_path: Output file path
        options: Export configuration options

    Returns:
        Export metadata and statistics

    Raises:
        GitCommandError: If export operation fails
    """
```

**Example:**

```python
# Perform search and export results
query = SearchQuery(content_pattern="TODO")
results = gh.search_advanced_sync(query)

# Export to JSON
json_options = ExportOptions(
    format=OutputFormat.JSON,
    include_metadata=True,
    pretty_print=True
)
export_info = gh.export_with_options(results, "todos.json", json_options)

# Export to CSV with specific fields
csv_options = ExportOptions(
    format=OutputFormat.CSV,
    fields=["file_path", "line_number", "author", "commit_date"],
    include_metadata=False
)
gh.export_with_options(results, "todos.csv", csv_options)

# Export repository analysis
repo_info = gh.analyze_repository()
yaml_options = ExportOptions(
    format=OutputFormat.YAML,
    pretty_print=True,
    exclude_fields=["raw_data"]
)
gh.export_with_options(repo_info, "repo_analysis.yaml", yaml_options)

print(f"Exported {export_info['records_exported']} records")
print(f"File size: {export_info['file_size_bytes']} bytes")
```

## Error Handling

GitHound provides comprehensive error handling with specific exception types and detailed error messages.

### Exception Types

```python
from git import GitCommandError

try:
    gh = GitHound(Path("/invalid/path"))
except GitCommandError as e:
    print(f"Repository error: {e}")

try:
    results = gh.search_advanced_sync(invalid_query)
except GitCommandError as e:
    print(f"Search error: {e}")

try:
    blame_info = gh.analyze_blame("nonexistent_file.py")
except GitCommandError as e:
    print(f"Blame error: {e}")
```

### Timeout Handling

```python
# Set custom timeout for operations
gh = GitHound(Path("/path/to/large/repo"), timeout=600)  # 10 minutes

# Override timeout for specific operations
try:
    repo_info = gh.analyze_repository(timeout=120)  # 2 minutes
except GitCommandError as e:
    if "timeout" in str(e).lower():
        print("Operation timed out - try increasing timeout or reducing scope")
    else:
        print(f"Analysis failed: {e}")
```

### Graceful Degradation

```python
# Handle partial failures gracefully
repo_info = gh.analyze_repository(include_detailed_stats=True)

if 'author_statistics_error' in repo_info:
    print(f"Warning: Author statistics failed: {repo_info['author_statistics_error']}")
    print("Continuing with basic repository information...")

# Check for data availability
if 'contributors' in repo_info:
    print(f"Found {len(repo_info['contributors'])} contributors")
else:
    print("Contributor information not available")
```

## Advanced Usage

### Context Manager Usage

GitHound supports context manager protocol for automatic resource cleanup:

```python
# Recommended: Use as context manager
with GitHound(Path("/path/to/repo")) as gh:
    repo_info = gh.analyze_repository()
    results = gh.search_advanced_sync(query)
    # Resources automatically cleaned up

# Manual cleanup (if not using context manager)
gh = GitHound(Path("/path/to/repo"))
try:
    # Perform operations
    pass
finally:
    gh.cleanup()  # Manual cleanup
```

### Batch Operations

```python
# Analyze multiple repositories
repos = [
    Path("/path/to/repo1"),
    Path("/path/to/repo2"),
    Path("/path/to/repo3")
]

results = {}
for repo_path in repos:
    try:
        with GitHound(repo_path) as gh:
            results[repo_path.name] = gh.analyze_repository()
    except GitCommandError as e:
        print(f"Failed to analyze {repo_path}: {e}")

# Compare results across repositories
for name, info in results.items():
    print(f"{name}: {info['total_commits']} commits, {len(info['contributors'])} contributors")
```

### Custom Search Workflows

```python
# Multi-stage search workflow
def find_security_issues(gh: GitHound) -> dict[str, list[SearchResult]]:
    """Find potential security issues in the repository."""

    security_patterns = {
        "passwords": SearchQuery(
            content_pattern=r"password\s*=\s*['\"][^'\"]+['\"]",
            file_extensions=["py", "js", "java", "php"]
        ),
        "api_keys": SearchQuery(
            content_pattern=r"api[_-]?key\s*[=:]\s*['\"][^'\"]+['\"]",
            case_sensitive=False
        ),
        "sql_injection": SearchQuery(
            content_pattern=r"SELECT.*\+.*FROM",
            file_extensions=["py", "php", "java"]
        ),
        "hardcoded_secrets": SearchQuery(
            content_pattern=r"(secret|token|key)\s*[=:]\s*['\"][a-zA-Z0-9]{20,}['\"]",
            case_sensitive=False
        )
    }

    issues = {}
    for issue_type, query in security_patterns.items():
        try:
            results = gh.search_advanced_sync(query, max_results=50)
            if results:
                issues[issue_type] = results
                print(f"Found {len(results)} potential {issue_type} issues")
        except GitCommandError as e:
            print(f"Search for {issue_type} failed: {e}")

    return issues

# Use the custom workflow
with GitHound(Path("/path/to/repo")) as gh:
    security_issues = find_security_issues(gh)

    # Export security report
    if security_issues:
        export_options = ExportOptions(
            format=OutputFormat.JSON,
            include_metadata=True,
            pretty_print=True
        )
        gh.export_with_options(security_issues, "security_report.json", export_options)
```

### Performance Optimization

```python
# Optimize for large repositories
def analyze_large_repository(repo_path: Path) -> dict[str, Any]:
    """Optimized analysis for large repositories."""

    # Use longer timeout for large repos
    with GitHound(repo_path, timeout=1800) as gh:  # 30 minutes

        # Start with basic analysis
        repo_info = gh.analyze_repository(include_detailed_stats=False)

        # Selective detailed analysis based on size
        if repo_info['total_commits'] < 10000:
            # Small repo - full analysis
            detailed_info = gh.analyze_repository(include_detailed_stats=True)
            repo_info.update(detailed_info)
        else:
            # Large repo - sample analysis
            print("Large repository detected - using sampling approach")

            # Analyze recent activity only
            recent_query = SearchQuery(
                date_from=datetime.now() - timedelta(days=90),  # Last 3 months
                max_file_size=1024*1024  # Skip large files
            )
            recent_results = gh.search_advanced_sync(recent_query, max_results=1000)
            repo_info['recent_activity'] = len(recent_results)

        return repo_info

# Use optimized analysis
large_repo_info = analyze_large_repository(Path("/path/to/large/repo"))
```

## Best Practices

### 1. Resource Management

```python
# Always use context managers
with GitHound(Path("/path/to/repo")) as gh:
    # Perform operations
    pass

# Or ensure manual cleanup
gh = GitHound(Path("/path/to/repo"))
try:
    # Operations
    pass
finally:
    gh.cleanup()
```

### 2. Error Handling

```python
# Comprehensive error handling
def safe_repository_analysis(repo_path: Path) -> dict[str, Any] | None:
    """Safely analyze a repository with comprehensive error handling."""

    try:
        with GitHound(repo_path) as gh:
            return gh.analyze_repository()

    except GitCommandError as e:
        if "not a git repository" in str(e).lower():
            print(f"Error: {repo_path} is not a Git repository")
        elif "timeout" in str(e).lower():
            print(f"Error: Analysis of {repo_path} timed out")
        else:
            print(f"Git error analyzing {repo_path}: {e}")
        return None

    except PermissionError:
        print(f"Error: Permission denied accessing {repo_path}")
        return None

    except Exception as e:
        print(f"Unexpected error analyzing {repo_path}: {e}")
        return None
```

### 3. Performance Considerations

```python
# Optimize search queries
def optimized_search(gh: GitHound, pattern: str) -> list[SearchResult]:
    """Perform optimized search with reasonable limits."""

    query = SearchQuery(
        content_pattern=pattern,
        max_file_size=1024*1024,      # Skip files > 1MB
        exclude_globs=[               # Skip common large/binary files
            "*.min.js", "*.bundle.js", "*.map",
            "*.jpg", "*.png", "*.gif", "*.pdf",
            "node_modules/*", ".git/*", "*.lock"
        ],
        fuzzy_search=False,           # Disable fuzzy for performance
        case_sensitive=False          # Usually what users want
    )

    return gh.search_advanced_sync(query, max_results=500)
```

### 4. Data Export Best Practices

```python
# Structured export workflow
def export_analysis_report(gh: GitHound, output_dir: Path) -> None:
    """Export comprehensive analysis report."""

    output_dir.mkdir(exist_ok=True)

    # Repository overview
    repo_info = gh.analyze_repository()
    overview_options = ExportOptions(
        format=OutputFormat.YAML,
        pretty_print=True,
        exclude_fields=["raw_data", "internal_metadata"]
    )
    gh.export_with_options(repo_info, output_dir / "overview.yaml", overview_options)

    # Author statistics
    author_stats = gh.get_author_statistics()
    stats_options = ExportOptions(
        format=OutputFormat.JSON,
        pretty_print=True
    )
    gh.export_with_options(author_stats, output_dir / "authors.json", stats_options)

    # Recent activity
    recent_query = SearchQuery(
        date_from=datetime.now() - timedelta(days=30)
    )
    recent_activity = gh.search_advanced_sync(recent_query)

    activity_options = ExportOptions(
        format=OutputFormat.CSV,
        fields=["commit_hash", "author", "commit_date", "file_path", "commit_message"]
    )
    gh.export_with_options(recent_activity, output_dir / "recent_activity.csv", activity_options)

    print(f"Analysis report exported to {output_dir}")

# Use the export workflow
with GitHound(Path("/path/to/repo")) as gh:
    export_analysis_report(gh, Path("./analysis_output"))
```

### 5. Integration with Other Tools

```python
# Integration with pandas for data analysis
import pandas as pd

def analyze_commit_patterns(gh: GitHound) -> pd.DataFrame:
    """Analyze commit patterns using pandas."""

    # Get all commits from last year
    query = SearchQuery(
        date_from=datetime.now() - timedelta(days=365)
    )
    results = gh.search_advanced_sync(query, max_results=10000)

    # Convert to DataFrame
    data = []
    for result in results:
        data.append({
            'author': result.author,
            'date': result.commit_date,
            'file_path': result.file_path,
            'file_extension': Path(result.file_path).suffix,
            'commit_hash': result.commit_hash,
            'hour': result.commit_date.hour,
            'weekday': result.commit_date.weekday()
        })

    df = pd.DataFrame(data)

    # Analyze patterns
    print("Commits by author:")
    print(df['author'].value_counts().head(10))

    print("\nCommits by file type:")
    print(df['file_extension'].value_counts().head(10))

    print("\nCommits by hour of day:")
    print(df['hour'].value_counts().sort_index())

    return df

# Use with pandas
with GitHound(Path("/path/to/repo")) as gh:
    commit_df = analyze_commit_patterns(gh)
    commit_df.to_csv("commit_analysis.csv", index=False)
```

This comprehensive Python API reference covers all major GitHound functionality with practical examples
and best practices. For more specific use cases or advanced features, refer to the individual module
documentation or the GitHound source code.

## 🚀 Related Documentation

### API References

- **[REST API](rest-api.md)** - HTTP API for external integrations
- **[WebSocket API](websocket-api.md)** - Real-time API documentation
- **[OpenAPI Specification](openapi.md)** - Interactive API documentation

### Integration Guides

- **[MCP Server](../mcp-server/README.md)** - Model Context Protocol integration
- **[CLI Usage](../user-guide/cli-usage.md)** - Command-line interface

### Getting Started

- **[Installation Guide](../getting-started/installation.md)** - Install GitHound
- **[Quick Start](../getting-started/quick-start.md)** - Basic usage examples
- **[Configuration](../getting-started/configuration.md)** - Environment setup

### Advanced Topics

- **[Architecture Overview](../architecture/overview.md)** - System design

### Need Help

- **[Troubleshooting Guide](../troubleshooting/README.md)** - Solve common issues
- **[FAQ](../troubleshooting/faq.md)** - Frequently asked questions

---

**📚 [Back to Documentation Home](../index.md)** |
**⬅️ [CLI Usage](../user-guide/cli-usage.md)** |
**➡️ [REST API](rest-api.md)**
