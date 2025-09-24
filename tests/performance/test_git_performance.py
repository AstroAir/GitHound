"""
Performance tests for GitHound git operations.

These tests ensure that git operations perform within acceptable time and memory limits
for various repository sizes and operation types.
"""

import asyncio
import time
from pathlib import Path
from typing import Any, Optional

import pytest

try:
    import psutil
except ImportError:
    psutil = None  #

from githound.git_blame import get_author_statistics, get_file_blame
from githound.git_diff import compare_commits
from githound.git_handler import (
    extract_commit_metadata,
    get_commits_with_filters,
    get_repository,
    get_repository_metadata,
)


class PerformanceMonitor:
    """Monitor performance metrics during test execution."""

    def __init__(self) -> None:
        self.process = psutil.Process()
        self.start_time: float = 0
        self.start_memory: float = 0
        self.peak_memory: float = 0

    def start_monitoring(self) -> None:
        """Start performance monitoring."""
        self.start_time = time.perf_counter()
        self.start_memory = self.get_memory_usage()
        self.peak_memory = self.start_memory

    def stop_monitoring(self) -> dict[str, float]:
        """Stop monitoring and return metrics."""
        end_time = time.perf_counter()
        end_memory = self.get_memory_usage()

        return {
            "duration_seconds": end_time - self.start_time,
            "start_memory_mb": self.start_memory,
            "end_memory_mb": end_memory,
            "peak_memory_mb": self.peak_memory,
            "memory_increase_mb": end_memory - self.start_memory,
        }

    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        memory_info = self.process.memory_info()
        memory_mb = float(memory_info.rss) / 1024 / 1024
        self.peak_memory = max(self.peak_memory, memory_mb)
        return memory_mb


@pytest.fixture
def performance_monitor() -> None:
    """Provide a performance monitor for tests."""
    return PerformanceMonitor()


@pytest.fixture
def performance_thresholds() -> None:
    """Define performance thresholds for different operations."""
    return {
        # Increased threshold for system load tolerance
        "repository_loading": {"max_duration_seconds": 2.5, "max_memory_increase_mb": 50},
        "commit_history_small": {"max_duration_seconds": 1.0, "max_memory_increase_mb": 25},
        "commit_history_large": {"max_duration_seconds": 5.0, "max_memory_increase_mb": 100},
        "file_blame": {"max_duration_seconds": 3.0, "max_memory_increase_mb": 30},
        "author_statistics": {"max_duration_seconds": 10.0, "max_memory_increase_mb": 75},
        "commit_comparison": {"max_duration_seconds": 2.0, "max_memory_increase_mb": 40},
    }


