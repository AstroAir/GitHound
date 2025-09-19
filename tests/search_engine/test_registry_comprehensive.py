"""Comprehensive tests for GitHound search engine registry module."""

import pytest
from typing import List, Dict, Any, Type
from unittest.mock import Mock, AsyncMock

from githound.search_engine.registry import (
    SearcherRegistry,
    SearcherInfo,
    RegistryConfig,
    SearcherCapability,
    SearcherPriority
)
from githound.search_engine.base import BaseSearcher, SearchContext
from githound.search_engine import (
    CommitHashSearcher,
    AuthorSearcher,
    ContentSearcher,
    FuzzySearcher
)
from githound.models import SearchQuery, SearchType


@pytest.fixture
def registry_config() -> RegistryConfig:
    """Create registry configuration for testing."""
    return RegistryConfig(
        auto_register_defaults=True,
        enable_priority_sorting=True,
        allow_duplicate_types=False,
        max_searchers=50
    )


@pytest.fixture
def mock_searcher() -> Mock:
    """Create a mock searcher for testing."""
    searcher = Mock(spec=BaseSearcher)
    searcher.name = "MockSearcher"
    searcher.search_types = [SearchType.CONTENT]
    searcher.priority = SearcherPriority.NORMAL
    searcher.can_handle = AsyncMock(return_value=True)
    searcher.search = AsyncMock(return_value=[])
    return searcher


@pytest.fixture
def sample_searcher_info() -> SearcherInfo:
    """Create sample searcher info for testing."""
    return SearcherInfo(
        name="TestSearcher",
        searcher_class=ContentSearcher,
        search_types=[SearchType.CONTENT],
        priority=SearcherPriority.HIGH,
        capabilities=[SearcherCapability.FUZZY_SEARCH],
        description="Test searcher for unit tests"
    )


