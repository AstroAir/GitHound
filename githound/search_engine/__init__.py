"""Search engine package for GitHound."""

from .base import BaseSearcher, CacheableSearcher, ParallelSearcher, SearchContext
from .branch_searcher import BranchSearcher
from .cache import CacheBackend, MemoryCache, RedisCache, SearchCache
from .commit_searcher import AuthorSearcher, CommitHashSearcher, DateRangeSearcher, MessageSearcher
from .diff_searcher import DiffSearcher

# Enhanced components (optional imports for backward compatibility)
try:
    from .bm25_ranker import BM25Ranker  # noqa: F401
    from .enhanced_orchestrator import EnhancedSearchOrchestrator  # noqa: F401
    from .indexer import IncrementalIndexer, InvertedIndex  # noqa: F401
    from .performance_monitor import (  # noqa: F401
        BottleneckDetector,
        PerformanceMonitor,
        SearchProfiler,
    )
    from .query_optimizer import QueryOptimizer, QueryPlanner  # noqa: F401

    _HAS_ENHANCED_FEATURES = True
except ImportError:
    _HAS_ENHANCED_FEATURES = False

# Factory and configuration
from .factory import (
    SearchEngineFactory,
    create_search_orchestrator,
    get_default_factory,
    initialize_default_registry,
)
from .file_searcher import ContentSearcher, FilePathSearcher, FileTypeSearcher
from .fuzzy_searcher import FuzzySearcher
from .history_searcher import HistorySearcher
from .orchestrator import SearchOrchestrator
from .pattern_searcher import CodePatternSearcher

# Search utilities
from .ranking_engine import RankingEngine
from .registry import SearcherMetadata, SearcherRegistry, get_global_registry
from .result_processor import ResultProcessor

# Advanced search components
from .searcher import AdvancedSearcher
from .tag_searcher import TagSearcher

__all__ = [
    # Base classes
    "BaseSearcher",
    "SearchContext",
    "CacheableSearcher",
    "ParallelSearcher",
    # Core orchestration
    "SearchOrchestrator",
    # Basic searchers
    "CommitHashSearcher",
    "AuthorSearcher",
    "MessageSearcher",
    "DateRangeSearcher",
    "FilePathSearcher",
    "FileTypeSearcher",
    "ContentSearcher",
    "FuzzySearcher",
    # Advanced searchers
    "AdvancedSearcher",
    "BranchSearcher",
    "DiffSearcher",
    "HistorySearcher",
    "CodePatternSearcher",
    "TagSearcher",
    # Search utilities
    "RankingEngine",
    "ResultProcessor",
    # Caching
    "SearchCache",
    "MemoryCache",
    "RedisCache",
    "CacheBackend",
    # Factory and configuration
    "SearchEngineFactory",
    "get_default_factory",
    "create_search_orchestrator",
    "initialize_default_registry",
    # Registry
    "SearcherRegistry",
    "SearcherMetadata",
    "get_global_registry",
]

# Conditionally add enhanced features to __all__
if _HAS_ENHANCED_FEATURES:
    __all__.extend(
        [
            "EnhancedSearchOrchestrator",
            "IncrementalIndexer",
            "InvertedIndex",
            "BM25Ranker",
            "QueryOptimizer",
            "QueryPlanner",
            "PerformanceMonitor",
            "SearchProfiler",
            "BottleneckDetector",
        ]
    )
