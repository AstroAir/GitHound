# GitHound MCP Integration Guide

GitHound now provides comprehensive Model Context Protocol (MCP) integration using FastMCP 2.0, allowing LLMs to directly access all GitHound functionality through standardized tools, resources, and prompts.

## Overview

The GitHound MCP server exposes all repository analysis capabilities through:

- **25+ MCP Tools** for search, analysis, and management
- **7 MCP Resources** for dynamic data access
- **3 MCP Prompts** for common workflows
- **Robust validation** with Pydantic models
- **FastMCP 2.0** patterns and best practices

## Quick Start

### Installation

```bash
# Install GitHound with MCP support
pip install githound[mcp]

# Or upgrade FastMCP to 2.0+
pip install "fastmcp>=2.11.0"
```

### Running the MCP Server

```bash
# Start with stdio transport (default)
python -m githound.mcp_server

# Start with HTTP transport
python -m githound.mcp_server --http --port 3000

# Start with SSE transport
python -m githound.mcp_server --sse --host 0.0.0.0 --port 3001
```

## MCP Tools

### Advanced Search Tools

#### `advanced_search`

Perform multi-modal search across the repository with comprehensive filtering.

**Parameters:**

- `repo_path` (required): Path to Git repository
- `content_pattern`: Content pattern to search for
- `commit_hash`: Specific commit hash
- `author_pattern`: Author name or email pattern
- `message_pattern`: Commit message pattern
- `date_from`/`date_to`: Date range (ISO format)
- `file_path_pattern`: File path pattern
- `file_extensions`: List of file extensions
- `fuzzy_search`: Enable fuzzy matching
- `fuzzy_threshold`: Fuzzy matching threshold (0.0-1.0)
- `max_results`: Maximum results (default: 100)

**Example:**

```json
{
  "repo_path": "/path/to/repo",
  "content_pattern": "authentication",
  "author_pattern": "john@example.com",
  "date_from": "2024-01-01T00:00:00Z",
  "fuzzy_search": true,
  "fuzzy_threshold": 0.8
}
```

#### `fuzzy_search`

Perform fuzzy search with configurable similarity threshold.

**Parameters:**

- `repo_path` (required): Path to Git repository
- `search_term` (required): Term to search for
- `threshold`: Similarity threshold (0.0-1.0, default: 0.8)
- `search_types`: Types to search (content, author, message, file_path)
- `max_results`: Maximum results (default: 50)

#### `content_search`

Search file content with advanced pattern matching.

**Parameters:**

- `repo_path` (required): Path to Git repository
- `pattern` (required): Content pattern to search for
- `file_extensions`: File extensions to include
- `case_sensitive`: Case sensitive search
- `whole_word`: Match whole words only
- `max_results`: Maximum results (default: 100)

### Repository Analysis Tools

#### `analyze_repository`

Get comprehensive repository metadata and statistics.

#### `analyze_commit`

Analyze a specific commit with detailed information.

#### `get_filtered_commits`

Retrieve commits with advanced filtering options.

#### `get_file_history_mcp`

Get complete change history for a specific file.

#### `analyze_file_blame`

Perform detailed blame analysis on a file.

### Comparison Tools

#### `compare_commits_diff`

Compare two commits and show differences.

#### `compare_branches_diff`

Compare two branches and show differences.

### Repository Management Tools

#### `list_branches`

List all branches with detailed information.

#### `list_tags`

List all tags with metadata.

#### `list_remotes`

List all remote repositories with URLs.

#### `validate_repository`

Validate repository integrity and check for issues.

### Web Interface Tools

#### `start_web_server`

Start the GitHound web interface server.

**Parameters:**

- `repo_path` (required): Path to Git repository
- `host`: Host to bind (default: "localhost")
- `port`: Port to bind (default: 8000)
- `auto_open`: Automatically open browser (default: true)

### Export and Reporting Tools

#### `export_repository_data`

Export repository data in various formats (JSON, YAML, CSV).

#### `generate_repository_report`

Generate comprehensive repository analysis report.

## MCP Resources

Resources provide dynamic access to repository data:

### `githound://repository/{repo_path}/config`

Repository configuration and settings.

### `githound://repository/{repo_path}/branches`

Branch information and metadata.

### `githound://repository/{repo_path}/contributors`

Contributor information and statistics.

### `githound://repository/{repo_path}/summary`

Repository summary and overview.

### `githound://repository/{repo_path}/files/{file_path}/history`

Complete history of changes for a specific file.

### `githound://repository/{repo_path}/commits/{commit_hash}/details`

Detailed information about a specific commit.

### `githound://repository/{repo_path}/blame/{file_path}`

Line-by-line authorship information for a file.

## MCP Prompts

Prompts provide structured workflows for common tasks:

### `investigate_bug`

Generate a structured bug investigation workflow.

**Parameters:**

- `bug_description` (required): Description of the bug
- `suspected_files`: Files that might be related
- `time_frame`: Time frame to investigate (default: "last 30 days")

### `prepare_code_review`

Generate a comprehensive code review preparation workflow.

**Parameters:**

- `branch_name` (required): Branch to review
- `base_branch`: Base branch for comparison (default: "main")
- `focus_areas`: Specific areas to focus on

### `analyze_performance_regression`

Generate a systematic performance regression analysis workflow.

**Parameters:**

- `performance_issue` (required): Description of the performance issue
- `suspected_timeframe`: Time frame when issue occurred (default: "last 2 weeks")
- `affected_components`: Components that might be affected

## Error Handling

All tools include comprehensive error handling:

- **Validation Errors**: Pydantic models validate all inputs
- **Git Errors**: Proper handling of Git command failures
- **File System Errors**: Path validation and existence checks
- **Network Errors**: Graceful handling of web server issues

## Best Practices

### Search Optimization

- Use specific patterns for better results
- Combine multiple search criteria for precision
- Use fuzzy search for approximate matching
- Limit results to avoid overwhelming responses

### Resource Usage

- Cache repository objects when possible
- Use appropriate date ranges for large repositories
- Consider file size limits for content search
- Monitor memory usage with large result sets

### Integration Patterns

- Combine tools for comprehensive analysis
- Use resources for contextual information
- Leverage prompts for guided workflows
- Export results for external processing

## Troubleshooting

### Common Issues

**Repository Not Found**

```
Error: Repository path does not exist: /path/to/repo
```

Solution: Verify the repository path exists and is accessible.

**Invalid Git Repository**

```
Error: Not a valid Git repository
```

Solution: Ensure the path points to a Git repository with `.git` directory.

**Search Timeout**

```
Error: Search operation timed out
```

Solution: Reduce search scope or increase timeout limits.

### Performance Tips

- Use specific file extensions to limit search scope
- Set reasonable `max_results` limits
- Use date ranges to focus on recent changes
- Consider repository size when setting timeouts

## Examples

See the `examples/mcp/` directory for complete usage examples and integration patterns.
