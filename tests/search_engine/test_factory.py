"""Tests for SearchEngineFactory and related components."""

from unittest.mock import Mock, patch

import pytest

from githound.models import SearchEngineConfig, SearchQuery, SearchType
from githound.search_engine.analytics import SearchAnalytics
from githound.search_engine.factory import (
    SearchEngineFactory,
    create_search_orchestrator,
    get_default_factory,
    initialize_default_registry,
)
from githound.search_engine.registry import SearcherMetadata, SearcherRegistry


class TestSearchEngineFactory:
    """Test cases for SearchEngineFactory."""

    def test_factory_initialization(self):
        """Test factory initialization with default config."""
        factory = SearchEngineFactory()
        assert factory.config is not None
        assert isinstance(factory.config, SearchEngineConfig)

    def test_factory_with_custom_config(self):
        """Test factory initialization with custom config."""
        config = SearchEngineConfig(
            enable_advanced_searchers=False, max_workers=2, enable_caching=False
        )
        factory = SearchEngineFactory(config)
        assert factory.config == config
        assert factory.config.max_workers == 2

    def test_create_orchestrator_basic(self):
        """Test creating basic orchestrator."""
        config = SearchEngineConfig(enable_advanced_searchers=False, enable_basic_searchers=True)
        factory = SearchEngineFactory(config)
        orchestrator = factory.create_orchestrator()

        assert orchestrator is not None
        assert len(orchestrator._searchers) > 0
        # Should have basic searchers only
        searcher_names = [s.name for s in orchestrator._searchers]
        assert "commit_hash" in searcher_names
        assert "author" in searcher_names
        assert "content" in searcher_names

    def test_create_orchestrator_advanced(self):
        """Test creating orchestrator with advanced searchers."""
        config = SearchEngineConfig(enable_advanced_searchers=True, enable_basic_searchers=True)
        factory = SearchEngineFactory(config)
        orchestrator = factory.create_orchestrator()

        assert orchestrator is not None
        assert len(orchestrator._searchers) > 5  # Should have both basic and advanced
        searcher_names = [s.name for s in orchestrator._searchers]
        assert "advanced" in searcher_names or any("advanced" in name for name in searcher_names)

    def test_create_orchestrator_with_overrides(self):
        """Test creating orchestrator with parameter overrides."""
        config = SearchEngineConfig(enable_advanced_searchers=False)
        factory = SearchEngineFactory(config)

        # Override to enable advanced
        orchestrator = factory.create_orchestrator(enable_advanced=True)
        assert orchestrator is not None

    @patch("githound.search_engine.factory.RedisCache")
    def test_create_cache_redis(self, mock_redis):
        """Test creating Redis cache."""
        config = SearchEngineConfig(enable_caching=True, cache_backend="redis")
        factory = SearchEngineFactory(config)
        cache = factory._create_cache()

        assert cache is not None
        mock_redis.assert_called_once()

    def test_create_cache_memory(self):
        """Test creating memory cache."""
        config = SearchEngineConfig(enable_caching=True, cache_backend="memory")
        factory = SearchEngineFactory(config)
        cache = factory._create_cache()

        assert cache is not None

    def test_create_ranking_engine(self):
        """Test creating ranking engine."""
        factory = SearchEngineFactory()
        ranking_engine = factory._create_ranking_engine()

        assert ranking_engine is not None
        assert hasattr(ranking_engine, "rank_results")

    def test_create_result_processor(self):
        """Test creating result processor."""
        factory = SearchEngineFactory()
        processor = factory._create_result_processor()

        assert processor is not None
        assert hasattr(processor, "process_results")

    def test_create_analytics(self):
        """Test creating analytics."""
        config = SearchEngineConfig(enable_analytics=True)
        factory = SearchEngineFactory(config)
        analytics = factory._create_analytics()

        assert analytics is not None
        assert isinstance(analytics, SearchAnalytics)

    def test_create_for_query_basic(self):
        """Test creating orchestrator optimized for basic query."""
        factory = SearchEngineFactory()
        query = SearchQuery(content_pattern="test")

        orchestrator = factory.create_for_query(query)
        assert orchestrator is not None

    def test_create_for_query_advanced(self):
        """Test creating orchestrator optimized for advanced query."""
        factory = SearchEngineFactory()
        query = SearchQuery(content_pattern="test", branch_analysis=True, statistical_analysis=True)

        orchestrator = factory.create_for_query(query)
        assert orchestrator is not None

    def test_get_available_searchers(self):
        """Test getting available searchers."""
        factory = SearchEngineFactory()
        searchers = factory.get_available_searchers()

        assert isinstance(searchers, dict)
        assert len(searchers) > 0
        assert "commit_hash" in searchers
        assert "content" in searchers

    def test_create_custom_orchestrator(self):
        """Test creating custom orchestrator with specific searchers."""
        factory = SearchEngineFactory()
        searcher_names = ["commit_hash", "author", "content"]

        orchestrator = factory.create_custom_orchestrator(searcher_names)
        assert orchestrator is not None
        assert len(orchestrator._searchers) == len(searcher_names)


class TestGlobalFactory:
    """Test cases for global factory functions."""

    def test_get_default_factory(self):
        """Test getting default factory instance."""
        factory1 = get_default_factory()
        factory2 = get_default_factory()

        # Should return same instance
        assert factory1 is factory2
        assert isinstance(factory1, SearchEngineFactory)

    def test_create_search_orchestrator_function(self):
        """Test convenience function for creating orchestrator."""
        orchestrator = create_search_orchestrator()
        assert orchestrator is not None

    def test_create_search_orchestrator_with_config(self):
        """Test convenience function with custom config."""
        config = SearchEngineConfig(max_workers=2)
        orchestrator = create_search_orchestrator(config=config)
        assert orchestrator is not None


