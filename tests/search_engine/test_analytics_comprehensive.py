"""Comprehensive tests for GitHound search engine analytics module."""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
from typing import Any, Dict, List

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
def sample_search_query() -> SearchQuery:
    """Create sample search query for testing."""
    return SearchQuery(
        content_pattern="test",
        author_pattern="Test User",
        message_pattern="commit",
        fuzzy_search=True,
        fuzzy_threshold=0.8
    )


@pytest.fixture
def sample_search_results() -> List[SearchResult]:
    """Create sample search results for testing."""
    return [
        SearchResult(
            commit_hash="abc123",
            file_path="test1.py",
            line_number=10,
            matching_line="def test_function():",
            search_type=SearchType.CONTENT,
            relevance_score=0.95
        ),
        SearchResult(
            commit_hash="def456",
            file_path="test2.py", 
            line_number=20,
            matching_line="class TestClass:",
            search_type=SearchType.CONTENT,
            relevance_score=0.85
        )
    ]


class TestSearchAnalytics:
    """Test SearchAnalytics class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.analytics = SearchAnalytics()

    @pytest.mark.asyncio
    async def test_analytics_initialization(self, analytics_config: AnalyticsConfig) -> None:
        """Test analytics initialization."""
        analytics = SearchAnalytics(config=analytics_config)
        
        assert analytics.config == analytics_config
        assert analytics.enabled == analytics_config.enabled
        assert analytics._metrics == {}
        assert analytics._performance_data == []

    @pytest.mark.asyncio
    async def test_start_search_tracking(self, sample_search_query: SearchQuery) -> None:
        """Test starting search tracking."""
        search_id = await self.analytics.start_search(
            query=sample_search_query,
            repo_path="/test/repo",
            branch="main"
        )
        
        assert search_id is not None
        assert len(search_id) > 0
        assert search_id in self.analytics._metrics

    @pytest.mark.asyncio
    async def test_end_search_tracking(
        self, 
        sample_search_query: SearchQuery,
        sample_search_results: List[SearchResult]
    ) -> None:
        """Test ending search tracking."""
        search_id = await self.analytics.start_search(
            query=sample_search_query,
            repo_path="/test/repo"
        )
        
        metrics = await self.analytics.end_search(
            search_id=search_id,
            results=sample_search_results,
            duration=1.5
        )
        
        assert metrics is not None
        assert metrics.search_id == search_id
        assert metrics.result_count == len(sample_search_results)
        assert metrics.duration == 1.5
        assert metrics.query == sample_search_query

    @pytest.mark.asyncio
    async def test_record_performance_metrics(self) -> None:
        """Test recording performance metrics."""
        await self.analytics.record_performance(
            operation="search",
            duration=2.5,
            memory_usage=1024,
            cpu_usage=0.75
        )
        
        assert len(self.analytics._performance_data) == 1
        perf_data = self.analytics._performance_data[0]
        assert perf_data["operation"] == "search"
        assert perf_data["duration"] == 2.5
        assert perf_data["memory_usage"] == 1024
        assert perf_data["cpu_usage"] == 0.75

    @pytest.mark.asyncio
    async def test_get_search_statistics(self, sample_search_query: SearchQuery) -> None:
        """Test getting search statistics."""
        # Record multiple searches
        for i in range(3):
            search_id = await self.analytics.start_search(
                query=sample_search_query,
                repo_path=f"/test/repo{i}"
            )
            await self.analytics.end_search(
                search_id=search_id,
                results=[],
                duration=float(i + 1)
            )
        
        stats = await self.analytics.get_statistics()
        
        assert stats["total_searches"] == 3
        assert stats["average_duration"] == 2.0  # (1+2+3)/3
        assert "total_results" in stats
        assert "performance_metrics" in stats

    @pytest.mark.asyncio
    async def test_export_analytics_data(self, analytics_config: AnalyticsConfig) -> None:
        """Test exporting analytics data."""
        analytics = SearchAnalytics(config=analytics_config)
        
        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            await analytics.export_data("/test/export.json")
            
            mock_open.assert_called_once()
            mock_file.write.assert_called()

    @pytest.mark.asyncio
    async def test_analytics_disabled(self) -> None:
        """Test analytics when disabled."""
        config = AnalyticsConfig(enabled=False)
        analytics = SearchAnalytics(config=config)
        
        search_id = await analytics.start_search(
            query=SearchQuery(content_pattern="test"),
            repo_path="/test/repo"
        )
        
        # Should return None when disabled
        assert search_id is None
        assert len(analytics._metrics) == 0


class TestPerformanceTracker:
    """Test PerformanceTracker class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.tracker = PerformanceTracker()

    @pytest.mark.asyncio
    async def test_track_operation_context_manager(self) -> None:
        """Test tracking operation using context manager."""
        async with self.tracker.track("test_operation") as tracker:
            await asyncio.sleep(0.1)  # Simulate work
            tracker.add_metric("items_processed", 100)
        
        metrics = self.tracker.get_metrics("test_operation")
        assert len(metrics) == 1
        assert metrics[0]["operation"] == "test_operation"
        assert metrics[0]["duration"] >= 0.1
        assert metrics[0]["items_processed"] == 100

    @pytest.mark.asyncio
    async def test_track_multiple_operations(self) -> None:
        """Test tracking multiple operations."""
        operations = ["search", "index", "export"]
        
        for op in operations:
            async with self.tracker.track(op):
                await asyncio.sleep(0.05)
        
        for op in operations:
            metrics = self.tracker.get_metrics(op)
            assert len(metrics) == 1
            assert metrics[0]["operation"] == op

    def test_get_performance_summary(self) -> None:
        """Test getting performance summary."""
        # Add some mock data
        self.tracker._metrics = {
            "search": [
                {"duration": 1.0, "memory": 100},
                {"duration": 2.0, "memory": 200}
            ],
            "index": [
                {"duration": 0.5, "memory": 50}
            ]
        }
        
        summary = self.tracker.get_summary()
        
        assert "search" in summary
        assert "index" in summary
        assert summary["search"]["count"] == 2
        assert summary["search"]["avg_duration"] == 1.5
        assert summary["index"]["count"] == 1
        assert summary["index"]["avg_duration"] == 0.5


