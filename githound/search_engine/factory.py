"""Search engine factory for consistent orchestrator creation and configuration."""

import logging
from typing import Any

from ..models import SearchEngineConfig, SearchQuery, SearchType
from .base import BaseSearcher
from .branch_searcher import BranchSearcher
from .cache import CacheBackend, MemoryCache, RedisCache, SearchCache

# Import all searchers
from .commit_searcher import AuthorSearcher, CommitHashSearcher, DateRangeSearcher, MessageSearcher
from .diff_searcher import DiffSearcher

# Import enhanced components
from .enhanced_orchestrator import EnhancedSearchOrchestrator
from .file_searcher import ContentSearcher, FilePathSearcher, FileTypeSearcher
from .fuzzy_searcher import FuzzySearcher
from .history_searcher import HistorySearcher
from .orchestrator import SearchOrchestrator
from .pattern_searcher import CodePatternSearcher

# Import utilities
from .ranking_engine import RankingEngine
from .registry import SearcherMetadata, SearcherRegistry, get_global_registry
from .result_processor import ResultProcessor
from .searcher import AdvancedSearcher
from .tag_searcher import TagSearcher

logger = logging.getLogger(__name__)


class SearchEngineFactory:
    """Factory for creating and configuring search orchestrators."""

    def __init__(self, config: SearchEngineConfig | None = None) -> None:
        """Initialize the factory with configuration."""
        self.config = config or SearchEngineConfig()
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate the configuration."""
        issues = self.config.validate_config()
        if issues:
            logger.warning(f"Configuration issues found: {issues}")
            for issue in issues:
                logger.warning(f"  - {issue}")

    def create_orchestrator(
        self,
        enable_advanced: bool | None = None,
        enable_caching: bool | None = None,
        enable_ranking: bool | None = None,
        enhanced: bool = False,
    ) -> SearchOrchestrator:
        """Create a fully configured search orchestrator.

        Args:
            enable_advanced: Enable advanced searchers
            enable_caching: Enable result caching
            enable_ranking: Enable result ranking
            enhanced: Use enhanced orchestrator with monitoring and optimization

        Returns:
            Configured SearchOrchestrator instance
        """
        # Override config with parameters if provided
        use_advanced = (
            enable_advanced
            if enable_advanced is not None
            else self.config.enable_advanced_searchers
        )
        use_caching = enable_caching if enable_caching is not None else self.config.enable_caching
        use_ranking = enable_ranking if enable_ranking is not None else self.config.enable_ranking

        # Create orchestrator (enhanced or regular)
        if enhanced:
            orchestrator = EnhancedSearchOrchestrator(
                enable_monitoring=True, enable_optimization=True
            )
        else:
            orchestrator = SearchOrchestrator()

        # Register searchers based on configuration
        self._register_searchers(orchestrator, use_advanced)

        # Configure caching if enabled
        if use_caching:
            cache = self._create_cache()
            orchestrator.set_cache(cache)

        # Configure ranking if enabled
        if use_ranking:
            ranking_engine = self._create_ranking_engine()
            orchestrator.set_ranking_engine(ranking_engine)

        # Configure result processor
        result_processor = self._create_result_processor()
        orchestrator.set_result_processor(result_processor)

        logger.info(f"Created orchestrator with {len(orchestrator._searchers)} searchers")
        return orchestrator

    def _register_searchers(self, orchestrator: SearchOrchestrator, enable_advanced: bool) -> None:
        """Register searchers with the orchestrator."""
        # Always register basic searchers if enabled
        if self.config.enable_basic_searchers:
            basic_searchers = self._create_basic_searchers()
            for searcher in basic_searchers:
                orchestrator.register_searcher(searcher)
                logger.debug(f"Registered basic searcher: {searcher.name}")

        # Register advanced searchers if enabled
        if enable_advanced and self.config.enable_advanced_searchers:
            advanced_searchers = self._create_advanced_searchers()
            for searcher in advanced_searchers:
                orchestrator.register_searcher(searcher)
                logger.debug(f"Registered advanced searcher: {searcher.name}")

    def _create_basic_searchers(self) -> list[BaseSearcher]:
        """Create basic searchers."""
        searchers: list[BaseSearcher] = [
            CommitHashSearcher(),
            AuthorSearcher(),
            MessageSearcher(),
            DateRangeSearcher(),
            FilePathSearcher(),
            FileTypeSearcher(),
            ContentSearcher(),
        ]

        # Add fuzzy searcher if enabled
        if self.config.enable_fuzzy_search:
            searchers.append(FuzzySearcher())

        return searchers

    def _create_advanced_searchers(self) -> list[BaseSearcher]:
        """Create advanced searchers."""
        searchers: list[BaseSearcher] = []

        # Add advanced multi-criteria searcher
        searchers.append(AdvancedSearcher(max_workers=self.config.max_workers))

        # Add analysis searchers
        searchers.append(BranchSearcher())
        searchers.append(DiffSearcher())
        searchers.append(HistorySearcher())
        searchers.append(TagSearcher())

        # Add pattern searcher if enabled
        if self.config.enable_pattern_detection:
            searchers.append(CodePatternSearcher())

        return searchers

    def _create_cache(self) -> SearchCache:
        """Create cache backend based on configuration."""
        cache_config = self.config.get_cache_config()

        backend: CacheBackend
        if cache_config["backend"] == "redis":
            try:
                backend = RedisCache(
                    url=cache_config["redis_url"], default_ttl=cache_config["ttl_seconds"]
                )
                logger.info("Using Redis cache backend")
            except Exception as e:
                logger.warning(f"Failed to create Redis cache, falling back to memory: {e}")
                backend = MemoryCache(
                    max_size=cache_config["max_size"], default_ttl=cache_config["ttl_seconds"]
                )
        else:
            backend = MemoryCache(
                max_size=cache_config["max_size"], default_ttl=cache_config["ttl_seconds"]
            )
            logger.info("Using memory cache backend")

        return SearchCache(backend=backend, default_ttl=cache_config["ttl_seconds"])

    def _create_ranking_engine(self) -> RankingEngine:
        """Create ranking engine with configured weights."""
        ranking_engine = RankingEngine()
        ranking_engine.set_ranking_weights(self.config.ranking_weights)
        logger.debug(f"Created ranking engine with weights: {self.config.ranking_weights}")
        return ranking_engine

    def _create_result_processor(self) -> ResultProcessor:
        """Create result processor with default filters and enrichers."""
        processor = ResultProcessor()

        # Add default filters based on configuration
        if self.config.default_max_results:
            processor.add_filter(
                lambda result: True  # Placeholder - actual filtering done in orchestrator
            )

        # Add default enrichers
        processor.add_enricher(ResultProcessor.create_file_info_enricher())

        # Add default groupers
        processor.add_grouper("file_type", ResultProcessor.create_file_type_grouper())
        processor.add_grouper("search_type", ResultProcessor.create_search_type_grouper())
        processor.add_grouper("author", ResultProcessor.create_author_grouper())
        processor.add_grouper("directory", ResultProcessor.create_directory_grouper())

        logger.debug("Created result processor with default configuration")
        return processor

    def create_for_query(self, query: SearchQuery) -> SearchOrchestrator:
        """Create an orchestrator optimized for a specific query."""
        # Determine if advanced searchers are needed
        needs_advanced = query.has_advanced_analysis() or query.is_complex_query()

        # Create orchestrator with appropriate configuration
        orchestrator = self.create_orchestrator(enable_advanced=needs_advanced)

        logger.info(f"Created query-optimized orchestrator (advanced: {needs_advanced})")
        return orchestrator

    def get_available_searchers(self) -> dict[str, Any]:
        """Get all available searcher types."""
        searchers = {
            # Basic searchers
            "commit_hash": CommitHashSearcher,
            "author": AuthorSearcher,
            "message": MessageSearcher,
            "date_range": DateRangeSearcher,
            "file_path": FilePathSearcher,
            "file_type": FileTypeSearcher,
            "content": ContentSearcher,
            "fuzzy": FuzzySearcher,
            # Advanced searchers
            "advanced": AdvancedSearcher,
            "branch": BranchSearcher,
            "diff": DiffSearcher,
            "history": HistorySearcher,
            "pattern": CodePatternSearcher,
            "tag": TagSearcher,
        }
        return searchers

    def create_custom_orchestrator(self, searcher_names: list[str]) -> SearchOrchestrator:
        """Create orchestrator with specific searchers."""
        available_searchers = self.get_available_searchers()
        orchestrator = SearchOrchestrator()

        for name in searcher_names:
            if name in available_searchers:
                searcher_class = available_searchers[name]
                if name == "advanced":
                    searcher = searcher_class(max_workers=self.config.max_workers)
                else:
                    searcher = searcher_class()
                orchestrator.register_searcher(searcher)
                logger.debug(f"Registered custom searcher: {name}")
            else:
                logger.warning(f"Unknown searcher: {name}")

        # Always add caching and ranking if enabled
        if self.config.enable_caching:
            cache = self._create_cache()
            orchestrator.set_cache(cache)

        if self.config.enable_ranking:
            ranking_engine = self._create_ranking_engine()
            orchestrator.set_ranking_engine(ranking_engine)

        result_processor = self._create_result_processor()
        orchestrator.set_result_processor(result_processor)

        logger.info(f"Created custom orchestrator with {len(orchestrator._searchers)} searchers")
        return orchestrator


# Global factory instance for convenience
_default_factory: SearchEngineFactory | None = None


def get_default_factory() -> SearchEngineFactory:
    """Get the default factory instance."""
    global _default_factory
    if _default_factory is None:
        _default_factory = SearchEngineFactory()
    return _default_factory


def create_search_orchestrator(
    config: SearchEngineConfig | None = None, enable_advanced: bool | None = None
) -> SearchOrchestrator:
    """Convenience function to create a search orchestrator."""
    if config:
        factory = SearchEngineFactory(config)
    else:
        factory = get_default_factory()

    return factory.create_orchestrator(enable_advanced=enable_advanced)


def initialize_default_registry() -> SearcherRegistry:
    """Initialize the global registry with default searchers."""
    registry = get_global_registry()

    # Register basic searchers
    registry.register_searcher(
        CommitHashSearcher,
        SearcherMetadata(
            name="commit_hash",
            description="Search by specific commit hash",
            search_types=[SearchType.COMMIT_HASH],
            capabilities=["commit_search"],
            priority=10,
            performance_cost=1,
            memory_usage=1,
        ),
    )

    registry.register_searcher(
        AuthorSearcher,
        SearcherMetadata(
            name="author",
            description="Search by commit author",
            search_types=[SearchType.AUTHOR],
            capabilities=["author_search"],
            priority=20,
            performance_cost=2,
            memory_usage=1,
        ),
    )

    registry.register_searcher(
        MessageSearcher,
        SearcherMetadata(
            name="message",
            description="Search in commit messages",
            search_types=[SearchType.MESSAGE],
            capabilities=["message_search"],
            priority=30,
            performance_cost=2,
            memory_usage=1,
        ),
    )

    registry.register_searcher(
        DateRangeSearcher,
        SearcherMetadata(
            name="date_range",
            description="Search by date range",
            search_types=[SearchType.DATE_RANGE],
            capabilities=["date_search"],
            priority=40,
            performance_cost=2,
            memory_usage=1,
        ),
    )

    registry.register_searcher(
        FilePathSearcher,
        SearcherMetadata(
            name="file_path",
            description="Search by file path pattern",
            search_types=[SearchType.FILE_PATH],
            capabilities=["file_search"],
            priority=50,
            performance_cost=2,
            memory_usage=1,
        ),
    )

    registry.register_searcher(
        FileTypeSearcher,
        SearcherMetadata(
            name="file_type",
            description="Search by file type/extension",
            search_types=[SearchType.FILE_TYPE],
            capabilities=["file_search"],
            priority=60,
            performance_cost=1,
            memory_usage=1,
        ),
    )

    registry.register_searcher(
        ContentSearcher,
        SearcherMetadata(
            name="content",
            description="Search in file content",
            search_types=[SearchType.CONTENT],
            capabilities=["content_search"],
            priority=70,
            performance_cost=4,
            memory_usage=3,
        ),
    )

    registry.register_searcher(
        FuzzySearcher,
        SearcherMetadata(
            name="fuzzy",
            description="Fuzzy string matching",
            search_types=[SearchType.CONTENT, SearchType.AUTHOR, SearchType.MESSAGE],
            capabilities=["fuzzy_search", "content_search", "author_search", "message_search"],
            priority=80,
            performance_cost=3,
            memory_usage=2,
            dependencies=["rapidfuzz"],
        ),
    )

    # Register advanced searchers
    registry.register_searcher(
        AdvancedSearcher,
        SearcherMetadata(
            name="advanced",
            description="Multi-criteria advanced search",
            search_types=[SearchType.COMBINED],
            capabilities=[
                "content_search",
                "author_search",
                "message_search",
                "file_search",
                "date_search",
            ],
            priority=100,
            requires_advanced=True,
            performance_cost=4,
            memory_usage=3,
        ),
    )

    registry.register_searcher(
        BranchSearcher,
        SearcherMetadata(
            name="branch",
            description="Branch analysis and comparison",
            search_types=[SearchType.BRANCH_ANALYSIS],
            capabilities=["branch_analysis"],
            priority=110,
            requires_advanced=True,
            performance_cost=3,
            memory_usage=2,
        ),
    )

    registry.register_searcher(
        DiffSearcher,
        SearcherMetadata(
            name="diff",
            description="Diff and change analysis",
            search_types=[SearchType.DIFF_ANALYSIS],
            capabilities=["diff_analysis"],
            priority=120,
            requires_advanced=True,
            performance_cost=4,
            memory_usage=3,
        ),
    )

    registry.register_searcher(
        HistorySearcher,
        SearcherMetadata(
            name="history",
            description="Temporal and historical analysis",
            search_types=[SearchType.TEMPORAL_ANALYSIS],
            capabilities=["temporal_analysis"],
            priority=130,
            requires_advanced=True,
            performance_cost=4,
            memory_usage=3,
        ),
    )

    registry.register_searcher(
        CodePatternSearcher,
        SearcherMetadata(
            name="pattern",
            description="Code pattern and quality analysis",
            search_types=[
                SearchType.PATTERN_DETECTION,
                SearchType.CODE_QUALITY,
                SearchType.SECURITY_ANALYSIS,
            ],
            capabilities=["pattern_analysis", "code_quality", "security_analysis"],
            priority=140,
            requires_advanced=True,
            performance_cost=5,
            memory_usage=4,
        ),
    )

    registry.register_searcher(
        TagSearcher,
        SearcherMetadata(
            name="tag",
            description="Tag and version analysis",
            search_types=[SearchType.TAG_ANALYSIS],
            capabilities=["version_analysis"],
            priority=160,
            requires_advanced=True,
            performance_cost=2,
            memory_usage=2,
        ),
    )

    logger.info(f"Initialized registry with {len(registry._searchers)} searchers")
    return registry
