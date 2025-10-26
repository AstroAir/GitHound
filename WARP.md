# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Commands you’ll use often

- Install (editable) with extras
```bash path=null start=null
pip install -e . --dependency-groups dev,test,docs,build
# or with uv
uv pip install -e . --dependency-groups dev,test,docs,build
# or via Make
make install-dev
```

- Lint, format, type-check
```bash path=null start=null
make quality                     # black + isort + ruff + mypy + docs quick-validate
make lint                        # ruff
make lint-fix                    # ruff --fix
make format                      # black + isort
make type-check                  # mypy (strict per pyproject)
```

- Tests (pytest configured in pyproject; coverage threshold 85%)
```bash path=null start=null
pytest                           # run all tests
pytest -m "unit and not slow" -v # fast feedback
pytest -m integration -v         # integration tests only
pytest --cov=githound --cov-report=term-missing --cov-report=html
# Single file / single test
pytest tests/test_cli.py -q
pytest tests/test_cli.py::test_search_command -q
# Parallel (requires pytest-xdist)
pytest -n auto -v
```

- Frontend (web static assets)
```bash path=null start=null
cd githound/web/static
npm install
npm test                         # jest unit tests
npm run lint && npm run format:check
```

- Web UI E2E (Playwright harness)
```bash path=null start=null
make test-web-install            # install Python + Node E2E deps
make test-web                    # run all Playwright suites via run_tests.py
# or directly
cd githound/web/tests && npm install && npx playwright test
```

- Run the web/API server
```bash path=null start=null
uvicorn githound.web.main:app --reload --port 8000
# API docs: http://localhost:8000/docs, ReDoc: /redoc
```

- Run the MCP server
```bash path=null start=null
githound mcp-server
# options: --host 0.0.0.0 --port 3000 --log-level DEBUG
# alt: python -m githound.mcp_server
```

- Build artifacts
```bash path=null start=null
make build                       # sdist + wheel via python -m build
make clean                       # remove build/test caches
```

- Docs
```bash path=null start=null
make docs                        # mkdocs build
make docs-serve                  # mkdocs serve (local preview)
make docs-validate-quick        # fast validator used in CI quality target
```

- Pre-commit
```bash path=null start=null
pre-commit install
pre-commit run --all-files
```

## High-level architecture (big picture)

- Core packages (under `githound/`)
  - CLI: Typer-based entry at `githound/cli.py` (exposed as `githound` via project.scripts)
  - Web/API: FastAPI app at `githound/web/main.py` with modular routers in `githound/web/apis/`, services, middleware (rate limiting), models, and static assets in `githound/web/static/` (served at `/static`). WebSocket support for live progress.
  - MCP: FastMCP 2.x integration; entry `githound/mcp_server.py` wraps `githound/mcp/server.py` tools/resources/prompts for Model Context Protocol clients.
  - Search engine: Modular orchestrator in `githound/search_engine/` with base classes, multiple searchers (commit, author, message, date, path, type, content, fuzzy), optional ripgrep acceleration, result ranking, caching, and parallelism.
  - Git operations: Consolidated helpers in `git_handler.py`, `git_diff.py`, `git_blame.py` built on GitPython.
  - Utilities: `githound/utils/` provides `ExportManager` (JSON/YAML/CSV/Excel/text, streaming) and `ProgressManager` (multi-task progress, cancellation, rich display).

- Data flow
  - GitPython Repo → Search Orchestrator → Searchers (parallel) → Ranking/Caching → `SearchResult`/metrics → CLI/Web/MCP output and export utilities.

- Testing and quality
  - Pytest configured in `pyproject.toml` with markers: unit, integration, performance, api, mcp, cli, search. Coverage collected (term/html/xml) with `--cov-fail-under=85` enforced in CI.
  - Type checking is strict via mypy (with pydantic plugin). Ruff handles linting; Black + isort for formatting/imports. Pre-commit hooks mirror these checks.
  - Web UI tests use Playwright harness under `githound/web/tests/` with npm scripts; Python wrapper `githound/web/tests/run_tests.py` and Make targets are provided.

- Frontend
  - `githound/web/static/` is a lightweight ES module setup tested with Jest (no heavy bundling). Quality scripts: `npm run quality`, `quality:fix`, and jest coverage.

## Cross-component rules (from project AI guidelines)

- Always construct search via the factory/orchestrator
```python path=null start=null
from githound.search_engine import create_search_orchestrator
orchestrator = create_search_orchestrator()
```
- Route Git access through handlers in `git_handler.py` rather than ad-hoc GitPython calls.
- Web routes should return schema objects from `githound/web/models/api_models.py` or `githound/schemas.py`; apply rate limiting decorators where appropriate.
- Prefer `ExportManager` for output formatting and file exports; avoid duplicating serialization logic.

## CI signals to mirror locally

- GitHub Actions run: formatting (black/isort), lint (ruff), mypy, pytest (unit + integration), coverage report, docs validation, CodeQL/Semgrep, package build checks, and Playwright where applicable. Use `make check` (quality + unit tests) or `make ci` (quality + all tests + build) before opening PRs.
