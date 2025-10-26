# MCP Tools Reference

Comprehensive reference for all 29 tools exposed by the GitHound MCP server.

## Advanced Search Tools

### `advanced_search`

Perform multi-modal search across the repository with comprehensive filtering.

**Parameters:**

- `repo_path` (required): Path to Git repository
- `branch` (optional): Branch to search (default: current branch)
- `content_pattern` (optional): Content search pattern
- `commit_hash` (optional): Specific commit hash to search
- `author_pattern` (optional): Author name or email pattern
- `message_pattern` (optional): Commit message pattern
- `date_from` (optional): Start date filter (ISO format)
- `date_to` (optional): End date filter (ISO format)
- `file_path_pattern` (optional): File path pattern
- `file_extensions` (optional): List of file extensions to search
- `case_sensitive` (optional): Case-sensitive search (default: false)
- `fuzzy_search` (optional): Enable fuzzy matching (default: false)
- `fuzzy_threshold` (optional): Fuzzy matching threshold 0.0-1.0 (default: 0.8)
- `max_results` (optional): Maximum results to return (default: 100)
- `include_globs` (optional): Glob patterns to include
- `exclude_globs` (optional): Glob patterns to exclude
- `max_file_size` (optional): Maximum file size in bytes
- `min_commit_size` (optional): Minimum commit size
- `max_commit_size` (optional): Maximum commit size

**Returns:** Structured search results with matches, context, and metadata

### `fuzzy_search`

Perform fuzzy string matching across repository content.

**Parameters:**

- `repo_path` (required): Path to Git repository
- `query` (required): Fuzzy search query
- `threshold` (optional): Similarity threshold 0.0-1.0 (default: 0.8)
- `max_results` (optional): Maximum results (default: 50)

**Returns:** Fuzzy matches with similarity scores

### `content_search`

Search within file contents with advanced pattern matching.

**Parameters:**

- `repo_path` (required): Path to Git repository
- `pattern` (required): Search pattern (supports regex)
- `file_types` (optional): File extensions to search
- `context_lines` (optional): Lines of context around matches (default: 3)

**Returns:** Content matches with file locations and context

### `detect_patterns`

Detect common code patterns and anti-patterns in the repository.

**Parameters:**

- `repo_path` (required): Path to Git repository
- `pattern_types` (optional): Types of patterns to detect
- `file_extensions` (optional): File extensions to analyze
- `severity_threshold` (optional): Minimum severity level to report

**Returns:** Detected patterns with locations and severity ratings

### `search_by_tag`

Search repository content by Git tags and releases.

**Parameters:**

- `repo_path` (required): Path to Git repository
- `tag_pattern` (optional): Tag name pattern to search
- `content_pattern` (optional): Content pattern within tagged versions
- `include_prereleases` (optional): Include pre-release tags (default: false)

**Returns:** Search results organized by tags and releases

### `create_search_engine`

Create and configure a custom search engine with specific capabilities.

**Parameters:**

- `enable_advanced_searchers` (optional): Enable advanced search capabilities (default: true)
- `enable_basic_searchers` (optional): Enable basic search capabilities (default: true)
- `enable_caching` (optional): Enable search result caching (default: true)
- `enable_ranking` (optional): Enable result ranking (default: true)
- `enable_analytics` (optional): Enable search analytics (default: true)
- `enable_fuzzy_search` (optional): Enable fuzzy search capabilities (default: true)
- `enable_pattern_detection` (optional): Enable pattern detection (default: true)
- `max_workers` (optional): Maximum worker threads (default: 4)
- `cache_backend` (optional): Cache backend type (memory/redis, default: memory)

**Returns:** Search engine configuration and capabilities

### `query_searcher_registry`

Query the searcher registry for available searchers and their capabilities.

**Parameters:**

- `repo_path` (required): Path to Git repository
- `search_types` (optional): Filter by specific search types
- `capabilities` (optional): Filter by searcher capabilities
- `enabled_only` (optional): Only return enabled searchers (default: true)

**Returns:** Available searchers with their metadata and capabilities

### `get_search_analytics`

Retrieve search performance analytics and usage patterns.

**Parameters:**

- `repo_path` (optional): Path to Git repository for repo-specific analytics
- `time_range_hours` (optional): Time range for analytics in hours (default: 24)
- `include_performance` (optional): Include performance metrics (default: true)
- `include_usage_patterns` (optional): Include usage pattern analysis (default: true)

