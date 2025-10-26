# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GitHound is an advanced Git repository analysis tool providing multi-modal search capabilities, detailed metadata extraction, blame analysis, diff comparison, and multiple integration options. It offers three primary interfaces:

1. **CLI** (`githound/cli.py`) - Typer-based command-line interface with Rich output
2. **Web/REST API** (`githound/web/main.py`) - FastAPI application with OpenAPI documentation
3. **MCP Server** (`githound/mcp_server.py`) - Model Context Protocol server for AI integration

## Development Environment

### Requirements

- **Python 3.11+** (3.12 recommended for type checking)
- **Git** must be installed and in PATH
- Virtual environment recommended

### Installation

```bash
# Development installation with all dependencies
pip install -e . --dependency-groups dev,test,docs,build

# Or using make
make install-dev

# Or using uv (faster)
uv pip install -e . --dependency-groups dev,test,docs,build
```

### Python Path on Windows

The installed Python on this system is at:

```text
C:\Users\Max Qian\AppData\Local\Programs\Python\Python311\python.exe
```

Use `.venv/Scripts/python.exe` when working within the virtual environment.

## Common Commands

### Testing

```bash
# Run all tests (requires installed test dependencies)
pytest

# Fast unit tests only (exclude slow/integration tests)
pytest -m "unit and not slow" -v

# Specific test categories
pytest -m integration          # Integration tests
pytest -m performance          # Performance tests
pytest -m mcp                  # MCP server tests
pytest -m api                  # Web API tests

# Run with coverage (90% minimum required)
pytest --cov=githound --cov-report=html --cov-report=term

# Run single test file
pytest tests/test_cli.py -v

# Run specific test
pytest tests/test_cli.py::test_search_command -v

# Using make
make test-unit                 # Fast unit tests
make test-integration          # Integration tests
make test-all                  # All tests
make test-cov                  # With coverage report
```

### Code Quality

```bash
# Format code (Black + isort)
make format

# Run linter (Ruff)
make lint
make lint-fix                  # Auto-fix issues

# Type checking (mypy with strict settings)
make type-check
mypy githound --show-error-codes

# All quality checks at once
make quality                   # format + lint + type-check + docs-validate-quick

# Full CI check
make check                     # quality + test-unit
```

### Running the Application

```bash
# CLI usage
githound search --repo-path /path/to/repo --content "function"
githound analyze /path/to/repo
githound blame /path/to/repo src/main.py
githound diff /path/to/repo commit1 commit2

# Web server (development mode with auto-reload)
uvicorn githound.web.main:app --reload --port 8000

# MCP server
githound mcp-server
githound mcp-server --host 0.0.0.0 --port 3000
python -m githound.mcp_server
```

### Building

```bash
# Clean build artifacts
make clean

# Build package
make build                     # Both wheel and sdist
make build-wheel               # Wheel only
```

## Architecture Overview

### Core Package Structure

```text
githound/
├── __init__.py               # Main GitHound class, primary API entry point
├── cli.py                    # Typer CLI application (command group)
├── models.py                 # Pydantic v2 models (SearchQuery, SearchResult, etc.)
├── schemas.py                # API/export schemas (OutputFormat, ExportOptions)
├── git_handler.py            # GitPython wrappers (get_repository, walk_history)
├── git_blame.py              # Blame analysis functionality
├── git_diff.py               # Diff comparison functionality
├── searcher.py               # Legacy searcher (uses ripgrep when available)
├── search_engine/            # Modular search system (see below)
├── mcp/                      # MCP server integration
│   ├── server.py             # FastMCP 2.x server setup
│   ├── direct_wrappers.py    # MCP tool wrappers
│   ├── tools/                # MCP tool implementations
│   ├── auth/                 # Authentication providers (JWT, OAuth, Permit, Eunomia)
│   └── models.py             # MCP-specific models
├── web/                      # FastAPI web application
│   ├── main.py               # FastAPI app definition, lifespan, middleware
│   ├── apis/                 # API routers (search_api, analysis_api, auth_api)
│   ├── middleware/           # Rate limiting (SlowAPI + Redis)
│   ├── models/               # API models (api_models.py)
│   ├── services/             # Auth service, WebSocket service
│   ├── static/               # Frontend assets
│   └── tests/                # Web frontend Playwright tests
└── utils/                    # Utilities (export, progress, version)
```