class TestSearcherRegistry:
    """Test SearcherRegistry class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.registry = SearcherRegistry()

    def test_registry_initialization(self, registry_config: RegistryConfig) -> None:
        """Test registry initialization."""
        registry = SearcherRegistry(config=registry_config)
        
        assert registry.config == registry_config
        assert len(registry._searchers) == 0
        assert len(registry._searcher_info) == 0

    def test_register_searcher_basic(self, mock_searcher: Mock) -> None:
        """Test basic searcher registration."""
        result = self.registry.register_searcher(mock_searcher)
        
        assert result is True
        assert len(self.registry._searchers) == 1
        assert mock_searcher.name in self.registry._searcher_info

    def test_register_searcher_with_info(
        self,
        mock_searcher: Mock,
        sample_searcher_info: SearcherInfo
    ) -> None:
        """Test registering searcher with custom info."""
        result = self.registry.register_searcher(mock_searcher, sample_searcher_info)
        
        assert result is True
        assert self.registry._searcher_info[mock_searcher.name] == sample_searcher_info

    def test_register_duplicate_searcher(self, mock_searcher: Mock) -> None:
        """Test registering duplicate searcher."""
        # Register first time
        result1 = self.registry.register_searcher(mock_searcher)
        assert result1 is True
        
        # Try to register again
        result2 = self.registry.register_searcher(mock_searcher)
        assert result2 is False  # Should fail
        assert len(self.registry._searchers) == 1

    def test_register_searcher_class(self) -> None:
        """Test registering searcher by class."""
        result = self.registry.register_searcher_class(
            ContentSearcher,
            priority=SearcherPriority.HIGH
        )
        
        assert result is True
        assert len(self.registry._searchers) == 1
        
        # Check that instance was created
        searcher_names = list(self.registry._searcher_info.keys())
        assert len(searcher_names) == 1

    def test_unregister_searcher(self, mock_searcher: Mock) -> None:
        """Test unregistering searcher."""
        # Register first
        self.registry.register_searcher(mock_searcher)
        assert len(self.registry._searchers) == 1
        
        # Unregister
        result = self.registry.unregister_searcher(mock_searcher.name)
        assert result is True
        assert len(self.registry._searchers) == 0
        assert mock_searcher.name not in self.registry._searcher_info

    def test_unregister_nonexistent_searcher(self) -> None:
        """Test unregistering non-existent searcher."""
        result = self.registry.unregister_searcher("NonExistent")
        assert result is False

    def test_get_searcher_by_name(self, mock_searcher: Mock) -> None:
        """Test getting searcher by name."""
        self.registry.register_searcher(mock_searcher)
        
        retrieved = self.registry.get_searcher(mock_searcher.name)
        assert retrieved == mock_searcher

    def test_get_nonexistent_searcher(self) -> None:
        """Test getting non-existent searcher."""
        retrieved = self.registry.get_searcher("NonExistent")
        assert retrieved is None

    def test_get_searchers_by_type(self, mock_searcher: Mock) -> None:
        """Test getting searchers by search type."""
        self.registry.register_searcher(mock_searcher)
        
        searchers = self.registry.get_searchers_by_type(SearchType.CONTENT)
        assert len(searchers) == 1
        assert searchers[0] == mock_searcher

    def test_get_searchers_by_capability(self) -> None:
        """Test getting searchers by capability."""
        # Register fuzzy searcher
        fuzzy_searcher = FuzzySearcher()
        self.registry.register_searcher(
            fuzzy_searcher,
            SearcherInfo(
                name="FuzzySearcher",
                searcher_class=FuzzySearcher,
                search_types=[SearchType.CONTENT],
                priority=SearcherPriority.NORMAL,
                capabilities=[SearcherCapability.FUZZY_SEARCH]
            )
        )
        
        searchers = self.registry.get_searchers_by_capability(SearcherCapability.FUZZY_SEARCH)
        assert len(searchers) == 1
        assert searchers[0] == fuzzy_searcher

    @pytest.mark.asyncio
    async def test_get_applicable_searchers(self, mock_searcher: Mock) -> None:
        """Test getting applicable searchers for a query."""
        self.registry.register_searcher(mock_searcher)
        
        query = SearchQuery(content_pattern="test")
        searchers = await self.registry.get_applicable_searchers(query)
        
        assert len(searchers) == 1
        assert searchers[0] == mock_searcher
        mock_searcher.can_handle.assert_called_once_with(query)

    @pytest.mark.asyncio
    async def test_get_applicable_searchers_with_filtering(self) -> None:
        """Test getting applicable searchers with filtering."""
        # Create searchers with different capabilities
        content_searcher = Mock(spec=BaseSearcher)
        content_searcher.name = "ContentSearcher"
        content_searcher.can_handle = AsyncMock(return_value=True)
        
        author_searcher = Mock(spec=BaseSearcher)
        author_searcher.name = "AuthorSearcher"
        author_searcher.can_handle = AsyncMock(return_value=False)
        
        self.registry.register_searcher(content_searcher)
        self.registry.register_searcher(author_searcher)
        
        query = SearchQuery(content_pattern="test")
        searchers = await self.registry.get_applicable_searchers(query)
        
        # Only content searcher should be returned
        assert len(searchers) == 1
        assert searchers[0] == content_searcher

    def test_list_all_searchers(self, mock_searcher: Mock) -> None:
        """Test listing all registered searchers."""
        self.registry.register_searcher(mock_searcher)
        
        all_searchers = self.registry.list_searchers()
        assert len(all_searchers) == 1
        assert all_searchers[0] == mock_searcher

    def test_get_searcher_info(self, mock_searcher: Mock, sample_searcher_info: SearcherInfo) -> None:
        """Test getting searcher information."""
        self.registry.register_searcher(mock_searcher, sample_searcher_info)
        
        info = self.registry.get_searcher_info(mock_searcher.name)
        assert info == sample_searcher_info

    def test_update_searcher_priority(self, mock_searcher: Mock) -> None:
        """Test updating searcher priority."""
        self.registry.register_searcher(mock_searcher)
        
        result = self.registry.update_searcher_priority(
            mock_searcher.name,
            SearcherPriority.HIGH
        )
        
        assert result is True
        info = self.registry.get_searcher_info(mock_searcher.name)
        assert info.priority == SearcherPriority.HIGH

    def test_clear_registry(self, mock_searcher: Mock) -> None:
        """Test clearing the registry."""
        self.registry.register_searcher(mock_searcher)
        assert len(self.registry._searchers) == 1
        
        self.registry.clear()
        assert len(self.registry._searchers) == 0
        assert len(self.registry._searcher_info) == 0

    def test_registry_statistics(self, mock_searcher: Mock) -> None:
        """Test getting registry statistics."""
        self.registry.register_searcher(mock_searcher)
        
        stats = self.registry.get_statistics()
        
        assert stats["total_searchers"] == 1
        assert stats["searchers_by_type"][SearchType.CONTENT] == 1
        assert stats["searchers_by_priority"][SearcherPriority.NORMAL] == 1


class TestSearcherInfo:
    """Test SearcherInfo class."""

    def test_searcher_info_creation(self) -> None:
        """Test creating searcher info."""
        info = SearcherInfo(
            name="TestSearcher",
            searcher_class=ContentSearcher,
            search_types=[SearchType.CONTENT, SearchType.FILE_PATH],
            priority=SearcherPriority.HIGH,
            capabilities=[SearcherCapability.FUZZY_SEARCH, SearcherCapability.REGEX_SEARCH],
            description="Test searcher"
        )
        
        assert info.name == "TestSearcher"
        assert info.searcher_class == ContentSearcher
        assert len(info.search_types) == 2
        assert info.priority == SearcherPriority.HIGH
        assert len(info.capabilities) == 2
        assert info.description == "Test searcher"

    def test_searcher_info_equality(self) -> None:
        """Test searcher info equality comparison."""
        info1 = SearcherInfo(
            name="TestSearcher",
            searcher_class=ContentSearcher,
            search_types=[SearchType.CONTENT],
            priority=SearcherPriority.NORMAL
        )
        
        info2 = SearcherInfo(
            name="TestSearcher",
            searcher_class=ContentSearcher,
            search_types=[SearchType.CONTENT],
            priority=SearcherPriority.NORMAL
        )
        
        info3 = SearcherInfo(
            name="DifferentSearcher",
            searcher_class=ContentSearcher,
            search_types=[SearchType.CONTENT],
            priority=SearcherPriority.NORMAL
        )
        
        assert info1 == info2
        assert info1 != info3

    def test_searcher_info_string_representation(self) -> None:
        """Test searcher info string representation."""
        info = SearcherInfo(
            name="TestSearcher",
            searcher_class=ContentSearcher,
            search_types=[SearchType.CONTENT],
            priority=SearcherPriority.HIGH
        )
        
        str_repr = str(info)
        assert "TestSearcher" in str_repr
        assert "HIGH" in str_repr


class TestSearcherPriority:
    """Test SearcherPriority enum."""

    def test_priority_ordering(self) -> None:
        """Test priority ordering."""
        priorities = [
            SearcherPriority.LOW,
            SearcherPriority.NORMAL,
            SearcherPriority.HIGH,
            SearcherPriority.CRITICAL
        ]
        
        # Test that priorities are ordered correctly
        for i in range(len(priorities) - 1):
            assert priorities[i].value < priorities[i + 1].value

    def test_priority_comparison(self) -> None:
        """Test priority comparison operations."""
        assert SearcherPriority.HIGH > SearcherPriority.NORMAL
        assert SearcherPriority.NORMAL > SearcherPriority.LOW
        assert SearcherPriority.CRITICAL > SearcherPriority.HIGH


class TestSearcherCapability:
    """Test SearcherCapability enum."""

    def test_capability_values(self) -> None:
        """Test capability enum values."""
        capabilities = [
            SearcherCapability.FUZZY_SEARCH,
            SearcherCapability.REGEX_SEARCH,
            SearcherCapability.CASE_INSENSITIVE,
            SearcherCapability.MULTI_LINE,
            SearcherCapability.CONTEXT_AWARE
        ]
        
        # All capabilities should have unique values
        values = [cap.value for cap in capabilities]
        assert len(values) == len(set(values))


@pytest.mark.integration
class TestRegistryIntegration:
    """Integration tests for registry components."""

    def test_registry_with_real_searchers(self) -> None:
        """Test registry with real searcher implementations."""
        registry = SearcherRegistry()
        
        # Register real searchers
        searchers = [
            CommitHashSearcher(),
            AuthorSearcher(),
            ContentSearcher(),
            FuzzySearcher()
        ]
        
        for searcher in searchers:
            registry.register_searcher(searcher)
        
        assert len(registry.list_searchers()) == len(searchers)

    @pytest.mark.asyncio
    async def test_registry_query_routing(self) -> None:
        """Test query routing through registry."""
        registry = SearcherRegistry()
        
        # Register searchers
        content_searcher = ContentSearcher()
        author_searcher = AuthorSearcher()
        
        registry.register_searcher(content_searcher)
        registry.register_searcher(author_searcher)
        
        # Test content query
        content_query = SearchQuery(content_pattern="test")
        content_searchers = await registry.get_applicable_searchers(content_query)
        
        # Test author query
        author_query = SearchQuery(author_pattern="john")
        author_searchers = await registry.get_applicable_searchers(author_query)
        
        # Verify appropriate searchers are selected
        assert len(content_searchers) >= 1
        assert len(author_searchers) >= 1

    def test_registry_priority_sorting(self) -> None:
        """Test searcher priority sorting."""
        registry = SearcherRegistry()
        
        # Register searchers with different priorities
        low_searcher = Mock(spec=BaseSearcher)
        low_searcher.name = "LowPriority"
        low_searcher.priority = SearcherPriority.LOW
        
        high_searcher = Mock(spec=BaseSearcher)
        high_searcher.name = "HighPriority"
        high_searcher.priority = SearcherPriority.HIGH
        
        normal_searcher = Mock(spec=BaseSearcher)
        normal_searcher.name = "NormalPriority"
        normal_searcher.priority = SearcherPriority.NORMAL
        
        # Register in random order
        registry.register_searcher(low_searcher)
        registry.register_searcher(high_searcher)
        registry.register_searcher(normal_searcher)
        
        # Get sorted searchers
        sorted_searchers = registry.get_searchers_by_priority()
        
        # Should be sorted by priority (highest first)
        assert sorted_searchers[0] == high_searcher
        assert sorted_searchers[1] == normal_searcher
        assert sorted_searchers[2] == low_searcher

    def test_registry_configuration_enforcement(self) -> None:
        """Test registry configuration enforcement."""
        config = RegistryConfig(
            max_searchers=2,
            allow_duplicate_types=False
        )
        registry = SearcherRegistry(config=config)
        
        # Register up to limit
        searcher1 = Mock(spec=BaseSearcher)
        searcher1.name = "Searcher1"
        searcher2 = Mock(spec=BaseSearcher)
        searcher2.name = "Searcher2"
        searcher3 = Mock(spec=BaseSearcher)
        searcher3.name = "Searcher3"
        
        assert registry.register_searcher(searcher1) is True
        assert registry.register_searcher(searcher2) is True
        assert registry.register_searcher(searcher3) is False  # Should exceed limit
        
        assert len(registry.list_searchers()) == 2
