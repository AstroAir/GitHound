"""Comprehensive tests for GitHound search engine functionality.

This module imports and runs all search engine tests from the search_engine subdirectory.
The tests have been organized into separate modules for better maintainability:

- test_base.py: Tests for base classes (BaseSearcher, CacheableSearcher, SearchContext)
- test_orchestrator.py: Tests for SearchOrchestrator
- test_commit_searcher.py: Tests for commit-based searchers
- test_file_searcher.py: Tests for file-based searchers
- test_fuzzy_searcher.py: Tests for fuzzy search functionality

All tests can still be run by executing this module, or individual test modules
can be run separately for focused testing.
"""

# Import all test modules to ensure they are discovered by pytest
# Note: These imports are for pytest discovery. Individual test modules
# can be run separately for focused testing.

# The following imports ensure all search engine tests are discovered
# when running pytest on this file or the tests directory
try:
    from tests.search_engine.test_base import *
    from tests.search_engine.test_orchestrator import *
    from tests.search_engine.test_commit_searcher import *
    from tests.search_engine.test_file_searcher import *
    from tests.search_engine.test_fuzzy_searcher import *
except ImportError:
    # Fallback for when running from different contexts
    pass