class TestGitOperationPerformance:
    """Test performance of core git operations."""

    @pytest.mark.performance
    def test_repository_loading_performance(
        self, temp_repo_with_commits, performance_monitor, performance_thresholds
    ) -> None:
        """Test repository loading performance."""
        repo, temp_dir, initial_commit, second_commit = temp_repo_with_commits
        thresholds = performance_thresholds["repository_loading"]

        performance_monitor.start_monitoring()

        # Test repository loading multiple times
        for _ in range(5):
            loaded_repo = get_repository(Path(temp_dir))
            assert loaded_repo is not None

        metrics = performance_monitor.stop_monitoring()

        # Assert performance requirements
        assert (
            metrics["duration_seconds"] < thresholds["max_duration_seconds"]
        ), f"Repository loading took {metrics['duration_seconds']:.2f}s, expected < {thresholds['max_duration_seconds']}s"

        assert (
            metrics["memory_increase_mb"] < thresholds["max_memory_increase_mb"]
        ), f"Memory increased by {metrics['memory_increase_mb']:.2f}MB, expected < {thresholds['max_memory_increase_mb']}MB"

    @pytest.mark.performance
    def test_commit_history_performance_small(
        self, temp_repo_with_commits, performance_monitor, performance_thresholds
    ) -> None:
        """Test commit history retrieval performance for small datasets."""
        repo, temp_dir, initial_commit, second_commit = temp_repo_with_commits
        thresholds = performance_thresholds["commit_history_small"]

        performance_monitor.start_monitoring()

        # Get commit history (small dataset)
        commits = get_commits_with_filters(repo=repo, max_count=10)

        commit_list = list(commits)
        assert len(commit_list) > 0

        metrics = performance_monitor.stop_monitoring()

        # Assert performance requirements
        assert (
            metrics["duration_seconds"] < thresholds["max_duration_seconds"]
        ), f"Small commit history took {metrics['duration_seconds']:.2f}s, expected < {thresholds['max_duration_seconds']}s"

        assert (
            metrics["memory_increase_mb"] < thresholds["max_memory_increase_mb"]
        ), f"Memory increased by {metrics['memory_increase_mb']:.2f}MB, expected < {thresholds['max_memory_increase_mb']}MB"

    @pytest.mark.performance
    @pytest.mark.slow
    def test_commit_history_performance_large(
        self, temp_repo_with_commits, performance_monitor, performance_thresholds
    ) -> None:
        """Test commit history retrieval performance for larger datasets."""
        repo, temp_dir, initial_commit, second_commit = temp_repo_with_commits
        thresholds = performance_thresholds["commit_history_large"]

        # Create additional commits for testing
        self._create_additional_commits(repo, str(temp_dir), count=50)

        performance_monitor.start_monitoring()

        # Get larger commit history
        commits = get_commits_with_filters(repo=repo, max_count=100)

        commit_list = list(commits)

        metrics = performance_monitor.stop_monitoring()

        # Assert performance requirements
        assert (
            metrics["duration_seconds"] < thresholds["max_duration_seconds"]
        ), f"Large commit history took {metrics['duration_seconds']:.2f}s, expected < {thresholds['max_duration_seconds']}s"

        assert (
            metrics["memory_increase_mb"] < thresholds["max_memory_increase_mb"]
        ), f"Memory increased by {metrics['memory_increase_mb']:.2f}MB, expected < {thresholds['max_memory_increase_mb']}MB"

    @pytest.mark.performance
    def test_file_blame_performance(
        self, temp_repo_with_commits, performance_monitor, performance_thresholds
    ) -> None:
        """Test file blame operation performance."""
        repo, temp_dir, initial_commit, second_commit = temp_repo_with_commits
        thresholds = performance_thresholds["file_blame"]

        # Create a file with multiple lines for blame testing
        test_file = Path(temp_dir) / "blame_test.py"
        content = "\n".join([f"# Line {i+1}: This is test content" for i in range(100)])
        test_file.write_text(content)

        repo.index.add(["blame_test.py"])
        repo.index.commit("Add blame test file")

        performance_monitor.start_monitoring()

        # Test file blame operation
        blame_info = get_file_blame(repo, "blame_test.py")
        assert blame_info is not None
        assert blame_info.total_lines > 0

        metrics = performance_monitor.stop_monitoring()

        # Assert performance requirements
        assert (
            metrics["duration_seconds"] < thresholds["max_duration_seconds"]
        ), f"File blame took {metrics['duration_seconds']:.2f}s, expected < {thresholds['max_duration_seconds']}s"

        assert (
            metrics["memory_increase_mb"] < thresholds["max_memory_increase_mb"]
        ), f"Memory increased by {metrics['memory_increase_mb']:.2f}MB, expected < {thresholds['max_memory_increase_mb']}MB"

    @pytest.mark.performance
    def test_author_statistics_performance(
        self, temp_repo_with_commits, performance_monitor, performance_thresholds
    ) -> None:
        """Test author statistics calculation performance."""
        repo, temp_dir, initial_commit, second_commit = temp_repo_with_commits
        thresholds = performance_thresholds["author_statistics"]

        # Create commits with different authors
        self._create_commits_with_different_authors(repo, temp_dir, count=20)

        performance_monitor.start_monitoring()

        # Calculate author statistics
        author_stats = get_author_statistics(repo)
        assert len(author_stats) > 0

        metrics = performance_monitor.stop_monitoring()

        # Assert performance requirements
        assert (
            metrics["duration_seconds"] < thresholds["max_duration_seconds"]
        ), f"Author statistics took {metrics['duration_seconds']:.2f}s, expected < {thresholds['max_duration_seconds']}s"

        assert (
            metrics["memory_increase_mb"] < thresholds["max_memory_increase_mb"]
        ), f"Memory increased by {metrics['memory_increase_mb']:.2f}MB, expected < {thresholds['max_memory_increase_mb']}MB"

    @pytest.mark.performance
    def test_commit_comparison_performance(
        self, temp_repo_with_commits, performance_monitor, performance_thresholds
    ) -> None:
        """Test commit comparison performance."""
        repo, temp_dir, initial_commit, second_commit = temp_repo_with_commits
        thresholds = performance_thresholds["commit_comparison"]

        # Create additional commits for comparison
        third_commit = self._create_additional_commits(repo, temp_dir, count=1)[0]

        performance_monitor.start_monitoring()

        # Compare commits
        diff_result = compare_commits(
            repo=repo, from_commit=initial_commit.hexsha, to_commit=third_commit.hexsha
        )

        assert diff_result is not None
        assert diff_result.files_changed >= 0

        metrics = performance_monitor.stop_monitoring()

        # Assert performance requirements
        assert (
            metrics["duration_seconds"] < thresholds["max_duration_seconds"]
        ), f"Commit comparison took {metrics['duration_seconds']:.2f}s, expected < {thresholds['max_duration_seconds']}s"

        assert (
            metrics["memory_increase_mb"] < thresholds["max_memory_increase_mb"]
        ), f"Memory increased by {metrics['memory_increase_mb']:.2f}MB, expected < {thresholds['max_memory_increase_mb']}MB"

    def _create_additional_commits(self, repo: Any, temp_dir: str, count: int) -> list[Any]:
        """Create additional commits for testing."""
        commits: list[Any] = []

        for i in range(count):
            file_path = Path(temp_dir) / f"perf_test_{i}.txt"
            file_path.write_text(f"Performance test file {i}\nContent line 2\nContent line 3")

            repo.index.add([f"perf_test_{i}.txt"])
            commit = repo.index.commit(f"Performance test commit {i}")
            commits.append(commit)

        return commits

    def _create_commits_with_different_authors(self, repo: Any, temp_dir: str, count: int) -> None:
        """Create commits with different authors for testing."""
        authors = [
            ("Alice Developer", "alice@example.com"),
            ("Bob Contributor", "bob@example.com"),
            ("Charlie Maintainer", "charlie@example.com"),
        ]

        for i in range(count):
            author_name, author_email = authors[i % len(authors)]

            # Configure author for this commit
            with repo.config_writer() as config:  # [attr-defined]
                config.set_value("user", "name", author_name)  # [attr-defined]
                # [attr-defined]
                config.set_value("user", "email", author_email)

            file_path = Path(temp_dir) / f"author_test_{i}.txt"
            file_path.write_text(f"File by {author_name}\nCommit number {i}")

            repo.index.add([f"author_test_{i}.txt"])
            repo.index.commit(f"Commit by {author_name} - {i}")


