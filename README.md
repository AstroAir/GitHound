# GitHound - Enhanced Git Repository Analysis Tool

GitHound is a comprehensive Git repository analysis tool that provides advanced search capabilities, detailed metadata extraction, blame analysis, diff comparison, and multiple integration options including MCP (Model Context Protocol) server support and REST API.

## 🚀 New Features (v2.0)

### Enhanced Git Information Retrieval
- **Advanced Metadata Extraction**: Comprehensive commit, branch, tag, and repository information
- **Advanced Git Log Parsing**: Filter by date range, author, file patterns, and commit message keywords
- **Git Blame Functionality**: Line-by-line authorship tracking with detailed history
- **Git Diff Analysis**: Compare commits, branches, and files with detailed change analysis

### Structured Data Output
- **JSON/YAML Schemas**: Standardized data formats for all git information types
- **Enhanced Export Capabilities**: Export in JSON, YAML, CSV, XML formats with filtering and sorting
- **Data Filtering and Sorting**: Comprehensive options for data manipulation and presentation

### MCP (Model Context Protocol) Server Support
- **FastMCP Integration**: Full MCP server implementation exposing all GitHound functionality
- **MCP Tools**: Repository analysis, commit history, blame analysis, diff comparison
- **MCP Resources**: Repository configuration, branch information, contributor statistics
- **Error Handling**: Comprehensive error handling and response formatting

### Complete API Interface
- **Enhanced REST API**: Comprehensive endpoints for all functionality
- **OpenAPI Documentation**: Detailed Swagger/OpenAPI documentation
- **Authentication & Authorization**: JWT-based authentication with role-based access
- **Rate Limiting & Security**: Built-in security measures and rate limiting
- **Async Operations**: Support for long-running operations with status tracking

## 📋 Features

### Core Functionality
- **Multi-modal Search**: Search by content, commit hash, author, message, date range, file path, and file type
- **Fuzzy Search**: Find approximate matches with configurable similarity thresholds
- **Advanced Filtering**: Filter results by file patterns, commit size, and other criteria
- **Progress Tracking**: Real-time progress reporting with cancellation support

### Analysis Capabilities
- **Repository Analysis**: Comprehensive repository metadata and statistics
- **Commit Analysis**: Detailed commit information with file changes
- **Blame Analysis**: Line-by-line authorship tracking
- **Diff Analysis**: Compare commits, branches, and files
- **Author Statistics**: Contribution analysis and statistics

### Export and Integration
- **Multiple Export Formats**: JSON, YAML, CSV, XML, Excel, and text formats
- **Data Filtering**: Advanced filtering and sorting options
- **MCP Server**: Model Context Protocol server for AI integration
- **REST API**: Comprehensive API for external integrations
- **Web Interface**: Modern web UI with real-time updates
- **CLI Interface**: Rich command-line interface

## 🛠 Installation

```bash
# Install from PyPI
pip install githound

# Install with all dependencies
pip install githound[all]

# Install development version
git clone https://github.com/your-org/githound.git
cd githound
pip install -e ".[dev]"
```

## 🚀 Quick Start

### Command Line Interface

```bash
# Basic content search
githound search "function" /path/to/repo

# Advanced search with multiple criteria
githound search --author "john.doe" --date-from "2023-01-01" --message "bug fix" /path/to/repo

# Repository analysis
githound analyze /path/to/repo

# File blame analysis
githound blame /path/to/repo src/main.py

# Export results
githound search "function" /path/to/repo --export results.yaml --format yaml
```

### MCP Server

```bash
# Start MCP server
githound mcp-server

# Or run directly
python -m githound.mcp_server
```

### Web Interface & API

```bash
# Start web server with enhanced API
githound web --host 0.0.0.0 --port 8000

# API documentation available at:
# http://localhost:8000/api/v2/docs (Enhanced API)
# http://localhost:8000/api/docs (Legacy API)
```

### Python API

```python
from githound import GitHound
from githound.models import SearchQuery
from githound.schemas import ExportOptions, OutputFormat
from pathlib import Path

# Initialize GitHound
gh = GitHound(Path("/path/to/repo"))

# Repository analysis
repo_info = gh.analyze_repository()
print(f"Repository has {repo_info['total_commits']} commits")

# Advanced search
query = SearchQuery(
    content_pattern="function",
    author_pattern="john",
    fuzzy_search=True,
    fuzzy_threshold=0.8
)
results = gh.search_advanced(query)

# Blame analysis
blame_info = gh.analyze_blame("src/main.py")
print(f"File has {blame_info.total_lines} lines from {len(blame_info.contributors)} contributors")

# Diff analysis
diff_info = gh.compare_commits("commit1", "commit2")
print(f"Diff: {diff_info.files_changed} files changed")

# Export with options
export_options = ExportOptions(
    format=OutputFormat.YAML,
    include_metadata=True,
    pretty_print=True
)
gh.export_with_options(results, "output.yaml", export_options)
```

## 🔧 Advanced Usage

### Enhanced Git Operations

```python
from githound.git_handler import (
    get_repository_metadata, get_commits_with_filters,
    extract_commit_metadata
)
from githound.git_blame import get_file_blame, get_author_statistics
from githound.git_diff import compare_commits, compare_branches

# Repository metadata
repo = get_repository(Path("/path/to/repo"))
metadata = get_repository_metadata(repo)

# Filtered commits
commits = get_commits_with_filters(
    repo=repo,
    author_pattern="john",
    date_from=datetime(2023, 1, 1),
    file_patterns=["*.py"]
)

# Author statistics
author_stats = get_author_statistics(repo)

# Compare branches
diff_result = compare_branches(repo, "main", "feature-branch")
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test suites
pytest tests/test_git_enhancements.py
pytest tests/test_structured_output.py
pytest tests/test_mcp_server.py
pytest tests/test_enhanced_api.py

# Run with coverage
pytest --cov=githound --cov-report=html

# Run integration tests
pytest tests/integration/
```