"""
Git Operations Utilities

This module provides utility functions for git operations used across
the MCP server examples. It includes helpers for repository analysis,
commit processing, and metadata extraction.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class GitCommit:
    """Represents a Git commit with metadata."""

    hash: str
    author: str
    author_email: str
    date: datetime
    message: str
    files_changed: int
    insertions: int
    deletions: int


@dataclass
class GitAuthor:
    """Represents a Git author with statistics."""

    name: str
    email: str
    commit_count: int
    insertions: int
    deletions: int
    files_modified: int


@dataclass
class GitRepository:
    """Represents a Git repository with metadata."""

    name: str
    path: Path
    total_commits: int
    total_files: int
    total_authors: int
    branches: list[str]
    tags: list[str]
    first_commit_date: datetime | None
    last_commit_date: datetime | None


class GitOperationsError(Exception):
    """Exception raised for Git operations errors."""

    pass


class GitOperations:
    """Utility class for Git operations."""

    def __init__(self, repo_path: str) -> None:
        """
        Initialize Git operations for a repository.

        Args:
            repo_path: Path to the Git repository
        """
        self.repo_path = Path(repo_path).resolve()
        self._validate_repository()

    def _validate_repository(self) -> None:
        """Validate that the path is a Git repository."""
        if not self.repo_path.exists():
            raise GitOperationsError(f"Repository path does not exist: {self.repo_path}")

        git_dir = self.repo_path / ".git"
        if not git_dir.exists():
            raise GitOperationsError(f"Not a Git repository: {self.repo_path}")

    async def _run_git_command(self, args: list[str]) -> str:
        """
        Run a Git command asynchronously.

        Args:
            args: Git command arguments

        Returns:
            Command output as string

        Raises:
            GitOperationsError: If command fails
        """
        try:
            process = await asyncio.create_subprocess_exec(
                "git",
                *args,
                cwd=self.repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode().strip()
                raise GitOperationsError(f"Git command failed: {error_msg}")

            return stdout.decode().strip()

        except FileNotFoundError as e:
            raise GitOperationsError(
                "Git command not found. Please ensure Git is installed."
            ) from e
        except Exception as e:
            raise GitOperationsError(f"Failed to execute Git command: {e}") from e

    async def get_repository_info(self) -> GitRepository:
        """
        Get comprehensive repository information.

        Returns:
            GitRepository object with metadata
        """
        logger.info(f"Getting repository info for {self.repo_path}")

        # Get repository name
        name = self.repo_path.name

        # Get total commits
        commit_count_output = await self._run_git_command(["rev-list", "--count", "HEAD"])
        total_commits = int(commit_count_output)

        # Get total files (tracked files)
        files_output = await self._run_git_command(["ls-files"])
        total_files = len(files_output.split("\n")) if files_output else 0

        # Get authors
        authors_output = await self._run_git_command(["log", "--format=%ae", "HEAD"])
        unique_authors = set(authors_output.split("\n")) if authors_output else set()
        total_authors = len(unique_authors)

        # Get branches
        branches_output = await self._run_git_command(["branch", "-a"])
        branches: list[Any] = []
        for line in branches_output.split("\n"):
            line = line.strip()
            if line and not line.startswith("*"):
                branch = line.replace("remotes/origin/", "").replace("remotes/", "")
                if branch not in branches and not branch.startswith("HEAD"):
                    branches.append(branch)
            elif line.startswith("*"):
                current_branch = line[2:].strip()
                if current_branch not in branches:
                    branches.insert(0, current_branch)

        # Get tags
        try:
            tags_output = await self._run_git_command(["tag", "-l"])
            tags = tags_output.split("\n") if tags_output else []
        except GitOperationsError:
            tags: list[Any] = []

        # Get first and last commit dates
        try:
            first_commit_output = await self._run_git_command(
                ["log", "--reverse", "--format=%ai", "-1"]
            )
            first_commit_date = datetime.fromisoformat(
                first_commit_output.replace
                if first_commit_output is not None
                else None(" ", "T", 1).rstrip("Z")
            )
        except (GitOperationsError, ValueError):
            first_commit_date = None

        try:
            last_commit_output = await self._run_git_command(["log", "--format=%ai", "-1"])
            last_commit_date = datetime.fromisoformat(
                last_commit_output.replace
                if last_commit_output is not None
                else None(" ", "T", 1).rstrip("Z")
            )
        except (GitOperationsError, ValueError):
            last_commit_date = None

        return GitRepository(
            name=name,
            path=self.repo_path,
            total_commits=total_commits,
            total_files=total_files,
            total_authors=total_authors,
            branches=branches,
            tags=tags,
            first_commit_date=first_commit_date,
            last_commit_date=last_commit_date,
        )

    async def get_commit_history(
        self,
        limit: int = 10,
        author: str | None = None,
        since: str | None = None,
        until: str | None = None,
        file_path: str | None = None,
    ) -> list[GitCommit]:
        """
        Get commit history with optional filtering.

        Args:
            limit: Maximum number of commits to return
            author: Filter by author name or email
            since: Filter commits since this date (ISO format)
            until: Filter commits until this date (ISO format)
            file_path: Filter commits that modified this file

        Returns:
            List of GitCommit objects
        """
        logger.info(f"Getting commit history (limit: {limit})")

        # Build git log command
        args = ["log", f"--max-count={limit}", "--format=%H|%an|%ae|%ai|%s"]

        if author:
            args.extend(["--author", author])

        if since:
            args.extend(["--since", since])

        if until:
            args.extend(["--until", until])

        if file_path:
            args.extend(["--", file_path])

        # Get commit log
        log_output = await self._run_git_command(args)

        if not log_output:
            return []

        commits: list[Any] = []
        for line in log_output.split("\n"):
            if not line:
                continue

            parts = line.split("|", 4)
            if len(parts) != 5:
                continue

            commit_hash, author_name, author_email, date_str, message = parts

            # Parse date
            try:
                commit_date = datetime.fromisoformat(
                    date_str.replace if date_str is not None else None(" ", "T", 1).rstrip("Z")
                )
            except ValueError:
                commit_date = datetime.now()

            # Get commit stats
            try:
                stats_output = await self._run_git_command(
                    ["show", "--stat", "--format=", commit_hash]
                )

                # Parse stats (files changed, insertions, deletions)
                files_changed = 0
                insertions = 0
                deletions = 0

                for stat_line in stats_output.split("\n"):
                    if "file" in stat_line and "changed" in stat_line:
                        # Parse summary line like "2 files changed, 10 insertions(+), 5 deletions(-)"
                        parts = stat_line.split(",")
                        for part in parts:
                            part = part.strip()
                            if "file" in part and "changed" in part:
                                files_changed = int(part.split()[0])
                            elif "insertion" in part:
                                insertions = int(part.split()[0])
                            elif "deletion" in part:
                                deletions = int(part.split()[0])
                        break
                    elif stat_line.strip() and "|" in stat_line:
                        # Count individual file changes
                        files_changed += 1

            except GitOperationsError:
                files_changed = 0
                insertions = 0
                deletions = 0

            commits.append(
                GitCommit(
                    hash=commit_hash,
                    author=author_name,
                    author_email=author_email,
                    date=commit_date,
                    message=message,
                    files_changed=files_changed,
                    insertions=insertions,
                    deletions=deletions,
                )
            )

        return commits

    async def get_author_statistics(self) -> dict[str, Any]:
        """
        Get author contribution statistics.

        Returns:
            Dictionary containing author statistics
        """
        logger.info("Getting author statistics")

        # Get all commits with author info
        log_output = await self._run_git_command(["log", "--format=%an|%ae|%H"])

        if not log_output:
            return {"authors": [], "total_authors": 0}

        # Count commits per author
        author_commits: dict[str, Any] = {}
        commit_hashes: list[Any] = []

        for line in log_output.split("\n"):
            if not line:
                continue

            parts = line.split("|", 2)
            if len(parts) != 3:
                continue

            author_name, author_email, commit_hash = parts
            author_key = (author_name, author_email)

            if author_key not in author_commits:
                author_commits[author_key] = []

            author_commits[author_key].append(commit_hash)
            commit_hashes.append(commit_hash)

        # Get detailed stats for each author
        authors: list[Any] = []
        for (author_name, author_email), commits in author_commits.items():
            # Get insertions and deletions for this author
            total_insertions = 0
            total_deletions = 0
            files_modified = set()

            for commit_hash in commits:
                try:
                    stats_output = await self._run_git_command(
                        ["show", "--stat", "--format=", commit_hash]
                    )

                    for stat_line in stats_output.split("\n"):
                        if "|" in stat_line and ("+" in stat_line or "-" in stat_line):
                            # Parse file stat line
                            parts = stat_line.split("|")
                            if len(parts) >= 2:
                                file_path = parts[0].strip()
                                files_modified.add(file_path)

                                # Count + and - symbols
                                changes = parts[1].strip()
                                total_insertions += changes.count("+")
                                total_deletions += changes.count("-")
                        elif "insertion" in stat_line or "deletion" in stat_line:
                            # Parse summary line
                            parts = stat_line.split(",")
                            for part in parts:
                                part = part.strip()
                                if "insertion" in part:
                                    total_insertions += int(part.split()[0])
                                elif "deletion" in part:
                                    total_deletions += int(part.split()[0])

                except GitOperationsError:
                    continue

            authors.append(
                GitAuthor(
                    name=author_name,
                    email=author_email,
                    commit_count=len(commits),
                    insertions=total_insertions,
                    deletions=total_deletions,
                    files_modified=len(files_modified),
                )
            )

        # Sort authors by commit count
        authors.sort(key=lambda a: a.commit_count, reverse=True)

        return {"authors": authors, "total_authors": len(authors)}

    async def get_file_history(self, file_path: str, limit: int = 10) -> list[GitCommit]:
        """
        Get commit history for a specific file.

        Args:
            file_path: Path to the file within the repository
            limit: Maximum number of commits to return

        Returns:
            List of GitCommit objects that modified the file
        """
        logger.info(f"Getting file history for {file_path}")

        return await self.get_commit_history(limit=limit, file_path=file_path)

    async def analyze_commit(self, commit_hash: str) -> GitCommit:
        """
        Analyze a specific commit in detail.

        Args:
            commit_hash: Hash of the commit to analyze

        Returns:
            GitCommit object with detailed information
        """
        logger.info(f"Analyzing commit {commit_hash}")

        # Get commit info
        commit_info = await self._run_git_command(
            ["show", "--format=%H|%an|%ae|%ai|%s", "--stat", commit_hash]
        )

        lines = commit_info.split("\n")
        if not lines:
            raise GitOperationsError(f"Commit not found: {commit_hash}")

        # Parse commit header
        header_parts = lines[0].split("|", 4)
        if len(header_parts) != 5:
            raise GitOperationsError(f"Invalid commit format: {commit_hash}")

        hash_val, author_name, author_email, date_str, message = header_parts

        # Parse date
        try:
            commit_date = datetime.fromisoformat(
                date_str.replace if date_str is not None else None(" ", "T", 1).rstrip("Z")
            )
        except ValueError:
            commit_date = datetime.now()

        # Parse stats
        files_changed = 0
        insertions = 0
        deletions = 0

        for line in lines[1:]:
            if "file" in line and "changed" in line:
                # Parse summary line
                parts = line.split(",")
                for part in parts:
                    part = part.strip()
                    if "file" in part and "changed" in part:
                        files_changed = int(part.split()[0])
                    elif "insertion" in part:
                        insertions = int(part.split()[0])
                    elif "deletion" in part:
                        deletions = int(part.split()[0])
                break
            elif "|" in line and ("+" in line or "-" in line):
                # Count individual file changes
                files_changed += 1

        return GitCommit(
            hash=hash_val,
            author=author_name,
            author_email=author_email,
            date=commit_date,
            message=message,
            files_changed=files_changed,
            insertions=insertions,
            deletions=deletions,
        )