class TestSearcherRegistry:
    """Test cases for SearcherRegistry."""

    def test_registry_initialization(self):
        """Test registry initialization."""
        registry = SearcherRegistry()
        assert registry is not None
        assert len(registry._searchers) == 0

    def test_register_searcher(self):
        """Test registering a searcher."""
        from githound.search_engine.commit_searcher import CommitHashSearcher

        registry = SearcherRegistry()
        metadata = SearcherMetadata(
            name="test_searcher",
            description="Test searcher",
            search_types=[SearchType.COMMIT_HASH],
            capabilities=["commit_search"],
        )

        registry.register_searcher(CommitHashSearcher, metadata)
        assert "test_searcher" in registry._searchers
        assert registry.get_metadata("test_searcher") == metadata

    def test_get_searcher_instance(self):
        """Test getting searcher instance."""
        from githound.search_engine.commit_searcher import CommitHashSearcher

        registry = SearcherRegistry()
        metadata = SearcherMetadata(
            name="test_searcher",
            description="Test searcher",
            search_types=[SearchType.COMMIT_HASH],
            capabilities=["commit_search"],
        )

        registry.register_searcher(CommitHashSearcher, metadata)
        instance = registry.get_searcher_instance("test_searcher")

        assert instance is not None
        assert isinstance(instance, CommitHashSearcher)

    def test_list_searchers(self):
        """Test listing searchers."""
        from githound.search_engine.commit_searcher import CommitHashSearcher

        registry = SearcherRegistry()
        metadata = SearcherMetadata(
            name="test_searcher",
            description="Test searcher",
            search_types=[SearchType.COMMIT_HASH],
            capabilities=["commit_search"],
            enabled=True,
        )

        registry.register_searcher(CommitHashSearcher, metadata)
        searchers = registry.list_searchers()

        assert "test_searcher" in searchers

    def test_get_searchers_for_query(self):
        """Test getting searchers for a specific query."""
        from githound.search_engine.commit_searcher import CommitHashSearcher

        registry = SearcherRegistry()
        metadata = SearcherMetadata(
            name="commit_searcher",
            description="Commit searcher",
            search_types=[SearchType.COMMIT_HASH],
            capabilities=["commit_search"],
        )

        registry.register_searcher(CommitHashSearcher, metadata)

        query = SearchQuery(commit_hash="abc123")
        searchers = registry.get_searchers_for_query(query)

        assert "commit_searcher" in searchers

    def test_performance_estimate(self):
        """Test getting performance estimate."""
        from githound.search_engine.commit_searcher import CommitHashSearcher

        registry = SearcherRegistry()
        metadata = SearcherMetadata(
            name="test_searcher",
            description="Test searcher",
            search_types=[SearchType.COMMIT_HASH],
            capabilities=["commit_search"],
            performance_cost=3,
            memory_usage=2,
        )

        registry.register_searcher(CommitHashSearcher, metadata)
        estimate = registry.get_performance_estimate(["test_searcher"])

        assert estimate["total_performance_cost"] == 3
        assert estimate["total_memory_usage"] == 2
        assert estimate["searcher_count"] == 1

    def test_enable_disable_searcher(self):
        """Test enabling and disabling searchers."""
        from githound.search_engine.commit_searcher import CommitHashSearcher

        registry = SearcherRegistry()
        metadata = SearcherMetadata(
            name="test_searcher",
            description="Test searcher",
            search_types=[SearchType.COMMIT_HASH],
            capabilities=["commit_search"],
        )

        registry.register_searcher(CommitHashSearcher, metadata)

        # Test disable
        assert registry.disable_searcher("test_searcher")
        assert not registry.get_metadata("test_searcher").enabled

        # Test enable
        assert registry.enable_searcher("test_searcher")
        assert registry.get_metadata("test_searcher").enabled

    def test_registry_stats(self):
        """Test getting registry statistics."""
        registry = SearcherRegistry()
        stats = registry.get_registry_stats()

        assert "total_searchers" in stats
        assert "enabled_searchers" in stats
        assert "unique_capabilities" in stats

    def test_initialize_default_registry(self):
        """Test initializing default registry."""
        registry = initialize_default_registry()

        assert registry is not None
        assert len(registry._searchers) > 0

        # Check that basic searchers are registered
        searcher_names = list(registry._searchers.keys())
        assert "commit_hash" in searcher_names
        assert "author" in searcher_names
        assert "content" in searcher_names


@pytest.mark.asyncio
class TestSearchEngineIntegration:
    """Integration tests for the complete search engine."""

    async def test_end_to_end_search(self):
        """Test complete search workflow using factory."""
        # This would require a real git repository
        # For now, just test that the components work together
        factory = SearchEngineFactory()
        orchestrator = factory.create_orchestrator()

        assert orchestrator is not None
        assert len(orchestrator._searchers) > 0

    async def test_query_optimization(self):
        """Test that factory optimizes orchestrator for query type."""
        factory = SearchEngineFactory()

        # Basic query
        basic_query = SearchQuery(content_pattern="test")
        basic_orchestrator = factory.create_for_query(basic_query)

        # Advanced query
        advanced_query = SearchQuery(
            content_pattern="test", branch_analysis=True, statistical_analysis=True
        )
        advanced_orchestrator = factory.create_for_query(advanced_query)

        # Advanced orchestrator should have more searchers
        assert len(advanced_orchestrator._searchers) >= len(basic_orchestrator._searchers)


if __name__ == "__main__":
    pytest.main([__file__])
