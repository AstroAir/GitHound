"""Diff analysis searchers for GitHound."""

import asyncio
import re
from collections import defaultdict
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from ..models import CommitInfo, SearchQuery, SearchResult, SearchType
from .base import CacheableSearcher, SearchContext


class DiffSearcher(CacheableSearcher):
    """Searcher for analyzing diffs and changes between commits."""

    def __init__(self) -> None:
        super().__init__("diff", "diff")

        # Patterns for different types of changes
        self.change_patterns = {
            "function_added": r"^\+.*def\s+(\w+)\s*\(",
            "function_removed": r"^\-.*def\s+(\w+)\s*\(",
            "class_added": r"^\+.*class\s+(\w+)\s*[\(:]",
            "class_removed": r"^\-.*class\s+(\w+)\s*[\(:]",
            "import_added": r"^\+.*(?:import|from)\s+(\S+)",
            "import_removed": r"^\-.*(?:import|from)\s+(\S+)",
            "comment_added": r"^\+.*#\s*(.+)",
            "comment_removed": r"^\-.*#\s*(.+)",
            "todo_added": r"^\+.*(?:#.*)?(?:TODO|FIXME|XXX|HACK)\s*:?\s*(.+)",
            "todo_removed": r"^\-.*(?:#.*)?(?:TODO|FIXME|XXX|HACK)\s*:?\s*(.+)",
        }

    async def can_handle(self, query: SearchQuery) -> bool:
        """Check if this searcher can handle diff-related queries."""
        # Handle queries that mention diffs, changes, or evolution
        return (
            (hasattr(query, "diff_analysis") and bool(query.diff_analysis))
            or (hasattr(query, "change_analysis") and bool(query.change_analysis))
            or (hasattr(query, "commit_range") and bool(query.commit_range))
            or any(
                keyword in (query.text or "").lower()
                for keyword in ["diff", "change", "evolution", "modified"]
            )
        )

    async def estimate_work(self, context: SearchContext) -> int:
        """Estimate work based on recent commits."""
        try:
            # Estimate based on recent commits (last 100)
            commits = list(context.repo.iter_commits(max_count=100))
            return min(len(commits) * 3, 400)  # Estimate 3 units per commit
        except Exception:
            return 100

    async def search(self, context: SearchContext) -> AsyncGenerator[SearchResult, None]:
        """Perform diff analysis."""
        self._report_progress(context, "Starting diff analysis...", 0.0)

        # Check cache first
        cache_key = self._get_cache_key(context, "diff_analysis")
        cached_results = await self._get_from_cache(context, cache_key)
        if cached_results:
            self._report_progress(context, "Using cached diff results", 1.0)
            for result in cached_results:
                yield result
            return

        # Perform diff analysis
        results: List[SearchResult] = []

        # Analyze recent changes
        self._report_progress(context, "Analyzing recent changes...", 0.2)
        recent_results = await self._analyze_recent_changes(context)
        results.extend(recent_results)

        # Analyze change patterns
        self._report_progress(context, "Analyzing change patterns...", 0.5)
        pattern_results = await self._analyze_change_patterns(context)
        results.extend(pattern_results)

        # Analyze file evolution
        self._report_progress(context, "Analyzing file evolution...", 0.8)
        evolution_results = await self._analyze_file_evolution(context)
        results.extend(evolution_results)

        # Cache results
        await self._set_cache(context, cache_key, results)

        # Yield results
        for result in results:
            yield result

        self._report_progress(context, "Diff analysis completed", 1.0)

    async def _analyze_recent_changes(self, context: SearchContext) -> List[SearchResult]:
        """Analyze recent changes in the repository."""
        results: List[SearchResult] = []

        try:
            # Fetch recent commits for analysis (limit to 20 for memory efficiency)
            commits = list(context.repo.iter_commits(max_count=20))

            if not commits:
                return results

            # Process commits for change analysis (limit to 10 for performance optimization)
            for i, commit in enumerate(commits[:10]):
                try:
                    # Skip merge commits as they don't represent direct code changes
                    if len(commit.parents) > 1:
                        continue

                    # Generate diff between commit and its parent
                    if commit.parents:
                        # Standard commit with parent - compare against first parent
                        diff = commit.parents[0].diff(commit)
                    else:
                        # Initial commit has no parent - compare against empty tree
                        diff = commit.diff(None)

                    # Extract and analyze change statistics from the diff
                    change_summary = self._analyze_commit_diff(diff)

                    # Only include commits that actually contain changes
                    if change_summary["total_changes"] > 0:
                        commit_info = self._create_commit_info(commit)

                        result = SearchResult(
                            commit_hash=commit.hexsha,
                            file_path=f"diffs/commit_{commit.hexsha[:8]}.txt",
                            line_number=1,
                            matching_line=f"Commit changes: {change_summary['files_changed']} files, +{change_summary['insertions']} -{change_summary['deletions']}",
                            commit_info=commit_info,
                            search_type=SearchType.COMBINED,
                            # Assign higher relevance scores to more recent commits (decay by 5% per position)
                            relevance_score=1.0 - (i * 0.05),
                            match_context={
                                "analysis_type": "commit_changes",
                                "change_summary": change_summary,
                                "commit_rank": i + 1,  # 1-based ranking for display purposes
                            },
                        )
                        results.append(result)

                except Exception:
                    continue

            # Add summary of recent activity
            if results:
                total_files = sum(
                    r.match_context["change_summary"]["files_changed"]
                    for r in results
                    if r.match_context
                )
                total_insertions = sum(
                    r.match_context["change_summary"]["insertions"]
                    for r in results
                    if r.match_context
                )
                total_deletions = sum(
                    r.match_context["change_summary"]["deletions"]
                    for r in results
                    if r.match_context
                )

                summary_result = SearchResult(
                    commit_hash="diff_analysis",
                    file_path="diffs/recent_summary.txt",
                    line_number=1,
                    matching_line=f"Recent activity: {len(results)} commits, {total_files} files changed, +{total_insertions} -{total_deletions}",
                    commit_info=None,
                    search_type=SearchType.COMBINED,
                    relevance_score=1.0,
                    match_context={
                        "analysis_type": "recent_summary",
                        "commits_analyzed": len(results),
                        "total_files": total_files,
                        "total_insertions": total_insertions,
                        "total_deletions": total_deletions,
                    },
                )
                results.append(summary_result)

        except Exception as e:
            # Error handling
            result = SearchResult(
                commit_hash="diff_analysis",
                file_path="diffs/error.txt",
                line_number=1,
                matching_line=f"Error analyzing recent changes: {str(e)}",
                commit_info=None,
                search_type=SearchType.COMBINED,
                relevance_score=0.5,
                match_context={"analysis_type": "diff_error", "error": str(e)},
            )
            results.append(result)

        return results

    async def _analyze_change_patterns(self, context: SearchContext) -> List[SearchResult]:
        """Analyze patterns in code changes."""
        results: List[SearchResult] = []

        try:
            # Get recent commits for pattern analysis
            commits = list(context.repo.iter_commits(max_count=50))

            # Track patterns across commits
            pattern_counts = defaultdict(list)

            for commit in commits[:20]:  # Limit for performance
                try:
                    if len(commit.parents) > 1:  # Skip merge commits
                        continue

                    # Get diff
                    if commit.parents:
                        diff = commit.parents[0].diff(commit)
                    else:
                        continue

                    # Analyze patterns in this commit
                    commit_patterns = self._find_change_patterns(diff)

                    for pattern_type, matches in commit_patterns.items():
                        if matches:
                            pattern_counts[pattern_type].extend(matches)

                except Exception:
                    continue

            # Create results for significant patterns
            for pattern_type, matches in pattern_counts.items():
                if len(matches) >= 2:  # Only show patterns that appear multiple times

                    # Get a representative example
                    example_match = matches[0]

                    result = SearchResult(
                        commit_hash="pattern_analysis",
                        file_path=f"patterns/{pattern_type}.txt",
                        line_number=1,
                        matching_line=f"Pattern '{pattern_type}': {len(matches)} occurrences",
                        commit_info=None,
                        search_type=SearchType.COMBINED,
                        relevance_score=min(len(matches) * 0.1, 1.0),
                        match_context={
                            "analysis_type": "change_pattern",
                            "pattern_type": pattern_type,
                            "occurrence_count": len(matches),
                            "example": example_match,
                            "all_matches": matches[:5],  # Limit examples
                        },
                    )
                    results.append(result)

        except Exception:
            pass

        return results

    async def _analyze_file_evolution(self, context: SearchContext) -> List[SearchResult]:
        """Analyze how files have evolved over time."""
        results: List[SearchResult] = []

        try:
            # Get recent commits
            commits = list(context.repo.iter_commits(max_count=30))

            # Track file changes
            file_changes = defaultdict(list)

            for commit in commits:
                try:
                    if len(commit.parents) > 1:  # Skip merge commits
                        continue

                    # Get diff
                    if commit.parents:
                        diff = commit.parents[0].diff(commit)
                    else:
                        continue

                    # Track changes per file
                    for diff_item in diff:
                        if diff_item.a_path:
                            file_path = diff_item.a_path
                        elif diff_item.b_path:
                            file_path = diff_item.b_path
                        else:
                            continue

                        change_info = {
                            "commit": commit.hexsha[:8],
                            "date": datetime.fromtimestamp(commit.committed_date),
                            "change_type": diff_item.change_type,
                            "insertions": (
                                diff_item.insertions if hasattr(diff_item, "insertions") else 0
                            ),
                            "deletions": (
                                diff_item.deletions if hasattr(diff_item, "deletions") else 0
                            ),
                        }

                        file_changes[file_path].append(change_info)

                except Exception:
                    continue

            # Find files with significant evolution
            for file_path, changes in file_changes.items():
                if len(changes) >= 3:  # Files changed in at least 3 commits

                    total_insertions = sum(c["insertions"] for c in changes)
                    total_deletions = sum(c["deletions"] for c in changes)

                    # Get the most recent change
                    recent_change = max(changes, key=lambda c: c["date"])

                    result = SearchResult(
                        commit_hash=recent_change["commit"],
                        file_path=file_path,
                        line_number=1,
                        matching_line=f"File evolution: {len(changes)} changes, +{total_insertions} -{total_deletions}",
                        commit_info=None,
                        search_type=SearchType.COMBINED,
                        relevance_score=min(len(changes) * 0.15, 1.0),
                        match_context={
                            "analysis_type": "file_evolution",
                            "file_path": file_path,
                            "change_count": len(changes),
                            "total_insertions": total_insertions,
                            "total_deletions": total_deletions,
                            "recent_changes": changes[:3],  # Most recent 3 changes
                        },
                    )
                    results.append(result)

        except Exception:
            pass

        return results

    def _analyze_commit_diff(self, diff: Any) -> Dict[str, int]:
        """Analyze a commit's diff and return summary statistics."""
        summary = {
            "files_changed": 0,
            "insertions": 0,
            "deletions": 0,
            "total_changes": 0,
        }

        try:
            for diff_item in diff:
                summary["files_changed"] += 1

                if hasattr(diff_item, "insertions") and diff_item.insertions:
                    summary["insertions"] += diff_item.insertions
                if hasattr(diff_item, "deletions") and diff_item.deletions:
                    summary["deletions"] += diff_item.deletions

            summary["total_changes"] = summary["insertions"] + summary["deletions"]

        except Exception:
            pass

        return summary

    def _find_change_patterns(self, diff: Any) -> Dict[str, List[str]]:
        """Find specific patterns in diff content."""
        patterns_found = defaultdict(list)

        try:
            for diff_item in diff:
                if not diff_item.diff:
                    continue

                # Get diff content as string
                try:
                    diff_content = diff_item.diff.decode("utf-8", errors="ignore")
                except (AttributeError, UnicodeDecodeError):
                    continue

                # Search for patterns
                for pattern_name, pattern_regex in self.change_patterns.items():
                    matches = re.findall(pattern_regex, diff_content, re.MULTILINE)
                    if matches:
                        patterns_found[pattern_name].extend(matches)

        except Exception:
            pass

        return patterns_found

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
