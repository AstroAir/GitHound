# Repository Guidelines

## Project Structure & Modules
- Source: `githound/` (core), with key subpackages: `search_engine/`, `mcp/`, `web/`, `utils/`.
- Entry points: `githound/cli.py` (Typer CLI), `githound/mcp_server.py` (MCP), `githound/web/api.py` (FastAPI).
- Tests: `tests/` (unit, integration, performance) with markers; fixtures in `tests/fixtures/`.
- Docs & examples: `docs/`, `examples/`; helper scripts in `scripts/`.

## Build, Test, and Development
- Install dev deps: `pip install -e ".[dev,test,docs,build]"` or `make install-dev`.
- Format/lint/types: `make quality` (runs `black`, `isort`, `ruff`, `mypy`).
- Tests: `make test` (unit), `make test-all` (full), coverage: `make test-cov`.
- Docs: `make docs` (build) or `make docs-serve` (local server).
- Package: `make build`; clean: `make clean`.
- Pre-commit: `pre-commit install` then commit; CI mirrors these checks.

## Coding Style & Naming
- Python 3.11+. Format with Black (line length 100) and isort (profile=black). Lint with Ruff.
- Type checking with mypy (pydantic plugin); add/maintain type hints.
- Naming: modules/files `snake_case.py`; classes `PascalCase`; functions/vars `snake_case`; constants `UPPER_CASE`.
- Example: `githound/search_engine/commit_searcher.py`, test file `tests/search_engine/test_commit_searcher.py`.

## Testing Guidelines
- Framework: pytest. Common markers: `unit`, `integration`, `performance`, `api`, `mcp`.
- Run fast suite: `pytest -m "unit and not slow" -v`.
- Integration/perf may require services (e.g., Redis). Start with `docker compose up -d redis` or use the provided `docker-compose.yml`.
- Coverage: aim ≥90%; CI enforces ≥85% (`--cov=githound`). Place tests under `tests/<area>/test_*.py`.

## Commit & Pull Requests
- Commits: clear, imperative subjects. Conventional prefixes (e.g., `feat:`, `fix:`, `docs:`, `ci:`) are encouraged but not required. Reference issues (e.g., `Fixes #123`).
- Branch names: `feat/<scope>`, `fix/<scope>`, `chore/<scope>`.
- PRs: use the template; include a summary, linked issues, test evidence, and note perf/security impacts. All checks must pass: `ruff`, `black --check`, `mypy`, and tests.

## Security & Configuration
- Never commit secrets. Use `.env.example` as a guide; set env like `REDIS_URL`, `GITHOUND_*` locally or in CI.
- For local services and APIs, see `docker-compose.yml` and `docker/` configs. Default web starts at `http://localhost:8000`.

## Agent Notes
- Keep changes focused; match existing patterns and directory layout.
- Prefer `make check` before opening a PR. Update docs/examples when behavior changes.
