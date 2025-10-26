---
type: "manual"
---

Complete the current Git commit operation by following these sequential steps:

## 1. Pre-Commit Validation and Fixes

**First, identify what changes are staged:**

- Run `git status` to see what files are currently staged for commit
- Run `git diff --cached` to review the actual changes that will be committed

**Then, run pre-commit hooks and fix all failures:**

- Execute the pre-commit hooks (likely via `git commit` attempt or `pre-commit run --all-files`)
- Capture and analyze ALL failure messages from the pre-commit output
- For each type of failure identified, fix the issues in this order of priority:
  1. **Formatting issues** (Black, isort, trailing whitespace, etc.) - these are usually auto-fixable
  2. **Linting errors** (Ruff, flake8, etc.) - fix code quality issues
  3. **Type checking errors** (mypy) - resolve type inconsistencies
  4. **Test failures** (pytest) - ensure all tests pass
  5. **Other checks** (documentation validation, security checks, etc.)
- After fixing each category of issues, re-run the pre-commit hooks to verify resolution
- **Critical**: Do NOT disable checks, add `# noqa` comments, or modify pre-commit configuration to bypass failures. All issues must be genuinely resolved through proper code fixes.
- Continue this iterative process until `git commit` (or `pre-commit run --all-files`) completes with zero failures

## 2. Craft a Detailed Commit Message

Once all pre-commit hooks pass, write a commit message following this structure:

**Format:**

```
<type>(<scope>): <subject line - imperative mood, 50-72 chars max>

<body - detailed explanation of WHAT changed and WHY>
- Use bullet points for multiple changes
- Explain the motivation and context
- Reference related work or decisions

<footer - optional references>
Fixes #<issue-number>
Relates to #<issue-number>
Breaking Change: <description if applicable>
```

**Guidelines:**

- Subject line: Use imperative mood (e.g., "Add feature" not "Added feature"), keep under 72 characters
- Body: Explain the reasoning behind changes, not just what changed (the diff shows what changed)
- Include context from the current work (based on recent changes to GitHound's search engine, MCP server, web API, or CLI components)
- Reference any relevant issue numbers, pull requests, or documentation

## 3. Execute Commit and Push

**Commit the changes:**

- Run `git commit` with the crafted message (or use `git commit -m "message"` for simple commits)
- Verify the commit was created successfully by checking `git log -1` output
- Note the commit hash for reference

**Push to remote repository:**

- Identify the current branch with `git branch --show-current`
- Push using `git push origin <branch-name>` (or `git push` if upstream is configured)
- Verify the push succeeded by checking the command output for errors
- Confirm the commit appears on the remote by checking `git log origin/<branch-name> -1`

## 4. Final Verification

- Confirm no uncommitted changes remain (`git status` should show clean working tree)
- Verify the remote repository reflects the new commit (check commit hash matches)
- Report the commit hash, branch name, and confirmation that all steps completed successfully

**Constraints:**

- Do NOT use `git commit --no-verify` or any flags that skip pre-commit hooks
- Do NOT modify `.pre-commit-config.yaml` or other configuration files to disable checks
- Do NOT proceed to commit if any pre-commit hook failures remain unresolved
- Do NOT create new test files or documentation unless they are necessary to fix pre-commit failures
- Follow the project's existing conventions (see CLAUDE.md and pyproject.toml for standards)
