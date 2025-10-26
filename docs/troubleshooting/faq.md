# Frequently Asked Questions (FAQ)

This document answers the most commonly asked questions about GitHound functionality, configuration, and usage.

## General Questions

### What is GitHound

GitHound is a comprehensive Git repository analysis tool that provides advanced search capabilities, detailed metadata extraction, blame analysis, diff comparison, and multiple integration options including a Model Context Protocol (MCP) server for AI integration.

### What makes GitHound different from other Git tools

GitHound offers:

- **Multi-modal search**: Content, commits, authors, dates, file paths, and types
- **AI Integration**: MCP Server with 29 tools for AI assistants
- **Advanced analysis**: Blame tracking, diff analysis, pattern detection
- **Multiple interfaces**: CLI, Python API, REST API, WebSocket, MCP
- **Export capabilities**: JSON, YAML, CSV, XML, Excel formats
- **Performance**: Parallel processing, caching, streaming results

### Is GitHound free to use

Yes, GitHound is open-source software released under the MIT License. You can use it freely for personal and commercial projects.

## Installation and Setup

### What are the system requirements

- **Python**: 3.11 or higher
- **Git**: 2.30 or higher
- **Redis**: 6.0+ (optional, for caching and rate limiting)
- **Memory**: 2GB+ RAM recommended
- **Storage**: 1GB+ free space

### Can I use GitHound without Redis

Yes, GitHound works without Redis using in-memory caching. Redis is recommended for:

- Better performance with large repositories
- Persistent caching across sessions
- Rate limiting in production deployments
- Multi-user environments

### How do I install GitHound on Windows

```bash
# Install Python 3.11+ from python.org or Microsoft Store
# Install Git from git-scm.com

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install GitHound
pip install githound

# Verify installation
githound --version
```

### Can I run GitHound in Docker

Yes, GitHound includes comprehensive Docker support:

```bash
# Clone repository
git clone https://github.com/AstroAir/GitHound.git
cd GitHound

# Start with Docker Compose
docker-compose up -d

# Access services
# Web API: http://localhost:8000
# MCP Server: http://localhost:3000
```

## Usage Questions

### How do I search for specific content in my repository

```bash
# Basic content search
githound search --repo-path . --content "function_name"

# Advanced search with filters
githound search --repo-path . \
  --content "error handling" \
  --file-type "py" \
  --date-from "2024-01-01" \
  --author "john@example.com"

# Fuzzy search for approximate matches
githound search --repo-path . \
  --content "aproximate_spelling" \
  --fuzzy-search \
  --fuzzy-threshold 0.7
```

### How do I analyze who wrote specific lines of code

```bash
# Analyze blame for entire file
githound blame . src/main.py

# Export blame analysis
githound blame . src/main.py --export blame_analysis.json

# Get blame for specific line range
githound blame . src/main.py --line-start 10 --line-end 50
```

### Can I search across multiple repositories

Currently, GitHound analyzes one repository at a time. For multiple repositories:

```bash
# Script to analyze multiple repos
for repo in repo1 repo2 repo3; do
  githound search --repo-path "$repo" --content "search_term" \
    --export "results_${repo}.json"
done
```

### How do I export search results

```bash
# Export to JSON (default)
githound search --repo-path . --content "query" --export results.json

# Export to different formats
githound search --repo-path . --content "query" --export results.csv
githound search --repo-path . --content "query" --export results.yaml
githound search --repo-path . --content "query" --export results.xlsx

# Include metadata in export
githound search --repo-path . --content "query" \
  --export results.json --include-metadata
```

## MCP Server Questions

### What is the MCP server and why would I use it

The MCP (Model Context Protocol) server allows AI assistants to analyze Git repositories directly. It provides 29 tools for:

- Repository analysis and search
- Commit history exploration
- File blame and diff analysis
- Pattern detection and code insights

### How do I set up the MCP server

```bash
# Start MCP server
python -m githound.mcp_server

# Or with custom configuration
export FASTMCP_SERVER_HOST=0.0.0.0
export FASTMCP_SERVER_PORT=3000
python -m githound.mcp_server
```

### Which AI assistants support MCP

GitHound's MCP server works with:

- **Claude Desktop** (Anthropic)
- **Cursor** (AI code editor)
- **VS Code** (with MCP extensions)
- **GitHub Copilot** (with MCP integration)
- **Custom AI applications** using MCP protocol

### How do I configure authentication for the MCP server

```bash
# Enable authentication
export FASTMCP_SERVER_ENABLE_AUTH=true

# GitHub OAuth
export FASTMCP_SERVER_AUTH_GITHUB_CLIENT_ID=your_client_id
export FASTMCP_SERVER_AUTH_GITHUB_CLIENT_SECRET=your_secret

# JWT authentication
export FASTMCP_SERVER_AUTH_JWT_SECRET_KEY=your_secret
export FASTMCP_SERVER_AUTH_JWT_ISSUER=your_issuer
```

## Performance Questions

### Why are my searches slow

Common causes and solutions:

1. **Large repository**: Use date filters and file type filters
2. **No caching**: Enable Redis caching
3. **Too many workers**: Reduce `GITHOUND_MAX_WORKERS`
4. **Broad search terms**: Use more specific search patterns

