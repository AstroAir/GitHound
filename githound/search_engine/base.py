"""Base classes for the search engine architecture."""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional

from git import Repo
from pydantic import BaseModel

from ..models import SearchQuery, SearchResult, SearchMetrics


class SearchContext(BaseModel):
    """Context information for search operations."""
    
    repo: Any  # git.Repo object
    query: SearchQuery
    branch: Optional[str] = None
    progress_callback: Optional[Callable[[str, float], None]] = None
    cache: Optional[Dict[str, Any]] = None
    
    class Config:
        arbitrary_types_allowed = True


class BaseSearcher(ABC):
    """Abstract base class for all searchers."""
    
    def __init__(self, name: str):
        self.name = name
        self._metrics = SearchMetrics()
    
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
    
    def _update_metrics(self, **kwargs):
        """Update search metrics."""
        for key, value in kwargs.items():
            if hasattr(self._metrics, key):
                current_value = getattr(self._metrics, key)
                if isinstance(current_value, (int, float)):
                    setattr(self._metrics, key, current_value + value)
                else:
                    setattr(self._metrics, key, value)


class CacheableSearcher(BaseSearcher):
    """Base class for searchers that support caching."""
    
    def __init__(self, name: str, cache_prefix: str = ""):
        super().__init__(name)
        self.cache_prefix = cache_prefix or name
    
    def _get_cache_key(self, context: SearchContext, suffix: str = "") -> str:
        """Generate a cache key for the given context."""
        repo_path = str(context.repo.working_dir)
        query_hash = hash(str(context.query))
        branch = context.branch or "HEAD"
        return f"{self.cache_prefix}:{repo_path}:{branch}:{query_hash}:{suffix}"
    
    async def _get_from_cache(self, context: SearchContext, key: str) -> Optional[Any]:
        """Get value from cache if available."""
        if not context.cache:
            return None
        
        try:
            value = context.cache.get(key)
            if value is not None:
                self._update_metrics(cache_hits=1)
            else:
                self._update_metrics(cache_misses=1)
            return value
        except Exception:
            self._update_metrics(cache_misses=1)
            return None
    
    async def _set_cache(self, context: SearchContext, key: str, value: Any, ttl: int = 3600) -> None:
        """Set value in cache."""
        if not context.cache:
            return
        
        try:
            context.cache[key] = value
        except Exception:
            pass  # Ignore cache errors


class ParallelSearcher(BaseSearcher):
    """Base class for searchers that can run operations in parallel."""
    
    def __init__(self, name: str, max_workers: int = 4):
        super().__init__(name)
        self.max_workers = max_workers
        self._semaphore = asyncio.Semaphore(max_workers)
    
    async def _run_parallel(self, tasks: List[Callable], context: SearchContext) -> List[Any]:
        """Run tasks in parallel with concurrency control."""
        async def _run_task(task: Callable) -> Any:
            async with self._semaphore:
                return await task()
        
        return await asyncio.gather(*[_run_task(task) for task in tasks])
