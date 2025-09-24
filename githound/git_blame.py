"""Git blame functionality for line-by-line authorship tracking."""

from datetime import datetime
from typing import Any

from git import GitCommandError, Repo
from pydantic import BaseModel, Field


class BlameInfo(BaseModel):
    """Information about a single line's authorship."""

    line_number: int = Field(..., description="Line number (1-based)")
    content: str = Field(..., description="Line content")
    commit_hash: str = Field(..., description="Commit hash that last modified this line")
    author_name: str = Field(..., description="Author name")
    author_email: str = Field(..., description="Author email")
    commit_date: datetime = Field(..., description="Date of the commit")
    commit_message: str = Field(..., description="Commit message")


class FileBlameResult(BaseModel):
    """Complete blame information for a file."""

    file_path: str = Field(..., description="Path to the file")
    total_lines: int = Field(..., description="Total number of lines")
    blame_info: list[BlameInfo] = Field(..., description="Blame information for each line")
    contributors: list[str] = Field(..., description="List of unique contributors")
    oldest_line_date: datetime | None = Field(None, description="Date of the oldest line")
    newest_line_date: datetime | None = Field(None, description="Date of the newest line")


def get_file_blame(repo: Repo, file_path: str, commit: str | None = None) -> FileBlameResult:
    """
    Get line-by-line authorship information for a file.

    Args:
        repo: The Git repository object.
        file_path: Path to the file relative to repository root.
        commit: Specific commit to blame (defaults to HEAD).

    Returns:
        FileBlameResult with complete blame information.

    Raises:
        GitCommandError: If the file doesn't exist or blame fails.
    """
    try:
        # Get the commit object
        if commit:
            commit_obj = repo.commit(commit)
        else:
            commit_obj = repo.head.commit

        # Get blame information
        blame_data = repo.blame(commit_obj, file_path)

        blame_info: list[BlameInfo] = []
        contributors = set()
        dates: list[Any] = []

        line_number = 1
        # GitPython blame data structure is complex, use type ignore for now
        for commit_info, lines in blame_data:  # type: ignore
            for line in lines:  # type: ignore
                blame_entry = BlameInfo(
                    line_number=line_number,
                    content=str(line).rstrip("\n\r"),
                    commit_hash=commit_info.hexsha,  # type: ignore
                    author_name=commit_info.author.name,  # type: ignore
                    author_email=commit_info.author.email,  # type: ignore
                    commit_date=datetime.fromtimestamp(commit_info.committed_date),  # type: ignore
                    commit_message=str(commit_info.message).strip(),  # type: ignore
                )

                blame_info.append(blame_entry)
                contributors.add(
                    f"{commit_info.author.name} <{commit_info.author.email}>"  # type: ignore
                )
                dates.append(blame_entry.commit_date)
                line_number += 1

        return FileBlameResult(
            file_path=file_path,
            total_lines=len(blame_info),
            blame_info=blame_info,
            contributors=list(contributors),
            oldest_line_date=min(dates) if dates else None,
            newest_line_date=max(dates) if dates else None,
        )

    except Exception as e:
        raise GitCommandError(f"Failed to get blame for '{file_path}': {str(e)}")


