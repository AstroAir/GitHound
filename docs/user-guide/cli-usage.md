# CLI Usage Guide

GitHound provides a powerful command-line interface for Git repository analysis. This guide covers
all CLI commands and options.

## Basic Command Structure

```bash
githound [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS] [ARGUMENTS]
```

## Global Options

- `--version`: Show GitHound version
- `--help`: Show help information
- `--verbose, -v`: Enable verbose output
- `--quiet, -q`: Suppress non-essential output
- `--config FILE`: Use custom configuration file

## Commands Overview

### Search Command

Search for patterns across Git history:

```bash
githound search [OPTIONS]
```

#### Basic Examples

```bash
# Search for "function" in current repository
githound search --repo-path . --content "function"

# Search with case sensitivity
githound search --repo-path . --content "Function" --case-sensitive

# Search in specific file types
githound search --repo-path . --content "class" --file-extensions py
```

#### Search Options

- `--repo-path PATH`: Repository path (required)
- `--content PATTERN`: Content search pattern
- `--author PATTERN`: Filter by author name/email
- `--message PATTERN`: Filter by commit message
- `--date-from DATE`: Start date (YYYY-MM-DD or relative like "7 days ago")
- `--date-to DATE`: End date
- `--file-path-pattern PATTERN`: Filter by file path pattern
- `--file-extensions EXT [EXT ...]`: Filter by file extensions
- `--branch BRANCH`: Search specific branch
- `--case-sensitive`: Enable case-sensitive search
- `--fuzzy-search`: Enable fuzzy matching
- `--fuzzy-threshold FLOAT`: Fuzzy matching threshold (0.0-1.0)
- `--max-results INT`: Maximum results to return
- `--include-globs PATTERN [PATTERN ...]`: Include file patterns
- `--exclude-globs PATTERN [PATTERN ...]`: Exclude file patterns
- `--max-results N`: Limit number of results
- `--fuzzy`: Enable fuzzy search
- `--fuzzy-threshold FLOAT`: Fuzzy search threshold (0.0-1.0)
- `--case-sensitive`: Enable case-sensitive search
- `--export FILE`: Export results to file
- `--format FORMAT`: Output format (json, yaml, csv, xml, text)

### Analyze Command

Analyze repository metadata and statistics:

```bash
githound analyze [OPTIONS] REPOSITORY_PATH
```

#### Examples

```bash
# Basic repository analysis
githound analyze .

# Export analysis results
githound analyze . --export analysis.json --format json

# Include detailed statistics
githound analyze . --detailed
```

#### Analyze Options

- `--detailed`: Include detailed statistics
- `--export FILE`: Export results to file
- `--format FORMAT`: Output format
- `--include-branches`: Include branch analysis
- `--include-tags`: Include tag analysis

### Blame Command

Analyze file authorship line by line:

```bash
githound blame [OPTIONS] REPOSITORY_PATH FILE_PATH
```

#### Examples

```bash
# Basic blame analysis
githound blame . src/main.py

# Show author statistics
githound blame . src/main.py --stats

# Export blame information
githound blame . src/main.py --export blame.json
```

#### Blame Options

- `--stats`: Show author statistics
- `--line-range START:END`: Analyze specific line range
- `--export FILE`: Export results to file
- `--format FORMAT`: Output format

### Diff Command

Compare commits or branches:

```bash
githound diff REPOSITORY_PATH FROM_REF TO_REF [OPTIONS]
```

#### Examples

```bash
# Compare two commits
githound diff . abc123 def456

# Compare branches
githound diff . main feature --branches

# Compare specific file between commits
githound diff . abc123 def456 --file src/main.py
```

#### Diff Options

- `FROM_REF`: Source commit/branch reference (required)
- `TO_REF`: Target commit/branch reference (required)
- `--file, -f`: File patterns to filter diff
- `--format, -F`: Output format (text, json, csv)
- `--output, -o`: Output file path
- `--branches`: Compare as branches instead of commits

### Web Command

Start the web interface:

```bash
githound web [OPTIONS]
```

#### Examples

```bash
# Start web server on default port
githound web

# Start on specific host and port
githound web --host 0.0.0.0 --port 9000

# Start with auto-open browser
githound web --open
```

#### Web Options

- `--host HOST`: Server host (default: localhost)
- `--port PORT`: Server port (default: 8000)
- `--open`: Auto-open browser
- `--no-reload`: Disable auto-reload

### MCP Server Command

Start the MCP (Model Context Protocol) server:

```bash
githound mcp-server [OPTIONS]
```

#### Examples

```bash
# Start MCP server on default port
githound mcp-server

# Start on specific port
githound mcp-server --port 4000

# Start MCP server
githound mcp-server --host localhost --port 3000
```

#### MCP Server Options

- `--host HOST`: Server host (default: localhost)
- `--port PORT`: Server port (default: 3000)

### Authentication Configuration

Authentication is configured via environment variables:

```bash
# Enable authentication
export FASTMCP_SERVER_ENABLE_AUTH=true

# GitHub OAuth
export FASTMCP_SERVER_AUTH_GITHUB_CLIENT_ID=your_client_id
export FASTMCP_SERVER_AUTH_GITHUB_CLIENT_SECRET=your_secret

# JWT authentication
export FASTMCP_SERVER_AUTH_JWT_SECRET_KEY=your_secret
```

## Output Formats

GitHound supports multiple output formats:

### JSON Format

```bash
githound search --repo-path . --content "function" --format json
```

Structured JSON output with full metadata.

### YAML Format

```bash
githound search --repo-path . --content "function" --format yaml
```

Human-readable YAML format.

### CSV Format

