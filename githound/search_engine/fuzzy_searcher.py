"""Fuzzy search capabilities for GitHound."""

from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any

try:
    from rapidfuzz import fuzz, process
except ImportError:
    # Use mock for testing when rapidfuzz is not available
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    import mock_rapidfuzz
    fuzz = mock_rapidfuzz.fuzz  # type: ignore[assignment]
    process = mock_rapidfuzz.process  # type: ignore[assignment]

from ..models import CommitInfo, SearchQuery, SearchResult, SearchType
from .base import CacheableSearcher, SearchContext


class FuzzySearcher(CacheableSearcher):
    """Advanced fuzzy searcher that combines multiple search types with fuzzy matching."""

    def __init__(self) -> None:
        super().__init__("fuzzy", "fuzzy")
        self._author_cache: dict[str, list[dict[str, Any]]] = {}
        self._message_cache: dict[str, list[dict[str, Any]]] = {}

    async def can_handle(self, query: SearchQuery) -> bool:
        """Check if this searcher can handle the query."""
        return query.fuzzy_search and (
            query.author_pattern is not None
            or query.message_pattern is not None
            or query.content_pattern is not None
        )

    async def estimate_work(self, context: SearchContext) -> int:
        """Estimate work based on repository size."""
        try:
            branch = context.branch or context.repo.active_branch.name
            commits = list(context.repo.iter_commits(branch, max_count=1000))
            return min(len(commits), 1000)
        except:
            return 200

    async def search(self, context: SearchContext) -> AsyncGenerator[SearchResult, None]:
        """Perform fuzzy search across multiple dimensions."""
        query = context.query

        if not query.fuzzy_search:
            return

        self._report_progress(context, "Starting fuzzy search...", 0.0)

        # Build search targets from repository
        search_targets = await self._build_search_targets(context)

        # Perform fuzzy matching for each search type
        results = []

        if query.author_pattern:
            author_results = await self._fuzzy_search_authors(
                query.author_pattern, search_targets, query.fuzzy_threshold
            )
            results.extend(author_results)

        if query.message_pattern:
            message_results = await self._fuzzy_search_messages(
                query.message_pattern, search_targets, query.fuzzy_threshold
            )
            results.extend(message_results)

        if query.content_pattern:
            content_results = await self._fuzzy_search_content(
                query.content_pattern, search_targets, query.fuzzy_threshold
            )
            results.extend(content_results)

        # Sort by relevance score and yield results
        results.sort(key=lambda r: r.relevance_score, reverse=True)

        for result in results:
            yield result

        self._update_metrics(
            total_commits_searched=len(search_targets), total_results_found=len(results)
        )
        self._report_progress(
            context, f"Fuzzy search completed: {len(results)} matches", 1.0)

    async def _build_search_targets(self, context: SearchContext) -> list[dict]:
        """Build a list of search targets from the repository."""
        targets = []
        branch = context.branch or context.repo.active_branch.name

        self._report_progress(context, "Building search index...", 0.1)

        commits_processed = 0
        for commit in context.repo.iter_commits(branch):
            commits_processed += 1

            # Create commit info
            commit_info = CommitInfo(
                hash=commit.hexsha,
                short_hash=commit.hexsha[:8],
                author_name=commit.author.name,
                author_email=commit.author.email,
                committer_name=commit.committer.name,
                committer_email=commit.committer.email,
                message=commit.message.strip(),
                date=datetime.fromtimestamp(commit.committed_date),
                files_changed=len(commit.stats.files),
                insertions=commit.stats.total["insertions"],
                deletions=commit.stats.total["deletions"],
                parents=[parent.hexsha for parent in commit.parents],
            )

            # Get file content for content search
            file_contents = []
            for parent in commit.parents:
                diffs = commit.diff(parent)
                for diff in diffs:
                    if diff.b_blob is None or diff.b_path is None:
                        continue

                    try:
                        content = diff.b_blob.data_stream.read().decode("utf-8", errors="ignore")
                        file_contents.append(
                            {"path": diff.b_path, "content": content})
                    except (UnicodeDecodeError, AttributeError):
                        continue

            targets.append(
                {"commit": commit, "commit_info": commit_info,
                    "file_contents": file_contents}
            )

            # Limit to prevent memory issues
            if commits_processed >= 1000:
                break

            if commits_processed % 100 == 0:
                progress = 0.1 + (commits_processed / 1000) * \
                    0.2  # 10-30% progress
                self._report_progress(
                    context, f"Indexed {commits_processed} commits", progress)

        return targets

    async def _fuzzy_search_authors(
        self, pattern: str, targets: list[dict], threshold: float
    ) -> list[SearchResult]:
        """Perform fuzzy search on author names and emails."""
        results = []

        # Extract all unique authors
        authors = set()
        author_to_commits: dict[str, list[dict[str, Any]]] = {}

        for target in targets:
            commit_info = target["commit_info"]
            author_key = f"{commit_info.author_name} <{commit_info.author_email}>"
            authors.add(author_key)

            if author_key not in author_to_commits:
                author_to_commits[author_key] = []
            author_to_commits[author_key].append(target)

        # Perform fuzzy matching
        matches = process.extract(
            pattern, list(authors), scorer=fuzz.partial_ratio, score_cutoff=threshold * 100
        )

        for match, score, _ in matches:
            relevance_score = score / 100.0

            # Create results for all commits by this author
            for target in author_to_commits[match]:
                result = SearchResult(
                    commit_hash=target["commit_info"].hash,
                    file_path=target["commit"].repo.working_dir,
                    line_number=None,
                    matching_line=None,
                    search_type=SearchType.AUTHOR,
                    relevance_score=relevance_score,
                    commit_info=target["commit_info"],
                    match_context={
                        "search_term": pattern,
                        "matched_author": match,
                        "fuzzy_score": score,
                    },
                    search_time_ms=None,
                )
                results.append(result)

        return results

    async def _fuzzy_search_messages(
        self, pattern: str, targets: list[dict], threshold: float
    ) -> list[SearchResult]:
        """Perform fuzzy search on commit messages."""
        results = []

        # Extract all commit messages
        messages = []
        message_to_target = {}

        for target in targets:
            message = target["commit_info"].message
            messages.append(message)
            message_to_target[message] = target

        # Perform fuzzy matching
        matches = process.extract(
            pattern, messages, scorer=fuzz.partial_ratio, score_cutoff=threshold * 100
        )

        for match, score, _ in matches:
            relevance_score = score / 100.0
            target = message_to_target[match]

            result = SearchResult(
                commit_hash=target["commit_info"].hash,
                file_path=target["commit"].repo.working_dir,
                line_number=None,
                matching_line=None,
                search_type=SearchType.MESSAGE,
                relevance_score=relevance_score,
                commit_info=target["commit_info"],
                match_context={
                    "search_term": pattern,
                    "matched_message": match,
                    "fuzzy_score": score,
                },
                search_time_ms=None,
            )
            results.append(result)

        return results

    async def _fuzzy_search_content(
        self, pattern: str, targets: list[dict], threshold: float
    ) -> list[SearchResult]:
        """Perform fuzzy search on file content."""
        results = []

        # Extract all content lines
        content_lines = []
        line_to_context = {}

        for target in targets:
            for file_content in target["file_contents"]:
                lines = file_content["content"].split("\n")
                for line_num, line in enumerate(lines, 1):
                    line = line.strip()
                    if len(line) > 10:  # Skip very short lines
                        content_lines.append(line)
                        line_to_context[line] = {
                            "target": target,
                            "file_path": file_content["path"],
                            "line_number": line_num,
                        }

        # Perform fuzzy matching (limit to prevent performance issues)
        if len(content_lines) > 10000:
            content_lines = content_lines[:10000]

        matches = process.extract(
            pattern,
            content_lines,
            scorer=fuzz.partial_ratio,
            score_cutoff=threshold * 100,
            limit=100,  # Limit results
        )

        for match, score, _ in matches:
            relevance_score = score / 100.0
            context = line_to_context[match]
            target = context["target"]

            result = SearchResult(
                commit_hash=target["commit_info"].hash,
                file_path=context["file_path"],
                line_number=context["line_number"],
                matching_line=match,
                search_type=SearchType.CONTENT,
                relevance_score=relevance_score,
                commit_info=target["commit_info"],
                match_context={
                    "search_term": pattern,
                    "matched_line": match,
                    "fuzzy_score": score,
                    "file_path": context["file_path"],
                },
                search_time_ms=None,
            )
            results.append(result)

        return results
