"""File-based searchers for GitHound."""

import fnmatch
import json
import re
import subprocess
from collections.abc import AsyncGenerator
from pathlib import Path

from ..models import CommitInfo, SearchQuery, SearchResult, SearchType
from .base import CacheableSearcher, ParallelSearcher, SearchContext


class FilePathSearcher(CacheableSearcher):
    """Searcher for files by path patterns."""

    def __init__(self) -> None:
        super().__init__("file_path", "file_path")

    async def can_handle(self, query: SearchQuery) -> bool:
        """Check if this searcher can handle the query."""
        return query.file_path_pattern is not None

    async def estimate_work(self, context: SearchContext) -> int:
        """Estimate work based on repository size."""
        try:
            branch = context.branch or context.repo.active_branch.name
            commits = list(context.repo.iter_commits(branch, max_count=500))
            return min(len(commits), 500)
        except:
            return 100

    async def search(self, context: SearchContext) -> AsyncGenerator[SearchResult, None]:
        """Search for files by path pattern."""
        file_pattern = context.query.file_path_pattern
        if not file_pattern:
            return

        self._report_progress(
            context, f"Searching for files matching '{file_pattern}'...", 0.0)

        branch = context.branch or context.repo.active_branch.name

        # Compile regex pattern
        regex_pattern = None
        try:
            flags = 0 if context.query.case_sensitive else re.IGNORECASE
            regex_pattern = re.compile(file_pattern, flags)
        except re.error:
            # If regex is invalid, use glob pattern
            pass

        commits_searched = 0
        results_found = 0
        seen_files = set()  # Track unique file paths

        try:
            for commit in context.repo.iter_commits(branch):
                commits_searched += 1

                # Get files changed in this commit
                for parent in commit.parents:
                    diffs = commit.diff(parent)
                    for diff in diffs:
                        if diff.b_blob is None or diff.b_path is None:
                            continue

                        file_path = diff.b_path

                        # Skip if we've already seen this file
                        if file_path in seen_files:
                            continue

                        match = False
                        if regex_pattern:
                            match = regex_pattern.search(file_path) is not None
                        else:
                            # Use glob pattern matching
                            match = fnmatch.fnmatch(file_path, file_pattern)

                        if match:
                            seen_files.add(file_path)

                            # Create commit info
                            commit_info = CommitInfo(
                                hash=commit.hexsha,
                                short_hash=commit.hexsha[:8],
                                author_name=commit.author.name,
                                author_email=commit.author.email,
                                committer_name=commit.committer.name,
                                committer_email=commit.committer.email,
                                message=commit.message.strip(),
                                date=commit.committed_date,
                                files_changed=len(commit.stats.files),
                                insertions=commit.stats.total["insertions"],
                                deletions=commit.stats.total["deletions"],
                                parents=[
                                    parent.hexsha for parent in commit.parents],
                            )

                            result = SearchResult(
                                commit_hash=commit.hexsha,
                                file_path=Path(file_path),
                                line_number=None,
                                matching_line=None,
                                search_type=SearchType.FILE_PATH,
                                relevance_score=1.0,
                                commit_info=commit_info,
                                match_context={
                                    "search_pattern": file_pattern,
                                    "matched_path": file_path,
                                },
                                search_time_ms=None,
                            )

                            results_found += 1
                            yield result

                if commits_searched % 50 == 0:
                    progress = min(commits_searched / 500, 0.9)
                    self._report_progress(
                        context,
                        f"Searched {commits_searched} commits, found {results_found} file matches",
                        progress,
                    )

        except Exception as e:
            self._report_progress(
                context, f"Error searching file paths: {e}", 1.0)

        finally:
            self._update_metrics(
                total_commits_searched=commits_searched,
                total_files_searched=len(seen_files),
                total_results_found=results_found,
            )
            self._report_progress(
                context, f"File path search completed: {results_found} matches", 1.0
            )


