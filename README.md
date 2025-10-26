# GitHound - Advanced Git Repository Analysis Tool

GitHound is a comprehensive Git repository analysis tool that provides advanced search capabilities,
detailed metadata extraction, blame analysis, diff comparison, and multiple integration options
including Model Context Protocol (MCP) server support and REST API.

## 🚀 Key Features

- **🔍 Advanced Search**: Multi-modal search across commits, content, authors, and metadata
- **📊 Repository Analysis**: Comprehensive Git analysis with blame, diff, and statistics
- **🤖 AI Integration**: Full MCP Server support for seamless AI tool integration
- **🌐 Multiple Interfaces**: CLI, REST API, WebSocket, and Web Interface options
- **📤 Flexible Export**: Multiple output formats with advanced filtering and sorting

> **📚 For complete feature details, see our [full documentation](docs/index.md)**

## 🎯 Use Cases

### For Developers

- **Code Archaeology**: Understand how code evolved over time
- **Bug Investigation**: Track down when and why bugs were introduced
- **Refactoring Planning**: Identify code patterns and dependencies
- **Code Review**: Analyze changes and their impact

### For Project Managers

- **Team Analytics**: Understand team contributions and patterns
- **Release Planning**: Analyze changes between releases
- **Quality Metrics**: Track code quality and technical debt
- **Risk Assessment**: Identify high-risk areas and dependencies

### For AI/ML Applications

- **Training Data**: Extract structured git data for ML models
- **Code Understanding**: Provide context for AI code assistants
- **Automated Analysis**: Integrate with AI workflows via MCP Server
- **Pattern Recognition**: Identify development patterns and anomalies

## 📚 Documentation

### Getting Started

- **[Quick Start Guide](docs/getting-started/quick-start.md)** - Get up and running in minutes
- **[Installation Guide](docs/getting-started/installation.md)** - Detailed setup instructions
- **[Configuration Guide](docs/getting-started/configuration.md)** - Configuration options

### User Guides

- **[CLI Usage](docs/user-guide/cli-usage.md)** - Command-line interface guide
- **[Search Capabilities](docs/user-guide/search-capabilities.md)** - Advanced search features
- **[Export Options](docs/user-guide/export-options.md)** - Data export and formatting
- **[Web Interface](docs/user-guide/web-interface.md)** - Web-based interface guide

### API Reference

- **[Python API](docs/api-reference/python-api.md)** - Complete Python library documentation
- **[REST API](docs/api-reference/rest-api.md)** - HTTP API documentation
- **[WebSocket API](docs/api-reference/websocket-api.md)** - Real-time API documentation

### Integration Guides

- **[MCP Server](docs/mcp-server/README.md)** - Model Context Protocol integration

### 🤖 MCP Integration

- **30+ MCP Tools**: Advanced search, analysis, repository management, and web integration
- **7 MCP Resources**: Dynamic access to repository data and metadata
- **3 MCP Prompts**: Structured workflows for bug investigation, code review, and performance analysis
- **FastMCP 2.0**: Latest MCP protocol with enhanced capabilities and authentication support
- **Advanced Authentication**: Permit.io and Eunomia authorization providers for fine-grained access
- **LLM-Ready**: Direct integration with Claude, GPT, Cursor, and other AI models

## 🛠 Installation

**Note**: GitHound is currently in development and not yet published to PyPI. Install from source:

### Prerequisites

- **Python 3.11+**: GitHound requires Python 3.11 or higher
- **Git**: Git must be installed and accessible in your PATH

### Installation Steps

```bash
# Clone the repository
git clone https://github.com/AstroAir/GitHound.git
cd GitHound

# Basic installation
pip install -e .

# Install with development dependencies (recommended for contributors)
pip install -e . --dependency-groups dev

# Install with test dependencies
pip install -e . --dependency-groups test

# Install with documentation dependencies
pip install -e . --dependency-groups docs

# Install with build dependencies
pip install -e . --dependency-groups build

# Install with all dependencies (recommended for development)
pip install -e . --dependency-groups dev,test,docs,build
```

### Alternative Installation Methods

```bash
# Using uv (faster package manager)
uv pip install -e . --dependency-groups dev,test,docs,build

# Using make (if available)
make install-dev
```

## 🤖 MCP Server

GitHound provides full Model Context Protocol (MCP) support, allowing LLMs to directly access
all repository analysis capabilities.

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

