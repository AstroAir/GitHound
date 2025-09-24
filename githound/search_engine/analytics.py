"""Search analytics and performance monitoring for GitHound."""

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, DefaultDict, Dict, List, Optional

from ..models import SearchQuery, SearchResult, SearchType

logger = logging.getLogger(__name__)


@dataclass
class SearchEvent:
    """Represents a search event for analytics."""

    timestamp: datetime
    query_hash: str
    search_types: List[SearchType]
    duration_ms: float
    result_count: int
    cache_hits: int
    cache_misses: int
    memory_usage_mb: Optional[float]
    error_count: int
    searcher_count: int
    repository_path: str
    branch: Optional[str]
    user_agent: Optional[str] = None
    session_id: Optional[str] = None


@dataclass
class PerformanceMetrics:
    """Performance metrics for a time period."""

    total_searches: int
    avg_duration_ms: float
    median_duration_ms: float
    p95_duration_ms: float
    avg_results_per_search: float
    cache_hit_rate: float
    error_rate: float
    avg_memory_usage_mb: float
    most_common_search_types: List[tuple[SearchType, int]]
    peak_concurrent_searches: int


class SearchAnalytics:
    """Analytics and monitoring system for search operations."""

    def __init__(
        self,
        retention_days: int = 30,
        max_events_in_memory: int = 10000,
        enable_persistence: bool = True,
        analytics_file: Optional[Path] = None,
    ):
        self.retention_days = retention_days
        self.max_events_in_memory = max_events_in_memory
        self.enable_persistence = enable_persistence
        self.analytics_file = analytics_file or Path("search_analytics.jsonl")

        # In-memory storage
        self._events: deque[SearchEvent] = deque(maxlen=max_events_in_memory)
        self._active_searches: Dict[str, datetime] = {}
        self._performance_cache: Dict[str, PerformanceMetrics] = {}

        # Counters
        self._total_searches = 0
        self._total_errors = 0
        self._concurrent_searches = 0
        self._peak_concurrent = 0

        # Load existing data if available
        if self.enable_persistence and self.analytics_file.exists():
            self._load_analytics_data()

    async def start_search(
        self,
        query: SearchQuery,
        repository_path: str,
        branch: Optional[str] = None,
        session_id: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> str:
        """Start tracking a search operation."""
        search_id = f"{time.time()}_{hash(str(query))}"
        self._active_searches[search_id] = datetime.now()

        self._concurrent_searches += 1
        self._peak_concurrent = max(self._peak_concurrent, self._concurrent_searches)

        logger.debug(f"Started tracking search {search_id}")
        return search_id

    async def end_search(
        self,
        search_id: str,
        results: List[SearchResult],
        cache_hits: int = 0,
        cache_misses: int = 0,
        memory_usage_mb: Optional[float] = None,
        error_count: int = 0,
        searcher_count: int = 1,
        branch: Optional[str] = None,
    ) -> None:
        """End tracking a search operation and record metrics."""
        if search_id not in self._active_searches:
            logger.warning(f"Search ID {search_id} not found in active searches")
            return

        start_time = self._active_searches.pop(search_id)
        duration = (datetime.now() - start_time).total_seconds() * 1000

        self._concurrent_searches -= 1
        self._total_searches += 1
        self._total_errors += error_count

        # Extract search types from results
        search_types = list(set(result.search_type for result in results))

        # Create search event
        event = SearchEvent(
            timestamp=start_time,
            query_hash=search_id.split("_")[1],
            search_types=search_types,
            duration_ms=duration,
            result_count=len(results),
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            memory_usage_mb=memory_usage_mb,
            error_count=error_count,
            searcher_count=searcher_count,
            repository_path="",  # Anonymized for privacy
            branch=branch,
        )

        # Store event
        self._events.append(event)

        # Persist if enabled
        if self.enable_persistence:
            await self._persist_event(event)

        # Clear performance cache to force recalculation
        self._performance_cache.clear()

        logger.debug(f"Recorded search event: {duration:.2f}ms, {len(results)} results")

    async def get_performance_metrics(
        self, time_period: timedelta = timedelta(hours=24)
    ) -> PerformanceMetrics:
        """Get performance metrics for a specific time period."""
        cache_key = f"metrics_{time_period.total_seconds()}"

        if cache_key in self._performance_cache:
            return self._performance_cache[cache_key]

        cutoff_time = datetime.now() - time_period
        relevant_events = [event for event in self._events if event.timestamp >= cutoff_time]

        if not relevant_events:
            return PerformanceMetrics(
                total_searches=0,
                avg_duration_ms=0.0,
                median_duration_ms=0.0,
                p95_duration_ms=0.0,
                avg_results_per_search=0.0,
                cache_hit_rate=0.0,
                error_rate=0.0,
                avg_memory_usage_mb=0.0,
                most_common_search_types=[],
                peak_concurrent_searches=0,
            )

        # Calculate metrics
        durations = [event.duration_ms for event in relevant_events]
        durations.sort()

        total_cache_hits = sum(event.cache_hits for event in relevant_events)
        total_cache_requests = sum(
            event.cache_hits + event.cache_misses for event in relevant_events
        )

        # Count search types
        search_type_counts: DefaultDict[SearchType, int] = defaultdict(int)
        for event in relevant_events:
            for search_type in event.search_types:
                search_type_counts[search_type] += 1

        most_common_types = sorted(search_type_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        metrics = PerformanceMetrics(
            total_searches=len(relevant_events),
            avg_duration_ms=sum(durations) / len(durations),
            median_duration_ms=durations[len(durations) // 2],
            p95_duration_ms=durations[int(len(durations) * 0.95)],
            avg_results_per_search=sum(event.result_count for event in relevant_events)
            / len(relevant_events),
            cache_hit_rate=total_cache_hits / max(total_cache_requests, 1),
            error_rate=sum(event.error_count for event in relevant_events) / len(relevant_events),
            avg_memory_usage_mb=sum(event.memory_usage_mb or 0 for event in relevant_events)
            / len(relevant_events),
            most_common_search_types=most_common_types,
            peak_concurrent_searches=self._peak_concurrent,
        )

        self._performance_cache[cache_key] = metrics
        return metrics

    async def get_usage_patterns(self) -> Dict[str, Any]:
        """Analyze usage patterns and trends."""
        if not self._events:
            return {}

        # Hourly distribution
        hourly_counts: DefaultDict[int, int] = defaultdict(int)
        for event in self._events:
            hour = event.timestamp.hour
            hourly_counts[hour] += 1

        # Daily distribution
        daily_counts: DefaultDict[str, int] = defaultdict(int)
        for event in self._events:
            day = event.timestamp.strftime("%Y-%m-%d")
            daily_counts[day] += 1

        # Search type trends
        search_type_trends = defaultdict(list)
        for event in self._events:
            day = event.timestamp.strftime("%Y-%m-%d")
            for search_type in event.search_types:
                search_type_trends[search_type.value].append(day)

        return {
            "hourly_distribution": dict(hourly_counts),
            "daily_distribution": dict(daily_counts),
            "search_type_trends": {k: len(set(v)) for k, v in search_type_trends.items()},
            "total_events": len(self._events),
            "date_range": {
                "start": min(event.timestamp for event in self._events).isoformat(),
                "end": max(event.timestamp for event in self._events).isoformat(),
            },
        }

    async def get_optimization_recommendations(self) -> List[str]:
        """Generate optimization recommendations based on analytics."""
        recommendations = []

        metrics = await self.get_performance_metrics()

        # Performance recommendations
        if metrics.avg_duration_ms > 5000:
            recommendations.append(
                "Average search duration is high (>5s). Consider enabling caching or optimizing queries."
            )

        if metrics.cache_hit_rate < 0.3:
            recommendations.append(
                "Cache hit rate is low (<30%). Consider increasing cache TTL or size."
            )

        if metrics.error_rate > 0.1:
            recommendations.append(
                "Error rate is high (>10%). Check for common error patterns and improve error handling."
            )

        if metrics.avg_memory_usage_mb > 500:
            recommendations.append(
                "Memory usage is high (>500MB). Consider implementing memory limits or optimizing searchers."
            )

        # Usage pattern recommendations
        patterns = await self.get_usage_patterns()

        if patterns.get("total_events", 0) > 1000:
            recommendations.append(
                "High search volume detected. Consider implementing rate limiting or query optimization."
            )

        return recommendations

    async def cleanup_old_events(self) -> int:
        """Remove events older than retention period."""
        cutoff_time = datetime.now() - timedelta(days=self.retention_days)

        original_count = len(self._events)
        self._events = deque(
            (event for event in self._events if event.timestamp >= cutoff_time),
            maxlen=self.max_events_in_memory,
        )

        removed_count = original_count - len(self._events)
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} old analytics events")

        return removed_count

    async def _persist_event(self, event: SearchEvent) -> None:
        """Persist an event to storage."""
        try:
            with open(self.analytics_file, "a") as f:
                event_dict = asdict(event)
                event_dict["timestamp"] = event.timestamp.isoformat()
                event_dict["search_types"] = [st.value for st in event.search_types]
                f.write(json.dumps(event_dict) + "\n")
        except Exception as e:
            logger.error(f"Failed to persist analytics event: {e}")

    def _load_analytics_data(self) -> None:
        """Load existing analytics data from storage."""
        try:
            with open(self.analytics_file, "r") as f:
                for line in f:
                    if line.strip():
                        event_dict = json.loads(line)
                        event_dict["timestamp"] = datetime.fromisoformat(event_dict["timestamp"])
                        event_dict["search_types"] = [
                            SearchType(st) for st in event_dict["search_types"]
                        ]
                        event = SearchEvent(**event_dict)
                        self._events.append(event)

            logger.info(f"Loaded {len(self._events)} analytics events from storage")
        except Exception as e:
            logger.error(f"Failed to load analytics data: {e}")


# Global analytics instance
_global_analytics: Optional[SearchAnalytics] = None


def get_global_analytics() -> SearchAnalytics:
    """Get the global analytics instance."""
    global _global_analytics
    if _global_analytics is None:
        _global_analytics = SearchAnalytics()
    return _global_analytics
