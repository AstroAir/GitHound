"""
Unified search orchestrator for GitHound.

Provides a single, consistent interface for creating and configuring
search orchestrators across the application.
"""

from ...search_engine import (
    AuthorSearcher,
    CommitHashSearcher,
    ContentSearcher,
    DateRangeSearcher,
    FilePathSearcher,
    FileTypeSearcher,
    FuzzySearcher,
    MessageSearcher,
    SearchOrchestrator,
)


def create_search_orchestrator() -> SearchOrchestrator:
    """
    Create and configure a search orchestrator with all available searchers.
    
    This is the single source of truth for search orchestrator configuration
    across the entire application.
    
    Returns:
        SearchOrchestrator: Fully configured orchestrator with all searchers registered
    """
    orchestrator = SearchOrchestrator()

    # Register all available searchers in order of priority
    orchestrator.register_searcher(CommitHashSearcher())
    orchestrator.register_searcher(AuthorSearcher())
    orchestrator.register_searcher(MessageSearcher())
    orchestrator.register_searcher(DateRangeSearcher())
    orchestrator.register_searcher(FilePathSearcher())
    orchestrator.register_searcher(FileTypeSearcher())
    orchestrator.register_searcher(ContentSearcher())
    orchestrator.register_searcher(FuzzySearcher())

    return orchestrator


def create_enhanced_search_orchestrator() -> SearchOrchestrator:
    """
    Create an enhanced search orchestrator with optimized configuration.
    
    This is an alias for create_search_orchestrator() to maintain
    backward compatibility with existing code.
    
    Returns:
        SearchOrchestrator: Fully configured orchestrator
    """
    return create_search_orchestrator()
