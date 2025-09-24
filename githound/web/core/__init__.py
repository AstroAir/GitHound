"""Core business logic for GitHound web interface.

This module contains the core business logic components that power the GitHound web interface,
including search orchestration, Git operations management, and data processing pipelines.

Key Components:
    - SearchOrchestrator: Unified search coordination across multiple search engines
    - GitOperationsManager: Git repository operations and metadata extraction
    - DataProcessor: Result processing and transformation for web consumption
    - CacheManager: Intelligent caching for improved performance

The core module abstracts complex Git operations and search functionality into
clean, testable components that can be easily consumed by the web API layer.
"""
