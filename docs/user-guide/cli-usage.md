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

| Command | Description |
|---------|-------------|
| `search` | Search for patterns across Git history |
| `analyze` | Analyze repository metadata and statistics |
| `blame` | Analyze file authorship line by line |
| `diff` | Compare commits, branches, or files |
| `web` | Start the web interface server |
| `mcp-server` | Start the MCP server for AI integration |
| `quickstart` | Interactive quickstart guide |
| `cleanup` | Clean cache and temporary files |
| `version` | Show version and build information |

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
githound search --repo-path . --content "class" --ext py
```

#### Search Options

**Required:**

- `--repo-path, -p PATH`: Repository path (required)

**Search Criteria:**

- `--content, -c PATTERN`: Content search pattern (regex)
- `--commit HASH`: Search for specific commit hash
- `--author, -a PATTERN`: Filter by author name/email
- `--message, -m PATTERN`: Filter by commit message
- `--date-from DATE`: Start date (YYYY-MM-DD)
- `--date-to DATE`: End date (YYYY-MM-DD)
- `--file-path, -f PATTERN`: Filter by file path pattern
- `--ext EXTENSION`: File extensions to include (e.g., py, js)
- `--branch, -b BRANCH`: Search specific branch

**Search Behavior:**

- `--fuzzy`: Enable fuzzy matching
- `--fuzzy-threshold FLOAT`: Fuzzy matching threshold (0.0-1.0, default: 0.8)
- `--case-sensitive, -s`: Enable case-sensitive search
- `--include, -i PATTERN`: Glob patterns to include
- `--exclude, -e PATTERN`: Glob patterns to exclude
- `--max-file-size BYTES`: Maximum file size in bytes
- `--max-results INT`: Maximum number of results to return

**Output Options:**

- `--format FORMAT`: Output format (json, yaml, csv, xml, text, default: text)
- `--output, -o PATH`: Output file path
- `--details`: Show detailed information in text output
- `--metadata`: Include commit metadata in JSON output
- `--no-progress`: Disable progress indicators

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
githound analyze . --output analysis.json --format json

# Include detailed statistics
githound analyze . --detailed
```

#### Analyze Options

- `--detailed/--basic`: Include detailed statistics (default: detailed)
- `--author-stats/--no-author-stats`: Include author statistics (default: enabled)
- `--output, -o FILE`: Output file path
- `--format, -f FORMAT`: Output format (text, json, yaml, csv, xml)

### Blame Command

Analyze file authorship line by line:

```bash
githound blame [OPTIONS] [REPO_PATH] FILE_PATH
```

#### Examples

```bash
# Basic blame analysis
githound blame . src/main.py

# Blame specific commit
githound blame . src/main.py --commit abc123

# Export blame information
githound blame . src/main.py --output blame.json --format json
```

#### Blame Options

- `--commit, -c HASH`: Specific commit to blame (default: HEAD)
- `--format, -f FORMAT`: Output format (json, yaml, csv, xml, text, default: text)
- `--output, -o PATH`: Output file path
- `--line-numbers / --no-line-numbers`: Show line numbers (default: enabled)

### Diff Command

Compare commits or branches:

```bash
githound diff [OPTIONS] [REPO_PATH] FROM_REF TO_REF
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
githound web [OPTIONS] [REPO_PATH]
```

#### Examples

```bash
# Start web server on default port
githound web

# Start on specific host and port
githound web --host 0.0.0.0 --port 9000

# Start with auto-open browser (default behavior)
githound web --open

# Start in development mode
githound web --dev

# Interactive configuration
githound web --interactive
```

#### Web Options

- `--host, -h HOST`: Host to bind the server (default: localhost)
- `--port, -p PORT`: Port to bind the server (default: 8000)
- `--open / --no-open`: Automatically open browser (default: open)
- `--dev`: Enable development mode with auto-reload
- `--interactive, -i`: Interactive configuration mode

### MCP Server Command

Start the MCP (Model Context Protocol) server:

```bash
githound mcp-server [OPTIONS] [REPO_PATH]
```

#### MCP Server Examples

```bash
# Start MCP server on default port
githound mcp-server

# Start on specific port
githound mcp-server --port 4000

# Start with custom host and logging
githound mcp-server --host 0.0.0.0 --port 3000 --log-level DEBUG
```

#### MCP Server Options

- `--port, -p PORT`: Port to bind the MCP server (default: 3000)
- `--host, -h HOST`: Host to bind the server (default: localhost)
- `--log-level LEVEL`: Logging level (default: INFO)

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

### Quickstart Command

Interactive quickstart guide for new users:

```bash
githound quickstart [OPTIONS] [REPO_PATH]
```

#### Quickstart Examples

```bash
# Run interactive quickstart in current repository
githound quickstart

# Run quickstart in specific repository
githound quickstart /path/to/repo
```

The quickstart command provides a guided tour of GitHound's capabilities and helps you get
started with common tasks. It includes interactive menus for repository analysis, search,
blame analysis, diff comparison, and web interface setup.

### Cleanup Command

Clean cache and temporary files:

```bash
githound cleanup [OPTIONS] [REPO_PATH]
```

#### Cleanup Examples

```bash
# Interactive cleanup (default behavior)
githound cleanup

# Only clean cache files
githound cleanup --cache-only

# Skip confirmation prompts
githound cleanup --force
```

#### Cleanup Options

- `--cache-only`: Only clean cache files, leave other temporary files
- `--force, -f`: Skip confirmation prompts

### Version Command

Show version and build information:

```bash
githound version [OPTIONS]
```

#### Version Examples

```bash
# Show basic version information
githound version

# Show detailed build information
githound version --build-info
```

#### Version Options

- `--build-info, -b`: Show detailed build information including dependencies and build environment

## Getting Help

### Command Help

```bash
# General help
githound --help

# Command-specific help
githound search --help
githound analyze --help
githound blame --help
githound diff --help
githound web --help
githound mcp-server --help
githound quickstart --help
githound cleanup --help
githound version --help
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

- **[Configuration Guide](../getting-started/configuration.md)** - Complete configuration reference

### Need Help

- **[Troubleshooting Guide](../troubleshooting/README.md)** - Solve common CLI issues
- **[FAQ](../troubleshooting/faq.md)** - Frequently asked questions

---

**📚 [Back to Documentation Home](../index.md)** |
**⬅️ [Quick Start](../getting-started/quick-start.md)** |
**➡️ [Search Capabilities](search-capabilities.md)**
