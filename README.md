# GitHound - Enhanced Git Repository Analysis Tool

GitHound is a comprehensive Git repository analysis tool that provides advanced search capabilities, detailed metadata extraction, blame analysis, diff comparison, and multiple integration options including MCP (Model Context Protocol) server support and REST API.

## 🚀 Key Features

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
- **🆕 MCP Server**: Full Model Context Protocol support with FastMCP 2.0
- **REST API**: Comprehensive API for external integrations
- **Web Interface**: Modern web UI with real-time updates
- **CLI Interface**: Rich command-line interface

### 🤖 MCP Integration (New!)

- **25+ MCP Tools**: Advanced search, analysis, and repository management
- **7 MCP Resources**: Dynamic access to repository data and metadata
- **3 MCP Prompts**: Structured workflows for bug investigation, code review, and performance analysis
- **FastMCP 2.0**: Latest MCP protocol with enhanced capabilities
- **LLM-Ready**: Direct integration with Claude, GPT, and other AI models

## 🛠 Installation

```bash
# Install development version (currently the only way to install)
git clone https://github.com/AstroAir/GitHound.git
cd GitHound
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"

# Install with test dependencies
pip install -e ".[test]"

# Install with all dependencies
pip install -e ".[dev,test,docs,build]"
```

## 🤖 MCP Integration

GitHound now provides full Model Context Protocol (MCP) support, allowing LLMs to directly access all repository analysis capabilities.

### Starting the MCP Server

```bash
# Start MCP server (stdio transport by default)
githound mcp-server

# Start with custom host and port
githound mcp-server --host 0.0.0.0 --port 3000

# Start with custom log level
githound mcp-server --log-level DEBUG

# Or run directly
python -m githound.mcp_server
```

### MCP Tools Available

- **Search Tools**: `advanced_search`, `fuzzy_search`, `content_search`
- **Analysis Tools**: `analyze_repository`, `analyze_commit`, `analyze_file_blame`
- **Comparison Tools**: `compare_commits_diff`, `compare_branches_diff`
- **Management Tools**: `list_branches`, `list_tags`, `validate_repository`
- **Export Tools**: `export_repository_data`, `generate_repository_report`
- **Web Tools**: `start_web_server`

### MCP Resources

- `githound://repository/{repo_path}/config` - Repository configuration
- `githound://repository/{repo_path}/summary` - Repository summary
- `githound://repository/{repo_path}/files/{file_path}/history` - File history
- `githound://repository/{repo_path}/commits/{commit_hash}/details` - Commit details

### MCP Prompts

- `investigate_bug` - Structured bug investigation workflow
- `prepare_code_review` - Code review preparation workflow
- `analyze_performance_regression` - Performance regression analysis

For detailed MCP documentation, see [docs/mcp_integration.md](docs/mcp_integration.md).

## 🚀 Quick Start

### Command Line Interface

```bash
# Basic content search
githound search --repo-path /path/to/repo --content "function"

# Advanced search with multiple criteria
githound search --repo-path /path/to/repo --author "john.doe" --date-from "2023-01-01" --message "bug fix"

# Repository analysis
githound analyze /path/to/repo

# File blame analysis
githound blame /path/to/repo src/main.py

# Export results
githound search --repo-path /path/to/repo --content "function" --export results.yaml --format yaml
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
results = await gh.search_advanced(query)

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
    get_repository, get_repository_metadata, get_commits_with_filters,
    extract_commit_metadata
)
from githound.git_blame import get_file_blame, get_author_statistics
from githound.git_diff import compare_commits, compare_branches
from pathlib import Path
from datetime import datetime

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

## 📚 Examples and Documentation

GitHound includes comprehensive examples demonstrating all functionality:

### Example Categories

- **`examples/mcp_server/`** - MCP server usage examples and client interactions
- **`examples/rest_api/`** - REST API usage with sample requests/responses
- **`examples/git_operations/`** - Git repository analysis and operations
- **`examples/output_formats/`** - JSON/YAML output examples and schemas
- **`examples/error_handling/`** - Error handling patterns and recovery
- **`examples/workflows/`** - End-to-end workflow examples

### Running Examples

```bash
# MCP server examples
python examples/mcp_server/basic_setup.py
python examples/mcp_server/tool_usage.py /path/to/repo
python examples/mcp_server/client_interactions.py /path/to/repo

# Git operations examples
python examples/git_operations/repository_analysis.py /path/to/repo
python examples/git_operations/commit_analysis.py /path/to/repo [commit_hash]

