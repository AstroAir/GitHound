"""Tests for SearchAnalytics and performance monitoring."""

import asyncio
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from githound.models import SearchQuery, SearchResult, SearchType
from githound.search_engine.analytics import (
    PerformanceMetrics,
    SearchAnalytics,
    SearchEvent,
    get_global_analytics,
)


class TestSearchEvent:
    """Test cases for SearchEvent dataclass."""

    def test_search_event_creation(self):
        """Test creating a search event."""
        event = SearchEvent(
            timestamp=datetime.now(),
            query_hash="test_hash",
            search_types=[SearchType.CONTENT],
            duration_ms=100.0,
            result_count=5,
            cache_hits=2,
            cache_misses=3,
            memory_usage_mb=50.0,
            error_count=0,
            searcher_count=3,
            repository_path="/test/repo",
            branch="main",
        )

        assert event.query_hash == "test_hash"
        assert event.duration_ms == 100.0
        assert event.result_count == 5
        assert SearchType.CONTENT in event.search_types


class TestPerformanceMetrics:
    """Test cases for PerformanceMetrics dataclass."""

    def test_performance_metrics_creation(self):
        """Test creating performance metrics."""
        metrics = PerformanceMetrics(
            total_searches=100,
            avg_duration_ms=150.0,
            median_duration_ms=120.0,
            p95_duration_ms=300.0,
            avg_results_per_search=10.5,
            cache_hit_rate=0.75,
            error_rate=0.02,
            avg_memory_usage_mb=75.0,
            most_common_search_types=[(SearchType.CONTENT, 50)],
            peak_concurrent_searches=5,
        )

        assert metrics.total_searches == 100
        assert metrics.cache_hit_rate == 0.75
        assert metrics.most_common_search_types[0][0] == SearchType.CONTENT