**Returns:** Search analytics including performance metrics and usage patterns

## Repository Analysis Tools

### `analyze_repository`

Get comprehensive repository metadata and statistics.

**Parameters:**

- `repo_path` (required): Path to Git repository
- `include_stats` (optional): Include detailed statistics (default: true)
- `include_contributors` (optional): Include contributor analysis (default: true)

**Returns:** Complete repository analysis including:

- Basic metadata (name, description, branches, tags)
- Commit statistics
- Contributor information
- File type distribution
- Repository health metrics

### `get_filtered_commits`

Retrieve commits with advanced filtering options.

**Parameters:**

- `repo_path` (required): Path to Git repository
- `branch` (optional): Branch to analyze (default: current)
- `author` (optional): Filter by author
- `message_pattern` (optional): Filter by commit message pattern
- `date_from` (optional): Start date filter
- `date_to` (optional): End date filter
- `max_commits` (optional): Maximum commits to return (default: 100)

**Returns:** Filtered commit list with metadata

### `analyze_branches`

Perform comprehensive branch analysis including metrics and comparisons.

**Parameters:**

- `repo_path` (required): Path to Git repository
- `branch_name` (optional): Specific branch to analyze
- `compare_with` (optional): Branch to compare against
- `include_metrics` (optional): Include branch metrics (default: true)
- `max_commits` (optional): Maximum commits to analyze (default: 100)

**Returns:** Branch analysis with metrics, commit history, and comparison data

### `analyze_diffs`

Perform detailed diff analysis between references.

**Parameters:**

- `repo_path` (required): Path to Git repository
- `from_ref` (required): Source reference (commit, branch, tag)
- `to_ref` (required): Target reference (commit, branch, tag)
- `file_patterns` (optional): File patterns to include in analysis
- `include_stats` (optional): Include diff statistics (default: true)

**Returns:** Detailed diff analysis with file changes, statistics, and impact assessment

### `analyze_statistics`

Perform statistical analysis of repository data.

**Parameters:**

- `repo_path` (required): Path to Git repository
- `analysis_types` (optional): Types of analysis to perform
- `time_range_days` (optional): Time range for analysis in days (default: 90)
- `include_trends` (optional): Include trend analysis (default: true)
- `group_by` (optional): Group results by author, date, or file type (default: author)

**Returns:** Statistical analysis including trends, patterns, and insights

### `analyze_tags`

Analyze repository tags and version information.

**Parameters:**

- `repo_path` (required): Path to Git repository
- `tag_pattern` (optional): Pattern to filter tags
- `include_releases` (optional): Include release information (default: true)
- `compare_versions` (optional): Compare version differences (default: true)

**Returns:** Tag analysis with version information and release comparisons

### `list_branches`

Get all repository branches with detailed information.

**Parameters:**

- `repo_path` (required): Path to Git repository
- `include_remote` (optional): Include remote branches (default: true)
- `include_merged` (optional): Include merged branches (default: true)

**Returns:** Branch list with commit info and merge status

### `list_tags`

Get all repository tags with associated information.

**Parameters:**

- `repo_path` (required): Path to Git repository
- `include_annotated` (optional): Include annotated tag info (default: true)

**Returns:** Tag list with commit references and annotations

### `list_remotes`

Get all configured remote repositories.

**Parameters:**

- `repo_path` (required): Path to Git repository

**Returns:** Remote repository URLs and configurations

### `validate_repository`

Validate repository structure and health.

**Parameters:**

- `repo_path` (required): Path to Git repository
- `check_integrity` (optional): Perform integrity checks (default: true)

**Returns:** Repository validation results and health status

## Commit Analysis Tools

### `analyze_commit`

Get detailed information about a specific commit.

**Parameters:**

- `repo_path` (required): Path to Git repository
- `commit_hash` (optional): Specific commit hash (default: HEAD)
- `include_diff` (optional): Include diff information (default: true)
- `include_stats` (optional): Include change statistics (default: true)

**Returns:** Comprehensive commit analysis including:

- Commit metadata (author, date, message)
- File changes and statistics
- Diff information
- Parent/child relationships

### `get_commit_history`

Retrieve commit history with filtering and pagination.

