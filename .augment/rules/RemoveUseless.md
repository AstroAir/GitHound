---
type: "manual"
---

Conduct a comprehensive audit of the GitHound project directory (d:\Project\GitHound) to identify and remove unnecessary files while preserving all essential project components. Follow this systematic approach:

**Phase 1: Discovery and Analysis**

1. Scan the entire project directory structure to identify potential candidates for removal
2. For each candidate file, use the `view` tool to examine its contents and determine its purpose
3. Categorize findings into the following groups:

**Files to Target for Removal:**

- **Procedural/temporary documentation**: Draft documents, meeting notes, planning documents, brainstorming files, or process documentation that served a temporary purpose and is no longer relevant to the project's current state
- **Duplicate documentation**: Multiple versions of the same document, outdated copies, or redundant markdown files
- **Backup files**: Files with extensions like .bak, .tmp, .old, or ending with ~ (tilde)
- **Editor artifacts**: .DS_Store (macOS), Thumbs.db (Windows), .swp, .swo (Vim), .idea/ contents (if not gitignored)
- **Build artifacts**: Compiled files, distribution packages, or generated outputs that should not be version-controlled (e.g., **pycache**/, *.pyc, dist/, build/,*.egg-info/)
- **Cache and temporary outputs**: Log files, temporary test outputs, or cached data files
- **Obsolete code**: Deprecated or replaced source files that are no longer referenced or used

**Files to PRESERVE (Do Not Remove):**

- Core documentation: README.md, CLAUDE.md, TESTING_GUIDELINES.md, any files in docs/ directory, CONTRIBUTING.md, LICENSE, CHANGELOG.md
- Configuration files: pyproject.toml, .gitignore, .github/ directory contents, setup.py, setup.cfg, tox.ini, .pre-commit-config.yaml
- Source code: All files in githound/ directory and its subdirectories
- Tests: All files in tests/ directory and its subdirectories
- Examples: All files in examples/ directory
- CI/CD files: GitHub Actions workflows, deployment scripts
- Package metadata: MANIFEST.in, requirements files, poetry.lock, Pipfile.lock

**Phase 2: Reporting**
Present a detailed report with:

- Complete list of files identified for removal, organized by category
- For each file: full path, file size, and a brief explanation of why it's considered unnecessary
- Total number of files and estimated disk space to be reclaimed
- Any files you're uncertain about, with reasoning for why they might or might not be necessary

**Phase 3: Confirmation and Execution**

- Wait for explicit user confirmation before deleting any files
- Upon confirmation, use the `remove-files` tool to delete the approved files
- Provide a summary of completed deletions

**Special Considerations:**

- If a file's purpose is ambiguous, err on the side of caution and flag it for user review rather than recommending deletion
- Check if files are referenced in .gitignore - if they are ignored but still present in the repository, investigate why
- Look for patterns that suggest a file is generated (e.g., "generated", "auto", "temp" in filename or path)
- Consider the last modification date context if available through git history

Begin with Phase 1: Discovery and Analysis.
