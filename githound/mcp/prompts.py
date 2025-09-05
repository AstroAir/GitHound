"""MCP prompts for common GitHound workflows."""


def investigate_bug(
    bug_description: str,
    suspected_files: str = "",
    time_frame: str = "last 30 days"
) -> str:
    """
    Generate a prompt for investigating a bug using GitHound's analysis capabilities.

    Provides a structured approach to bug investigation including relevant
    search queries, blame analysis, and commit history examination.
    """
    return f"""# Bug Investigation Workflow

## Bug Description
{bug_description}

## Investigation Steps

### 1. Search for Related Changes
Use GitHound's advanced search to find commits related to this bug:

**Content Search:**
- Search for error messages, function names, or keywords from the bug description
- Use fuzzy search if exact terms don't yield results
- Check recent commits in the specified time frame: {time_frame}

**Recommended Search Queries:**
```
advanced_search:
  content_pattern: "{bug_description.split()[0] if bug_description else 'error'}"
  date_from: "{time_frame}"
  fuzzy_search: true
  fuzzy_threshold: 0.7
```

### 2. Analyze Suspected Files
{f"Focus on these suspected files: {suspected_files}" if suspected_files else "Identify files that might be related to the bug"}

**File Analysis:**
- Use `get_file_blame` to see who last modified critical lines
- Use `get_file_history` to understand recent changes
- Look for patterns in commit messages

### 3. Examine Recent Changes
**Author Analysis:**
- Identify contributors who worked on related code
- Check their recent commits for similar changes
- Look for patterns in their commit history

### 4. Timeline Analysis
**Commit History:**
- Use `get_commit_history` with date filtering
- Look for commits around the time the bug was introduced
- Check for related changes in the same time period

### 5. Generate Report
**Documentation:**
- Export findings using `export_repository_data`
- Include relevant commit hashes, file changes, and author information
- Prepare summary for team discussion

## Next Steps
1. Execute the recommended searches
2. Analyze the results for patterns
3. Identify the root cause
4. Plan the fix strategy
"""


def prepare_code_review(
    branch_name: str,
    base_branch: str = "main",
    focus_areas: str = ""
) -> str:
    """
    Generate a prompt for preparing a comprehensive code review.

    Provides guidance on analyzing changes, checking history, and
    identifying potential issues before code review.
    """
    return f"""# Code Review Preparation Workflow

## Review Target
**Branch:** {branch_name}
**Base:** {base_branch}
{f"**Focus Areas:** {focus_areas}" if focus_areas else ""}

## Pre-Review Analysis

### 1. Compare Branches
Get an overview of all changes:
```
compare_branches_diff:
  from_branch: "{base_branch}"
  to_branch: "{branch_name}"
```

### 2. Analyze Changed Files
For each modified file:
- Use `get_file_blame` to understand current ownership
- Use `get_file_history` to see change patterns
- Check if changes follow established patterns

### 3. Author Analysis
**Contributor Review:**
- Use `get_author_stats` to understand the contributor's history
- Check their typical commit patterns and quality
- Identify if this is a new contributor who might need extra attention

### 4. Search for Related Changes
**Pattern Detection:**
- Search for similar changes in the codebase
- Look for related bug fixes or features
- Check for consistency with existing implementations

### 5. Quality Checks
**Code Quality:**
- Look for large commits that might need breaking down
- Check for appropriate commit message quality
- Identify any files with high change frequency (potential hotspots)

### 6. Security and Performance
**Risk Assessment:**
- Search for changes to security-sensitive areas
- Look for performance-critical code modifications
- Check for changes to configuration or deployment files

## Review Checklist
- [ ] All changes are properly documented
- [ ] Commit messages are clear and descriptive
- [ ] No large files or sensitive data added
- [ ] Changes follow project conventions
- [ ] Related tests are included
- [ ] Documentation is updated if needed

## Tools to Use
1. `compare_branches_diff` - Overall change analysis
2. `get_file_blame` - Understand file ownership
3. `advanced_search` - Find related code patterns
4. `get_author_stats` - Contributor analysis
5. `export_repository_data` - Generate review summary
"""


def analyze_performance_regression(
    performance_issue: str,
    suspected_timeframe: str = "last 2 weeks",
    affected_components: str = ""
) -> str:
    """
    Generate a prompt for analyzing performance regressions.

    Provides a systematic approach to identifying commits that might
    have introduced performance issues.
    """
    return f"""# Performance Regression Analysis

## Issue Description
{performance_issue}

## Analysis Timeframe
{suspected_timeframe}

{f"## Affected Components{chr(10)}{affected_components}{chr(10)}" if affected_components else ""}

## Investigation Strategy

### 1. Timeline Analysis
**Commit History Review:**
```
get_commit_history:
  date_from: "{suspected_timeframe}"
  max_count: 100
```

Look for:
- Large commits that might contain performance-impacting changes
- Changes to core algorithms or data structures
- Database query modifications
- Caching or optimization changes

### 2. File-Specific Analysis
**Hot Spot Identification:**
- Use `advanced_search` to find performance-related keywords:
  - "performance", "optimization", "cache", "query", "algorithm"
  - "slow", "timeout", "memory", "cpu"
- Focus on files with high change frequency

### 3. Author Pattern Analysis
**Contributor Investigation:**
- Identify who made changes during the regression period
- Use `get_author_stats` to understand their typical change patterns
- Look for unusual activity or large commits

### 4. Code Pattern Search
**Performance-Related Changes:**
```
advanced_search:
  content_pattern: "(loop|query|cache|memory|performance)"
  date_from: "{suspected_timeframe}"
  fuzzy_search: true
```

### 5. Diff Analysis
**Change Impact Assessment:**
For suspicious commits:
- Use `compare_commits` to see exact changes
- Look for algorithmic complexity changes
- Check for removed optimizations
- Identify new expensive operations

### 6. Blame Analysis
**Ownership Tracking:**
- Use `get_file_blame` on performance-critical files
- Identify recent changes to hot code paths
- Track down specific lines that might be problematic

## Red Flags to Look For
- O(n²) algorithms replacing O(n) ones
- Removed caching mechanisms
- Added database queries in loops
- Memory leaks or excessive allocations
- Synchronous operations replacing asynchronous ones

## Documentation
Use `export_repository_data` to create a comprehensive report including:
- Timeline of suspicious commits
- Author analysis
- File change patterns
- Specific code changes that might impact performance

## Next Steps
1. Execute the analysis workflow
2. Identify the most likely culprit commits
3. Create test cases to reproduce the issue
4. Plan the performance fix
"""