class FileTypeSearcher(CacheableSearcher):
    """Searcher for files by extension/type."""

    def __init__(self) -> None:
        super().__init__("file_type", "file_type")

    async def can_handle(self, query: SearchQuery) -> bool:
        """Check if this searcher can handle the query."""
        return query.file_extensions is not None and len(query.file_extensions) > 0

    async def estimate_work(self, context: SearchContext) -> int:
        """Estimate work based on repository size."""
        try:
            branch = context.branch or context.repo.active_branch.name
            commits = list(context.repo.iter_commits(branch, max_count=500))
            return min(len(commits), 500)
        except:
            return 100

    async def search(self, context: SearchContext) -> AsyncGenerator[SearchResult, None]:
        """Search for files by extension."""
        extensions = context.query.file_extensions
        if not extensions:
            return

        # Normalize extensions (ensure they start with .)
        normalized_extensions: list[Any] = []
        for ext in extensions:
            if not ext.startswith("."):
                ext = "." + ext
            normalized_extensions.append(ext.lower if ext is not None else None())

        self._report_progress(
            context, f"Searching for files with extensions: {', '.join(normalized_extensions)}", 0.0
        )

        branch = context.branch or context.repo.active_branch.name

        commits_searched = 0
        results_found = 0
        seen_files = set()

        try:
            for commit in context.repo.iter_commits(branch):
                commits_searched += 1

                for parent in commit.parents:
                    diffs = commit.diff(parent)
                    for diff in diffs:
                        if diff.b_blob is None or diff.b_path is None:
                            continue

                        file_path = diff.b_path

                        if file_path in seen_files:
                            continue

                        # Check file extension
                        file_ext = Path(file_path).suffix.lower()
                        if file_ext in normalized_extensions:
                            seen_files.add(file_path)

                            commit_info = CommitInfo(
                                hash=commit.hexsha,
                                short_hash=commit.hexsha[:8],
                                author_name=commit.author.name,
                                author_email=commit.author.email,
                                committer_name=commit.committer.name,
                                committer_email=commit.committer.email,
                                message=commit.message.strip(),
                                date=commit.committed_date,
                                files_changed=len(commit.stats.files),
                                insertions=commit.stats.total["insertions"],
                                deletions=commit.stats.total["deletions"],
                                parents=[
                                    parent.hexsha for parent in commit.parents],
                            )

                            result = SearchResult(
                                commit_hash=commit.hexsha,
                                file_path=Path(file_path),
                                line_number=None,
                                matching_line=None,
                                search_type=SearchType.FILE_TYPE,
                                relevance_score=1.0,
                                commit_info=commit_info,
                                match_context={
                                    "search_extensions": extensions,
                                    "matched_extension": file_ext,
                                    "file_path": file_path,
                                },
                                search_time_ms=None,
                            )

                            results_found += 1
                            yield result

                if commits_searched % 50 == 0:
                    progress = min(commits_searched / 500, 0.9)
                    self._report_progress(
                        context,
                        f"Searched {commits_searched} commits, found {results_found} file type matches",
                        progress,
                    )

        except Exception as e:
            self._report_progress(
                context, f"Error searching file types: {e}", 1.0)

        finally:
            self._update_metrics(
                total_commits_searched=commits_searched,
                total_files_searched=len(seen_files),
                total_results_found=results_found,
            )
            self._report_progress(
                context, f"File type search completed: {results_found} matches", 1.0
            )


