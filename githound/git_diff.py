"""Git diff analysis functionality for comparing commits, branches, and files."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, cast

from git import Repo, Commit, GitCommandError, Diff
from pydantic import BaseModel, Field


class ChangeType(str, Enum):
    """Types of changes in a diff."""
    ADDED = "A"
    DELETED = "D"
    MODIFIED = "M"
    RENAMED = "R"
    COPIED = "C"
    TYPE_CHANGED = "T"
    UNMERGED = "U"
    UNKNOWN = "X"


class DiffLineInfo(BaseModel):
    """Information about a single line in a diff."""
    
    line_number_old: Optional[int] = Field(None, description="Line number in old file")
    line_number_new: Optional[int] = Field(None, description="Line number in new file")
    content: str = Field(..., description="Line content")
    change_type: str = Field(..., description="Type of change: '+', '-', or ' '")


class FileDiffInfo(BaseModel):
    """Detailed diff information for a single file."""
    
    file_path: str = Field(..., description="Path to the file")
    old_file_path: Optional[str] = Field(None, description="Old file path (for renames)")
    change_type: ChangeType = Field(..., description="Type of change")
    lines_added: int = Field(0, description="Number of lines added")
    lines_deleted: int = Field(0, description="Number of lines deleted")
    is_binary: bool = Field(False, description="Whether the file is binary")
    diff_lines: List[DiffLineInfo] = Field(default_factory=list, description="Detailed line-by-line diff")


class CommitDiffResult(BaseModel):
    """Complete diff result for a commit comparison."""
    
    from_commit: str = Field(..., description="Source commit hash")
    to_commit: str = Field(..., description="Target commit hash")
    files_changed: int = Field(..., description="Number of files changed")
    total_additions: int = Field(..., description="Total lines added")
    total_deletions: int = Field(..., description="Total lines deleted")
    file_diffs: List[FileDiffInfo] = Field(..., description="Detailed file diffs")


def analyze_diff(diff: Diff) -> FileDiffInfo:
    """
    Analyze a single Git diff object.
    
    Args:
        diff: Git diff object.
        
    Returns:
        FileDiffInfo with detailed analysis.
    """
    # Determine change type
    if diff.new_file:
        change_type = ChangeType.ADDED
    elif diff.deleted_file:
        change_type = ChangeType.DELETED
    elif diff.renamed_file:
        change_type = ChangeType.RENAMED
    elif diff.copied_file:
        change_type = ChangeType.COPIED
    else:
        change_type = ChangeType.MODIFIED
    
    file_path = diff.b_path or diff.a_path or "unknown"
    old_file_path = diff.a_path if diff.renamed_file else None
    
    # Check if binary file
    is_binary = False
    try:
        if diff.a_blob and diff.a_blob.size > 0:
            # Try to decode a small portion to check if it's text
            sample = diff.a_blob.data_stream.read(1024)
            try:
                sample.decode('utf-8')
            except UnicodeDecodeError:
                is_binary = True
        elif diff.b_blob and diff.b_blob.size > 0:
            sample = diff.b_blob.data_stream.read(1024)
            try:
                sample.decode('utf-8')
            except UnicodeDecodeError:
                is_binary = True
    except Exception:
        is_binary = True
    
    diff_lines = []
    lines_added = 0
    lines_deleted = 0
    
    if not is_binary:
        try:
            # Get the diff text
            if diff.diff is None:
                return FileDiffInfo(
                    file_path=file_path,
                    change_type=change_type,
                    lines_added=0,
                    lines_deleted=0,
                    diff_lines=[]
                )
            elif isinstance(diff.diff, bytes):
                diff_text = diff.diff.decode('utf-8', errors='ignore')
            else:
                diff_text = diff.diff
            
            old_line_num = 1
            new_line_num = 1
            
            for line in diff_text.split('\n'):
                if line.startswith('@@'):
                    # Parse hunk header to get line numbers
                    parts = line.split()
                    if len(parts) >= 3:
                        old_range = parts[1][1:]  # Remove the '-'
                        new_range = parts[2][1:]  # Remove the '+'
                        
                        if ',' in old_range:
                            old_line_num = int(old_range.split(',')[0])
                        else:
                            old_line_num = int(old_range)
                            
                        if ',' in new_range:
                            new_line_num = int(new_range.split(',')[0])
                        else:
                            new_line_num = int(new_range)
                    continue
                
                if line.startswith('+') and not line.startswith('+++'):
                    diff_lines.append(DiffLineInfo(
                        line_number_old=None,
                        line_number_new=new_line_num,
                        content=line[1:],
                        change_type='+'
                    ))
                    lines_added += 1
                    new_line_num += 1
                elif line.startswith('-') and not line.startswith('---'):
                    diff_lines.append(DiffLineInfo(
                        line_number_old=old_line_num,
                        line_number_new=None,
                        content=line[1:],
                        change_type='-'
                    ))
                    lines_deleted += 1
                    old_line_num += 1
                elif line.startswith(' '):
                    diff_lines.append(DiffLineInfo(
                        line_number_old=old_line_num,
                        line_number_new=new_line_num,
                        content=line[1:],
                        change_type=' '
                    ))
                    old_line_num += 1
                    new_line_num += 1
                    
        except Exception:
            # If we can't parse the diff, just count from the diff object
            pass
    
    return FileDiffInfo(
        file_path=file_path,
        old_file_path=old_file_path,
        change_type=change_type,
        lines_added=lines_added,
        lines_deleted=lines_deleted,
        is_binary=is_binary,
        diff_lines=diff_lines
    )


def compare_commits(
    repo: Repo,
    from_commit: str,
    to_commit: str,
    file_patterns: Optional[List[str]] = None
) -> CommitDiffResult:
    """
    Compare two commits and return detailed diff analysis.
    
    Args:
        repo: The Git repository object.
        from_commit: Source commit hash or reference.
        to_commit: Target commit hash or reference.
        file_patterns: Optional list of file patterns to filter.
        
    Returns:
        CommitDiffResult with complete diff analysis.
    """
    try:
        from_commit_obj = repo.commit(from_commit)
        to_commit_obj = repo.commit(to_commit)
        
        # Get the diff between commits
        if file_patterns:
            # GitPython accepts various path types, cast to satisfy mypy
            diffs = from_commit_obj.diff(to_commit_obj, paths=cast(Any, file_patterns))
        else:
            diffs = from_commit_obj.diff(to_commit_obj)
        
        file_diffs = []
        total_additions = 0
        total_deletions = 0
        
        for diff in diffs:
            file_diff = analyze_diff(diff)
            file_diffs.append(file_diff)
            total_additions += file_diff.lines_added
            total_deletions += file_diff.lines_deleted
        
        return CommitDiffResult(
            from_commit=from_commit_obj.hexsha,
            to_commit=to_commit_obj.hexsha,
            files_changed=len(file_diffs),
            total_additions=total_additions,
            total_deletions=total_deletions,
            file_diffs=file_diffs
        )
        
    except Exception as e:
        raise GitCommandError(f"Error comparing commits '{from_commit}' and '{to_commit}': {str(e)}")


def compare_branches(
    repo: Repo,
    from_branch: str,
    to_branch: str,
    file_patterns: Optional[List[str]] = None
) -> CommitDiffResult:
    """
    Compare two branches and return detailed diff analysis.
    
    Args:
        repo: The Git repository object.
        from_branch: Source branch name.
        to_branch: Target branch name.
        file_patterns: Optional list of file patterns to filter.
        
    Returns:
        CommitDiffResult with complete diff analysis.
    """
    try:
        from_commit = repo.branches[from_branch].commit
        to_commit = repo.branches[to_branch].commit
        
        return compare_commits(repo, from_commit.hexsha, to_commit.hexsha, file_patterns)
        
    except KeyError as e:
        raise GitCommandError(f"Branch not found: {str(e)}")
    except Exception as e:
        raise GitCommandError(f"Error comparing branches '{from_branch}' and '{to_branch}': {str(e)}")


def get_file_diff_history(
    repo: Repo,
    file_path: str,
    max_commits: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Get the diff history for a specific file across commits.
    
    Args:
        repo: The Git repository object.
        file_path: Path to the file.
        max_commits: Maximum number of commits to examine.
        
    Returns:
        List of dictionaries containing file diff history.
    """
    history = []
    
    try:
        kwargs: Dict[str, Any] = {'paths': [file_path]}
        if max_commits:
            kwargs['max_count'] = max_commits

        commits = list(repo.iter_commits(**kwargs))
        
        for i, commit in enumerate(commits):
            if i < len(commits) - 1:
                # Compare with previous commit
                parent_commit = commits[i + 1]
                
                try:
                    diffs = parent_commit.diff(commit, paths=[file_path])
                    
                    if diffs:
                        diff = diffs[0]
                        file_diff = analyze_diff(diff)
                        
                        history.append({
                            'commit_hash': commit.hexsha,
                            'parent_commit_hash': parent_commit.hexsha,
                            'commit_date': datetime.fromtimestamp(commit.committed_date),
                            'author': f"{commit.author.name} <{commit.author.email}>",
                            'message': commit.message.strip(),
                            'change_type': file_diff.change_type.value,
                            'lines_added': file_diff.lines_added,
                            'lines_deleted': file_diff.lines_deleted,
                            'is_binary': file_diff.is_binary
                        })
                        
                except Exception:
                    # Skip this comparison if it fails
                    continue
                    
    except GitCommandError as e:
        raise GitCommandError(f"Error getting diff history for '{file_path}': {e}")
    
    return history
