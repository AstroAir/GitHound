# CLI Usage Guide

GitHound provides a powerful command-line interface for Git repository analysis. This guide covers all CLI commands and options.

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
githound search [OPTIONS] PATTERN REPOSITORY_PATH
```

#### Basic Examples

```bash
# Search for "function" in current repository
githound search "function" .

# Search with case sensitivity
githound search --case-sensitive "Function" .

# Search in specific file types
githound search --file-type "py" "class" .
```

#### Search Options

- `--author PATTERN`: Filter by author name/email
- `--message PATTERN`: Filter by commit message
- `--date-from DATE`: Start date (YYYY-MM-DD or relative like "7 days ago")
- `--date-to DATE`: End date
- `--file-path PATTERN`: Filter by file path pattern
- `--file-type EXTENSION`: Filter by file extension
- `--branch BRANCH`: Search specific branch
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

Compare commits, branches, or files:

```bash
githound diff [OPTIONS] REPOSITORY_PATH
```

#### Examples

```bash
# Compare two commits
githound diff . --commit1 abc123 --commit2 def456

# Compare branches
githound diff . --branch1 main --branch2 feature

# Compare specific file between commits
githound diff . --commit1 abc123 --commit2 def456 --file src/main.py
```

#### Diff Options

- `--commit1 HASH`: First commit hash
- `--commit2 HASH`: Second commit hash
- `--branch1 NAME`: First branch name
- `--branch2 NAME`: Second branch name
- `--file PATH`: Compare specific file
- `--export FILE`: Export results to file
- `--format FORMAT`: Output format

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

# Start with authentication
githound mcp-server --auth --api-key your-key
```

#### MCP Server Options

- `--host HOST`: Server host (default: localhost)
- `--port PORT`: Server port (default: 3000)
- `--auth`: Enable authentication
- `--api-key KEY`: API key for authentication

## Output Formats

GitHound supports multiple output formats:

### JSON Format

```bash
githound search "function" . --format json
```

Structured JSON output with full metadata.

### YAML Format

```bash
githound search "function" . --format yaml
```

Human-readable YAML format.

### CSV Format

```bash
githound search "function" . --format csv
```

Tabular CSV format for analysis tools.

### Text Format

```bash
githound search "function" . --format text
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
githound --config /path/to/config.yaml search "pattern" .

# Override config with environment variables
GITHOUND_MAX_RESULTS=500 githound search "pattern" .
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

   ```
   Error: Repository not found at path: /invalid/path
   ```

   Solution: Verify the repository path exists and is a Git repository.

2. **Invalid date format**

   ```
   Error: Invalid date format. Use YYYY-MM-DD or relative dates like "7 days ago"
   ```

   Solution: Use correct date format.

3. **Permission denied**

   ```
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
