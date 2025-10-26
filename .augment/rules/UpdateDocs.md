---
type: "manual"
---

Conduct a comprehensive audit and update of all code examples in the GitHound project documentation and example files. For each example:

1. **Locate all example files and documentation** containing code samples:
   - Files in the `examples/` directory
   - Code examples in `docs/` directory (MkDocs documentation)
   - Code snippets in README.md and other markdown files
   - Docstrings with example code in Python modules

2. **Verify each example against the current codebase**:
   - Check that all imports match the current module structure
   - Verify that class names, method signatures, and parameters are up-to-date
   - Ensure API endpoints and routes reflect the current FastAPI implementation
   - Confirm that CLI commands match the current Typer interface
   - Validate that Pydantic models (v2) are used correctly with current field definitions

3. **Ensure complete coverage**:
   - Every major feature should have at least one working example
   - Examples should cover: CLI usage, Web API usage, MCP server usage, and programmatic Python API usage
   - Include examples for search operations, analysis, blame, diff, and export functionality

4. **Test each example for correctness**:
   - Verify that code examples are syntactically correct
   - Check that examples would execute successfully with the current codebase
   - Ensure examples follow current best practices and conventions from CLAUDE.md

5. **Maintain one-to-one correspondence**:
   - Each documented feature should have a corresponding working example
   - Each example should clearly map to specific functionality in the codebase
   - Remove any outdated examples that reference deprecated features

6. **Check systematically, one by one**:
   - Process each example file individually
   - Document which examples were verified, updated, or flagged for issues
   - Provide a summary report of all changes made

Focus on accuracy and completeness. Do not skip any examples. Ensure all code samples are executable and reflect the current state of the GitHound codebase.
