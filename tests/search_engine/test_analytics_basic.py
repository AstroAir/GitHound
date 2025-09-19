"""Basic tests for GitHound search engine analytics module."""

import pytest
from datetime import datetime
from unittest.mock import Mock

from githound.search_engine.analytics import (
    SearchEvent,
    PerformanceMetrics,
    SearchAnalytics
)
from githound.models import SearchQuery, SearchResult, SearchType


@pytest.fixture
def analytics_instance() -> SearchAnalytics:
    """Create analytics instance for testing."""
    return SearchAnalytics(
        retention_days=30,
        max_events=1000,
        enable_performance_tracking=True
    )


@pytest.fixture
def sample_search_event() -> SearchEvent:
    """Create sample search event for testing."""
    return SearchEvent(
        timestamp=datetime.now(),
        query_hash="test_hash_123",
        search_types=[SearchType.CONTENT],
        duration_ms=150.5,
        result_count=5,
        cache_hits=2,
        cache_misses=3,
        memory_usage_mb=64.0,
        error_count=0,
        searcher_count=3,
        repository_path="/test/repo",
        branch="main"
    )


class TestSearchEvent:
    """Test SearchEvent dataclass."""

    def test_search_event_creation(self, sample_search_event: SearchEvent) -> None:
        """Test creating a search event."""
        assert sample_search_event.query_hash == "test_hash_123"
        assert sample_search_event.duration_ms == 150.5
        assert sample_search_event.result_count == 5
        assert sample_search_event.repository_path == "/test/repo"

    def test_search_event_with_optional_fields(self) -> None:
        """Test search event with optional fields."""
        event = SearchEvent(
            timestamp=datetime.now(),
            query_hash="test",
            search_types=[SearchType.AUTHOR],
            duration_ms=100.0,
            result_count=1,
            cache_hits=0,
            cache_misses=1,
            memory_usage_mb=None,
            error_count=0,
            searcher_count=1,
            repository_path="/repo",
            branch=None,
            user_agent="test-agent",
            session_id="session-123"
        )
        
        assert event.user_agent == "test-agent"
        assert event.session_id == "session-123"
        assert event.memory_usage_mb is None
        assert event.branch is None


class TestPerformanceMetrics:
    """Test PerformanceMetrics dataclass."""

    def test_performance_metrics_creation(self) -> None:
        """Test creating performance metrics."""
        metrics = PerformanceMetrics(
            total_searches=100,
            avg_duration_ms=125.5,
            median_duration_ms=110.0,
            p95_duration_ms=250.0,
            avg_results_per_search=3.5,
            cache_hit_rate=0.75,
            error_rate=0.02,
            avg_memory_usage_mb=48.0,
            most_common_search_types=[(SearchType.CONTENT, 60), (SearchType.AUTHOR, 25)],
            peak_concurrent_searches=5
        )
        
        assert metrics.total_searches == 100
        assert metrics.avg_duration_ms == 125.5
        assert metrics.cache_hit_rate == 0.75
        assert len(metrics.most_common_search_types) == 2


