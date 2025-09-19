"""Search orchestrator that coordinates multiple searchers."""

import asyncio
import time
from collections.abc import AsyncGenerator, Callable
from typing import Any

from git import Repo

from ..models import SearchMetrics, SearchQuery, SearchResult
from .base import BaseSearcher, SearchContext

# mypy: disable-error-code=unreachable
# Note: mypy incorrectly flags code as unreachable due to dynamic searcher registration


class SearchOrchestrator:
    """Orchestrates multiple searchers to handle complex queries."""

    def __init__(self) -> None:
        self._searchers: list[BaseSearcher] = []
        self._cache = None
        self._ranking_engine = None
        self._result_processor = None
        self._analytics = None
        self._metrics = SearchMetrics(
            total_commits_searched=0,
            total_files_searched=0,
            total_results_found=0,
            search_duration_ms=0.0,
            cache_hits=0,
            cache_misses=0,
            memory_usage_mb=None,
        )

    def register_searcher(self, searcher: BaseSearcher) -> None:
        """Register a searcher with the orchestrator."""
        self._searchers.append(searcher)

    def unregister_searcher(self, searcher: BaseSearcher) -> None:
        """Unregister a searcher from the orchestrator."""
        if searcher in self._searchers:
            self._searchers.remove(searcher)

    def set_cache(self, cache: Any) -> None:
        """Set the cache for the orchestrator."""
        self._cache = cache

    def set_ranking_engine(self, ranking_engine: Any) -> None:
        """Set the ranking engine for the orchestrator."""
        self._ranking_engine = ranking_engine

    def set_result_processor(self, result_processor: Any) -> None:
        """Set the result processor for the orchestrator."""
        self._result_processor = result_processor

    def set_analytics(self, analytics: Any) -> None:
        """Set the analytics for the orchestrator."""
        self._analytics = analytics

    @property
    def metrics(self) -> SearchMetrics:
        """Get combined metrics from all searchers."""
        combined = SearchMetrics(
            total_commits_searched=0,
            total_files_searched=0,
            total_results_found=0,
            search_duration_ms=0.0,
            cache_hits=0,
            cache_misses=0,
            memory_usage_mb=None,
        )

        # Combine metrics from all searchers
        for searcher in self._searchers:
            searcher_metrics = searcher.metrics
            combined.total_commits_searched += searcher_metrics.total_commits_searched
            combined.total_files_searched += searcher_metrics.total_files_searched
            combined.total_results_found += searcher_metrics.total_results_found
            combined.cache_hits += searcher_metrics.cache_hits
            combined.cache_misses += searcher_metrics.cache_misses

        # Add orchestrator-specific metrics
        combined.search_duration_ms = self._metrics.search_duration_ms
        combined.memory_usage_mb = self._metrics.memory_usage_mb

        return combined

    async def search(
        self,
        repo: Repo,
        query: SearchQuery,
        branch: str | None = None,
        progress_callback: Callable[[str, float], None] | None = None,
        cache: dict | None = None,
        max_results: int | None = None,
    ) -> AsyncGenerator[SearchResult, None]:
        """
        Perform a search using all applicable searchers.

        Args:
            repo: Git repository to search
            query: Search query
            branch: Branch to search (defaults to current branch)
            progress_callback: Optional progress callback
            cache: Optional cache dictionary
            max_results: Maximum number of results to return

        Yields:
            SearchResult objects
        """
        start_time = time.time()
        results_count = 0
        search_id = None
        all_results_list: list[SearchResult] = []
        searcher_count = 0

        try:
            # Start analytics tracking if available
            if self._analytics:
                search_id = await self._analytics.start_search(
                    query, str(repo.working_dir), branch
                )
            # Create search context
            # Use internal cache if no cache provided
            effective_cache = cache if cache is not None else self._cache

            # Ensure forward references are resolved for SearchContext
            try:
                from .cache import SearchCache
                SearchContext.update_forward_refs(SearchCache=SearchCache)
            except Exception:
                pass  # Ignore if already resolved or other issues

            context = SearchContext(
                repo=repo,
                query=query,
                branch=branch,
                progress_callback=progress_callback,
                cache=effective_cache,
            )

            # Find applicable searchers
            applicable_searchers: list[BaseSearcher] = []
            for searcher in self._searchers:
                if await searcher.can_handle(query):
                    applicable_searchers.append(searcher)

            if not applicable_searchers:
                if progress_callback:
                    progress_callback("No applicable searchers found", 1.0)
                return

            searcher_count = len(applicable_searchers)

            # Estimate total work for progress reporting
            total_work = 0
            searcher_work: dict[BaseSearcher, int] = {}
            for searcher in applicable_searchers:
                work = await searcher.estimate_work(context)
                searcher_work[searcher] = work
                total_work += work

            # Run searchers and collect results
            completed_work = 0

            async def run_searcher(searcher: BaseSearcher) -> list[SearchResult]:
                nonlocal completed_work, results_count

                searcher_results: list[SearchResult] = []
                async for result in searcher.search(context):
                    searcher_results.append(result)
                    results_count += 1

                    # Check max results limit
                    if max_results and results_count >= max_results:
                        break

                # Update progress
                completed_work += searcher_work[searcher]
                if progress_callback and total_work > 0:
                    progress = completed_work / total_work
                    progress_callback(f"Completed {searcher.name}", progress)

                return searcher_results

            # Run all searchers concurrently
            searcher_tasks = [run_searcher(searcher)
                              for searcher in applicable_searchers]
            all_results = await asyncio.gather(*searcher_tasks)

            # Flatten results
            flattened_results: list[SearchResult] = []
            for searcher_results in all_results:
                flattened_results.extend(searcher_results)

            # Apply ranking if ranking engine is available
            if self._ranking_engine and flattened_results:
                if progress_callback:
                    progress_callback("Ranking results...", 0.9)
                flattened_results = await self._ranking_engine.rank_results(
                    flattened_results, query, context
                )
            else:
                # Fallback to simple relevance score sorting
                flattened_results.sort(
                    key=lambda r: r.relevance_score, reverse=True)

            # Apply result processing if processor is available
            if self._result_processor and flattened_results:
                if progress_callback:
                    progress_callback("Processing results...", 0.95)
                flattened_results = await self._result_processor.process_results(
                    flattened_results, query, context
                )

            # Yield results and collect for analytics
            for result in flattened_results:
                if max_results and results_count >= max_results:
                    break
                all_results_list.append(result)
                yield result

        finally:
            # NOTE: This finally block always executes, even with the return statement
            # in the try block above. This is correct Python behavior for cleanup.

            # Update metrics
            end_time = time.time()
            self._metrics.search_duration_ms = (end_time - start_time) * 1000
            self._metrics.total_results_found = len(all_results_list)

            # End analytics tracking if available
            if self._analytics and search_id:
                try:
                    await self._analytics.end_search(
                        search_id,
                        all_results_list,
                        cache_hits=self._metrics.cache_hits,
                        cache_misses=self._metrics.cache_misses,
                        memory_usage_mb=self._metrics.memory_usage_mb,
                        error_count=0,  # TODO: Track errors properly
                        searcher_count=searcher_count
                    )
                except Exception:
                    # Don't let analytics errors break the search
                    pass

            if progress_callback:
                progress_callback("Search completed", 1.0)

    async def get_available_searchers(self, query: SearchQuery) -> list[str]:
        """Get list of searcher names that can handle the given query."""
        available: list[str] = []
        for searcher in self._searchers:
            if await searcher.can_handle(query):
                available.append(searcher.name)
        return available

    def get_searcher_by_name(self, name: str) -> BaseSearcher | None:
        """Get a searcher by name."""
        for searcher in self._searchers:
            if searcher.name == name:
                return searcher
        return None

    def list_searchers(self) -> list[str]:
        """List all registered searcher names."""
        return [searcher.name for searcher in self._searchers]
