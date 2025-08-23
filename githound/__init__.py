"""GitHound: Advanced Git Repository Analysis Tool.

This module provides the main GitHound class for comprehensive Git repository analysis,
including search, blame, diff, and export functionality.
"""

import asyncio
import functools
import platform
import threading
import time
import warnings
from collections.abc import Callable
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, TypeVar, Union

# Suppress NumPy compatibility warnings for better user experience
warnings.filterwarnings("ignore", message=".*NumPy.*")
warnings.filterwarnings("ignore", message=".*_ARRAY_API.*")

from git import GitCommandError, Repo

T = TypeVar("T")


class TimeoutError(Exception):
    """Raised when an operation times out."""

    pass


@contextmanager
def timeout_context(seconds: int) -> Generator[None, None, None]:
    """Cross-platform context manager for timeout operations."""
    if seconds <= 0:
        yield
        return

    # For cross-platform compatibility, we'll implement a simple timeout
    # In a production environment, you might want to use more sophisticated
    # timeout mechanisms like concurrent.futures.ThreadPoolExecutor

    if platform.system() != "Windows":
        # Unix-like systems can use signal-based timeout
        try:
            import signal

            def timeout_handler(signum, frame):
                raise TimeoutError("Operation timed out")

            old_handler = signal.signal(signal.SIGALRM, timeout_handler)  # type: ignore
            signal.alarm(seconds)  # type: ignore

            try:
                yield
            finally:
                signal.alarm(0)  # type: ignore
                signal.signal(signal.SIGALRM, old_handler)  # type: ignore
        except (AttributeError, ImportError):
            # Fallback: no timeout
            yield
    else:
        # Windows: no timeout for now (could implement with threading.Timer)
        yield


def with_timeout(timeout_seconds: int) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to add timeout to functions."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                with timeout_context(timeout_seconds):
                    return func(*args, **kwargs)
            except TimeoutError:
                raise GitCommandError(f"Operation timed out after {timeout_seconds} seconds")

        return wrapper

    return decorator