@pytest.mark.performance
class TestConcurrentOperations:
    """Test performance of concurrent git operations."""

    @pytest.mark.asyncio
    async def test_concurrent_repository_analysis(
        self, temp_repo_with_commits, performance_monitor
    ) -> None:
        """Test concurrent repository analysis operations."""
        repo, temp_dir, initial_commit, second_commit = temp_repo_with_commits

        performance_monitor.start_monitoring()

        # Create multiple concurrent analysis tasks
        async def analyze_repository_async() -> None:
            """Async wrapper for repository analysis."""
            return await asyncio.get_event_loop().run_in_executor(
                None, get_repository_metadata, repo
            )

        # Run 5 concurrent analyses
        tasks = [analyze_repository_async() for _ in range(5)]
        results = await asyncio.gather(*tasks)

        metrics = performance_monitor.stop_monitoring()

        # Verify all analyses completed successfully
        assert len(results) == 5
        for result in results:
            assert result is not None
            assert "total_commits" in result

        # Performance should be reasonable even with concurrency
        assert (
            metrics["duration_seconds"] < 10.0
        ), f"Concurrent analysis took {metrics['duration_seconds']:.2f}s, expected < 10.0s"

    @pytest.mark.asyncio
    async def test_concurrent_commit_operations(
        self, temp_repo_with_commits, performance_monitor
    ) -> None:
        """Test concurrent commit-related operations."""
        repo, temp_dir, initial_commit, second_commit = temp_repo_with_commits

        performance_monitor.start_monitoring()

        # Create concurrent commit operations
        async def extract_commit_async(commit) -> None:
            """Async wrapper for commit metadata extraction."""
            return await asyncio.get_event_loop().run_in_executor(
                None, extract_commit_metadata, commit
            )

        commits = [initial_commit, second_commit]
        tasks = [extract_commit_async(commit) for commit in commits for _ in range(3)]

        results = await asyncio.gather(*tasks)

        metrics = performance_monitor.stop_monitoring()

        # Verify all operations completed successfully
        assert len(results) == 6  # 2 commits × 3 repetitions
        for result in results:
            assert result is not None
            assert hasattr(result, "hash")
            assert hasattr(result, "author_name")

        # Performance should be reasonable
        assert (
            metrics["duration_seconds"] < 5.0
        ), f"Concurrent commit operations took {metrics['duration_seconds']:.2f}s, expected < 5.0s"


@pytest.mark.benchmark
class TestBenchmarkOperations:
    """Benchmark tests for git operations using pytest-benchmark."""

    def test_benchmark_repository_loading(self, temp_repo_with_commits, benchmark) -> None:
        """Benchmark repository loading operation."""
        repo, temp_dir, initial_commit, second_commit = temp_repo_with_commits

        def load_repository() -> None:
            return get_repository(Path(temp_dir))

        result = benchmark(load_repository)
        assert result is not None

    def test_benchmark_commit_metadata_extraction(self, temp_repo_with_commits, benchmark) -> None:
        """Benchmark commit metadata extraction."""
        repo, temp_dir, initial_commit, second_commit = temp_repo_with_commits

        def extract_metadata() -> None:
            return extract_commit_metadata(initial_commit)

        result = benchmark(extract_metadata)
        assert result is not None
        assert result.hash == initial_commit.hexsha

    def test_benchmark_repository_metadata(self, temp_repo_with_commits, benchmark) -> None:
        """Benchmark repository metadata extraction."""
        repo, temp_dir, initial_commit, second_commit = temp_repo_with_commits

        def get_metadata() -> None:
            return get_repository_metadata(repo)

        result = benchmark(get_metadata)
        assert result is not None
        assert "total_commits" in result
