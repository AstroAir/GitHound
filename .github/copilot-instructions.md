# GitHound – AI agent working guide

This repo provides advanced Git analysis via three faces: a Typer CLI (`githound/cli.py`), a FastAPI web/API app (`githound/web/main.py`), and an MCP server wrapper (`githound/mcp_server.py`). Use these notes to navigate quickly and make safe changes.

## Architecture and data flow

- Core packages live under `githound/`:
  - `search_engine/` – modular search system. Factory: `create_search_orchestrator()`; orchestrates searchers (content/author/message/date/file/fuzzy, plus analysis modes). See `githound/search_engine/README.md`.
  - `utils/` – helpers (export, progress, etc.).
  - `web/` – FastAPI application. App is defined in `githound/web/main.py`; server helpers in `githound/web/server.py`; routers under `githound/web/apis/`.
  - `mcp/` – FastMCP 2.x integration exposed via `githound/mcp_server.py` (a compatibility shim re-exporting the modular server and direct wrapper tools).
  - Git wrappers: `git_handler.py`, `git_diff.py`, `git_blame.py` consolidate GitPython operations.
- Typical flow: GitPython Repo → Search Orchestrator → `models.SearchResult`/metrics → export or API/CLI output.
- Content search uses ripgrep if available (see `githound/searcher.py` and dependency `ripgrepy`); handle the case where `rg` is missing gracefully.

## Key contracts (Pydantic v2 models)

- Queries: `githound.models.SearchQuery` (supports combined criteria, fuzzy, limits, caching, parallelism).
- Results: `githound.models.SearchResult`, `SearchMetrics` for perf, and richer API schemas in `githound/schemas.py` for REST responses/exports.
- Engine configuration: `githound.models.SearchEngineConfig` governs workers, caching (memory/Redis), ranking, limits.

## Interfaces and entry points

- CLI: command group `githound` → see `githound/cli.py`. Uses Rich for tables and multiple output formats. Example: `githound search --repo-path . --content "function"`.
- Web/API: FastAPI app at `githound.web.main:app` (preferred). Run with uvicorn. Routers: `search_api.py`, `analysis_api.py`, `repository_api.py`, `integration_api.py`. Static assets served from `githound/web/static` at `/static`.
- MCP: `githound mcp-server` or `python -m githound.mcp_server`. Exposes tools/resources/prompts described in README. The shim guards imports; if MCP deps are missing you must handle ImportError paths.

## Build, test, and quality (Windows PowerShell examples)

- Install (dev):
  - `pip install -e . --dependency-groups dev,test,docs,build`
  - Or `make install-dev` (if Make available)
- Run checks:
  - `make quality` (black, isort, ruff, mypy)
  - `pytest -m "unit and not slow" -v` for fast suite; full: `pytest -v`
  - Coverage enforced ≥85% (see `[tool.pytest.ini_options]` in `pyproject.toml`)
- Web/API dev:
  - `uvicorn githound.web.main:app --reload --port 8000`
  - Or `python -m githound.web.server dev`
- MCP server:
  - `githound mcp-server`; options: `--host`, `--port`, `--log-level`.

## Project conventions and patterns

- Python 3.11+, formatting with Black (line length 100), lint with Ruff, strict mypy (+ pydantic plugin). Follow naming rules in `AGENTS.md`.
- Prefer the orchestrator factory: `from githound.search_engine import create_search_orchestrator` then `await orchestrator.search(repo, SearchQuery(...))`.
- Ranking/caching/parallelism are opt-in via `SearchQuery` and `SearchEngineConfig`. Respect defaults; avoid breaking performance guarantees (e.g., keep worker counts reasonable, skip >10MB files unless explicitly requested).
- Rate limiting in web via SlowAPI (`githound/web/middleware`); Redis URL configurable via env (`REDIS_URL`).
- Exports use `githound.utils.export.ExportManager` and schemas in `githound/schemas.py` (JSON/YAML/CSV; Excel optional via pandas/openpyxl).

## Integration points and cross-component rules

- Git access via `git_handler.get_repository`, `process_commit`, `walk_history`. Don’t reimplement raw Git calls in endpoints; route through handlers/searchers.
- Web routes should return schema objects from `githound/web/models/api_models.py` or `githound/schemas.py`. Use `limiter.limit` decorators and add request IDs via `githound/web/utils/validation.get_request_id`.
- CLI should print via `SafeConsole` and the provided `print_results_*` helpers to preserve Windows/Unicode compatibility.

## Adding features safely

- New search dimension: implement a searcher in `githound/search_engine/*_searcher.py` based on `BaseSearcher`, then register in the orchestrator factory.
- API endpoint: add a router under `githound/web/apis/`, include it in `main.py`, and document tags. Add tests under `tests/api` and mark with `@pytest.mark.api`.
- Keep public APIs stable; add types and unit tests; run `make check` before PRs. CI mirrors Make targets.

Questions or gaps? If any of the above is unclear (e.g., MCP tool list vs current code, or the web entry import), ask which interface the team prefers and I’ll align the docs/commands accordingly.