# Output format examples
python examples/output_formats/json_output.py /path/to/repo

# REST API examples (requires running server)
uvicorn githound.web.api:app --reload --port 8000
python examples/rest_api/basic_usage.py /path/to/repo
```

## 🧪 Testing

GitHound includes comprehensive test coverage with multiple test categories:

### Test Categories

- **Unit Tests**: Core functionality testing
- **Integration Tests**: End-to-end workflow testing
- **Performance Tests**: Performance benchmarks and limits
- **API Tests**: REST API endpoint testing
- **MCP Tests**: MCP server functionality testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/                    # Unit tests
pytest tests/integration/             # Integration tests
pytest tests/performance/             # Performance tests

# Run with markers
pytest -m "not slow"                  # Skip slow tests
pytest -m "performance"               # Only performance tests
pytest -m "integration"               # Only integration tests

# Run specific test suites
pytest tests/test_git_enhancements.py
pytest tests/test_structured_output.py
pytest tests/test_mcp_server.py
pytest tests/test_enhanced_api.py

# Run with coverage
pytest --cov=githound --cov-report=html --cov-report=term

# Run with verbose output
pytest -v -s

# Run performance benchmarks
pytest tests/performance/ --benchmark-only
```

### Test Requirements

All tests maintain:

- **Zero errors** for both pytest and mypy
- **Comprehensive coverage** of all functionality
- **Type safety** with proper annotations
- **Performance benchmarks** within acceptable limits

```bash
# Verify type checking
mypy githound --show-error-codes

# Check test coverage
pytest --cov=githound --cov-report=term --cov-fail-under=90
```

## 🔌 API Reference

### MCP Server Tools

GitHound provides comprehensive MCP tools for AI integration:

| Tool                     | Description                  | Parameters                                                 |
| ------------------------ | ---------------------------- | ---------------------------------------------------------- |
| `analyze_repository`     | Repository metadata analysis | `repo_path`                                                |
| `analyze_commit`         | Detailed commit analysis     | `repo_path`, `commit_hash`                                 |
| `get_commit_history`     | Filtered commit history      | `repo_path`, `max_count`, `author`, `date_from`, `date_to` |
| `get_file_history`       | File change history          | `repo_path`, `file_path`, `max_count`                      |
| `get_file_blame`         | Line-by-line blame info      | `repo_path`, `file_path`                                   |
| `compare_commits`        | Commit comparison            | `repo_path`, `from_commit`, `to_commit`                    |
| `compare_branches`       | Branch comparison            | `repo_path`, `from_branch`, `to_branch`                    |
| `get_author_stats`       | Author statistics            | `repo_path`                                                |
| `export_repository_data` | Data export                  | `repo_path`, `output_path`, `format`                       |

### MCP Resource URIs

| Resource                                    | Description              |
| ------------------------------------------- | ------------------------ |
| `githound://repository/{path}/config`       | Repository configuration |
| `githound://repository/{path}/contributors` | Contributor information  |
| `githound://repository/{path}/summary`      | Repository summary       |

### REST API Endpoints

| Endpoint                  | Method    | Description               |
| ------------------------- | --------- | ------------------------- |
| `/health`                 | GET       | API health check          |
| `/api/search`             | POST      | Start new search          |
| `/api/search/{id}`        | GET       | Get search results        |
| `/api/search/{id}/status` | GET       | Get search status         |
| `/api/searches`           | GET       | List all searches         |
| `/api/export`             | POST      | Export data               |
| `/ws/{search_id}`         | WebSocket | Real-time search progress |

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone repository
git clone https://github.com/AstroAir/GitHound.git
cd GitHound

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run type checking
mypy githound
```

### Code Quality

- **Type Safety**: All code must pass mypy type checking
- **Test Coverage**: Maintain >90% test coverage
- **Documentation**: Update documentation for new features
- **Examples**: Add examples for new functionality

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastMCP](https://github.com/jlowin/fastmcp) for MCP server support
- Uses [GitPython](https://github.com/gitpython-developers/GitPython) for Git operations
- API built with [FastAPI](https://fastapi.tiangolo.com/)
- Testing with [pytest](https://pytest.org/)

## 📞 Support

- **Documentation**: [Full documentation](https://github.com/AstroAir/GitHound/tree/master/docs)
- **Issues**: [GitHub Issues](https://github.com/AstroAir/GitHound/issues)
- **Discussions**: [GitHub Discussions](https://github.com/AstroAir/GitHound/discussions)
- **Examples**: See `examples/` directory for comprehensive usage examples
