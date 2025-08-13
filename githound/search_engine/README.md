# GitHound Search Engine

This directory contains the enhanced search engine architecture for GitHound, providing multi-modal search capabilities with performance optimizations and fuzzy matching.

## Architecture

The search engine follows a modular, extensible architecture with the following components:

### Base Classes (`base.py`)
- **BaseSearcher**: Abstract base class for all searchers
- **CacheableSearcher**: Base class for searchers that support caching
- **ParallelSearcher**: Base class for searchers that can run operations in parallel
- **SearchContext**: Context information passed to searchers

### Search Orchestrator (`orchestrator.py`)
- **SearchOrchestrator**: Coordinates multiple searchers to handle complex queries
- Manages parallel execution of searchers
- Combines and ranks results from multiple sources
- Provides progress reporting and metrics collection

### Commit-based Searchers (`commit_searcher.py`)
- **CommitHashSearcher**: Exact commit hash matching
- **AuthorSearcher**: Author name/email search with fuzzy matching
- **MessageSearcher**: Commit message search with regex and fuzzy support
- **DateRangeSearcher**: Time-based commit filtering

### File-based Searchers (`file_searcher.py`)
- **FilePathSearcher**: File path pattern matching with glob/regex support
- **FileTypeSearcher**: File extension filtering
- **ContentSearcher**: Enhanced content search with ripgrep integration and ranking

### Fuzzy Search (`fuzzy_searcher.py`)
- **FuzzySearcher**: Advanced fuzzy matching across multiple dimensions
- Uses rapidfuzz for high-performance fuzzy string matching
- Configurable similarity thresholds
- Cross-dimensional search combining authors, messages, and content

## Key Features

### Multi-Modal Search
- Search by commit hash, author, message, date range, file path, file type, and content
- Combine multiple search criteria in a single query
- Intelligent result ranking and relevance scoring

### Performance Optimizations
- Parallel search execution with configurable worker pools
- Caching layer for frequently accessed data
- Progress reporting for long-running operations
- Memory-efficient processing for large repositories

### Fuzzy Matching
- Configurable similarity thresholds (0.0-1.0)
- Support for typos and partial matches
- Cross-dimensional fuzzy search capabilities

### Extensibility
- Plugin-like architecture for adding new searchers
- Dependency injection for testability
- Abstract base classes for consistent interfaces

## Usage Example

```python
from githound.search_engine import SearchOrchestrator
from githound.search_engine import (
    CommitHashSearcher, AuthorSearcher, ContentSearcher, FuzzySearcher
)
from githound.models import SearchQuery
from git import Repo

# Create orchestrator and register searchers
orchestrator = SearchOrchestrator()
orchestrator.register_searcher(CommitHashSearcher())
orchestrator.register_searcher(AuthorSearcher())
orchestrator.register_searcher(ContentSearcher())
orchestrator.register_searcher(FuzzySearcher())

# Create search query
query = SearchQuery(
    author_pattern="john",
    content_pattern="bug fix",
    fuzzy_search=True,
    fuzzy_threshold=0.8
)

# Perform search
repo = Repo("/path/to/repo")
async for result in orchestrator.search(repo, query):
    print(f"Found match in {result.file_path} at commit {result.commit_hash[:8]}")
    print(f"Relevance: {result.relevance_score:.2f}")
```

## Performance Considerations

- The search engine is optimized for repositories with up to 10,000 commits
- Caching is enabled by default with 1-hour TTL
- Parallel execution uses 4 workers by default (configurable)
- Memory usage is monitored and reported in metrics
- Large files (>10MB) are skipped by default to prevent memory issues

## Future Enhancements

- Elasticsearch integration for very large repositories
- Machine learning-based relevance scoring
- Incremental indexing for faster subsequent searches
- Distributed search across multiple repositories