class ContentSearcher(ParallelSearcher, CacheableSearcher):
    """Enhanced content searcher with ranking and performance optimizations."""

    def __init__(self) -> None:
        super().__init__("content", 4)  # Use 4 parallel workers
        self.cache_prefix = "content"

    async def can_handle(self, query: SearchQuery) -> bool:
        """Check if this searcher can handle the query."""
        return query.content_pattern is not None

    async def estimate_work(self, context: SearchContext) -> int:
        """Estimate work based on repository size and file filters."""
        try:
            branch = context.branch or context.repo.active_branch.name
            commits = list(context.repo.iter_commits(branch, max_count=200))

            # Estimate files per commit
            total_files = 0
            for commit in commits[:10]:  # Sample first 10 commits
                for parent in commit.parents:
                    diffs = commit.diff(parent)
                    total_files += len([d for d in diffs if d.b_blob is not None])

            avg_files_per_commit = max(total_files / 10, 1) if commits else 1
            return int(len(commits) * avg_files_per_commit)
        except:
            return 500

    async def search(self, context: SearchContext) -> AsyncGenerator[SearchResult, None]:
        """Search for content patterns in files."""
        content_pattern = context.query.content_pattern
        if not content_pattern:
            return

        self._report_progress(
            context, f"Searching file content for '{content_pattern}'...", 0.0)

        branch = context.branch or context.repo.active_branch.name

        commits_searched = 0
        files_searched = 0
        results_found = 0

        try:
            for commit in context.repo.iter_commits(branch):
                commits_searched += 1

                for parent in commit.parents:
                    diffs = commit.diff(parent)
                    for diff in diffs:
                        if diff.b_blob is None or diff.b_path is None:
                            continue

                        file_path = diff.b_path
                        files_searched += 1

                        # Apply file filters
                        if not self._should_search_file(file_path, context.query):
                            continue

                        try:
                            # Get file content
                            content = diff.b_blob.data_stream.read()

                            # Check file size limit
                            if (
                                context.query.max_file_size
                                and len(content) > context.query.max_file_size
                            ):
                                continue

                            # Search content using ripgrep
                            matches = await self._search_content_with_ripgrep(
                                content, content_pattern, context.query
                            )

                            for match in matches:
                                commit_info = CommitInfo(
                                    hash=commit.hexsha,
                                    short_hash=commit.hexsha[:8],
                                    author_name=commit.author.name,
                                    author_email=commit.author.email,
                                    committer_name=commit.committer.name,
                                    committer_email=commit.committer.email,
                                    message=commit.message.strip(),
                                    date=commit.committed_date,
                                    files_changed=len(commit.stats.files),
                                    insertions=commit.stats.total["insertions"],
                                    deletions=commit.stats.total["deletions"],
                                    parents=[
                                        parent.hexsha for parent in commit.parents],
                                )

                                # Calculate relevance score based on match quality
                                relevance_score = self._calculate_relevance_score(
                                    match, content_pattern, file_path
                                )

                                result = SearchResult(
                                    commit_hash=commit.hexsha,
                                    file_path=Path(file_path),
                                    line_number=match.get("line_number"),
                                    matching_line=match.get("text"),
                                    search_type=SearchType.CONTENT,
                                    relevance_score=relevance_score,
                                    commit_info=commit_info,
                                    match_context={
                                        "search_pattern": content_pattern,
                                        "file_path": file_path,
                                        "line_number": match.get("line_number"),
                                        "column_start": match.get("column_start"),
                                        "column_end": match.get("column_end"),
                                    },
                                    search_time_ms=None,
                                )

                                results_found += 1
                                yield result

                        except (UnicodeDecodeError, AttributeError):
                            # Skip binary files or files with encoding issues
                            continue

                if commits_searched % 20 == 0:
                    progress = min(commits_searched / 200, 0.9)
                    self._report_progress(
                        context,
                        f"Searched {commits_searched} commits, {files_searched} files, found {results_found} matches",
                        progress,
                    )

        except Exception as e:
            self._report_progress(
                context, f"Error searching content: {e}", 1.0)

        finally:
            self._update_metrics(
                total_commits_searched=commits_searched,
                total_files_searched=files_searched,
                total_results_found=results_found,
            )
            self._report_progress(
                context, f"Content search completed: {results_found} matches", 1.0
            )

    def _should_search_file(self, file_path: str, query: SearchQuery) -> bool:
        """Check if file should be searched based on filters."""
        # Check include globs
        if query.include_globs:
            if not any(fnmatch.fnmatch(file_path, pattern) for pattern in query.include_globs):
                return False

        # Check exclude globs
        if query.exclude_globs:
            if any(fnmatch.fnmatch(file_path, pattern) for pattern in query.exclude_globs):
                return False

        # Check file extensions
        if query.file_extensions:
            file_ext = Path(file_path).suffix.lower()
            normalized_extensions = [
                ext if ext.startswith(".") else "." + ext for ext in query.file_extensions
            ]
            if file_ext not in [ext.lower() for ext in normalized_extensions]:
                return False

        return True

    async def _search_content_with_ripgrep(
        self, content: bytes, pattern: str, query: SearchQuery
    ) -> list[dict]:
        """Search content using ripgrep and return structured results."""
        rg_args = ["rg", "--json", pattern, "-"]

        if not query.case_sensitive:
            rg_args.append("-i")

        try:
            process = subprocess.run(
                rg_args, input=content, capture_output=True, check=True, text=True
            )

            results: list[Any] = []
            for line in process.stdout.strip().split("\n"):
                if not line:
                    continue

                try:
                    match = json.loads(line)
                    if match["type"] == "match":
                        data = match["data"]
                        results.append(
                            {
                                "line_number": data["line_number"],
                                "text": data["lines"]["text"].strip(),
                                "column_start": data.get("submatches", [{}])[0].get("start", 0),
                                "column_end": data.get("submatches", [{}])[0].get("end", 0),
                            }
                        )
                except (json.JSONDecodeError, KeyError):
                    continue

            return results

        except (subprocess.CalledProcessError, FileNotFoundError):
            return []

    def _calculate_relevance_score(self, match: dict, pattern: str, file_path: str) -> float:
        """Calculate relevance score for a content match."""
        score = 0.5  # Base score

        # Boost score for exact matches
        if pattern.lower() in match.get("text", "").lower():
            score += 0.3

        # Boost score for matches in important file types
        important_extensions = [".py", ".js", ".java",
                                ".cpp", ".c", ".h", ".md", ".txt"]
        if any(file_path.endswith(ext) for ext in important_extensions):
            score += 0.1

        # Boost score for matches in file names vs deep paths
        path_depth = len(Path(file_path).parts)
        if path_depth <= 3:
            score += 0.1

        return min(score, 1.0)