**Parameters:**

- `repo_path` (required): Path to Git repository
- `branch` (optional): Branch to analyze (default: current)
- `max_commits` (optional): Maximum commits (default: 50)
- `skip_commits` (optional): Number of commits to skip (default: 0)
- `author` (optional): Filter by author
- `since` (optional): Date filter (ISO format)

**Returns:** Paginated commit history with metadata

### `compare_commits_diff`

Compare two commits and analyze differences.

**Parameters:**

- `repo_path` (required): Path to Git repository
- `commit1` (required): First commit hash
- `commit2` (required): Second commit hash
- `include_context` (optional): Include diff context (default: true)

**Returns:** Detailed comparison with file-by-file diffs

### `compare_branches_diff`

Compare two branches and analyze differences.

**Parameters:**

- `repo_path` (required): Path to Git repository
- `branch1` (required): First branch name
- `branch2` (required): Second branch name
- `include_merge_base` (optional): Include merge base analysis (default: true)

**Returns:** Branch comparison with divergence analysis

## File Analysis Tools

### `get_file_history_mcp`

Get complete history of a specific file.

**Parameters:**

- `repo_path` (required): Path to Git repository
- `file_path` (required): Path to file within repository
- `max_commits` (optional): Maximum commits to analyze (default: 50)
- `include_renames` (optional): Track file renames (default: true)

**Returns:** File history with all changes and metadata

### `analyze_file_blame`

Get line-by-line authorship information for a file.

**Parameters:**

- `repo_path` (required): Path to Git repository
- `file_path` (required): Path to file within repository
- `commit` (optional): Specific commit to analyze (default: HEAD)
- `include_line_numbers` (optional): Include line numbers (default: true)

**Returns:** Detailed blame information with author and commit data for each line

## Author & Statistics Tools

### `get_author_stats`

Get comprehensive author statistics and contributions.

**Parameters:**

- `repo_path` (required): Path to Git repository
- `branch` (optional): Branch to analyze (default: current)
- `since` (optional): Date filter for analysis period
- `include_merge_commits` (optional): Include merge commits (default: false)

**Returns:** Author statistics including commit counts, lines changed, and activity patterns

### `get_file_blame`

Get detailed blame information for a specific file.

**Parameters:**

- `repo_path` (required): Path to Git repository
- `file_path` (required): Path to file within repository
- `commit` (optional): Specific commit to blame (default: HEAD)
- `line_range` (optional): Specific line range to analyze

**Returns:** Line-by-line blame information with author and commit details

### `compare_commits_mcp`

Compare commits using MCP-optimized format.

**Parameters:**

- `repo_path` (required): Path to Git repository
- `commit1` (required): First commit hash
- `commit2` (required): Second commit hash
- `format` (optional): Output format ("detailed", "summary")

**Returns:** MCP-formatted commit comparison data

## Export & Management Tools

### `export_repository_data`

Export repository data in various formats.

**Parameters:**

- `repo_path` (required): Path to Git repository
- `format` (required): Export format ("json", "csv", "yaml")
- `output_path` (optional): Output file path
- `include_diffs` (optional): Include diff data (default: false)
- `date_range` (optional): Date range for export

**Returns:** Export status and file location

### `start_web_server`

Start the GitHound web interface server.

**Parameters:**

- `repo_path` (required): Path to Git repository
- `host` (optional): Server host (default: "localhost")
- `port` (optional): Server port (default: 8000)
- `auto_open` (optional): Auto-open browser (default: true)

**Returns:** Server status and access URL

### `generate_repository_report`

Generate comprehensive repository analysis report.

**Parameters:**

- `repo_path` (required): Path to Git repository
- `report_type` (optional): Report type ("summary", "detailed", "security")
- `output_format` (optional): Output format ("html", "pdf", "markdown")
- `include_charts` (optional): Include visual charts (default: true)

**Returns:** Generated report location and metadata

## MCP Resources

GitHound provides 7 dynamic MCP resources for real-time data access:

### Repository Resources

- `githound://repository/{repo_path}/config` - Repository configuration and metadata
- `githound://repository/{repo_path}/branches` - All branches with detailed information
- `githound://repository/{repo_path}/contributors` - Contributor statistics and activity
- `githound://repository/{repo_path}/summary` - Repository summary and health metrics