class TestSearchAnalytics:
    """Test cases for SearchAnalytics."""

    def test_analytics_initialization(self):
        """Test analytics initialization."""
        analytics = SearchAnalytics(
            retention_days=7, max_events_in_memory=100, enable_persistence=False
        )

        assert analytics.retention_days == 7
        assert analytics.max_events_in_memory == 100
        assert not analytics.enable_persistence

    @pytest.mark.asyncio
    async def test_start_end_search(self):
        """Test starting and ending search tracking."""
        analytics = SearchAnalytics(enable_persistence=False)

        query = SearchQuery(content_pattern="test")
        search_id = await analytics.start_search(
            query=query, repository_path="/test/repo", branch="main"
        )

        assert search_id is not None
        assert search_id in analytics._active_searches

        # Create some mock results
        results = [
            SearchResult(
                commit_hash="abc123",
                file_path=Path("test.py"),
                line_number=1,
                matching_line="test content",
                commit_info=None,
                search_type=SearchType.CONTENT,
                relevance_score=0.8,
            )
        ]

        await analytics.end_search(
            search_id=search_id, results=results, cache_hits=2, cache_misses=1, memory_usage_mb=25.0
        )

        assert search_id not in analytics._active_searches
        assert len(analytics._events) == 1

        event = analytics._events[0]
        assert event.result_count == 1
        assert event.cache_hits == 2
        assert event.cache_misses == 1

    @pytest.mark.asyncio
    async def test_performance_metrics(self):
        """Test getting performance metrics."""
        analytics = SearchAnalytics(enable_persistence=False)

        # Add some test events
        now = datetime.now()
        for i in range(5):
            event = SearchEvent(
                timestamp=now - timedelta(minutes=i),
                query_hash=f"hash_{i}",
                search_types=[SearchType.CONTENT],
                duration_ms=100.0 + i * 10,
                result_count=5 + i,
                cache_hits=i,
                cache_misses=2,
                memory_usage_mb=50.0,
                error_count=0,
                searcher_count=3,
                repository_path="/test/repo",
                branch="main",
            )
            analytics._events.append(event)

        metrics = await analytics.get_performance_metrics(timedelta(hours=1))

        assert metrics.total_searches == 5
        assert metrics.avg_duration_ms > 0
        assert metrics.cache_hit_rate >= 0
        assert len(metrics.most_common_search_types) > 0

    @pytest.mark.asyncio
    async def test_usage_patterns(self):
        """Test analyzing usage patterns."""
        analytics = SearchAnalytics(enable_persistence=False)

        # Add test events across different hours
        now = datetime.now()
        for i in range(3):
            event = SearchEvent(
                timestamp=now - timedelta(hours=i),
                query_hash=f"hash_{i}",
                search_types=[SearchType.CONTENT],
                duration_ms=100.0,
                result_count=5,
                cache_hits=1,
                cache_misses=1,
                memory_usage_mb=50.0,
                error_count=0,
                searcher_count=3,
                repository_path="/test/repo",
                branch="main",
            )
            analytics._events.append(event)

        patterns = await analytics.get_usage_patterns()

        assert "hourly_distribution" in patterns
        assert "daily_distribution" in patterns
        assert "search_type_trends" in patterns
        assert patterns["total_events"] == 3

    @pytest.mark.asyncio
    async def test_optimization_recommendations(self):
        """Test getting optimization recommendations."""
        analytics = SearchAnalytics(enable_persistence=False)

        # Add events with high duration to trigger recommendations
        now = datetime.now()
        event = SearchEvent(
            timestamp=now,
            query_hash="slow_hash",
            search_types=[SearchType.CONTENT],
            duration_ms=6000.0,  # High duration
            result_count=5,
            cache_hits=0,  # Low cache hit rate
            cache_misses=10,
            memory_usage_mb=600.0,  # High memory usage
            error_count=2,  # High error count
            searcher_count=3,
            repository_path="/test/repo",
            branch="main",
        )
        analytics._events.append(event)

        recommendations = await analytics.get_optimization_recommendations()

        assert len(recommendations) > 0
        # Should recommend optimizations for high duration, low cache hit rate, etc.

    @pytest.mark.asyncio
    async def test_cleanup_old_events(self):
        """Test cleaning up old events."""
        analytics = SearchAnalytics(retention_days=1, enable_persistence=False)

        # Add old and new events
        now = datetime.now()
        old_event = SearchEvent(
            timestamp=now - timedelta(days=2),  # Older than retention
            query_hash="old_hash",
            search_types=[SearchType.CONTENT],
            duration_ms=100.0,
            result_count=5,
            cache_hits=1,
            cache_misses=1,
            memory_usage_mb=50.0,
            error_count=0,
            searcher_count=3,
            repository_path="/test/repo",
            branch="main",
        )

        new_event = SearchEvent(
            timestamp=now,  # Recent
            query_hash="new_hash",
            search_types=[SearchType.CONTENT],
            duration_ms=100.0,
            result_count=5,
            cache_hits=1,
            cache_misses=1,
            memory_usage_mb=50.0,
            error_count=0,
            searcher_count=3,
            repository_path="/test/repo",
            branch="main",
        )

        analytics._events.extend([old_event, new_event])
        assert len(analytics._events) == 2

        removed_count = await analytics.cleanup_old_events()

        assert removed_count == 1
        assert len(analytics._events) == 1
        assert analytics._events[0].query_hash == "new_hash"

    @pytest.mark.asyncio
    async def test_persistence(self):
        """Test event persistence to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            analytics_file = Path(temp_dir) / "test_analytics.jsonl"

            analytics = SearchAnalytics(enable_persistence=True, analytics_file=analytics_file)

            # Start and end a search to generate an event
            query = SearchQuery(content_pattern="test")
            search_id = await analytics.start_search(query=query, repository_path="/test/repo")

            results = [
                SearchResult(
                    commit_hash="abc123",
                    file_path=Path("test.py"),
                    line_number=1,
                    matching_line="test content",
                    commit_info=None,
                    search_type=SearchType.CONTENT,
                    relevance_score=0.8,
                )
            ]

            await analytics.end_search(search_id, results)

            # Check that file was created and contains data
            assert analytics_file.exists()
            content = analytics_file.read_text()
            assert len(content.strip()) > 0

    def test_global_analytics(self):
        """Test global analytics instance."""
        analytics1 = get_global_analytics()
        analytics2 = get_global_analytics()

        # Should return same instance
        assert analytics1 is analytics2
        assert isinstance(analytics1, SearchAnalytics)


@pytest.mark.asyncio
class TestAnalyticsIntegration:
    """Integration tests for analytics with search engine."""

    async def test_analytics_with_orchestrator(self):
        """Test analytics integration with search orchestrator."""
        from githound.models import SearchEngineConfig
        from githound.search_engine.factory import SearchEngineFactory

        # Create factory with analytics enabled
        config = SearchEngineConfig(enable_analytics=True)
        factory = SearchEngineFactory(config)
        orchestrator = factory.create_orchestrator()

        # Verify analytics is set
        assert orchestrator._analytics is not None
        assert isinstance(orchestrator._analytics, SearchAnalytics)

    async def test_concurrent_searches(self):
        """Test analytics with concurrent searches."""
        analytics = SearchAnalytics(enable_persistence=False)

        async def mock_search(search_num: int):
            query = SearchQuery(content_pattern=f"test_{search_num}")
            search_id = await analytics.start_search(query=query, repository_path="/test/repo")

            # Simulate some work
            await asyncio.sleep(0.01)

            results = [
                SearchResult(
                    commit_hash=f"abc{search_num}",
                    file_path=Path(f"test_{search_num}.py"),
                    line_number=1,
                    matching_line=f"test content {search_num}",
                    commit_info=None,
                    search_type=SearchType.CONTENT,
                    relevance_score=0.8,
                )
            ]

            await analytics.end_search(search_id, results)

        # Run multiple searches concurrently
        await asyncio.gather(*[mock_search(i) for i in range(5)])

        assert len(analytics._events) == 5
        assert analytics._peak_concurrent > 0


if __name__ == "__main__":
    pytest.main([__file__])