# Start from specific repository
githound mcp-server /path/to/repo --port 4000
```

### MCP Tools Available (29 Tools)

- **Search Tools**: `advanced_search`, `fuzzy_search`, `content_search`, `detect_patterns`,
  `search_by_tag`, `create_search_engine`, `query_searcher_registry`, `get_search_analytics`
- **Analysis Tools**: `analyze_repository`, `analyze_commit`, `get_filtered_commits`,
  `get_file_history_mcp`, `analyze_branches`, `analyze_diffs`, `analyze_statistics`, `analyze_tags`
- **Blame Tools**: `analyze_file_blame`, `get_file_blame`, `get_author_stats`
- **Comparison Tools**: `compare_commits_diff`, `compare_branches_diff`, `compare_commits_mcp`
- **Management Tools**: `list_branches`, `list_tags`, `list_remotes`, `validate_repository`
- **Export Tools**: `export_repository_data`, `generate_repository_report`
- **Web Tools**: `start_web_server`

### MCP Resources (7 Resources)

- `githound://repository/{repo_path}/config` - Repository configuration and metadata
- `githound://repository/{repo_path}/branches` - All branches with detailed information
- `githound://repository/{repo_path}/contributors` - Contributor statistics and activity
- `githound://repository/{repo_path}/summary` - Repository summary and health metrics
- `githound://repository/{repo_path}/files/{file_path}/history` - Complete file change history
- `githound://repository/{repo_path}/commits/{commit_hash}/details` - Detailed commit information
- `githound://repository/{repo_path}/blame/{file_path}` - File blame information

### MCP Prompts (3 Prompts)

- `investigate_bug_prompt` - Structured bug investigation workflow with search strategies
- `prepare_code_review_prompt` - Code review preparation workflow with analysis steps
- `analyze_performance_regression_prompt` - Performance regression analysis with systematic approach

### MCP Configuration

GitHound supports standard MCP.json configuration for AI platforms:

```json
{
  "mcpServers": {
    "githound": {
      "command": "python",
      "args": ["-m", "githound.mcp_server"],
      "env": {
        "PYTHONPATH": "/path/to/githound",
        "FASTMCP_SERVER_LOG_LEVEL": "INFO"
      },
      "description": "GitHound MCP Server - Comprehensive Git repository analysis"
    }
  }
}
```

For detailed MCP documentation, see [docs/mcp-server/README.md](docs/mcp-server/README.md).

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

# Compare commits or branches
githound diff /path/to/repo abc123 def456

# Export results to file (supports JSON, YAML, CSV formats)
githound search --repo-path /path/to/repo --content "function" --output results.yaml --format yaml
githound search --repo-path /path/to/repo --content "function" --output results.csv --format csv

# Excel format available with optional dependencies (pandas, openpyxl)
# pip install pandas openpyxl
# githound search --repo-path /path/to/repo --content "function" --output results.xlsx --format excel

# Interactive quickstart guide
githound quickstart /path/to/repo

# Clean cache and temporary files
githound cleanup --cache-only  # Only clean cache files
githound cleanup --force       # Skip confirmation prompts

# Show version and build information
githound version
githound version --build-info  # Show detailed build information
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
# Start web server
githound web --host 0.0.0.0 --port 8000

# Start with auto-open browser
githound web --open

# Start in development mode with auto-reload
githound web --dev

# Interactive configuration mode
githound web --interactive

# API documentation available at:
# http://localhost:8000/docs (OpenAPI/Swagger)
# http://localhost:8000/redoc (ReDoc)
# http://localhost:8000/api/info (API information)
```

### Python API

```python
from githound import GitHound
from githound.models import SearchQuery
from githound.schemas import OutputFormat
from pathlib import Path

# Initialize GitHound with repository
repo_path = Path("/path/to/repo")
gh = GitHound(repo_path)

# Repository analysis
repo_info = gh.analyze_repository()
print(f"Repository has {repo_info['total_commits']} commits")

# Advanced search
query = SearchQuery(
    content_pattern="function",
    author_pattern="john",
    fuzzy_search=True,
    fuzzy_threshold=0.8,
    max_results=100
)
results = await gh.search_advanced(query)

# Blame analysis
blame_info = gh.analyze_blame("src/main.py")
print(f"File has {len(blame_info.lines)} lines from {len(set(line.author for line in blame_info.lines))} contributors")