### File Resources

- `githound://repository/{repo_path}/files/{file_path}/history` - Complete file change history
- `githound://repository/{repo_path}/commits/{commit_hash}/details` - Detailed commit information
- `githound://repository/{repo_path}/blame/{file_path}` - File blame information

## MCP Prompts

GitHound provides 3 specialized prompts for common workflows:

### `investigate_bug_prompt`

Bug investigation prompt that guides through:

**Parameters:**

- `bug_description` (required): Description of the bug to investigate
- `suspected_files` (optional): Files that might be related to the bug
- `time_frame` (optional): Time frame to focus investigation (default: "last 30 days")

### `prepare_code_review_prompt`

Code review preparation prompt for:

**Parameters:**

- `branch_name` (required): Branch to review
- `base_branch` (optional): Base branch for comparison (default: "main")
- `focus_areas` (optional): Specific areas to focus on during review

### `analyze_performance_regression_prompt`

Performance regression analysis prompt for:

**Parameters:**

- `performance_issue` (required): Description of the performance issue
- `suspected_timeframe` (optional): When the regression might have occurred (default: "last 2 weeks")
- `affected_components` (optional): Components that might be affected

## Tool Categories Summary

### Search & Discovery (5 tools)

- `advanced_search` - Multi-modal repository search
- `fuzzy_search` - Fuzzy string matching
- `content_search` - Advanced content pattern matching
- `detect_patterns` - Code pattern detection
- `search_by_tag` - Tag-based search capabilities

### Repository Management (7 tools)

- `analyze_repository` - Complete repository analysis
- `get_filtered_commits` - Advanced commit filtering
- `list_branches` - Branch information and status
- `list_tags` - Tag management and metadata
- `list_remotes` - Remote repository configuration
- `validate_repository` - Repository health checks
- `generate_repository_report` - Comprehensive reporting

### Commit Analysis (5 tools)

- `analyze_commit` - Detailed commit information
- `get_commit_history` - Historical commit data
- `compare_commits_diff` - Commit comparison
- `compare_branches_diff` - Branch comparison
- `compare_commits_mcp` - MCP-optimized commit comparison

### File Operations (3 tools)

- `get_file_history_mcp` - File change history
- `analyze_file_blame` - Line-by-line authorship
- `get_file_blame` - Detailed blame information

### Statistics & Export (4 tools)

- `get_author_stats` - Author contribution analysis
- `export_repository_data` - Data export capabilities
- `start_web_server` - Web interface access
- Advanced statistics and reporting tools

### Utilities (1+ tools)

- Various utility functions for repository validation
- Configuration management
- Performance optimization
- Error handling and diagnostics

**Total: 29 Tools** providing comprehensive Git repository analysis and search capabilities.

## Usage Patterns

### Basic Repository Analysis

```python
# Get repository overview
analyze_repository(repo_path="/path/to/repo")

# List all branches
list_branches(repo_path="/path/to/repo", include_remote=True)

# Get recent commits
get_commit_history(repo_path="/path/to/repo", max_commits=20)
```

### Advanced Search Operations

```python
# Search for specific patterns
advanced_search(
    repo_path="/path/to/repo",
    query="authentication",
    search_type="content",
    include_patterns=["*.py", "*.js"]
)

# Fuzzy search for similar terms
fuzzy_search(
    repo_path="/path/to/repo",
    query="authentification",  # typo
    threshold=0.7
)
```

### Comparative Analysis

```python
# Compare two commits
compare_commits_diff(
    repo_path="/path/to/repo",
    commit1="abc123",
    commit2="def456"
)

# Compare branches
compare_branches_diff(
    repo_path="/path/to/repo",
    branch1="main",
    branch2="feature/new-auth"
)
```

## Error Handling

All tools include comprehensive error handling:

- **Repository validation** - Ensures valid Git repository
- **Path validation** - Verifies file and directory existence
- **Parameter validation** - Type checking and range validation
- **Graceful degradation** - Partial results when possible
- **Detailed error messages** - Clear diagnostic information

## Performance Considerations

- **Caching** - Results cached for repeated queries
- **Pagination** - Large result sets are paginated
- **Lazy loading** - Data loaded on demand
- **Resource limits** - Configurable limits for large repositories
- **Timeout handling** - Configurable timeouts for long operations