def with_retry(
    max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to add retry logic to functions.

    Args:
        max_attempts: Maximum number of attempts.
        delay: Initial delay between attempts in seconds.
        backoff: Backoff multiplier for delay.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:

            last_exception = None
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except (OSError, GitCommandError) as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        raise GitCommandError(
                            f"Operation failed after {max_attempts} attempts: {str(e)}"
                        )
                except Exception as e:
                    # Don't retry for non-transient errors
                    raise e

            # This should never be reached, but just in case
            raise last_exception or GitCommandError("Unknown error in retry logic")

        return wrapper

    return decorator


from .git_blame import FileBlameResult, get_file_blame
from .git_diff import CommitDiffResult, compare_branches, compare_commits
from .git_handler import get_repository, get_repository_metadata
from .models import RepositoryInfo, SearchQuery, SearchResult
from .schemas import ExportOptions, OutputFormat
from .search_engine import (
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


class GitHound:
    """Main GitHound class providing comprehensive Git repository analysis capabilities.

    This class serves as the primary interface for GitHound functionality, providing
    methods for repository analysis, advanced search, blame analysis, diff comparison,
    and data export.

    Example:
        ```python
        from githound import GitHound
        from githound.models import SearchQuery
        from pathlib import Path

        # Initialize GitHound
        gh = GitHound(Path("/path/to/repo"))

        # Analyze repository
        repo_info = gh.analyze_repository()

        # Perform advanced search
        query = SearchQuery(content_pattern="function", author_pattern="john")
        results = gh.search_advanced(query)

        # Analyze file blame
        blame_info = gh.analyze_blame("src/main.py")

        # Compare commits
        diff_info = gh.compare_commits("commit1", "commit2")
        ```
    """

    def __init__(self, repo_path: Path, timeout: int = 300):
        """Initialize GitHound with a repository path.

        Args:
            repo_path: Path to the Git repository.
            timeout: Default timeout for Git operations in seconds (default: 300).

        Raises:
            GitCommandError: If the path is not a valid Git repository.
        """
        self.repo_path = repo_path
        self.timeout = timeout
        self.repo = get_repository(repo_path)
        self._search_orchestrator: SearchOrchestrator | None = None
        self._export_manager: Any | None = None
        self._cleanup_callbacks: list[Callable[[], None]] = []

    @property
    def search_orchestrator(self) -> SearchOrchestrator:
        """Get or create the search orchestrator with all searchers registered."""
        if self._search_orchestrator is None:
            self._search_orchestrator = SearchOrchestrator()

            # Register all available searchers
            self._search_orchestrator.register_searcher(CommitHashSearcher())
            self._search_orchestrator.register_searcher(AuthorSearcher())
            self._search_orchestrator.register_searcher(MessageSearcher())
            self._search_orchestrator.register_searcher(DateRangeSearcher())
            self._search_orchestrator.register_searcher(FilePathSearcher())
            self._search_orchestrator.register_searcher(FileTypeSearcher())
            self._search_orchestrator.register_searcher(ContentSearcher())
            self._search_orchestrator.register_searcher(FuzzySearcher())

        return self._search_orchestrator

    @property
    def export_manager(self) -> Any:
        """Get or create the export manager."""
        if self._export_manager is None:
            try:
                from rich.console import Console

                from .utils.export import ExportManager

                self._export_manager = ExportManager(Console())
            except ImportError as e:
                raise GitCommandError(f"Export functionality requires additional dependencies: {e}")
        return self._export_manager

    def analyze_repository(
        self, include_detailed_stats: bool = True, timeout: int | None = None
    ) -> dict[str, Any]:
        """Analyze repository and return comprehensive metadata.

        Args:
            include_detailed_stats: Whether to include detailed statistics.
            timeout: Timeout in seconds (uses instance default if None).

        Returns:
            Dictionary containing repository metadata including:
            - Basic repository information (path, branches, tags, remotes)
            - Commit statistics (total commits, contributors, date range)
            - Repository health metrics

        Raises:
            GitCommandError: If repository analysis fails or times out.
        """
        timeout_seconds = timeout or self.timeout

        @with_timeout(timeout_seconds)
        @with_retry(max_attempts=3, delay=0.5)
        def _analyze() -> dict[str, Any]:
            metadata = get_repository_metadata(self.repo)

            if include_detailed_stats:
                # Add additional detailed statistics
                from .git_blame import get_author_statistics

                try:
                    author_stats = get_author_statistics(self.repo)
                    metadata["author_statistics"] = author_stats
                except Exception as e:
                    metadata["author_statistics_error"] = str(e)

            return metadata

        try:
            return _analyze()
        except Exception as e:
            raise GitCommandError(f"Failed to analyze repository: {str(e)}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()

    def cleanup(self):
        """Clean up resources and caches."""
        # Run cleanup callbacks
        for callback in self._cleanup_callbacks:
            try:
                callback()
            except Exception:
                pass  # Ignore cleanup errors

        # Clear caches
        self._search_orchestrator = None
        self._export_manager = None
        self._cleanup_callbacks.clear()

        # Force garbage collection for large repositories
        import gc

        gc.collect()

    def add_cleanup_callback(self, callback: Callable[[], None]) -> None:
        """Add a cleanup callback to be called when GitHound is cleaned up."""
        self._cleanup_callbacks.append(callback)

    async def search_advanced(
        self,
        query: SearchQuery,
        branch: str | None = None,
        max_results: int | None = None,
        enable_progress: bool = False,
    ) -> list[SearchResult]:
        """Perform advanced multi-modal search.

        Args:
            query: SearchQuery object with search criteria.
            branch: Branch to search (defaults to current branch).
            max_results: Maximum number of results to return.
            enable_progress: Whether to enable progress reporting.

        Returns:
            List of SearchResult objects.

        Raises:
            GitCommandError: If search operation fails.
        """
        try:
            results = []

            # Perform search using orchestrator
            async for result in self.search_orchestrator.search(
                repo=self.repo, query=query, branch=branch, max_results=max_results
            ):
                results.append(result)

            return results

        except Exception as e:
            raise GitCommandError(f"Search operation failed: {str(e)}")

    def search_advanced_sync(
        self,
        query: SearchQuery,
        branch: str | None = None,
        max_results: int | None = None,
        enable_progress: bool = False,
    ) -> list[SearchResult]:
        """Synchronous version of search_advanced for convenience.

        Args:
            query: SearchQuery object with search criteria.
            branch: Branch to search (defaults to current branch).
            max_results: Maximum number of results to return.
            enable_progress: Whether to enable progress reporting.

        Returns:
            List of SearchResult objects.
        """
        return asyncio.run(self.search_advanced(query, branch, max_results, enable_progress))

    def analyze_blame(self, file_path: str, commit: str | None = None) -> FileBlameResult:
        """Analyze file blame information.

        Args:
            file_path: Path to the file relative to repository root.
            commit: Specific commit to blame (defaults to HEAD).

        Returns:
            FileBlameResult with line-by-line authorship information.

        Raises:
            GitCommandError: If blame analysis fails.
        """
        try:
            return get_file_blame(self.repo, file_path, commit)
        except Exception as e:
            raise GitCommandError(f"Blame analysis failed: {str(e)}")

    def compare_commits(
        self, from_commit: str, to_commit: str, file_patterns: list[str] | None = None
    ) -> CommitDiffResult:
        """Compare two commits and return detailed diff information.

        Args:
            from_commit: Source commit hash or reference.
            to_commit: Target commit hash or reference.
            file_patterns: Optional file patterns to filter the diff.

        Returns:
            CommitDiffResult with detailed comparison information.

        Raises:
            GitCommandError: If commit comparison fails.
        """
        try:
            return compare_commits(self.repo, from_commit, to_commit, file_patterns)
        except Exception as e:
            raise GitCommandError(f"Commit comparison failed: {str(e)}")

    def compare_branches(
        self, from_branch: str, to_branch: str, file_patterns: list[str] | None = None
    ) -> CommitDiffResult:
        """Compare two branches and return detailed diff information.

        Args:
            from_branch: Source branch name.
            to_branch: Target branch name.
            file_patterns: Optional file patterns to filter the diff.

        Returns:
            CommitDiffResult with detailed comparison information.

        Raises:
            GitCommandError: If branch comparison fails.
        """
        try:
            return compare_branches(self.repo, from_branch, to_branch, file_patterns)
        except Exception as e:
            raise GitCommandError(f"Branch comparison failed: {str(e)}")

    def export_with_options(
        self, data: Any, output_path: str | Path, options: ExportOptions
    ) -> None:
        """Export data with specified options.

        Args:
            data: Data to export (SearchResult list, repository metadata, etc.).
            output_path: Path to the output file.
            options: Export options specifying format and other settings.

        Raises:
            GitCommandError: If export operation fails.
        """
        try:
            output_path = Path(output_path)

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            if options.format == OutputFormat.JSON:
                self.export_manager.export_to_json(data, output_path, options.include_metadata)
            elif options.format == OutputFormat.YAML:
                self.export_manager.export_to_yaml(data, output_path, options.include_metadata)
            elif options.format == OutputFormat.CSV:
                self.export_manager.export_to_csv(data, output_path, options.include_metadata)
            elif options.format == OutputFormat.XML:
                # XML export not yet implemented in ExportManager, use JSON as fallback
                from rich.console import Console

                Console().print(
                    "[yellow]⚠ XML export not yet implemented. Using JSON format.[/yellow]"
                )
                self.export_manager.export_to_json(
                    data, output_path.with_suffix(".json"), options.include_metadata
                )
            else:
                self.export_manager.export_to_text(
                    data, output_path, "detailed" if options.include_metadata else "simple"
                )

        except Exception as e:
            raise GitCommandError(f"Export operation failed: {str(e)}")

    def get_file_history(
        self, file_path: str, max_count: int | None = None, branch: str | None = None
    ) -> list[dict[str, Any]]:
        """Get the commit history for a specific file.

        Args:
            file_path: Path to the file relative to repository root.
            max_count: Maximum number of commits to return.
            branch: Branch to search (defaults to current branch).

        Returns:
            List of commit information dictionaries.

        Raises:
            GitCommandError: If file history retrieval fails.
        """
        try:
            from .git_handler import get_file_history

            return get_file_history(self.repo, file_path, branch, max_count)
        except Exception as e:
            raise GitCommandError(f"File history retrieval failed: {str(e)}")

    def get_author_statistics(self, branch: str | None = None) -> dict[str, Any]:
        """Get author statistics for the repository.

        Args:
            branch: Branch to analyze (defaults to current branch).

        Returns:
            Dictionary containing author statistics.

        Raises:
            GitCommandError: If author statistics retrieval fails.
        """
        try:
            from .git_blame import get_author_statistics

            return get_author_statistics(self.repo, branch)
        except Exception as e:
            raise GitCommandError(f"Author statistics retrieval failed: {str(e)}")


# Version information
__version__ = "0.1.0"

# Export the main class and key components
__all__ = ["GitHound", "SearchQuery", "SearchResult", "ExportOptions", "OutputFormat", "__version__"]

# Re-export commonly used classes for convenience
from .models import SearchQuery, SearchResult
from .schemas import ExportOptions
