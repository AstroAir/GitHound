---
type: "manual"
---

## 1. Mission

Execute a comprehensive test suite analysis and remediation cycle for the GitHound project. Identify all test failures, errors, and warnings, then systematically resolve each issue through root cause analysis and targeted fixes. Ensure all tests pass successfully while maintaining existing functionality and code quality standards.

### Specific Requirements

**Phase 1: Test Discovery and Environment Setup**

1. Examine `pyproject.toml`, `pytest.ini`, `tox.ini`, and any test configuration files to identify:
   - The testing framework in use (pytest expected based on project context)
   - Test markers and categories (unit, integration, performance, mcp, api, cli)
   - Coverage requirements and thresholds
   - Test execution commands and options
2. Verify test dependencies are installed (check `pyproject.toml` dependency groups: test, dev)
3. Identify the complete test directory structure under `tests/`

**Phase 2: Initial Test Execution**

1. Run the full test suite using the project's standard test command (likely `pytest` or `make test-all`)
2. Capture complete output including:
   - All failures with full tracebacks
   - All errors with context
   - All warnings
   - Coverage metrics if applicable
   - Execution time and performance data

**Phase 3: Issue Analysis and Categorization**
For each failure/error discovered:

1. Classify the issue type (assertion failure, import error, type error, runtime exception, etc.)
2. Identify the affected test file and specific test function
3. Determine the root cause by:
   - Examining the test code and what it's testing
   - Reviewing the implementation code being tested
   - Checking for recent changes that may have introduced regressions
   - Verifying dependencies and imports are correct
4. Assess impact scope (isolated to one test, affects multiple tests, indicates systemic issue)

**Phase 4: Systematic Remediation**
For each identified issue:

1. **Before making any fix:**
   - Use codebase-retrieval to understand the full context of the code being modified
   - Identify ALL downstream callers and dependencies that might be affected
   - Verify the intended behavior from existing documentation or related tests
2. **Implement the fix:**
   - Make minimal, targeted changes that address the root cause
   - Ensure fixes align with project conventions (SOLID principles, type safety, error handling per CLAUDE.md)
   - Update any affected downstream code (callers, implementations, type definitions)
   - Do NOT disable or skip failing tests unless explicitly requested
3. **Verify the fix:**
   - Re-run the specific test(s) that were failing
   - Run related tests in the same test file/module
   - Check that no new failures were introduced
4. Document the fix internally for the final summary

**Phase 5: Regression Prevention**

1. After all individual fixes, run the complete test suite again to ensure:
   - All previously failing tests now pass
   - No new failures were introduced by the fixes
   - Coverage thresholds are maintained (85% minimum per CLAUDE.md)
2. If new failures appear, return to Phase 3 for those issues

**Phase 6: Final Validation and Reporting**

1. Confirm all tests pass with no errors or failures
2. Verify code quality standards are maintained (run type checking with mypy if tests modified type signatures)
3. Provide a comprehensive summary including:
   - Total number of issues found and fixed
   - Categorization of issue types
   - Specific changes made for each fix (file paths, functions/classes modified)
   - Any patterns or systemic issues discovered
   - Final test execution results (pass count, coverage %, execution time)

### Constraints and Guidelines

- **DO NOT** create new test files unless absolutely necessary to fix an issue
- **DO NOT** skip or disable tests to make them "pass" - fix the underlying issue
- **DO NOT** make changes beyond what's needed to fix test failures
- **DO** use parallel tool calls for efficiency when gathering information
- **DO** maintain strict adherence to the project's type safety requirements (mypy strict mode)
- **DO** preserve existing code style and conventions
- **DO** ask for clarification via ClarificationProtocol if you encounter genuinely ambiguous situations that cannot be resolved through available tools

### Success Criteria

- All tests in the test suite execute successfully (exit code 0)
- No test failures, errors, or critical warnings
- Code coverage meets or exceeds project thresholds (85% minimum)
- All fixes are minimal, targeted, and maintain code quality
- Type checking passes (mypy) if any type-related changes were made