class TestMetricsCollector:
    """Test MetricsCollector class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.collector = MetricsCollector()

    @pytest.mark.asyncio
    async def test_collect_system_metrics(self) -> None:
        """Test collecting system metrics."""
        with patch('psutil.cpu_percent', return_value=50.0):
            with patch('psutil.virtual_memory') as mock_memory:
                mock_memory.return_value.percent = 60.0
                mock_memory.return_value.used = 1024 * 1024 * 1024  # 1GB
                
                metrics = await self.collector.collect_system_metrics()
                
                assert metrics["cpu_percent"] == 50.0
                assert metrics["memory_percent"] == 60.0
                assert metrics["memory_used"] == 1024 * 1024 * 1024

    @pytest.mark.asyncio
    async def test_collect_search_metrics(
        self,
        sample_search_query: SearchQuery,
        sample_search_results: List[SearchResult]
    ) -> None:
        """Test collecting search-specific metrics."""
        metrics = await self.collector.collect_search_metrics(
            query=sample_search_query,
            results=sample_search_results,
            duration=1.5,
            repo_path="/test/repo"
        )
        
        assert metrics["query_complexity"] > 0
        assert metrics["result_count"] == len(sample_search_results)
        assert metrics["duration"] == 1.5
        assert metrics["repo_path"] == "/test/repo"
        assert "timestamp" in metrics

    @pytest.mark.asyncio
    async def test_export_metrics_json(self) -> None:
        """Test exporting metrics to JSON."""
        test_metrics = {"test": "data", "count": 42}
        
        with patch('builtins.open', create=True) as mock_open:
            with patch('json.dump') as mock_json_dump:
                mock_file = MagicMock()
                mock_open.return_value.__enter__.return_value = mock_file
                
                await self.collector.export_metrics(
                    metrics=test_metrics,
                    filepath="/test/metrics.json",
                    format="json"
                )
                
                mock_open.assert_called_once_with("/test/metrics.json", "w")
                mock_json_dump.assert_called_once_with(test_metrics, mock_file, indent=2)

    @pytest.mark.asyncio
    async def test_export_metrics_csv(self) -> None:
        """Test exporting metrics to CSV."""
        test_metrics = [
            {"operation": "search", "duration": 1.0},
            {"operation": "index", "duration": 2.0}
        ]
        
        with patch('builtins.open', create=True) as mock_open:
            with patch('csv.DictWriter') as mock_csv_writer:
                mock_file = MagicMock()
                mock_open.return_value.__enter__.return_value = mock_file
                mock_writer = MagicMock()
                mock_csv_writer.return_value = mock_writer
                
                await self.collector.export_metrics(
                    metrics=test_metrics,
                    filepath="/test/metrics.csv",
                    format="csv"
                )
                
                mock_open.assert_called_once_with("/test/metrics.csv", "w", newline="")
                mock_writer.writeheader.assert_called_once()
                mock_writer.writerows.assert_called_once_with(test_metrics)


@pytest.mark.integration
class TestAnalyticsIntegration:
    """Integration tests for analytics components."""

    @pytest.mark.asyncio
    async def test_end_to_end_analytics_workflow(
        self,
        analytics_config: AnalyticsConfig,
        sample_search_query: SearchQuery,
        sample_search_results: List[SearchResult]
    ) -> None:
        """Test complete analytics workflow."""
        analytics = SearchAnalytics(config=analytics_config)
        
        # Start search
        search_id = await analytics.start_search(
            query=sample_search_query,
            repo_path="/test/repo",
            branch="main"
        )
        
        # Record performance during search
        await analytics.record_performance(
            operation="search_execution",
            duration=1.2,
            memory_usage=512,
            cpu_usage=0.6
        )
        
        # End search
        metrics = await analytics.end_search(
            search_id=search_id,
            results=sample_search_results,
            duration=1.5
        )
        
        # Verify complete workflow
        assert metrics is not None
        assert metrics.search_id == search_id
        assert len(analytics._performance_data) == 1
        
        # Get statistics
        stats = await analytics.get_statistics()
        assert stats["total_searches"] == 1
        assert stats["total_results"] == len(sample_search_results)
