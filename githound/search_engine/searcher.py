"""Advanced multi-criteria searchers for GitHound."""

import asyncio
import re
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any, Awaitable, Callable, Literal, Pattern

try:
    from rapidfuzz import fuzz
except ImportError:
    # Use mock for testing when rapidfuzz is not available
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    import mock_rapidfuzz

    fuzz = mock_rapidfuzz.fuzz  # type: ignore[assignment]

from ..models import CommitInfo, SearchQuery, SearchResult, SearchType
from .base import CacheableSearcher, ParallelSearcher, SearchContext


class AdvancedSearcher(CacheableSearcher, ParallelSearcher):
    """Advanced searcher for complex multi-criteria searches with logical operators."""

    def __init__(self, max_workers: int = 4) -> None:
        CacheableSearcher.__init__(self, "advanced", "advanced")
        ParallelSearcher.__init__(self, "advanced", max_workers)
        self._search_operators = {
            "AND": self._and_operation,
            "OR": self._or_operation,
            "NOT": self._not_operation,
        }

    async def can_handle(self, query: SearchQuery) -> bool:
        """Check if this searcher can handle complex queries."""
        # Handle queries with multiple criteria
        criteria_count = sum(
            [
                bool(query.content_pattern),
                bool(query.author_pattern),
                bool(query.message_pattern),
                bool(query.file_path_pattern),
                bool(query.commit_hash),
                bool(query.date_from or query.date_to),
            ]
        )
        return criteria_count >= 2

    async def estimate_work(self, context: SearchContext) -> int:
        """Estimate work based on query complexity."""
        try:
            branch = context.branch or context.repo.active_branch.name
            commits = list(context.repo.iter_commits(branch, max_count=2000))
            # Complex searches require more work
            complexity_multiplier = self._calculate_complexity(context.query)
            return min(len(commits) * complexity_multiplier, 5000)
        except Exception:
            return 1000

    def _calculate_complexity(self, query: SearchQuery) -> int:
        """Calculate query complexity factor."""
        complexity = 1
        if query.content_pattern:
            complexity += 2
        if query.fuzzy_search:
            complexity += 1
        if query.file_path_pattern:
            complexity += 1
        if query.author_pattern:
            complexity += 1
        if query.message_pattern:
            complexity += 1
        return min(complexity, 5)

    async def search(self, context: SearchContext) -> AsyncGenerator[SearchResult, None]:
        """Perform advanced multi-criteria search."""
        query = context.query
        self._report_progress(context, "Starting advanced search...", 0.0)

        # Check cache first
        cache_key = self._get_cache_key(context, "advanced_search")
        cached_results = await self._get_from_cache(context, cache_key)
        if cached_results:
            self._report_progress(context, "Using cached results", 1.0)
            for result in cached_results:
                yield result
            return

        # Perform multi-criteria search
        results: list[SearchResult] = []
        async for result in self._perform_multi_criteria_search(context):
            results.append(result)
            yield result

        # Cache results
        await self._set_cache(context, cache_key, results)
        self._report_progress(context, "Advanced search completed", 1.0)

    async def _perform_multi_criteria_search(
        self, context: SearchContext
    ) -> AsyncGenerator[SearchResult, None]:
        """Perform the actual multi-criteria search."""
        query = context.query
        branch = context.branch or context.repo.active_branch.name

        # Create search tasks for different criteria
        search_tasks = []

        if query.content_pattern:
            search_tasks.append(self._search_content_criteria)
        if query.author_pattern:
            search_tasks.append(self._search_author_criteria)
        if query.message_pattern:
            search_tasks.append(self._search_message_criteria)
        if query.file_path_pattern:
            search_tasks.append(self._search_file_criteria)
        if query.date_from or query.date_to:
            search_tasks.append(self._search_date_criteria)

        # Execute searches in parallel
        task_lambdas: list[Callable[[], Awaitable[list[SearchResult]]]] = [
            lambda task=task: task(context) for task in search_tasks  # type: ignore[misc]
        ]
        task_results = await self._run_parallel(task_lambdas, context)

        # Combine results using logical operations
        combined_results = self._combine_search_results(task_results, query)

        # Sort by relevance and yield
        combined_results.sort(key=lambda r: r.relevance_score, reverse=True)
        for result in combined_results:
            yield result

    async def _search_content_criteria(self, context: SearchContext) -> list[SearchResult]:
        """Search based on content criteria."""
        results: list[SearchResult] = []
        query = context.query
        branch = context.branch or context.repo.active_branch.name

        if not query.content_pattern:
            return results

        try:
            # Use ripgrep for fast content search
            import json
            import subprocess

            cmd = ["rg", "--json", "--line-number", "--no-heading", "--max-filesize", "10M"]

            if not query.case_sensitive:
                cmd.append("--ignore-case")

            cmd.extend([query.content_pattern, str(context.repo.working_dir)])

            process = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if process.returncode == 0:
                for line in process.stdout.strip().split("\n"):
                    if line:
                        try:
                            data = json.loads(line)
                            if data.get("type") == "match":
                                # Get commit info for this file
                                file_path = data["data"]["path"]["text"]
                                line_number = data["data"]["line_number"]
                                matching_line = data["data"]["lines"]["text"]

                                # Find the most recent commit for this file
                                commits = list(
                                    context.repo.iter_commits(branch, paths=file_path, max_count=1)
                                )

                                if commits:
                                    commit = commits[0]
                                    commit_info = self._create_commit_info(commit)

                                    result = SearchResult(
                                        commit_hash=commit.hexsha,
                                        file_path=file_path,
                                        line_number=line_number,
                                        matching_line=matching_line.strip(),
                                        commit_info=commit_info,
                                        search_type=SearchType.CONTENT,
                                        relevance_score=self._calculate_content_relevance(
                                            matching_line, query.content_pattern
                                        ),
                                        match_context={
                                            "search_criteria": "content",
                                            "pattern": query.content_pattern,
                                        },
                                    )
                                    results.append(result)
                        except (json.JSONDecodeError, KeyError):
                            continue

        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
            # Fallback to manual search if ripgrep fails
            results.extend(await self._manual_content_search(context))

        self._update_metrics(total_files_searched=len(results))
        return results

    async def _search_author_criteria(self, context: SearchContext) -> list[SearchResult]:
        """Search based on author criteria."""
        results: list[SearchResult] = []
        query = context.query
        branch = context.branch or context.repo.active_branch.name

        if not query.author_pattern:
            return results

        commits_processed = 0
        for commit in context.repo.iter_commits(branch):
            commits_processed += 1
            if commits_processed > 2000:  # Limit for performance
                break

            author_match = self._match_author(commit, query.author_pattern, query.fuzzy_search)
            if author_match:
                commit_info = self._create_commit_info(commit)

                # Create result for each file in the commit
                for file_path in commit.stats.files:
                    result = SearchResult(
                        commit_hash=commit.hexsha,
                        file_path=file_path,
                        line_number=None,
                        matching_line=None,
                        commit_info=commit_info,
                        search_type=SearchType.AUTHOR,
                        relevance_score=author_match,
                        match_context={
                            "search_criteria": "author",
                            "pattern": query.author_pattern,
                            "matched_author": f"{commit.author.name} <{commit.author.email}>",
                        },
                    )
                    results.append(result)

        self._update_metrics(total_commits_searched=commits_processed)
        return results

    async def _search_message_criteria(self, context: SearchContext) -> list[SearchResult]:
        """Search based on commit message criteria."""
        results: list[SearchResult] = []
        query = context.query
        branch = context.branch or context.repo.active_branch.name

        if not query.message_pattern:
            return results

        commits_processed = 0
        for commit in context.repo.iter_commits(branch):
            commits_processed += 1
            if commits_processed > 2000:  # Limit for performance
                break

            message_match = self._match_message(commit, query.message_pattern, query.fuzzy_search)
            if message_match:
                commit_info = self._create_commit_info(commit)

                # Create result for each file in the commit
                for file_path in commit.stats.files:
                    result = SearchResult(
                        commit_hash=commit.hexsha,
                        file_path=file_path,
                        line_number=None,
                        matching_line=commit.message.strip(),
                        commit_info=commit_info,
                        search_type=SearchType.MESSAGE,
                        relevance_score=message_match,
                        match_context={
                            "search_criteria": "message",
                            "pattern": query.message_pattern,
                            "matched_message": commit.message.strip(),
                        },
                    )
                    results.append(result)

        self._update_metrics(total_commits_searched=commits_processed)
        return results

    async def _search_file_criteria(self, context: SearchContext) -> list[SearchResult]:
        """Search based on file path criteria."""
        results: list[SearchResult] = []
        query = context.query
        branch = context.branch or context.repo.active_branch.name

        if not query.file_path_pattern:
            return results

        # Compile regex pattern
        try:
            flags = 0 if query.case_sensitive else re.IGNORECASE
            regex_pattern = re.compile(query.file_path_pattern, flags)
        except re.error:
            # Fallback to glob-style matching
            regex_pattern = None

        commits_processed = 0
        for commit in context.repo.iter_commits(branch):
            commits_processed += 1
            if commits_processed > 2000:  # Limit for performance
                break

            for file_path in commit.stats.files:
                file_match = self._match_file_path(
                    file_path, query.file_path_pattern, regex_pattern
                )
                if file_match:
                    commit_info = self._create_commit_info(commit)

                    result = SearchResult(
                        commit_hash=commit.hexsha,
                        file_path=file_path,
                        line_number=None,
                        matching_line=None,
                        commit_info=commit_info,
                        search_type=SearchType.FILE_PATH,
                        relevance_score=file_match,
                        match_context={
                            "search_criteria": "file_path",
                            "pattern": query.file_path_pattern,
                            "matched_path": file_path,
                        },
                    )
                    results.append(result)

        self._update_metrics(total_commits_searched=commits_processed)
        return results

    async def _search_date_criteria(self, context: SearchContext) -> list[SearchResult]:
        """Search based on date criteria."""
        results: list[SearchResult] = []
        query = context.query
        branch = context.branch or context.repo.active_branch.name

        if not (query.date_from or query.date_to):
            return results

        commits_processed = 0
        for commit in context.repo.iter_commits(branch):
            commits_processed += 1
            if commits_processed > 2000:  # Limit for performance
                break

            commit_date = datetime.fromtimestamp(commit.committed_date)
            date_match = self._match_date_range(commit_date, query.date_from, query.date_to)

            if date_match:
                commit_info = self._create_commit_info(commit)

                # Create result for each file in the commit
                for file_path in commit.stats.files:
                    result = SearchResult(
                        commit_hash=commit.hexsha,
                        file_path=file_path,
                        line_number=None,
                        matching_line=None,
                        commit_info=commit_info,
                        search_type=SearchType.DATE_RANGE,
                        relevance_score=date_match,
                        match_context={
                            "search_criteria": "date_range",
                            "commit_date": commit_date.isoformat(),
                            "date_from": query.date_from.isoformat() if query.date_from else None,
                            "date_to": query.date_to.isoformat() if query.date_to else None,
                        },
                    )
                    results.append(result)

        self._update_metrics(total_commits_searched=commits_processed)
        return results

    def _combine_search_results(
        self, task_results: list[list[SearchResult]], query: SearchQuery
    ) -> list[SearchResult]:
        """Combine results from multiple search criteria using logical operations."""
        if not task_results:
            return []

        # For now, implement AND logic (intersection of results)
        # Future enhancement: support OR, NOT operations based on query syntax
        if len(task_results) == 1:
            return task_results[0]

        # Find intersection based on commit_hash + file_path
        result_keys = set()
        combined_results: list[SearchResult] = []

        # Start with first result set
        first_results = task_results[0]
        for result in first_results:
            key = (result.commit_hash, str(result.file_path))
            result_keys.add(key)
            combined_results.append(result)

        # Intersect with other result sets
        for other_results in task_results[1:]:
            other_keys = {(r.commit_hash, str(r.file_path)) for r in other_results}
            result_keys = result_keys.intersection(other_keys)

        # Filter to only include intersected results
        final_results = [
            r for r in combined_results if (r.commit_hash, str(r.file_path)) in result_keys
        ]

        # Boost relevance scores for results that match multiple criteria
        for result in final_results:
            result.relevance_score = min(result.relevance_score * 1.2, 1.0)

        return final_results

    def _create_commit_info(self, commit: Any) -> CommitInfo:
        """Create CommitInfo from git commit object."""
        return CommitInfo(
            hash=commit.hexsha,
            short_hash=commit.hexsha[:8],
            author_name=commit.author.name,
            author_email=commit.author.email,
            committer_name=commit.committer.name,
            committer_email=commit.committer.email,
            message=commit.message.strip(),
            date=datetime.fromtimestamp(commit.committed_date),
            files_changed=len(commit.stats.files),
            insertions=commit.stats.total.get("insertions", 0),
            deletions=commit.stats.total.get("deletions", 0),
            parents=[parent.hexsha for parent in commit.parents],
        )

    def _match_author(self, commit: Any, pattern: str, fuzzy: bool = False) -> float:
        """Match author against pattern."""
        author_text = f"{commit.author.name} {commit.author.email}".lower()
        pattern_lower = pattern.lower()

        if fuzzy:
            # Use fuzzy matching
            similarity = fuzz.partial_ratio(pattern_lower, author_text) / 100.0
            return similarity if similarity >= 0.6 else 0.0
        else:
            # Exact substring match
            return 1.0 if pattern_lower in author_text else 0.0

    def _match_message(self, commit: Any, pattern: str, fuzzy: bool = False) -> float:
        """Match commit message against pattern."""
        message = commit.message.strip().lower()
        pattern_lower = pattern.lower()

        if fuzzy:
            # Use fuzzy matching
            similarity = fuzz.partial_ratio(pattern_lower, message) / 100.0
            return similarity if similarity >= 0.6 else 0.0
        else:
            # Try regex first, fallback to substring
            try:
                if re.search(pattern, message, re.IGNORECASE):
                    return 1.0
            except re.error:
                pass
            return 1.0 if pattern_lower in message else 0.0

    def _match_file_path(
        self, file_path: str, pattern: str, regex_pattern: Pattern[str] | None = None
    ) -> float:
        """Match file path against pattern."""
        if regex_pattern:
            return 1.0 if regex_pattern.search(file_path) else 0.0
        else:
            # Fallback to glob-style matching
            import fnmatch

            return 1.0 if fnmatch.fnmatch(file_path, pattern) else 0.0

    def _match_date_range(
        self, commit_date: datetime, date_from: datetime | None, date_to: datetime | None
    ) -> float:
        """Match commit date against date range."""
        if date_from and commit_date < date_from:
            return 0.0
        if date_to and commit_date > date_to:
            return 0.0
        return 1.0

    def _calculate_content_relevance(self, matching_line: str, pattern: str) -> float:
        """Calculate relevance score for content matches."""
        # Simple relevance based on pattern length vs line length
        if not matching_line or not pattern:
            return 0.5

        pattern_ratio = len(pattern) / len(matching_line)
        # Higher score for patterns that match a significant portion of the line
        return min(0.5 + pattern_ratio, 1.0)

    async def _manual_content_search(self, context: SearchContext) -> list[SearchResult]:
        """Fallback manual content search when ripgrep is not available."""
        results: list[SearchResult] = []
        query = context.query
        branch = context.branch or context.repo.active_branch.name

        if not query.content_pattern:
            return results

        try:
            # Compile regex pattern
            flags = 0 if query.case_sensitive else re.IGNORECASE
            regex_pattern = re.compile(query.content_pattern, flags)
        except re.error:
            # Fallback to simple string search
            regex_pattern = None

        commits_processed = 0
        for commit in context.repo.iter_commits(branch):
            commits_processed += 1
            if commits_processed > 500:  # Limit for manual search
                break

            for file_path in commit.stats.files:
                try:
                    # Get file content at this commit
                    file_content = (
                        commit.tree[file_path].data_stream.read().decode("utf-8", errors="ignore")
                    )
                    lines = file_content.split("\n")

                    for line_num, line in enumerate(lines, 1):
                        match = False
                        if regex_pattern:
                            match = bool(regex_pattern.search(line))
                        else:
                            pattern_check = (
                                query.content_pattern.lower()
                                if not query.case_sensitive
                                else query.content_pattern
                            )
                            line_check = line.lower() if not query.case_sensitive else line
                            match = pattern_check in line_check

                        if match:
                            commit_info = self._create_commit_info(commit)

                            result = SearchResult(
                                commit_hash=commit.hexsha,
                                file_path=file_path,
                                line_number=line_num,
                                matching_line=line.strip(),
                                commit_info=commit_info,
                                search_type=SearchType.CONTENT,
                                relevance_score=self._calculate_content_relevance(
                                    line, query.content_pattern
                                ),
                                match_context={
                                    "search_criteria": "content",
                                    "pattern": query.content_pattern,
                                    "manual_search": True,
                                },
                            )
                            results.append(result)

                except (UnicodeDecodeError, KeyError, AttributeError):
                    # Skip files that can't be read or don't exist
                    continue

        return results

    # Logical operation methods for future enhancement
    async def _and_operation(
        self, results_a: list[SearchResult], results_b: list[SearchResult]
    ) -> list[SearchResult]:
        """Perform AND operation on two result sets."""
        keys_a = {(r.commit_hash, str(r.file_path)) for r in results_a}
        return [r for r in results_b if (r.commit_hash, str(r.file_path)) in keys_a]

    async def _or_operation(
        self, results_a: list[SearchResult], results_b: list[SearchResult]
    ) -> list[SearchResult]:
        """Perform OR operation on two result sets."""
        combined = results_a.copy()
        existing_keys = {(r.commit_hash, str(r.file_path)) for r in results_a}

        for result in results_b:
            key = (result.commit_hash, str(result.file_path))
            if key not in existing_keys:
                combined.append(result)
                existing_keys.add(key)

        return combined

    async def _not_operation(
        self, results_a: list[SearchResult], results_b: list[SearchResult]
    ) -> list[SearchResult]:
        """Perform NOT operation (A - B)."""
        keys_b = {(r.commit_hash, str(r.file_path)) for r in results_b}
        return [r for r in results_a if (r.commit_hash, str(r.file_path)) not in keys_b]
