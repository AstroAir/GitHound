"""Search engine package for GitHound."""

from .base import BaseSearcher, CacheableSearcher, ParallelSearcher, SearchContext
from .commit_searcher import AuthorSearcher, CommitHashSearcher, DateRangeSearcher, MessageSearcher
from .file_searcher import ContentSearcher, FilePathSearcher, FileTypeSearcher
from .fuzzy_searcher import FuzzySearcher
from .orchestrator import SearchOrchestrator

# Advanced search components
from .searcher import AdvancedSearcher
from .branch_searcher import BranchSearcher
from .diff_searcher import DiffSearcher
from .history_searcher import HistorySearcher
from .pattern_searcher import CodePatternSearcher
from .statistical_searcher import StatisticalSearcher
from .tag_searcher import TagSearcher

# Search utilities
from .ranking_engine import RankingEngine
from .result_processor import ResultProcessor
from .cache import SearchCache, MemoryCache, RedisCache, CacheBackend

# Factory and configuration
from .factory import SearchEngineFactory, get_default_factory, create_search_orchestrator, initialize_default_registry
from .registry import SearcherRegistry, SearcherMetadata, get_global_registry
from .analytics import SearchAnalytics, SearchEvent, PerformanceMetrics, get_global_analytics

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
    "StatisticalSearcher",
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

    # Analytics
    "SearchAnalytics",
    "SearchEvent",
    "PerformanceMetrics",
    "get_global_analytics",
]
