"""Base classes for the search engine architecture."""

import asyncio
import os
import time
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Awaitable, Callable

# Forward declaration to avoid circular imports
from typing import Any

from pydantic import BaseModel, ConfigDict

from ..models import SearchMetrics, SearchQuery, SearchResult

# Import SearchCache for runtime use in Pydantic models
try:
    from .cache import SearchCache
except ImportError:
    SearchCache = None  # type: ignore[misc, assignment]


class SearchContext(BaseModel):
    """Context information for search operations."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    repo: Any  # git.Repo object
    query: SearchQuery
    branch: str | None = None
    progress_callback: Callable[[str, float], None] | None = None
    cache: dict[
        str, Any
    ] | Any | None = None  # Changed from "SearchCache" to Any to avoid forward ref issues


class BaseSearcher(ABC):
    """Abstract base class for all searchers."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._metrics = SearchMetrics(
            total_commits_searched=0,
            total_files_searched=0,
            total_results_found=0,
            search_duration_ms=0.0,
            cache_hits=0,
            cache_misses=0,
            memory_usage_mb=None,
        )

    @property
    def metrics(self) -> SearchMetrics:
        """Get search metrics."""
        return self._metrics

    @abstractmethod
    async def can_handle(self, query: SearchQuery) -> bool:
        """Check if this searcher can handle the given query."""
        pass

    @abstractmethod
    def search(self, context: SearchContext) -> AsyncGenerator[SearchResult, None]:
        """Perform the search and yield results."""
        pass

    async def estimate_work(self, context: SearchContext) -> int:
        """Estimate the amount of work this searcher will do (for progress reporting)."""
        return 1

    def _report_progress(self, context: SearchContext, message: str, progress: float) -> None:
        """Report progress if callback is available."""
        if context.progress_callback:
            context.progress_callback(f"[{self.name}] {message}", progress)

    def _update_metrics(self, **kwargs: Any) -> None:
        """Update search metrics.
        Accepts numeric fields of SearchMetrics and increments or sets appropriately.
        """
        for key, value in kwargs.items():
            if hasattr(self._metrics, key):
                current_value = getattr(self._metrics, key)
                if isinstance(current_value, int | float) and isinstance(value, int | float):
                    setattr(self._metrics, key, current_value + value)
                else:
                    setattr(self._metrics, key, value)

    def _calculate_search_time_ms(self, start_time: float) -> float:
        """Calculate search time in milliseconds from start time."""
        return (time.time() - start_time) * 1000


class CacheableSearcher(BaseSearcher):
    """Base class for searchers that support caching."""

    def __init__(self, name: str, cache_prefix: str = "") -> None:
        super().__init__(name)
        self.cache_prefix = cache_prefix or name

    def _get_cache_key(self, context: SearchContext, suffix: str = "") -> str:
        """Generate a cache key for the given context."""
        repo_path = str(context.repo.working_dir)
        query_hash = hash(str(context.query))
        branch = context.branch or "HEAD"
        return f"{self.cache_prefix}:{repo_path}:{branch}:{query_hash}:{suffix}"

    async def _get_from_cache(self, context: SearchContext, key: str) -> Any | None:
        """Get value from cache if available."""
        if not context.cache:
            return None

        try:
            # Handle both dict and SearchCache
            if hasattr(context.cache, "get") and callable(context.cache.get):
                # SearchCache or similar async cache
                get_method = context.cache.get
                if asyncio.iscoroutinefunction(get_method):
                    value = await get_method(key)  # type: ignore[misc]
                else:
                    value = get_method(key)
            else:
                # Regular dict
                value = context.cache.get(key) if hasattr(context.cache, "get") else None

            if value is not None:
                self._update_metrics(cache_hits=1)
            else:
                self._update_metrics(cache_misses=1)
            return value
        except Exception:
            self._update_metrics(cache_misses=1)
            return None

    async def _set_cache(
        self, context: SearchContext, key: str, value: Any, ttl: int = 3600
    ) -> None:
        """Set value in cache."""
        if not context.cache:
            return

        try:
            # Handle both dict and SearchCache
            if hasattr(context.cache, "set") and callable(context.cache.set):
                # SearchCache or similar async cache
                set_method = context.cache.set
                if asyncio.iscoroutinefunction(set_method):
                    await set_method(value, key, ttl=ttl)
                else:
                    set_method(value, key, ttl=ttl)
            else:
                # Regular dict
                if hasattr(context.cache, "__setitem__"):
                    context.cache[key] = value
        except Exception:
            pass  # Ignore cache errors


class ParallelSearcher(BaseSearcher):
    """Base class for searchers that can run operations in parallel with dynamic worker sizing."""

    def __init__(self, name: str, max_workers: int = 4) -> None:
        super().__init__(name)
        # Optimize: Use dynamic worker count based on CPU cores if not specified
        if max_workers <= 0:
            max_workers = min(32, (os.cpu_count() or 1) + 4)
        self.max_workers = max_workers
        self._semaphore = asyncio.Semaphore(max_workers)

    async def _run_parallel(
        self,
        tasks: list[Callable[[], Awaitable[Any]]],
        context: SearchContext,
        batch_size: int | None = None,
    ) -> list[Any]:
        """Run tasks in parallel with concurrency control and optional batching.

        Args:
            tasks: List of async tasks to execute
            context: Search context
            batch_size: Optional batch size for processing tasks in chunks
                       (useful for very large task lists to reduce memory pressure)

        Returns:
            List of results from all tasks
        """

        async def _run_task(task: Callable[[], Awaitable[Any]]) -> Any:
            async with self._semaphore:
                return await task()

        # If batch_size is specified and we have many tasks, process in batches
        if batch_size and len(tasks) > batch_size:
            all_results = []
            for i in range(0, len(tasks), batch_size):
                batch = tasks[i : i + batch_size]
                batch_results = await asyncio.gather(*[_run_task(task) for task in batch])
                all_results.extend(batch_results)
            return all_results
        else:
            # Process all tasks at once
            return await asyncio.gather(*[_run_task(task) for task in tasks])
