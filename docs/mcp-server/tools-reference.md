# MCP Tools Reference

Comprehensive reference for all 25+ tools exposed by the GitHound MCP server.

## Advanced Search Tools

### `advanced_search`

Perform multi-modal search across the repository with comprehensive filtering.

**Parameters:**

- `repo_path` (required): Path to Git repository
- `query` (required): Search query string
- `search_type` (optional): "content", "commit", "author", "file" (default: "content")
- `branch` (optional): Branch to search (default: current branch)
- `max_results` (optional): Maximum results to return (default: 100)
- `case_sensitive` (optional): Case-sensitive search (default: false)
- `include_patterns` (optional): File patterns to include
- `exclude_patterns` (optional): File patterns to exclude
- `date_from` (optional): Start date filter (ISO format)
- `date_to` (optional): End date filter (ISO format)

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
- `githound://repository/{repo_path}/tags` - All tags with annotations
- `githound://repository/{repo_path}/contributors` - Contributor statistics and activity

### Analysis Resources

- `githound://repository/{repo_path}/summary` - Repository summary and health metrics
- `githound://repository/{repo_path}/activity` - Recent activity and trends
- `githound://repository/{repo_path}/files` - File structure and statistics

## MCP Prompts

GitHound provides 3 specialized prompts for common workflows:

### `analyze_codebase`

Comprehensive codebase analysis prompt that guides through:

- Repository structure analysis
- Code quality assessment
- Contributor activity review
- Security and maintenance recommendations

### `investigate_changes`

Change investigation prompt for:

- Tracking specific changes or features
- Understanding code evolution
- Identifying related commits and authors
- Impact analysis

### `generate_insights`

Repository insights generation prompt for:

- Trend analysis and patterns
- Performance and activity metrics
- Collaboration and workflow insights
- Strategic recommendations

## Tool Categories Summary

### Search & Discovery (4 tools)

- `advanced_search` - Multi-modal repository search
- `fuzzy_search` - Fuzzy string matching
- `content_search` - Advanced content pattern matching
- Pattern analysis capabilities

### Repository Management (7 tools)

- `analyze_repository` - Complete repository analysis
- `get_filtered_commits` - Advanced commit filtering
- `list_branches` - Branch information and status
- `list_tags` - Tag management and metadata
- `list_remotes` - Remote repository configuration
- `validate_repository` - Repository health checks
- `generate_repository_report` - Comprehensive reporting

### Commit Analysis (4 tools)

- `analyze_commit` - Detailed commit information
- `get_commit_history` - Historical commit data
- `compare_commits_diff` - Commit comparison
- `compare_branches_diff` - Branch comparison

### File Operations (2 tools)

- `get_file_history_mcp` - File change history
- `analyze_file_blame` - Line-by-line authorship

### Statistics & Export (3 tools)

- `get_author_stats` - Author contribution analysis
- `export_repository_data` - Data export capabilities
- `start_web_server` - Web interface access

### Utilities (5+ tools)

- Various utility functions for repository validation
- Configuration management
- Performance optimization
- Error handling and diagnostics

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
