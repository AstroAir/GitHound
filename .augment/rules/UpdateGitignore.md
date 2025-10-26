---
type: "manual"
---

Update the `.gitignore` file located at the repository root (`.gitignore`) to properly exclude files and directories that should not be tracked in version control for this GitHound Python project. Follow these steps sequentially:

1. **Examine the current project structure**: Use the `view` tool to explore the repository directory structure (at least 2 levels deep) to identify what files, directories, and artifacts currently exist in the project.

2. **Review the existing .gitignore**: Use the `view` tool to read the current `.gitignore` file and understand what patterns are already being ignored.

3. **Analyze the project type and dependencies**:
   - Check `pyproject.toml` to understand the project's build system, dependencies, and tooling (e.g., pytest, mypy, ruff, mkdocs)
   - Identify the project as a Python package with CLI, web API, and MCP server components
   - Note any virtual environment directories (`.venv`, `venv`, etc.)

4. **Identify files and directories to ignore**: Based on the project analysis, determine what should be excluded, including but not limited to:
   - **Python-specific**: `__pycache__/`, `*.py[cod]`, `*$py.class`, `*.so`, `.Python`, `build/`, `develop-eggs/`, `dist/`, `downloads/`, `eggs/`, `.eggs/`, `lib/`, `lib64/`, `parts/`, `sdist/`, `var/`, `wheels/`, `*.egg-info/`, `.installed.cfg`, `*.egg`, `pip-log.txt`, `pip-delete-this-directory.txt`
   - **Virtual environments**: `.venv/`, `venv/`, `ENV/`, `env/`
   - **Testing and coverage**: `.pytest_cache/`, `.coverage`, `htmlcov/`, `.tox/`, `.nox/`, `coverage.xml`, `*.cover`
   - **Type checking**: `.mypy_cache/`, `.dmypy.json`, `dmypy.json`, `.pytype/`
   - **Documentation**: `docs/_build/`, `site/` (MkDocs output)
   - **IDE/Editor files**: `.vscode/`, `.idea/`, `*.swp`, `*.swo`, `*~`, `.DS_Store`
   - **OS-specific**: `Thumbs.db`, `desktop.ini` (Windows), `.DS_Store`, `.AppleDouble`, `.LSOverride` (macOS)
   - **Logs and temporary files**: `*.log`, `*.tmp`, `*.temp`, `.cache/`
   - **Environment and secrets**: `.env`, `.env.local`, `*.pem`, `*.key`
   - **Build tools**: `.ruff_cache/`, `.pdm-build/`, `.pdm-python`

5. **Update the .gitignore file**: Use the `str-replace-editor` tool to modify the `.gitignore` file with well-organized sections (with comments) for each category of ignored files. Ensure patterns are:
   - Specific enough to avoid ignoring important project files (e.g., don't use overly broad patterns like `*.py`)
   - Properly formatted (one pattern per line, use `#` for comments)
   - Organized logically with section headers for readability

6. **Verify the changes**: After updating, use the `launch-process` tool to run `git status --ignored` to confirm that appropriate files are being ignored and no critical project files are accidentally excluded.

**Goal**: Create a comprehensive, well-organized `.gitignore` file that prevents build artifacts, dependencies, IDE configurations, OS files, and temporary files from being committed, while ensuring all source code, configuration files, tests, and documentation remain properly tracked in version control.