# Author statistics
author_stats = gh.get_author_statistics()
print(f"Repository has {len(author_stats)} contributors")

# Diff analysis
diff_info = gh.compare_commits("commit1", "commit2")
print(f"Diff: {diff_info.statistics.files_changed} files changed")

# Export results to file (supports JSON, YAML, CSV)
from githound.utils.export import ExportManager
from pathlib import Path
export_manager = ExportManager()
export_manager.export_to_yaml(results, Path("output.yaml"), include_metadata=True)
export_manager.export_to_json(results, Path("output.json"), include_metadata=True)
export_manager.export_to_csv(results, Path("output.csv"), include_metadata=True)
```

## 🔧 Advanced Usage

### Enhanced Git Operations

```python
from githound import GitHound
from githound.models import SearchQuery
from githound.schemas import OutputFormat
from pathlib import Path
from datetime import datetime

# Repository analysis
gh = GitHound(Path("/path/to/repo"))
repo_info = gh.analyze_repository()

# Search with filters
search_query = SearchQuery(
    author_pattern="john",
    date_from=datetime(2023, 1, 1),
    file_extensions=["py"]
)
results = gh.search_advanced_sync(search_query)

# Blame analysis
blame_info = gh.analyze_blame("src/main.py")

# Export results
from githound.schemas import ExportOptions
options = ExportOptions(format=OutputFormat.JSON, include_metadata=True)
gh.export_with_options(results, "analysis.json", options)
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
uvicorn githound.web.main:app --reload --port 8000
python examples/rest_api/rest_basic_usage.py
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

GitHound provides 29 comprehensive MCP tools for AI integration:

| Category | Tools | Description |
| -------- | ----- | ----------- |
| **Search** | `advanced_search`, `fuzzy_search`, `content_search` | Multi-modal search with fuzzy matching |
| **Analysis** | `analyze_repository`, `analyze_commit`, `analyze_branches` | Repository and commit analysis |
| **Blame** | `analyze_file_blame`, `get_file_blame`, `get_author_stats` | Line-by-line authorship tracking |
| **Comparison** | `compare_commits_diff`, `compare_branches_diff` | Detailed diff analysis |
| **Management** | `list_branches`, `list_tags`, `validate_repository` | Repository management |
| **Export** | `export_repository_data`, `generate_repository_report` | Data export in multiple formats |
| **Advanced** | `detect_patterns`, `analyze_statistics`, `create_search_engine` | Pattern detection and analytics |

### MCP Resource URIs

| Resource                                    | Description              |
| ------------------------------------------- | ------------------------ |
| `githound://repository/{path}/config`       | Repository configuration |
| `githound://repository/{path}/contributors` | Contributor information  |
| `githound://repository/{path}/summary`      | Repository summary       |

### REST API Endpoints

| Endpoint                           | Method    | Description               |
| ---------------------------------- | --------- | ------------------------- |
| `/health`                          | GET       | API health check          |
| `/api/v1/search/advanced`          | POST      | Advanced search           |
| `/api/v1/search/fuzzy`             | GET       | Fuzzy search              |
| `/api/v1/search/historical`        | GET       | Historical search         |
| `/api/v1/analysis/blame`           | POST      | File blame analysis       |
| `/api/v1/analysis/diff/commits`    | POST      | Commit comparison         |
| `/api/integration/export`          | POST      | Export data               |
| `/ws/{connection_id}`              | WebSocket | Real-time updates         |

## 🤝 Contributing

We welcome contributions! Please check the repository for contribution guidelines.

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
- CLI powered by [Typer](https://typer.tiangolo.com/) with [Rich](https://rich.readthedocs.io/)
- Search capabilities enhanced by [RapidFuzz](https://github.com/maxbachmann/RapidFuzz)
- Caching support via [Redis](https://redis.io/) and [DiskCache](https://grantjenks.com/docs/diskcache/)
- Testing with [pytest](https://pytest.org/) and [Playwright](https://playwright.dev/)

## 📞 Support

- **Documentation**: [Full documentation](docs/)
- **Issues**: [GitHub Issues](https://github.com/AstroAir/GitHound/issues)
- **Discussions**: [GitHub Discussions](https://github.com/AstroAir/GitHound/discussions)
- **Examples**: See `examples/` directory for comprehensive usage examples
