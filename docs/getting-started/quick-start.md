# Quick Start Guide

Get up and running with GitHound in just a few minutes! This guide will walk you through the basic usage and key features.

## Prerequisites

Make sure you have GitHound installed. If not, see the [Installation Guide](installation.md).

## Basic Usage

### 1. Your First Search

Navigate to any Git repository and run a basic search:

```bash
cd /path/to/your/git/repo
githound search "function" .
```

This searches for the word "function" in all commits in the current repository.

### 2. Repository Analysis

Get comprehensive repository information:

```bash
githound analyze .
```

This provides:

- Repository metadata (branches, tags, remotes)
- Contributor statistics
- Commit patterns
- File type distribution

### 3. File Blame Analysis

Analyze who wrote each line of a file:

```bash
githound blame . src/main.py
```

This shows:

- Line-by-line authorship
- Commit information for each line
- Author statistics for the file

## Advanced Search Examples

### Search by Author

```bash
githound search --author "john.doe" .
```

### Search by Date Range

```bash
githound search --date-from "2023-01-01" --date-to "2023-12-31" .
```

### Search by File Type

```bash
githound search --file-type "py" "class" .
```

### Combined Search

```bash
githound search \
  --author "john.doe" \
  --date-from "2023-01-01" \
  --message "bug fix" \
  --file-type "py" \
  "function" .
```

### Fuzzy Search

```bash
githound search --fuzzy --fuzzy-threshold 0.8 "functon" .
```

## Export Results

### Export to JSON

```bash
githound search "function" . --export results.json --format json
```

### Export to YAML

```bash
githound search "function" . --export results.yaml --format yaml
```

### Export to CSV

```bash
githound search "function" . --export results.csv --format csv
```

## Web Interface

Start the web interface for interactive analysis:

```bash
githound web --port 8000
```

Then open <http://localhost:8000> in your browser.

Features:

- Interactive search interface
- Real-time results
- Visual diff viewer
- Export capabilities
- WebSocket updates

## MCP Server

Start the MCP (Model Context Protocol) server for AI integration:

```bash
githound mcp-server --port 3000
```

This enables AI tools to interact with GitHound programmatically.

## Common Workflows

### 1. Bug Investigation

When investigating a bug, you might want to:

```bash
# Find recent changes to a specific file
githound search --file-path "src/buggy_file.py" --date-from "2023-11-01" .

# Check who last modified specific lines
githound blame . src/buggy_file.py

# Compare recent commits
githound diff --commit1 HEAD~5 --commit2 HEAD .
```

### 2. Code Review Preparation

Before a code review:

```bash
# Find all changes by a specific author
githound search --author "developer" --date-from "2023-11-01" .

# Export changes for review
githound search --author "developer" --date-from "2023-11-01" . \
  --export review.json --format json
```

### 3. Refactoring Analysis

When planning refactoring:

```bash
# Find all usages of a function
githound search "old_function_name" .

# Analyze file history
githound blame . src/legacy_file.py

# Check recent changes to understand impact
githound search --file-path "src/legacy_file.py" --date-from "2023-01-01" .
```

## Configuration

### Basic Configuration

Create `~/.githound/config.yaml`:

```yaml
# Search defaults
search:
  max_results: 1000
  fuzzy_threshold: 0.8

# Export defaults
export:
  default_format: "json"
  include_metadata: true

# Web server defaults
web:
  host: "localhost"
  port: 8000
```

### Environment Variables

```bash
export GITHOUND_DEFAULT_REPO="/path/to/default/repo"
export GITHOUND_LOG_LEVEL="INFO"
```

## Performance Tips

### 1. Use Specific Searches

Instead of broad searches, be specific:

```bash
# Good: Specific file type and pattern
githound search --file-type "py" "class MyClass" .

# Less efficient: Broad search
githound search "class" .
```

### 2. Limit Date Ranges

For large repositories, limit the date range:

```bash
githound search --date-from "2023-01-01" "function" .
```

### 3. Use Caching

GitHound automatically caches results. For repeated searches, subsequent runs will be faster.

## Output Formats

### Terminal Output

By default, GitHound provides rich terminal output with:

- Syntax highlighting
- Progress bars
- Formatted tables
- Color coding

### JSON Output

For programmatic use:

```bash
githound search "function" . --format json
```

### Structured Data

All outputs include comprehensive metadata:

- Commit information
- File paths and line numbers
- Author details
- Timestamps
- Relevance scores

## Next Steps

Now that you're familiar with the basics:

1. **Explore CLI Features**: Read the [CLI Usage Guide](../user-guide/cli-usage.md)
2. **Learn Search Capabilities**: Check out [Search Capabilities](../user-guide/search-capabilities.md)
3. **Try the Web Interface**: Explore the [Web Interface Guide](../user-guide/web-interface.md)
4. **Set Up MCP Server**: Learn about [MCP Server Setup](../mcp-server/setup.md)
5. **API Integration**: Explore the [REST API](../api-reference/rest-api.md)

## Getting Help

- **CLI Help**: Run `githound --help` or `githound COMMAND --help`
- **Documentation**: Browse this documentation site
- **Issues**: Report bugs on [GitHub Issues](https://github.com/your-org/githound/issues)
- **Discussions**: Ask questions in [GitHub Discussions](https://github.com/your-org/githound/discussions)

## Examples Repository

Check out our [examples repository](https://github.com/your-org/githound-examples) for:

- Sample configurations
- Integration examples
- Use case demonstrations
- Best practices
