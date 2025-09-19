"""Dynamic searcher registry for GitHound search engine."""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type, Union
from dataclasses import field

from ..models import SearchQuery, SearchType
from .base import BaseSearcher

logger = logging.getLogger(__name__)


@dataclass
class SearcherMetadata:
    """Metadata about a searcher."""
    
    name: str
    description: str
    search_types: List[SearchType]
    capabilities: List[str]
    priority: int = 100  # Lower numbers = higher priority
    enabled: bool = True
    requires_advanced: bool = False
    performance_cost: int = 1  # 1=low, 5=high
    memory_usage: int = 1  # 1=low, 5=high
    dependencies: List[str] = field(default_factory=list)  # External dependencies


class SearcherRegistry:
    """Registry for managing searchers dynamically."""
    
    def __init__(self) -> None:
        self._searchers: Dict[str, Type[BaseSearcher]] = {}
        self._metadata: Dict[str, SearcherMetadata] = {}
        self._instances: Dict[str, BaseSearcher] = {}
        self._initialized = False
    
    def register_searcher(
        self,
        searcher_class: Type[BaseSearcher],
        metadata: SearcherMetadata,
        replace_existing: bool = False
    ) -> None:
        """Register a searcher class with metadata."""
        name = metadata.name
        
        if name in self._searchers and not replace_existing:
            logger.warning(f"Searcher '{name}' already registered, skipping")
            return
        
        # Validate searcher class
        if not issubclass(searcher_class, BaseSearcher):
            raise ValueError(f"Searcher class must inherit from BaseSearcher")
        
        self._searchers[name] = searcher_class
        self._metadata[name] = metadata
        
        logger.info(f"Registered searcher: {name}")
    
    def unregister_searcher(self, name: str) -> None:
        """Unregister a searcher."""
        if name in self._searchers:
            del self._searchers[name]
            del self._metadata[name]
            if name in self._instances:
                del self._instances[name]
            logger.info(f"Unregistered searcher: {name}")
        else:
            logger.warning(f"Searcher '{name}' not found for unregistration")
    
    def get_searcher_class(self, name: str) -> Optional[Type[BaseSearcher]]:
        """Get a searcher class by name."""
        return self._searchers.get(name)
    
    def get_searcher_instance(self, name: str, **kwargs: Any) -> Optional[BaseSearcher]:
        """Get or create a searcher instance."""
        if name not in self._searchers:
            logger.error(f"Searcher '{name}' not found")
            return None
        
        # Check if we have a cached instance
        if name in self._instances and not kwargs:
            return self._instances[name]
        
        # Create new instance
        try:
            searcher_class = self._searchers[name]
            instance = searcher_class(**kwargs)
            
            # Cache instance if no custom kwargs
            if not kwargs:
                self._instances[name] = instance
            
            return instance
        except Exception as e:
            logger.error(f"Failed to create searcher instance '{name}': {e}")
            return None
    
    def get_metadata(self, name: str) -> Optional[SearcherMetadata]:
        """Get metadata for a searcher."""
        return self._metadata.get(name)
    
    def list_searchers(
        self,
        enabled_only: bool = True,
        search_type: Optional[SearchType] = None,
        capability: Optional[str] = None
    ) -> List[str]:
        """List available searchers with optional filtering."""
        searchers = []
        
        for name, metadata in self._metadata.items():
            # Filter by enabled status
            if enabled_only and not metadata.enabled:
                continue
            
            # Filter by search type
            if search_type and search_type not in metadata.search_types:
                continue
            
            # Filter by capability
            if capability and capability not in metadata.capabilities:
                continue
            
            searchers.append(name)
        
        # Sort by priority (lower number = higher priority)
        searchers.sort(key=lambda name: self._metadata[name].priority)
        return searchers
    
    def get_searchers_for_query(self, query: SearchQuery) -> List[str]:
        """Get appropriate searchers for a given query."""
        applicable_searchers = []
        
        for name, metadata in self._metadata.items():
            if not metadata.enabled:
                continue
            
            # Check if searcher can handle the query
            if self._can_handle_query(metadata, query):
                applicable_searchers.append(name)
        
        # Sort by priority
        applicable_searchers.sort(key=lambda name: self._metadata[name].priority)
        return applicable_searchers
    
    def _can_handle_query(self, metadata: SearcherMetadata, query: SearchQuery) -> bool:
        """Check if a searcher can handle a specific query."""
        # Check if advanced searcher is needed
        if metadata.requires_advanced and not query.has_advanced_analysis():
            return False
        
        # Check specific capabilities
        if query.content_pattern and "content_search" not in metadata.capabilities:
            return False
        
        if query.author_pattern and "author_search" not in metadata.capabilities:
            return False
        
        if query.message_pattern and "message_search" not in metadata.capabilities:
            return False
        
        if query.file_path_pattern and "file_search" not in metadata.capabilities:
            return False
        
        if query.commit_hash and "commit_search" not in metadata.capabilities:
            return False
        
        if (query.date_from or query.date_to) and "date_search" not in metadata.capabilities:
            return False
        
        if query.fuzzy_search and "fuzzy_search" not in metadata.capabilities:
            return False
        
        # Check advanced analysis capabilities
        if query.branch_analysis and "branch_analysis" not in metadata.capabilities:
            return False
        
        if query.diff_analysis and "diff_analysis" not in metadata.capabilities:
            return False
        
        if query.pattern_analysis and "pattern_analysis" not in metadata.capabilities:
            return False
        
        if query.statistical_analysis and "statistical_analysis" not in metadata.capabilities:
            return False
        
        if query.temporal_analysis and "temporal_analysis" not in metadata.capabilities:
            return False
        
        if query.version_analysis and "version_analysis" not in metadata.capabilities:
            return False
        
        return True
    
    def get_performance_estimate(self, searcher_names: List[str]) -> Dict[str, Any]:
        """Get performance estimate for a set of searchers."""
        total_cost = 0
        total_memory = 0
        max_cost = 0
        max_memory = 0
        
        for name in searcher_names:
            metadata = self._metadata.get(name)
            if metadata:
                total_cost += metadata.performance_cost
                total_memory += metadata.memory_usage
                max_cost = max(max_cost, metadata.performance_cost)
                max_memory = max(max_memory, metadata.memory_usage)
        
        return {
            "total_performance_cost": total_cost,
            "total_memory_usage": total_memory,
            "max_performance_cost": max_cost,
            "max_memory_usage": max_memory,
            "searcher_count": len(searcher_names),
            "estimated_complexity": "low" if total_cost <= 5 else "medium" if total_cost <= 15 else "high"
        }
    
    def enable_searcher(self, name: str) -> bool:
        """Enable a searcher."""
        if name in self._metadata:
            self._metadata[name].enabled = True
            logger.info(f"Enabled searcher: {name}")
            return True
        return False
    
    def disable_searcher(self, name: str) -> bool:
        """Disable a searcher."""
        if name in self._metadata:
            self._metadata[name].enabled = False
            logger.info(f"Disabled searcher: {name}")
            return True
        return False
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        enabled_count = sum(1 for m in self._metadata.values() if m.enabled)
        advanced_count = sum(1 for m in self._metadata.values() if m.requires_advanced)
        
        capabilities = set()
        for metadata in self._metadata.values():
            capabilities.update(metadata.capabilities)
        
        return {
            "total_searchers": len(self._searchers),
            "enabled_searchers": enabled_count,
            "disabled_searchers": len(self._searchers) - enabled_count,
            "advanced_searchers": advanced_count,
            "basic_searchers": len(self._searchers) - advanced_count,
            "unique_capabilities": len(capabilities),
            "all_capabilities": sorted(list(capabilities)),
            "cached_instances": len(self._instances)
        }
    
    def validate_dependencies(self) -> Dict[str, List[str]]:
        """Validate that all searcher dependencies are available."""
        issues = {}
        
        for name, metadata in self._metadata.items():
            searcher_issues = []
            
            for dependency in metadata.dependencies:
                try:
                    __import__(dependency)
                except ImportError:
                    searcher_issues.append(f"Missing dependency: {dependency}")
            
            if searcher_issues:
                issues[name] = searcher_issues
        
        return issues


# Global registry instance
_global_registry: Optional[SearcherRegistry] = None


def get_global_registry() -> SearcherRegistry:
    """Get the global searcher registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = SearcherRegistry()
        _initialize_default_searchers(_global_registry)
    return _global_registry


def _initialize_default_searchers(registry: SearcherRegistry) -> None:
    """Initialize the registry with default searchers."""
    # This will be called by the factory to register all available searchers
    pass
