"""Search orchestrator that coordinates multiple searchers."""

import asyncio
import time
from typing import AsyncGenerator, Dict, List, Optional, Callable

from git import Repo

from ..models import SearchQuery, SearchResult, SearchMetrics
from .base import BaseSearcher, SearchContext


class SearchOrchestrator:
    """Orchestrates multiple searchers to handle complex queries."""
    
    def __init__(self):
        self._searchers: List[BaseSearcher] = []
        self._metrics = SearchMetrics()
    
    def register_searcher(self, searcher: BaseSearcher) -> None:
        """Register a searcher with the orchestrator."""
        self._searchers.append(searcher)
    
    def unregister_searcher(self, searcher: BaseSearcher) -> None:
        """Unregister a searcher from the orchestrator."""
        if searcher in self._searchers:
            self._searchers.remove(searcher)
    
    @property
    def metrics(self) -> SearchMetrics:
        """Get combined metrics from all searchers."""
        combined = SearchMetrics()
        
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
        branch: Optional[str] = None,
        progress_callback: Optional[Callable[[str, float], None]] = None,
        cache: Optional[Dict] = None,
        max_results: Optional[int] = None
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
        
        try:
            # Create search context
            context = SearchContext(
                repo=repo,
                query=query,
                branch=branch,
                progress_callback=progress_callback,
                cache=cache
            )
            
            # Find applicable searchers
            applicable_searchers = []
            for searcher in self._searchers:
                if await searcher.can_handle(query):
                    applicable_searchers.append(searcher)
            
            if not applicable_searchers:
                if progress_callback:
                    progress_callback("No applicable searchers found", 1.0)
                return
            
            # Estimate total work for progress reporting
            total_work = 0
            searcher_work = {}
            for searcher in applicable_searchers:
                work = await searcher.estimate_work(context)
                searcher_work[searcher] = work
                total_work += work
            
            # Run searchers and collect results
            completed_work = 0
            
            async def run_searcher(searcher: BaseSearcher) -> List[SearchResult]:
                nonlocal completed_work, results_count
                
                searcher_results = []
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
            searcher_tasks = [run_searcher(searcher) for searcher in applicable_searchers]
            all_results = await asyncio.gather(*searcher_tasks)
            
            # Flatten and rank results
            flattened_results = []
            for searcher_results in all_results:
                flattened_results.extend(searcher_results)
            
            # Sort by relevance score (descending)
            flattened_results.sort(key=lambda r: r.relevance_score, reverse=True)
            
            # Yield results
            for result in flattened_results:
                if max_results and results_count >= max_results:
                    break
                yield result
            
        finally:
            # Update metrics
            end_time = time.time()
            self._metrics.search_duration_ms = (end_time - start_time) * 1000
            self._metrics.total_results_found = results_count
            
            if progress_callback:
                progress_callback("Search completed", 1.0)
    
    async def get_available_searchers(self, query: SearchQuery) -> List[str]:
        """Get list of searcher names that can handle the given query."""
        available = []
        for searcher in self._searchers:
            if await searcher.can_handle(query):
                available.append(searcher.name)
        return available
    
    def get_searcher_by_name(self, name: str) -> Optional[BaseSearcher]:
        """Get a searcher by name."""
        for searcher in self._searchers:
            if searcher.name == name:
                return searcher
        return None
    
    def list_searchers(self) -> List[str]:
        """List all registered searcher names."""
        return [searcher.name for searcher in self._searchers]