def get_line_history(
    repo: Repo, file_path: str, line_number: int, max_commits: int | None = None
) -> list[dict[str, Any]]:
    """
    Get the history of changes for a specific line in a file.

    Args:
        repo: The Git repository object.
        file_path: Path to the file relative to repository root.
        line_number: Line number to track (1-based).
        max_commits: Maximum number of commits to examine.

    Returns:
        List of dictionaries containing line change history.
    """
    history: list[Any] = []

    try:
        kwargs: dict[str, Any] = {"paths": [file_path]}
        if max_commits:
            kwargs["max_count"] = max_commits

        for commit in repo.iter_commits(**kwargs):
            try:
                # Get blame for this commit
                blame_data = repo.blame(commit, file_path)

                current_line = 1
                # GitPython blame data structure is complex, use type ignore
                for commit_info, lines in blame_data:  # type: ignore
                    for line in lines:  # type: ignore
                        if current_line == line_number:
                            history.append(
                                {
                                    "commit_hash": commit.hexsha,
                                    "commit_date": datetime.fromtimestamp(commit.committed_date),
                                    "author": f"{commit_info.author.name} <{commit_info.author.email}>",  # type: ignore
                                    "message": str(commit_info.message).strip(),  # type: ignore
                                    "line_content": str(line).rstrip("\n\r"),
                                    "line_commit_hash": commit_info.hexsha,  # type: ignore
                                    "line_author": f"{commit_info.author.name} <{commit_info.author.email}>",  # type: ignore
                                    "line_date": datetime.fromtimestamp(commit_info.committed_date),  # type: ignore
                                }
                            )
                            break
                        current_line += 1
                    else:
                        continue
                    break

            except Exception:
                # Skip commits where we can't get blame (file might not exist)
                continue

    except GitCommandError as e:
        raise GitCommandError(f"Error getting line history for '{file_path}:{line_number}': {e}")

    return history


def get_author_statistics(
    repo: Repo, file_path: str | None = None, branch: str | None = None
) -> dict[str, dict[str, Any]]:
    """
    Get authorship statistics for a file or entire repository.

    Args:
        repo: The Git repository object.
        file_path: Specific file to analyze (optional, analyzes all files if None).
        branch: Branch to analyze (defaults to current branch).

    Returns:
        Dictionary with author statistics.
    """
    author_stats: dict[str, dict[str, Any]] = {}

    try:
        if file_path:
            # Analyze single file
            blame_result = get_file_blame(repo, file_path)

            for blame_info in blame_result.blame_info:
                author_key = f"{blame_info.author_name} <{blame_info.author_email}>"

                if author_key not in author_stats:
                    author_stats[author_key] = {
                        "lines_authored": 0,
                        "commits": set(),
                        "files": set(),
                        "first_commit_date": blame_info.commit_date,
                        "last_commit_date": blame_info.commit_date,
                    }

                stats = author_stats[author_key]
                stats["lines_authored"] += 1
                stats["commits"].add(blame_info.commit_hash)
                stats["files"].add(file_path)

                if blame_info.commit_date < stats["first_commit_date"]:
                    stats["first_commit_date"] = blame_info.commit_date
                if blame_info.commit_date > stats["last_commit_date"]:
                    stats["last_commit_date"] = blame_info.commit_date
        else:
            # Analyze entire repository
            kwargs: dict[str, Any] = {}
            if branch:
                kwargs["rev"] = branch

            for commit in repo.iter_commits(**kwargs):
                author_key = f"{commit.author.name} <{commit.author.email}>"

                if author_key not in author_stats:
                    author_stats[author_key] = {
                        "lines_authored": 0,
                        "commits": set(),
                        "files": set(),
                        "first_commit_date": datetime.fromtimestamp(commit.committed_date),
                        "last_commit_date": datetime.fromtimestamp(commit.committed_date),
                    }

                stats = author_stats[author_key]
                stats["commits"].add(commit.hexsha)

                commit_date = datetime.fromtimestamp(commit.committed_date)
                if commit_date < stats["first_commit_date"]:
                    stats["first_commit_date"] = commit_date
                if commit_date > stats["last_commit_date"]:
                    stats["last_commit_date"] = commit_date

                # Count files changed in this commit
                if commit.parents:
                    for parent in commit.parents:
                        diffs = commit.diff(parent)
                        for diff in diffs:
                            if diff.b_path:
                                stats["files"].add(diff.b_path)

    except Exception as e:
        raise GitCommandError(f"Error getting author statistics: {str(e)}")

    # Convert sets to counts for final output
    for author, stats in author_stats.items():
        stats["total_commits"] = len(stats["commits"])
        stats["total_files"] = len(stats["files"])
        del stats["commits"]  # Remove the set, keep only the count
        del stats["files"]  # Remove the set, keep only the count

    return author_stats
