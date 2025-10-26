---
type: "always_apply"
---

Conduct a comprehensive test coverage audit of the GitHound codebase to identify gaps between source modules and their corresponding test files. This is a **read-only analysis task** - do not create, modify, or delete any files.

## Audit Scope

Systematically examine **every** Python module (`.py` file) in the following directories:

- `githound/` (root level: `__init__.py`, `cli.py`, `models.py`, `schemas.py`, `git_handler.py`, `git_blame.py`, `git_diff.py`, `searcher.py`, `mcp_server.py`)
- `githound/search_engine/` (all `.py` files including subdirectories)
- `githound/web/` (all `.py` files including `main.py`, subdirectories: `apis/`, `middleware/`, `models/`, `services/`)
- `githound/mcp/` (all `.py` files including subdirectories: `tools/`, `auth/`)
- `githound/utils/` (all `.py` files)

## Audit Methodology

For each source module discovered:

1. **Identify the module's full path** relative to the repository root (e.g., `githound/search_engine/commit_searcher.py`)

2. **Determine the expected test file location** following Python testing conventions:
   - Source: `githound/path/to/module.py` → Expected test: `tests/path/to/test_module.py` OR `tests/test_module.py`
   - Account for alternative test organization patterns (e.g., `tests/search_engine/`, `tests/web/`, `tests/integration/`)

3. **Verify test file existence and assess coverage quality**:
   - Does a corresponding test file exist?
   - If yes, examine the test file to assess coverage depth (number of test functions, test markers, comprehensiveness)
   - Note any test files that appear minimal or placeholder-only

4. **Cross-reference with project standards**:
   - Coverage requirements from `CLAUDE.md`: 85% minimum overall, 90% for new code, 95% for core modules (CLI, search engine, Git operations)
   - Testing guidelines from `tests/TESTING_GUIDELINES.md`
   - Pytest markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.performance`, `@pytest.mark.mcp`, `@pytest.mark.api`, `@pytest.mark.cli`

## Execution Requirements

- **Completeness**: Examine EVERY `.py` file in the specified directories without exception (excluding `__pycache__`, `.pyc` files)
- **Autonomy**: Work through all modules systematically without requesting user confirmation to continue
- **Tool usage**: Use `view` to list directory contents and examine files; use `codebase-retrieval` to find test files and understand testing patterns
- **Sequential processing**: Process modules in a logical order (e.g., alphabetically by directory, then by filename) to ensure nothing is missed

## Output Format

Provide a structured markdown report with the following sections:

### 1. Executive Summary

- Total number of source modules audited
- Total number of test files found
- Overall coverage assessment (percentage of modules with tests)
- Key findings and critical gaps

### 2. Modules with Complete Test Coverage

List modules that have comprehensive test files with good coverage indicators (multiple test functions, various test markers, thorough testing)

Format:

- `githound/module.py` → `tests/test_module.py` ✅ (X test functions, markers: unit, integration)

### 3. Modules with Partial Test Coverage

List modules that have test files but appear to have incomplete or minimal coverage

Format:

- `githound/module.py` → `tests/test_module.py` ⚠️ (Only Y test functions, may need expansion)

### 4. Modules Missing Tests Entirely

List modules that have NO corresponding test file

Format:

- `githound/module.py` ❌ (No test file found)

### 5. Special Cases and Notes

- Test files that don't map to specific source modules (e.g., `tests/conftest.py`, integration tests)
- Modules that may not require tests (e.g., `__init__.py` files that only contain imports)
- Any unusual testing patterns or organizational structures discovered

### 6. Recommendations

Based on coverage requirements (85% overall, 90% new code, 95% core modules), prioritize which missing tests should be addressed first.

## Important Constraints

- **Read-only**: Do NOT create, modify, or delete any files
- **No test implementation**: Only audit and report; do not write or suggest specific test code
- **No assumptions**: If a test file's coverage quality is unclear from examination, note it as "requires manual review" rather than making assumptions