### Search Engine Architecture

The search engine is modular and extensible. Located in `githound/search_engine/`:

- **Factory Pattern**: Use `create_search_orchestrator()` from `githound/search_engine/factory.py` to get a configured orchestrator
- **Orchestrator**: `SearchOrchestrator` coordinates multiple searchers, handles parallel execution, ranking, and result aggregation
- **Base Classes**: `BaseSearcher`, `CacheableSearcher`, `ParallelSearcher` in `base.py`
- **Searcher Types**:
  - `commit_searcher.py`: CommitHashSearcher, AuthorSearcher, MessageSearcher, DateRangeSearcher
  - `file_searcher.py`: FilePathSearcher, FileTypeSearcher, ContentSearcher
  - `fuzzy_searcher.py`: FuzzySearcher (uses rapidfuzz)
  - Additional: branch, tag, history, pattern searchers
- **Caching**: `cache.py` supports memory and Redis-based caching
- **Ranking**: `ranking_engine.py` provides relevance scoring

**Important**: Always use the factory pattern when creating search orchestrators:

```python
from githound.search_engine import create_search_orchestrator
orchestrator = create_search_orchestrator(enable_advanced=True)
```

### Data Flow

```text
GitPython Repo → Search Orchestrator → Searchers (parallel) →
  → Results → Ranking → SearchResult list → Export/API/CLI
```

Content search prefers ripgrep (via `ripgrepy` dependency) but falls back gracefully if unavailable.

## Key Contracts

### Pydantic Models (v2)

- **SearchQuery** (`models.py`): Query parameters with combined criteria, fuzzy matching, limits, caching options
- **SearchResult** (`models.py`): Search results with commit info, file paths, content snippets, relevance scores
- **SearchMetrics** (`models.py`): Performance metrics (execution time, cache hits, etc.)
- **SearchEngineConfig** (`models.py`): Engine configuration (workers, caching, ranking, limits)
- **ExportOptions/OutputFormat** (`schemas.py`): Export configuration for JSON/YAML/CSV/XML output

### Important Conventions

1. **Type Safety**: Strict mypy typing enforced (100% coverage). All code must pass `mypy githound --show-error-codes`
2. **Formatting**: Black (line length 100), isort, Ruff linting
3. **Test Coverage**: 85% minimum overall, 90% for new code, 95% for core modules
4. **Async/Sync**: Many functions offer both async and sync versions (e.g., `search_advanced()` and `search_advanced_sync()`)

## Integration Points

### Git Operations

- Route all Git access through `git_handler.py` functions: `get_repository()`, `process_commit()`, `walk_history()`, `get_file_history()`
- Don't reimplement raw GitPython calls in API endpoints or CLI commands

### Web API Routes

- Core routes: `/api/v1/search`, `/api/v1/analysis`, `/api/v1/auth`
- All routes in `githound/web/apis/` should return schema objects from `githound/web/models/api_models.py` or `githound/schemas.py`
- Apply rate limiting with `limiter.limit()` decorators from `githound/web/middleware/rate_limiting.py`
- Use `get_request_id()` from `githound/web/utils/validation.py` for request tracking
- Redis URL configurable via `REDIS_URL` environment variable
- **Note**: Repository management (clone/init), webhooks, and health checks have been removed to focus on core analysis

### CLI Output

- Use `SafeConsole` and `print_results_*` helpers for Windows/Unicode compatibility
- Rich formatting for tables and output

### MCP Server

- Entry point: `githound/mcp_server.py` (compatibility shim)
- Core implementation: `githound/mcp/server.py`
- 29+ MCP tools, 7 MCP resources, 3 MCP prompts (see README for full list)
- FastMCP 2.x with optional authentication (JWT, OAuth, Permit.io, Eunomia)
- Handle `ImportError` gracefully if MCP dependencies missing

### Exports

