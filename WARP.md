# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

GitHound is a comprehensive Git repository analysis tool built in Python 3.11+ that provides advanced search capabilities, detailed metadata extraction, blame analysis, diff comparison, and multiple integration options including MCP (Model Context Protocol) server support and REST API.

## Architecture

### Core Components

- **GitHound Main Class** (`githound/__init__.py`): Central orchestrator providing unified interface for all functionality
- **Search Engine** (`githound/search_engine/`): Modular search system with specialized searchers:
  - `orchestrator.py`: Coordinates multiple search strategies
  - `commit_searcher.py`, `file_searcher.py`: Specialized search implementations
  - `fuzzy_searcher.py`: Fuzzy matching capabilities
- **Git Operations** (`githound/git_*.py`): Core Git interaction modules:
  - `git_handler.py`: Repository metadata and commit processing
  - `git_blame.py`: Line-by-line authorship tracking
  - `git_diff.py`: Commit and branch comparison
- **MCP Server** (`githound/mcp/`): Model Context Protocol implementation for AI integration
- **Web Interface** (`githound/web/`): FastAPI-based REST API and web interface
- **CLI** (`githound/cli.py`): Typer-based command-line interface

### Key Entry Points

- **CLI**: `githound/cli.py` - Main command-line interface using Typer
- **MCP Server**: `githound/mcp_server.py` - MCP protocol server for AI integration
- **Web API**: `githound/web/api.py` - FastAPI REST endpoints
- **Python API**: `githound/__init__.py` - Main GitHound class for programmatic use

### Data Models

- **Core Models** (`githound/models.py`): SearchQuery, SearchResult, GitHoundConfig
- **Export Schemas** (`githound/schemas.py`): ExportOptions, OutputFormat definitions
- **MCP Models** (`githound/mcp/models.py`): MCP-specific data structures

## Development Commands

### Environment Setup

```bash
# Install development dependencies (recommended)
pip install -e ".[dev,test,docs,build]"
# Or use Make
make install-dev

# Set up pre-commit hooks
pre-commit install
```

### Code Quality

```bash
# Run all quality checks (format, lint, type-check)
make quality

# Individual checks
make format      # Black + isort formatting
make lint        # Ruff linting
make type-check  # mypy type checking
```

### Testing

```bash
# Fast unit tests only
make test-unit
pytest -m "unit and not slow" -v

# All tests including integration/performance
make test-all
pytest -v

# Test with coverage
make test-cov
pytest --cov=githound --cov-report=html

# Specific test categories
pytest -m integration    # Integration tests
pytest -m performance    # Performance tests
pytest -m mcp           # MCP server tests
pytest -m api           # API tests

# Single test file
pytest tests/test_git_handler.py -v
```

### Build and Documentation

```bash
# Build package
make build
python -m build

# Build documentation
make docs
cd docs && mkdocs build

# Serve docs locally
make docs-serve
cd docs && mkdocs serve
```

### Development Workflow

```bash
# Quick check before committing
make check  # Runs quality + unit tests

# Full CI pipeline
make ci     # Runs quality + all tests + build
```

## Running GitHound

### CLI Usage

```bash
# Repository analysis
githound analyze .

# Advanced search
githound search --repo-path . --content "function" --author "john"

# File blame analysis
githound blame . src/main.py

# Commit comparison
githound diff HEAD~1 HEAD

# Start web interface
githound web --port 8080
```

### MCP Server

```bash
# Start MCP server (stdio transport)
githound mcp-server

# Start with custom host/port
githound mcp-server --host 0.0.0.0 --port 3000

# Or run directly
python -m githound.mcp_server
```

### Python API

```python
from githound import GitHound
from githound.models import SearchQuery
from pathlib import Path

# Initialize and analyze repository
gh = GitHound(Path("."))
repo_info = gh.analyze_repository()

# Advanced search
query = SearchQuery(content_pattern="function", fuzzy_search=True)
results = gh.search_advanced_sync(query)

# Blame analysis
blame_info = gh.analyze_blame("src/main.py")
```

## Testing Guidelines

### Test Structure

- **Unit Tests**: `tests/test_*.py` - Core functionality testing
- **Integration Tests**: `tests/integration/` - End-to-end workflow testing
- **Performance Tests**: `tests/performance/` - Benchmarks and performance limits
- **MCP Tests**: Tests marked with `@pytest.mark.mcp`
- **API Tests**: Tests marked with `@pytest.mark.api`

### Test Requirements

- All tests must pass both pytest and mypy type checking
- Maintain >85% test coverage (CI enforced)
- Use appropriate test markers for different test categories
- Integration tests may require Docker services (Redis, etc.)

### Running Specific Tests

```bash
# Skip slow tests for faster development
pytest -m "not slow" -v

# Test specific modules
pytest tests/test_search_engine.py
pytest tests/mcp/ -v

# Performance benchmarks
pytest tests/performance/ --benchmark-only
```

## Code Style

- **Python Version**: 3.11+ required
- **Formatting**: Black (line length 100) + isort (profile=black)
- **Linting**: Ruff with comprehensive rule set
- **Type Checking**: mypy with strict settings for core modules
- **Naming Conventions**:
  - Files/modules: `snake_case.py`
  - Classes: `PascalCase`
  - Functions/variables: `snake_case`
  - Constants: `UPPER_CASE`

## Important Configuration

### Environment Variables

- `GITHOUND_*`: Application-specific configuration
- `REDIS_URL`: Redis connection for caching (optional)

### Docker Support

```bash
# Start required services
docker compose up -d redis

# Development environment
docker compose -f docker-compose.yml up
```

## Key Architecture Patterns

### Search Engine Architecture

The search engine uses a modular orchestrator pattern where specialized searchers handle different search types (content, author, commit hash, etc.). The `SearchOrchestrator` coordinates multiple searchers and aggregates results.

### MCP Integration

GitHound provides 25+ MCP tools, 7 resources, and 3 structured prompts for AI integration. The MCP server uses FastMCP 2.0 for protocol compliance and supports both stdio and HTTP transports.

### Async/Sync Patterns

The codebase supports both async and sync operations. Core search operations are async for performance, with sync wrappers provided for convenience (e.g., `search_advanced_sync()`).

### Error Handling

- Use `GitCommandError` for Git-related failures
- Implement retry logic with exponential backoff for transient failures
- Provide detailed error messages with context

## Performance Considerations

- Search operations use streaming results to handle large repositories
- Built-in caching with Redis support for expensive operations
- Progress reporting for long-running operations
- Memory-efficient processing of large Git histories

## Export and Integration

- Multiple export formats: JSON, YAML, CSV, XML, Excel
- REST API with OpenAPI documentation at `/api/v2/docs`
- WebSocket support for real-time progress updates
- MCP protocol for AI model integration