class TestSearchAnalytics:
    """Test SearchAnalytics class."""

    def test_analytics_initialization(self) -> None:
        """Test analytics initialization."""
        analytics = SearchAnalytics(
            retention_days=7,
            max_events=500,
            enable_performance_tracking=False
        )
        
        assert analytics.retention_days == 7
        assert analytics.max_events == 500
        assert analytics.enable_performance_tracking is False

    def test_record_search_event(
        self, 
        analytics_instance: SearchAnalytics,
        sample_search_event: SearchEvent
    ) -> None:
        """Test recording a search event."""
        initial_count = len(analytics_instance.events)
        
        analytics_instance.record_event(sample_search_event)
        
        assert len(analytics_instance.events) == initial_count + 1
        assert analytics_instance.events[-1] == sample_search_event

    def test_get_performance_metrics(
        self,
        analytics_instance: SearchAnalytics,
        sample_search_event: SearchEvent
    ) -> None:
        """Test getting performance metrics."""
        # Record some events
        for i in range(5):
            event = SearchEvent(
                timestamp=datetime.now(),
                query_hash=f"hash_{i}",
                search_types=[SearchType.CONTENT],
                duration_ms=100.0 + i * 10,
                result_count=i + 1,
                cache_hits=i,
                cache_misses=1,
                memory_usage_mb=50.0,
                error_count=0,
                searcher_count=2,
                repository_path="/repo",
                branch="main"
            )
            analytics_instance.record_event(event)
        
        metrics = analytics_instance.get_performance_metrics()
        
        assert metrics.total_searches == 5
        assert metrics.avg_duration_ms > 0
        assert 0 <= metrics.cache_hit_rate <= 1
        assert metrics.error_rate >= 0

    def test_cleanup_old_events(self, analytics_instance: SearchAnalytics) -> None:
        """Test cleanup of old events."""
        # Create old event (beyond retention period)
        old_event = SearchEvent(
            timestamp=datetime.now() - analytics_instance.retention_period - analytics_instance.retention_period,
            query_hash="old_hash",
            search_types=[SearchType.CONTENT],
            duration_ms=100.0,
            result_count=1,
            cache_hits=0,
            cache_misses=1,
            memory_usage_mb=50.0,
            error_count=0,
            searcher_count=1,
            repository_path="/repo",
            branch="main"
        )
        
        # Create recent event
        recent_event = SearchEvent(
            timestamp=datetime.now(),
            query_hash="recent_hash",
            search_types=[SearchType.CONTENT],
            duration_ms=100.0,
            result_count=1,
            cache_hits=0,
            cache_misses=1,
            memory_usage_mb=50.0,
            error_count=0,
            searcher_count=1,
            repository_path="/repo",
            branch="main"
        )
        
        analytics_instance.record_event(old_event)
        analytics_instance.record_event(recent_event)
        
        initial_count = len(analytics_instance.events)
        analytics_instance.cleanup_old_events()
        
        # Should have removed old event but kept recent one
        assert len(analytics_instance.events) < initial_count
        assert any(event.query_hash == "recent_hash" for event in analytics_instance.events)

    def test_export_analytics_data(self, analytics_instance: SearchAnalytics) -> None:
        """Test exporting analytics data."""
        # Add some test data
        event = SearchEvent(
            timestamp=datetime.now(),
            query_hash="export_test",
            search_types=[SearchType.CONTENT],
            duration_ms=100.0,
            result_count=1,
            cache_hits=0,
            cache_misses=1,
            memory_usage_mb=50.0,
            error_count=0,
            searcher_count=1,
            repository_path="/repo",
            branch="main"
        )
        analytics_instance.record_event(event)
        
        # Export data
        exported_data = analytics_instance.export_data()
        
        assert "events" in exported_data
        assert "performance_metrics" in exported_data
        assert len(exported_data["events"]) >= 1

    def test_get_search_trends(self, analytics_instance: SearchAnalytics) -> None:
        """Test getting search trends."""
        # Add events with different search types
        search_types = [SearchType.CONTENT, SearchType.AUTHOR, SearchType.CONTENT]
        
        for i, search_type in enumerate(search_types):
            event = SearchEvent(
                timestamp=datetime.now(),
                query_hash=f"trend_hash_{i}",
                search_types=[search_type],
                duration_ms=100.0,
                result_count=1,
                cache_hits=0,
                cache_misses=1,
                memory_usage_mb=50.0,
                error_count=0,
                searcher_count=1,
                repository_path="/repo",
                branch="main"
            )
            analytics_instance.record_event(event)
        
        trends = analytics_instance.get_search_trends()
        
        assert "search_type_distribution" in trends
        assert "temporal_patterns" in trends

    def test_max_events_limit(self) -> None:
        """Test that max events limit is enforced."""
        analytics = SearchAnalytics(max_events=3)
        
        # Add more events than the limit
        for i in range(5):
            event = SearchEvent(
                timestamp=datetime.now(),
                query_hash=f"limit_hash_{i}",
                search_types=[SearchType.CONTENT],
                duration_ms=100.0,
                result_count=1,
                cache_hits=0,
                cache_misses=1,
                memory_usage_mb=50.0,
                error_count=0,
                searcher_count=1,
                repository_path="/repo",
                branch="main"
            )
            analytics.record_event(event)
        
        # Should not exceed max_events limit
        assert len(analytics.events) <= 3


@pytest.mark.integration
class TestAnalyticsIntegration:
    """Integration tests for analytics components."""

    def test_end_to_end_analytics_workflow(self) -> None:
        """Test complete analytics workflow."""
        analytics = SearchAnalytics(
            retention_days=7,
            max_events=100,
            enable_performance_tracking=True
        )
        
        # Simulate search operations
        for i in range(10):
            event = SearchEvent(
                timestamp=datetime.now(),
                query_hash=f"workflow_hash_{i}",
                search_types=[SearchType.CONTENT if i % 2 == 0 else SearchType.AUTHOR],
                duration_ms=100.0 + i * 5,
                result_count=i + 1,
                cache_hits=i // 2,
                cache_misses=i - (i // 2),
                memory_usage_mb=50.0 + i,
                error_count=1 if i == 5 else 0,  # One error
                searcher_count=2,
                repository_path="/repo",
                branch="main"
            )
            analytics.record_event(event)
        
        # Verify analytics data
        assert len(analytics.events) == 10
        
        metrics = analytics.get_performance_metrics()
        assert metrics.total_searches == 10
        assert metrics.error_rate > 0  # Should detect the error
        
        trends = analytics.get_search_trends()
        assert len(trends["search_type_distribution"]) > 0
        
        exported = analytics.export_data()
        assert len(exported["events"]) == 10
