---
type: "manual"
---

Conduct a systematic, exhaustive code quality audit of the GitHound codebase to verify implementation completeness and production-readiness. This audit must be performed methodically using the following structured approach:

## Phase 1: Component Discovery and Cataloging

1. **Identify the full scope of components** by examining:
   - All Python modules in `githound/` directory and subdirectories
   - All classes, functions, and methods within each module
   - All API endpoints in `githound/web/apis/`
   - All MCP tools in `githound/mcp/tools/`
   - All CLI commands in `githound/cli.py`
   - All search engine components in `githound/search_engine/`

2. **Create a structured inventory** listing:
   - Module path (e.g., `githound/search_engine/commit_searcher.py`)
   - Component type (module, class, function, method, endpoint, tool)
   - Component name and signature
   - Approximate line number range

## Phase 2: Individual Component Verification

For **each component** identified in Phase 1, perform the following checks and document findings:

### 2.1 Implementation Completeness Checks

- **Placeholder Detection**: Verify the component does NOT contain:
  - Functions with only `pass` statements
  - Functions returning only `None` without logic
  - Stub implementations with comments like "# TODO: implement this"
  - Ellipsis (`...`) as the only body content
  - Raise `NotImplementedError` without valid reason

- **TODO/FIXME Markers**: Search for and flag:
  - `# TODO` comments indicating incomplete work
  - `# FIXME` comments indicating known issues
  - `# HACK` or `# XXX` comments indicating temporary solutions
  - `# NOTE:` comments suggesting future changes needed

- **Mock/Simplified Implementations**: Identify:
  - Hardcoded return values that should be dynamic
  - Simplified logic that bypasses actual business requirements
  - Test/mock code in production modules
  - Commented-out code blocks that suggest incomplete refactoring

### 2.2 Production-Readiness Checks

- **Error Handling**: Verify:
  - Try-except blocks have meaningful exception handling (not just `pass` or generic logging)
  - Appropriate exception types are caught (not bare `except:`)
  - Error messages are informative and actionable
  - Critical operations have proper error recovery or cleanup

- **Edge Case Handling**: Confirm:
  - Null/None value checks where appropriate
  - Empty collection handling (empty lists, dicts, strings)
  - Boundary condition validation (min/max values, array bounds)
  - Type validation for inputs when necessary

- **Documentation**: Check:
  - Docstrings are present for public functions/classes
  - Complex logic has explanatory comments
  - Function signatures match their documented behavior

### 2.3 Reporting Format for Each Component

Output findings for each component using this exact format:

```
---
Component: {full.module.path.ComponentName}
Location: {file_path}:{line_start}-{line_end}
Type: {class|function|method|endpoint|tool}
Status: {COMPLETE|INCOMPLETE|NEEDS_REVIEW}

Findings:
{If COMPLETE: "✓ Implementation is production-ready with no placeholders, TODOs, or incomplete logic."}
{If INCOMPLETE or NEEDS_REVIEW: Bulleted list of specific issues:}
  - Issue type: Specific description with line number if applicable
  - Issue type: Specific description with line number if applicable

{If INCOMPLETE: Recommended actions or next steps}
---
```

## Phase 3: Comprehensive Summary Report

After examining ALL components, provide a final summary with:

1. **Audit Statistics**:
   - Total components examined: {count}
   - Complete (production-ready): {count} ({percentage}%)
   - Incomplete (has issues): {count} ({percentage}%)
   - Needs review (uncertain): {count} ({percentage}%)

2. **Critical Issues** (if any):
   - List components with placeholders or TODOs that block production deployment
   - Prioritize by severity and impact

3. **Component Breakdown by Category**:
   - Core modules: {complete/total}
   - Search engine: {complete/total}
   - Web API: {complete/total}
   - MCP server: {complete/total}
   - CLI: {complete/total}
   - Utilities: {complete/total}

4. **Recommendations**:
   - Immediate action items (must-fix before production)
   - Medium-priority improvements
   - Optional enhancements

## Execution Requirements

- **Use codebase-retrieval tool** extensively to discover components and examine implementations
- **Use view tool with search_query_regex** to find TODO/FIXME markers, placeholder patterns, and incomplete implementations
- **Do NOT skip any components** - every discovered component must be individually verified and reported
- **Do NOT summarize multiple components together** - each component gets its own verification entry
- **Be thorough and systematic** - work through the codebase directory by directory, file by file
- **Provide evidence** - when flagging issues, include specific line numbers or code snippets as proof

Begin the audit immediately and work through all phases sequentially.