```bash
githound search --repo-path . --content "function" --format csv
```

Tabular CSV format for analysis tools.

### Text Format

```bash
githound search --repo-path . --content "function" --format text
```

Human-readable text format (default for terminal).

## Advanced Usage

### Complex Search Queries

```bash
# Multi-criteria search
githound search \
  --author "john.doe" \
  --date-from "2023-01-01" \
  --date-to "2023-12-31" \
  --message "bug fix" \
  --file-type "py" \
  "authentication" .

# Fuzzy search with custom threshold
githound search --fuzzy --fuzzy-threshold 0.7 "functon" .

# Search specific branch
githound search --branch feature/auth "login" .
```

### Batch Operations

```bash
# Export multiple analyses
githound analyze . --export analysis.json
githound search "TODO" . --export todos.csv --format csv
githound blame . src/main.py --export blame.yaml --format yaml

# Process multiple repositories
for repo in repo1 repo2 repo3; do
  githound analyze "$repo" --export "${repo}_analysis.json"
done
```

### Pipeline Integration

```bash
# Use in CI/CD pipelines
githound search "TODO\|FIXME\|HACK" . --format json | \
  jq '.results | length' > todo_count.txt

# Generate reports
githound analyze . --format json | \
  jq '.contributors | sort_by(.commits) | reverse' > top_contributors.json
```

## Configuration Integration

### Using Configuration Files

```bash
# Use custom config file
githound --config /path/to/config.yaml search --repo-path . --content "pattern"

# Override config with environment variables
GITHOUND_MAX_RESULTS=500 githound search --repo-path . --content "pattern"
```

### Project-specific Settings

Create `.githound.yaml` in your repository:

```yaml
search:
  file_patterns:
    - "*.py"
    - "*.js"
  exclude_patterns:
    - "node_modules/"
    - "__pycache__/"

aliases:
  bugs: "--message 'bug|fix|error' --date-from '30 days ago'"
```

Use aliases:

```bash
githound search bugs .
```

## Performance Tips

### Optimize Search Performance

```bash
# Limit results for faster searches
githound search "pattern" . --max-results 100

# Search specific file types
githound search --file-type "py" "pattern" .

# Use date ranges to limit scope
githound search --date-from "7 days ago" "pattern" .
```

### Memory Management

```bash
# For large repositories, use streaming output
githound search "pattern" . --format json > results.json

# Process results in chunks
githound search "pattern" . --max-results 1000 --export chunk1.json
```

## Error Handling

### Common Error Messages

1. **Repository not found**

   ```text
   Error: Repository not found at path: /invalid/path
   ```

   Solution: Verify the repository path exists and is a Git repository.

2. **Invalid date format**

   ```text
   Error: Invalid date format. Use YYYY-MM-DD or relative dates like "7 days ago"
   ```

   Solution: Use correct date format.

3. **Permission denied**

   ```text
   Error: Permission denied accessing repository
   ```

   Solution: Check file permissions and repository access.

### Debug Mode

```bash
# Enable verbose output for debugging
githound --verbose search "pattern" .

# Show detailed error information
githound --verbose --debug search "pattern" .
```

## Integration Examples

### Git Hooks

```bash
#!/bin/bash
# pre-commit hook to check for TODOs
todo_count=$(githound search "TODO\|FIXME" . --format json | jq '.results | length')
if [ "$todo_count" -gt 10 ]; then
  echo "Too many TODOs ($todo_count). Please address some before committing."
  exit 1
fi
```

### Continuous Integration

```yaml
# GitHub Actions example
- name: Analyze repository
  run: |
    githound analyze . --export analysis.json
    githound search "TODO\|FIXME" . --export todos.json

- name: Upload artifacts
  uses: actions/upload-artifact@v2
  with:
    name: analysis-results
    path: |
      analysis.json
      todos.json
```

### Monitoring Scripts

```bash
#!/bin/bash
# Daily repository health check
DATE=$(date +%Y%m%d)
githound analyze . --export "health_${DATE}.json"
githound search "bug\|error\|fix" . --date-from "1 day ago" --export "recent_fixes_${DATE}.json"
```

## Getting Help

### Command Help

```bash
# General help
githound --help

# Command-specific help
githound search --help
githound analyze --help
githound blame --help
```

### Version Information

```bash
# Show version
githound --version

# Show detailed version info
githound --version --verbose
```

### Documentation

- Online documentation: [GitHound Docs](https://githound.readthedocs.io)
- GitHub repository: [GitHound GitHub](https://github.com/your-org/githound)
- Issue tracker: [GitHub Issues](https://github.com/your-org/githound/issues)

## 🚀 Related Guides

### User Guides

- **[Search Capabilities](search-capabilities.md)** - Advanced search features and patterns
- **[Export Options](export-options.md)** - Data export formats and configuration
- **[Web Interface](web-interface.md)** - Browser-based GitHound interface

### API Integration

- **[Python API](../api-reference/python-api.md)** - Use GitHound in Python applications
- **[REST API](../api-reference/rest-api.md)** - HTTP API for external integrations
- **[MCP Server](../mcp-server/README.md)** - AI tool integration

### Configuration

- **[Configuration Guide](../getting-started/configuration.md)** - Environment setup
- **[Configuration Guide](../getting-started/configuration.md)** - Complete configuration reference

### Need Help

- **[Troubleshooting Guide](../troubleshooting/README.md)** - Solve common CLI issues
- **[FAQ](../troubleshooting/faq.md)** - Frequently asked questions

---

**📚 [Back to Documentation Home](../index.md)** |
**⬅️ [Quick Start](../getting-started/quick-start.md)** |
**➡️ [Search Capabilities](search-capabilities.md)**
