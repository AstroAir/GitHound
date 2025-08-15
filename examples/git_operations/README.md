# Git Operations Examples

This directory contains comprehensive examples for GitHound's git repository analysis capabilities.

## Examples Overview

- `repository_analysis.py` - Repository metadata and statistics
- `commit_analysis.py` - Detailed commit examination
- `blame_operations.py` - File blame and line history
- `diff_analysis.py` - Commit and branch comparisons
- `file_tracking.py` - File history and evolution
- `author_statistics.py` - Contributor analysis
- `branch_operations.py` - Branch analysis and comparison

## Git Operations Categories

### Repository Analysis
- Repository metadata extraction
- Branch and tag enumeration
- Remote repository information
- Repository health metrics
- Contributor statistics

### Commit Operations
- Commit metadata extraction
- Commit history filtering
- Commit message analysis
- File change tracking
- Parent/child relationships

### Blame and History
- Line-by-line blame information
- Author attribution
- Change timeline tracking
- File evolution analysis
- Code ownership patterns

### Diff Analysis
- Commit-to-commit differences
- Branch comparison
- File-level diff analysis
- Change statistics
- Merge conflict detection

### File Operations
- File history tracking
- Rename detection
- Content evolution
- Size and complexity metrics
- Modification patterns

## Running Examples

Each example can be run independently:

```bash
python examples/git_operations/repository_analysis.py /path/to/repo
python examples/git_operations/commit_analysis.py /path/to/repo commit-hash
# etc.
```

## Common Patterns

### Repository Setup
```python
from githound.git_handler import get_repository
from pathlib import Path

repo = get_repository(Path("/path/to/repository"))
```

### Commit Analysis
```python
from githound.git_handler import extract_commit_metadata

commit = repo.head.commit
metadata = extract_commit_metadata(commit)
print(f"Commit: {metadata.hash}")
print(f"Author: {metadata.author_name}")
print(f"Message: {metadata.message}")
```

### Blame Operations
```python
from githound.git_blame import get_file_blame

blame_info = get_file_blame(repo, "src/main.py")
for line_num, blame_data in blame_info.line_blame.items():
    print(f"Line {line_num}: {blame_data.author} - {blame_data.commit_hash}")
```

### Diff Analysis
```python
from githound.git_diff import compare_commits

diff_result = compare_commits(
    repo=repo,
    from_commit="HEAD~1",
    to_commit="HEAD"
)
print(f"Files changed: {diff_result.files_changed}")
print(f"Lines added: {diff_result.total_additions}")
print(f"Lines deleted: {diff_result.total_deletions}")
```

## Output Examples

### Repository Metadata
```json
{
  "total_commits": 1250,
  "total_branches": 15,
  "total_tags": 8,
  "contributors": ["alice", "bob", "charlie"],
  "latest_commit": "abc123...",
  "repository_size": "45.2 MB",
  "creation_date": "2022-01-15T10:30:00Z"
}
```

### Commit Information
```json
{
  "hash": "abc123def456...",
  "author_name": "Alice Developer",
  "author_email": "alice@example.com",
  "commit_date": "2023-11-15T14:30:00Z",
  "message": "Fix critical bug in authentication",
  "files_changed": 3,
  "insertions": 25,
  "deletions": 8,
  "parent_hashes": ["def456ghi789..."]
}
```

### Blame Information
```json
{
  "file_path": "src/auth.py",
  "total_lines": 150,
  "line_blame": {
    "1": {
      "author": "Alice Developer",
      "commit_hash": "abc123...",
      "commit_date": "2023-10-01T09:15:00Z",
      "line_content": "import hashlib"
    }
  }
}
```

## Error Handling

Common error scenarios and handling:

```python
try:
    repo = get_repository(Path(repo_path))
except GitCommandError as e:
    print(f"Git operation failed: {e}")
except FileNotFoundError:
    print(f"Repository not found: {repo_path}")
except PermissionError:
    print(f"Permission denied: {repo_path}")
```
