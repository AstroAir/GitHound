"""Enhanced search orchestrator with advanced optimizations.

This module extends the base orchestrator with performance monitoring,
query optimization, and intelligent result caching.
"""

import hashlib
import json
import time
from collections.abc import AsyncGenerator, Callable
from pathlib import Path
from typing import Any

from git import Repo

from ..models import SearchQuery, SearchResult
from .indexer import IncrementalIndexer
from .orchestrator import SearchOrchestrator
from .performance_monitor import BottleneckDetector, PerformanceMonitor, SearchProfiler
from .query_optimizer import QueryOptimizer, QueryPlanner


class EnhancedSearchOrchestrator(SearchOrchestrator):
    """Enhanced orchestrator with performance monitoring and optimization."""

    def __init__(self, enable_monitoring: bool = True, enable_optimization: bool = True) -> None:
        """Initialize enhanced orchestrator.

        Args:
            enable_monitoring: Enable performance monitoring
            enable_optimization: Enable query optimization
        """
        super().__init__()

        # Performance monitoring
        self.enable_monitoring = enable_monitoring
        self.monitor = PerformanceMonitor() if enable_monitoring else None
        self.profiler = SearchProfiler() if enable_monitoring else None
        self.bottleneck_detector = BottleneckDetector() if enable_monitoring else None

        # Query optimization
        self.enable_optimization = enable_optimization
        self.query_optimizer = QueryOptimizer() if enable_optimization else None
        self.query_planner = QueryPlanner() if enable_optimization else None

        # Indexing system
        self.indexer: IncrementalIndexer | None = None
        self.use_indexing = True

        # Result cache
        self.result_cache: dict[str, list[SearchResult]] = {}
        self.cache_max_size = 100

    def initialize_indexer(self, repo_path: Path, cache_dir: Path | None = None) -> None:
        """Initialize the incremental indexer.

        Args:
            repo_path: Path to the repository
            cache_dir: Optional cache directory for indexes
        """
        if self.use_indexing:
            self.indexer = IncrementalIndexer(repo_path, cache_dir)
            self.indexer.load_indexes()

    async def build_index(
        self,
        repo: Repo,
        branch: str | None = None,
        progress_callback: Callable[[str, float], None] | None = None,
    ) -> dict[str, Any]:
        """Build or update search indexes.

        Args:
            repo: Git repository
            branch: Branch to index
            progress_callback: Progress callback function

        Returns:
            Indexing statistics
        """
        if not self.indexer:
            repo_path = Path(repo.working_dir) if repo.working_dir else Path.cwd()
            self.initialize_indexer(repo_path)

        if self.indexer:
            return self.indexer.build_incremental_index(repo, branch, progress_callback)

        return {"status": "indexing_disabled"}

    def _make_cache_key(self, query: SearchQuery, branch: str | None) -> str:
        """Create a cache key for a query."""
        # Serialize query to JSON for consistent hashing
        query_dict = {
            "commit_hash": query.commit_hash,
            "author_pattern": query.author_pattern,
            "message_pattern": query.message_pattern,
            "content_pattern": query.content_pattern,
            "file_path_pattern": query.file_path_pattern,
            "file_extensions": query.file_extensions,
            "date_after": query.date_after.isoformat() if query.date_after else None,
            "date_before": query.date_before.isoformat() if query.date_before else None,
            "branch": branch,
        }

        query_json = json.dumps(query_dict, sort_keys=True)
        return hashlib.md5(query_json.encode()).hexdigest()

    async def search(
        self,
        repo: Repo,
        query: SearchQuery,
        branch: str | None = None,
        progress_callback: Callable[[str, float], None] | None = None,
        cache: dict[str, Any] | None = None,
        max_results: int | None = None,
    ) -> AsyncGenerator[SearchResult, None]:
        """Enhanced search with optimization and monitoring.

        Args:
            repo: Git repository to search
            query: Search query
            branch: Branch to search
            progress_callback: Progress callback
            cache: Optional cache dictionary
            max_results: Maximum results to return

        Yields:
            SearchResult objects
        """
        # Start monitoring
        search_id = f"search_{int(time.time() * 1000)}"
        if self.profiler:
            self.profiler.start_profile(search_id, query)

        if self.monitor:
            self.monitor.start_timer("total_search")
            self.monitor.increment_counter("total_searches")

        try:
            # Optimize query
            optimized_query = query
            if self.enable_optimization and self.query_optimizer:
                if self.monitor:
                    self.monitor.start_timer("query_optimization")

                optimized_query = self.query_optimizer.optimize(query)

                if self.monitor:
                    opt_time = self.monitor.stop_timer("query_optimization")
                    if self.profiler:
                        self.profiler.add_stage("query_optimization", opt_time)

            # Check cache
            cache_key = self._make_cache_key(optimized_query, branch)
            if cache_key in self.result_cache:
                if self.monitor:
                    self.monitor.increment_counter("cache_hits")

                for result in self.result_cache[cache_key]:
                    yield result

                if self.profiler:
                    self.profiler.add_stage("cache_lookup", 0.0, {"hit": True})
                return

            if self.monitor:
                self.monitor.increment_counter("cache_misses")

            # Try to use indexer for fast lookup
            if self.use_indexing and self.indexer and optimized_query.content_pattern:
                if self.monitor:
                    self.monitor.start_timer("index_search")

                index_results = await self._search_with_index(
                    repo, optimized_query, branch, max_results
                )

                if index_results:
                    # Cache results
                    self._cache_results(cache_key, index_results)

                    if self.monitor:
                        index_time = self.monitor.stop_timer("index_search")
                        if self.profiler:
                            self.profiler.add_stage(
                                "index_search", index_time, {"result_count": len(index_results)}
                            )

                    for result in index_results:
                        yield result
                    return

                if self.monitor:
                    self.monitor.stop_timer("index_search")

            # Fall back to regular search
            if self.monitor:
                self.monitor.start_timer("regular_search")

            results_list = []
            async for result in super().search(
                repo, optimized_query, branch, progress_callback, cache, max_results
            ):
                results_list.append(result)
                yield result

            # Cache results
            self._cache_results(cache_key, results_list)

            if self.monitor:
                search_time = self.monitor.stop_timer("regular_search")
                if self.profiler:
                    self.profiler.add_stage(
                        "regular_search", search_time, {"result_count": len(results_list)}
                    )

        finally:
            # End monitoring
            if self.monitor:
                total_time = self.monitor.stop_timer("total_search")

            if self.profiler:
                profile = self.profiler.end_profile()

                # Detect bottlenecks
                if self.bottleneck_detector:
                    bottlenecks = self.bottleneck_detector.analyze_profile(profile)
                    if bottlenecks and progress_callback:
                        for bottleneck in bottlenecks:
                            if bottleneck.get("severity") == "high":
                                progress_callback(
                                    f"Performance warning: {bottleneck['message']}", 1.0
                                )

    async def _search_with_index(
        self,
        repo: Repo,
        query: SearchQuery,
        branch: str | None,
        max_results: int | None,
    ) -> list[SearchResult] | None:
        """Search using the inverted index.

        Returns:
            List of results if index search was successful, None otherwise
        """
        if not self.indexer:
            return None

        results = []

        # Search content index
        if query.content_pattern:
            content_matches = self.indexer.search_content(
                query.content_pattern, limit=max_results or 100
            )

            # Convert index results to SearchResult objects
            for commit_hash, score in content_matches[: max_results or 100]:
                try:
                    commit = repo.commit(commit_hash)
                    from datetime import datetime

                    from ..models import CommitInfo, SearchType

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
                        parents=[p.hexsha for p in commit.parents],
                    )

                    result = SearchResult(
                        commit_hash=commit.hexsha,
                        file_path=Path(""),
                        line_number=None,
                        matching_line=query.content_pattern,
                        search_type=SearchType.CONTENT,
                        relevance_score=score,
                        commit_info=commit_info,
                        match_context={"source": "inverted_index"},
                        search_time_ms=0.0,
                    )

                    results.append(result)
                except Exception:
                    continue

        return results if results else None

    def _cache_results(self, cache_key: str, results: list[SearchResult]) -> None:
        """Cache search results."""
        # Evict oldest entry if cache is full
        if len(self.result_cache) >= self.cache_max_size:
            oldest_key = next(iter(self.result_cache))
            del self.result_cache[oldest_key]

        self.result_cache[cache_key] = results

    def get_performance_report(self) -> str:
        """Get a performance report."""
        if not self.monitor:
            return "Performance monitoring is disabled"

        return self.monitor.report()

    def get_all_profiles(self) -> list[dict[str, Any]]:
        """Get all search profiles."""
        if not self.profiler:
            return []

        return self.profiler.get_all_profiles()

    def get_bottlenecks(self) -> list[dict[str, Any]]:
        """Get detected performance bottlenecks."""
        if not self.bottleneck_detector:
            return []

        return self.bottleneck_detector.get_all_bottlenecks()

    def reset_monitoring(self) -> None:
        """Reset all monitoring data."""
        if self.monitor:
            self.monitor.reset()

        if self.profiler:
            self.profiler.clear_profiles()

        if self.bottleneck_detector:
            self.bottleneck_detector.clear()

    def clear_cache(self) -> None:
        """Clear the result cache."""
        self.result_cache.clear()

    def get_stats(self) -> dict[str, Any]:
        """Get comprehensive statistics."""
        stats = {
            "search_metrics": self.metrics.__dict__,
            "cache_size": len(self.result_cache),
            "cache_max_size": self.cache_max_size,
        }

        if self.monitor:
            stats["performance"] = self.monitor.get_all_stats()

        if self.indexer:
            stats["indexer"] = self.indexer.get_stats()

        return stats