```bash
# Optimize performance
export GITHOUND_CACHE_BACKEND=redis
export GITHOUND_MAX_WORKERS=4
export GITHOUND_TIMEOUT=300
```

### How can I improve search performance

1. **Use filters**:

   ```bash
   githound search --file-type py --date-from "2024-01-01"
   ```

2. **Enable caching**:

   ```bash
   export REDIS_URL=redis://localhost:6379/0
   export GITHOUND_CACHE_BACKEND=redis
   ```

3. **Limit results**:

   ```bash
   githound search --max-results 100
   ```

### How much memory does GitHound use

Memory usage depends on:

- Repository size
- Search scope
- Number of results
- Caching configuration

Typical usage:

- **Small repos** (<1000 commits): 100-500MB
- **Medium repos** (1000-10000 commits): 500MB-2GB
- **Large repos** (>10000 commits): 2GB+

## Configuration Questions

### Where does GitHound store its configuration

Configuration locations (in order of precedence):

1. Environment variables
2. Command-line arguments
3. Project config file (`.githound.yaml`)
4. User config file (`~/.githound/config.yaml`)
5. System config file (`/etc/githound/config.yaml`)

### How do I configure GitHound for my team

Create a project configuration file:

```yaml
# .githound.yaml
search:
  max_results: 1000
  fuzzy_threshold: 0.8
  default_file_types: ["py", "js", "ts", "java"]

export:
  default_format: "json"
  include_metadata: true

web:
  host: "0.0.0.0"
  port: 8000
  enable_cors: true

mcp:
  enable_auth: true
  rate_limit_enabled: true
```

### Can I customize the output format

Yes, GitHound supports multiple output formats and customization:

```bash
# Built-in formats
githound search --export results.json    # JSON
githound search --export results.yaml   # YAML
githound search --export results.csv    # CSV
githound search --export results.xlsx   # Excel

# Custom formatting with Python API
from githound import GitHound
results = gh.search_advanced_sync(query)
# Process and format results as needed
```

## Integration Questions

### Can I use GitHound in my CI/CD pipeline

Yes, GitHound works well in CI/CD:

```yaml
# GitHub Actions example
- name: Analyze repository
  run: |
    pip install githound
    githound search --repo-path . --content "TODO" --export todos.json

- name: Upload results
  uses: actions/upload-artifact@v3
  with:
    name: analysis-results
    path: todos.json
```

### How do I integrate GitHound with my Python application

```python
from githound import GitHound
from pathlib import Path

# Initialize GitHound
gh = GitHound(Path("/path/to/repo"))

# Search for content
from githound.models import SearchQuery
query = SearchQuery(
    content_pattern="function_name",
    file_extensions=["py"]
)
results = gh.search_advanced_sync(query, max_results=100)

# Analyze repository
repo_info = gh.analyze_repository()

# Get blame information
blame_info = gh.analyze_blame("src/main.py")
```

### Can I use GitHound with other programming languages

GitHound analyzes Git repositories regardless of programming language. It works with:

- Python, JavaScript, TypeScript, Java, C++, C#, Go, Rust
- HTML, CSS, Markdown, YAML, JSON, XML
- Any text-based files in Git repositories

## Troubleshooting Questions

### GitHound says "not a git repository" but I'm in a Git repo

1. **Check if you're in the repository root**:

   ```bash
   git status
   pwd
   ```

2. **Verify repository integrity**:

   ```bash
   git fsck --full
   ```

3. **Check permissions**:

   ```bash
   ls -la .git/
   ```

### I'm getting permission errors

1. **Check file permissions**:

   ```bash
   chmod -R 755 /path/to/repo
   ```

2. **Run with appropriate user**:

   ```bash
   sudo chown -R $USER:$USER /path/to/repo
   ```

3. **Use virtual environment**:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install githound
   ```

### The web interface isn't loading

1. **Check if server is running**:

   ```bash
   curl http://localhost:8000/health
   ```

2. **Verify port availability**:

   ```bash
   lsof -i :8000  # Linux/Mac
   netstat -ano | findstr :8000  # Windows
   ```

3. **Check logs**:

   ```bash
   export GITHOUND_LOG_LEVEL=DEBUG
   githound web
   ```

## Getting More Help

### Where can I find more documentation

- [Installation Guide](../getting-started/installation.md)
- [User Guide](../user-guide/)
- [API Reference](../api-reference/)
- [MCP Server Documentation](../mcp-server/)
- [Configuration Guide](../getting-started/configuration.md)

### How do I report bugs or request features

1. **Check existing issues**: [GitHub Issues](https://github.com/AstroAir/GitHound/issues)
2. **Create new issue**: Use the issue templates
3. **Join discussions**: [GitHub Discussions](https://github.com/AstroAir/GitHound/discussions)

### How can I contribute to GitHound

For contributing information, please check the main repository for:

- Development setup
- Coding standards
- Testing requirements
- Pull request process

### Is there a community or support forum

- **GitHub Discussions**: Questions and community support
- **GitHub Issues**: Bug reports and feature requests
- **Documentation**: Comprehensive guides and examples
- **Examples**: Real-world usage patterns in the examples directory
