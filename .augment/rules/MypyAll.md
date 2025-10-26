---
type: "manual"
---

## 1. Mission

Execute comprehensive mypy type checking across the entire GitHound codebase and systematically resolve all discovered type-related issues to achieve 100% mypy compliance while maintaining existing functionality and adhering to the project's strict typing standards as defined in `pyproject.toml`.

### Context and Requirements

- The project enforces strict mypy typing with 100% coverage (as documented in CLAUDE.md)
- Configuration is in `pyproject.toml` under `[tool.mypy]`
- The project uses Python 3.11+ with modern typing features (including `Self` type)
- Pydantic v2 is used throughout; no `Any` types without justification
- All fixes must maintain compatibility with existing code and tests

### Execution Steps

**Phase 1: Initial Assessment**

1. Run `mypy githound --show-error-codes` to generate a complete baseline report of all type checking errors and warnings
2. Capture and analyze the full output, categorizing issues by:
   - Missing type annotations
   - Incorrect or incompatible type annotations
   - Import errors for typing modules
   - Configuration-related issues
   - Any other mypy-specific errors

**Phase 2: Systematic Resolution**
For each identified issue, in order of severity:

1. Locate the exact file and line number where the issue occurs
2. Use codebase-retrieval to understand the context and usage patterns of the affected code
3. Determine the appropriate fix:
   - Add precise type annotations (parameters, return types, class attributes)
   - Correct incompatible type annotations based on actual usage
   - Add necessary typing imports (`from typing import ...`)
   - Use appropriate type constructs (`Optional`, `Union`, `Literal`, `Protocol`, etc.)
   - Apply `# type: ignore[error-code]` ONLY when absolutely necessary with clear justification
4. Implement the fix using str-replace-editor
5. Verify downstream impacts using codebase-retrieval to find all callers/usages

**Phase 3: Verification**

1. Re-run `mypy githound --show-error-codes` after all fixes to confirm zero errors
2. Run the test suite with `pytest -m "unit and not slow" -v` to ensure no functionality is broken
3. If any tests fail, investigate and resolve the root cause
4. Perform a final mypy check to confirm complete compliance

**Phase 4: Configuration Review (if needed)**

- Only modify `pyproject.toml` mypy configuration if absolutely necessary
- Document any configuration changes with clear rationale
- Ensure changes align with project's strict typing requirements

### Success Criteria

- Zero mypy errors when running `mypy githound --show-error-codes`
- All existing tests pass
- No use of `Any` type without documented justification
- All type annotations follow Python typing best practices and project conventions
- Code remains functionally equivalent to pre-fix state