- Use `ExportManager` from `githound/utils/export.py`
- Supported formats: JSON, YAML, CSV (Excel optional via pandas/openpyxl)
- Schema-based exports for consistency

## Testing Guidelines

### Test Categories (use pytest markers)

- `@pytest.mark.unit`: Fast, isolated tests
- `@pytest.mark.integration`: Integration tests with external dependencies
- `@pytest.mark.performance`: Performance/benchmark tests
- `@pytest.mark.mcp`: MCP server functionality
- `@pytest.mark.api`: Web API tests
- `@pytest.mark.cli`: CLI tests

### Running Tests

```bash
# Fast feedback loop
pytest -m "unit and not slow" -v

# Specific module
pytest tests/test_cli.py -v

# With coverage
pytest --cov=githound --cov-report=html
```

### Test Structure

- Follow Arrange-Act-Assert (AAA) pattern
- Use descriptive test names: `test_feature_with_condition_returns_expected_result()`
- Mock external dependencies (file systems, network, Git operations when appropriate)
- Fixtures in `tests/conftest.py` and `tests/fixtures/`

### Coverage Requirements

- Overall: 85% minimum (enforced by CI)
- New code: 90% minimum
- Core modules (CLI, search engine, Git ops): 95%

## Adding Features

### New Search Capability

1. Create searcher in `githound/search_engine/*_searcher.py` based on `BaseSearcher`
2. Register in orchestrator factory (`githound/search_engine/factory.py`)
3. Add query parameters to `SearchQuery` model if needed
4. Add tests in `tests/search_engine/`

### New API Endpoint

1. Create router in `githound/web/apis/`
2. Define models in `githound/web/models/api_models.py`
3. Include router in `githound/web/main.py`
4. Add rate limiting decorator
5. Add tests in `tests/web/` or `tests/integration/`
6. Update OpenAPI documentation (automatic from FastAPI)

### New CLI Command

1. Add command to `githound/cli.py` using Typer decorators
2. Use Rich for formatted output
3. Handle errors gracefully with try/except
4. Add tests in `tests/test_cli.py`

## Performance Considerations

- Search engine optimized for repos with up to 10,000 commits
- Caching enabled by default (1-hour TTL)
- Parallel execution: 4 workers default (configurable via `SearchEngineConfig`)
- Large files (>10MB) skipped by default
- Memory usage monitored in metrics
- Use `max_results` parameter to limit result sets

## Windows-Specific Notes

- This repository is developed on Windows (git bash/PowerShell compatible)
- Use `.venv\Scripts\activate` (not `source .venv/bin/activate`)
- Makefile works in git bash or with make for Windows
- Paths use `Path` from pathlib for cross-platform compatibility
- Unicode handling in CLI via Rich's `SafeConsole`

## Configuration

- MCP server: Configure via `githound/mcp/config.py` or environment variables
- Web API: Configure via environment variables (see `githound/web/main.py`)
- Search engine: Configure via `SearchEngineConfig` object
- Rate limiting: Redis backend configurable via `REDIS_URL`

## Documentation

- Main docs in `docs/` (MkDocs format)
- API docs auto-generated from code (FastAPI OpenAPI)
- Examples in `examples/` directory
- Validate docs: `make docs-validate` or `python scripts/validate_all_docs.py`

## Git Workflow

- Main branch: `master`
- Feature branch (for PRs): `feature/enhanced-search-engine`
- Always run `make check` before committing
- CI enforces: type checking, linting, tests, coverage

## Important Files to Review

- `githound/__init__.py`: Main GitHound API class
- `githound/search_engine/README.md`: Search engine architecture details
- `tests/TESTING_GUIDELINES.md`: Comprehensive testing standards
- `.github/copilot-instructions.md`: Additional AI agent guidelines
- `pyproject.toml`: All tool configurations (mypy, ruff, pytest, coverage)

## Known Constraints

- Strict mypy typing: no `Any` types without justification
- Pydantic v2 required (v1 not supported)
- Python 3.11+ required (uses `Self` type, etc.)
- FastMCP 2.11.0+ for MCP functionality
- ripgrep optional but recommended for fast content search
